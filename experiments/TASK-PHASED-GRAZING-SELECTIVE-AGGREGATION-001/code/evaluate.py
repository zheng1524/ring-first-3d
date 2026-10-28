"""Independent real-view diagnostics and source-indexed derived scene exports."""
from aggregation import *
from anchors import ring_diagnostic
def scene_points(sc,mode='core'):
    pp=[];cc=[];refs=[];ii=[];uv=[];cl=[]
    for j,cid in enumerate(sc['references']):
        if mode=='primary'and j:continue
        z=np.load(R/f'local_results/scenes/{sc["scene"]}/{cid}.npz');keep=~z['cleaning_removed'];sel=z['accepted']if mode!='evidence'else keep&(z['class_id']!=EXPLAINED)
        if j==0:sel=keep
        ids=np.flatnonzero(sel);pp.append(z['XYZ_mm'][ids]);cc.append(z['RGB'][ids]);refs.append(np.full(len(ids),j,int));ii.append(ids);uv.append(z['source_uv'][ids]);cl.append(z['class_id'][ids])
    return dict(P=np.concatenate(pp),C=np.concatenate(cc),reference_index=np.concatenate(refs),original_point_id=np.concatenate(ii),source_uv=np.concatenate(uv),class_id=np.concatenate(cl),references=sc['references'])
def export_scene(sc,mode):
    a=scene_points(sc,mode);folder=R/'local_results/scene_exports';folder.mkdir(parents=True,exist_ok=True);name=sc['scene']+'_'+mode;np.savez_compressed(folder/(name+'.npz'),XYZ_mm=a['P'],RGB=a['C'],source_reference_index=a['reference_index'],source_original_point_id=a['original_point_id'],source_uv=a['source_uv'],class_id=a['class_id'],reference_names=np.array(a['references']),coordinate=sc['scene']+'_RING_MM',source_kind='actual original P0 points only')
    scene=trimesh.Scene()
    for j,cid in enumerate(a['references']):
        take=a['reference_index']==j
        if not take.any():continue
        g=trimesh.points.PointCloud(a['P'][take]/1000,colors=np.rint(a['C'][take]*255).astype(np.uint8));g.metadata.update(source_reference=cid,original_ids=a['original_point_id'][take].tolist(),source_uv=a['source_uv'][take].tolist(),classes=a['class_id'][take].tolist(),kind='PRIMARY'if j==0 else'OBSERVED_ADDITION_POSE_CONDITIONAL'if mode=='core'else'EVIDENCE_NOT_CERTIFIED');scene.add_geometry(g,node_name=cid+'_'+g.metadata['kind'])
    b=background(sc['primary']);g=trimesh.points.PointCloud(b['P']/1000,colors=np.rint(b['C']*255).astype(np.uint8));g.metadata.update(kind='BACKGROUND_FROM_FROZEN_DEPTH_DISPLAY_ONLY',source_reference=sc['primary'],original_cache_ids=b['ids'].tolist(),source_uv=b['uv'].tolist());scene.add_geometry(g,node_name='Background_DISPLAY_ONLY');m=source(sc['primary'])['ring'].copy();m.vertices=np.asarray(m.vertices)/1000;m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0,roughnessFactor=.8,doubleSided=True));m.metadata.update(kind='KNOWN_BLACK_CAD_PRIOR',source=str(ring_path(case(sc['primary']))));scene.add_geometry(m,node_name='Ring_KNOWN_CAD');condition=case(sc['primary'])['condition'];camera_status='UNQUALIFIED_CAMERA_STRESS'if'UNQUALIFIED'in condition else condition;scene.metadata.update(task=R.name,status=sc['status'],camera_condition=camera_status,units='meters; exact NPZ in millimeters',source_manifest=name+'.npz',GT_used=False,primary_coordinates_unchanged=True)
    def extras(tree):
        for m in tree['meshes']:
            if m['name']in scene.geometry:m.setdefault('extras',{}).update(clean(scene.geometry[m['name']].metadata))
    path=folder/(name+'.glb');scene.export(path,tree_postprocessor=extras)
    return dict(scene=sc['scene'],mode=mode,camera_condition=camera_status,path=str(path),npz=str(folder/(name+'.npz')),bytes=path.stat().st_size,sha256=sha(path),points=len(a['P']),public_uploaded=False)
