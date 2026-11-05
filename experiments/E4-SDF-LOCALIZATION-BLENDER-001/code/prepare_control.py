"""Controlled scene design; target GT and its edit are never optimizer inputs."""
from model import *
import time
def main():
    cfg=load(R/'config/SCENE_INPUTS.json');a=np.load(R/'inputs/BASE_SOURCE_MESH.npz');V=a['V'];F=a['F'];m=trimesh.Trimesh(V,F,process=False);assert m.is_watertight and m.is_winding_consistent
    if m.volume<0:F=F[:,[0,2,1]];m=trimesh.Trimesh(V,F,process=False)
    # Preregister one local edit by a generic normalized spatial location, not Paris type.
    extent=np.ptp(V,axis=0);L=float(max(extent));query=V.min(0)+extent*np.array([.78,.15,.60]);j=cKDTree(V).query(query)[1];center=V[j];radius=.24*L;amp=.06*L;rr=np.linalg.norm(V-center,axis=1)/radius;psi=np.zeros(len(V));sel=rr<1;psi[sel]=np.exp(1-1/(1-rr[sel]**2));GT=V+amp*psi[:,None]*m.vertex_normals
    np.savez_compressed(R/'audit_only/TARGET_GT.npz',V=GT,F=F,base_V=V,base_F=F,true_center_mm=center,true_radius_mm=radius,normal_displacement_mm=amp*psi,delta_xyz_mm=GT-V,changed=psi>0,true_amplitude_mm=amp,construction_query=query)
    # Initial field only reads the base mesh, not edited geometry.
    h=.15;lo=np.floor((V.min(0)-.9)/h)*h+.013*h;hi=V.max(0)+.9;shape=np.ceil((hi-lo)/h).astype(int)+1;P=np.stack(np.meshgrid(*[lo[k]+h*np.arange(shape[k])for k in range(3)],indexing='ij'),-1).reshape(-1,3);phi=signed(scene(V,F),P);tets=grid_tets(shape);values=phi[tets];active=(values.min(1)<.6)&(values.max(1)>-.6);tets=tets[active]
    np.savez_compressed(R/'inputs/BASE_FIELD.npz',P=P,phi=phi,tets=tets,origin=lo,shape=shape,h=h,radius=.28*L,V=V,F=F)
    views=[]
    for s in cfg['views']:
        E=np.asarray(s['world_to_camera_cv']);T=np.eye(4);T[:3,:3]=E[:,:3].T;T[:3,3]=np.asarray(s['camera_center_mm']);Kedge=np.asarray(s['K']);K=Kedge.copy();K[:2,2]-=.5
        views.append(dict(id=s['source_id'],K_edge=Kedge,K_pixel_center=K,c2w_mm=T,width=640,height=360,role='FIT'if s['source_id']in ['IIa6.5_R10_obs01','IIa6.5_R10_obs03','IIa6.5_R10_obs05']else'UPDATE_HOLDOUT'))
    save('inputs/CAMERAS.json',views)
    p=dict(task='E4-SDF-LOCALIZATION-BLENDER-001',first_case='IIa6.5',three_type_scope='IIa first; Ip/Is asset audit only, HUMAN_HOLD after first-scene delivery',h_mm=h,correction='one Wendland C4 compact radial SDF correction',parameters=['center_x_mm','center_y_mm','center_z_mm','amplitude_mm'],correction_radius_mm=.28*L,center_bounds_mm=[(V.min(0)-.15*L).tolist(),(V.max(0)+.15*L).tolist()],amplitude_bounds_mm=[-.6,.6],initial_amplitude_abs_mm=.05,max_iterations=12,max_function_evaluations=500,Powell_xtol_mm=.01,Powell_ftol=1e-5,GT_allowed='generation and independent post-freeze audit only',GT_loss=False,fit_views=[v['id']for v in views if v['role']=='FIT'],holdout_views=[v['id']for v in views if v['role']!='FIT'],projection_gate=dict(min_IoU=.99,max_p95_contour_px=1.,max_point_projection_px=.001),renderer='Open3D pixel-center rays, frozen full CAD occlusion; no PyTorch3D claim',loss='mean symmetric visible silhouette contour distance / fixed source normalization + 0.2 fixed-mask XOR; no GT coordinates or target edit',seed_rule='weighted visible base silhouette points from target Mask discrepancy only; no GT edit location',evaluation_thresholds=dict(center_error_mm=.5,wrong_region_displacement_p95_mm=.05,direction_correct=True,at_least_half_GT_peak=True,normal_angle_p95_growth_limit_deg=5),parameter_search=False)
    save('config/LOCKED_PROTOCOL.json',p);body=Body();q=np.r_[V.mean(0),0.];t=time.time();v,f=body.mesh(q);save('metrics/DMTET_RESOURCE_CHECK.json',dict(nodes=len(P),tets=len(tets),mesh_V=len(v),mesh_F=len(f),seconds_per_extraction=time.time()-t,quality=normals_quality(v,f)))
    # Differentiability of the official extractor on a fixed tetrahedron topology.
    vv=torch.tensor([[[0.,0,0],[1,0,0],[0,1,0],[0,0,1]]],dtype=torch.float64);tt=torch.tensor([[0,1,2,3]]);ss=torch.tensor([[-.3,.7,.7,.7]],dtype=torch.float64,requires_grad=True);out,_=marching_tetrahedra(vv,tt,ss);loss=out[0].sum();loss.backward();analytic=ss.grad.detach().numpy();fd=[]
    for k in range(4):
        plus=ss.detach().clone();minus=ss.detach().clone();plus[0,k]+=1e-6;minus[0,k]-=1e-6;vp,_=marching_tetrahedra(vv,tt,plus);vm,_=marching_tetrahedra(vv,tt,minus);fd.append(float((vp[0].sum()-vm[0].sum())/2e-6))
    save('metrics/DMTET_DERIVATIVE_TEST.json',dict(passed=bool(np.max(abs(analytic-np.array(fd)))<1e-7),analytical=analytic,finite_difference=fd,official_source_unmodified=True))
    print('CONTROL_READY',p['fit_views'],'tet extraction',time.time()-t,flush=True)
if __name__=='__main__':main()
