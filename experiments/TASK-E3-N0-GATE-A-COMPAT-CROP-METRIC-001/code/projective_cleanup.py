"""One user-authorized projective review of the55 human-reviewed candidates.
No raw mutation, new camera, arbitrary surface deletion or inferred completion.
"""
from crop import *
def preregister():
    path=R/'config/PROJECTIVE_CLEANUP_PREREGISTERED.json';assert not path.exists(),'ONE_ROUND_ONLY'
    quals=list(csv.DictReader((REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv').open()));p95=max(float(q['Ring_p95_px'])for q in quals if q['camera']in CORE);margin=int(np.ceil(p95))+2
    p=dict(user_authorization='User: these reviewed points look at the Polyp edge in2D but extremely far from the body in3D and are not credible; authorizes one multi-angle projection cleanup before ROI selection.',authorization_scope='55 reviewed original native candidates only; no model inference or general G2/G3',candidate_ids=asset(R/'HUMAN_REVIEW_POINTS.csv'),observer_order=CORE+['G01_004_growth_r04'],silhouette_margin_archived_px=margin,margin_basis='ceil(max CORE historical Ring p95)+2px =8px; fixed before projective cleanup results',minimum_distinct_opposing_view_blocks=2,support_veto_mm=.25,CAD_epsilon_mm=.002,
        exclusion_rule='Human-reviewed candidate; at least2 distinct inherited view blocks project inside image onto BG at >8 archived-pixel distance outside Polyp; no CAD occlusion; zero unoccluded near-depth Polyp support. Only derived valid-depth mask becomes0.',
        other_states='Ring/CAD-hidden/outside-image/depth-layer conflict/unknown are not contradictions; silhouette evidence conditional on inherited cameras and possible real BG occlusion, never physical truth.',protected='All other original pixels unchanged, including single-source unique surfaces; exactly one pass; no parameter search',output='new derived depth/validity arrays; original RGB/Mask/native depth/cameras unchanged',RAW_or_GT_oracle_used_to_generate_depth=False,neural_forward=0,GPU=0)
    save(path,p);return p

def main():
    p=preregister();candidates=list(csv.DictReader((R/'HUMAN_REVIEW_POINTS.csv').open()));blocks={r['source_id']:r['view_block']for r in csv.DictReader((D0/'VIEW_COVERAGE_SELECTION.csv').open())};evidence=[];decisions=[];excluded={cid:[]for cid in IDS}
    for row in candidates:
        cid=row['source'];s=native(cid);u,v=int(row['native_u']),int(row['native_v']);X=unproject(np.array([s['depth'][v,u]],float),s['T'],np.array([[u,v]]),s['Kn']);opposed=set();support=[];reasons=[]
        for observer in p['observer_order']:
            if observer==cid:continue
            t=native(observer);uv,z=vis.project_camera(X,t['K'],t['T']);q,z=float(uv[0,0]),float(z[0]);r=float(uv[0,1]);inside=np.isfinite([q,r,z]).all()and z>0 and -.5<=q<639.5 and -.5<=r<359.5;lab=-1;dist=np.nan;cad=np.inf;hdepth=np.nan;contradiction=False;near=False
            if inside:
                pixel=np.floor([q+.5,r+.5]).astype(int);lab=int(t['labels'][pixel[1],pixel[0]]);dm=cv2.distanceTransform((t['labels']!=1).astype(np.uint8),cv2.DIST_L2,5);dist=float(dm[pixel[1],pixel[0]]);cad=float(cast(ringscene(),uv,t['K'],t['T'])[0][0]);hidden=np.isfinite(cad)and z>cad+p['CAD_epsilon_mm'];pack=np.load(t['c']['pack']);hdepth=float(pack['depth_mm'][pixel[1],pixel[0]])
                if hidden:status='CAD_OCCLUDED_NOT_OPPOSITION'
                elif lab==0 and dist>p['silhouette_margin_archived_px']:status='CONDITIONAL_LARGE_SILHOUETTE_CONTRADICTION';contradiction=True;opposed.add(blocks[observer])
                elif lab==1 and np.isfinite(hdepth)and hdepth>0 and abs(z-hdepth)<=p['support_veto_mm']:status='NEAR_DEPTH_POLYP_SUPPORT';near=True;support.append(observer)
                elif lab==2:status='RING_MASK_UNRESOLVED_NOT_OPPOSITION'
                elif lab==1:status='POLYP_DEPTH_LAYER_UNRESOLVED_NOT_OPPOSITION'
                else:status='BOUNDARY_OR_UNKNOWN_NOT_OPPOSITION'
            else:status='OUTSIDE_CAMERA_FIELD_NOT_OPPOSITION'
            ev=dict(review_id=row['review_id'],source=cid,native_id=int(row['native_pixel_id']),observer=observer,observer_block=blocks[observer],target_archive_u=q,target_archive_v=r,target_axial_z_mm=z,target_Mask_label=lab,distance_outside_Polyp_px=dist,CAD_first_hit_mm=cad,observer_HERO_depth_mm=hdepth,evidence=status,large_mask_contradiction=contradiction,near_depth_support=near,camera_qualification='INHERITED_CONDITIONAL_NOT_CERTIFIED',physical_truth=False);evidence.append(ev);reasons.append(status)
        remove=len(opposed)>=p['minimum_distinct_opposing_view_blocks']and not support
        if remove:excluded[cid].append(int(row['native_pixel_id']))
        decisions.append(dict(**row,derived_action='PROJECTIVE_EXCLUDE'if remove else 'RETAIN_UNRESOLVED',opposing_distinct_blocks=sorted(opposed),near_support_sources=support,evidence_statuses=reasons,original_input_modified=False,physical_truth_certified=False))
    out=R/'local_results/projective_cleanup_v1';out.mkdir(exist_ok=True);summary=[]
    for cid in IDS:
        s=native(cid);depth=s['depth'].copy();valid=s['valid'].copy();mask=np.zeros(depth.shape,bool);ids=np.array(excluded[cid],np.int64);mask.flat[ids]=True;depth[mask]=0;valid[mask]=False
        assert np.array_equal(depth[~mask],s['depth'][~mask])and np.all(s['valid'][mask]);np.savez_compressed(out/(cid+'.npz'),depth_mm=depth,valid=valid,projective_excluded=mask,original_native_id=np.arange(depth.size).reshape(depth.shape));summary.append(dict(source=cid,original_legal_N=int(s['valid'].sum()),reviewed_candidate_N=sum(r['source']==cid for r in candidates),derived_excluded_N=int(mask.sum()),derived_legal_N=int(valid.sum()),all_other_pixels_bitwise_unchanged=True,originals_SHA_unchanged=all(sha(a['path'])==a['sha256']for a in next(r for r in MANIFEST['sources']if r['source_id']==cid)['assets'].values()),derived_file=asset(out/(cid+'.npz'))))
    table('PROJECTIVE_CLEANUP_EVIDENCE.csv',evidence);table('PROJECTIVE_CLEANUP_DECISIONS.csv',decisions);save('PROJECTIVE_CLEANUP_SUMMARY.json',dict(protocol=asset(R/'config/PROJECTIVE_CLEANUP_PREREGISTERED.json'),rounds=1,candidate_N=55,excluded_N=sum(len(v)for v in excluded.values()),retained_unresolved_N=55-sum(len(v)for v in excluded.values()),sources=summary,conditional_geometric_proxy_only=True,possible_BG_occlusion_not_independently_certified=True,original_inputs_unchanged=True,source_order_unchanged=True,source_dag_unchanged=True,original_six_source_denominator=sum(s['original_legal_N']for s in summary),new_cameras=0,GPU=0,model_forward=0))
    save('config/HUMAN_JUDGMENT_AND_SCOPE_UPDATE.json',dict(user_judgment='Human judged reviewed red-marked points unreliable due to extreme3D separation despite edge placement in2D; authorizes one multi-angle projective cleanup before ROI selection.',method_extension='derived copies only, candidate55 only, old gates unchanged',r14_judgment='No separate definitive anatomical judgment for r14 single-pixel ridge; retain as unresolved',no_automatic_Gate_B=True))
    print('ONE_PASS_PROJECTIVE_CLEANUP',len(candidates),'candidates',sum(len(v)for v in excluded.values()),'derived exclusions; no original mutation',flush=True)

if __name__=='__main__':main()
