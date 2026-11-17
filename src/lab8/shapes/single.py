"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import dispatch, run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


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
    shape = "single"
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

    def decide(observation: dict[str, Any]) -> dict[str, Any]:
        complete(
            budget,
            seed=seed,
            purpose="react",
            prompt="Choose the next read-only claim investigation step.",
        )
        last_tool = observation.get("last_tool")
        if last_tool is None:
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": claim["order_id"],
                    "principal_id": claim["principal_id"],
                },
            }
        result = observation["last_result"]
        if last_tool == "lookup_order":
            if not result["visible"]:
                return {
                    "final": {
                        "status": "escalated",
                        "proposal_amount": 0,
                        "error_reason": result["reason"],
                    }
                }
            return {"tool": "compute_compensation", "args": {"order": result["order"]}}
        if last_tool == "compute_compensation":
            return {
                "final": {
                    "status": "quote",
                    "quote": result,
                }
            }
        return {
            "final": {
                "status": "failed",
                "proposal_amount": 0,
                "error_reason": "unexpected_tool_result",
            }
        }

    outcome = run_react(
        conn,
        budget,
        observation={"claim": {"order_id": claim["order_id"]}},
        decide=decide,
        max_steps=8,
    )
    observation = outcome["observation"]
    if "last_result" in observation:
        trace.add(
            "agent_tool",
            {
                "tool": observation["last_tool"],
                "result": observation["last_result"],
            },
        )

    final = outcome["final"]
    if final["status"] == "escalated":
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
            error_reason=final["error_reason"],
        )
    if final["status"] != "quote":
        trace.add("decision", {"status": "failed"})
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final.get("error_reason", "step_cap"),
        )

    quote = final["quote"]
    proposal = int(quote["amount_vnd"])
    trace.add("quote", quote)
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
