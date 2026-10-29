"""Source-preserving scene export, fixed-frame evaluation, independent cross gate."""
from ownership import *
def scene_ids():return list(load(R/'provenance/OWNERSHIP_ORDER_FROZEN.json')['orders'])
def eval_targets(sid):
    vv=views();held=[v for v in vv.values()if v['source_id']==sid.replace('_','_video',1)and v.get('role')=='HOLDOUT'];out=[];cid=load(R/'provenance/OWNERSHIP_ORDER_FROZEN.json')['orders'][sid][0]
    for v in held:out.append(dict(id=v['id'],RGB=v['RGB'],Mask=v['Mask'],K=np.array(v['K']),c2w=np.array(v['c2w']),ring_case=cid,role='A_FROZEN_HOLDOUT_NOT_USED_FOR_NEW_HERO_MATCH_OR_F2_SELECTION; not whole-pipeline blind'))
    if not out:
        t=dict(selection(sid));t['role']='DIAGNOSTIC_ONLY_NO_FROZEN_HELD_CAMERA; may be a source image';t['ring_case']=cid;out=[t]
    return out
def exports(sid,mode):
    a=pointset(sid,mode);folder=R/'local_results/glb';folder.mkdir(parents=True,exist_ok=True);npz=folder/(sid+'_'+mode+'_sources.npz');np.savez_compressed(npz,XYZ_mm=a['P'],RGB=a['C'],source_reference_index=a['reference_index'],source_original_id=a['original_ids'],source_uv=a['source_uv'],class_id=a['class_id'],reference_names=np.array(a['references']),coordinate_frame=sid+'_LOCAL_RING_MM',post_backprojection_point_motion_mm=0.)
    scene=trimesh.Scene()
    for j,cid in enumerate(a['references']):
        ix=a['reference_index']==j
        if not ix.any():continue
        g=trimesh.points.PointCloud(a['P'][ix]/1000,colors=np.rint(a['C'][ix]*255).astype(np.uint8));g.metadata.update(source_reference=cid,original_ids=a['original_ids'][ix].tolist(),source_uv=a['source_uv'][ix].tolist(),original_classes=a['class_id'][ix].tolist(),new_HERO=case(cid).get('new_reference',False),camera_identity=case(cid).get('camera_identity','HISTORICAL_FROZEN_CANDIDATE'));scene.add_geometry(g,node_name=cid+'_ACTUAL_SOURCE_POINTS')
    primary=a['references'][0];b=background(primary);g=trimesh.points.PointCloud(b['P']/1000,colors=np.rint(b['C']*255).astype(np.uint8));g.metadata.update(kind='ACTUAL_BACKGROUND_XYZ_DISPLAY_ONLY',source_reference=primary,source_cache_ids=b['ids'].tolist(),source_uv=b['uv'].tolist());scene.add_geometry(g,node_name='Background_DISPLAY_ONLY');m=source(primary)['ring'].copy();m.vertices=np.asarray(m.vertices)/1000;m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0,roughnessFactor=.8,doubleSided=True));m.metadata.update(kind='KNOWN_BLACK_OPAQUE_CAD_PRIOR',path=str(ring_path(case(primary))));scene.add_geometry(m,node_name='Ring_KNOWN_CAD');scene.metadata.update(task=R.name,scene=sid,mode=mode,units='meters; exact NPZ in millimeters',camera_condition='UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else case(primary)['condition'],GT_used=False)
    def extras(tree):
        for m in tree['meshes']:
            if m['name']in scene.geometry:m.setdefault('extras',{}).update(clean(scene.geometry[m['name']].metadata))
    path=folder/(sid+'_'+mode+'.glb');scene.export(path,tree_postprocessor=extras);trimesh.points.PointCloud(a['P'],colors=np.rint(a['C']*255).astype(np.uint8)).export(folder/(sid+'_'+mode+'.ply'));return dict(scene=sid,method=mode,points=len(a['P']),path=str(path),npz=str(npz),bytes=path.stat().st_size,sha256=sha(path),public_uploaded=False)
def normal_coverage(a):
    h=np.zeros(24)
    for j,cid in enumerate(a['references']):
        s=source(cid);n,reliable=normal(cid);sel=a['original_ids'][a['reference_index']==j];sel=sel[reliable[sel]];w=vertex_area(s['P'],s['F']);az=np.mod(np.arctan2(n[:,1],n[:,0]),2*np.pi);el=np.arcsin(np.clip(n[:,2],-1,1));bins=np.minimum((az/(2*np.pi)*8).astype(int),7)+8*np.clip(((el+np.pi/2)/np.pi*3).astype(int),0,2);h+=np.bincount(bins[sel],weights=w[sel],minlength=24)
    return dict(normal_area_exposure_hist=h,normal_bins_2pct=int((h>=max(1e-12,.02*h.sum())).sum()),normal_bins_any_support=int((h>0).sum()),area_exposure_proxy_mm2=float(h.sum()))
def main():
    verify();rows=[];summ=[];models=[];contrib=load(R/'metrics/novel_surface_contribution.json')
    for sid in scene_ids():
        method=['Single_Cleaned','Raw_F1','Cleaned_F1','Raw_F2','ViewPartition_Cleaned_F2'];arrays={k:pointset(sid,k)for k in method}
        for mode in ['Raw_F1','Cleaned_F1','ViewPartition_Cleaned_F2']:models.append(exports(sid,mode))
        if sid.startswith('G01'):
            p=GRAZ/f'local_results/scene_exports/{sid}_core.npz';z=np.load(p);arrays['Historical_Primary_Aggregation']=dict(P=z['XYZ_mm'],C=z['RGB'])
            for label in ['B','C']:
                path=OLD/('independent_confidence_fusion_v1/meshes/'+sid[-3:]+'_Polyp_'+('B_raw_multiref.ply'if label=='B'else'C_confidence_fused.ply'));m=trimesh.load(path,process=False);arrays['Historical_'+label]=dict(P=np.asarray(m.vertices),C=m.visual.vertex_colors[:,:3]/255.)
        for t in eval_targets(sid):
            base=projection(arrays['Single_Cleaned']['P'],arrays['Single_Cleaned']['C'],t);folder=R/'local_results/evaluation'/sid/t['id'];folder.mkdir(parents=True,exist_ok=True)
            for label,a in arrays.items():
                p=projection(a['P'],a['C'],t);m=metric(p,t);rows.append(dict(scene=sid,group=sid[:3],method=label,target=t['id'],role=t['role'],**m,common_with_single=common_metric(base,p,t)));np.savez_compressed(folder/(label+'.npz'),**p)
        rr=[x for x in contrib if x['scene']==sid and x['method']=='ViewPartition_Cleaned_F2'];a=arrays['ViewPartition_Cleaned_F2'];directions=normal_coverage(a);single=normal_coverage(arrays['Single_Cleaned']);summ.append(dict(scene=sid,group=sid[:3],condition=case(a['references'][0])['condition'],references=len(a['references']),new_HERO_references=sum(case(cid).get('new_reference',False)for cid in a['references']),initial_owner=a['references'][0],F2_points=len(a['P']),primary_retained_N=rr[0]['accepted_N'],accepted_additional_points=sum(r['accepted_new_N']for r in rr),accepted_additional_area_exposure_proxy_mm2=sum(r['accepted_new_area_proxy_mm2']for r in rr),novel_candidate_points=sum(r['classes']['NOVEL_CANDIDATE']['N']for r in rr[1:]),conflict_exposure_points=sum(r['classes']['GEOMETRIC_CONFLICT']['N']for r in rr[1:]),new_HERO_contributed_points=sum(r['accepted_new_N']for r in rr if r['source_new_HERO']),single_normal_direction=single,aggregate_normal_direction=directions,status='VIEW_PARTITION_AGGREGATION_POSE_CONDITIONAL',true_geometric_accuracy='NOT_EVALUABLE_NO_GT',unknown_surfaces_not_completed=True));print('D EVAL',sid,'F2 points',len(a['P']),'additional',summ[-1]['accepted_additional_points'],flush=True)
    both('scene_evaluation',rows);both('multigroup_summary',summ);both('GLB_INDEX',models);crossvideo(arrays=None)
def crossvideo(arrays=None):
    edge=next(e for e in load(R/'metrics/registration_edges.json')if e['kind']=='CROSS_VIDEO');H=np.linalg.inv(np.array(edge['Ring']['H_source_to_target_world']));q=cfg();checks=[];tests=[]
    for src,dst,T in [('G01_004_ref08','G01_005_raw00459',np.linalg.inv(H)),('G01_005_raw00459','G01_004_ref08',H)]:
        a=source(src);b=source(dst);ids=np.flatnonzero(~selected_mask(src));Bids=np.flatnonzero(~selected_mask(dst));P=transform(a['P'][ids],T);rt=mesh_scene(b['P'],b['F'][~selected_mask(dst)[b['F']].any(1)]);hit=rt.compute_closest_points(o3d().core.Tensor(P.astype(np.float32)));dist=np.linalg.norm(P-hit['points'].numpy(),axis=1);uv,z=vis.project_camera(P,b['p']['K'],b['p']['pose']);xy=np.floor(uv+.5).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ii=np.flatnonzero(inside);u,v=xy[ii].T;valid=b['p']['labels'][v,u]==1;ii=ii[valid];u,v=xy[ii].T;dz=z[ii]-b['p']['depth_mm'][v,u];tau=depth_tau(z[ii],b['p']['K']);w=vertex_area(a['P'],a['F'][~selected_mask(src)[a['F']].any(1)])[ids];den=w[ii].sum();conf=float(w[ii[abs(dz)>tau]].sum()/den)if den else 1.;row=dict(source=src,target=dst,source_N=len(ids),overlap_N=len(ii),point_to_surface_mm=stats(dist),overlap_axial_difference_mm=stats(dz),conflict_area_exposure_fraction=conf,source_area_exposure_mm2=float(w.sum()),overlap_area_exposure_mm2=float(den),distance_is_diagnostic_not_GT=True);checks.append(row);tests.append(conf<=q['cross_gate_maximum_conflict_area_fraction']and np.median(dist)<=q['cross_gate_nearest_median_mm']and np.quantile(dist,.95)<=q['cross_gate_nearest_p95_mm'])
    both('crossvideo_geometry_validation',checks);images=[]
    for sid,dst,T in [('G01_004','G01_005',np.linalg.inv(H)),('G01_005','G01_004',H)]:
        a=pointset(sid,'ViewPartition_Cleaned_F2')
        for t in eval_targets(dst):
            tt=dict(t,c2w=np.linalg.inv(T)@np.array(t['c2w']),ring_case=a['references'][0]);pred=projection(a['P'],a['C'],tt);m=metric(pred,tt);images.append(dict(source=sid,target_scene=dst,role=t['role'],**m));tests.append(m['coverage']>=.55 and m['covered_N']/max(1,m['covered_N']+m['outside_Polyp_N'])>=.75)
    passed=edge['status']=='VERIFIED_ADJACENT_CONSTRAINT'and all(tests);both('crossvideo_image_validation',images);save('metrics/CROSSVIDEO_GATE.json',dict(status='CROSS_VIDEO_SELECTIVE_AGGREGATION_ELIGIBLE'if passed else'CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED',H_005_to_004=H,source_edge=edge['id'],pair_edge_status=edge['status'],geometry_and_bidirectional_checks=tests,fusion_certified=False,pointcloud_joint_only=not passed,independent_absolute_pose_GT=False,GT_used=False));export_cross(H,passed)
def export_cross(H,passed):
    """Joint candidate always exists; no welding or false fused status."""
    scene=trimesh.Scene();P=[];C=[];rr=[];ii=[]
    for j,(sid,T)in enumerate([('G01_004',np.eye(4)),('G01_005',H)]):
        a=pointset(sid,'ViewPartition_Cleaned_F2');Q=transform(a['P'],T);g=trimesh.points.PointCloud(Q/1000,colors=np.rint(a['C']*255).astype(np.uint8));g.metadata.update(kind='SINGLE_VIDEO_BLOCK_IN_CANDIDATE_FRAME',source_video=sid,source_references=a['references'],reference_index=a['reference_index'].tolist(),original_ids=a['original_ids'].tolist(),H_to_004=T.tolist());scene.add_geometry(g,node_name=sid+'_BLOCK_NOT_WELDED');b=background(a['references'][0]);g=trimesh.points.PointCloud(transform(b['P'],T)/1000,colors=np.rint(b['C']*255).astype(np.uint8));g.metadata.update(kind='ACTUAL_BACKGROUND_XYZ_DISPLAY_ONLY',source_reference=a['references'][0],source_ids=b['ids'].tolist());scene.add_geometry(g,node_name=sid+'_Background');P.append(Q);C.append(a['C']);rr.append(np.full(len(Q),j,int));ii.append(a['original_ids'])
    m=source(pointset('G01_004','Single_Cleaned')['references'][0])['ring'].copy();m.vertices=np.asarray(m.vertices)/1000;m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0,roughnessFactor=.8));scene.add_geometry(m,node_name='Ring004_KNOWN_CAD');scene.metadata.update(status='REGISTRATION_CANDIDATE_NOT_FUSED',H_005_to_004=H.tolist(),units='meters',GT_used=False);folder=R/'local_results/glb';path=folder/'G01_004_005_registration_candidate_not_fused.glb'
    def extras(tree):
        for m in tree['meshes']:
            if m['name']in scene.geometry:m.setdefault('extras',{}).update(clean(scene.geometry[m['name']].metadata))
    scene.export(path,tree_postprocessor=extras);np.savez_compressed(folder/'G01_004_005_candidate_sources.npz',XYZ_mm=np.r_[tuple(P)],RGB=np.r_[tuple(C)],source_video=np.r_[tuple(rr)],original_ids=np.r_[tuple(ii)],H_005_to_004=H);rows=load(R/'metrics/GLB_INDEX.json');rows.append(dict(scene='G01_004_005',method='registration_candidate_not_fused',path=str(path),bytes=path.stat().st_size,sha256=sha(path),public_uploaded=False));both('GLB_INDEX',rows)
    if passed:save('metrics/CROSSVIDEO_ELIGIBLE_NOTE.json',dict(status='Independent gate eligible, source-priority cross aggregation still required; no simple union called fusion',not_fused_yet=True))
if __name__=='__main__':main()
