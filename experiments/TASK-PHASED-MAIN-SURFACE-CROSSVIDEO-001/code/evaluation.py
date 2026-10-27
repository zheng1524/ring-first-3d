"""Source RGB point/ORIGINAL-triangle projection and independent holdout checks."""
from registration import *
def geometry(video,mode='D0_FULL'):
    if mode in ['B','C']:
        f=ICF/('meshes/'+video+'_Polyp_'+('B_raw_multiref.ply'if mode=='B'else'C_confidence_fused.ply'));m=trimesh.load(f,process=False);return m
    if mode=='SINGLE':
        cid=load(R/f'metrics/D0_{video}.json')['main_reference'];s=source(cid);m=mesh(s['P'],s['m'].faces);m.visual.vertex_colors=np.rint(s['rgb']*255).astype(np.uint8);return m
    parts=[];d=load(R/f'metrics/D0_{video}.json')
    for c in [c for c in cases()if c['video']==video]:
        a=np.load(R/f'local_results/D0/{video}/{c["id"]}_source_exact.npz');status=a['face_status'];keep=status!=4 if mode=='D0_FULL'else(status==5)|((c['id']==d['main_reference'])&np.ones(len(status),bool));m=mesh(a['XYZ_mm'],a['faces'][keep]);m.visual.vertex_colors=np.rint(a['RGB']*255).astype(np.uint8);parts.append(m)
    combined=trimesh.util.concatenate(parts);combined.remove_unreferenced_vertices();return combined
def point_data(video,mode='D0_FULL',with_background=True):
    if mode=='SINGLE':
        cid=load(R/f'metrics/D0_{video}.json')['main_reference'];s=source(cid);P=s['P'];rgb=s['rgb']
    elif mode in ['B','C']:
        m=geometry(video,mode);P=np.asarray(m.vertices);rgb=m.visual.vertex_colors[:,:3]/255.
    else:
        a=np.load(R/f'local_results/D0/{video}/scene_points_exact.npz');sel=np.ones(len(a['XYZ_mm']),bool)if mode=='D0_FULL'else a['core'];P=a['XYZ_mm'][sel];rgb=a['RGB'][sel]
    N=len(P);bparts=[];cparts=[]
    if with_background:
        if mode in ['B','C']:
            m=trimesh.load(ICF/('meshes/'+video+'_Background_'+('B_raw_multiref.ply'if mode=='B'else'C_confidence_fused.ply')),process=False);bparts=[np.asarray(m.vertices)];cparts=[m.visual.vertex_colors[:,:3]/255.]
        else:
            refs=[load(R/f'metrics/D0_{video}.json')['main_reference']]if mode=='SINGLE'else[c['id']for c in cases()if c['video']==video]
            for cid in refs:b=background(cid);bparts.append(b['P'][b['display']]);cparts.append(b['rgb'][b['display']])
    if bparts:P=np.r_[P,*bparts];rgb=np.r_[rgb,*cparts]
    kind=np.r_[np.ones(N,int),np.full(len(P)-N,2)];return P,rgb,kind
def triangle_predict(m,t,H):
    sc=scene_for(t);o=sc.o3d;T=transform(m.vertices,H);rt=o.t.geometry.RaycastingScene(nthreads=2);rt.add_triangles(o.core.Tensor(T.astype(np.float32)),o.core.Tensor(np.asarray(m.faces,np.uint32)));uv=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];rays=vis.camera_rays(uv,np.array(t['K']),np.array(t['c2w']));hit=rt.cast_rays(o.core.Tensor(rays.astype(np.float32)));z=hit['t_hit'].numpy();ringz=sc.cast(uv)['t_hit'].numpy();valid=np.isfinite(z)&(z>0)&(z<=ringz+cfg()['CAD_occlusion_tolerance_mm']);fid=hit['primitive_ids'].numpy();bary=hit['primitive_uvs'].numpy();color=np.zeros((640*360,4),np.uint8);F=m.faces[fid[valid]];w=bary[valid];weights=np.c_[1-w.sum(1),w];rgb=m.visual.vertex_colors[:,:3]/255.;C=(rgb[F]*weights[:,:,None]).sum(1);color[valid,:3]=np.rint(np.clip(C,0,1)*255).astype(np.uint8);color[valid,3]=255
    return dict(RGBA=color.reshape(360,640,4),z=z.reshape(360,640),face_id=fid.reshape(360,640),source_barycentric=bary.reshape(360,640,2),kind=valid.reshape(360,640).astype(int),known_CAD_occlusion=True,original_triangles_only=True,B_RGB_used_for_prediction=False)
