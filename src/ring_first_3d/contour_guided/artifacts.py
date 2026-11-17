"""Existing atomic publication, actual PNG/GLB/NPZ hashes and required evidence."""
import json,shutil,re
from ..policy.artifacts import write_json
from ..policy.contracts import require
from ..contracts.identities import sha256

def enhance(root,task,state,latest,pending):
 metrics=json.loads((pending/'metrics.json').read_text());metrics.update(engineering_only=False,profile='EXPLICIT_CONTOUR_INIT_A',GT_read=any(s.startswith('G3_')for s in latest),new_scientific_predictions=int('G1_all_train'in latest),history_prediction_fallback=0,world_predictions_GT_aligned=False)
 for s,r in latest.items():
  if r['status']=='PASS':metrics[s]={k:v for k,v in r['payload'].items()if k!='files'}
 files={};row=latest.get('G4_visualize')or latest.get('G4_smoke_visualize')
 if row and row['status']=='PASS':
  folder=root/'attempts'/row['attempt_id']
  for name,rec in row['payload']['files'].items():
   p=folder/name;require(p.is_file()and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
   if p.suffix not in {'.png','.html','.json','.csv','.md','.glb','.npz'}:continue
   target=pending/name if name in {'TECHNICAL_REPORT.md','RESULT_CARD.md'}else pending/'visualization'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);files[str(target.relative_to(pending))]=dict(sha256=sha256(target),bytes=target.stat().st_size)
  failures=json.loads((pending/'failures.json').read_text());failures['scientific_failures']=row['payload']['scientific_failures'];(pending/'failures.json').unlink();write_json(pending/'failures.json',failures);state['scientific_acceptance']='AWAITING_HUMAN_REVIEW'
 state['contour_files']=files;(pending/'metrics.json').unlink();write_json(pending/'metrics.json',metrics)

def validate(root,state):
 files=state.get('contour_files',{})
 for n,r in files.items():
  p=root/n;require(p.is_file()and sha256(p)==r['sha256']and p.stat().st_size==r['bytes'],'ARTIFACT_MISSING',n)
 if any('-G4_visualize-'in r['path']for r in state['attempts']):
  require({'visualization/figures/Fig1_2D_TO_3D.png','visualization/figures/Fig2_ALL_BODY_GT.png','visualization/figures/Fig4_BODY_HERO_RELATION.png','visualization/BODY_SHAPE_METRICS.csv','visualization/HERO_ALL11_METRICS.csv','visualization/BODY_UPDATE_LINKS.json','visualization/FAILURE_LEDGER.json','visualization/GT_RIGID_TRANSFORMS.json'}<=set(files),'ARTIFACT_MISSING','Real 2D→3D mechanism, GT copies and all11 HERO required')
  require(any(n.endswith('_H4_FULL_HERO.glb')for n in files),'ARTIFACT_MISSING','Actual registered HERO GLB')
  first=re.search(r'!\[[^\]]*\]\(([^)]+)\)',(root/'TECHNICAL_REPORT.md').read_text());require(first and first.group(1)=='visualization/figures/Fig1_2D_TO_3D.png','MAIN_FIGURE','2D correspondence → actual3D update')
