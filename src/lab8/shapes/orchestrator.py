"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


_TRACE_ORDER_FIELDS = (
    "order_id",
    "status",
    "delay_days",
    "shipping_fee_vnd",
    "paid_vnd",
    "damage_verified",
    "carrier",
)
_TRACE_QUOTE_FIELDS = ("amount_vnd", "reason", "clause_ids", "parts")


def _trace_order(result: dict) -> dict:
    """Explicit allowlist of order fields for the trace (no phone/address/notes/items)."""
    out = {"visible": bool(result.get("visible")), "reason": result.get("reason")}
    if result.get("order_id"):
        out["order_id"] = result["order_id"]
    order = result.get("order") or {}
    if order:
        out["order"] = {k: order[k] for k in _TRACE_ORDER_FIELDS if k in order}
    return out


def _trace_history(result: dict | None) -> dict | None:
    if result is None:
        return None
    keys = ("visible", "reason", "order_id", "refund_count", "refunded_vnd")
    return {k: result[k] for k in keys if k in result}


def _trace_quote(result: dict) -> dict:
    return {k: result[k] for k in _TRACE_QUOTE_FIELDS if k in result}


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    shape = "orchestrator"
    run_id = make_run_id(shape, claim_id, seed)
    budget = Budget()
    trace = Trace(run_id)

    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add(
        "claim",
        {
            "found": claim["found"],
            "claim_id": claim_id,
            "order_id": claim.get("order_id"),
        },
    )
    if not claim["found"]:
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )
    if not claim["order_id"]:
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    complete(
        budget,
        seed=seed,
        purpose="orchestrate",
        prompt="Delegate an owner-scoped claim investigation to read-only tools.",
    )
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="verify_order_and_quote",
        facts={},
        allowed_tools=[
            "lookup_order",
            "lookup_policy",
            "lookup_refund_history",
            "compute_compensation",
        ],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(
        conn,
        budget,
        handoff,
        principal_id=claim["principal_id"],
    )
    order_result = investigated["tools"].get("lookup_order", {})
    trace.add(
        "investigation",
        {
            "claim_view": investigated["claim_view"],
            "lookup_order": _trace_order(order_result),
            "policy_count": len(
                investigated["tools"].get("lookup_policy", {}).get("policies", [])
            ),
            "refund_history": _trace_history(
                investigated["tools"].get("lookup_refund_history")
            ),
        },
    )
    if not order_result.get("visible"):
        trace.add("decision", {"status": "escalated"})
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_result.get("reason", "not_found"),
        )

    quote = investigated["tools"]["compute_compensation"]
    proposal = int(quote["amount_vnd"])
    trace.add("quote", safe_dump(_trace_quote(quote)))
    if proposal <= 0:
        trace.add("decision", {"status": "denied"})
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote["reason"],
        )

    try:
        refund = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("refund", {"ok": refund["ok"], "reason": refund["reason"]})
    if not refund["ok"]:
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="failed" if refund["conflict"] else "denied",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=refund["reason"],
        )
    return finish(
        conn,
        shape=shape,
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
    )
