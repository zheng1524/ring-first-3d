"""Post-output audits only: no geometry, classification or parameter changes."""
from evaluate import *
def cached_anchors():
    path=OLD/'ring_first_v13_multisource/observations/LightGlue_004_08__v005_00459.npz';vp=OLD/'ring_first_v13_multisource/inputs/views.json';save('provenance/CACHED_ANCHOR_DIAGNOSTIC_INPUTS.json',stamp([path,vp,Path(__file__)],role='FIXED_H_DIAGNOSTIC_ONLY; no fit or output change'))
    a=np.load(path);s=source('G01_004_ref08');d=source('G01_005_raw00459');views={x['id']:x for x in load(vp)}
    for key,x in [('004_08',s),('v005_00459',d)]:assert views[key]['RGB_SHA256']==sha(x['c']['RGB'])and views[key]['Mask_SHA256']==sha(x['c']['Mask'])
    bg=np.load(INC/'local_results/background/G01_004_ref08.npz');P=np.r_[s['P'],bg['XYZ_mm']];UV=np.r_[s['uv'],bg['source_uv']];dist,idx=cKDTree(UV).query(a['p']);xy=np.floor(a['p']+.5).astype(int);xy=np.clip(xy,[0,0],[639,359]);depthvalid=np.isfinite(s['p']['depth_mm'][xy[:,1],xy[:,0]]);valid=a['usable']&(dist<=2)&depthvalid&(a['category_a']==a['category_b']);dm=cv2.distanceTransform((s['p']['labels']!=1).astype(np.uint8),cv2.DIST_L2,5);region=np.where(a['category_a']==1,'Polyp',np.where(dm[xy[:,1],xy[:,0]]<=60,'NearBackground','FarBackground'));rows=[]
    decision=load(PHASE/'metrics/D1_decision.json');candidate=[('Historical_FULL_LightGlue',np.array(decision['H_005_to_004'])),('Historical_LightGlue_PnP',np.array(decision['primary_output_H_005_to_004']))]
    for name,H in candidate:
        uv,z=vis.project_camera(transform(P[idx],np.linalg.inv(H)),d['p']['K'],d['p']['pose']);err=np.linalg.norm(uv-a['q'],axis=1)
        for reg in ['Polyp','NearBackground','FarBackground']:
            for role,sel in [('historical_train',~a['held']),('historical_held',a['held'])]:
                ok=valid&(region==reg)&sel&(z>0);rows.append(dict(candidate=name,source='G01_004_ref08',target='G01_005_raw00459',region=reg,role=role,cache_match_N=len(a['p']),cache_usable_N=int(a['usable'].sum()),valid_exact_source_XYZ_matches=int(ok.sum()),reprojection_px=stats(err[ok]),depth_to_transverse_mm_median=float(np.median(err[ok]*z[ok]/490))if ok.any()else None,independent_new_pose_truth=False,exact_P0_nearest_source_pixel=True,new_transform_fitted=False))
    both('cached_anchor_diagnostics',rows)
def novel_audits():
    ss=load(R/'metrics/aggregation_summary.json');rows=[];oldrows=[]
    for sc in ss:
        main=source(sc['primary']);prim=mesh_scene(main['P'],main['F']);o=o3d()
        for cid in sc['references'][1:]:
            s=source(cid);a=np.load(R/f'local_results/scenes/{sc["scene"]}/{cid}.npz');ids=np.flatnonzero(a['accepted']);F=s['F'];keep=a['accepted'][F].all(1);comp=face_components(F[keep]);weights=vertex_area(s['P'],F);closest=prim.compute_closest_points(o.core.Tensor(s['P'][ids].astype(np.float32)))['points'].numpy();dist=np.linalg.norm(s['P'][ids]-closest,axis=1);cf=int(len(np.unique(comp)));n=normals(cid);oldfile=INC/f'local_results/scenes/{sc["scene"].replace("_alternate","")}/{cid}_faces_exact.npz';old=np.load(oldfile);oldstatus=old['face_status'];of=old['faces'];N=int(old['original_vertex_N']);touched={}
            for k,name in [('0','PRIMARY_SUPPORTED'),('1','PRIMARY_UNKNOWN'),('2','CONFLICT'),('3','UNKNOWN'),('4','DUPLICATE'),('5','OLD_ACCEPTED_PATCH')]:
                vv=np.unique(of[oldstatus==int(k)]);vv=vv[vv<N];touched[name]=int(np.isin(ids,vv).sum())
            oldaccepted=np.unique(of[oldstatus==5]);oldaccepted=oldaccepted[oldaccepted<N];rec=dict(scene=sc['scene'],reference=cid,accepted_points=len(ids),primary_nearest_distance_diagnostic_mm=stats(dist),accepted_farther_than_old_03mm=int((dist>.3).sum()),accepted_without_reliable_normal=int((~n['reliable'][ids]).sum()),complete_original_faces_with_all_three_vertices_accepted=int(keep.sum()),complete_original_face_area_proxy_mm2=float(s['areas'][keep].sum()),complete_original_face_components=cf,accepted_points_unreferenced_by_complete_accepted_original_faces=int((~np.isin(ids,np.unique(F[keep]))).sum()),point_area_exposure_proxy_mm2=float(weights[ids].sum()),historical_face_class_incidence_nonexclusive=touched,actual_point_ids_also_in_old_accepted_face=int(np.isin(ids,oldaccepted).sum()),interpretation='source-pixel connected does not guarantee single geometric sheet; area is exposure proxy, classes overlap at original vertices')
            rows.append(rec)
            # Independent-view added support / foreground displacement is diagnostic
            # only. Output selection remains frozen even when the result worsens.
            for t in targets(sc['scene'].replace('_alternate','')):
                if t['role']=='SELECTION_VIEW_USED_FOR_FUSION_NOT_INDEPENDENT':continue
                p=projection(s['P'][ids],s['C'][ids],t,ids);m=metric(p,t);base=np.load(R/f'local_results/validation/{sc["scene"]}/{t["id"]}/primary.npz');obj=cv2.imread(t['Mask'],0)==1;new=(p['layer']==1)&obj&(base['layer']!=1);front=(p['layer']==1)&(base['layer']==1)&(p['z']<base['z'])&obj;oldrows.append(dict(scene=sc['scene'],reference=cid,target=t['id'],role=t['role'],added_source_points=len(ids),covered_new_target_pixels=int(new.sum()),added_foreground_on_previously_covered_target_pixels=int(front.sum()),added_alone=m,not_anatomical_labels=True))
    both('novel_continuity_and_old_rule_audit',rows);both('novel_independent_view_support',oldrows)
    # Same-source additions from two references may still overlap. Quantify it,
    # instead of claiming source-based exposure sum is unique added area.
    rows=[]
    for sc in ss:
        if len(sc['references'])<3:continue
        first,second=sc['references'][1:3];a=np.load(R/f'local_results/scenes/{sc["scene"]}/{first}.npz');b=np.load(R/f'local_results/scenes/{sc["scene"]}/{second}.npz');s=source(first);t=target_source(second);ids=np.flatnonzero(a['accepted']);pred=projection(s['P'][ids],s['C'][ids],t,ids);q=source(second);uv=q['uv'];z=((q['P']-q['p']['pose'][:3,3])@q['p']['pose'][:3,:3])[:,2];at=pred['layer'][uv[:,1],uv[:,0]]==1;dz=abs(pred['z'][uv[:,1],uv[:,0]]-z);overlap=b['accepted']&at&(dz<=depth_tau(z,q['p']['K']));rows.append(dict(scene=sc['scene'],first=first,second=second,second_accepted_points=int(b['accepted'].sum()),possible_duplicate_addition_points=int(overlap.sum()),interpretation='one-direction source-center projection diagnostic; not unique area or verified duplicate anatomy',geometry_changed=False))
    both('addition_overlap_audit',rows)
