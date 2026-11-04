"""Only two cases; audit all same-video candidates and freeze source pools."""
from inputs import *
def farthest(uv,count=512):
    best=np.full(len(uv),np.inf);chosen=[];ix=int(np.argmin(((uv-uv.mean(0))**2).sum(1)))
    for _ in range(min(count,len(uv))):chosen.append(ix);best=np.minimum(best,((uv-uv[ix])**2).sum(1));best[chosen]=-1;ix=int(np.argmax(best))
    return np.array(chosen)
def main():
    assert not(R/'config/LOCKED_PROTOCOL.json').exists()
    scenes={'G01_004':dict(initial='E2',P1=['G01_004_ref08','G01_004_ref13','G01_004_ref03'],former_B='G01_004_growth_r14',tier='CONDITIONAL_RESEARCH_ALL_ARE_INSUFFICIENT_EVIDENCE'), 'G06_004':dict(initial='E1',P1=['G06_004_growth_r01','G06_004_growth_r03','G06_004_growth_r06'],former_B='G06_004_growth_r06',tier='CONDITIONAL_RESEARCH_MIXED_GATE')};audit=[];manifest=[]
    for scene,sc in scenes.items():
        legal=[]
        for cid,c in sorted(CC.items()):
            if c['scene_id']!=scene:continue
            gate=GATE.get(cid,{});cleanup=N0/'frozen_inputs/native'/(cid+'.npz');reasons=[]
            if gate.get('qualification')=='UNQUALIFIED_GEOMETRY':reasons.append('GEOMETRIC_CONTRADICTION')
            if not gate.get('Ring_pass'):reasons.append('RING_NOT_PASSED')
            if gate.get('admission')!='CONDITIONAL_RESEARCH_INPUT':reasons.append('NO_EXISTING_RESEARCH_ADMISSION')
            if not cleanup.exists():reasons.append('CURRENT_CLEANUP_MISSING')
            if not reasons:legal.append(cid)
            audit.append(dict(source=cid,scene=scene,qualification=gate.get('qualification'),block=gate.get('block'),Ring_pass=gate.get('Ring_pass'),current_cleanup_exists=cleanup.exists(),admitted=not reasons,reasons=reasons,strict_certification=False,former_B=cid==sc['former_B'],heldout_this_task=False))
        sc['P2']=list(dict.fromkeys(sc['P1']+legal));assert set(sc['P1'])<=set(legal)
    pr=dict(task=R.name,date='2026-11-05 Asia/Shanghai',parent_commit='b8c41565d467c922fdf2f45d3a4adf92f332813d',case_order=list(scenes),scenes=scenes,stop=dict(minimum_candidates=10,cumulative_rejection_fraction_gt=.5,rolling_window=10,rolling_rejection_fraction_gt=.5,count_backtracking_and_feasible_direction_trials=True,scope='GLOBAL_STOP_NO_SECOND_CASE_ON_TRIGGER',P0_infeasible_global_stop=True),P0=dict(solver='single SLSQP solve, nine live parameters',max_iterations=60,gap_mm=.05,minimum_volume_ratio=.85,axis_ratio_bounds=[.8,1.25],center_domain_equivalent_diameter_fraction=.25,rotation_component_change_rad=.5,mean_Mask_IoU_drop_max=.03,per_view_Mask_IoU_drop_max=.05,relative_depth_MAE_increase_mm_max=.15,native_hit_fraction_drop_max=.05,clearance_certification='1-Lipschitz ellipsoid level on CAD barycentric subdivision4 + covering radius; full-mesh FCL; O3D signs; independent Blender BVH and EXACT Boolean'),P1=dict(modes=12,max_iterations=12,ftol=1e-3),P2=dict(modes=32,max_iterations=18,ftol=1e-5),optimizer=dict(method='residual Gauss-Newton LM + SLSQP feasible-direction QP',lambda_initial=.01,lambda_good_factor=.33,lambda_bad_factor=3.,candidate_trials_per_iteration=4,pixel_radius='max(1,p75 real bidirectional contour error); image Jacobian bound, no uniform world-mm step cap',rho_good=.75,rho_bad=.25),loss=dict(Mask=1.,Depth=1.,HERO=.1,Reg=.02,contour_sigma_archive_px=3.,relative_depth_sigma_mm=.25,HERO_sigma_mm=.5,pose_prior=.002,RGB_photometric=0.,Base=0.),accept=dict(per_view_contour_increase_from_newP0_px_max=.5,native_coverage_drop_from_newP0=.05,no_intersection=True,actual_mesh_path='adaptive whole-triangle FCL separation certificate on linear vertex path, max depth8',min_triangle_area_ratio=.15),fixed_ROI_and_metric=True,GT=False,camera_update=False,cleanup_update=False,DXY_readonly=True,official_ring_unchanged=True,independent_holdout=False,no_80_arm_restart=True)
    save('config/LOCKED_PROTOCOL.json',pr);table('metrics/VIEW_QUALIFICATION.csv',audit)
    for scene,sc in scenes.items():
        for cid in sc['P2']:
            prior=PARENT/'inputs'/(cid+'.npz');dest=R/'inputs'/(cid+'.npz')
            if prior.exists():dest.write_bytes(prior.read_bytes())
            else:
                n=cleaned(cid);s=source(cid);z=n['depth'];h,w=z.shape;mask=n['native_labels']==1;dt=cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);jump=np.zeros(z.shape)
                for axis in [0,1]:
                    for step in [-1,1]:jump=np.maximum(jump,abs(z-np.roll(z,step,axis)))
                valid=n['valid']&mask&(dt>2)&(jump<=.75)&(n['native_RGB'].min(2)<245);v,u=np.nonzero(valid);uv=np.c_[u,v];cad=cast(ringscene(scene),uv,n['Kn'],s['T'])[0];uv=uv[z[v,u]<=cad+.05];uv=uv[farthest(uv)];zz=z[uv[:,1],uv[:,0]].astype(float);assert len(uv)==512;pairs=np.c_[np.arange(256),np.arange(256)+256]
                np.savez_compressed(dest,uv=uv,pixel_id=uv[:,1]*w+uv[:,0],z=zz,X=unproject(zz,s['T'],uv,n['Kn']),pairs=pairs,delta=zz[pairs[:,0]]-zz[pairs[:,1]],Kn=n['Kn'],K=s['K'],T=s['T'],cad=cast(ringscene(scene),uv,n['Kn'],s['T'])[0])
            for key in ['RGB','Mask','camera_file','pack','mesh','source_points']:manifest.append(asset(CC[cid][key]))
            manifest.extend([asset(CC[cid]['E1_actual_native']['path']),asset(N0/'frozen_inputs/native'/(cid+'.npz')),asset(CC[cid]['Ring_CAD']['path'])])
        row=p0(scene,sc['initial']);save('inputs/'+scene+'_historical_P0.json',row)
        cad=ringmesh(scene);np.savez_compressed(R/'inputs'/(scene+'_CAD.npz'),V=cad.vertices,F=cad.faces)
    save('assets_index/SOURCES.json',manifest);save('metrics/INPUT_FREEZE.json',dict(protocol=asset(R/'config/LOCKED_PROTOCOL.json'),inputs=[asset(p)for p in sorted((R/'inputs').glob('*'))],Camera_Gate=asset(N0/'config/CAMERA_GATE_RESULTS.json'),parent_P0=asset(A1/'metrics/PRIMARY_A_ONLY.json')))
    print('PREPARED',[(s,len(c['P1']),len(c['P2']))for s,c in scenes.items()],flush=True)
if __name__=='__main__':main()
