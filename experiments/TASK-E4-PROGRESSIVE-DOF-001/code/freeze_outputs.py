"""Freeze outputs before post-run diagnostics/GT. Never starts an optimizer."""
from model import *
import datetime
def main():
    assert load(R/'metrics/S1_FINISHED.json')['finished'];stages=['S1']
    if load(R/'metrics/KERNEL_SELECTION.json')['eligible']:
        assert load(R/'metrics/S2_FINISHED.json')['finished'];stages+=['S2']
        if load(R/'metrics/CENTER_RELEASE_GATE.json')['released']:
            assert load(R/'metrics/S3_FINISHED.json')['finished'];stages+=['S3']
        elif not(R/'metrics/S3_STATUS.json').exists():save('metrics/S3_STATUS.json',dict(status='NOT_TRIGGERED',reason='per-kernel effective fit signal gate failed',no_GT_or_holdout_selection=True))
    if not(R/'local_results/P0').exists():Body().save('P0',np.zeros(6))
    freeze=R/'metrics/ALL_OPTIMIZED_PREDICTIONS_FREEZE.json'
    if freeze.exists():
        for f in load(freeze)['files']+load(freeze)['configs']:assert sha(f['path'])==f['sha256']
    else:
        assert not(R/'metrics/POSTERIOR.json').exists()
        files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()];configs=[asset(p)for p in sorted((R/'config').glob('*.json'))]
        if(R/'metrics/CENTER_RELEASE_GATE.json').exists():configs.append(asset(R/'metrics/CENTER_RELEASE_GATE.json'))
        save('metrics/ALL_OPTIMIZED_PREDICTIONS_FREEZE.json',dict(files=files,configs=configs,timestamp=datetime.datetime.now().isoformat(),before_first_native_GT_read=True,GT_selection=False,stages=stages,before_final_diagnostic_probes=True))
    print('FROZEN_AND_VERIFIED',stages,flush=True)
if __name__=='__main__':main()