def image_metrics(pred,t):
    B=np.asarray(Image.open(t['RGB']).convert('RGB'));lab=cv2.imread(t['Mask'],0);valid=pred['kind']==1;obj=lab==1;both=valid&obj;N=int(obj.sum());out=dict(target_mask_N=N,predicted_Polyp_pixels=int(valid.sum()),covered_Polyp_pixels=int(both.sum()),coverage=float(both.sum()/N),outside_mask_predictions=int((valid&~obj).sum()),RGB=errors(pred,B,both),whole_predicted_RGB=errors(pred,B,valid))
    if 'z'in pred:
        edge=valid&~cv2.erode(valid.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);trueedge=obj&~cv2.erode(obj.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);dist=cv2.distanceTransform((~trueedge).astype(np.uint8),cv2.DIST_L2,5);e=dist[edge];depth=pred['z'][edge];finite=np.isfinite(depth)&(depth>0);focal=np.sqrt(np.array(t['K'])[0,0]*np.array(t['K'])[1,1]);out.update(predicted_boundary_N=int(edge.sum()),boundary_to_observation_px=stats(e),boundary_lateral_scale_mm=stats(e[finite]*depth[finite]/focal),boundary_source_depth_mm=stats(depth[finite]),lateral_interpretation='per-predicted-boundary axial depth / effective focal, approximate transverse scale only, axial uncertainty remains')
        if edge.any():v,u=np.nonzero(edge);bv,bu=np.nonzero(trueedge);dd,_=cKDTree(np.c_[u,v]).query(np.c_[bu,bv]);out['observation_boundary_to_prediction_px']=stats(dd)
        else:out['observation_boundary_to_prediction_px']=stats([])
    return out
def predict_scene(video,mode,t,H):
    P,rgb,kind=point_data(video,mode);points=transform(P,H);pred=point_projection(points,rgb,np.arange(len(P)),t,kind);tri=triangle_predict(geometry(video,mode),t,H);return pred,tri
def store_images(dest,pred,tri,t):
    dest.mkdir(parents=True,exist_ok=True);B=np.asarray(Image.open(t['RGB']).convert('RGB'));Image.fromarray(B).save(dest/'B_real.png');Image.fromarray(pred['RGBA']).save(dest/'A_RGB_point_prediction.png');Image.fromarray(tri['RGBA']).save(dest/'A_RGB_original_triangle_prediction.png');mask=tri['kind']>0;overlay=B.astype(float);overlay[mask]=.3*overlay[mask]+.7*tri['RGBA'][:,:,:3][mask];Image.fromarray(np.rint(overlay).astype(np.uint8)).save(dest/'Overlay.png');diff=np.zeros((360,640,4),np.uint8);err=np.abs(tri['RGBA'][:,:,:3].astype(float)-B).mean(2);from matplotlib import colormaps;diff[mask,:3]=np.rint(colormaps['magma'](np.clip(err[mask]/128,0,1))[:,:3]*255).astype(np.uint8);diff[mask,3]=255;Image.fromarray(diff).save(dest/'Difference_all_predicted_valid.png');np.savez_compressed(dest/'point_prediction_exact.npz',**pred);np.savez_compressed(dest/'triangle_prediction_exact.npz',**tri)
