import html
import json
from pathlib import Path
import shutil
from .io import fetch,stage_record
from ..contracts.identities import sha256
from ..policy.contracts import require


def enhance(root,task,state,latest,pending):
    metrics=json.loads((pending/"metrics.json").read_text())
    metrics.update(experiment="controlled_real_G01_correspondence",new_scientific_predictions=0,GT_read="G0_prepare"in latest,GT_read_by_generator_or_evaluator="G0_prepare"in latest,
        GT_read_by_predictor=False,body_updates=0,condition_order=["C0","C1","C3"],scientific_acceptance="AWAITING_HUMAN_REVIEW")
    body="<h1>G01 controlled correspondence | G0–G1 only</h1><p>Real original Blender G01, R10 CAD, frozen cameras; synthetic author-world pose. No Body update.</p>"
    if "G1_visualize"in latest and latest["G1_visualize"]["status"]=="PASS":
        record=latest["G1_visualize"];folder=root/"attempts"/record["attempt_id"];payload=record["payload"];figure_files={};cards=[]
        def get_file(name):
            p=folder/name;rec=payload["files"][name]
            require(p.is_file()and sha256(p)==rec["sha256"],"ARTIFACT_SHA",name)
            return p
        for name,title in payload["figures"].items():
            src=get_file("figures/"+name);dest=pending/"visualization"/name;shutil.copyfile(src,dest)
            figure_files[name]=dict(sha256=sha256(dest),bytes=dest.stat().st_size)
            cards.append(f'<section><h2>{html.escape(title)}</h2><a href="{name}"><img style="width:100%" src="{name}" alt="{html.escape(title)}"></a></section>')
        shutil.copyfile(get_file("PIXEL_FACE_AUDIT.csv"),pending/"visualization/PIXEL_FACE_AUDIT.csv")
        figure_files["PIXEL_FACE_AUDIT.csv"]=dict(sha256=sha256(pending/"visualization/PIXEL_FACE_AUDIT.csv"),bytes=(pending/"visualization/PIXEL_FACE_AUDIT.csv").stat().st_size)
        # Replace only the not-yet-published snapshot link; historical assets persist.
        (pending/"evidence.png").unlink();shutil.copyfile(get_file("figures/01_scene.png"),pending/"evidence.png")
        state["scientific_figures"]=figure_files
        metrics["correspondence_rows"]=payload["rows"]
        metrics["unmatched_targets"]=sum(r["failed_N"]for r in payload["rows"]if not r["oracle"])
        body+='<p><a href="PIXEL_FACE_AUDIT.csv">Actual pixel / face / barycentric / XYZ audit CSV</a> · <a href="../metrics.json">Metrics with full denominators</a></p>'+"".join(cards)
    else:body+="<p>Preparation/execution incomplete. No actual scientific figure is claimed yet.</p>"
    body+="<p>Magenta means unmatched observed target. Gray means true Ring-occluded Body; not an observable contour. Oracle is evaluation-only. No optimization or error correction was executed.</p>"
    # Keep baseline validator's explicit real evidence and stage SVG contract.
    original=(pending/"visualization/index.html").read_text()
    original=original.split("<h2>Registered real regression evidence</h2>")[0]+body+'<h2>Actual G01 scene evidence</h2><img src="../evidence.png" alt="Fresh actual G01/Ring/camera control scene"><p><a href="../RESULT_CARD.md">Result card</a> · <a href="../failures.json">Execution failures</a></p></html>'
    (pending/"visualization/index.html").write_text(original)
    (pending/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    note="\n## G0–G1 scientific scope\n\nTrue G01 mesh-derived synthetic initial Body; no deployment-pose certification. GT reads restricted to generator/evaluator. Practical predictions are frozen before evaluation; no Body update. Independent Oracle is diagnostic only.\n"
    audit="\n## 科研审计固定表\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | 1 个真实 G01，3 条件 × 4 个相关视角；完整像素分母见 metrics.json |\n| 本算法独立成功 | 各实用方法独立产生对应，数值覆盖率见 metrics；不是独立 Body 重建成功 |\n| 本算法失败 | 未匹配点保留 NaN；各条件/视角/方法失败数均保留，不用成功子集冒充全体 |\n| 历史测量值回退 | 0；无 S0/V2/历史直径回退 |\n| 失败组及具体原因 | G01 对应失败按射线无交点、CAD 遮挡拒绝列于 metrics 和可视化；执行失败见 failures.json |\n| 最终统计样本 | 仅各方法独立匹配点统计误差，同时给全体分母；共同成功点配对见独立评价；4 视角不是4独立组 |\n| 是否使用 GT 选择算法 | 否；GT 仅用于受控初始场景生成和冻结后的独立评价，参数和算法未按 GT 误差选择 |\n\n[实际误差、覆盖率与完整分母](metrics.json) · [失败区域与物理尺度图](visualization/index.html)\n"
    for name in ["RESULT_CARD.md","TECHNICAL_REPORT.md"]:
        p=pending/name;text=p.read_text().replace("scientific acceptance: NOT_APPLICABLE","scientific acceptance: AWAITING_HUMAN_REVIEW").replace("GT not read","GT restricted to generator/evaluator")
        if name=="TECHNICAL_REPORT.md":text=text.split("## Scientific audit")[0]
        p.write_text(text+note+(audit if name=="TECHNICAL_REPORT.md"else""))


def validate_scientific_artifacts(root,state):
    metrics=json.loads((root/"metrics.json").read_text())
    require(metrics.get("GT_read_by_predictor")is False and metrics.get("body_updates")==0,"GT_LEAK","Scientific role or Body update violation")
    if "scientific_figures"in state:
        for name,rec in state["scientific_figures"].items():
            p=root/"visualization"/name
            require(p.is_file()and sha256(p)==rec["sha256"]and p.stat().st_size==rec["bytes"],"ARTIFACT_MISSING",name)
    # Verify every data file, not just top-level worker payloads.
    for rec in state["attempts"]:
        p=root/rec["path"];result=json.loads(p.read_text())
        for name,asset in result.get("payload",{}).get("files",{}).items():
            q=p.parent/name
            require(q.resolve().is_relative_to(root)and q.is_file()and sha256(q)==asset["sha256"],"ARTIFACT_SHA",name)
