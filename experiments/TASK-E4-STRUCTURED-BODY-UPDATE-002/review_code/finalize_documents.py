"""Bind review deliverables without altering accepted scientific artifacts."""
from pathlib import Path
import hashlib, json
TD=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')

ledger=read(TD/'FAILURE_REGISTRY.json')
for rec in ledger['records']:
    if rec.get('symptom')=='SWEEP_GATES_REJECTED':
        rec['confirmed_cause']='Actual connected candidate mesh failed persisted self-intersection and/or fresh correspondence/FIT objective gates; multiview support existed. See full per-backtrack UPDATES and retained GROWTH_PROPOSAL meshes.'
        rec['additional_evidence']=['evidence/GROWTH_DIAGNOSTICS.json','evidence/REAL_SWEEP_INTERSECTION_DIAGNOSTICS.json']
    if rec.get('symptom')=='UNDERCONSTRAINED_GROWTH':
        rec['confirmed_cause']='No candidate passed the frozen multiview support/identifiability criteria; per-view support and seed rejection reasons retained in UPDATES and GROWTH_DIAGNOSTICS.'
ledger['post_acceptance_observations']=[dict(
    type='SCIENTIFIC_NEGATIVE',symptom='RIGID_EVALUATION_SENSITIVITY',
    observed='G03 independent rigid evaluation rotations differ by about122 degrees; G05 prediction moves at most0.00004851mm while independently aligned copies differ by0.05777mm.',
    cause_status='observed_sensitivity_only',
    repair='Report fixed INITIAL-to-GT matrix / fixed material sampling diagnostic for all arms, alongside unchanged primary evaluation; never select predictions using GT.',
    evidence='evidence/ALIGNMENT_SENSITIVITY.json',permanent_rule=False,rule_status='candidate',review='unreviewed')]
ledger['review_packaging_failure']=read(TD/'evidence/REVIEW_PACKAGING_FAILURES/CAUSE.json')
ledger['review_verifier_initial_assertion_repair']=dict(
    type='ENGINEERING_ERROR',symptom='Review verifier initially expected generic PASS instead of actual Runner ACCEPTED_ENGINEERING status',
    cause_status='confirmed',repair='Assert the actual documented accepted engineering status; all other hash/geometric checks retained and passed.',
    scientific_predictions_changed=False,permanent_rule=False,rule_status='candidate')
dump(TD/'FAILURE_REGISTRY.json',ledger)
paths=[]
for folder in ['review_code','review_assets','metrics','visualization']:
    paths.extend(p for p in (TD/folder).rglob('*')if p.is_file())
paths.extend(TD/n for n in ['TASK.yaml','TASK_FREEZE.json','TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json','RUN_MANIFEST.json','WORK_STATUS.md','README.md','metrics.json'])
paths.extend(p for p in (TD/'evidence').rglob('*')if p.is_file() and 'author_reference'not in p.parts)
files={str(p.relative_to(TD)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(set(paths))}
dump(TD/'REVIEW_MANIFEST.json',dict(
    schema=1,kind='POST_ACCEPTANCE_READ_ONLY_REVIEW',
    canonical_run=str(TD/'runs/PILOT_002'),
    canonical_manifest_sha256=sha(TD/'runs/PILOT_002/RUN_MANIFEST.json'),
    frozen_prediction_source_commit=read(TD/'evidence/FINAL_PATH_VERIFICATION.json')['version']['frozen_source_commit'],
    scientific_acceptance='AWAITING_HUMAN_REVIEW',no_prediction_updates=True,files=files))
print('Review bound:',len(files),'files; no scientific artifacts modified')