def benchmark_D0():
    rows=[]
    for video in ['004','005']:
        for mode in ['SINGLE','B','C','D0_CORE','D0_FULL']:
            m=geometry(video,mode);cl=face_components(m.faces);area=m.area_faces;ca=np.bincount(cl,weights=area);e,cnt=edge_counts(m.faces);top=dict(points=len(m.vertices),faces=len(m.faces),face_area_exposure_sum_mm2=float(area.sum()),components=len(ca),largest_component_fraction=float(ca.max()/ca.sum()),nonmanifold_edges=int((cnt>2).sum()),boundary_edges=int((cnt==1).sum()),true_unique_visible_area_mm2=None)
            for t in target(video,'selection')+target(video,'holdout'):
                p,tri=predict_scene(video,mode,t,np.eye(4));row=dict(video=video,method=mode,target=t['id'],role=t['role'],topology=top,points=image_metrics(p,t),triangles=image_metrics(tri,t),meaning='source-preserving model/Mask/RGB consistency, not absolute accuracy');rows.append(row)
                if mode in ['SINGLE','B','C','D0_FULL']:store_images(R/f'local_results/D0_evaluation/{video}/{mode}/{t["id"]}',p,tri,t)
            print('D0_BENCHMARK',video,mode,top['faces'],flush=True)
    save('metrics/D0_BC_comparison.json',rows);csvsave('metrics/D0_BC_comparison.csv',rows)
def polyp_overlap(H):
    m4=geometry('004','D0_CORE');m5=geometry('005','D0_CORE');p4=np.asarray(m4.vertices);p5=transform(m5.vertices,H);a,n=nearest(p5,m4);m5t=m5.copy();m5t.apply_transform(H);b,_=nearest(p4,m5t);rows=[]
    for video,P,m,T in [('005',p5,m5,np.eye(4)),('004',transform(p4,np.linalg.inv(H)),m4,np.eye(4))]:
        other='004'if video=='005'else'005';cid=load(R/f'metrics/D0_{other}.json')['main_reference'];p=source(cid)['p'];uv,z=vis.project_camera(P,p['K'],p['pose']);xy=np.rint(uv).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(inside);x,y=xy[ids].T;ii=ids[(p['labels'][y,x]==1)&np.isfinite(p['depth_mm'][y,x])];x,y=xy[ii].T;res=z[ii]-p['depth_mm'][y,x];front=np.zeros(len(P),bool);front[ii[res<-.5]]=True;seen=np.zeros(len(P),bool);seen[ii]=True;af=m.area_faces;touch=seen[m.faces].any(1);cf=front[m.faces].any(1);den=float(af[touch].sum());rows.append(dict(source=video,target=other,source_vertices=len(P),same_object_observed_vertices=len(ii),front_conflict_vertices=int(front.sum()),observed_face_exposure_area_mm2=den,front_conflict_face_exposure_mm2=float(af[cf].sum()),front_conflict_fraction=float(af[cf].sum()/den)if den else None,axial_residual_mm=stats(res),occluded_or_deeper_regions='UNKNOWN, not all treated as errors'))
    return dict(forward_nearest_mm=stats(a),reverse_nearest_mm=stats(b),forward_within_03=float((a<=.3).mean()),reverse_within_03=float((b<=.3).mean()),overlap_is_pose_conditional=True,source_conflicts=rows)
