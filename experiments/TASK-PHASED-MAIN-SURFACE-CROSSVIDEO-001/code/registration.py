"""Bounded mature Open3D robust GICP; original background coordinates preserved."""
from model import *
from scipy.spatial.transform import Rotation
def o3d_module():
    sys.path.insert(0,str(OLD/'surface_fusion_v3/vendor'));import open3d as o3d;return o3d
def transform(P,H):return np.asarray(P)@np.asarray(H)[:3,:3].T+np.asarray(H)[:3,3]
def rotangle(RR):return float(np.degrees(np.arccos(np.clip((np.trace(RR)-1)/2,-1,1))))
def ring_geometry(H):return dict(center_mm=float(np.linalg.norm(H[:3,3])),normal_degrees=float(np.degrees(np.arccos(np.clip(H[2,2],-1,1)))),scale_singular_values=np.linalg.svd(H[:3,:3])[1],SE3=bool(np.allclose(H[3],[0,0,0,1])and np.allclose(H[:3,:3].T@H[:3,:3],np.eye(3),atol=1e-6)and np.linalg.det(H[:3,:3])>0))
def quality(cid,other_ids):
    b=background(cid);P=b['P'];support=np.zeros(len(P),int);front=np.zeros(len(P),bool);q=cfg()
    for other in other_ids:
        p=source(other)['p'];uv,z=vis.project_camera(P,p['K'],p['pose']);xy=np.rint(uv).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(inside);x,y=xy[ids].T;valid=(p['labels'][y,x]==0)&np.isfinite(p['depth_mm'][y,x]);ids=ids[valid];x,y=xy[ids].T;r=z[ids]-p['depth_mm'][y,x];support[ids[abs(r)<=q['background_fit_consistency_mm']]]+=1;front[ids[r<-q['background_fit_consistency_mm']]]=True
    good=b['quality']&(support>=1)&~front;return good,support,front
def working_cloud(parts):
    P=np.r_[tuple(x['P']for x in parts)]if parts else np.empty((0,3));ref=np.concatenate([np.full(len(x['P']),i,int)for i,x in enumerate(parts)])if parts else np.empty(0,int);ids=np.r_[tuple(x['ids']for x in parts)]if parts else np.empty(0,int)
    if not len(P):return P,ref,ids
    vox=np.floor(P/cfg()['registration_voxel_mm']).astype(np.int64);_,idx=np.unique(vox,axis=0,return_index=True);idx.sort();return P[idx],ref[idx],ids[idx]
