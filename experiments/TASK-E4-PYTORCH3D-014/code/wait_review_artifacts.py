from common import *
import subprocess
while not(R/'provenance/INDEPENDENT_EVALUATION_COMPLETE.json').exists():time.sleep(10)
for script in ['figures_final.py','report014.py']:
 print('DELIVERY_BUILD',script,flush=True);subprocess.run(['/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python','-B',str(R/'code'/script)],check=True)
save('provenance/REVIEW_ARTIFACTS_BUILT.json',dict(epoch=time.time(),awaiting_visual_inspection_and_Git_push=True,task_finished=False))
