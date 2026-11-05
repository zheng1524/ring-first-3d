from common import *
import argparse,subprocess
def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['pre','predictions']);a=ap.parse_args()
    if a.stage=='pre':
        assert load(R/'metrics/PROJECTION_GATE.json')['passed']and load(R/'metrics/GRADIENT_GATE.json')['passed']
        files=sorted((R/'code').glob('*.py'))+sorted((R/'config').glob('*'))+sorted((R/'inputs').rglob('*'))+[R/'01_PROTOCOL.md']
        dst='assets_index/PREOPT_FREEZE.json'
    else:
        for case in['virtual','real']:
            for arm in['Baseline','RingAware']:assert load(R/'metrics'/(case+'_'+arm+'_RUN.json'))['completed_steps']==300
        files=sorted((R/'local_results').rglob('*.npz'))+sorted((R/'local_results').rglob('*.obj'))+sorted((R/'local_results').rglob('*.ply'))+sorted((R/'config').glob('*'))+sorted((R/'code').glob('*.py'))
        dst='assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json'
    assert not(R/dst).exists(),dst
    save(dst,dict(files=[asset(p)for p in files if p.is_file()],commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),GT_allowed_only_after_this_record=a.stage=='predictions',time_epoch=time.time()))
    print(dst,flush=True)
if __name__=='__main__':main()
