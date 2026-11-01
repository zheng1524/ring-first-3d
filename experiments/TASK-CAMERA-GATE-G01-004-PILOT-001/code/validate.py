"""Numerical controls, identity/holdout invariants and deliverable checks."""
from common import *
import re
def main():
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=detail))
    original=load(R/'config/ORIGINAL_TEST12.json');plans=load(R/'config/RGB_ONLY_METHOD_SELECTION.json');qs=load(R/'config/FINAL_CAMERA_QUALIFICATION.json');ob=load(R/'config/ORIGINAL_OBSERVABILITY.json');aux=load(R/'config/HERO_AUXILIARY.json');corr=load(R/'config/BOUNDED_CORRECTION_RESULTS.json')
    check('exact_five_camera_scope_nine_pairs',set(CC)==set(IDS) and len(plans)==9 and {r['camera'] for r in qs}==set(IDS))
    check('protocol_identical_to_pre_run_freeze',sha(R/'config/protocol.json')==load(R/'config/BEFORE_FORMAL_RUN.json')['protocol']['sha256'])
    identity=[source(c) for c in IDS];check('K_c2w_Mask_RGB_numeric_identity_and_proper_rotations',all(np.linalg.norm(s['T'][:3,:3].T@s['T'][:3,:3]-np.eye(3))<1e-8 for s in identity))
    mismatch=[]
    for a in load(R/'config/INPUT_HASHES_BEFORE.json'):
        if sha(a['path'])!=a['sha256']:mismatch.append(a['path'])
    check('all_original_input_and_cached_match_hashes_unchanged',not mismatch,mismatch)
    state=protected_state();save('config/PROTECTED_END.json',state)
    check('all_historical_worktree_HEAD_status_dirty_hashes_unchanged',state==load(R/'config/PROTECTED_START.json'),dict(worktree_N=len(state)))
    sa,sb=source(IDS[0]),source(IDS[1]);rng=np.random.default_rng(0);X=rng.uniform([-2,-2,0],[2,2,3],(64,3));p,z=vis.project_camera(X,sa['K'],sa['T']);q,zz=vis.project_camera(X,sb['K'],sb['T']);F=fundamental(sa['K'],sa['T'],sb['K'],sb['T']);err=sampson(F,p,q)
    check('labelled_generated_control_c2w_to_F_direction',float(err.max())<1e-9,dict(synthetic_control_not_project_truth=True,max_px=float(err.max())))
    reverse=sampson(F.T,q,p);wrong=sampson(F.T,p,q)
    check('Sampson_reciprocal_symmetry_and_transpose_negative_control',np.max(abs(err-reverse))<1e-9 and np.median(wrong)>1e-2,dict(wrong_transpose_median_px=float(np.median(wrong))))
    h=cv2.triangulatePoints(sa['K']@np.linalg.inv(sa['T'])[:3],sb['K']@np.linalg.inv(sb['T'])[:3],p.T,q.T);back=(h[:3]/h[3]).T
    check('control_triangulation_reprojects_with_mm_coordinates',np.max(abs(back-X))<1e-7,dict(max_mm=float(np.max(abs(back-X)))))
    rays=vis.camera_rays(p,sa['K'],sa['T']);back=rays[:,:3]+rays[:,3:]*z[:,None]
    check('actual_nonunit_ray_axial_Z_roundtrip',np.max(abs(back-X))<1e-9 and np.max(abs(np.linalg.norm(rays[:,3:],axis=1)-1))>1e-3)
    check('zero_baseline_F_unresolved_not_success',not np.isfinite(fundamental(sa['K'],sa['T'],sa['K'],sa['T'])).all())
    a=torus_contours(sa['T'][:3,3],sa['T'][:3,:3],sa['K'],n=cfg['torus_curve_samples']).reshape(-1,2);rz=Rotation.from_euler('z',17,degrees=True).as_matrix();b=torus_contours(rz@sa['T'][:3,3],rz@sa['T'][:3,:3],sa['K'],n=cfg['torus_curve_samples']).reshape(-1,2);e=cKDTree(a).query(b)[0]
    check('Ring_continuous_yaw_symmetry_control',np.max(e)<.5,dict(sampled_curve_max_px=float(np.max(e)),sampling_control_only=True))
    check('Ring_rank_never_claimed_full_SE3',all(r['full_SE3_certified'] is False for r in original['Ring']) and all(r['ring_only_singular_values'][-1]<1e-10 for r in ob.values()))
    selects=[];partitions=[];original_match_identity=[];new_sift=0;cached_sift=0
    for plan in plans:
        desired=next((m['method'] for m in plan['methods'] if m['sufficient_RGB_only']),None);selects.append(desired==plan['selected_method'])
        inputplan=next(p for p in load(R/'config/MATCH_PLAN_FROZEN.json') if p['pair_id']==plan['pair_id'])
        for m in plan['methods']:
            d=match_data(plan['A'],plan['B'],m['method']);partitions.append(np.array_equal(d['held'],fit_partition(d['p'],d['q'])))
            im=next(x for x in inputplan['methods'] if x['method']==m['method'])
            if m['method']=='SIFT':new_sift+=im['kind']=='NEW_CPU_SIFT';cached_sift+=im['kind']=='EXISTING_RGB_MATCHES'
            if im['asset']:
                raw=np.load(im['asset']['path']);p0,q0=(raw['q'],raw['p']) if im['reverse'] else (raw['p'],raw['q']);original_match_identity.append(np.array_equal(d['p'],p0) and np.array_equal(d['q'],q0))
        for r in original['pairs']:
            if r['A']==plan['A'] and r['B']==plan['B']:selects.append(r['selected_for_gate']==(r['method']==desired))
    check('RGB_only_priority_selection_never_hops_to_pose_PASS',all(selects))
    check('all_correspondences_use_exact_frozen_spatial_holdout',all(partitions))
    check('cached_real_match_coordinates_retained_exactly',all(original_match_identity),dict(existing_match_caches=len(original_match_identity)))
    check('only_five_CPU_SIFT_pairs_supplemented_four_reused',new_sift==5 and cached_sift==4)
    qualifications_ok=[]
    for r in qs:
        required=set(BASE)-{r['camera']};sufficient={g['other'] for g in r['image_geometry']}
        if required-sufficient:qualifications_ok.append(r['new_status']=='INSUFFICIENT_EVIDENCE' and set(r['missing_sufficient_required_relations'])==required-sufficient)
    check('required_ref13_cannot_be_replaced_by_two_fit_relations',all(qualifications_ok) and bool(qualifications_ok))
    check('no_HERO_metric_used_for_qualification',all(not r['HERO_used_for_qualification'] for r in qs) and not original['HERO_used'])
    check('no_optimization_without_FIT_error_trigger',sum(c['optimizer_calls'] for c in corr)==0 and all(c['status']=='NOT_ATTEMPTED' for c in corr),dict(optimizer_calls=0))
    check('all_twenty_HERO_directions_keep_fixed_target_denominators',len(aux)==20 and all(r['target_Polyp_denominator']==int((source(r['target'])['labels']==1).sum()) and not r['source_XYZ_deformed'] for r in aux))
    check('original_Test12_hash_frozen_before_HERO',sha(R/'config/ORIGINAL_TEST12.json')==load(R/'config/ORIGINAL_TEST12_FROZEN.json')['extra']['results']['sha256'] and load(R/'config/BEFORE_HERO_AUXILIARY.json')['extra']['original_Test12_already_complete'])
    check('complete_isolated_CPU_reproduction',load(R/'config/REPRODUCTION_VALIDATION.json')['status']=='PASS')
    images=sorted((R/'figures').glob('*.png'));decode=[]
    for p in images:
        with Image.open(p) as im:im.verify()
        decode.append(asset(p))
    check('three_real_project_figures_decode',len(images)==3,decode)
    missing=[]
    for name in ['TECHNICAL_REPORT.md','FAILURE_LEDGER.md','CAMERA_GATE_PROTOCOL_v0.1.md','REPRODUCE.md']:
        for path in re.findall(r'\]\(([^)]+)\)',(R/name).read_text()):
            if path.startswith(('http','#')):continue
            if not (R/path.split('#')[0]).exists():missing.append((name,path))
    check('reports_and_protocol_links_resolve',not missing,missing)
    forbidden=[]
    for path in (SOURCE_ROOT/'code').glob('*.py'):
        tr=ast.parse(path.read_text())
        for n in ast.walk(tr):
            if isinstance(n,(ast.Import,ast.ImportFrom)):
                names=[n.module or ''] if isinstance(n,ast.ImportFrom) else [a.name for a in n.names]
                if any(s.startswith(('torch','tensorflow','mast3r','lightglue','romatch')) for s in names):forbidden.append(str(path))
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['step','from_pretrained','VideoCapture']:forbidden.append(str(path))
    check('no_neural_training_weights_or_new_video_processing_in_task_code',not forbidden,forbidden)
    save('config/VALIDATION_RESULTS.json',dict(status='PASS_ENGINEERING_NOT_CAMERA_CERTIFICATION' if all(c['status']=='PASS' for c in checks) else 'FAIL',checks=checks,qualified_camera_N=sum(r['new_status']=='CONDITIONAL_USABLE' for r in qs),camera_denominator=5,GT=False,GPU=0,optimizer_calls=0))
    table('config/VALIDATION_RESULTS.csv',checks)
    freeze('FINAL_CODE_AND_PROTOCOL_FREEZE.json',dict(validation=asset(R/'config/VALIDATION_RESULTS.json'),qualification=asset(R/'CAMERA_QUALIFICATION.csv')))
    paths=[p for p in sorted(R.rglob('*')) if p.is_file() and 'runtime' not in p.relative_to(R).parts and p.name not in ['DELIVERABLE_HASHES.json'] and not p.name.endswith('.log')]
    save('config/DELIVERABLE_HASHES.json',[dict(relative_path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths])
    print('VALIDATION',sum(c['status']=='PASS' for c in checks),'/',len(checks),'; camera qualification 0/5; engineering only',flush=True)
    if any(c['status']!='PASS' for c in checks):
        print(json.dumps(clean([c for c in checks if c['status']!='PASS']),ensure_ascii=False),flush=True);raise SystemExit(1)
if __name__=='__main__':main()
