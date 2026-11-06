"""Wait for fixed nine routes; then run frozen-output evaluation, without any training retry."""
from pathlib import Path
import subprocess,json,sys,time
r=Path(__file__).resolve().parents[1]
while True:
 p=r/'runtime/SERIAL_STATUS.json'
 try:s=json.loads(p.read_text())if p.exists()else[]
 except json.JSONDecodeError:s=[]
 if len(s)==9:break
 time.sleep(20)
assert all(x['returncode']==0 and x['result'] is not None for x in s),s
for f in['freeze_predictions.py','evaluate_run.py']:
 print('POST',f,flush=True);subprocess.run([sys.executable,'-B',str(r/'code'/f)],check=True)
print('POST Blender',flush=True);subprocess.run(['/home/liu/blender/blender-5.0.1-linux-x64/blender','--background','--factory-startup','--python',str(r/'code/blender_checks.py'),'--',str(r)],check=True)
for f in['post_audit.py','figures_updates.py','objective_components.py','write_report.py']:
 print('POST',f,flush=True);subprocess.run([sys.executable,'-B',str(r/'code'/f)],check=True)
print('POST_COMPLETE',flush=True)
