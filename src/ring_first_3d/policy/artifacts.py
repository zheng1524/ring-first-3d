"""Immutable snapshots and atomic current pointer, including failed attempts."""
import html
import json
import os
from pathlib import Path
import shutil
import uuid
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from .contracts import STAGES, canonical, digest, require, stages_for
from ..contracts.identities import sha256

ALIASES = ("RUN_MANIFEST.json", "RESULT_CARD.md", "TECHNICAL_REPORT.md", "metrics.json", "failures.json", "visualization", "evidence.png")


def write_json(path, value):
    path=Path(path)
    data=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    temporary=path.with_name(".atomic-"+uuid.uuid4().hex)
    try:
        with temporary.open("x") as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.link(temporary,path)  # Atomic publication, fails if historical path exists.
    finally:
        temporary.unlink(missing_ok=True)


def read_state(root):
    p = Path(root) / "RUN_MANIFEST.json"
    require(p.is_file(), "STATE_MISSING", str(p))
    state = json.loads(p.read_text())
    require(state["schema"] == 1, "STATE_INVALID", "Unknown run state")
    return state


def load_attempt(root, rec):
    p = Path(root) / rec["path"]
    require(p.resolve().is_relative_to(Path(root).resolve() / "attempts"), "ARTIFACT_PATH", str(p))
    require(p.is_file() and sha256(p) == rec["sha256"], "ATTEMPT_SHA", str(p))
    return json.loads(p.read_text())


def heads(root, state):
    rows = [load_attempt(root, r) for r in state["attempts"]]
    result = {}
    for row in rows:
        require(row["freeze_sha256"] == state["freeze_sha256"], "ATTEMPT_IDENTITY", "Attempt belongs to another freeze")
        result[row["stage"]] = row
    return result


