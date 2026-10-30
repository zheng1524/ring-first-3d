"""Complete-original-face growth with frontier anchors and bounded joint SE3.

No pointwise F2 admission, no remeshing, no averaging/smoothing or GT.
"""
from frontier import *
from scipy.sparse.csgraph import dijkstra
from scipy.linalg import fractional_matrix_power
import copy,time
EXPLAINED,NOVEL,OCCLUDED,CONFLICT,UNKNOWN=range(5)
LABELS=['OVERLAP_ANCHOR','FRONTIER_EXTENSION','OCCLUDED','OVERLAP_CONFLICT','UNKNOWN']
def selected_mask(cid):return cleaned(cid)['clean_removed']
for node in ast.parse((GRAZ/'code/aggregation.py').read_text()).body:
    if isinstance(node,ast.FunctionDef)and node.name=='classify':exec(compile(ast.Module(body=[node],type_ignores=[]),str(GRAZ/'code/aggregation.py'),'exec'),globals())
def scene_query(blocks,P):
    a=mesh_arrays(blocks);sc=mesh_scene(a['P'],a['F']);out=sc.compute_closest_points(o3d().core.Tensor(P.astype(np.float32)));idx=out['primitive_ids'].numpy().astype(int);Q=out['points'].numpy();return a,Q,np.linalg.norm(Q-P,axis=1),idx
def group_H(blocks,cid,component):
    bb=[b for b in blocks if b['reference']==cid and b['original_component']==component];return np.array(max(bb,key=lambda b:len(b['face_ids']))['H'])if bb else np.eye(4)
def replace_group_H(blocks,cid,component,H):
    for b in blocks:
        if b['reference']==cid and b['original_component']==component:b['H']=H.copy()
def motion_ok(H,role):
    max_t=cfg()['growth_primary_max_derived_translation_mm']if role.startswith('PRIMARY')else cfg()['growth_max_derived_translation_mm'];return np.linalg.norm(H[:3,3])<=max_t and rotangle(H)<=cfg()['growth_max_derived_rotation_deg']
