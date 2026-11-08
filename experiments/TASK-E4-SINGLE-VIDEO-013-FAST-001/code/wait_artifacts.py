from common import *
import subprocess
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
while not(R/'provenance/EVALUATION_COMPLETE.json').exists():time.sleep(10)
for name in ['report.py','figures.py']:
 print('BUILD',name,flush=True);subprocess.run([PY,'-B',str(R/'code'/name)],check=True)
save('provenance/ARTIFACTS_READY.json',dict(epoch=time.time(),awaiting_integrity_and_visual_review=True,scientific_status_not_assumed=True))
