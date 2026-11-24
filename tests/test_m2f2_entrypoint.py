"""The unified entrypoint must stop when its W0 inputs cannot be produced."""
import json

import pytest

from tools.m2f2_unified import run_w0


def test_missing_prepared_aborts_before_downstream(tmp_path):
    with pytest.raises(RuntimeError, match="W0_FAILED.*MISSING_PREPARED"):
        run_w0([("G_TEST", "group_that_does_not_exist")], tmp_path, "test-run")
    records = json.loads((tmp_path / "w0/W0_RUN_COMMANDS.json").read_text())
    assert len(records) == 2
    assert {row["video_id"] for row in records} == {"004", "005"}
    assert all(row["status"] == "FAIL" for row in records)
    assert all(row["run_id"] == "test-run" and row["code_version"] for row in records)
