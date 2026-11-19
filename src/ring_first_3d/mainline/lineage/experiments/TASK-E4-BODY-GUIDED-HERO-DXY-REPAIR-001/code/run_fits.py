from common import *
from concurrent.futures import ThreadPoolExecutor,as_completed
def worker(name,arm):
    with (R/'runtime'/(name+'_'+arm+'.log')).open('w') as f:
        p=subprocess.run([sys.executable,str(R/'code/fitting.py'),name,arm],stdout=f,stderr=subprocess.STDOUT)
    return name,arm,p.returncode
def main():
    assert (R/'provenance/PREOPT_FREEZE.json').exists()
    assert not (R/'provenance/ALL_PREDICTIONS_FROZEN.json').exists()
    save('provenance/SOLVER_CODE_FREEZE.json',dict(epoch=time.time(),code=[asset(p) for p in sorted((R/'code').glob('*.py'))],views=asset(R/'config/BODY_FIT_VIEWS.json'),protocol=asset(R/'01_PROTOCOL.md'),GT_read=False))
    plan=load(R/'config/BODY_FIT_VIEWS.json')
    with ThreadPoolExecutor(max_workers=3) as ex:
        fs=[ex.submit(worker,name,arm) for name in plan for arm in ['E1','E2']]
        for f in as_completed(fs):
            name,arm,rc=f.result();print('FIT_FINISH',name,arm,rc,flush=True)
            if rc:raise RuntimeError('FIT_WORKER_FAILED:'+name+arm)
    save('provenance/ALL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),GT_read=False,HOLDOUT_used_for_selection=False,files=[asset(p) for p in sorted((R/'local_results').rglob('*.json'))],views=asset(R/'config/BODY_FIT_VIEWS.json')))
if __name__=='__main__':main()
