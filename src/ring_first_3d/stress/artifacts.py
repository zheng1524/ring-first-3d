"""Reuse atomic publication; enforce task-specific complete Mesh evidence."""
import json,re,shutil
from ..policy.artifacts import write_json
from ..policy.contracts import require
from ..contracts.identities import sha256

def enhance(root,task,state,latest,pending):
 metrics=json.loads((pending/'metrics.json').read_text());metrics.update(engineering_only=False,profile='MULTISURFACE_STRESS_REAL_PILOT',GT_read='G0_views_noise'in latest,history_prediction_fallback=0,new_scientific_predictions=int('G3_all_predict'in latest),camera_optimization=False)
 for stage in task['authorization']['stages']:
  if stage in latest and latest[stage]['status']=='PASS':metrics[stage]=latest[stage]['payload']
 files={};row=latest.get('G4_visualize')
 if row and row['status']=='PASS':
  folder=root/'attempts'/row['attempt_id'];payload=row['payload']
  for name,rec in payload['files'].items():
   p=folder/name;require(p.resolve().is_relative_to(folder)and p.is_file()and sha256(p)==rec['sha256'],'ARTIFACT_SHA',name)
   if p.suffix not in {'.png','.html','.js','.json','.csv','.md'}:continue
   target=pending/name if name in {'TECHNICAL_REPORT.md','RESULT_CARD.md'}else pending/'visualization'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);files[str(target.relative_to(pending))]=dict(sha256=sha256(target),bytes=target.stat().st_size)
  failure=json.loads((pending/'failures.json').read_text());failure['scientific_failures']=payload['scientific_failures'];(pending/'failures.json').unlink();write_json(pending/'failures.json',failure);state['scientific_acceptance']='AWAITING_HUMAN_REVIEW'
 state['stress_files']=files;(pending/'metrics.json').unlink();write_json(pending/'metrics.json',metrics)

def validate(root,state):
 files=state.get('stress_files',{})
 for name,rec in files.items():
  p=root/name;require(p.resolve().is_relative_to(root)and p.is_file()and sha256(p)==rec['sha256']and p.stat().st_size==rec['bytes'],'ARTIFACT_MISSING',name)
 if any('-G4_visualize-'in r['path']for r in state['attempts']):
  required={'visualization/figures/01_MAIN_STRESS_SECTIONS.png','visualization/multisurface_3d.html','visualization/sections_all.html','visualization/data.js','visualization/cases/C7_E1.js','visualization/STRESS_METRICS.json','visualization/STRESS_METRICS.csv','visualization/MODEL_METRICS.json','visualization/REGISTRATION_METRICS.json','visualization/FAILURE_LEDGER.json','visualization/NOISE_AUDIT.json','visualization/REAL_AUDIT.json','visualization/REAL_METRICS.json'}|{'visualization/'+g+'/index.html'for g in ['G01','G03','G05']}
  require(required<=set(files),'ARTIFACT_MISSING','Stress and all real-group evidence mandatory')
  first=re.search(r'!\[[^\]]*\]\(([^)]+)\)',(root/'TECHNICAL_REPORT.md').read_text());require(first and first.group(1)=='visualization/figures/01_MAIN_STRESS_SECTIONS.png','MAIN_FIGURE','Actual cuts first')
