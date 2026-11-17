"""Reuse atomic policy snapshots; failed C0 still delivers measured PNG evidence."""
import json,shutil
from .contracts import require
from ..contracts.identities import sha256


def enhance(root,task,state,latest,pending):
    metrics=json.loads((pending/'metrics.json').read_text());metrics.update(engineering_only=False,new_scientific_predictions=int('G1_C0_update' in latest),GT_read='G2_C0_evaluate' in latest,history_prediction_fallback=0)
    files={};row=latest.get('G4_visualize') or latest.get('G3_C0_visualize')
    if row and row['status']=='PASS':
        folder=root/'attempts'/row['attempt_id']
        for name,rec in row['payload']['files'].items():
            p=folder/name
            if p.suffix not in {'.png','.glb','.json','.npz','.md','.html','.csv'}:continue
            require(p.is_file() and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
            dst=pending/name if name in {'TECHNICAL_REPORT.md','RESULT_CARD.md'} else pending/'visualization'/name
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);files[str(dst.relative_to(pending))]=dict(sha256=sha256(dst),bytes=dst.stat().st_size)
        failures=json.loads((pending/'failures.json').read_text());failures['scientific_failures']=row['payload']['scientific_failures'];(pending/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
        metrics.update(C0_scientific_pass=row['payload']['scientific_pass'],real_status=row['payload']['real_status'])
    else:
        (pending/'visualization/index.html').write_text('<!doctype html><meta charset="utf-8"><p>Structural task preparation; scientific PNGs not generated yet.</p><a href="../RESULT_CARD.md">Current result</a>')
    state['structural_files']=files;(pending/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')


def validate(root,state):
    files=state.get('structural_files',{})
    for n,r in files.items():
        p=root/n;require(p.is_file() and sha256(p)==r['sha256'] and p.stat().st_size==r['bytes'],'ARTIFACT_MISSING',n)
    if any('-G3_C0_visualize-' in r['path'] for r in state['attempts']):
        require({'visualization/figures/C0_BODY_3D.png','visualization/figures/C0_DEFORMATION_GROWTH.png','visualization/figures/C0_ACTUAL_MESH_SECTIONS.png','visualization/C0_METRICS.json','visualization/INITIALIZATION_AUDIT.json','visualization/FAILURE_REGISTRY.json'}<=set(files),'ARTIFACT_MISSING','Actual scientific PNGs and failures required')