def background_sets():
    spec=[];clouds={}
    for scene in load(R/'metrics/D0_scenes.json'):
        video=scene['video'];main=scene['main_reference'];cc=scene['all_available_references'];C=source(main)['p']['pose'][:3,3];other=max([c for c in cc if c!=main],key=lambda c:np.linalg.norm(source(c)['p']['pose'][:3,3]-C));fit_ids=[main,other];held=next(c for c in cc if c not in fit_ids);parts=[];rows=[]
        for cid in cc:
            b=background(cid);others=[c for c in fit_ids if c!=cid];good,support,front=quality(cid,others);ids=np.flatnonzero(good);role='FIT'if cid in fit_ids else'GEOMETRIC_HOLDOUT_MODEL_CONDITIONAL';rows.append(dict(reference=cid,role=role,raw_background_N=len(b['P']),fit_ROI_N=int(b['fit_roi'].sum()),quality_N=int(b['quality'].sum()),consistent_nonconflict_N=len(ids),display_N=int(b['display'].sum()),display_mask_used_for_fit=False));np.savez_compressed(R/f'local_results/background/{cid}_registration_indices.npz',fit_good=good,support=support,front=front,source_original_ids=ids,role=role)
            if cid in fit_ids:parts.append(dict(P=b['P'][ids],ids=ids,reference=cid))
        P,ref,ids=working_cloud(parts);held_good,_sup,_front=quality(held,fit_ids);HP=background(held)['P'][held_good];clouds[video]=(P,HP);np.savez_compressed(R/f'local_results/background/{video}_working.npz',XYZ_mm=P,source_fit_reference_index=ref,source_original_id=ids,heldout_XYZ_mm=HP,fit_reference_ids=np.array(fit_ids),heldout_reference_id=held);spec.append(dict(video=video,fit_references=fit_ids,geometric_holdout=held,working_points=len(P),heldout_points=len(HP),rows=rows,voxel_selection='one unchanged original point per 0.25mm voxel, no scene downsampling'))
    save('provenance/D1_FIT_SELECTION_FROZEN.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),scenes=spec,source_sha256=sha(Path(__file__)),before_cross_video_optimization=True));csvsave('metrics/background_registration_support.csv',[dict(video=x['video'],**r)for x in spec for r in x['rows']]);return clouds
def cloud(P):
    o=o3d_module();c=o.geometry.PointCloud(o.utility.Vector3dVector(P));param=o.geometry.KDTreeSearchParamHybrid(radius=cfg()['registration_covariance_radius_mm'],max_nn=cfg()['registration_covariance_max_nn']);c.estimate_normals(param);c.estimate_covariances(param);return c
def pair_stats(P,Q,H,normals=None):
    if not len(P)or not len(Q):return dict(source_N=len(P),target_N=len(Q),nearest_mm=stats([]),point_to_plane_mm=stats([]),within_05_fraction=None)
    T=transform(P,H);d,idx=cKDTree(Q).query(T,workers=1);r=np.abs(np.sum((T-Q[idx])*normals[idx],axis=1))if normals is not None else d;return dict(source_N=len(P),target_N=len(Q),nearest_mm=stats(d),point_to_plane_mm=stats(r),within_05_fraction=float((d<=cfg()['geometry_distance_support_mm']).mean()))
def observation(P,Q,H,normals):
    if not len(P)or not len(Q):return dict(raw_information_eigen_ratio=0.,Ring_augmented_eigen_ratio=0.,yaw_conditional_information=0.,geometry_eigen_ratio=0.,source_N=len(P))
    T=transform(P,H);d,idx=cKDTree(Q).query(T);valid=d<=cfg()['registration_max_correspondence_mm'];X=T[valid];N=normals[idx[valid]];J=np.c_[np.cross(X,N)/12.4,N];info=J.T@J/max(1,len(J));ev=np.linalg.eigvalsh(info);aug=info+np.diag([1.,1.,0.,1.,1.,1.]);ae=np.linalg.eigvalsh(aug);pe=np.linalg.eigvalsh(np.cov(T.T));return dict(correspondences=int(valid.sum()),raw_information_eigenvalues=ev,raw_information_eigen_ratio=float(max(0,ev[0])/max(ev[-1],1e-12)),Ring_augmented_eigenvalues=ae,Ring_augmented_eigen_ratio=float(max(0,ae[0])/max(ae[-1],1e-12)),yaw_conditional_information=float(info[2,2]),geometry_eigen_ratio=float(max(0,pe[0])/max(pe[-1],1e-12)),interpretation='conditional point-to-plane geometry plus 5 Ring priors; not absolute pose observability or truth')
def run_D1():
    verify();q=cfg();clouds=background_sets();P4,H4=clouds['004'];P5,H5=clouds['005'];o=o3d_module();old=load(ICF/'inputs/H_frozen.json');yaw=np.angle(np.mean([np.exp(1j*np.arctan2(np.array(x['H'])[1,0],np.array(x['H'])[0,0]))for x in old]));seeds=[dict(tag=x['tag'],H=np.array(x['H']))for x in old]
    for name,delta in [('RingYaw',0),('RingYaw_minus5',-q['seed_yaw_perturbation_degrees']),('RingYaw_plus5',q['seed_yaw_perturbation_degrees'])]:H=np.eye(4);H[:3,:3]=Rotation.from_euler('z',yaw+np.deg2rad(delta)).as_matrix();seeds.append(dict(tag=name,H=H))
    save('provenance/D1_INITIALIZATIONS_FROZEN.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),H_direction='005_to_004',units='mm',initializations=seeds,config=q));rows=[];enough=min(len(P4),len(P5))>=q['registration_minimum_points_per_video'];c4=cloud(P4)if len(P4)>=3 else None;c5=cloud(P5)if len(P5)>=3 else None;N4=np.asarray(c4.normals)if c4 is not None else None;N5=np.asarray(c5.normals)if c5 is not None else None
    def record(tag,H,initial,solver,trace,is_new):
        g=ring_geometry(H);f=pair_stats(P5,P4,H,N4);b=pair_stats(P4,P5,np.linalg.inv(H),N5);yawdiff=abs(np.degrees(np.arctan2(np.sin(np.arctan2(H[1,0],H[0,0])-np.arctan2(initial[1,0],initial[0,0])),np.cos(np.arctan2(H[1,0],H[0,0])-np.arctan2(initial[1,0],initial[0,0])))));valid=g['SE3']and g['center_mm']<=q['ring_translation_bound_mm']and g['normal_degrees']<=q['ring_normal_bound_degrees']and yawdiff<=q['yaw_step_bound_degrees'];metric=(f['point_to_plane_mm']['median']or 1e3)+(b['point_to_plane_mm']['median']or 1e3)+.1*g['center_mm'];row=dict(tag=tag,is_new=is_new,H_005_to_004=H,initial_H=initial,solver_status=solver,trace=trace,Ring=g,yaw_change_degrees=yawdiff,reasonable_bounds=bool(valid),training_score=metric,forward_background=f,reverse_background=b,heldout_forward=pair_stats(H5,H4,H),observability=observation(P5,P4,H,N4)if N4 is not None else{},status='DISPLAY_CANDIDATE_NOT_CERTIFIED'if valid else'deprecated_candidate');rows.append(row);return row
    for seed in seeds[:2]:record('HISTORICAL_'+seed['tag'],seed['H'],seed['H'],'HISTORICAL_UNCHANGED',[],False)
    if enough:
        reg=o.pipelines.registration;est=reg.TransformationEstimationForGeneralizedICP(q['registration_generalized_epsilon'],reg.HuberLoss(q['registration_Huber_k_mm']));criteria=reg.ICPConvergenceCriteria(1e-8,1e-8,5)
        for seed in seeds:
            H=seed['H'].copy();trace=[];status='MAX_ITERATION_BUDGET_RETURNED'
            for block in range(q['registration_iterations']//5):
                result=reg.registration_generalized_icp(c5,c4,q['registration_max_correspondence_mm'],H,est,criteria);new=np.asarray(result.transformation).copy();stepT=np.linalg.norm(new[:3,3]-H[:3,3]);stepR=rotangle(new[:3,:3]@H[:3,:3].T);trace.append(dict(block=block+1,iteration_upper_bound=5*(block+1),fitness=float(result.fitness),inlier_rmse_mm=float(result.inlier_rmse),translation_step_mm=stepT,rotation_step_deg=stepR));H=new;g=ring_geometry(H)
                if g['center_mm']>q['ring_translation_bound_mm']or g['normal_degrees']>q['ring_normal_bound_degrees']:status='STOPPED_RING_BOUNDS';break
                if block>=1 and stepT<1e-4 and stepR<1e-4:status='CONVERGED_ENDPOINT_STABLE';break
            row=record('GICP_'+seed['tag'],H,seed['H'],status,trace,True);print('GICP',seed['tag'],status,'ring',row['Ring']['center_mm'],row['Ring']['normal_degrees'],'train',row['training_score'],flush=True)
    eligible=[r for r in rows if r['reasonable_bounds']];best=min(eligible or rows,key=lambda r:r['training_score']);H=np.array(best['H_005_to_004']);near=[]
    for r in rows:
        if r['is_new']and r['reasonable_bounds']:
            Q=np.array(r['H_005_to_004']);near.append(dict(tag=r['tag'],rotation_deg=rotangle(Q[:3,:3]@H[:3,:3].T),translation_mm=np.linalg.norm(Q[:3,3]-H[:3,3])))
    stable=sum(r['rotation_deg']<=q['stable_initializations_rotation_degrees']and r['translation_mm']<=q['stable_initializations_translation_mm']for r in near)>=3;decision=dict(best_candidate=best['tag'],H_005_to_004=H,H_direction='005_to_004',units='millimeters',selection='training background symmetry score plus Ring penalty; holdout RGB not used',working_input_qualified=enough,initialization_stability=near,multiple_initializations_stable=bool(stable),Ring=best['Ring'],observability=best['observability'],status='REGISTRATION_CANDIDATE_NOT_YET_FUSED',backup='NOT_RUN; classify geometry/holdout first. No new method search without independent constraint.',GT_used=False)
    save('metrics/D1_candidates.json',rows);csvsave('metrics/D1_candidates.csv',rows);save('metrics/D1_decision.json',decision);print('D1 SELECTED',best['tag'],'enough background',enough,'stable',stable,flush=True)
if __name__=='__main__':run_D1()
