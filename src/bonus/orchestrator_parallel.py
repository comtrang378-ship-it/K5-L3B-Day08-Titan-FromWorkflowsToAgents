"""B1: parallel read-only investigators with one host-controlled writer."""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import Future, ThreadPoolExecutor
from functools import lru_cache
from typing import Any

from lab8.config_loader import load_yaml
from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import dispatch
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

_READ_TOOLS = ("lookup_order", "lookup_policy", "lookup_refund_history")


@lru_cache(maxsize=1)
def _latency_config() -> dict[str, Any]:
    config = load_yaml("bonus/latency.yaml")
    if not isinstance(config, dict):
        raise ValueError("bonus/latency.yaml must contain a YAML mapping")
    for section in ("model_calls", "tools", "host_calls"):
        if not isinstance(config.get(section), dict):
            raise ValueError(f"bonus/latency.yaml must define a {section} mapping")
    jitter_ms = config.get("jitter_ms")
    if not isinstance(jitter_ms, int) or jitter_ms < 0:
        raise ValueError("bonus/latency.yaml jitter_ms must be a non-negative integer")
    return config


def _duration_ms(section: str, name: str, seed: int, call_index: int = 0) -> int:
    config = _latency_config()
    values = config[section]
    if name not in values:
        raise KeyError(f"missing simulated latency for {section}.{name}")
    base_ms = values[name]
    if not isinstance(base_ms, int) or base_ms < 0:
        raise ValueError(f"{section}.{name} must be a non-negative integer")
    jitter_ms = config["jitter_ms"]
    digest = hashlib.sha256(f"{seed}:{section}:{name}:{call_index}".encode()).digest()
    jitter = int.from_bytes(digest[:4], "big") % (2 * jitter_ms + 1) - jitter_ms
    return max(0, base_ms + jitter)


