"""Final hashes/protection and explicit artifact index; no new scientific runs."""
from crop import *
import re

def main():
    original=load(R/'config/PROTECTED_START.json');after=protected_state();assert original==after,'HISTORICAL_WORKTREE_CHANGED'
    checked=[]
    for row in MANIFEST['sources']:
        for a in row['assets'].values():assert sha(a['path'])==a['sha256'],a['path'];checked.append(a['path'])
    protocol=load(R/'config/BEFORE_FORMAL_CALCULATION.json')['protocol'];assert sha(R/'config/GATE_A_PREREGISTERED.json')==protocol['sha256'],'PREREGISTERED_THRESHOLDS_CHANGED'
    official=load(R/'config/OFFICIAL_ARTIFACTS.json')
    for a in official['official_files']:assert sha(NF/a['relative_path'])==a['sha256'],a['relative_path']
    cleanup=load(R/'PROJECTIVE_CLEANUP_SUMMARY.json');assert cleanup['rounds']==1 and cleanup['excluded_N']==46 and cleanup['retained_unresolved_N']==9
    for row in cleanup['sources']:
        s=native(row['source']);d=np.load(row['derived_file']['path']);mask=d['projective_excluded'];assert np.array_equal(d['depth_mm'][~mask],s['depth'][~mask]);assert np.array_equal(d['valid'],s['valid']&~mask);assert (d['depth_mm'][mask]==0).all()
    post=list(csv.DictReader((R/'POST_REVIEW_INPUT_CONTRACTS.csv').open()));assert all(r['selected_domain_OUT_OF_GRID_N']=='0'and r['invalid_nonzero_N']=='0'and r['crop_affine_exactly_unchanged']=='True'and r['c2w_rotation_unchanged']=='True'for r in post)
    cross=load(R/'derived_projective_v1/config/CROSS_VIEW_GATE.json');assert cross['all_analytic_pass']and cross['pair_count']==24
    model=load(R/'config/MODEL_LOAD_GUARD_RESULTS.json');assert model['model_forward_calls']==0 and not model['CUDA_initialized']and not model['forbidden_GT_training_imports']
    replay=load(R/'runtime/replay_delivery/REPLAY_VERIFY.json');assert replay['status']=='PASS'and len(replay['comparisons'])==9
    save('config/FINAL_PROTECTION_CHECK.json',dict(all_historical_worktrees_unchanged=True,worktree_N=len(after),source_asset_checks=len(checked),unique_original_paths=len(set(checked)),source_SHA_unchanged=True,official24_files_SHA_unchanged=True,original_inputs_modified=0,derived_modified_pixel_N=46,unresolved_pixels_retained=9,cleanup_rounds=1,crop_rule_unchanged=True,projection_original_denominators_retained=True,GPU=0,forward_calls=0,GT_read=False,main_environment_modified=False,replay_identical_CSV_N=9,baseline_preregistered_thresholds_unchanged=True))
    state=load(R/'GATE_A_STATUS.json')
    for gate in state['gates']:
        if gate['gate']=='A8':gate['status']='PASS'
    state['final_protection']='PASS';state['safe_replay_identical_CSV_N']=9;save('GATE_A_STATUS.json',state);table('GATE_A_DECISION.csv',state['gates'])
    report=R/'TECHNICAL_REPORT.md';report.write_text(report.read_text().replace('PASS_SUBJECT_TO_FINAL_HASH_CHECK','PASS'))
    local=[]
    for base in [R/'local_results',R/'derived_projective_v1/local_results']:
        for p in sorted(base.rglob('*')):
            if p.is_file():local.append(asset(p))
    save('LOCAL_RESULTS_INDEX.json',dict(local_task_root=R,files=local,bytes=sum(a['bytes']for a in local),checkpoint_index='config/CHECKPOINT_FILES.json',official_source_index='config/OFFICIAL_ARTIFACTS.json',safe_replay_evidence=asset(R/'runtime/replay_delivery/REPLAY_VERIFY.json'),no_neural_fusion_Mesh=True,large_arrays_and_weights_uploaded=False))
    # Append actual post-review/official geometry reuse to the original matrix.
    matrix=R/'CODE_REUSE_MATRIX.md';text=matrix.read_text();marker='## Post-review exact execution reuse'
    if marker not in text:
        text+='\n'+marker+'\n\nOfficial `pipeline.utils.unproject` was called only as a pure CPU geometric function (no module forward). SHA256 `'+sha(NF/'pipeline/utils.py')+'`.\n\n`build_crops.main`, `cross_view.main`, `metric_domain.make_domain/main` were reused by exact AST binding for derived data and safe replay; `SameCameraScene.draw` was also imported unchanged for Fig2. No projection/unprojection duplication. Execution fingerprints are in config/DERIVED_EXECUTION_PROVENANCE.json and config/CODE_REUSE_AFTER_SCOPE_UPDATE.json.\n';matrix.write_text(text)
    required=['TECHNICAL_REPORT.md','FAILURE_LEDGER.md','REPRODUCE.md','CODE_REUSE_MATRIX.md','CHECKPOINT_COMPATIBILITY_MATRIX.csv','SOURCE_AND_CROP_MANIFEST.json','METRIC_TRANSFORM.json','CROP_GEOMETRY_TESTS.csv','CROSS_VIEW_PROJECTION_VALIDATION.csv','GT_ISOLATION_AUDIT.md']
    for file in required:assert(R/file).is_file(),file
    links=[]
    for p in R.glob('*.md'):
        if p.name=='TASK.md':continue
        for t in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if t.startswith(('http:','https:','#')):continue
            ok=(p.parent/t.split('#')[0]).exists();assert ok,(p.name,t);links.append(dict(document=p.name,target=t,exists=ok))
    for p in (R/'code').glob('*.py'):compile(p.read_text(),str(p),'exec')
    png=[]
    for p in sorted((R/'figures').glob('*.png')):
        im=Image.open(p);assert im.width>=1500 and im.height>=1200;png.append(dict(**asset(p),W=im.width,H=im.height))
    assert len(png)==6
    save('config/DELIVERY_VALIDATION.json',dict(required=required,links=links,PNG=png,syntax_files=len(list((R/'code').glob('*.py'))),code_snapshot_commit=git(REPO,'rev-parse','HEAD'),parent_commit=load(R/'config/GATE_A_PREREGISTERED.json')['parent_commit'],Gate_A='FAIL_RETAINED',actual_forward=0,manual_visual_note='assistant viewed all6 PNG; researcher reviewed2 pixel montages. PM anatomical acceptance pending.',verbatim_PM_markdown_two_space_hardbreaks_preserved=True))
    files=[p for p in R.rglob('*')if p.is_file()and not any(x in ['runtime','local_results','__pycache__']for x in p.relative_to(R).parts)and p.name!='DELIVERY_INDEX.json']
    save('DELIVERY_INDEX.json',dict(task=R.name,files=[asset(p)for p in sorted(files)],source_commit_for_numeric_snapshot=git(REPO,'rev-parse','HEAD'),byte_count=sum(p.stat().st_size for p in files),weights_or_raw_data_uploaded=False,scientific_gate='GATE_A_FAIL',Gate_B_authorized=False))
    print('FINAL_DELIVERY',len(files)+1,'curated files;',sum(p.stat().st_size for p in files),'bytes; GATE_A_FAIL retained; protection PASS',flush=True)
if __name__=='__main__':main()
