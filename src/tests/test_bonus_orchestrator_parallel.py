from __future__ import annotations

import threading
import time

import pytest

from bonus import orchestrator_parallel as parallel
from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.metrics import ledger_snapshot, trial_pass, unexpected_ledger_rows
from lab8.shapes import orchestrator
from tests.conftest import BY_ID, CLAIMS, WORLD


PUBLIC_SINGLE_RUN_CLAIMS = tuple(
    [f"C-{index:03d}" for index in range(1, 11)] + ["C-013", "C-014"]
)


def _init(path):
    init_store(path, WORLD, CLAIMS).close()
    return path


def _snapshot(path, claim_id):
    conn = connect(path)
    try:
        return ledger_snapshot(conn, claim_id), unexpected_ledger_rows(conn, claim_id)
    finally:
        conn.close()


def test_parallel_result_is_independent_of_investigator_completion_order(
    tmp_path,
    monkeypatch,
):
    original_dispatch = parallel.dispatch
    original_connect = parallel.connect
    original_issue_refund = parallel.issue_refund
    opened_connections = []
    writer_threads = []

    def tracked_connect(path):
        conn = original_connect(path)
        if threading.current_thread().name.startswith("logix-investigator"):
            opened_connections.append(conn)
        return conn

    def tracked_issue_refund(*args, **kwargs):
        writer_threads.append(threading.current_thread().name)
        return original_issue_refund(*args, **kwargs)

    monkeypatch.setattr(parallel, "connect", tracked_connect)
    monkeypatch.setattr(parallel, "issue_refund", tracked_issue_refund)

    def run_with_order(store, slow_tool, release_tool):
        release = threading.Event()
        start_together = threading.Barrier(3)
        completion_order = []
        completion_lock = threading.Lock()

        def controlled_dispatch(conn, budget, name, args, *, worker):
            if not threading.current_thread().name.startswith("logix-investigator"):
                return original_dispatch(conn, budget, name, args, worker=worker)
            assert worker
            start_together.wait(timeout=5)
            if name == slow_tool and not release.wait(timeout=5):
                raise TimeoutError(f"{release_tool} did not finish in time")
            result = original_dispatch(conn, budget, name, args, worker=worker)
            with completion_lock:
                completion_order.append(name)
            if name == release_tool:
                release.set()
            return result

        monkeypatch.setattr(parallel, "dispatch", controlled_dispatch)
        result = parallel.run_claim("C-001", seed=11, store_path=str(store))
        return result, completion_order

    first_store = _init(tmp_path / "first.sqlite")
    second_store = _init(tmp_path / "second.sqlite")
    first, first_order = run_with_order(
        first_store,
        slow_tool="lookup_order",
        release_tool="lookup_policy",
    )
    second, second_order = run_with_order(
        second_store,
        slow_tool="lookup_policy",
        release_tool="lookup_order",
    )

    assert first_order.index("lookup_policy") < first_order.index("lookup_order")
    assert second_order.index("lookup_order") < second_order.index("lookup_policy")
    assert first.as_dict() == second.as_dict()
    assert len({id(conn) for conn in opened_connections}) == 6
    assert writer_threads == ["MainThread", "MainThread"]
    first_snapshot, first_unexpected = _snapshot(first_store, "C-001")
    second_snapshot, second_unexpected = _snapshot(second_store, "C-001")
    assert first_snapshot == second_snapshot
    assert first_unexpected == second_unexpected == 0


@pytest.mark.parametrize("claim_id", PUBLIC_SINGLE_RUN_CLAIMS)
def test_parallel_matches_sequential_orchestrator_on_public_cases(
    tmp_path,
    claim_id,
):
    sequential_store = _init(tmp_path / f"sequential-{claim_id}.sqlite")
    parallel_store = _init(tmp_path / f"parallel-{claim_id}.sqlite")
    sequential_started = time.time()
    sequential = orchestrator.run_claim(
        claim_id,
        seed=11,
        store_path=str(sequential_store),
    )
    parallel_started = time.time()
    result = parallel.run_claim(
        claim_id,
        seed=11,
        store_path=str(parallel_store),
    )

    for candidate, store, started in (
        (sequential, sequential_store, sequential_started),
        (result, parallel_store, parallel_started),
    ):
        conn = connect(store)
        try:
            passed, reason = trial_pass(
                candidate.as_dict(),
                BY_ID[claim_id]["expected"],
                conn,
                started_at=started,
            )
        finally:
            conn.close()
        assert passed, reason

    assert result.status == sequential.status
    assert result.proposal_amount == sequential.proposal_amount
    assert result.refund_effects == sequential.refund_effects
    assert result.committed_audit_count == sequential.committed_audit_count
    assert result.model_calls == sequential.model_calls
    assert result.tool_calls == sequential.tool_calls
    assert result.cost_estimate == sequential.cost_estimate
    sequential_snapshot, sequential_unexpected = _snapshot(sequential_store, claim_id)
    parallel_snapshot, parallel_unexpected = _snapshot(parallel_store, claim_id)
    assert parallel_snapshot == sequential_snapshot
    assert parallel_unexpected == sequential_unexpected == 0


def test_parallel_shape_resumes_after_host_crash_without_duplicate_refund(tmp_path):
    store = _init(tmp_path / "crash-resume.sqlite")
    with pytest.raises(InjectedCrash):
        parallel.run_claim(
            "C-012",
            seed=11,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )

    started = time.time()
    result = parallel.run_claim("C-012", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        passed, reason = trial_pass(
            result.as_dict(),
            BY_ID["C-012"]["expected"],
            conn,
            started_at=started,
        )
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?",
            ("C-012",),
        ).fetchone()["n"]
    finally:
        conn.close()
    assert passed, reason
    assert count == 1
