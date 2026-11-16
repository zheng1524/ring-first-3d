"""Failure facts are advisory memory; only explicitly reviewed rules may be permanent."""
import json
from pathlib import Path
from .contracts import ROOT, require, fields
from ..contracts.identities import sha256


def registry(path=None):
    value = json.loads(Path(path or ROOT / "docs/registry/FAILURE_REGISTRY.json").read_text())
    require(value["schema"] == 1 and type(value["failures"]) is list, "FAILURE_MEMORY", "Invalid registry")
    seen = set()
    for row in value["failures"]:
        fields(row, "id category modules symptom cause cause_status repair regression evidence rule_status review", "failure row")
        require(row["id"] not in seen, "FAILURE_MEMORY", "Duplicate ID")
        seen.add(row["id"])
        require(row["category"] in ["code_error", "environment_error", "data_identity_error", "scientific_negative", "incomplete_evaluation"], "FAILURE_MEMORY", row["id"])
        require(row["cause_status"] in ["confirmed", "observed_only"], "FAILURE_MEMORY", "Do not promote suspected causes")
        require(row["evidence"] and row["regression"] and row["repair"], "FAILURE_MEMORY", "Evidence/repair/regression required")
        for item in row["evidence"]:
            if isinstance(item,dict):
                fields(item,"path sha256","local failure evidence")
                p=(ROOT/item["path"]).resolve()
                require(p.is_relative_to(ROOT) and p.is_file() and sha256(p)==item["sha256"],"FAILURE_MEMORY","Local evidence missing or changed")
            else:
                require(isinstance(item,str) and "/blob/" in item,"FAILURE_MEMORY","Historical evidence must pin a blob commit")
        require(row["rule_status"] in ["candidate", "reviewed_permanent"], "FAILURE_MEMORY", "Unknown rule status")
        if row["rule_status"] == "reviewed_permanent":
            require(row["review"].get("status") == "approved" and row["review"].get("reviewer") and row["review"].get("evidence"), "UNREVIEWED_RULE", row["id"])
    return value