def final_tables():
    rows=[];normalrows=[]
    for sc in load(R/'metrics/aggregation_summary.json'):
        for cid in sc['references'][1:]:
            z=np.load(R/f'local_results/scenes/{sc["scene"]}/{cid}.npz')
            for i in np.flatnonzero(z['accepted']):rows.append(dict(scene=sc['scene'],source_reference=cid,group=case(cid)['group'],actual_video=case(cid)['video'],source_frame=case(cid)['reference'],original_point_id=int(i),source_u=int(z['source_uv'][i,0]),source_v=int(z['source_uv'][i,1]),region_id=int(z['region_id'][i]),class_id=int(z['class_id'][i]),normal_reliable=bool(z['normal_reliable'][i]),beta_deg=float(z['beta_deg'][i]),exact_geometry_file=str(R/f'local_results/scenes/{sc["scene"]}/{cid}.npz'),scientific_identity='OBSERVED_ADDITION_POSE_CONDITIONAL'))
    both('accepted_source_index',rows)
    for c in cases():
        s=source(c['id']);n=normals(c['id'])
        for name,sel in cohorts(s).items():
            good=sel&n['reliable'];normalrows.append(dict(reference=c['id'],group=c['group'],condition=c['condition'],cohort=name,cohort_N=int(sel.sum()),reliable_N=int(good.sum()),beta_all_raw_normal_deg=stats(n['beta_deg'][sel]),beta_reliable_raw_normal_deg=stats(n['beta_deg'][good]),rho_points_per_mm2=stats(s['a']['rho_surface_radius'][sel]),PCA_difference_deg=stats(abs(n['beta_deg'][good]-n['PCA_beta_diagnostic_deg'][good])),diagnostic_proxy_not_truth=True))
    both('normal_region_distributions',normalrows)
    fail=[dict(group=c['group'],source=c['id'],condition=c['condition'],stage='A',status='ANGLE_REJECTED_USE_RAW_BASELINE',reason='fixed angles do not achieve G01 net structural benefit; Raw preserved; see cleaning_comparison',evidence='figures/diagnostics/'+c['id']+'_Raw_Marked_Cleaned.png')for c in cases()]
    for sid in ['G01_004','G01_005']:fail.append(dict(group='G01',source=sid,stage='B-E',status='CONDITIONAL_NOT_CERTIFIED',reason='PRIMARY_AMBIGUOUS; no new normal direction bins; added points may re-occlude main; source-connected patches have fragments/uncertain normals',evidence='figures/Fig2_single_video_aggregation.png'))
    for gid in ['G06','G07','G08']:fail.append(dict(group=gid,source=gid,stage='B-E',status='NOT_EVALUABLE_MULTIREFERENCE',reason='single frozen P0 only; no extra reference inferred; '+('UNQUALIFIED_CAMERA_STRESS'if gid=='G07'else'LIMITED_STRESS'if gid=='G08'else'NORMAL_CONDITIONAL'),evidence='figures/cases/'+gid+('_005'if gid=='G08'else'_004')+'/Layers_L1-L5.png'))
    fail.append(dict(group='G01',source='004↔005',stage='C-crossvideo',status='REGISTRATION_CANDIDATE_NOT_FUSED',reason='no new primary-pair SIFT matches; cached true Polyp correspondences only2 train/1 held; Ring symmetry; no new H stability; known foreground depth inconsistency remains',evidence='figures/Fig3_crossvideo_comparison.png'));both('failure_ledger',fail)
def main():cached_anchors();novel_audits();final_tables();print('SUPPLEMENTAL audit only complete',flush=True)
if __name__=='__main__':main()
