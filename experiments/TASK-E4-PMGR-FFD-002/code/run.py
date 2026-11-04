from optimize import *
from p0 import safe_p0
from data import Data
from case_gate import check_case
import traceback

def historical(scene,row,p,data):
    if scene!='G01_004':
        save('metrics/'+scene+'_C0.json',dict(status='NOT_RUN_HISTORICAL_R1',P0=None,P1=None,P2=None,P3=None));return
    rows=[]
    for name,path in [('P0',R1/'local_results/G01_004/P0.npz'),('P1_PARTIAL',R1/'local_results/G01_004/LAST_SAFE.npz')]:
        cp=dict(np.load(path));m=Body(row,p);_,Q,_=decode(p,m.R0);base=m.vertices(p);m.fields=((cp['V']-base)@Q)[:,:,None];q=np.r_[p,1.];assert abs(m.vertices(q)-cp['V']).max()<1e-10;ob=Objective(scene,m,data);met=ob.evaluate(q,gradient=False);folder=R/'local_results'/scene/'C0';folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(name+'.npz'),V=cp['V'],F=cp['F'],q=q)
        for cid,im in ob.evaluate(q,gradient=False,return_images=True)['images'].items():np.savez_compressed(folder/(name+'__'+cid+'.npz'),**im)
        rows.append(dict(stage=name,status='READ_ONLY_HISTORICAL_REEVALUATION',source=asset(path),data_objective=met['data_E'],per_view=met['per_view'],not_budget_matched=True))
    save('metrics/'+scene+'_C0.json',dict(status='HISTORICAL_NEGATIVE_BASELINE',stages=rows,P2='NOT_RUN',P3='NOT_RUN',source_commit='432c8a9',no_advantage_percentage_allowed=True))

def main():
    assert all(x['passed']for x in load(R/'metrics/PRE_RUN_VALIDATION.json'))
    results=[]
    for scene in protocol()['scene_order']:
        data=Data(scene);data.freeze()
        try:row,p=safe_p0(scene)
        except Exception as e:
            results.append(dict(case=scene,status='NOT_EXECUTABLE',reason=str(e),traceback=traceback.format_exc()));save('metrics/RESULTS.json',results);print('CASE_NOT_EXECUTABLE',scene,e,flush=True);continue
        bases={}
        for kind in ['ffd','spectral']:
            model=Body(row,p);basis=construct_basis(scene,model,kind);bases[kind]=basis;np.savez_compressed(R/'inputs'/(scene+'_'+kind+'_BASIS.npz'),fields=basis['fields'],F=basis['F'],V0=basis['V0'],mass=basis['mass']);save('metrics/'+scene+'_'+kind+'_BASIS.json',{k:v for k,v in basis.items()if k not in ['fields','F','V0','mass']});print('BASIS',scene,kind,[x['available']for x in basis['stages']],flush=True)
        gate,checks=check_case(scene,row,p,bases['ffd']['fields'])
        if not gate:
            results.append(dict(case=scene,status='NUMERICAL_GATE_FAILED',reason='same-scale per-case Mask finite differences failed; do not train',gate=checks,arms=[]));save('metrics/RESULTS.json',results);continue
        case=dict(case=scene,status='RUNNING',arms=[])
        for arm in protocol()['arm_order']:
            start=time.perf_counter();kind='spectral'if arm=='C1'else'ffd';basis=bases[kind];m=Body(row,p,basis['fields']);ob=Objective(scene,m,data);nfinal=min(96,len(m.fields[0,0]));n0=nfinal if arm=='C3'else min(12,nfinal);q=np.r_[p,np.zeros(n0)];B=None;damping=.1;records=[];stages=[]
            try:
                stages.append(save_stage(scene,arm,'P0',m,q,ob,'SAFE_START'))
                for i,stage in enumerate(['P1','P2','P3']):
                    target=nfinal if arm=='C3'else min(protocol()['mode_counts'][i],nfinal);oldV=m.vertices(q);q=np.r_[q,np.zeros(max(0,target+9-len(q)))];jump=float(abs(m.vertices(q)-oldV).max());assert jump<1e-10
                    ident=observable(m,q,ob);save('metrics/'+scene+'_'+arm+'_'+stage+'_OBSERVABILITY.json',ident)
                    if target<protocol()['mode_counts'][i]and arm!='C3':
                        stages.append(save_stage(scene,arm,stage,m,q,ob,'STAGE_BLOCKED_INSUFFICIENT_SUPPORTED_MODES',dict(requested=protocol()['mode_counts'][i],available=target,basis_candidate_attempted=True,no_fake_new_mode=True,transfer_error_mm=jump)));continue
                    # Stage objective/support changes; parameter state is retained.
                    damping=min(damping,.1);q,B,damping,summary=run_stage(scene,arm,stage,m,q,ob,B,damping,protocol()['iterations'][i],records);summary['zero_mode_transfer_mm']=jump;stages.append(save_stage(scene,arm,stage,m,q,ob,summary['status'],summary))
                    save('metrics/'+scene+'_'+arm+'_PROGRESS.json',dict(stages=stages,elapsed_seconds=time.perf_counter()-start))
                final=save_stage(scene,arm,'LAST_SAFE',m,q,ob,'LAST_ACCEPTED_GEOMETRY');best=min(stages,key=lambda x:x['fixed_common_objective']);save_stage(scene,arm,'BEST',m,np.array(best['q']),ob,'TRAINING_OBJECTIVE_BEST_STAGE',dict(selected_stage=best['stage'],selection_no_GT_no_holdout=True));case['arms'].append(dict(arm=arm,status='ALL_STAGES_ATTEMPTED',stages=stages,last_safe=final,best_stage=best['stage'],accepted_N=sum(x['accepted']for x in records),rejected_N=sum(not x['accepted']for x in records),elapsed_seconds=time.perf_counter()-start))
            except Exception as e:
                case['arms'].append(dict(arm=arm,status='ENGINEERING_INTERRUPTED',reason=str(e),traceback=traceback.format_exc(),stages=stages));print('ARM_INTERRUPTED',scene,arm,repr(e),flush=True)
            save('metrics/'+scene+'_RESULTS.json',case)
        historical(scene,row,p,data);case['status']='REPORTED_ARMS_ATTEMPTED';results.append(case);save('metrics/RESULTS.json',results)
    save('metrics/RUN_FINISHED.json',dict(finished=True,all_requested_case_candidates_considered=True,majority_stop_removed_by_user=True,no_more_jobs_scheduled=True));print('DONE',[(r['case'],r['status'])for r in results],flush=True)

if __name__=='__main__':main()
