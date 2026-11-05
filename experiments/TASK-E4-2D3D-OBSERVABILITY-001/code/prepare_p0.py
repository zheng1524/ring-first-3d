"""Ring-only conservative ellipsoid. Never read native CAD or historical SDF."""
from model import *
def main():
    assert not (R/'inputs/BASE_FIELD.npz').exists()
    cad=dict(np.load(R/'inputs/RING_CAD.npz'));rc=cad['V'].mean(0);ri=5.0
    center=rc+np.array([0,0,.10*ri]);axes=ri*np.array([.5,.5,.15])
    # Generic fixed Ring-relative low-dimensional initializer, no shape label branches.
    mesh=trimesh.creation.icosphere(subdivisions=4);mesh.vertices=np.asarray(mesh.vertices)*axes+center
    V=np.asarray(mesh.vertices);F=np.asarray(mesh.faces);h=.15
    lo=np.floor((center-axes-.9)/h)*h+.013*h;hi=center+axes+.9
    shape=np.ceil((hi-lo)/h).astype(int)+1
    P=np.stack(np.meshgrid(*[lo[k]+h*np.arange(shape[k])for k in range(3)],indexing='ij'),-1).reshape(-1,3)
    phi=signed(scene(V,F),P);tets=grid_tets(shape);p=phi[tets];tets=tets[(p.min(1)<.6)&(p.max(1)>-.6)]
    np.savez_compressed(R/'inputs/BASE_FIELD.npz',P=P,phi=phi,tets=tets,h=h,origin=lo,shape=shape,radius=.36*ri,V=V,F=F)
    body=Body();v,f=body.mesh(np.r_[center,0.]);np.savez_compressed(R/'inputs/BASE_SOURCE_MESH.npz',V=v,F=f)
    cfg=dict(task='TASK-E4-2D3D-OBSERVABILITY-001',authorized='Gate A only',seed=20261105,P0_center_mm=center,P0_axes_mm=axes,P0_rotation_rad=[0,0,0],P0_rule='Ring center +0.10 inner-radius along +Z; axes=(0.5,0.5,0.15)*inner-radius; no target/GT use',inner_radius_mm=ri,correction_radius_mm=.36*ri,center_bounds_mm=[(center-axes-.75).tolist(),(center+axes+.75).tolist()],amplitude_bounds_mm=[-.6,.6],max_iterations=12,max_function_evaluations=500,Powell_xtol_mm=.01,Powell_ftol=1e-5,fit_views=['IIa6.5_R10_obs01','IIa6.5_R10_obs03','IIa6.5_R10_obs05'],holdout_views=['IIa6.5_R10_obs00','IIa6.5_R10_obs04'],seed_rule='unchanged mask-only weighted initial visible silhouette points; sign by fit-mask area',projection_gate=dict(min_IoU=.99,max_p95_contour_px=1,max_point_projection_px=.001),camera_decision='user authorized consistent choice: retain archived K/c2w, actual horizontal field angle from K; no 70deg overwrite',parameter_units=['mm','mm','mm','mm SDF coefficient; physical displacement measured separately'],A2=dict(epsilon_mm=.02,half_epsilon_mm=.01,surface_normalization_step_mm=.02,noise_px=.5,query_grid_stride_px=4,query_target_band_px=12,controlled_displacement_target_mm=.3,perturbation_bound='same parameter bounds; report if 0.2--0.5mm unavailable'),Gate_B=dict(status='NOT_AUTHORIZED',axes_R1=1.15,axes_R2=.85,translation_R3_mm=[.5,0,0],optional_TRF='only after observable/correct objective/Powell search failure established and human approval'),Gate_C=dict(status='NOT_AUTHORIZED',case='Ip4_R5'),Gate_D=dict(status='NOT_AUTHORIZED',Ring_noise_px=[1,5]))
    save('config/LOCKED_PROTOCOL.json',cfg)
    save('metrics/P0_PROVENANCE.json',dict(rule=cfg['P0_rule'],center_mm=center,axes_mm=axes,source=asset(R/'inputs/RING_CAD.npz'),GT_or_target_access=False,nodes=len(P),tets=len(tets),quality=normals_quality(v,f),SDF_from='closed independent ellipsoid nearest signed distance, no native CAD field'))
    old=REPO/'experiments/E4-SDF-LOCALIZATION-BLENDER-001/metrics/DMTET_DERIVATIVE_TEST.json'
    save('metrics/DMTET_DERIVATIVE_TEST.json',dict(**load(old),reused_from=asset(old)))
    print('INDEPENDENT_P0_CREATED',center,axes,len(P),len(tets),flush=True)
if __name__=='__main__':main()
