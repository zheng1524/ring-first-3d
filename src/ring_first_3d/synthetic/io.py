import json
from pathlib import Path
import numpy as np
from ..contracts.identities import sha256
from ..policy.contracts import require
from ..policy.artifacts import load_attempt


def outputs(attempt,payload):
    files={str(p.relative_to(attempt)):dict(sha256=sha256(p),bytes=p.stat().st_size)for p in sorted(attempt.rglob("*"))if p.is_file() and "runtime" not in p.relative_to(attempt).parts and p.name not in {"stdout.txt","stderr.txt","worker.json","request.json","payload.json","result.json"}}
    return dict(payload,files=files)


def stage_record(root,stage):
    state=json.loads((root/"RUN_MANIFEST.json").read_text())
    records=[r for r in state["attempts"]if f"-{stage}-" in r["path"]]
    require(records,"PREDECESSOR_FAILED",stage)
    result=load_attempt(root,records[-1]);require(result["status"]=="PASS","PREDECESSOR_FAILED",stage)
    return root/"attempts"/result["attempt_id"],result["payload"]


def fetch(root,stage,name):
    folder,payload=stage_record(root,stage);p=folder/name
    rec=payload["files"][name]
    require(p.is_file() and sha256(p)==rec["sha256"] and p.stat().st_size==rec["bytes"],"SOURCE_SHA",name)
    return p


def save_json(path,value):
    from ..evaluation.validation import clean
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(value),indent=2,allow_nan=False)+"\n")
