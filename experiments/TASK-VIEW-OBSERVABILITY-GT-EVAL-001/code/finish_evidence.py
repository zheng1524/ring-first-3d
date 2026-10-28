"""Supplemental evidence only; no re-estimation, no candidate selection."""
from io_utils import *
plt=vis.configure()
def main():
    records=load(R/'metrics/raw_photo_audit.json');review=dict(review='EXECUTOR_VISUAL_READ_OF_TRUE_13_PHOTO_CONTACT_SHEET; not user annotation, not GT',image=str(R/'figures/groups/all_photos_input_audit.png'),image_SHA256=sha(R/'figures/groups/all_photos_input_audit.png'),sources=[x['source_id']for x in records],conclusion='Ring, Polyp and surrounding tissue visually present in each; geometry/pose/scale association not inferred');save('provenance/INPUT_VISUAL_REVIEW.json',review)
    rows=load(R/'metrics/source_view_inventory.json')
    for r in rows:
        if r['source_type']=='photo':r.update(Ring_visible=True,Polyp_visible=True,background_visible=True,visibility_evidence='EXECUTOR_IMAGE_REVIEW_NOT_GT / provenance/INPUT_VISUAL_REVIEW.json')
    both('source_view_inventory',rows)
    fig,ax=plt.subplots(2,4,figsize=(19,10));stats=load(R/'metrics/gt_base_geometry.json')
    for j,r in enumerate(stats):
        g=r['group'];z=np.load(R/f'evaluation_only/{g}_verified_gt.npz');P=z['vertices_mm'];col=np.tile([.3,.65,.8],(len(P),1));base=abs(P[:,2]-r['GT_base_z_mm'])<.0001;col[base]=[.05,.65,.2]
        for i,dim in enumerate([(0,2),(0,1)]):vis.draw_rgb_points(ax[i,j],P[:,dim],col,P[:,1]if i==0 else P[:,2],size=.5);ax[i,j].set_aspect('equal');ax[i,j].set(xlabel='作者X / mm',ylabel='作者Z / mm'if i==0 else'作者Y / mm',title=g+'｜'+('真实底盖侧视'if i==0 else'底盖俯视')+f'\n{r["cap_faces"]}原面 / {r["cap_area_mm2"]:.3f} mm²');ax[i,j].grid(alpha=.15)
    fig.suptitle('EVALUATION ONLY｜Blender真实顶点、平坦底盖绿；作者坐标，无预测对齐/无Ring假基底');fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(R/'figures/groups/GT_actual_base_caps.png',dpi=140);plt.close(fig)
    # Full original GT files remain local; publish small object/unit metadata only.
    both('gt_object_verification',load(R/'evaluation_only/BLENDER_VERIFICATION.json'))
    save('provenance/ENGINEERING_NOTES.json',dict(GT_stdout_serialization_failure='Initial GT job saved all valid tables then failed only while printing numpy.bool_. Corrected print serialization; numerical job was not repeated; original pre-error source hash retained.',gt_rule_source_change='json.dumps(gt) -> json.dumps(clean(gt)) at final console output only',figure_layout_correction='Moved missing-candidate annotation into axes; no numeric changes',photo_supplement='Six inherited LightGlue/f490 poses frozen after initial16 video plots and BEFORE any photo prediction errors. No new pose estimation; all scope/photo combinations included.',full_reconstruction_rerun=False))
    historical=OLD/'multigroup_surface_gt_vnext/inputs/USER_REQUEST.txt';quote='同名Blender GT被人工确认为对应测量组完全可信、可用的三维几何GT。直接接受这一前提，不再要求额外实物扫描或重新证明制造准确性。';assert quote in historical.read_text();proof=load(R/'provenance/GT_PAIRING_EVIDENCE.json');proof.update(explicit_historical_human_identity_confirmation=dict(path=str(historical),sha256=sha(historical),quote=quote,role='Historical identity evidence only; not new task instructions; current GT-only evaluation restrictions prevail'));save('provenance/GT_PAIRING_EVIDENCE.json',proof)
    # Separate GT's definable scalar from availability of a valid frozen prediction.
    height=load(R/'metrics/gt_height_evaluation.json');diam=load(R/'metrics/gt_dxy_evaluation.json');manifest=load(R/'metrics/gt_asset_manifest.json')
    for r in manifest:
        hh=[x for x in height if x['scene']==r['prediction_scene']];dd=[x for x in diam if x['scene']==r['prediction_scene']];r.update(GT_height_definition_available=True,GT_Dxy_definition_available=True,prediction_height_conditions=len(hh),prediction_height_valid_conditions=sum(x['H_pred_mm']is not None for x in hh),prediction_Dxy_conditions=len(dd),prediction_Dxy_math_candidates=sum(x['Dxy_candidate_mm']is not None for x in dd),prediction_Dxy_formal_success=0)
        if not r['prediction_height_valid_conditions']:r['height_evaluable']='NOT_EVALUABLE_PREDICTION_BASE_OR_CAMERA'
        if not r['prediction_Dxy_math_candidates']:r['Dxy_evaluable']='NOT_EVALUABLE_NO_SUPPORTED_MODEL_CANDIDATE'
    both('gt_asset_manifest',manifest)
    # Expose existing match evidence without confusing epipolar fit with verified pose.
    lookup={x['id']:x['source']for x in load(V13/'inputs/views.json')};edgecache=list(csv.DictReader((V13/'pairwise_edges.csv').open()));evidence=[]
    for x in edgecache:
        if x['region']!='ALL':continue
        evidence.append(dict(A_frame=x['a'],B_frame=x['b'],A_source=lookup.get(x['a']),B_source=lookup.get(x['b']),method=x['method'],F_inliers=int(x['F_inliers']or 0),held=int(x['held']or 0),held_F_epipolar_px=json.loads(x['held_F_px']),identity='CACHED_IMAGE_MATCH / F_FIT; NOT VERIFIED 3D REGISTRATION',source_file=str(V13/'pairwise_edges.csv')))
    both('cached_correspondence_evidence',evidence)
    edge=load(R/'metrics/source_graph_edges.json');pairs=load(R/'metrics/view_pairwise_metrics.json');candidates=load(R/'metrics/photo_pose_candidates.json')
    for e in edge:
        e['pose_reprojection_px_status']='NOT_EVALUABLE_NO_REGISTERED_COMMON_POSE';e['matched_evidence_table']='cached_correspondence_evidence.csv'if e['group']=='G01'else None
        if e['group']=='G01'and ('photo'in e['A_source'])!=('photo'in e['B_source']):
            photo=next(x for x in [e['A_source'],e['B_source']]if'photo'in x);video=next(x for x in [e['A_source'],e['B_source']]if'video'in x);r=next(x for x in candidates if x['source'].replace('photo_','photo')==photo and x['scope']==video[-3:]);e['historical_photo_candidate_independent_checks']=r['independent_checks'];e['historical_photo_candidate_method']='V13 LightGlue f490; FAILED, not a newly registered pose'
    both('source_graph_edges',edge)
    for e in pairs:
        if e['A_source']!=e['B_source']:
            updated=next(x for x in edge if x['A_source']==e['A_source']and x['B_source']==e['B_source']);e.update(updated)
    both('view_pairwise_metrics',pairs)
    inv=load(R/'metrics/source_view_inventory.json')
    for r in inv:
        r['formal_camera_pose_exists']=r['camera_pose_exists'];r['historical_candidate_pose_exists']=bool(r['group_id']=='G01'and r['source_type']=='photo');r['historical_candidate_pose_source']=str(V13/'metrics/sparse_registration.json')if r['historical_candidate_pose_exists']else None
    both('source_view_inventory',inv)
if __name__=='__main__':main()
