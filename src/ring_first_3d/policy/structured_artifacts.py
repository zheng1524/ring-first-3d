"""Publish small scientific reports/figures, leave full phase arrays immutable."""
import json,shutil
from .contracts import require
from ..contracts.identities import sha256

def enhance(root,t,state,latest,pending):
    row=latest.get('G4_visualize');files={}
    if row and row['status']=='PASS':
        folder=root/'attempts'/row['attempt_id']
        for name,rec in row['payload']['files'].items():
            if name in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:dst=pending/name
            elif name.startswith('figures/')or name in ['index.html','FAILURE_REGISTRY.json','SUMMARY.json']:dst=pending/'visualization'/name
            else:continue
            src=folder/name;require(src.is_file()and sha256(src)==rec['sha256'],'ARTIFACT_SHA',name);dst.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,dst);files[str(dst.relative_to(pending))]=dict(sha256=sha256(dst),bytes=dst.stat().st_size)
        f=json.loads((pending/'failures.json').read_text());f['scientific_failures']=row['payload'].get('scientific_failures',[]);(pending/'failures.json').write_text(json.dumps(f,indent=2)+'\n')
    else:(pending/'visualization/index.html').write_text('<!doctype html><meta charset="utf-8"><p>Structured body pilot: stages not yet complete.</p><a href="../RESULT_CARD.md">Result card</a>')
    metrics=json.loads((pending/'metrics.json').read_text());metrics.update(engineering_only=False,new_scientific_predictions=sum(len(x['payload'].get('records',[]))for k,x in latest.items()if k.startswith('G1_')),GT_read='G2_evaluate'in latest,GT_used_for_prediction=False,HERO_read=False,scientific_acceptance='AWAITING_HUMAN_REVIEW');(pending/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    state['structured_files']=files

def validate(root,state):
    for name,rec in state.get('structured_files',{}).items():require((root/name).is_file()and sha256(root/name)==rec['sha256'],'ARTIFACT_MISSING',name)
    if any('-G4_visualize-'in x['path']for x in state['attempts']):require({'visualization/figures/G01_BODY.png','visualization/figures/G03_BODY.png','visualization/figures/G05_BODY.png','visualization/FAILURE_REGISTRY.json'}<=set(state['structured_files']),'ARTIFACT_MISSING','All three actual cases and failures')
