from common import *
import ast,subprocess
def main():
    checks={}
    for fn in ['PREOPT_FREEZE','PREDICTIONS_FROZEN_BEFORE_EVALUATION']:
        a=load(R/'assets_index'/(fn+'.json'));bad=[x['path']for x in a['files']if sha(x['path'])!=x['sha256']];checks[fn]=dict(passed=not bad,N=len(a['files']),bad=bad)
    for fn in ['HISTORY_PROTECTION']:
        a=load(R/'assets_index'/(fn+'.json'));bad=[x['path']for x in a if sha(x['path'])!=x['sha256']];checks[fn]=dict(passed=not bad,N=len(a),bad=bad)
    a=load(R/'assets_index/A_FROZEN.json');bad=[x['path']for x in a['sha_files']if sha(x['path'])!=x['sha256']];checks['A_unmodified']=dict(passed=not bad,N=len(a['sha_files']),bad=bad)
    prior=Path(load(R/'config/PROTOCOL.json')['A_frozen_root']);checks['Ring_renderer_exact']=dict(passed=sha(R/'code/p3d.py')==sha(prior/'code/p3d.py'))
    fair=load(R/'metrics/FAIRNESS.json');checks['fairness']=dict(passed=fair['same_full_view_sequence']and fair['A_reused_without_optimizer']and all(x['same_P0_V_F']and x['holdout_depth_loss_calls']==0 and x['optimizer_steps']==300 and x['accepted_steps']==300 and x['stage2_start_matches_stage1']is not False for x in fair['rows']))
    checks['depth_gradients']=dict(passed=load(R/'metrics/PREFLIGHT.json')['passed'])
    checkpoint_rows=[]
    for name in ['virtual','real']:
        for arm in ['B','C','D']:
            files=list((R/'local_results'/name/arm).glob('STEP_*.pt'));assert len(files)==9
            for p in files:
                import torch
                s=torch.load(p,map_location='cpu',weights_only=False);assert all(k in s for k in ['step','stage','global_q','local','origin','optimizer','numpy_state','torch_state','cuda_state','config'])
            checkpoint_rows.append(dict(case=name,arm=arm,checkpoint_N=len(files),all_optimizer_and_rng_states=True))
    checks['checkpoint_recovery_state']=dict(passed=True,rows=checkpoint_rows)
    for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
    checks['syntax']=dict(passed=True)
    figures=[]
    for p in sorted((R/'figures').glob('Fig*.png')):
        im=Image.open(p);im.verify();figures.append(asset(p))
    checks['four_real_figures']=dict(passed=len(figures)==4,files=figures)
    data=[asset(p)for folder in ['inputs','depth_observations','local_results']for p in sorted((R/folder).rglob('*'))if p.is_file()]
    save('assets_index/LOCAL_RESULTS.json',dict(root=str(R),files=data,large_data_uploaded=False,checkpoints=checkpoint_rows))
    scientific=load(R/'metrics/RESULT.json');checks['honest_geometry_failure']=dict(passed=scientific['geometry_passed_runs']==0 and all(x['geometry_status']=='FAIL'for x in scientific['failures']))
    save('assets_index/DELIVERY_VALIDATION.json',dict(passed=all(v['passed']for v in checks.values()),engineering_delivery_only_not_geometry_pass=True,checks=checks))
    print('DELIVERY_VALIDATION',all(v['passed']for v in checks.values()),flush=True)
if __name__=='__main__':main()
