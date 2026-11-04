from losses import *
def main():
    K=np.array([[450.,0,320],[0,450,180],[0,0,1.]]);T=np.eye(4);T[:3,:3]=np.diag([1,-1,-1]);T[:3,3]=[0,0,30];p=np.r_[np.zeros(6),np.log([4.,3.,2.])];R0=np.eye(3);u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()];z=first_depth(p,R0,vis.camera_rays(uv,K,T));mask=np.isfinite(z).reshape(360,640);labels=mask.astype(np.uint8);empty=mesh_scene(np.empty((0,3)),np.empty((0,3),int));cad=np.full(14400,np.inf);target=target_data(mask,labels,cad,T,K)
    def fun(x,t=target):return np.concatenate(two_d_parts(x,R0,t,K,T,empty))
    base=fun(p);moved=p.copy();moved[0]=.5;scaled=p.copy();scaled[6]+=.2;tests=[]
    tests.append(dict(name='true_mask_lower_loss_than_translation_or_scale',passed=float(base@base)<min(float(fun(moved)@fun(moved)),float(fun(scaled)@fun(scaled))),true_cost=float(base@base),translation_cost=float(fun(moved)@fun(moved)),scale_cost=float(fun(scaled)@fun(scaled))))
    js=[]
    for h in [.001,.0005]:js.append(np.column_stack([(fun(p+np.eye(9)[j]*h)-fun(p-np.eye(9)[j]*h))/(2*h)for j in range(9)]))
    diff=float(np.linalg.norm(js[0]-js[1])/np.linalg.norm(js[1]));tests.append(dict(name='mask_residual_gradient_finite_and_two_steps',passed=np.isfinite(js[1]).all()and diff<.1,J_relative_difference=diff,translation_gradient_norm=float(np.linalg.norm(js[1][:,:3]))))
    # Same outer convex support, genuinely different full mask: central known hole.
    hole=mask.copy();hole[170:190,308:332]=False;th=target_data(hole,hole.astype(np.uint8),cad,T,K);rh=fun(p,th);directions=np.c_[np.cos(np.arange(24)*2*np.pi/24),np.sin(np.arange(24)*2*np.pi/24)];support_same=np.array_equal((contour(mask)@directions.T).max(0),(contour(hole)@directions.T).max(0))
    tests.append(dict(name='full_mask_detects_nonconvex_hole_24_support_misses',passed=support_same and float(rh@rh)>float(base@base)+.01,same_24_support=support_same,base_cost=float(base@base),hole_cost=float(rh@rh)))
    ring=np.zeros_like(mask);ring[170:190,308:332]=True;lab=labels.copy();lab[ring]=2;observed=mask&~ring;tr=target_data(observed,lab,cad,T,K);unknown_grid=ring.reshape(90,4,160,4).mean((1,3)).ravel()==1
    tests.append(dict(name='Ring_pixels_unknown_not_negative_polyp_evidence',passed=bool((tr['region_weights'][unknown_grid]==0).all())and not len(tr['boundary'][ring[tr['boundary'][:,1].astype(int),tr['boundary'][:,0].astype(int)]]),unknown_grid_N=int(unknown_grid.sum())))
    # Exact analytic roots avoid the previous star-grid failure class.
    P,F=mesh(p,R0);tm=cast(mesh_scene(P,F),uv,K,T)[0];hit=np.isfinite(z)&np.isfinite(tm);err=abs(z[hit]-tm[hit]);tests.append(dict(name='ellipsoid_axial_roots_vs_actual_triangles',passed=bool(np.median(err)<.01 and np.quantile(err,.95)<.1),common_hit_N=int(hit.sum()),depth_error_mm=stats(err),rays_parameter='axial camera Z, not unit-ray range'))
    p_cad=p.copy();p_cad[2]=-2.5;p_cad[6:9]=np.log([7.,5.,2.]);rg=ringscene('G01_004');cz=cast(rg,uv,K,T)[0];pz=first_depth(p_cad,R0,vis.camera_rays(uv,K,T));blocked=np.isfinite(pz)&np.isfinite(cz)&(pz>cz+.05);visible=(np.isfinite(pz)&~blocked).reshape(360,640);lab_cad=visible.astype(np.uint8);lab_cad[np.isfinite(cz).reshape(360,640)]=2;actualgrid=target['grid'];gridCAD=cast(rg,actualgrid,K,T)[0];tc=target_data(visible,lab_cad,gridCAD,T,K);visib=cad_visibility(p_cad,R0,tc['grid_rays'],gridCAD)
    clearly_behind=np.isfinite(gridCAD)&(first_depth(p_cad,R0,tc['grid_rays'])>gridCAD+.5)
    tests.append(dict(name='actual_frozen_CAD_occlusion_order_control',passed=bool(blocked.sum()>0 and clearly_behind.sum()>0 and (visib[clearly_behind]<.02).all()),blocked_pixels=int(blocked.sum()),clear_behind_grid_N=int(clearly_behind.sum()),CAD=asset(CC['G01_004_ref08']['Ring_CAD']['path']),synthetic_control=True))
    # Same inputs -> same residual, including when report-only class names change.
    import fitting,copy
    one=fitting.Problem('G01_004','E1');two=fitting.Problem('G01_004','E2');one.targets=two.targets
    r1=one.residual(one.base);r2=two.residual(two.base);saved=fitting.protocol;renamed=copy.deepcopy(protocol())
    for x in renamed['scenes'].values():x['kind']='ARBITRARY_METADATA_ONLY'
    fitting.protocol=lambda:renamed
    relabeled=fitting.Problem('G01_004','E2');r3=relabeled.residual(relabeled.base);fitting.protocol=saved
    tests.append(dict(name='same_target_arm_identity_and_class_metadata_invariance',passed=np.array_equal(r1,r2)and np.array_equal(r2,r3),max_arm_residual_difference=float(abs(r1-r2).max()),max_class_label_difference=float(abs(r2-r3).max())))
    save('metrics/SYNTHETIC_TESTS.json',dict(tests=tests,all_pass=all(x['passed']for x in tests),GT='GENERATED_CONTROL_ONLY_NO_REAL_GT'));table('metrics/SYNTHETIC_TESTS.csv',tests);np.savez_compressed(R/'local_results/Synthetic_Mask_Controls.npz',full=mask,hole=hole,Ring=ring)
    print(json.dumps(clean(tests),indent=2),flush=True);assert all(x['passed']for x in tests)
if __name__=='__main__':main()
