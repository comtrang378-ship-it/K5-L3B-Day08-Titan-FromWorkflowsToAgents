"""Reproduce the B1 benchmark with official labels and add simulated DAG latency."""

from __future__ import annotations

import argparse
import json
import math
import tempfile
import time
from pathlib import Path
from typing import Any

from lab8.app import register_extra_shapes
from lab8.benchmark import LEAK_MARKERS, prepare_from_memory, render_table, run_trial
from lab8.config_loader import as_of, pricing, repo_path
from lab8.db import connect, load_json, load_jsonl
from lab8.metrics import (
    artifact_blob,
    check_trace,
    ledger_snapshot,
    summarize,
    trial_pass,
    unexpected_ledger_rows,
)

from bonus.orchestrator_parallel import simulated_critical_paths

EXPECTED_EXTRA_SHAPE = "orchestrator_parallel=bonus.orchestrator_parallel:run_claim"
SHAPES = ("orchestrator", "orchestrator_parallel")
_SAFETY_COUNTER_NAMES = {
    "trace_invalid": "trace_invalid_trials",
    "privacy_leak": "privacy_leak_trials",
    "approval_bypass": "approval_bypass_trials",
    "duplicate_refund": "duplicate_refund_trials",
    "unexpected_ledger_rows": "unexpected_ledger_trials",
    "result_ledger_mismatch": "result_ledger_mismatch_trials",
    "policy_denial_missing": "missing_policy_denial_trials",
}


def _trace_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    trace_path = Path(payload["trace_path"])
    body = json.loads(trace_path.read_text(encoding="utf-8"))
    events = body.get("events")
    if not isinstance(events, list):
        raise ValueError(f"{trace_path} does not contain an events list")
    return events


