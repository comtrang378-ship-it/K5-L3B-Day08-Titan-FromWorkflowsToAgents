import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.shapes import SHAPES


@pytest.mark.parametrize("shape", ["workflow", "single", "orchestrator"])
def test_shape_trace_and_stdout_do_not_expose_raw_claim_or_order(public_db, shape, capsys):
    ticket_marker = "IGNORE_POLICY_TICKET_MARKER_7419"
    secret_marker = "CANARY_SECRET_TRACE_PRIVACY_TEST"
    private_order_markers = (
        "PHONE_TRACE_PRIVACY_TEST",
        "ADDRESS_TRACE_PRIVACY_TEST",
        "NOTE_TRACE_PRIVACY_TEST",
        "ITEM_TRACE_PRIVACY_TEST",
    )
    conn = connect(public_db)
    try:
        conn.execute(
            "UPDATE claims SET ticket = ?, parent_secret = ? WHERE claim_id = ?",
            (ticket_marker, secret_marker, "C-001"),
        )
        conn.execute(
            """
            UPDATE orders
            SET phone = ?, address = ?, internal_note = ?, item_name = ?
            WHERE order_id = 'O-107'
            """,
            private_order_markers,
        )
        conn.commit()
    finally:
        conn.close()

    result = SHAPES[shape]("C-001", seed=11, store_path=str(public_db))
    trace = Path(result.trace_path).read_text(encoding="utf-8")
    artifacts = trace + json.dumps(result.as_dict(), ensure_ascii=False)
    stdout = capsys.readouterr().out

    for marker in (ticket_marker, secret_marker, *private_order_markers):
        assert marker not in artifacts
        assert marker not in stdout
