"""Orchestrator (shape C) handoff, trace and crash safety.

Student-marked like the other shape tests: run with
    python -m pytest -q -m student -o addopts= tests/test_orchestrator_handoff.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.handoff import (
    ALLOWED_FIELDS,
    FACT_KEYS,
    READONLY_TOOLS,
    HandoffError,
    make_handoff,
)
from lab8.shapes.orchestrator import run_claim
from tests.conftest import CLAIMS, WORLD

pytestmark = pytest.mark.student

SEEDS = (11, 22, 33, 44, 55)
ORDERS = {o["order_id"]: o for o in WORLD["orders"]}


def _sensitive(claim: dict) -> list[str]:
    vals = [claim["parent_secret"], json.dumps(claim["raw_headers"])]
    vals += [str(v) for v in claim["raw_headers"].values()]
    order = ORDERS.get(claim.get("order_id") or "")
    if order:
        vals += [order[k] for k in ("phone", "address", "internal_note", "item_name")]
    return [v for v in vals if v]


def test_make_handoff_drops_secrets_from_facts():
    h = make_handoff(
        request_id="REQ-1",
        claim_id="C-001",
        task="t",
        facts={
            "delay_days": 4,
            "carrier": "LOGIX_LOCAL",
            "parent_secret": "CANARY_SECRET_X",
            "phone": "0901000107",
            "address": "12 Le Loi",
            "raw_headers": {"Authorization": "Bearer CANARY_SECRET_X"},
            "note": "CANARY_SECRET_Y",
        },
        allowed_tools=["lookup_order"],
    )
    assert set(h) <= ALLOWED_FIELDS
    assert set(h["facts"]) <= FACT_KEYS
    blob = json.dumps(h)
    for bad in ("CANARY_SECRET_", "0901000107", "12 Le Loi", "parent_secret", "raw_headers"):
        assert bad not in blob


def test_make_handoff_rejects_canary_inside_allowed_fact():
    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-1",
            claim_id="C-001",
            task="t",
            facts={"carrier": "CANARY_SECRET_LEAK"},
            allowed_tools=["lookup_order"],
        )


@pytest.mark.parametrize("tool", ["issue_refund", "append_audit"])
def test_make_handoff_rejects_write_tools(tool):
    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-1",
            claim_id="C-001",
            task="t",
            facts={},
            allowed_tools=["lookup_order", tool],
        )


@pytest.mark.parametrize("claim", CLAIMS, ids=lambda c: c["claim_id"])
def test_orchestrator_trace_and_result_have_no_sensitive_values(claim, public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for seed in SEEDS:
        result = run_claim(claim["claim_id"], seed=seed, store_path=str(public_db))
        path = Path(result.trace_path)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        body = json.loads(text)
        assert body["run_id"] == result.run_id
        assert isinstance(body["events"], list)
        dumped = json.dumps(result.__dict__, default=str, ensure_ascii=False)
        for blob in (text, dumped):
            assert "CANARY_SECRET_" not in blob
            for value in _sensitive(claim):
                assert value not in blob, value
        handoffs = [e["payload"] for e in body["events"] if e["kind"] == "handoff"]
        for payload in handoffs:
            assert set(payload) <= ALLOWED_FIELDS
            assert set(payload["allowed_tools"]) <= READONLY_TOOLS
            assert set(payload["facts"]) <= FACT_KEYS


def test_orchestrator_crash_then_rerun_commits_once(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for i, point in enumerate(("before_effect", "after_effect_before_checkpoint", "after_checkpoint")):
        store = tmp_path / f"crash-{i}.sqlite"
        from lab8.db import init_store

        init_store(store, WORLD, CLAIMS).close()
        with pytest.raises(InjectedCrash):
            run_claim("C-001", seed=11, store_path=str(store), crash_at=point)
        result = run_claim("C-001", seed=11, store_path=str(store))
        assert result.status == "resolved"
        conn = connect(store)
        try:
            rows = conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id='C-001'").fetchone()[0]
            assert rows == 1
            assert get_refund(conn, "C-001")["amount_vnd"] == 35000
            assert committed_audit_count(conn, "C-001") == 1
        finally:
            conn.close()
