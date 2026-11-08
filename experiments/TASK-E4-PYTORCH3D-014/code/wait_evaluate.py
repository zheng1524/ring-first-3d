from common import *
import subprocess
marker=R/'provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json'
while not marker.exists():time.sleep(10)
view=load(R/'config/C_SELECTION.json')['method'];cases=[c['name']for c in load(R/'config/CASE_LOCK.json')]
for tag in [view,'D_D1_split','D_D2_bidir','D_D3_combo']:
 for n in cases:
  root=R/'arms'/tag
  if(root/'metrics'/(n+'_GRADIENT_DIAGNOSTIC.json')).exists():continue
  with(R/'runtime'/(tag+'_'+n+'_GRADIENT_PROBE.log')).open('w')as f:subprocess.run(['/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python','-B',str(R/'code/gradient_probe014.py'),n,'--record-only'],env=dict(os.environ,E4_RUN_DIR=str(root)),stdout=f,stderr=subprocess.STDOUT,check=True)
rows=[]
for tag in [view,'D_D1_split','D_D2_bidir','D_D3_combo']:
 for n in cases:
  d=load(R/'arms'/tag/'metrics'/(n+'_GRADIENT_DIAGNOSTIC.json'));err=d['additive_gradient_relative_error'];rows.append(dict(case=n,arm=tag,all_components_finite=all(q['finite']for q in d['rows']),relative_additivity_error=err,original_threshold=1e-4,original_test_pass=err<1e-4,continued_independent_evaluation_despite_failed_diagnostic=err>=1e-4))
table('metrics/GRADIENT_ADDITIVITY_CHECKS.csv',rows);save('metrics/GRADIENT_ADDITIVITY_CHECKS.json',rows)
subprocess.run(['/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python','-B',str(R/'code/postprocess014.py')],check=True)
