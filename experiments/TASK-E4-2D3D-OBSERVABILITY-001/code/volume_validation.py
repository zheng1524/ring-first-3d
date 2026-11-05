"""Independent fixed Sobol quadrature; checks flat-boundary grid aliasing only."""
from model import *
from scipy.stats import qmc
def main():
    assert load(R/'metrics/ALL_PREDICTIONS_FREEZE.json')['all_predictions_frozen_before_this_first_native_GT_evaluation']
    assert not (R/'metrics/VOLUME_SOBOL_VALIDATION.json').exists()
    body=Body();lo=body.P.min(0);hi=body.P.max(0);P=qmc.scale(qmc.Sobol(3,scramble=True,seed=20261105).random_base2(18),lo,hi);w=float(np.prod(hi-lo)/len(P));gt=np.load(R/'audit_only/NATIVE_CAD_GT.npz');base=np.load(R/'inputs/BASE_SOURCE_MESH.npz')
    GT=signed(scene(gt['V'],gt['F']),P)<0;B=signed(scene(base['V'],base['F']),P)<0;ga=GT&~B;gr=B&~GT
    def vol(x):return float(x.sum()*w)
    rows=[]
    for name,a in [('P0',base)]+[(a,np.load(R/'local_results'/a/'FINAL/MODEL.npz'))for a in ['ORIGINAL','SUBPIXEL_TARGET']]:
        o=signed(scene(a['V'],a['F']),P)<0;pa=o&~B;pr=B&~o
        rows.append(dict(state=name,volume_mm3=vol(o),symmetric_difference_mm3=vol(o!=GT),pred_added_mm3=vol(pa),pred_removed_mm3=vol(pr),added_recovered_mm3=vol(pa&ga),removed_recovered_mm3=vol(pr&gr),added_recovery_ratio=vol(pa&ga)/vol(ga),removed_recovery_ratio=vol(pr&gr)/vol(gr),wrong_added_mm3=vol(pa&~ga),wrong_removed_mm3=vol(pr&~gr)))
    save('metrics/VOLUME_SOBOL_VALIDATION.json',dict(method='single fixed 2^18 scrambled Sobol quadrature in independent P0 bounds; actual mesh signed occupancy for every state; proxy not exact Boolean',seed=20261105,N=len(P),GT_volume_mm3=vol(GT),GT_added_mm3=vol(ga),GT_removed_mm3=vol(gr),single_sign_unavoidable_difference_lower_bound_mm3=min(vol(ga),vol(gr)),rows=rows,no_predictions_or_original_metrics_changed=True,reason='coarse node quadrature can alias a flat native CAD base; validates evaluation precision, not parameter selection'))
    np.savez_compressed(R/'audit_only/FIXED_SOBOL_POINTS.npz',P=P,GT=GT,P0=B)
    print('SOBOL_VOLUME_VALIDATION',rows,vol(ga),vol(gr),flush=True)
if __name__=='__main__':main()
