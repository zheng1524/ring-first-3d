"""Isolated shape-only evaluation. Prediction values/statuses are immutable."""
from io_utils import *
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist,squareform
def summary(rows,pred,gt):
    good=[r for r in rows if r.get(pred)is not None and r.get(gt)is not None];e=np.array([r[pred]-r[gt]for r in good]);a=abs(e);rel=np.array([abs(r[pred]-r[gt])/r[gt]*100 for r in good])
    return dict(denominator=len(rows),numeric=len(good),not_evaluable=len(rows)-len(good),MAE_mm=float(a.mean())if len(a)else None,median_abs_error_mm=float(np.median(a))if len(a)else None,median_abs_relative_pct=float(np.median(rel))if len(rel)else None,p95_abs_error_mm=float(np.quantile(a,.95))if len(a)else None,max_abs_error_mm=float(a.max())if len(a)else None,RMSE_mm=float(np.sqrt(np.mean(e**2)))if len(a)else None)
def main():
    verify_predictions();freeze=R/'provenance/GT_PROTOCOL_BEFORE_ERRORS.json'
    if freeze.exists():raise RuntimeError('GT protocol already frozen; no repeat/adaptive evaluation')
    save(str(freeze.relative_to(R)),stamp([R/'PROTOCOL.md',Path(__file__),R/'provenance/PREDICTIONS_FROZEN.json'],geometry_audit_preceded_rule=True,prediction_errors_computed_before_rule=False,GT_used_to_change_predictions=False))
    gt={};assets=[];baserecord=[];groups=load(OLD/'multigroup_surface_gt_vnext/inputs/groups.json');audit=load(R/'evaluation_only/BLENDER_VERIFICATION.json')
    for rec in audit:
        g=rec['group'];z=np.load(R/f'evaluation_only/{g}_verified_gt.npz');P=z['vertices_mm'];F=z['faces'];z0=float(P[:,2].min());bottom=abs(P[:,2]-z0)<.0001;cap=np.all(bottom[F],axis=1);m=trimesh.Trimesh(P,F[cap],process=False);m.remove_unreferenced_vertices();edges=m.edges_unique;counts=np.bincount(m.edges_unique_inverse,minlength=len(edges));boundary=edges[counts==1];euler=len(m.vertices)-len(edges)+len(m.faces);parts=trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)),min_len=1);valid=len(m.vertices)>=3 and m.area>0 and euler==1 and len(parts)==1 and np.all(counts<=2)
        # The normal and base come from actual authoring cap geometry, never prediction.
        h=P[:,2]-z0;hgt=float(np.quantile(h,.95))if valid else None;ids=ConvexHull(P[:,:2]).vertices;D=squareform(pdist(P[ids,:2]));ii,jj=np.unravel_index(D.argmax(),D.shape);dgt=float(D[ii,jj])if valid else None
        gt[g]=dict(H_gt_mm=hgt,Dxy_gt_mm=dgt,GT_height_max_mm=float(h.max()),GT_base_z_mm=z0,GT_base_normal=[0,0,1],base_reliable_authoring=valid,actual_deployment_base_certified=False,GT_H95_weighting='UNWEIGHTED_NATIVE_VERTICES_FULL_SHAPE',GT_Dxy_scope='FULL_SHAPE_PROJECTED_FERET',authoring_vertices=len(P))
        baserecord.append(dict(group=g,**gt[g],cap_vertices=len(m.vertices),cap_faces=int(cap.sum()),cap_area_mm2=float(m.area),cap_components=len(parts),cap_euler=euler,cap_boundary_edges=len(boundary),GT_extents_mm=np.ptp(P,axis=0)))
        for sc in load(R/'prediction_snapshot/B_scenes.json'):
            if sc['group']!=g:continue
            assets.append(dict(group_id=g,prediction_scene=sc['id'],Blender_GT_file=rec['source'],Blender_SHA256=rec['sha256'],pairing_basis='HISTORICAL_USER_CONFIRMED_EXACT_PHYSICAL_GROUP_MAPPING; inputs/groups.json + GT_ASSET_AUDIT.json; source SHA reverified',model_units='METRIC / world_to_mm='+str(rec['world_to_mm']),true_scale_known=True,Ring_GT_geometry=False,base_definition_reliable=valid,base_identity='AUTHORING_FLAT_BASE_CAP; deployment tissue cut not independently calibrated',height_evaluable='SHAPE_SCALAR_CONDITIONAL'if valid else'NOT_EVALUABLE',Dxy_evaluable='MATH_CANDIDATE_ONLY'if valid else'NOT_EVALUABLE',surface_evaluable='NOT_EVALUABLE',not_evaluable_reason='NO_INDEPENDENT_REAL_TO_GT_TRANSFORM; full-shape/visible-support and vertex sampling differ',GT_mode='SHAPE_GT_EVALUATION_ONLY'))
    both('gt_asset_manifest',assets);both('gt_base_geometry',baserecord)
    heights=[]
    for r in load(R/'prediction_snapshot/C_height_geometry.json'):
        gg=gt[r['group']];hp=r['H95_mm'];hg=gg['H_gt_mm'];cand=r['diagnostic_H95_candidate_mm'];err=None if hp is None or hg is None else hp-hg
        heights.append(dict(group_id=r['group'],scene=r['scene'],source_id=r['reference'],roi_id='5-'+str(r['ROI_pixels'][1]),H_pred_mm=hp,H_gt_mm=hg,error_mm=err,abs_error_mm=None if err is None else abs(err),relative_error_pct=None if err is None else err/hg*100,diagnostic_H_candidate_mm=cand,diagnostic_candidate_error_mm=None if cand is None or hg is None else cand-hg,evaluation_status='SHAPE_SCALAR_CONDITIONAL'if err is not None else'NOT_EVALUABLE',original_status=r['base_status'],failure_reason=''if err is not None else r['base_status'],camera_condition=r['camera_condition'],comparison_scope='VISIBLE_P0_VERTEX_P95 vs FULL_GT_VERTEX_P95; sampling/support differ; no real pose GT',GT_height_max_mm=gg['GT_height_max_mm']))
    both('gt_height_evaluation',heights)
    diam=[]
    for r in load(R/'prediction_snapshot/D_observed_surface_definition_audit.json'):
        gg=gt[r['group']];d=r['diagnostic_candidate_Dproj_mm'];dg=gg['Dxy_gt_mm'];e=None if d is None or dg is None else d-dg
        diam.append(dict(group_id=r['group'],scene=r['scene'],source_id=r['base_reference'],roi_id='5-'+str(r['ROI_pixels'][1]),model=r['model'],Dxy_candidate_mm=d,Dxy_gt_mm=dg,error_mm=e,abs_error_mm=None if e is None else abs(e),relative_error_pct=None if e is None else e/dg*100,endpoint_observation_support=r['endpoint_observation_support'],original_formal_measurement_status=r['strict_initial_status'],observed_definition_audit_status=r['observed_surface_status'],formal_Dxy_mm=r['strict_initial_Dproj_mm'],GT_evaluation_status='MATHEMATICAL_CANDIDATE_DIAGNOSTIC_ONLY'if e is not None else'NOT_EVALUABLE',not_evaluable_reason=r['not_evaluable_reasons']+r['observed_surface_failure_reasons'],supported_model_area_fraction=r['supported_model_area_fraction'],projection_fill_fraction=None if r['projection_support']is None else r['projection_support']['fill_fraction'],comparison_scope='VISIBLE_SUPPORTED_MODEL_FERET vs FULL_GT_FERET; authoring base vs estimated base; no pose fit'))
    both('gt_dxy_evaluation',diam)
    mains={x['id']:x['main_reference']for x in load(R/'prediction_snapshot/B_scenes.json')};fixed=[]
    for g in ['G01','G06','G07','G08']:
        scene=next(s for s in mains if s.startswith(g));h=next(r for r in heights if r['scene']==scene and r['source_id']==mains[scene]and r['roi_id']=='5-30');d=next(r for r in diam if r['scene']==scene and r['source_id']==mains[scene]and r['roi_id']=='5-30'and r['model']=='core');fixed.append(dict(group=g,scene=scene,H_pred_mm=h['H_pred_mm'],H_gt_mm=h['H_gt_mm'],Dxy_candidate_mm=d['Dxy_candidate_mm'],Dxy_gt_mm=d['Dxy_gt_mm'],formal_Dxy_mm=d['formal_Dxy_mm'],height_failure=h['failure_reason'],Dxy_failure=d['not_evaluable_reason']))
    both('gt_group_prespecified',fixed)
    pergroup=[]
    for g in gt:
        hr=[x for x in heights if x['group_id']==g];dr=[x for x in diam if x['group_id']==g];pergroup.append(dict(group=g,height_conditions=len(hr),height_numeric=sum(x['H_pred_mm']is not None for x in hr),height_pred_range=[min(x['H_pred_mm']for x in hr if x['H_pred_mm']is not None),max(x['H_pred_mm']for x in hr if x['H_pred_mm']is not None)]if any(x['H_pred_mm']is not None for x in hr)else None,Dxy_conditions=len(dr),Dxy_candidates=sum(x['Dxy_candidate_mm']is not None for x in dr),Dxy_formal_success=sum(x['formal_Dxy_mm']is not None for x in dr)))
    save('metrics/gt_summary.json',dict(GT=gt,per_group=pergroup,prespecified_group_height=summary(fixed,'H_pred_mm','H_gt_mm'),prespecified_group_Dxy_math=summary(fixed,'Dxy_candidate_mm','Dxy_gt_mm'),prespecified_group_Dxy_formal=summary(fixed,'formal_Dxy_mm','Dxy_gt_mm'),all_conditions_height_descriptive_only=summary(heights,'H_pred_mm','H_gt_mm'),all_conditions_Dxy_math_descriptive_only=summary(diam,'Dxy_candidate_mm','Dxy_gt_mm'),independent_target_groups=4,paired_height_Dxy_groups=[x['group']for x in fixed if x['H_pred_mm']is not None and x['Dxy_candidate_mm']is not None],historical_fallback=0,GT_pose_fit=False))
    print('GT_EVALUATION_COMPLETE',len(heights),len(diam),json.dumps(clean(gt)))
if __name__=='__main__':main()
