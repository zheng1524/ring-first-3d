"""Complete the authorized second case from its one existing safe candidate.
Corrects an unintended legacy observation veto; never reruns initialization.
"""
from run import *
from zoneinfo import ZoneInfo
import datetime,subprocess

def main():
    scene='G06_004';file=R/'metrics/G06_CONTINUATION_START.json';assert not file.exists(),'Do not repeat a completed continuation'
    initial=load(R/'metrics/G06_004_SAFE_P0.json');assert initial['reasons']==['P0_MASK_EXPLANATION_LOSS'];path=R/'local_results/G06_004_P0_CANDIDATE.npz';candidate=dict(np.load(path));p=candidate['q'];row=p0(scene,'E1');body=Body(row,p);assert abs(body.vertices(p)-candidate['V']).max()<1e-10
    col=endpoint(Collision(scene),candidate['V'],candidate['F'],'G06_CONTINUATION_PHYSICAL');assert not col['collision']and initial['Blender']['EXACT_intersection_volume_mm3']==0
    save('metrics/INITIAL_EXECUTION_RESULTS.json',load(R/'metrics/RESULTS.json'));save('metrics/RUN_FINISHED_PHASE1.json',load(R/'metrics/RUN_FINISHED.json'));save('metrics/G06_CONTINUATION_START.json',dict(timestamp=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),candidate=asset(path),input_freeze=asset(R/'metrics/INPUT_FREEZE.json'),executed_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),admission='CONDITIONAL_PHYSICAL_START_WITH_MASK_REGRESSION',no_reinitialization=True,no_loss_or_evaluation_change=True))
    data=Data(scene);data.freeze();bases={}
    for kind in ['ffd','spectral']:
        m=Body(row,p);b=construct_basis(scene,m,kind);bases[kind]=b;np.savez_compressed(R/'inputs'/(scene+'_'+kind+'_BASIS.npz'),fields=b['fields'],F=b['F'],V0=b['V0'],mass=b['mass']);save('metrics/'+scene+'_'+kind+'_BASIS.json',{k:v for k,v in b.items()if k not in ['fields','F','V0','mass']});print('BASIS',scene,kind,[x['available']for x in b['stages']],flush=True)
    gate,checks=check_case(scene,row,p,bases['ffd']['fields'])
    if not gate:
        save('metrics/G06_CONTINUATION_FINISHED.json',dict(timestamp=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),finished=True,status='NUMERICAL_GATE_FAILED_BEFORE_UPDATES',checks=checks));print('G06_NUMERICAL_GATE_FAILED; no updates');return
    case=dict(case=scene,status='RUNNING',P0_admission='CONDITIONAL_PHYSICAL_START_WITH_MASK_REGRESSION',original_initialization_warning=asset(R/'metrics/G06_004_SAFE_P0.json'),arms=[])
    for arm in protocol()['arm_order']:
        start=time.perf_counter();kind='spectral'if arm=='C1'else'ffd';b=bases[kind];m=Body(row,p,b['fields']);ob=Objective(scene,m,data);nfinal=min(96,m.fields.shape[-1]);q=np.r_[p,np.zeros(nfinal if arm=='C3'else min(12,nfinal))];B=None;damping=.1;records=[];stages=[]
        try:
            stages.append(save_stage(scene,arm,'P0',m,q,ob,'PHYSICAL_START_MASK_REGRESSION_WARNING'))
            for i,stage in enumerate(['P1','P2','P3']):
                target=nfinal if arm=='C3'else min(protocol()['mode_counts'][i],nfinal);oldV=m.vertices(q);q=np.r_[q,np.zeros(max(0,target+9-len(q)))];jump=float(abs(m.vertices(q)-oldV).max());assert jump<1e-10;save('metrics/'+scene+'_'+arm+'_'+stage+'_OBSERVABILITY.json',observable(m,q,ob))
                if target<protocol()['mode_counts'][i]and arm!='C3':
                    stages.append(save_stage(scene,arm,stage,m,q,ob,'STAGE_BLOCKED_INSUFFICIENT_SUPPORTED_MODES',dict(requested=protocol()['mode_counts'][i],available=target,basis_candidate_attempted=True,no_fake_new_mode=True,transfer_error_mm=jump)));continue
                damping=min(damping,.1);q,B,damping,summary=run_stage(scene,arm,stage,m,q,ob,B,damping,protocol()['iterations'][i],records);summary['zero_mode_transfer_mm']=jump;stages.append(save_stage(scene,arm,stage,m,q,ob,summary['status'],summary));save('metrics/'+scene+'_'+arm+'_PROGRESS.json',dict(stages=stages,elapsed_seconds=time.perf_counter()-start))
            final=save_stage(scene,arm,'LAST_SAFE',m,q,ob,'LAST_ACCEPTED_GEOMETRY');best=min(stages,key=lambda x:x['fixed_common_objective']);save_stage(scene,arm,'BEST',m,np.array(best['q']),ob,'TRAINING_OBJECTIVE_BEST_STAGE',dict(selected_stage=best['stage'],selection_no_GT_no_holdout=True));case['arms'].append(dict(arm=arm,status='ALL_STAGES_ATTEMPTED',stages=stages,last_safe=final,best_stage=best['stage'],accepted_N=sum(x['accepted']for x in records),rejected_N=sum(not x['accepted']for x in records),elapsed_seconds=time.perf_counter()-start))
        except Exception as e:case['arms'].append(dict(arm=arm,status='ENGINEERING_INTERRUPTED',reason=str(e),traceback=traceback.format_exc(),stages=stages));print('ARM_INTERRUPTED',arm,repr(e),flush=True)
        save('metrics/'+scene+'_RESULTS.json',case)
    historical(scene,row,p,data);case['status']='REPORTED_ARMS_ATTEMPTED_WITH_P0_WARNING';results=load(R/'metrics/RESULTS.json');results=[x if x['case']!=scene else case for x in results];save('metrics/RESULTS.json',results);save('metrics/'+scene+'_RESULTS.json',case);save('metrics/G06_CONTINUATION_FINISHED.json',dict(timestamp=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),finished=True,all_original_arms_attempted=True,no_reinitialization=True));print('G06_DONE',[(x['arm'],x['status'])for x in case['arms']],flush=True)

if __name__=='__main__':main()