def joint_alignment(blocks,cid,component,P,N,ids,old_indices,Q,oldnorm,base_H):
    """GICP in an overlap band; planar bands use a bounded normal translation.

    A confidence-weighted SE3 split lets BOTH old and new source components
    move. Entire original components stay rigid; CAD/cameras never move.
    """
    a=mesh_arrays(blocks);bid=a['face_blocks'][old_indices];dominant=int(np.bincount(bid).argmax());sel=bid==dominant;ids=ids[sel];Q=Q[sel];oldnorm=oldnorm[sel];rec=dict(attempted=False,method='NONE',anchor_points=len(ids),dominant_old_block=blocks[dominant]['id'],old_component_rigid=True,new_component_rigid=True)
    if len(ids)<cfg()['growth_anchor_min_points']:return blocks,base_H,rec
    if blocks[dominant]['reference']==cid and blocks[dominant]['original_component']==component:
        rec.update(method='SAME_ORIGINAL_COMPONENT_TOPOLOGICAL_ANCHOR',seam_before_mm=stats(np.linalg.norm(P[ids]-Q,axis=1)),seam_after_mm=stats(np.linalg.norm(P[ids]-Q,axis=1)));return blocks,base_H,rec
    A=P[ids];err=np.linalg.norm(A-Q,axis=1);rec['seam_before_mm']=stats(err)
    if np.median(err)<.05:rec['method']='ALREADY_ALIGNED_WITHIN_SAMPLING';rec['seam_after_mm']=stats(err);return blocks,base_H,rec
    split=(source(cid)['uv'][ids,0]//16+3*(source(cid)['uv'][ids,1]//16))%5==0;train=~split
    if train.sum()<12:return blocks,base_H,rec
    n=oldnorm[train].mean(0);n/=max(np.linalg.norm(n),1e-12);dispersion=np.mean(np.linalg.norm(oldnorm[train]-n,axis=1));T=np.eye(4);rec.update(attempted=True,planar_normal_dispersion=float(dispersion))
    if dispersion<.15:
        shift=float(np.median(((Q-A)[train]*n).sum(1)));T[:3,3]=np.clip(shift,-cfg()['growth_max_derived_translation_mm'],cfg()['growth_max_derived_translation_mm'])*n;rec['method']='ROBUST_NORMAL_POINT_TO_PLANE_JOINT_SHIFT_DEGENERATE_BAND'
    else:
        o=o3d();aa=o.geometry.PointCloud();aa.points=o.utility.Vector3dVector(A[train]);bb=o.geometry.PointCloud();bb.points=o.utility.Vector3dVector(Q[train]);bb.normals=o.utility.Vector3dVector(oldnorm[train]);reg=o.pipelines.registration.registration_generalized_icp(aa,bb,cfg()['growth_anchor_radius_mm'],np.eye(4),o.pipelines.registration.TransformationEstimationForGeneralizedICP(),o.pipelines.registration.ICPConvergenceCriteria(max_iteration=cfg()['growth_registration_max_iterations']));T=np.array(reg.transformation);rec.update(method='OPEN3D_GENERALIZED_ICP_JOINT_SE3_SPLIT',GICP_fitness=float(reg.fitness),GICP_inlier_rmse_mm=float(reg.inlier_rmse))
    old=blocks[dominant];wold=old['stiffness'];wnew=cfg()['growth_candidate_stiffness'];fraction=wnew/(wold+wnew);oldDelta=np.real_if_close(fractional_matrix_power(np.linalg.inv(T),fraction)).real;newDelta=np.real_if_close(fractional_matrix_power(T,1-fraction)).real;Ho=oldDelta@np.array(old['H']);Hn=newDelta@base_H;rec.update(relative_correction=T,old_delta=oldDelta,new_delta=newDelta,new_H=Hn,old_H=Ho)
    if not motion_ok(Ho,old['role'])or not motion_ok(Hn,'NEW'):rec['reason']='BOUNDED_COMPONENT_MOTION_EXCEEDED';return blocks,base_H,rec
    adjusted=copy.deepcopy(blocks);replace_group_H(adjusted,old['reference'],old['original_component'],Ho);newP=transform(source(cid)['P'],Hn);_,QQ,dd,_=scene_query(adjusted,newP[ids]);after=dd;rec['seam_after_mm']=stats(after);held=split if split.any()else np.ones(len(ids),bool);improve=float(np.median(after[train])/(np.median(err[train])+1e-12));supported=additional_mask_support(newP[ids],train_neighbor(cid));oldids=np.unique(source(old['reference'])['F'][old['face_ids']]);old_support=additional_mask_support(block_P(next(b for b in adjusted if b['id']==old['id']))[oldids],train_neighbor(old['reference']));ok=improve<=1-cfg()['growth_registration_min_improvement_fraction']and np.quantile(after[held],.95)<=max(cfg()['growth_max_seam_p95_mm'],np.quantile(err[held],.95))and supported.mean()>=cfg()['growth_training_Mask_min_support']and old_support.mean()>=cfg()['growth_training_Mask_min_support'];rec.update(accepted=bool(ok),training_median_ratio=improve,held_band_after_mm=stats(after[held]),candidate_training_Mask_fraction=float(supported.mean()),old_training_Mask_fraction=float(old_support.mean()),reason='BOUNDED_OVERLAP_AND_NONHELD_IMAGE_SUPPORT'if ok else'NO_SUPPORTED_JOINT_IMPROVEMENT')
    if not ok:return blocks,base_H,rec
    replace_group_H(adjusted,cid,component,Hn);return adjusted,Hn,rec
def face_adjacency(F,P):
    E,start,count,face,_=edge_data(F);ix=np.flatnonzero(count==2);pairs=np.c_[face[start[ix]],face[start[ix]+1]];centers=P[F].mean(1);weights=np.linalg.norm(centers[pairs[:,0]]-centers[pairs[:,1]],axis=1);return pairs,weights
def attempt_component(blocks,cid,fids,round_id,allow_joint=True,H_initial=None):
    s=source(cid);component=int(face_components(s['F'])[fids[0]]);already=np.array(sorted({int(f)for b in blocks if b['reference']==cid for f in b['face_ids']}),int);available=~np.isin(fids,already);rec=dict(reference=cid,original_component=component,source_component_faces=len(fids),remaining_faces=int(available.sum()),status='CANDIDATE',accepted=False)
    if available.sum()<cfg()['growth_min_complete_patch_faces']:rec.update(status='REJECTED',reason='ALREADY_EXPLAINED_SOURCE_FACE_IDS');return None,rec
    H0=group_H(blocks,cid,component)if H_initial is None else np.asarray(H_initial);P=transform(s['P'],H0);N=normal(cid)[0]@H0[:3,:3].T;rel=normal(cid)[1];ids=np.unique(s['F'][fids]);fr=frontier(blocks);fi=np.flatnonzero(fr['eligible'])
    if not len(fi):rec.update(status='REJECTED',reason='NO_ELIGIBLE_GROWTH_FRONTIER');return None,rec
    fd,_=cKDTree(fr['midpoints'][fi]).query(P[ids]);edge_length=np.linalg.norm(P[s['F'][fids,0]]-P[s['F'][fids,1]],axis=1);band=min(cfg()['growth_frontier_band_cap_mm'],max(cfg()['growth_frontier_band_min_mm'],cfg()['growth_frontier_band_spacing_multiple']*np.median(edge_length)));near=ids[(fd<=band)&rel[ids]]
    if len(near)<cfg()['growth_anchor_min_points']:rec.update(status='REJECTED',reason='NO_SOURCE_CONNECTED_FRONTIER_ANCHOR',frontier_band_mm=band);return None,rec
    arrays,Q,dist,face_idx=scene_query(blocks,P[near]);norm=arrays['face_normals'][face_idx];cosine=(N[near]*norm).sum(1);ok=(dist<=cfg()['growth_anchor_radius_mm'])&(cosine>=np.cos(np.deg2rad(cfg()['growth_normal_max_degrees'])));anchors=near[ok];rec.update(overlap_anchor_points=len(anchors),frontier_band_mm=band)
    if len(anchors)<cfg()['growth_anchor_min_points']:rec.update(status='CONFLICT'if np.median(dist)>cfg()['growth_anchor_radius_mm']else'REJECTED',reason='NO_MEANINGFUL_FRONTIER_OVERLAP_BAND',seam_candidate_mm=stats(dist));return None,rec
    candidate_blocks=blocks;H=H0;alignment=dict(attempted=False)
    if allow_joint:candidate_blocks,H,alignment=joint_alignment(blocks,cid,component,P,N,anchors,face_idx[ok],Q[ok],norm[ok],H0)
    rec['joint_alignment']=alignment;arrays=mesh_arrays(candidate_blocks);t=target_source(cid);status,delta,proj=classify(arrays['P'],arrays['F'],s,t,H);P=transform(s['P'],H);F=s['F'][fids];no_bad=~np.isin(status[F],[OCCLUDED,CONFLICT,UNKNOWN]).any(1);novel=(status[F]==NOVEL).any(1);eligible=no_bad&novel&available;anchorfaces=(status[F]==EXPLAINED).all(1);pairs,weights=face_adjacency(F,P);starts=np.zeros(len(F),bool)
    if len(pairs):
        a,b=pairs.T;starts[b[anchorfaces[a]&eligible[b]]]=True;starts[a[anchorfaces[b]&eligible[a]]]=True
    if not starts.any():rec.update(status='CONFLICT'if(status[ids]==CONFLICT).any()else'REJECTED',reason='NO_COMPLETE_TRIANGLE_EXTENSION_ADJACENT_TO_ANCHOR',class_counts={k:int((status[ids]==j).sum())for j,k in enumerate(LABELS)});return None,rec
    fi=np.flatnonzero(frontier(candidate_blocks)['eligible']);front=frontier(candidate_blocks);tree=cKDTree(front['midpoints'][fi]);distance,_=tree.query(P[F[starts]].mean(1));ii=np.flatnonzero(starts);starts[ii[distance>band]]=False
    if not starts.any():rec.update(status='REJECTED',reason='ONLY_CLEANING_HOLE_OR_REMOTE_CUT_NOT_ACTIVE_FRONTIER');return None,rec
    both_eligible=eligible[pairs].all(1);pp=pairs[both_eligible];ww=weights[both_eligible];graph=coo_matrix((np.r_[ww,ww],(np.r_[pp[:,0],pp[:,1]],np.r_[pp[:,1],pp[:,0]])),shape=(len(F),len(F))).tocsr();geodesic=dijkstra(graph,directed=False,indices=np.flatnonzero(starts),min_only=True,limit=cfg()['growth_step_distance_mm']);take=eligible&np.isfinite(geodesic);parts=face_partitions(cid,fids[take]);parts=[p for p in parts if len(p)>=cfg()['growth_min_complete_patch_faces']]
    if not parts:rec.update(status='REJECTED',reason='NO_CONTINUOUS_COMPLETE_ORIGINAL_FACE_PATCH');return None,rec
    best=max(parts,key=lambda p:s['areas'][p].sum());ix=np.unique(s['F'][best]);support=additional_mask_support(P[ix],train_neighbor(cid));seam_edges,_,count,_,_=edge_data(s['F'][best]);seam_edges=seam_edges[count==1];edge_dist,_=tree.query(P[seam_edges].mean(1));seam=seam_edges[edge_dist<=band];seam_ids=np.unique(seam);a,Q,dist,idx=scene_query(candidate_blocks,P[seam_ids]);seam_p95=float(np.quantile(dist,.95))if len(dist)else 1e9;seam_length=float(np.linalg.norm(P[seam[:,0]]-P[seam[:,1]],axis=1).sum());rec.update(extension_original_face_ids=best,extension_points=len(ix),extension_complete_faces=len(best),delta_area_mm2=float(s['areas'][best].sum()),maximum_connected_original_face_area_mm2=float(s['areas'][best].sum()),seam_length_mm=seam_length,seam_distance_mm=stats(dist),training_neighbor=train_neighbor(cid)['id'],training_Mask_support=float(support.mean()),class_counts={k:int((status[ids]==j).sum())for j,k in enumerate(LABELS)},duplicate_overlap_faces_excluded=int(anchorfaces.sum()),candidate_H=H,original_XYZ_unchanged=True)
    if support.mean()<cfg()['growth_training_Mask_min_support']or seam_p95>cfg()['growth_max_seam_p95_mm']or seam_length<=0:rec.update(status='CONFLICT'if seam_p95>cfg()['growth_max_seam_p95_mm']else'REJECTED',reason='NEW_PATCH_IMAGE_OR_SEAM_NOT_SUPPORTED');return None,rec
    new=copy.deepcopy(candidate_blocks);existing=next((b for b in new if b['reference']==cid and b['original_component']==component and np.allclose(np.array(b['H']),H)),None)
    if existing is None:new.append(dict(id='growth_'+str(round_id)+'_'+cid,reference=cid,face_ids=best,H=H,generation=round_id,face_generations=np.full(len(best),round_id,int),role='BOUNDARY_GROWN_PATCH',stiffness=cfg()['growth_existing_patch_stiffness'],original_component=component))
    else:existing['face_ids']=np.r_[np.asarray(existing['face_ids']),best];existing['face_generations']=np.r_[np.asarray(existing['face_generations']),np.full(len(best),round_id,int)]
    rec.update(status='ACCEPTED',accepted=True,meaning='ENGINEERING_BOUNDARY_GROWTH_NOT_PHYSICAL_GT',reason='COMPLETE_ORIGINAL_FACE_CONNECTED_TO_FRONTIER_ANCHOR; JOINT_VERSION_SAVED',round=round_id);return new,rec
def attempt_reference(blocks,cid,round_id,allow_joint=True,H_initial=None):
    records=[];parts=face_partitions(cid);parts.sort(key=lambda p:-source(cid)['areas'][p].sum())
    for ids in parts:
        if len(ids)<cfg()['growth_raw_component_min_faces_for_attempt']:continue
        updated,record=attempt_component(blocks,cid,ids,round_id,allow_joint,H_initial);records.append(record)
        if updated is not None:return updated,records
    return None,records
def rank_references(sid,blocks):
    fr=frontier(blocks);ix=np.flatnonzero(fr['eligible']);P=fr['midpoints'][ix];length=fr['lengths'][ix];rows=[]
    for c in cases():
        if sceneid(c)!=sid:continue
        t=target_source(c['id']);support=additional_mask_support(P,t);quality=1.0 if c['source_camera_qualified']else .75;quality=.5 if'UNQUALIFIED'in c['condition']else quality;score=float(length[support].sum()*quality);rows.append(dict(reference=c['id'],visible_eligible_frontier_mm=float(length[support].sum()),score=score))
    return sorted(rows,key=lambda x:-x['score'])