def simulated_critical_paths(events: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    """Estimate sequential and DAG critical paths; this never sleeps or measures wall time."""
    claim_event = next((event for event in events if event.get("kind") == "claim"), None)
    if claim_event is None:
        raise ValueError("trace has no claim event")
    claim_payload = claim_event.get("payload") or {}
    prefix_ms = _duration_ms("tools", "get_claim_view", seed)
    if not claim_payload.get("found") or not claim_payload.get("order_id"):
        return {
            "sequential_ms": prefix_ms,
            "parallel_ms": prefix_ms,
            "amdahl_predicted_speedup": 1.0,
            "parallel_workers": len(_READ_TOOLS),
        }

    handoff_exists = any(event.get("kind") == "handoff" for event in events)
    if not handoff_exists:
        raise ValueError("trace has an order id but no handoff event")
    prefix_ms += _duration_ms("model_calls", "orchestrate", seed)
    prefix_ms += _duration_ms("tools", "get_claim_view", seed, call_index=1)

    investigation_event = next(
        (event for event in events if event.get("kind") == "investigation"),
        None,
    )
    if investigation_event is None:
        raise ValueError("trace has no investigation event")
    investigation = investigation_event.get("payload") or {}
    if not isinstance(investigation.get("lookup_order"), dict):
        raise ValueError("trace investigation has no lookup_order result")

    order_ms = _duration_ms("tools", "lookup_order", seed)
    policy_ms = _duration_ms("tools", "lookup_policy", seed)
    history_ms = _duration_ms("tools", "lookup_refund_history", seed)
    quote_exists = any(event.get("kind") == "quote" for event in events)
    quote_ms = _duration_ms("tools", "compute_compensation", seed) if quote_exists else 0
    writer_exists = any(event.get("kind") == "refund" for event in events)
    writer_ms = _duration_ms("host_calls", "issue_refund", seed) if writer_exists else 0

    investigator_work_ms = order_ms + policy_ms + history_ms
    sequential_ms = prefix_ms + investigator_work_ms + quote_ms + writer_ms
    parallel_investigator_path_ms = max(
        order_ms + quote_ms,
        policy_ms,
        history_ms,
    )
    parallel_ms = prefix_ms + parallel_investigator_path_ms + writer_ms

    serial_fraction = (sequential_ms - investigator_work_ms) / sequential_ms
    amdahl_speedup = 1 / (
        serial_fraction + (1 - serial_fraction) / len(_READ_TOOLS)
    )
    return {
        "sequential_ms": sequential_ms,
        "parallel_ms": parallel_ms,
        "amdahl_predicted_speedup": amdahl_speedup,
        "parallel_workers": len(_READ_TOOLS),
    }


def _read_tool(
    store_path: str,
    name: str,
    args: dict[str, Any],
) -> tuple[dict[str, Any], Budget]:
    conn = connect(store_path)
    try:
        worker_budget = Budget()
        result = dispatch(conn, worker_budget, name, args, worker=True)
        return result, worker_budget
    finally:
        conn.close()


def _merge_tool_budget(target: Budget, worker: Budget) -> None:
    if worker.model_calls:
        raise RuntimeError("investigators must not make model calls")
    target.tool_calls += worker.tool_calls
    target.cost_estimate += worker.cost_estimate
    target.steps += worker.steps


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, store_path=store_path, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None,
) -> RunResult:
    shape = "orchestrator_parallel"
    budget = Budget()
    trace = Trace(make_run_id(shape, claim_id, seed))

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
        allowed_tools=list(_READ_TOOLS),
    )
    trace.add("handoff", safe_dump(handoff))

    budget.add_tool(tool_cost())
    worker_claim = get_claim_view(conn, claim_id)
    principal_id = claim["principal_id"]
    read_args = {
        "lookup_order": {
            "order_id": worker_claim.get("order_id"),
            "principal_id": principal_id,
        },
        "lookup_policy": {},
        "lookup_refund_history": {
            "order_id": worker_claim.get("order_id"),
            "principal_id": principal_id,
        },
    }
    futures: dict[str, Future[tuple[dict[str, Any], Budget]]] = {}
    with ThreadPoolExecutor(max_workers=len(_READ_TOOLS), thread_name_prefix="logix-investigator") as pool:
        for name in _READ_TOOLS:
            futures[name] = pool.submit(_read_tool, store_path, name, read_args[name])

        # Retrieve the order first because quoting depends on it. The other results
        # are still gathered in a fixed order after the dependent quote is computed.
        order_result, order_budget = futures["lookup_order"].result()
        _merge_tool_budget(budget, order_budget)
        quote: dict[str, Any] | None = None
        if order_result.get("visible"):
            quote = dispatch(
                conn,
                budget,
                "compute_compensation",
                {"order": order_result["order"]},
                worker=True,
            )

        policy_result, policy_budget = futures["lookup_policy"].result()
        _merge_tool_budget(budget, policy_budget)
        history_result, history_budget = futures["lookup_refund_history"].result()
        _merge_tool_budget(budget, history_budget)

    investigated_tools = {
        "lookup_order": order_result,
        "lookup_policy": policy_result,
        "lookup_refund_history": history_result,
    }
    if quote is not None:
        investigated_tools["compute_compensation"] = quote
    investigated = {
        "claim_view": {
            key: worker_claim[key]
            for key in ("found", "claim_id", "order_id")
            if key in worker_claim
        },
        "tools": investigated_tools,
    }
    trace.add(
        "investigation",
        {
            "claim_view": investigated["claim_view"],
            "lookup_order": order_result,
            "policy_count": len(policy_result.get("policies", [])),
            "refund_history": history_result,
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

    if quote is None:
        raise RuntimeError("visible order did not produce a compensation quote")
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
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("refund", {"ok": outcome["ok"], "reason": outcome["reason"]})
    if not outcome["ok"]:
        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="failed" if outcome["conflict"] else "denied",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome["reason"],
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
