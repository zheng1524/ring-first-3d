"""Review packaging only. Never mutates immutable attempts or predictions."""
from pathlib import Path
import json,os,shutil,hashlib,csv,subprocess
ROOT=Path('/home/liu/ring_first_3d_structured_body_002');TD=ROOT/'experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002';run=TD/'runs/PILOT_002'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def link(src,dst):
 dst.parent.mkdir(exist_ok=True,parents=True)
 if dst.exists():
  if sha(src)==sha(dst):return
  raise RuntimeError('Review package differs: '+str(dst))
 os.link(src,dst)
state=read(run/'RUN_MANIFEST.json');assert state.get('accepted')is True
latest={}
for rr in state['attempts']:
 r=read(run/rr['path']);latest[r['stage']]=run/'attempts'/r['attempt_id']
for n in ['TECHNICAL_REPORT.md','RESULT_CARD.md','RUN_MANIFEST.json','metrics.json']:
 if n in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:
  shutil.copyfile(run/n,TD/n) # review prose may be enriched independently
 elif n=='RUN_MANIFEST.json':
  manifest=dict(state,canonical_run_dir=str(run),canonical_manifest_path=str(run/'RUN_MANIFEST.json'),canonical_manifest_sha256=sha((run/n).resolve()),relative_attempt_paths_are_relative_to=str(run));(TD/n).write_text(json.dumps(manifest,indent=2))
 else:link((run/n).resolve(),TD/n)
for p in (run/'visualization').resolve().rglob('*'):
 if p.is_file():
  target=TD/'visualization'/p.relative_to((run/'visualization').resolve());target.parent.mkdir(exist_ok=True,parents=True)
  if p.name=='index.html':shutil.copyfile(p,target)
  else:link(p,target)
(TD/'metrics').mkdir(exist_ok=True)
for p in (latest['G2_evaluate']/'metrics').glob('*.csv'):shutil.copyfile(p,TD/'metrics'/p.name)
shutil.copyfile(latest['G2_evaluate']/'FAILURE_REGISTRY.json',TD/'FAILURE_REGISTRY.json')
ledger=read(TD/'FAILURE_REGISTRY.json');ledger['engineering_failures']=[read(TD/'evidence/REPAIR_001.json'),read(TD/'evidence/SPARSE_READINESS_REPAIR.json')];ledger['original_scientific_registry']=str(latest['G2_evaluate']/'FAILURE_REGISTRY.json');(TD/'FAILURE_REGISTRY.json').write_text(json.dumps(ledger,indent=2))
for case in ['G01','G03','G05']:
 dst=TD/'runs'/case;dst.symlink_to(os.path.relpath(latest['G1_'+case]/case,dst.parent))
for n,stage in [('REGRESSION_RESULT.json','structured_regression'),('INITIALIZATION_AUDIT.json','G0_source_audit')]:
 src=latest[stage]/('result.json'if n.startswith('REGRESSION')else n);link(src,TD/'evidence'/n)
link(latest['structured_regression']/'regression_log.txt',TD/'evidence/REGRESSION_LOG.txt');link(latest['G2_evaluate']/'GT_FIRST_ACCESS.json',TD/'evidence/GT_FIRST_ACCESS.json')
# Compact prediction/review assets for git. Original full stage evidence stays under runs.
for case in ['G01','G03','G05']:
 for arm in ['DEFORM_ONLY','DEFORM_SWEEP']:
  src=latest['G1_'+case]/case/arm
  if (src/'FINAL.npz').exists():
   for n in ['FINAL.npz','PREDICTION_FROZEN.json','INPUT_CONTRACT.json','UPDATES.json']:
    link(src/n,TD/'review_assets'/case/arm/n)
  for p in (latest['G2_evaluate']/case).glob(arm+'_GT_ALIGNED.npz'):link(p,TD/'review_assets'/case/p.name)
 for n in ['INITIAL_GT_ALIGNED.npz','PREVIOUS_DEFORM_GROW_GT_ALIGNED.npz','GT.npz']:
  link(latest['G2_evaluate']/case/n,TD/'review_assets'/case/n)
# Verify output href/img paths and raw prediction immutability.
from html.parser import HTMLParser
class Paths(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']and not v.startswith(('#','http','data:')):
    p=(TD/'visualization'/v).resolve();assert p.exists(),str(p)
Paths().feed((TD/'visualization/index.html').read_text())
rows=read(latest['G2_evaluate']/'EVALUATION.json')['summary']
version=dict(branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),frozen_source_commit=subprocess.check_output(['git','rev-parse','cadde3e9'],cwd=ROOT,text=True).strip(),baseline='7c471701f38f1577ba506bc8ed1e38774f99dabe',historical_InitA='905e2a9b3615a5f429553837a05e5d53826cef03',TASK_sha256=sha(TD/'TASK.yaml'),code_lock_sha256=sha(TD/'inputs/CODE_LOCK.json'),runner_freeze=state['freeze_sha256'],runner_status=state['status'],scientific_acceptance='AWAITING_HUMAN_REVIEW',all_prediction_meshes={})
for case in ['G01','G03','G05']:
 for r in read(latest['G1_'+case]/'BODY_PREDICTIONS_FROZEN.json')['records']:
  if r['status']=='NUMERIC':p=latest['G1_'+case]/r['mesh_relative'];assert sha(p)==r['mesh_sha256'];version['all_prediction_meshes'][case+'/'+r['arm']]=dict(path=str(p),sha256=sha(p))
(TD/'evidence/FINAL_PATH_VERIFICATION.json').write_text(json.dumps(dict(visualization=str(TD/'visualization'),index=str(TD/'visualization/index.html'),figures=len(list((TD/'visualization/figures').glob('*.png'))),version=version),indent=2))
print(json.dumps(version,indent=2));print('PACKAGED',TD)
