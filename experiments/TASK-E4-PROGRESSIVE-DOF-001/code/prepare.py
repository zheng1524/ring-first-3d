"""Copies are already present; register independent configuration and metric queries."""
from model import *
from scipy.stats import qmc
def main():
    assert not (R/'config/LOCKED_PROTOCOL.json').exists()
    src=load(R/'config/SOURCE_GATE_A_PROTOCOL.json');c0=np.array(src['P0_center_mm']);a0=np.array(src['P0_axes_mm'])
    cfg=dict(task='TASK-E4-PROGRESSIVE-DOF-001',P0_center_mm=c0,P0_axes_mm=a0,fit_views=src['fit_views'],holdout_views=src['holdout_views'],seed=20261105,rotation_frozen=True,global_bounds=[[-.75,.75]]*3+[[float(np.log(.5)),float(np.log(1.4))]]*3,radius_mm=src['correction_radius_mm'],amplitude_bounds_mm=[[-.6,0.],[0.,.6]],center_offset_limit_mm=src['correction_radius_mm']/2,maxiter=12,maxfev=500,xtol=.01,ftol=1e-5,objective_corrected=False,signal_relative=.001,signal_absolute=1e-4,minimum_active_amplitude_mm=.02,Gate_B_C_D='NOT_RUN_NOT_AUTHORIZED')
    save('config/LOCKED_PROTOCOL.json',cfg)
    a=np.load(R/'inputs/BASE_FIELD.npz');lo=c0-.75+(a['P'].min(0)-c0)*1.4;hi=c0+.75+(a['P'].max(0)-c0)*1.4
    P=qmc.scale(qmc.Sobol(3,scramble=True,seed=cfg['seed']).random_base2(19),lo,hi)
    np.savez_compressed(R/'inputs/EVAL_POINTS.npz',P=P,lo=lo,hi=hi,weight=np.prod(hi-lo)/len(P))
    files=[asset(p)for p in sorted((R/'inputs').iterdir())if p.is_file()]
    save('assets_index/INPUT_MANIFEST.json',dict(files=files,no_data_regeneration=True,independent_metric_bounds_mm=[lo,hi],metric_points_N=len(P),GT_path_only=str(REPO/'experiments/TASK-E4-2D3D-OBSERVABILITY-001/audit_only/NATIVE_CAD_GT.npz'),GT_not_opened=True))
    print('PREPARED',len(P),lo,hi,flush=True)
if __name__=='__main__':main()
