"""All frozen methods, exact common native IDs; gained/lost hits are explicit."""
from common import *

def main():
 assert(R/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json').exists();rows=[];summary=[];plan=load(R/'config/VIEW_PLAN.json');arms=load(R/'config/ARM_PLAN.json')
 for g in ['G06','G05','G01','G03']:
  for arm in [a['arm']for a in arms if a['group']==g]:
   for role in ['FIT','HOLDOUT']:
    totals=dict(common_N=0,gained_N=0,lost_N=0,fixed_N=0,initial_abs=0.,final_abs=0.,gained_abs=0.,lost_abs=0.)
    for r in plan:
     if r['group']!=g or r['role']!=role:continue
     cid=r['view_id'];base=np.load(R/'evaluation/local_results'/g/'B0_FROZEN'/(cid+'_EVAL.npz'));final=np.load(R/'evaluation/local_results'/g/arm/(cid+'_EVAL.npz'));a=base['active'];b=final['active'];assert np.array_equal(base['uv'],final['uv']);common=a&b;gained=~a&b;lost=a&~b;err0=abs(base['z']-base['z_H']);err1=abs(final['z']-final['z_H']);row=dict(group=g,arm=arm,role=role,view=cid,fixed_N=len(a),common_N=int(common.sum()),gained_N=int(gained.sum()),lost_N=int(lost.sum()),common_initial_mm=stats(err0[common]),common_final_mm=stats(err1[common]),gained_final_mm=stats(err1[gained]),lost_initial_mm=stats(err0[lost]));rows.append(row)
     folder=R/'hero_fit'if role=='FIT'else R/'holdout/hero';obs=np.load(folder/cid/'OBS_TRUSTED.npz');out=R/'evaluation/local_results'/g/arm/(cid+'_HIT_TRANSITIONS.npz');np.savez_compressed(out,source_pixel_id=obs['pixel_id'],HERO_X=obs['X'],common=common,gained=gained,lost=lost,initial_body_face_id=base['face_id'],final_body_face_id=final['face_id'],initial_z=base['z'],final_z=final['z'])
     for k,mask in [('common_N',common),('gained_N',gained),('lost_N',lost)]:totals[k]+=int(mask.sum())
     totals['fixed_N']+=len(a);totals['initial_abs']+=float(err0[common].sum());totals['final_abs']+=float(err1[common].sum());totals['gained_abs']+=float(err1[gained].sum());totals['lost_abs']+=float(err0[lost].sum())
    summary.append(dict(group=g,arm=arm,role=role,**totals,common_initial_MAE_mm=totals['initial_abs']/totals['common_N']if totals['common_N']else None,common_final_MAE_mm=totals['final_abs']/totals['common_N']if totals['common_N']else None,gained_final_MAE_mm=totals['gained_abs']/totals['gained_N']if totals['gained_N']else None,lost_initial_MAE_mm=totals['lost_abs']/totals['lost_N']if totals['lost_N']else None))
 save('evaluation/metrics/EXACT_PAIRED_NATIVE_CORRESPONDENCES.json',dict(summary=summary,per_view=rows));table('evaluation/metrics/EXACT_PAIRED_NATIVE_CORRESPONDENCES.csv',summary)
 print('EXACT_PAIRED_NATIVE_CORRESPONDENCE_ANALYSIS_COMPLETE',flush=True)
if __name__=='__main__':main()
