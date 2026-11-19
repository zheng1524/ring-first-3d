"""Atomic publication/checks for actual simulation scientific artifacts."""
import json,shutil
from ..policy.contracts import require
from ..policy.artifacts import write_json
from ..contracts.identities import sha256


def enhance(root,task,state,latest,pending):
    metric=json.loads((pending/'metrics.json').read_text());metric.update(engineering_only=False,profile='SIM_PROTOCOL_REV1',label='G01_LIKE_SIMULATION',proxy='SYNTHETIC_HERO_PROXY',history_prediction_fallback=0)
    metric['GT_read']=any(k in latest for k in ['G0_simulate','G1_evaluate']);metric['new_scientific_predictions']=int('G3_matrix_predict'in latest)
    for stage in ['G0_simulate','G1_initialize','G1_evaluate','G2_evaluate','G3_smoke_evaluate','G3_matrix_predict','G4_evaluate']:
        if stage in latest and latest[stage]['status']=='PASS':metric[stage]=latest[stage]['payload']
    row=latest.get('G4_visualize');files={}
    if row and row['status']=='PASS':
        folder=root/'attempts'/row['attempt_id'];payload=row['payload']
        for name,rec in payload['files'].items():
            p=folder/name;require(p.resolve().is_relative_to(folder)and p.is_file()and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
            if p.suffix not in {'.png','.html','.json','.csv','.md'}:continue
            target=pending/name if name in {'TECHNICAL_REPORT.md','RESULT_CARD.md'}else pending/'visualization'/name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
            files[str(target.relative_to(pending))]=dict(sha256=sha256(target),bytes=target.stat().st_size)
        state['scientific_acceptance']='AWAITING_HUMAN_REVIEW'
        f=json.loads((pending/'failures.json').read_text());f['scientific_failures']=payload['scientific_failures'];(pending/'failures.json').unlink();write_json(pending/'failures.json',f)
    else:
        for name in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:
            p=pending/name;p.write_text(p.read_text().replace('No new scientific predictions; GT not read;','SIM_PROTOCOL_REV1 in progress; generator/evaluator GT access is explicit;').replace('GT not read;','GT access by registered generator/evaluator;'))
    state['sim_files']=files
    (pending/'metrics.json').unlink();write_json(pending/'metrics.json',metric)


def validate(root,state):
    for name,rec in state.get('sim_files',{}).items():
        p=root/name;require(p.resolve().is_relative_to(root)and p.is_file()and sha256(p)==rec['sha256']and p.stat().st_size==rec['bytes'],'ARTIFACT_MISSING',name)
    if any('-G4_visualize-'in r['path']for r in state['attempts']):
        require({'visualization/mesh_registration.html','visualization/REGISTRATION_METRICS.json','visualization/FAILURE_LEDGER.json','visualization/figures/S1_M2_PIPELINE_front.png','visualization/figures/S1_M2_PIPELINE_side.png','visualization/figures/S1_M2_PIPELINE_top.png'}<=set(state.get('sim_files',{})),'ARTIFACT_MISSING','Mandatory actual full-mesh scientific deliverables')
