"""Atomic scientific publication and mandatory exact-mesh-section checks."""
import json,shutil,re
from ..policy.artifacts import write_json
from ..policy.contracts import require
from ..contracts.identities import sha256


def enhance(root,task,state,latest,pending):
    metrics=json.loads((pending/'metrics.json').read_text());metrics.update(engineering_only=False,profile='MULTISURFACE_BODY_FUSION',GT_read='G0_views_noise'in latest,history_prediction_fallback=0,new_scientific_predictions=int('G4_fusion_predict'in latest),camera_optimization=False)
    for stage in ['fusion_regression','G0_views_noise','G1_body','G2_candidates','G3_smoke_evaluate','G3_all_predict','G4_fusion_predict','G4_evaluate']:
        if stage in latest and latest[stage]['status']=='PASS':metrics[stage]=latest[stage]['payload']
    files={};row=latest.get('G4_visualize')
    if row and row['status']=='PASS':
        folder=root/'attempts'/row['attempt_id'];payload=row['payload']
        for name,rec in payload['files'].items():
            p=folder/name;require(p.resolve().is_relative_to(folder)and p.is_file()and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
            if p.suffix not in {'.png','.html','.js','.json','.csv','.md'}:continue
            target=pending/name if name in {'TECHNICAL_REPORT.md','RESULT_CARD.md'}else pending/'visualization'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
            files[str(target.relative_to(pending))]=dict(sha256=sha256(target),bytes=target.stat().st_size)
        f=json.loads((pending/'failures.json').read_text());f['scientific_failures']=payload['scientific_failures'];(pending/'failures.json').unlink();write_json(pending/'failures.json',f);state['scientific_acceptance']='AWAITING_HUMAN_REVIEW'
    else:
        for name in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:
            p=pending/name;p.write_text(p.read_text().replace('No new scientific predictions; GT not read;','Multisurface experiment in progress; explicit generator/evaluator GT access;'))
    state['multisurface_files']=files;(pending/'metrics.json').unlink();write_json(pending/'metrics.json',metrics)


def validate(root,state):
    files=state.get('multisurface_files',{})
    for name,rec in files.items():
        p=root/name;require(p.resolve().is_relative_to(root)and p.is_file()and sha256(p)==rec['sha256']and p.stat().st_size==rec['bytes'],'ARTIFACT_MISSING',name)
    if any('-G4_visualize-'in r['path']for r in state['attempts']):
        require({'visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png','visualization/multisurface_3d.html','visualization/data.js','visualization/cases/C3_E1.js','visualization/SURFACE_OWNERSHIP_MAIN.csv','visualization/NOISE_AUDIT.json','visualization/REGISTRATION_METRICS.json','visualization/MODEL_METRICS.json','visualization/FAILURE_LEDGER.json'}<=set(files),'ARTIFACT_MISSING','Actual full Mesh cuts, per-view interactive and ownership required')
        report=(root/'TECHNICAL_REPORT.md').read_text();first=re.search(r'!\[[^\]]*\]\(([^)]+)\)',report)
        require(first and first.group(1)=='visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png','MAIN_FIGURE','First scientific figure must be actual multisurface Mesh sections')
        page=(root/'visualization/index.html').read_text();require(page.index('01_MAIN_MULTISURFACE_SECTIONS.png')<page.index('../evidence.png'),'MAIN_FIGURE','No historical figure before main scientific cut')