def cleaning_views():
    rows=[]
    for c in cases():
        cid=c['id'];s=source(cid);versions=['Raw','Density-T2','Angle-10','Angle-15','Angle-20'];folder=R/'local_results/cleaning'/cid
        for t in targets(sceneid(c)):
            raw=projection(s['P'],s['C'],t)
            for version in versions:
                z=np.load(folder/(version+'.npz'));ids=z['kept_original_ids'];pred=projection(s['P'][ids],s['C'][ids],t,ids);m=metric(pred,t);rows.append(dict(reference=cid,group=c['group'],condition=c['condition'],version=version,target=t['id'],view_role=t['role'],**m,common_with_Raw=common_metric(raw,pred,t)))
        # Full point states remain local. Masks retain every deleted original ID.
        trimesh.points.PointCloud(s['P'],colors=np.rint(s['C']*255).astype(np.uint8)).export(folder/'Raw.ply')
        for version in versions[1:]:
            z=np.load(folder/(version+'.npz'));col=s['C'].copy();col[z['deleted']]=[1,.05,.08];trimesh.points.PointCloud(s['P'],colors=np.rint(col*255).astype(np.uint8)).export(folder/(version+'_CandidateMarked.ply'));ids=z['kept_original_ids'];trimesh.points.PointCloud(s['P'][ids],colors=np.rint(s['C'][ids]*255).astype(np.uint8)).export(folder/(version+'_Cleaned.ply'));back=np.full(len(s['P']),-1,int);back[ids]=np.arange(len(ids));trimesh.Trimesh(s['P'][ids],back[s['F'][z['kept_original_face_ids']]],process=False).export(folder/(version+'_original_faces.ply'))
    both('cleaning_cross_view_validation',rows)
def main():
    verify();ss=load(R/'metrics/aggregation_summary.json');rows=[];exports=[]
    for sc in ss:
        for mode in ['primary','core','evidence']:exports.append(export_scene(sc,mode))
        methods={k:scene_points(sc,k)for k in ['primary','core','evidence']}
        if sc['scene'].startswith('G01')and not sc['scene'].endswith('alternate'):
            for name in ['B','C']:
                path=OLD/('independent_confidence_fusion_v1/meshes/'+sc['scene'].split('_')[1]+'_Polyp_'+('B_raw_multiref.ply'if name=='B'else'C_confidence_fused.ply'));m=trimesh.load(path,process=False);methods['historical_'+name]=dict(P=np.asarray(m.vertices),C=m.visual.vertex_colors[:,:3]/255.)
        sid=sc['scene'].replace('_alternate','')
        for t in targets(sid):
            base=projection(methods['primary']['P'],methods['primary']['C'],t)
            for name,a in methods.items():
                pred=projection(a['P'],a['C'],t);row=dict(scene=sc['scene'],group=sid.split('_')[0],method=name,target=t['id'],role=t['role'],**metric(pred,t),common_with_primary=common_metric(base,pred,t));rows.append(row)
                folder=R/'local_results/validation'/sc['scene']/t['id'];folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(name+'.npz'),**pred)
        print('VALIDATE',sc['scene'],'methods',len(methods),'views',len(targets(sid)),flush=True)
    both('cross_view_validation',rows);both('GLB_INDEX',exports)
    # Retain previous small-area result for the identical target and documented
    # historical source-priority rule, not as input to new geometry.
    prior=load(INC/'metrics/B_scenes.json');old=[dict(scene=x['id'],prior_main=x['main_reference'],prior_added_model_patch_mm2=x['new_patch_area_mm2'],old_rule='7 original-face probes / 0.3 mm distance / 30 degree normal / source support; optional original-face subdivision',identity='HISTORICAL_READ_ONLY_NOT_NEW_ANATOMICAL_AREA')for x in prior];both('historical_comparison',old)
    cleaning_views();crossvideo(ss)