def _trial_row(
    *,
    shape: str,
    claim: dict[str, Any],
    seed: int,
    store: Path,
    world: dict[str, Any],
    claims: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, bool], str | None, str | None]:
    claim_id = claim["claim_id"]
    expected = claim["expected"]
    prepare_from_memory(store, world, claims)
    started_at = time.time()
    payload, error = run_trial(shape, claim_id, seed, store)

    conn = connect(store)
    try:
        snapshot = ledger_snapshot(conn, claim_id)
        unexpected_rows = unexpected_ledger_rows(conn, claim_id)
        row: dict[str, Any] = {
            "shape": shape,
            "claim_id": claim_id,
            "seed": seed,
            "critical_path_ms": None,
        }
        trace_valid = False
        privacy_leak = False
        result_ledger_mismatch = False
        if error is not None or payload is None:
            passed = False
            reason = error or "missing_result"
            row.update(
                passed=passed,
                reason=reason,
                cost_estimate=0.0,
                steps=0,
                model_calls=0,
                tool_calls=0,
                run_id=f"R-{shape}-{claim_id}-s{seed}",
                status="error",
            )
        else:
            passed, reason = trial_pass(payload, expected, conn, started_at=started_at)
            trace_valid, _ = check_trace(payload, started_at=started_at)
            blob = artifact_blob(payload)
            privacy_leak = any(marker in blob for marker in LEAK_MARKERS) or any(
                marker in blob for marker in expected.get("forbid_substrings") or []
            )
            events = _trace_events(payload) if trace_valid else []
            if events:
                row["critical_path_ms"] = simulated_critical_paths(events, seed)[
                    "sequential_ms" if shape == "orchestrator" else "parallel_ms"
                ]
            reported_effects = payload.get("refund_effects") or []
            reported_amount = sum(int(effect["amount_vnd"]) for effect in reported_effects)
            result_ledger_mismatch = (
                len(reported_effects) != snapshot["refund_count"]
                or reported_amount != snapshot["refund_vnd"]
                or int(payload.get("committed_audit_count") or 0)
                != snapshot["committed_audit_count"]
            )
            row.update(
                passed=passed,
                reason=reason,
                cost_estimate=payload["cost_estimate"],
                steps=len(events),
                model_calls=payload["model_calls"],
                tool_calls=payload["tool_calls"],
                run_id=payload["run_id"],
                status=payload["status"],
            )

        own_refunds = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?",
                (claim_id,),
            ).fetchone()["n"]
        )
        approval_bypass = (
            not bool(expected.get("approval_ok"))
            and (snapshot["refund_count"] > 0 or snapshot["refund_vnd"] > 0)
        )
        policy_denial_missing = bool(expected.get("policy_denied")) and not snapshot["policy_denied"]
        safety = {
            "trace_invalid": not trace_valid,
            "privacy_leak": privacy_leak,
            "approval_bypass": approval_bypass,
            "duplicate_refund": own_refunds > 1,
            "unexpected_ledger_rows": unexpected_rows != 0,
            "result_ledger_mismatch": result_ledger_mismatch,
            "policy_denial_missing": policy_denial_missing,
        }
        behavior = None
        if payload is not None:
            behavior = json.dumps(
                {
                    "status": payload["status"],
                    "proposal_amount": payload["proposal_amount"],
                    "refund_effects": payload["refund_effects"],
                    "committed_audit_count": payload["committed_audit_count"],
                    "model_calls": payload["model_calls"],
                    "tool_calls": payload["tool_calls"],
                    "cost_estimate": payload["cost_estimate"],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
        ledger = json.dumps(
            {
                "refund_count": snapshot["refund_count"],
                "refund_vnd": snapshot["refund_vnd"],
                "committed_audit_count": snapshot["committed_audit_count"],
                "policy_denied": snapshot["policy_denied"],
                "unexpected_ledger_rows": unexpected_rows,
            },
            sort_keys=True,
        )
        return row, safety, behavior, ledger
    finally:
        conn.close()


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _critical_path_summary(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    values = [
        float(row["critical_path_ms"])
        for row in rows
        if row.get("critical_path_ms") is not None
    ]
    return {
        "trials": len(values),
        "mean_ms": round(sum(values) / len(values), 3) if values else None,
        "p95_ms": _percentile(values, 0.95),
    }


def run_b1(
    *,
    world: dict[str, Any],
    claims: list[dict[str, Any]],
    seeds: list[int],
) -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    safety_by_shape: dict[str, dict[str, int]] = {
        shape: {
            "trials": 0,
            "trace_invalid_trials": 0,
            "privacy_leak_trials": 0,
            "approval_bypass_trials": 0,
            "duplicate_refund_trials": 0,
            "unexpected_ledger_trials": 0,
            "result_ledger_mismatch_trials": 0,
            "missing_policy_denial_trials": 0,
        }
        for shape in SHAPES
    }
    results_by_pair: dict[tuple[str, int], dict[str, tuple[str | None, str]]] = {}

    with tempfile.TemporaryDirectory(
        prefix="lab8-bonus-b1-",
        ignore_cleanup_errors=True,
    ) as temp_dir:
        root = Path(temp_dir)
        for shape in SHAPES:
            for claim in claims:
                claim_id = claim["claim_id"]
                for seed in seeds:
                    store = root / f"{shape}-{claim_id}-{seed}.sqlite"
                    row, safety, behavior, ledger = _trial_row(
                        shape=shape,
                        claim=claim,
                        seed=seed,
                        store=store,
                        world=world,
                        claims=claims,
                    )
                    trials.append(row)
                    counters = safety_by_shape[shape]
                    counters["trials"] += 1
                    for key, value in safety.items():
                        if value:
                            counters[_SAFETY_COUNTER_NAMES[key]] += 1
                    pair = (claim_id, seed)
                    results_by_pair.setdefault(pair, {})[shape] = (behavior, ledger)

    paired_trials = 0
    behavior_mismatches = 0
    ledger_mismatches = 0
    rows_by_pair: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in trials:
        rows_by_pair.setdefault((row["claim_id"], row["seed"]), {})[row["shape"]] = row

    for pair_results in results_by_pair.values():
        if all(shape in pair_results for shape in SHAPES):
            paired_trials += 1
            baseline, variant = (pair_results[shape] for shape in SHAPES)
            behavior_mismatches += baseline[0] != variant[0]
            ledger_mismatches += baseline[1] != variant[1]

    by_shape = summarize(trials)
    path_by_shape = {
        shape: _critical_path_summary([row for row in trials if row["shape"] == shape])
        for shape in SHAPES
    }
    sequential_mean = path_by_shape["orchestrator"]["mean_ms"]
    parallel_mean = path_by_shape["orchestrator_parallel"]["mean_ms"]
    measured_speedups = []
    for pair, pair_rows in rows_by_pair.items():
        if all(shape in pair_rows for shape in SHAPES):
            sequential_row = pair_rows["orchestrator"]
            parallel_row = pair_rows["orchestrator_parallel"]
            if sequential_row["critical_path_ms"] and parallel_row["critical_path_ms"]:
                measured_speedups.append(
                    sequential_row["critical_path_ms"] / parallel_row["critical_path_ms"]
                )

    paired_rows = [
        row
        for row in trials
        if row["shape"] == "orchestrator" and row.get("critical_path_ms") is not None
    ]
    predicted_speedups = []
    from bonus.orchestrator_parallel import simulated_critical_paths

    for row in paired_rows:
        trace_path = Path("traces") / f"{row['run_id']}.json"
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        predicted_speedups.append(
            simulated_critical_paths(trace["events"], row["seed"])[
                "amdahl_predicted_speedup"
            ]
        )

    return {
        "topic": "B1 · Parallel investigators and critical path",
        "source_claim": (
            "The supplied lab brief attributes to Google Research 2026 that multi-agent "
            "parallelization helps only when task work can actually be parallelized."
        ),
        "controlled_variables": {
            "as_of": as_of(),
            "claim_ids": [claim["claim_id"] for claim in claims],
            "seeds": seeds,
            "pricing": pricing(),
            "model_backend": "MockLLM",
            "evaluator": "lab8.metrics.trial_pass",
            "database_isolation": "fresh SQLite store per shape/claim/seed",
        },
        "latency_model": {
            "config": "bonus/latency.yaml",
            "method": "DAG critical path; deterministic SHA-256 keyed jitter by seed/tool/call index",
            "wall_clock_measured": False,
            "parallel_workers": 3,
        },
        "by_shape": by_shape,
        "critical_path": {
            "by_shape": path_by_shape,
            "measured_speedup_mean": (
                round(sum(measured_speedups) / len(measured_speedups), 4)
                if measured_speedups
                else None
            ),
            "ratio_of_mean_paths": (
                round(sequential_mean / parallel_mean, 4)
                if sequential_mean and parallel_mean
                else None
            ),
            "amdahl_predicted_speedup_mean": (
                round(sum(predicted_speedups) / len(predicted_speedups), 4)
                if predicted_speedups
                else None
            ),
        },
        "safety_by_shape": safety_by_shape,
        "paired_equivalence": {
            "paired_claim_seed_trials": paired_trials,
            "behavior_mismatch_trials": behavior_mismatches,
            "ledger_mismatch_trials": ledger_mismatches,
        },
        "trials": trials,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the B1 parallel-investigator benchmark")
    parser.add_argument("--extra-shape", action="append", required=True)
    parser.add_argument("--cases", default=str(repo_path("data", "public_claims.jsonl")))
    parser.add_argument("--world", default=str(repo_path("data", "public_world_state.json")))
    parser.add_argument("--seeds", default="11,22,33,44,55")
    parser.add_argument("--out", default="reports/bonus_b1.json")
    args = parser.parse_args(argv)
    if args.extra_shape != [EXPECTED_EXTRA_SHAPE]:
        raise SystemExit(f"use --extra-shape {EXPECTED_EXTRA_SHAPE}")
    register_extra_shapes(args.extra_shape)
    world = load_json(args.world)
    claims = load_jsonl(args.cases)
    seeds = [int(value) for value in args.seeds.split(",") if value]
    if not seeds:
        raise SystemExit("--seeds must contain at least one integer")

    report = run_b1(world=world, claims=claims, seeds=seeds)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(render_table(report))
    for shape, stats in report["critical_path"]["by_shape"].items():
        print(
            f"{shape:<22} critical path mean/p95: "
            f"{stats['mean_ms']} / {stats['p95_ms']} ms"
        )
    print(f"critical-path speedup mean: {report['critical_path']['measured_speedup_mean']}")
    print(f"Amdahl predicted speedup mean: {report['critical_path']['amdahl_predicted_speedup_mean']}")
    print(f"paired ledger mismatches: {report['paired_equivalence']['ledger_mismatch_trials']}")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
