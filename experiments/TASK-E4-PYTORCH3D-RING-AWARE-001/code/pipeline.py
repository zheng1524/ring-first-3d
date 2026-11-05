"""Sequential, gate-checked once-only execution; no remote/GPU concurrency."""
from common import *
import subprocess

def run(script,*args):
    p=R/'runtime'/(script.replace('.py','')+('_'+'_'.join(args)if args else'')+'.log')
    with p.open('w')as f:
        result=subprocess.run([sys.executable,'-B',str(R/'code'/script),*args],stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(str(p))
def main():
    run('official.py')
    run('export_audit.py')
    run('projection_gate.py')
    assert load(R/'metrics/PROJECTION_GATE.json')['passed'],'Stop before optimization: projection failure'
    run('occlusion_audit.py');run('gradients.py')
    assert load(R/'metrics/GRADIENT_GATE.json')['passed'],'Stop before optimization: gradient failure'
    # PREOPT freeze must be requested after inspecting audit figures; do not automate it.
    print('Official reproduction, camera audit and gradient audit complete. Inspect figures before project run.',flush=True)
if __name__=='__main__':main()
