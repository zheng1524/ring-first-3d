"""Final frozen-run summary, including all failures and conditioned-error caveats."""
from common import *
from collections import Counter
ROOT=R

def main():
 assert(ROOT/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json').exists();plan=load(ROOT/'config/ARM_PLAN.json');rows=[];grads=[];local=[]
 for a in plan+ [v for v in load(ROOT/'config/ARM_PLAN_R1_RETAINED.json')if v['group']=='G06' and v['arm']in['B1_FULL','B2_TRUSTED']]:
  g,tag=a['group'],a['arm'];p=Path(a['path']);run=load(p/'metrics'/(g+'_RUN.json'));history=load(p/'metrics'/(g+'_TRAINING.json'));trials=load(p/'metrics'/(g+'_CANDIDATES.json'));counts=Counter(k for t in trials for k in t['reasons']);V=np.load(p/'local_results'/g/'FINAL.npz')['V'];V0=np.load(ROOT/'inputs'/g/'INITIAL.npz')['V'];delta=V-V0
  rows.append(dict(group=g,arm=tag,phase='MAIN_R2'if tag.endswith('_COH16')else'R1_RETAINED_DIAGNOSTIC',**run,iteration_rejections=run['attempts']-run['accepted'],candidate_checks=len(trials),rejected_candidate_checks=sum(not t['accepted']for t in trials),reasons=dict(counts),initial_parts=history[0]['parts']if history else{},final_parts=history[-1]['parts']if history else{},loss_ramp_caveat='ramp changes through iteration40: total first/final not a stationary-objective comparison',elapsed_caveat='R1 B2 was resumed: seconds only this resumed segment'if tag=='B2_TRUSTED'else'full process runtime'))
  for label in ['INITIAL','FINAL']:
   pth=p/'metrics'/(g+'_'+label+'_GRADIENTS.json')
   if not pth.exists():continue
   ga=np.load(p/'local_results'/g/(label+'_COMPONENT_GRADIENTS.npz'))
   for rec in load(pth):
    cid=rec.get('view');key=('hero_'if rec['term']=='HERO'else'silhouette_')+str(cid)
    k=dict(group=g,arm=tag,stage=label,**rec)
    if key in ga.files:
     v=ga[key];norm=np.linalg.norm(v);den=norm*np.linalg.norm(delta);k.update(all_parameter_gradient_finite=bool(np.isfinite(v).all()),nonzero_vertex_N=int((np.linalg.norm(v,axis=1)>1e-14).sum()),descent_to_total_delta_cosine=float(np.sum(-v*delta)/den)if den>0 else None)
    grads.append(k)
  if tag.endswith('_COH16'):
   h=np.load(ROOT/'hero_fit'/a['HERO_views'][0]/('OBS_'+('TRUSTED'if a['kind']=='OLD'else a['kind'])+'.npz'));local.append(dict(group=g,arm=tag,body_initial_XYZ_min=V0.min(0),body_initial_XYZ_max=V0.max(0),body_final_XYZ_min=V.min(0),body_final_XYZ_max=V.max(0),first_source_HERO_XYZ_min=h['X'].min(0),first_source_HERO_XYZ_max=h['X'].max(0)))
 save('metrics/OPTIMIZATION_PROCESS_SUMMARY.json',rows);table('metrics/OPTIMIZATION_PROCESS_SUMMARY.csv',rows);save('metrics/PER_VIEW_ACTUAL_GRADIENTS.json',grads);table('metrics/PER_VIEW_ACTUAL_GRADIENTS.csv',grads);save('metrics/BODY_AND_HERO_EXTENTS.json',local)
 comparison=load(ROOT/'evaluation/metrics/COMPARISON.json');base={r['group']:r for r in comparison if r['arm']=='B0_FROZEN'};paired=[]
 for r in comparison:
  if r['arm']=='B0_FROZEN':continue
  b=base[r['group']];paired.append(dict(group=r['group'],arm=r['arm'],phase=r['phase'],delta_HERO_MAE_mm=r['HERO_MAE_mm']-b['HERO_MAE_mm']if r['HERO_MAE_mm']is not None and b['HERO_MAE_mm']is not None else None,delta_FIT_active_N=r['FIT_active_N']-b['FIT_active_N'],delta_FIT_IoU=r['FIT_IoU']-b['FIT_IoU'],delta_HOLDOUT_IoU=r['HOLDOUT_IoU']-b['HOLDOUT_IoU'],delta_Ring64_min_mm=r['Ring64_min_mm']-b['Ring64_min_mm'],initial_Ring64_min_mm=b['Ring64_min_mm'],final_Ring64_min_mm=r['Ring64_min_mm'],self_intersections=r['self_intersections'],max_displacement_mm=r['max_displacement_mm']))
 save('evaluation/metrics/PAIRED_VS_FROZEN_BODY.json',paired);table('evaluation/metrics/PAIRED_VS_FROZEN_BODY.csv',paired)
 # Local full results are indexed; large HERO and checkpoints remain outside Git.
 paths=[]
 for root in [ROOT/'hero_fit',ROOT/'holdout/hero',ROOT/'arms',ROOT/'evaluation/local_results']:
  paths += [p for p in root.rglob('*')if p.is_file()and p.suffix in ['.npz','.pt','.ply']]
 save('RESULT_INDEX.json',dict(root=str(ROOT),files=[asset(p)for p in sorted(paths)],checkpoint_restore='serial018.py skips FINAL and resumes latest attempt/Adam/RNG checkpoint for unfinished arms',all_files_local=True,large_original_models_not_copied=True))
 print('ALL_FROZEN_RUN_DIAGNOSTICS_AND_ARTIFACT_INDEX_WRITTEN',flush=True)
if __name__=='__main__':main()
