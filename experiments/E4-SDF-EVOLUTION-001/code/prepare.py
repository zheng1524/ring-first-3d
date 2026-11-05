from inputs import *
from field import *
from collision import Collision
import platform,scipy,skimage,inspect,datetime
from scipy.optimize import lsq_linear
def main():
    fit=['G01_004_'+x for x in ['ref08','ref13','ref03','growth_r14']];val=['G01_004_'+x for x in ['growth_r04','growth_r06','growth_r10']]
    p=dict(task='E4-SDF-EVOLUTION-001',case='G01_004',fit=fit,validation=val,h_mm=.25,domain_margin_mm=2.,active_band_mm=1.25,CFL_field_mm=.075,max_surface_step_mm=.125,total_field_correction_mm=.75,CAD_field_margin_mm=.025,iterations=20,line_search=[1.,.5,.25],stop_after_no_accept=3,contour_max_px=20,projection_min_px_per_mm=1.,Huber_px=5.,contour_sigma_px=3.,HERO_sigma_mm=.5,HERO_weight=.15,prior_weight=.08,H1_weight=.35,bending_weight=.015,eikonal_weight=.1,protection_band_mm=.25,protection_slack_mm=.05,volume_upper_ratio=1.2,volume_lower_ratio=.8,per_step_volume_ratio=1.03,gradient_p01_lower=.35,gradient_p99_upper=1.8,LS_TRF_max_iter=12,LSMR_maxiter=120,LSMR_tol=1e-5,LS_tol=1e-5,minimum_objective_decrease=1e-6,random_seed=20261105,initialization_dependency='R1 safe P0 used all seven sources; validation is update-stage only, not initialization independent',selection='partition IDs frozen before SDF fitting; all sources INSUFFICIENT_EVIDENCE, conditional research admission only',GT='NOT_EVALUABLE',no_ablation=True,no_FFD=True,no_neural_training=True)
    save('config/LOCKED_PROTOCOL.json',p)
    P=dict(np.load(R1/'local_results/G01_004/P0.npz'));V=P['V'];F=P['F'];assert trimesh.Trimesh(V,F,process=False).is_watertight
    cad=ringmesh('G01_004');h=p['h_mm'];lo=np.floor((np.vstack([V,cad.vertices]).min(0)-2)/h)*h;hi=np.ceil((np.vstack([V,cad.vertices]).max(0)+2)/h)*h;shape=np.rint((hi-lo)/h).astype(int)+1;g=Field(lo,shape,h);phi=signed(mesh_scene(V,F),g.points)
    np.savez_compressed(R/'inputs/INITIAL_FIELD.npz',origin=lo,shape=shape,h=h,phi=phi,V=V,F=F)
    paths=[R1/'local_results/G01_004/P0.npz',N0/'config/CAMERA_GATE_RESULTS.json',R/'config/LOCKED_PROTOCOL.json'];rows=[]
    for cid in fit+val:
        s=source(cid);o=obs(cid);assert GATE[cid]['Ring_pass']and GATE[cid]['qualification']in ['INSUFFICIENT_EVIDENCE','CONDITIONAL_USABLE']
        cc=CC[cid];paths+=[R1/'inputs'/(cid+'.npz'),N0/'frozen_inputs/native'/(cid+'.npz'),Path(cc['pack']),Path(cc['Mask']),Path(cc['RGB']),Path(cc['camera_file']),Path(cc['E1_actual_native']['path']),Path(cc['Ring_CAD']['path']),Path('/home/liu/ring_first_3d_e4_ffd/experiments/TASK-E4-PMGR-FFD-002/inputs')/(cid+'_FIXED_MASK.npz')]
        rows.append(dict(source=cid,role='FIT'if cid in fit else'UPDATE_HOLDOUT',qualification=GATE[cid]['qualification'],partition=GATE[cid]['block'],fixed_native_N=len(o['X']),fixed_pairs_N=len(o['pairs']),RGB=asset(cc['RGB']),Mask=asset(cc['Mask']),upstream_RGB=cc.get('HERO_input_views'),K=s['K'],c2w_mm=s['T']))
    save('assets_index/FROZEN_INPUTS.json',dict(files=[asset(q)for q in dict.fromkeys(paths)],sources=rows,extracted=EXTRACTED,initial_field=asset(R/'inputs/INITIAL_FIELD.npz')))
    save('metrics/ENVIRONMENT.json',dict(Python=platform.python_version(),NumPy=np.__version__,SciPy=scipy.__version__,skimage=skimage.__version__,Open3D=o3d.__version__,trimesh=trimesh.__version__,lsq_linear_signature=str(inspect.signature(lsq_linear)),device='CPU only',new_packages_task_local=['scikit-image==0.25.2','lazy-loader==0.4','imageio==2.37.0','tifffile==2025.5.10'],grid_shape=shape,grid_nodes=g.N,grid_min_mm=lo,grid_max_mm=hi))
    print('PREPARED',shape,g.N,flush=True)
if __name__=='__main__':main()
