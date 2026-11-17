"""Orchestrator (shape C) durability: crash, resume, rerun, approval gate.

`lab8.crash_test` (crash.json 20/20) calls `durability.issue_refund` directly
and only runs swarm end to end, so it never exercises the orchestrator. These
tests close that gap for rubric C3 and must-pass 1 and 3:

- every crash point x every refunding public claim: resume leaves exactly one
  ledger row with the labelled amount and one `refund_committed` audit,
  including the order cap (T14) and an approval below the quote (T08);
- resume on a different seed after a crash still writes one refund;
- rerunning the same claim (T11) never adds a row or an audit;
- claims the approval gate rejects never refund, even with `crash_at` set,
  and leave a `policy_denied` audit.

    python -m pytest -q -m student -o addopts= tests/test_orchestrator_durability.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD

pytestmark = pytest.mark.student

CRASH_POINTS = ("before_effect", "after_effect_before_checkpoint", "after_checkpoint")
REFUNDING = [c["claim_id"] for c in CLAIMS if c["expected"]["refund_count"] == 1]
GATE_DENIED = [c["claim_id"] for c in CLAIMS if c["expected"]["policy_denied"]]


def _store(tmp_path: Path, name: str) -> str:
    path = tmp_path / f"{name}.sqlite"
    init_store(path, WORLD, CLAIMS).close()
    return str(path)


def _ledger(store: str, claim_id: str) -> tuple[int, int, int, int]:
    conn = connect(store)
    try:
        rows = conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = ?", (claim_id,)).fetchone()[0]
        refund = get_refund(conn, claim_id)
        denied = conn.execute(
            "SELECT COUNT(*) FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
            (claim_id,),
        ).fetchone()[0]
        return rows, (int(refund["amount_vnd"]) if refund else 0), committed_audit_count(conn, claim_id), denied
    finally:
        conn.close()


def test_public_set_has_refunding_and_gate_denied_claims():
    # Guard: the parametrised tests below must not silently run on nothing.
    assert {"C-001", "C-008", "C-014"} <= set(REFUNDING)
    assert {"C-007", "C-013"} <= set(GATE_DENIED)


@pytest.mark.parametrize("point", CRASH_POINTS)
@pytest.mark.parametrize("claim_id", REFUNDING)
def test_crash_then_resume_commits_exactly_once(claim_id, point, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    expected = BY_ID[claim_id]["expected"]
    store = _store(tmp_path, f"{claim_id}-{point}")

    with pytest.raises(InjectedCrash):
        run_claim(claim_id, seed=11, store_path=store, crash_at=point)

    result = run_claim(claim_id, seed=11, store_path=store)
    assert result.status == "resolved"
    assert result.proposal_amount == expected["proposal_amount"]
    assert _ledger(store, claim_id)[:3] == (1, expected["refund_vnd"], 1)
    assert result.committed_audit_count == 1
    assert [int(e["amount_vnd"]) for e in result.refund_effects] == [expected["refund_vnd"]]


@pytest.mark.parametrize("point", CRASH_POINTS)
def test_resume_on_another_seed_still_one_refund(point, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = _store(tmp_path, f"seed-{point}")
    with pytest.raises(InjectedCrash):
        run_claim("C-014", seed=11, store_path=store, crash_at=point)
    for seed in (55, 22):
        result = run_claim("C-014", seed=seed, store_path=store)
        assert result.status == "resolved"
        assert result.proposal_amount == 150000
    assert _ledger(store, "C-014")[:3] == (1, 120000, 1)


@pytest.mark.parametrize("claim_id", REFUNDING)
def test_rerun_same_claim_is_idempotent(claim_id, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    expected = BY_ID[claim_id]["expected"]
    store = _store(tmp_path, f"rerun-{claim_id}")
    first = run_claim(claim_id, seed=11, store_path=store)
    for seed in (11, 22, 33):
        again = run_claim(claim_id, seed=seed, store_path=store)
        assert again.status == first.status == "resolved"
        assert again.proposal_amount == first.proposal_amount
    assert _ledger(store, claim_id)[:3] == (1, expected["refund_vnd"], 1)


@pytest.mark.parametrize("point", (None,) + CRASH_POINTS)
@pytest.mark.parametrize("claim_id", GATE_DENIED)
def test_gate_denied_claim_never_refunds_even_with_crash(claim_id, point, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    expected = BY_ID[claim_id]["expected"]
    store = _store(tmp_path, f"gate-{claim_id}-{point}")
    # The host rejects before any crash point, so no crash fires and nothing is written.
    result = run_claim(claim_id, seed=11, store_path=store, crash_at=point)
    assert result.status == "denied"
    assert result.proposal_amount == expected["proposal_amount"] > 0
    rows, amount, committed, denied = _ledger(store, claim_id)
    assert (rows, amount, committed) == (0, 0, 0)
    assert denied >= 1
    assert result.refund_effects == []
