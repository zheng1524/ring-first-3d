from common import *
def main():
    assert not(R/'config/PROTOCOL.json').exists(),'ONE_PREREGISTRATION'
    phase=load(REPO/'experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/provenance/P2_PAIRS_FROZEN.json')
    old=load(REPO/'experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/provenance/A_TO_B_PAIRS_BEFORE_RENDER.json')['pairs']
    specs=[]
    for a in ['G01_004_ref08','G01_004_ref03','G06_004_ref04','G08_005_ref04']:
        if a.startswith('G08'):p=next(x for x in old if x['A']==a and x['executable']);bid=next(c['id']for c in CC.values()if c['scene_id']==CC[a]['scene_id']and c['reference']==p['B']);historical=p
        else:
            p=next(x for x in phase if x['A']==a);bid=next(c['id']for c in CC.values()if c['scene_id']==CC[a]['scene_id']and c['reference_index']==p['B_index']);historical=p
        assert source(bid)['c']['RGB']==(p['B_target']['RGB']if a.startswith('G08')else p['B_RGB'])
        specs.append(dict(A=a,B=bid,historical_pair=historical,primary=a=='G01_004_ref08'))
    orders=load(N0/'config/EXPERIMENT_FROZEN.json')['orders']
    # Start with the SAME historical A->B; then existing N0 CORE order, remaining frozen N0 order.
    orders['G01_004']=['G01_004_ref08','G01_004_growth_r14']+[x for x in orders['G01_004']if x not in ['G01_004_ref08','G01_004_growth_r14']]
    pr=dict(task=R.name,created=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent='50239b5f2ef94e1a182a4d5b7c04ac512e681d11',
      pairs=specs,B_orders=orders,B_counts={'G01_004':[2,4,8],'G06_004':[2,4,5]},
      selection='Historical Phase-C exact pairs, G08 frozen view-eval pair; N0 fixed view order, no current result selection',
      SIFT=dict(features=8000,contrast=.01,ratio=.72,mutual=True,seed=0,essential_threshold_px=2.,confidence=.999,iterations=2000,minimum_fit=12,minimum_cheirality=8,spatial_holdout='(floor(p.x/16)+3floor(q.y/16))%5==0'),
      A=dict(kinds=['Raw','Cleaned'],renderer='exact AST historical reprojection.py render; original A triangles/RGB; 640x360; CAD .05mm',scale='Only SIFT translation norm borrowed from RF, not direction/rotation; A pose fixed; CAD stays original A-world',metrics='fixed B Polyp mask denominator; RGB on RF & SIFT shared valid Polyp pixels, all common count reported',failure='No RF fallback for SIFT failure'),
      B=dict(pose='T_i=T_i0 exp_SE3([delta_t_mm,delta_omega_rad]); RIGHT body frame; A fixed; Ring world and scale fixed',depth='native axial Z_i+b_i; source native integer pixel IDs frozen',
        parameter_scale=dict(translation_mm=.1,rotation_deg=.1,depth_mm=.1),residual_scale=dict(epipolar_px=2.,reprojection_px=2.,silhouette_px=3.,depth_mm=.25,ring_px=3.),
        modality_balance='Each modality divided by sqrt(number of its scalar residuals); raw unit/noise scaled Jacobians also reported',
        C1=['epipolar','reprojection','silhouette'],C2=['epipolar','reprojection','silhouette','depth'],C3=['epipolar','reprojection','silhouette','depth','ring'],
        max_reprojection_matches_per_ordered_pair=64,max_depth_per_ordered_pair=128,max_silhouette_per_ordered_pair=32,max_ring_per_camera=128,
        depth_visibility='cleaned source + target, original mask interior>2px, finite positive; CAD first hit within .05mm; target observed depth not more than .25mm in front of candidate. Reliable-freespace proxy front conflicts kept; hidden/unknown excluded',
        silhouette='source boundary>2px from Ring, target within8px boundary; signed mask distance proxy, not material correspondence; no claim of full physical silhouette observability',
        differential_steps_normalized=[.01,.005,.0025],difference_relative_tolerance=.05,rank_relative_thresholds=[1e-2,1e-3,1e-4,1e-6],rank_primary=1e-3,structural_relative_threshold=1e-8,
        sensitivity_translation_mm=[-.2,-.1,-.05,0,.05,.1,.2],sensitivity_rotation_deg=[-.25,-.1,-.05,0,.05,.1,.25],sensitivity_depth_mm=[-.2,-.1,-.05,0,.05,.1,.2],
        grid='one 5x5 target body-tz vs target-depth bias in [-.2,-.1,0,.1,.2]mm; diagnostic not selection',
        minimum_correspondences_for_physical_claim=12,structural_claim='Only stable null after gauge fixing and finite-difference checks; unstable/insufficient evidence = NOT_EVALUABLE',
        ring='actual CAD compatible analytic torus contours; camera canonicalized by world yaw to respect exact Ring rotational symmetry; fixed observed Ring contour, baseline curve normal correspondences; no correspondence/material ID assumption',
        unknown='masked/occluded correspondence cannot certify accuracy; input correlations and same-HERO reuse limit information interpretation'),
      no_GT=True,optimizer_steps=0,new_HERO=0,GPU=0,new_fusion=0,cleanup_algorithm_changed=False)
    save('config/PROTOCOL.json',pr)
    ids=set(sum(orders.values(),[]))|{v for p in specs for v in [p['A'],p['B']]};manifest=[];identity=[]
    for cid in sorted(ids):
        c=CC[cid];s=source(cid);n=native(cid);o=original(cid)
        for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:
            row=asset(c[k]);assert row['sha256']==c['files'][k]['sha256'];manifest.append(row)
        for p in [c['E1_actual_native']['path'],c['Ring_CAD']['path']]:manifest.append(asset(p))
        if cid in sum(orders.values(),[])or cid in [x['A']for x in specs]:
            q=cleaned(cid);manifest.append(asset(q['cleanup_path']))
        uv,z=vis.project_camera(o['P'],s['K'],s['T']);err=np.max(abs(uv-o['uv']));assert err<1e-6
        identity.append(dict(source=cid,reference=c['reference'],native_shape=n['depth'].shape,RGB_shape=s['RGB'].shape,archive_original_points=len(o['P']),reprojection_closure_px=err,qualification=GATE[cid]['qualification'],block=GATE[cid]['block'],admission=GATE[cid]['admission']))
    legacy=[REPO/'visualization/real_p0_renderer.py',REPO/'experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py',N0/'code/common.py',CG/'code/tests12.py',PART/'code/matching.py',OLD.parent/'scripts/geometry.py',OLD/'ring_first_v12_pose_matching_audit/TECHNICAL_REPORT.md']
    for name in ['KEY_TECHNICAL_VERSION_v1.0.md','KEY_TECHNICAL_VERSION_E3_SDF_MULTIPOLYP_CANDIDATE_v0.2.md','KEY_TECHNICAL_VERSION_E3_SDF_RTX4090_CANDIDATE_v0.3.md']:legacy.append(REPO/'docs'/name)
    for task in ['TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001','TASK-E3-B-LOCAL-HERO-FIELDS-001','TASK-E3-C-VISIBILITY-CONSENSUS-001','TASK-E3-D0-OPEN3D-TSDF-BASELINE-001']:legacy.append(REPO/'experiments'/task/'TECHNICAL_REPORT.md')
    save('provenance/INPUT_MANIFEST.json',manifest);save('provenance/HISTORICAL_CODE_AND_VERSION.json',[asset(p)for p in legacy]);table('metrics/SOURCE_IDENTITY.csv',identity)
    save('provenance/BEFORE_A.json',dict(UTC=pr['created'],protocol=asset(R/'config/PROTOCOL.json'),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],input_manifest=asset(R/'provenance/INPUT_MANIFEST.json'),results_read=False))
    print('FROZEN',len(specs),'pairs',len(ids),'sources',flush=True)
if __name__=='__main__':main()
