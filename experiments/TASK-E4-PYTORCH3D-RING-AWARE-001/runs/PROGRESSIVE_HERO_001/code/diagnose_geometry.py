"""Postfreeze explanatory diagnostics; never supplies a floor, bound or GT parameter to training."""
from common import *
from evaluate import occupied
from scipy.stats import qmc
def main():
    g=np.load(OLD/'audit_only/NATIVE_CAD_GT.npz');zmin=float(g['V'][:,2].min());p0=np.load(R/'inputs/virtual/INITIAL.npz');v=p0['V'];lo=v.min(0)-np.ptp(v,axis=0);hi=v.max(0)+np.ptp(v,axis=0);X=lo+(hi-lo)*qmc.Sobol(3,scramble=True,seed=20261106).random_base2(18);weight=np.prod(hi-lo)/len(X);cfg=load(R/'config/PROTOCOL.json');rows=[]
    for arm in['P0','A','B','C','D']:
        path=R/'inputs/virtual/INITIAL.npz'if arm=='P0'else Path(cfg['A_frozen_root'])/'local_results/virtual/RingAware/FINAL.npz'if arm=='A'else R/'local_results/virtual'/arm/'FINAL.npz'
        a=np.load(path);oc=occupied(scene(a['V'],a['F']),X);rows.append(dict(arm=arm,vertices_below_GT_minZ=int((a['V'][:,2]<zmin).sum()),mesh_zmin_mm=float(a['V'][:,2].min()),GT_zmin_mm=zmin,occupancy_proxy_below_GT_minZ_mm3=float((oc&(X[:,2]<zmin)).sum()*weight),not_used_as_training_constraint=True,solid_volume_caveat='B/C/D self-intersect; proxy diagnostic, not certified Boolean volume'))
    summary=load(R/'metrics/SUMMARY.json');transitions=[]
    for name in['virtual','real']:
        for arm in['C','D']:
            r=next(x for x in summary if x['case']==name and x['arm']==arm and x['step']==100);a=np.load(R/'local_results'/name/arm/'STEP_0100.npz');transitions.append(dict(case=name,arm=arm,stage1_metrics=r,global_translation_normalized=a['global_q'][:3],axis_factors=np.exp(a['global_q'][3:]),stage2_start_identical=bool(np.array_equal(a['V'],np.load(R/'local_results'/name/arm/'STAGE2_START.npz')['V']))))
    save('metrics/POSTERIOR_CAUSE_DIAGNOSIS.json',dict(virtual_z_diagnostic=rows,global_stage_results=transitions,GT_used_after_prediction_freeze=True,training_rule_unchanged=True,scope='Evidence of low-DOF silhouette ambiguity and remaining hidden-side inference; no claim to uniquely separate every optimizer/representation effect.'))
    print(rows,flush=True)
if __name__=='__main__':main()
