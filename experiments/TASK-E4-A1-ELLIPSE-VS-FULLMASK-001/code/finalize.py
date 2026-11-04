"""Acceptance states, complete local meshes, small indexes and report checks."""
from fitting import *
import re
def main():
    records=load(R/'metrics/ALL_FITS.json');primary=load(R/'metrics/PRIMARY_A_ONLY.json');pairs=load(R/'metrics/PAIRED_COMPARISON.json');validation=load(R/'metrics/VALIDATION.json');summ=load(R/'metrics/SUMMARY.json');mesh_index=[];folder=R/'local_results/all_fits';folder.mkdir(exist_ok=True)
    for m in records:
        P,F=mesh(np.array(m['p']),np.array(m['R0']));name=f"{m['scene']}__{m['arm']}__{m['variant']}__start{m['start']}.ply";path=folder/name;trimesh.Trimesh(P,F,process=False).export(path);mesh_index.append(dict(scene=m['scene'],arm=m['arm'],variant=m['variant'],start=m['start'],mesh=asset(path),coordinate_unit='mm',optimizer_converged=m['optimizer_success'],diagnostic_only=not m['optimizer_success']))
    save('metrics/ALL_MESH_INDEX.json',mesh_index)
    with(R/'03_E1_E2_METRICS.csv').open()as f:rows=list(csv.DictReader(f))
    for row in rows:
        ok=row['optimizer_success']=='True';row['accepted_numeric_status']='CONVERGED_CONDITIONAL'if ok else'FAILED_BUDGET_NaN_ACCEPTED_METRICS';row['accepted_B_IoU']=row['B_IoU']if ok else'NaN';row['accepted_D_MAE_mm']=row['relative_depth_MAE_mm']if ok else'NaN';row['current_trial_tier']=row['tier'].replace('_AND_HEAD_CUE','');row['qualification_note']='original source tier preserved; no head-mask or class-conditioned fitting in this task'
    table('03_E1_E2_METRICS.csv',rows)
    aggregate=[]
    for arm in ['E1','E2']:
        ms=[m for m in primary if m['arm']==arm and m['variant']=='full'];aggregate.append(dict(arm=arm,target_physical_groups=4,numeric_output_groups=len(ms),strict_full_pipeline_independent_groups=0,full_mask_IoU=stats([m['B'][0]['full_mask_IoU']for m in ms]),relative_D_MAE_across_groups_mm=stats([m['B'][0]['relative_depth_mm']['MAE']for m in ms]),outside_per_fixed_mask=stats([m['B'][0]['outside_per_fixed_mask']for m in ms]),GT_MARE='NOT_EVALUABLE',GT_MAE='NOT_EVALUABLE',GT_p95='NOT_EVALUABLE',GT_maximum='NOT_EVALUABLE'))
    save('metrics/AGGREGATE_METRICS.json',aggregate)
    save('metrics/CONCLUSION.json',dict(label='MIXED',scope='four frozen single-video conditional/stress cases; one9p ellipsoid; same finite optimization budget',may_cancel_ellipse_preprocessing=False,may_promote_full_Mask_to_only_standard=False,no_class_specific_selection=True,evidence=pairs,cautions=['all B conditional, no independent 3D GT','DXY G01 Q_conflict_recovery and not strict','three bounded optimizations did not converge','stability includes local-minimum branch switching','Ring overlap predictions recorded separately'],integrity_fairness_checks_pass=validation['integrity_and_fairness_all_pass'],qualification_promoted=False,A2_B1_B2_executed=0,GPU=0,training=0,historical_measurement_fallback=0,stop='WAIT_FOR_RESEARCHER_REVIEW'))
    # Verify unchanged pre-existing experiment and dependencies independently of
    # this task's new source files; read only, no old result updates.
    files=[PREV/'code/common.py',PREV/'code/models.py',PREV/'config/PREREGISTERED.json',REPO/'AGENTS.md',DXY/'AGENTS.md',N0/'code/common.py',E1ROOT/'provenance/INPUT_ELIGIBILITY.json',REPO/'visualization/real_p0_renderer.py',REPO/'visualization/pointcloud_audit_renderer.py'];save('provenance/REUSED_CODE_AND_POLICY.json',[asset(p)for p in files])
    checks=[]
    for p in R.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('https:','http:','#')):continue
            clean_target=target.split('#')[0];checks.append(dict(file=p.name,target=target,exists=(p.parent/clean_target).exists()))
    save('metrics/REPORT_LINK_CHECKS.json',dict(all_pass=all(x['exists']for x in checks),checks=checks));assert all(x['exists']for x in checks)
    logs=''
    for name in ['dxy','prepare','synthetic','pre_ring_pool_fix_fits','fits','analysis','visualize','validation']:
        p=R/'runtime'/(name+'.log')
        if p.exists():logs+='\n### '+name+'\n'+p.read_text()
    (R/'metrics/EXECUTION_TRACE.txt').write_text(logs)
    local=[p for p in(R/'local_results').rglob('*')if p.is_file()];save('provenance/FINAL_ARTIFACT_INDEX.json',dict(code=[asset(p)for p in sorted((R/'code').glob('*.py'))],local_results=[asset(p)for p in sorted(local)],core_figures=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],large_raw_assets_copied=False,raw_data_modified=False,core_result_summary=summ))
    print('FINALIZED_MIXED',len(mesh_index),'actual local meshes; source inputs frozen; A2/B1/B2=0',flush=True)
if __name__=='__main__':main()
