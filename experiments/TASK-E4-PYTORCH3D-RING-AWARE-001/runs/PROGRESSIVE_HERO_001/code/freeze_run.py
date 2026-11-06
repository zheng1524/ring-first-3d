from common import *
import argparse,subprocess
CRITICAL=['common.py','p3d.py','components.py','train_progressive.py','evaluate.py']
def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['pre','predictions']);a=ap.parse_args()
    if a.phase=='pre':
        assert load(R/'metrics/PREFLIGHT.json')['passed'];files=[R/'code'/x for x in CRITICAL]+[R/'01_PROTOCOL.md',R/'config/PROTOCOL.json']+[p for folder in ['inputs','depth_observations']for p in sorted((R/folder).rglob('*'))if p.is_file()];fn='PREOPT_FREEZE'
    else:
        for name in['virtual','real']:
            for arm in['B','C','D']:assert load(R/'metrics'/(name+'_'+arm+'_RUN.json'))['status']in['COMPLETED','STOPPED']
        files=[R/'code'/x for x in CRITICAL]+[R/'01_PROTOCOL.md',R/'config/PROTOCOL.json']+[p for p in sorted((R/'local_results').rglob('*'))if p.is_file()]+[p for p in sorted((R/'metrics').glob('*_RUN.json'))];fn='PREDICTIONS_FROZEN_BEFORE_EVALUATION'
    assert not(R/'assets_index'/(fn+'.json')).exists()
    save('assets_index/'+fn+'.json',dict(files=[asset(p)for p in files],time_epoch=time.time(),commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),algorithm=CRITICAL,GT_exception='Virtual D only uses pre-generated ideal depth observations; no GT Mesh',no_checkpoint_selection=True))
    print(fn,len(files),flush=True)
if __name__=='__main__':main()
