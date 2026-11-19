"""Atomic original publication API, plus actual aligned/full Mesh assertions."""
import json,re,shutil
from ..policy.artifacts import write_json
from ..policy.contracts import require
from ..contracts.identities import sha256

def enhance(root,task,state,latest,pending):
 metrics=json.loads((pending/'metrics.json').read_text());metrics.update(engineering_only=False,profile='MULTIVIDEO_INIT_A_HERO',GT_read=any(s.startswith('G3_')for s in latest),history_prediction_fallback=0,new_scientific_predictions=int('G1_all_train'in latest),world_predictions_GT_aligned=False)
 for stage in task['authorization']['stages']:
  if stage in latest and latest[stage]['status']=='PASS':metrics[stage]=latest[stage]['payload']
 files={};row=latest.get('G4_visualize')or latest.get('G4_smoke_visualize')
 if row and row['status']=='PASS':
  folder=root/'attempts'/row['attempt_id'];payload=row['payload']
  for name,rec in payload['files'].items():
   p=folder/name;require(p.is_file()and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
   if p.suffix not in {'.png','.html','.js','.json','.csv','.md'}:continue
   target=pending/name if name in {'TECHNICAL_REPORT.md','RESULT_CARD.md'}else pending/'visualization'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);files[str(target.relative_to(pending))]=dict(sha256=sha256(target),bytes=target.stat().st_size)
  f=json.loads((pending/'failures.json').read_text());f['scientific_failures']=payload['scientific_failures'];(pending/'failures.json').unlink();write_json(pending/'failures.json',f);state['scientific_acceptance']='AWAITING_HUMAN_REVIEW'
 state['inita_files']=files;(pending/'metrics.json').unlink();write_json(pending/'metrics.json',metrics)

def validate(root,state):
 files=state.get('inita_files',{})
 for name,rec in files.items():
  p=root/name;require(p.is_file()and sha256(p)==rec['sha256']and p.stat().st_size==rec['bytes'],'ARTIFACT_MISSING',name)
 if any('-G4_visualize-'in r['path']for r in state['attempts']):
  require({'visualization/figures/Fig1_All_InitA_Bodies.png','visualization/BODY_SHAPE_METRICS.csv','visualization/BODY_SHAPE_METRICS.json','visualization/HERO_METRICS.json','visualization/GT_RIGID_TRANSFORMS.json','visualization/figures/Fig3_Verified_Ip_Failures.png','visualization/FAILURE_LEDGER.json'}<=set(files),'ARTIFACT_MISSING','Actual aligned Mesh, native Mask, verified Ip and HERO evidence')
  first=re.search(r'!\[[^\]]*\]\(([^)]+)\)',(root/'TECHNICAL_REPORT.md').read_text());require(first and first.group(1)=='visualization/figures/Fig1_All_InitA_Bodies.png','MAIN_FIGURE','Actual aligned bodies first')
