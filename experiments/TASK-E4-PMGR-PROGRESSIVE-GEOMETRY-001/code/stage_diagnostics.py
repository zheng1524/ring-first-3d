"""Post-fit descriptive first-change stages; never used to select models."""
from inputs import *
from collections import Counter
def main():
    rows=[]
    for file in sorted((R/'metrics/runs').glob('*__PMGR.json')):
        x=load(file);ss=x['stages'];cid=protocol()['scenes'][x['scene']]['B'][0];o=obs(cid);arrays=[dict(np.load(R/'local_results'/x['key']/(s['stage']+'__'+cid+'.npz')))for s in ss];common=np.logical_and.reduce([a['pair_hit']for a in arrays]);pp=o['pairs'][common];D=[float(abs(a['z'][pp[:,0]]-a['z'][pp[:,1]]-o['delta'][common]).mean())for a in arrays];I=[next(v['IoU']for v in st['evaluations']if v['source']==cid)for st in ss]
        first=lambda values,better:next((ss[j]['stage']for j in range(1,4)if better(values[j],values[0])),None)
        rows.append(dict(case_id=x['key'],scene=x['scene'],initial=x['initial'],seed=x['seed'],first_B_Mask_IoU_increase=first(I,lambda a,b:a>b),first_B_common_relative_D_decrease=first(D,lambda a,b:a<b),B_joint_common_pair_N=int(common.sum()),registered_pair_N=256,stage_IoU=I,stage_joint_common_D_MAE_mm=D,first_rejected_proposal_stage=next((s['stage']for s in x['steps']if not s['accepted']),None),accepted_proposals_by_stage=[sum(t['accepted']for t in x['steps']if t['stage']==s['stage'])for s in ss[1:]],max_final_displacement_mm=ss[-1]['max_P0_displacement_mm'],posthoc_descriptive_only=True))
    save('metrics/PMGR_STAGE_DIAGNOSTICS.json',rows);table('metrics/PMGR_STAGE_DIAGNOSTICS.csv',rows)
    save('metrics/FIRST_STAGE_COUNTS.json',dict(first_Mask_increase=dict(Counter(str(r['first_B_Mask_IoU_increase'])for r in rows)),first_D_decrease=dict(Counter(str(r['first_B_common_relative_D_decrease'])for r in rows)),first_proposal_rejection=dict(Counter(str(r['first_rejected_proposal_stage'])for r in rows)),not_a_new_PASS_criterion=True))
    print(load(R/'metrics/FIRST_STAGE_COUNTS.json'))
if __name__=='__main__':main()