def publish(root, task, state):
    stages=stages_for(task)
    root = Path(root)
    snapshot_id = f"{len(state['attempts']):04d}-{uuid.uuid4().hex[:12]}"
    snapshots = root / "snapshots"
    snapshots.mkdir(exist_ok=True)
    pending = snapshots / (".pending-" + snapshot_id)
    pending.mkdir()
    image = root / "assets/evidence.png"
    if not image.exists():
        image.parent.mkdir(exist_ok=True)
        shutil.copyfile(task["inputs"]["evidence"]["path"], image)
    require(sha256(image) == task["inputs"]["evidence"]["sha256"], "EVIDENCE_SHA", str(image))
    (pending / "evidence.png").symlink_to("../../assets/evidence.png")
    rows = [load_attempt(root, r) for r in state["attempts"]]
    latest = heads(root, state)
    failures = [dict(attempt=row["attempt_id"], stage=row["stage"], status=row["status"],
                     category="engineering_gate", reason=row.get("reason", ""),
                     evidence=f"attempts/{row['attempt_id']}/result.json") for row in rows if row["status"] != "PASS"]
    metrics = dict(engineering_only=True, new_scientific_predictions=0, GT_read=False,
                   history_prediction_fallback=0, durations_seconds={r["attempt_id"]: r["seconds"] for r in rows},
                   stages={s: latest[s]["status"] if s in latest else "NOT_RUN" for s in stages},
                   spent_seconds=state["spent_seconds"])
    write_json(pending / "metrics.json", metrics)
    write_json(pending / "failures.json", dict(schema=1, failures=failures, empty_means="No failed attempts recorded, not scientific success"))
    table = "\n".join(f"| {s} | {metrics['stages'][s]} |" for s in stages)
    status = "GATES_PASSED" if all(v == "PASS" for v in metrics["stages"].values()) else "INCOMPLETE_OR_FAILED"
    if status=="GATES_PASSED" and state.get("accepted",False):status="ACCEPTED_ENGINEERING"
    card = f"# {task['task_id']}\n\n{task['goal']}\n\nStatus: {status}; scientific acceptance: NOT_APPLICABLE.\n\n| Stage | Result |\n| --- | --- |\n{table}\n\nFailures retained: {len(failures)}. Compute seconds: {state['spent_seconds']:.4f}.\n\n[Visualization](visualization/index.html) · [Metrics](metrics.json) · [Failure evidence](failures.json)\n\nNo new scientific predictions; GT not read; historical measurement fallback 0.\n"
    (pending / "RESULT_CARD.md").write_text(card)
    report = card + "\n## Scientific audit\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | 新科学测量 0；冻结 G01 工程回归 1 |\n| 本算法独立成功 | 新科学预测 0；工程通过情况见上表 |\n| 本算法失败 | 新测量 NaN 不适用；工程失败逐次保留 |\n| 历史测量值回退 | 0 |\n| 失败组及具体原因 | failures.json 和每次 attempt 的原始输出 |\n| 最终统计样本 | 仅工程回归；误差 MAE/中位相对误差/p95/最大误差/配对比较 N/A |\n| 是否使用 GT 选择算法 | 否，固定输入/源码/授权随运行冻结 |\n\nEvidence image is the registered previous real regression figure; current stage outcomes and timings are from this run. It is not a new body reconstruction.\n"
    (pending / "TECHNICAL_REPORT.md").write_text(report)
    vis = pending / "visualization"
    vis.mkdir()
    bars = []
    for i, row in enumerate(rows):
        width = min(500, max(2, row["seconds"] * 12))
        color = "#24a878" if row["status"] == "PASS" else "#df6b54"
        bars.append(f'<text x="0" y="{i*30+17}">{html.escape(row["stage"])} {html.escape(row["status"])}</text><rect x="200" y="{i*30+2}" width="{width:.2f}" height="20" fill="{color}"/><text x="{205+width}" y="{i*30+17}">{row["seconds"]:.3f}s</text>')
    body = f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{html.escape(task["task_id"])}</title><style>body{{font:16px system-ui;max-width:1100px;margin:32px auto;background:#f7f9fc;color:#172333}}img{{max-width:100%}}svg{{background:white}}a{{color:#215db0}}pre{{white-space:pre-wrap}}</style><h1>{html.escape(task["task_id"])}</h1><p>{html.escape(task["goal"])}</p><p>{status}. Engineering verification only; GT not read.</p><svg role="img" aria-label="Actual stage status and duration" viewBox="0 0 850 {max(40,len(rows)*30)}">{"".join(bars)}</svg><p><a href="../RESULT_CARD.md">Result card</a> · <a href="../metrics.json">Actual metrics</a> · <a href="../failures.json">Failure evidence</a> · <a href="../RUN_MANIFEST.json">Frozen manifest</a></p><h2>Registered real regression evidence</h2><p>Historical input / inferred candidate / fixed metric projection; not a new scientific result. Current verification outcomes are above.</p><img src="../evidence.png" alt="Frozen G01 real regression evidence"><h2>Retained failed attempts</h2><pre>{html.escape(json.dumps(failures,ensure_ascii=False,indent=2))}</pre></html>'
    (vis / "index.html").write_text(body)
    if task.get("schema")==2:
        from ..synthetic.artifacts import enhance
        enhance(root,task,state,latest,pending)
    if task.get("schema")==3:
        from ..dualvideo.artifacts import enhance
        enhance(root,task,state,latest,pending)
    if task.get("schema")==4:
        from ..sim.artifacts import enhance
        enhance(root,task,state,latest,pending)
    state = dict(state, snapshot=snapshot_id, task_id=task["task_id"], status=status)
    names = ["RESULT_CARD.md", "TECHNICAL_REPORT.md", "metrics.json", "failures.json", "visualization/index.html", "evidence.png"]
    state["artifacts"] = {name: dict(path=f"snapshots/{snapshot_id}/{name}", sha256=sha256(pending/name), bytes=(pending/name).stat().st_size) for name in names}
    write_json(pending / "RUN_MANIFEST.json", state)
    pending.rename(snapshots / snapshot_id)
    pointer = root / (".current-" + uuid.uuid4().hex)
    pointer.symlink_to("snapshots/" + snapshot_id)
    os.replace(pointer, root / "current")  # One atomic pointer selects the complete snapshot.
    for name in ALIASES:
        alias = root / name
        if not alias.is_symlink() and not alias.exists():
            alias.symlink_to("current/" + name)
        require(alias.is_symlink() and os.readlink(alias) == "current/" + name, "ARTIFACT_ALIAS", name)
    fd = os.open(root, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return state


def check_artifacts(root, state):
    root = Path(root).resolve()
    require((root / "current").resolve() == root / "snapshots" / state["snapshot"], "ARTIFACT_PATH", "Current snapshot mismatch")
    required = {"RESULT_CARD.md", "TECHNICAL_REPORT.md", "metrics.json", "failures.json", "visualization/index.html", "evidence.png"}
    require(set(state["artifacts"]) == required, "ARTIFACT_MISSING", "Required artifact set differs")
    for name in required:
        rec = state["artifacts"][name]
        p = root / rec["path"]
        require(p.resolve().is_relative_to(root) and p.is_file(), "ARTIFACT_MISSING", name)
        require(p.stat().st_size == rec["bytes"] and sha256(p) == rec["sha256"], "ARTIFACT_SHA", name)
        require((root / name).is_file() and (root / name).resolve() == p.resolve(), "ARTIFACT_MISSING", "Public path " + name)
    require((root/"evidence.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "VISUALIZATION", "Real PNG evidence required")
    page = (root/"visualization/index.html").read_text()
    require("<svg" in page and '<img src="../evidence.png"' in page, "VISUALIZATION", "Status visualization and real evidence required")
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ("href","src") and value and not value.startswith("#"):
                    u=urlsplit(value)
                    require(not u.scheme and not u.netloc,"ARTIFACT_PATH","Local visualization references only")
                    p=(root/"visualization"/unquote(u.path)).resolve()
                    require(p.is_relative_to(root) and p.is_file(),"ARTIFACT_MISSING",value)
    Links().feed(page)
    metrics = json.loads((root/"metrics.json").read_text())
    if state.get("task_id")not in {"TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001","TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001","TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1"}:
        require(metrics["GT_read"] is False and metrics["history_prediction_fallback"] == 0 and metrics["new_scientific_predictions"] == 0, "GT_LEAK", "Unexpected scientific output")
    failures = json.loads((root/"failures.json").read_text())
    rows = [load_attempt(root, r) for r in state["attempts"]]
    require(len(failures["failures"]) == sum(r["status"] != "PASS" for r in rows), "FAILURE_LOG", "Failures omitted")
    require(all((root/f["evidence"]).is_file() for f in failures["failures"]), "FAILURE_LOG", "Missing failure evidence")
    if state.get("task_id")=="TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001":
        from ..synthetic.artifacts import validate_scientific_artifacts
        validate_scientific_artifacts(root,state)
    if state.get("task_id")=="TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001":
        from ..dualvideo.artifacts import validate_artifacts
        validate_artifacts(root,state)
    if state.get("task_id")=="TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1":
        from ..sim.artifacts import validate
        validate(root,state)
    return dict(status="PASS", verified_paths=len(required), visualization=str(root/"visualization/index.html"))
