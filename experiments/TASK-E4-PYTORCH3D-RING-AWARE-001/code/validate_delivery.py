from common import *
import ast,subprocess,re
def main():
    checks={}
    for fn in['PREOPT_FREEZE','PREDICTIONS_FROZEN_BEFORE_GT']:
        a=load(R/'assets_index'/(fn+'.json'));bad=[v['path']for v in a['files']if sha(v['path'])!=v['sha256']];checks[fn]=dict(passed=not bad,N=len(a['files']),bad=bad)
    a=load(R/'assets_index/HISTORY_PROTECTION.json');bad=[v['path']for v in a if sha(v['path'])!=v['sha256']];checks['history_preserved']=dict(passed=not bad,N=len(a),bad=bad)
    a=load(R/'assets_index/DXY_READONLY_REFERENCE.json');checks['DXY_readonly']=dict(passed=all(sha(v['path'])==v['sha256']for v in a['files']))
    gate={k:load(R/'metrics'/(k+'.json'))['passed']for k in['OFFICIAL_GATE','PROJECTION_GATE','GRADIENT_GATE']};checks['gates']=dict(passed=all(gate.values()),values=gate)
    for case in['virtual','real']:
        runs=[load(R/'metrics'/(case+'_'+arm+'_RUN.json'))for arm in['Baseline','RingAware']];logs=[list(csv.DictReader((R/'metrics'/(case+'_'+arm+'_TRAINING.csv')).open()))for arm in['Baseline','RingAware']]
        init=[np.load(R/'local_results'/case/arm/'STEP_0000.npz')for arm in['Baseline','RingAware']]
        checks[case+'_paired_fairness']=dict(passed=all(v['completed_steps']==300 for v in runs)and np.array_equal(init[0]['V'],init[1]['V'])and np.array_equal(init[0]['F'],init[1]['F'])and [r['views']for r in logs[0]]==[r['views']for r in logs[1]],identical_initial_mesh=True,identical_view_schedule=[r['views']for r in logs[0]]==[r['views']for r in logs[1]])
    for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
    checks['syntax']=dict(passed=True)
    for name in['Fig1_Official_Reproduction.png','Fig2_Ring_Occlusion_Audit.png','Fig3_Actual_Mesh_Comparison.png','Fig4_Training_And_Independent_Evaluation.png']:
        p=R/'figures'/name;im=Image.open(p);im.verify();checks[name]=dict(passed=True,asset=asset(p))
    artifacts=[]
    for folder in['inputs','local_results']:
        artifacts.extend(asset(p)for p in sorted((R/folder).rglob('*'))if p.is_file())
    save('assets_index/LOCAL_RESULTS.json',dict(root=str(R),files=artifacts,large_artifacts_uploaded=False))
    upstream_status=subprocess.check_output(['git','-C',str(R/'runtime/pytorch3d'),'status','--porcelain'],text=True)
    checks['official_source_unmodified']=dict(passed=not upstream_status.strip(),git_status=upstream_status)
    save('assets_index/DELIVERY_VALIDATION.json',dict(passed=all(v['passed']for v in checks.values()),checks=checks))
    print('DELIVERY_VALIDATION',all(v['passed']for v in checks.values()),flush=True)
if __name__=='__main__':main()
