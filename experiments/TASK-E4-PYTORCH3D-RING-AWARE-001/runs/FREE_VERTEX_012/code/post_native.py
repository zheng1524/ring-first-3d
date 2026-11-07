from common import *
import subprocess
while True:
 p=R/'runtime/SERIAL_STATUS.json'
 try:s=load(p)if p.exists()else[]
 except json.JSONDecodeError:s=[]
 if len(s)==9:break
 time.sleep(20)
for f in ['freeze_and_scale.py','evaluate_native.py']:
 print('POST',f,flush=True);subprocess.run([sys.executable,'-B',str(R/'code'/f)],check=True)
subprocess.run(['/home/liu/blender/blender-5.0.1-linux-x64/blender','--background','--factory-startup','--python',str(R/'code/blender_geometry_checks.py'),'--',str(R)],check=True)
print('NATIVE_POST_COMPLETE_NO_ORIGINAL_BLENDER_GT_READ',flush=True)
