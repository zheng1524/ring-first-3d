from pathlib import Path
import subprocess,sys,time
r=Path(__file__).resolve().parents[1]
def run(name,cmd):
 with(r/'runtime'/(name+'.log')).open('w')as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 print(name,p.returncode,flush=True)
 if p.returncode:print((r/'runtime'/(name+'.log')).read_text()[-5000:],flush=True);raise SystemExit(p.returncode)
run('FREEZE_AFTER',[sys.executable,'-B',str(r/'code/freeze.py'),'after'])
run('EVALUATION',[sys.executable,'-B',str(r/'code/evaluate_d2.py')])
run('BLENDER_CHECKS',['/home/liu/blender/blender-5.0.1-linux-x64/blender','--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(r/'code/blender_checks.py'),'--',str(r)])
run('NATIVE_SOLID_AUDIT',[sys.executable,'-B',str(r/'code/audit_native_solids.py')])
run('EXTRA_EVALUATE',[sys.executable,'-B',str(r/'code/extra_evaluate.py')])
run('SECTION_AUDIT',[sys.executable,'-B',str(r/'code/section_audit.py')])
run('READONLY_MULTIVIEW',[sys.executable,'-B',str(r/'code/readonly_multiview.py')])
run('HISTORICAL_AUDIT',[sys.executable,'-B',str(r/'code/historical_audit.py')])
run('FIGURES',[sys.executable,'-B',str(r/'code/figures_d2.py')])
run('BOUNDARY_DIAGNOSTICS',[sys.executable,'-B',str(r/'code/boundary_diagnostics.py')])
run('NATIVE_CONTRACT',[sys.executable,'-B',str(r/'code/native_contract.py')])
run('VALIDATE',[sys.executable,'-B',str(r/'code/validate.py')])
print('POST_DONE',flush=True)
