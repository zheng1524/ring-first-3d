"""Publish verified scene-failure evidence without accepting a failed gate."""
import html,json,shutil
from pathlib import Path
from ..contracts.identities import sha256
from ..policy.contracts import require
from ..policy.artifacts import write_json


def enhance(root,task,state,latest,pending):
    row=latest.get('G0_scene_audit')
    status='G0_NOT_RUN' if not row else 'STOPPED_AT_G0'if row['status']!='PASS'else'G0_PASSED_DOWNSTREAM_PENDING'
    metric=json.loads((pending/'metrics.json').read_text())
    metric.update(task_profile='dualvideo_scene_gate',GT_read=bool(row and (root/'attempts'/row['attempt_id']/'BLENDER_SCENE_INVENTORY.json').exists()),
        independent_registration_success=0,target_groups=1,failed_groups=1 if row and row['status']!='PASS'else 0,
        registration_metrics=None,all_conditions={s:'NOT_RUN'for s in task['dualvideo']['condition_order']},injection_performed=False)
    detail={};files={};vis=pending/'visualization'
    if row:
        folder=root/'attempts'/row['attempt_id'];payload=folder/'payload.json'
        if payload.exists():
            require(sha256(payload)==row['raw_files'].get('payload.json'),'ARTIFACT_SHA','Failed G0 payload')
            value=json.loads(payload.read_text())
            for name,rec in value.get('files',{}).items():
                p=folder/name
                require(p.resolve().is_relative_to(folder)and p.is_file()and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
                if p.suffix in {'.json','.png','.html'}:
                    out=vis/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
                    files[name]=dict(sha256=sha256(out),bytes=out.stat().st_size)
            p=folder/'G0_SCENE_METRICS.json'
            if p.exists():
                detail=json.loads(p.read_text());metric['G0']=detail
    state['dualvideo_files']=files
    (pending/'metrics.json').unlink();write_json(pending/'metrics.json',metric)
    failures=detail.get('failures',[])
    audit='''\n| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | G01：1；视频004/005各1；冻结33帧（25 FIT / 8 HOLDOUT） |
| 本算法独立成功 | Body初始化/完整局部Mesh配准 0/1；G0逐帧核验见指标 |
| 本算法失败 | G0未通过；G1–G4未运行，预测及配准误差 NaN |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | G01；见下方逐项失败与链接证据 |
| 最终统计样本 | 配准独立成功 0/1；MAE/相对误差/p95/最大误差/配对比较 N/A |
| 是否使用 GT 选择算法 | 否；TASK及源码先冻结；GT仅用于G0来源真实性核验，未生成预测 |
'''
    text=f"# {task['task_id']}\n\nStatus: {status}. Task acceptance: NOT_ACCEPTED.\n\n"
    text+='G0检查真实来源与原生Camera-to-Ring；004与005保留独立Ring坐标系。原始Blender只证明真实形状，不自动证明部署位姿。未进行误差注入。G1–G4、S0–S4全部NOT_RUN。\n\n'
    text+='[本地可视化](visualization/index.html) · [完整指标](metrics.json) · [运行清单](RUN_MANIFEST.json)\n\n'
    text+=audit+'\n'
    if detail:
        text+='| Video | Frames | Projection gate pass | Support@2px median | Boundary p95 median px |\n| --- | ---: | ---: | ---: | ---: |\n'
        for video,r in detail['summary'].items():text+=f"| {video} | {r['frames']} | {r['passed']} | {r['support_median']:.6f} | {r['boundary_p95_median_px']:.6f} |\n"
        text+='\nFull CAD IoU仅作诊断。遮挡边缘也会影响边界p95；未据此调参或替换相机。所有未匹配区域均保留。\n\n'
    for f in failures:text+=f"- {f.get('source_id','G01')} / `{f['code']}`: {f['reason']} [证据](visualization/{f['evidence']})\n"
    text+='\n每帧RGB/Mask/相机/Ring来源SHA、投影指标及缓存修正位姿差异详见G0_SCENE_METRICS.json和冻结输入清单。无扰动条件亦未作为配准实验运行。\n\n'
    text+='必须补充与真实004、005轨迹关联的Body-to-Ring固定部署变换凭据，并解决冻结原生相机的Ring投影门禁，重新冻结后才能开展初始化、映射和配准。不能用Oracle刚体对齐补齐该凭据。\n'
    if not row:text=text.replace('G0未通过','G0尚未运行')
    for name in ['RESULT_CARD.md','TECHNICAL_REPORT.md']:(pending/name).write_text(text)
    page=(vis/'index.html').read_text().replace('GT not read.','GT access restricted to source authenticity auditor.').replace('Engineering verification only;','Authenticity gate;')
    extra=f'<h2>{status}</h2><p>G1–G4 / S0–S4: NOT_RUN. No injection, initialization or registration. Separate native Ring frames; no certified Body deployment pose.</p>'
    for name in ['scene.html','G0_SCENE_METRICS.json','BLENDER_SCENE_INVENTORY.json','BODY_RING_POSE_CERTIFICATE_AUDIT.json']:
        if name in files:extra+=f'<p><a href="{name}">{name}</a></p>'
    for r in detail.get('rows',[]):
        extra+=f'<h3>{html.escape(r["source_id"])} | {r["role"]} | {r["projection_gate"]}</h3><p>Support@2px {r["support_within2px"]:.6f}; boundary p95 {r["observed_to_CAD_boundary_p95_px"]:.6f}px; no injection. Source/pose SHA in metrics.</p><img loading="lazy" src="{r["figure"]}" alt="Actual native Ring projection and unmatched observed regions">'
    page=page.replace('<h2>Registered real regression evidence</h2>',extra+'<h2>Historical engineering reference (not this experiment)</h2>')
    (vis/'index.html').write_text(page)


def validate_artifacts(root,state):
    for name,rec in state.get('dualvideo_files',{}).items():
        p=root/'visualization'/name
        require(p.resolve().is_relative_to(root)and p.is_file()and sha256(p)==rec['sha256']and p.stat().st_size==rec['bytes'],'ARTIFACT_MISSING',name)
    latest=[r for r in state['attempts']if '-G0_scene_audit-'in r['path']]
    if latest:
        from ..policy.artifacts import load_attempt
        row=load_attempt(root,latest[-1])
        if 'payload.json'in row.get('raw_files',{}):
            require({'scene.html','G0_SCENE_METRICS.json','BODY_RING_POSE_CERTIFICATE_AUDIT.json','BLENDER_SCENE_INVENTORY.json'}<=set(state.get('dualvideo_files',{})),'ARTIFACT_MISSING','G0 actual scene evidence')