def crossvideo(ss):
    h=load(R/'metrics/crossvideo_candidate.json');H=np.array(h['H_005_to_004']);a=next(x for x in ss if x['scene']=='G01_004');b=next(x for x in ss if x['scene']=='G01_005');A=scene_points(a);B=scene_points(b);rows=[];candidate_rr=[]
    # Candidate coordinate analysis proceeds even when registration is not certified.
    for src,dst,T in [(a,b,H),(b,a,np.linalg.inv(H))]:
        main=source(src['primary']);p=source(dst['primary']);t=target_source(dst['primary']);t['c2w']=T@np.asarray(t['c2w']);t['ring_case']=src['primary'];st,dz,_=classify(main['P'],main['F'][~selected_mask(src['primary'])[main['F']].any(1)],p,t,T);weights=vertex_area(p['P'],p['F']);co=dict(source=dst['scene'],primary=src['scene'],status='CANDIDATE_COORDINATES_NOT_FUSED',**{name:dict(N=int((st==k).sum()),area_proxy_mm2=float(weights[st==k].sum()))for k,name in enumerate(LABELS)});candidate_rr.append(co);np.savez_compressed(R/'local_results/scenes'/('cross_'+dst['scene']+'_to_'+src['scene']+'.npz'),class_id=st,depth_difference_mm=dz,source_original_id=np.arange(len(st)),H=T,XYZ_original_mm=p['P'],XYZ_in_candidate_frame_mm=transform(p['P'],T),source_uv=p['uv'],RGB=p['C'])
    for src,dst,T in [(a,b,np.linalg.inv(H)),(b,a,H)]:
        P=scene_points(src)['P'];C=scene_points(src)['C'];old=load(PHASE/'metrics/D1_decision.json');H0=np.array(old['primary_output_H_005_to_004']);T0=np.linalg.inv(H0)if src['scene']=='G01_004'else H0
        for t in targets(dst['scene']):
            # Keep source CAD fixed; transform actual B camera to source frame.
            tc=dict(t,c2w=np.linalg.inv(T)@np.array(t['c2w']),ring_case=src['primary']);pred=projection(P,C,tc);t0=dict(t,c2w=np.linalg.inv(T0)@np.array(t['c2w']),ring_case=src['primary']);base=projection(P,C,t0);row=dict(scene=src['scene'],target_scene=dst['scene'],candidate=h['selected'],target=t['id'],role=t['role'],**metric(pred,t),historical_candidate_metric=metric(base,t0),common_with_historical=common_metric(base,pred,t));rows.append(row);folder=R/'local_results/crossvideo'/src['scene'];folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(t['id']+'.npz'),**pred,c2w=np.asarray(tc['c2w']),H_source_to_target=T)
    both('crossvideo_reverse_projection',candidate_rr);both('crossvideo_validation',rows)
    anchors=load(R/'metrics/crossvideo_rigid_candidates.json');selected=next(x for x in anchors if x['candidate']==h['selected']);reg=selected.get('region_residuals',{});counts=selected.get('region_counts',{});hold_counts={k:reg.get(k,{}).get('heldout',{}).get('N',0)for k in ['Polyp','NearBackground']};stable=len(h['stability'])>=2 and all(r['translation_mm']<=1 and r['rotation_deg']<=2 for r in h['stability']);views=[r for r in rows if r['role']!='SELECTION_VIEW_USED_FOR_FUSION_NOT_INDEPENDENT'];gaps=[]
    for r in views:gaps.append(r['covered_N']/max(1,r['covered_N']+r['outside_Polyp_N']))
    checks=dict(Ring_plausible=h['Ring']['center_mm']<=3 and h['Ring']['normal_deg']<=15,independent_Polyp_and_near_BG_anchors=all(counts.get(k,0)>=8 and hold_counts.get(k,0)>=3 for k in hold_counts),multi_initialization_stable=stable,bidirectional_heldout_Mask_support=len(views)>=2 and all(r['coverage']>=.6 for r in views)and all(x>=.75 for x in gaps))
    passed=all(checks.values());save('metrics/crossvideo_decision.json',dict(h,acceptance_checks=checks,status='CROSS_VIDEO_SELECTIVE_FUSION_ELIGIBLE'if passed else'CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED',D2_executed=False,holdout_views=len(views),holding_failure_does_not_invalidate_single_video=True,physical_metric_accuracy='NOT_EVALUABLE_NO_GT',note='Ring symmetry and predicted-depth bias remain; low ICP/RGB residual alone is insufficient'))
    # Always provide a truthful layered, independently inspectable joint candidate.
    scn=trimesh.Scene()
    for sc,points,T in [(a,A,np.eye(4)),(b,B,H)]:
        P=transform(points['P'],T);g=trimesh.points.PointCloud(P/1000,colors=np.rint(points['C']*255).astype(np.uint8));g.metadata.update(kind='INDEPENDENT_SINGLE_VIDEO_IN_REGISTRATION_CANDIDATE',references=points['references'],source_reference_index=points['reference_index'].tolist(),source_original_id=points['original_point_id'].tolist(),H_to_004=T.tolist());scn.add_geometry(g,node_name=sc['scene']+'_NOT_FUSED');bg=background(sc['primary']);g=trimesh.points.PointCloud(transform(bg['P'],T)/1000,colors=np.rint(bg['C']*255).astype(np.uint8));g.metadata.update(kind='BACKGROUND_FROZEN_DEPTH_DISPLAY_ONLY',source=sc['primary'],H_to_004=T.tolist());scn.add_geometry(g,node_name=sc['scene']+'_Background_DISPLAY_ONLY')
    ring=source(a['primary'])['ring'].copy();ring.vertices=np.asarray(ring.vertices)/1000;ring.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0,roughnessFactor=.8));scn.add_geometry(ring,node_name='Ring004_KNOWN_CAD');scn.metadata.update(status='REGISTRATION_CANDIDATE_NOT_FUSED',H_005_to_004=H.tolist(),units='meters',GT_used=False)
    folder=R/'local_results/scene_exports';path=folder/'G01_004_005_registration_candidate_not_fused.glb';
    def extras(tree):
        for m in tree['meshes']:
            if m['name']in scn.geometry:m.setdefault('extras',{}).update(clean(scn.geometry[m['name']].metadata))
    scn.export(path,tree_postprocessor=extras);exports=load(R/'metrics/GLB_INDEX.json');exports.append(dict(scene='G01_004_005',mode='registration_candidate_not_fused',path=str(path),bytes=path.stat().st_size,sha256=sha(path),public_uploaded=False));both('GLB_INDEX',exports)
    print('CROSSVIDEO',h['selected'],checks,'not fused',not passed,flush=True)
if __name__=='__main__':main()
