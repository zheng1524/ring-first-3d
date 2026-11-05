"""Numerical probes only; never restart optimization or select a checkpoint."""
from checks import *
def main():
    assert not (R/'metrics/FINAL_PROBES_FINISHED.json').exists();stages=['S1']
    if (R/'metrics/S3_FINISHED.json').exists():stages+=['S3']
    elif (R/'metrics/S2_FINISHED.json').exists():stages+=['S2']
    for s in stages:
        q=np.array(load(R/'metrics'/(s+'_FINISHED.json'))['q']);sensitivity(Body(),Renderer(),q,s+'_FINAL')
    save('metrics/FINAL_PROBES_FINISHED.json',dict(stages=stages,no_new_optimizer=True,GT_not_read=True,predictions_unchanged=True))
if __name__=='__main__':main()
