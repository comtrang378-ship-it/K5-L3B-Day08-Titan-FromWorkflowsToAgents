import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.shapes import SHAPES


@pytest.mark.parametrize("shape", ["workflow", "single", "orchestrator"])
def test_shape_trace_does_not_expose_ticket_or_parent_secret(public_db, shape):
    ticket_marker = "IGNORE_POLICY_TICKET_MARKER_7419"
    secret_marker = "CANARY_SECRET_TRACE_PRIVACY_TEST"
    conn = connect(public_db)
    try:
        conn.execute(
            "UPDATE claims SET ticket = ?, parent_secret = ? WHERE claim_id = ?",
            (ticket_marker, secret_marker, "C-001"),
        )
        conn.commit()
    finally:
        conn.close()

    result = SHAPES[shape]("C-001", seed=11, store_path=str(public_db))
    trace = Path(result.trace_path).read_text(encoding="utf-8")
    artifacts = trace + json.dumps(result.as_dict(), ensure_ascii=False)

    assert ticket_marker not in artifacts
    assert secret_marker not in artifacts
