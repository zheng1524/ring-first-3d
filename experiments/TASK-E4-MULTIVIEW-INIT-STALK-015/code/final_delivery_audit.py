"""Read-only prediction/history integrity and completed-output audit, not scientific PASS."""
from common import *
import ast

def main():
    freeze=load(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json')
    first=load(R/'provenance/GT_FIRST_ACCESS.json')
    checks={}
    checks['prediction_N_81']=len(freeze['files'])==81
    checks['frozen_prediction_hashes_unchanged']=all(sha(f['path'])==f['sha256'] for f in freeze['files'])
    checks['GT_after_all_predictions_frozen']=first['epoch']>freeze['epoch']
    checks['GT_first_access_freeze_hash_valid']=sha(first['prediction_freeze']['path'])==first['prediction_freeze']['sha256']
    checks['scale_freeze_unchanged']=sha(freeze['scale']['path'])==freeze['scale']['sha256']
    for key in ['PHASE_A_SELECTED','PHASE_B_SELECTED']:
        checks[key+'_before_GT']=load(R/'config'/(key+'.json'))['epoch']<first['epoch']
    aa=load(R/'metrics/PHASE_A_RUNS.json');bb=load(R/'metrics/PHASE_B_RUNS.json')
    checks['33_phase_A_routes']=len(aa)==33
    checks['15_phase_B_routes']=len(bb)==15
    transforms=load(R/'metrics/BLENDER_RIGID_ALIGNMENT.json')
    seen={(x['case'],x['label']) for x in transforms}
    checks['81_unique_rigid_transforms']=len(transforms)==81 and len(seen)==81
    errors=[]
    for q in transforms:
        rot=np.asarray(q['R']);errors.append(max(float(np.max(abs(rot.T@rot-np.eye(3)))),abs(np.linalg.det(rot)-1)))
    checks['SE3_scale1_no_mirror']=all(x['scale']==1 for x in transforms)and max(errors)<1e-8
    gt=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json')
    checks['81_CD_Dxy_results']=len(gt)==81 and all(x.get('Chamfer_MAE_mm') is not None and x.get('Dxy_AE_mm') is not None for x in gt)
    copy_index=load(R/'metrics/REVIEW_MESH_COPY_INDEX.json')
    copies=[q for q in copy_index if 'review_copy' in q]
    copy_ok=[]
    for q in copies:
        a=np.load(q['source']['path']);b=np.load(q['review_copy']['path'])
        copy_ok.append(np.array_equal(a['V'],b['V'])and np.array_equal(a['F'],b['F']))
    checks['81_exact_review_geometry_copies']=len(copies)==81 and all(copy_ok)
    checks['11_final_body_PLY']=sum('review_PLY' in q for q in copy_index)==11
    history=load(R/'provenance/HISTORICAL_PROTECTION.json')['files'];changed=[];missing=[]
    for q in history:
        p=Path(q['path'])
        if not p.is_absolute():p=REPO/p
        if not p.exists():missing.append(str(p))
        elif sha(p)!=q['sha256']:changed.append(str(p))
    checks['historical_assets_unchanged']=not changed and not missing
    sources=load(R/'provenance/PHASE_A_CODE_AND_PROTOCOL_FROZEN.json')['files']
    checks['phase_A_24_training_sources_unchanged']=len(sources)==24 and all(sha(x['path'])==x['sha256'] for x in sources)
    changes=[]
    for q in load(R/'provenance/PHASE_B_CODE_SEEDS_AND_PROTOCOL_FROZEN.json')['files']:
        if sha(q['path'])!=q['sha256']:changes.append(Path(q['path']).name)
    expected={'phase_b.py','best_rigid015.py','final_figures.py','postprocess_all.py','prepare_evaluation.py'}
    checks['phase_B_changes_only_documented_IO_and_output']=set(changes)==expected
    ast_ok=True
    for p in (R/'code').glob('*.py'):
        try:ast.parse(p.read_text())
        except SyntaxError:ast_ok=False
    checks['all_current_sources_parse']=ast_ok
    checks['4_core_figures_exist']=all((R/'figures'/f).stat().st_size>10000 for f in [
        'Fig1_All11_Initializers_And_Updates.png','Fig2_All5_Ip_Stalk_Comparison.png',
        'Fig3_Current_Coverage_Gradient_And_Motion.png','Fig4_All11_Rigid_Aligned_GT_Comparison.png'])
    checks['11_case_and5_stalk_figures']=len(list((R/'figures/phase_A').glob('*_Initialization_And_Update.png')))==11 and len(list((R/'figures/phase_B').glob('*_Stalk_Comparison.png')))==5
    gradient_failures=[]
    for p in (R/'arms').glob('Stalk-*/metrics/*FINAL_COMPONENT_GRADIENTS.json'):
        g=load(p)
        if not g['additivity_pass']:gradient_failures.append(dict(case=g['case'],arm=g['arm'],error=g['additivity_relative_error'],threshold=g['additivity_threshold'],evidence=str(p)))
    result=dict(epoch=time.time(),integrity_checks=checks,all_integrity_checks_pass=all(checks.values()),
        target_groups=11,phase_A_routes=33,phase_B_routes=15,evaluation_models=81,
        audited_historical_files=len(history),unchanged_historical_files=len(history)-len(changed)-len(missing),changed_historical_files=changed,missing_historical_files=missing,
        maximum_rotation_orthogonality_or_determinant_error=max(errors),
        phase_B_changed_files=changes,documented_amendments=['PHASE_B_ENGINEERING_IO_FIX.json','EVAL_VIEW_METADATA_ADAPTER.json','OUTPUT_LAYOUT_FIX.json','FINAL_REVIEW_PUBLICATION_ADAPTER.json','FIRST_GT_ACCESS_PRESERVATION.json'],
        scientific_success=False,B0_status='B0_NOT_PASSED_THIS_RUN',
        retained_failed_test='G02 initial gradient additivity 0.00038848 > 0.0001',
        retained_final_gradient_failures=gradient_failures,
        no_historical_measurement_fallback=True,no_new_training_after_GT=True)
    save('metrics/DELIVERY_VERIFICATION.json',result)
    assert all(checks.values()),json.dumps(clean(checks),ensure_ascii=False)
    save('runtime/STATUS.json',dict(phase='COMPLETE_AWAITING_HUMAN_REVIEW',epoch=time.time(),
        phase_A_routes=33,phase_B_routes=15,evaluation_models=81,B0='NOT_PASSED_THIS_RUN',training_stopped=True))
    print('DELIVERY_INTEGRITY_PASS_SCIENTIFIC_FAILURES_RETAINED',len(history),flush=True)

if __name__=='__main__':main()