def evaluate_D1():
    candidates=load(R/'metrics/D1_candidates.json');decision=load(R/'metrics/D1_decision.json');new=[c for c in candidates if c['is_new']];display=min(new or candidates,key=lambda c:c['training_score']);save('metrics/D1_display_candidate.json',dict(candidate=display['tag'],H_005_to_004=display['H_005_to_004'],reasonable_bounds=display['reasonable_bounds'],status='DISPLAY_DIAGNOSTIC_NOT_FUSED',selection='Lowest training geometry score among new endpoints, even failed endpoint retained for inspection; does not change admissibility or D2 gate',admissible_best_candidate=decision['best_candidate']));rows=[];overlaps=[]
    for c in candidates:
        H=np.array(c['H_005_to_004']);overlap=polyp_overlap(H);overlaps.append(dict(candidate=c['tag'],**overlap))
        for video,other,T in [('005','004',H),('004','005',np.linalg.inv(H))]:
            for t in target(other,'holdout'):
                p,tri=predict_scene(video,'D0_FULL',t,T);row=dict(candidate=c['tag'],source_video=video,target_video=other,target=t['id'],target_raw_frame=t['raw_frame'],method='D0_FULL',points=image_metrics(p,t),triangles=image_metrics(tri,t),is_new=c['is_new'],training_selected=c['tag']==decision['best_candidate'],display_selected=c['tag']==display['tag'],B_not_used_for_fit=True,whole_pipeline_independent=False);rows.append(row)
                if c['tag']in [display['tag'],decision['best_candidate'],'HISTORICAL_FULL_RoMa']:store_images(R/f'local_results/D1_evaluation/{c["tag"]}/{video}_to_{other}/{t["id"]}',p,tri,t)
        print('D1_HELDOUT',c['tag'],'new?',c['is_new'],'forward p50',overlap['forward_nearest_mm']['median'],flush=True)
    save('metrics/D1_heldout.json',rows);csvsave('metrics/D1_heldout.csv',rows);save('metrics/D1_overlap_conflicts.json',overlaps);csvsave('metrics/D1_overlap_conflicts.csv',overlaps)
    # Predeclared acceptance is unchanged; display of failed endpoints is not admission.
    admitted=next(c for c in candidates if c['tag']==decision['best_candidate']);obs=admitted['observability'];reasons=[]
    if not decision['multiple_initializations_stable']:reasons.append('NO_STABLE_BOUNDED_GICP_CONSENSUS')
    if obs.get('Ring_augmented_eigen_ratio',0)<cfg()['observability_eigenvalue_ratio_minimum']:reasons.append('YAW_OR_COUPLED_POSE_WEAKLY_OBSERVABLE')
    if not decision['working_input_qualified']:reasons.append('INSUFFICIENT_RELIABLE_BACKGROUND')
    # Held-out comparisons use historical feasible winner; no 3px absolute rejection.
    hist=[c for c in candidates if not c['is_new']and c['reasonable_bounds']];baseline=min(hist,key=lambda c:c['training_score'])['tag']
    for r in [x for x in rows if x['candidate']==decision['best_candidate']]:
        b=next(x for x in rows if x['candidate']==baseline and x['source_video']==r['source_video']and x['target']==r['target']);rp=r['points'];bp=b['points'];rt=r['triangles'];bt=b['triangles']
        if rp['coverage']<bp['coverage']-cfg()['D2_holdout_coverage_loss_maximum']:reasons.append('HOLDOUT_COVERAGE_WORSENED')
        if rt['boundary_to_observation_px']['median']is not None and bt['boundary_to_observation_px']['median']is not None and rt['boundary_to_observation_px']['median']>bt['boundary_to_observation_px']['median']+cfg()['D2_holdout_boundary_median_worsening_maximum_px']:reasons.append('HOLDOUT_BOUNDARY_WORSENED_RELATIVE_TO_HISTORY')
    ov=next(x for x in overlaps if x['candidate']==decision['best_candidate'])
    if any((x['front_conflict_fraction']or 0)>.15 for x in ov['source_conflicts']):reasons.append('POLYP_FRONT_CONFLICT_AREA_HIGH')
    save('metrics/D2_gate.json',dict(status='NOT_FUSED'if reasons else'ELIGIBLE_ONE_CONSERVATIVE_FUSION',reasons=list(dict.fromkeys(reasons)),background_geometry_eigen_ratio=obs.get('geometry_eigen_ratio'),background_thinness_interpretation='Descriptive warning; thin geometry and model-predicted folds do not certify non-symmetric material structure',pixel_rule='Relative deterioration only, no 3px absolute veto',official_H_certified=False,source_unique_new_area_mm2=None,admissible_best_candidate=decision['best_candidate'],display_candidate=display['tag'],GT_used=False));print('D2 GATE',reasons or'eligible',flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['D0','D1']);x=p.parse_args();benchmark_D0()if x.mode=='D0'else evaluate_D1()
