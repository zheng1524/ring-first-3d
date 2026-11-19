from refine import *
from conics_init import candidates,mid_for
import argparse

def run(group):
 assert load(M/'STAGE1_GATE.json')['pass_basic_correctness'];guard_fit();views=[v for v in load(M/'config/VIEWS.json')if v['group']==group];ct=[]
 for v in views:
  cid=v['id'];C0=np.array(v['T']);save('results/'+group+'/P0/'+cid+'/FINAL.json',dict(status='FROZEN_ORIGINAL_REFERENCE',pose=C0,not_a_new_prediction=True))
  if v['role']=='HOLDOUT':
   for arm in ['S0','A1','A2','A3']:save('results/'+group+'/'+arm+'/'+cid+'/FINAL.json',dict(status='PROTECTED_NO_LOCAL_FIT',pose=C0,heldout_local_pose_not_refined=True))
   continue
  sift=Problem([v],False);rho=np.linalg.norm(sift.cads[v['ring_path']].V[:,:2],axis=1);radius=(rho.min()+rho.max())/2;e,src=mid_for(v);cand=[];failure=None
  try:cs=candidates(e,np.array(v['K']),radius,C0)if e else[]
  except Exception as ex:cs=[];failure=repr(ex)
  for c in cs:
   q=q_from_pose(np.array(c['C']),C0);physical,why=sift.physical(q);valid=bool(physical and np.isfinite(q).all()and abs(q).max()<2);c.update(q=q,within_frozen_P0_physical_bounds=valid,physical_detail=why,fit_SIFT_prior_objective=sift.true_cost(q)if valid else None);cand.append(c)
  valid=[c for c in cand if c['within_frozen_P0_physical_bounds']];best=min(valid,key=lambda c:c['fit_SIFT_prior_objective'])if valid else None;save('initialization/'+group+'/'+cid+'.json',dict(id=cid,Mid_source=src,candidates=cand,selected=best,reason=failure or('NO_MID_OR_NO_PHYSICAL_CONICS_SEED'if best is None else'FIT_SIFT_PRIOR_ONLY'),no_held_body_HERO_selection=True))
  for arm in ['S0','A1','A2','A3']:
   label=group+'/'+arm+'/'+cid
   if(M/'results'/label/'FINAL.json').exists():r=load(M/'results'/label/'FINAL.json')
   elif arm in ['A1','A3']and best is None:
    r=dict(label=label,status='NO_FEASIBLE_CONICS_INITIALIZATION',pose=None,reason=failure or'NO_MID_OR_SEED_OUTSIDE_UNCHANGED_P0_PHYSICAL_BOUNDS',no_prediction_fallback=True);save('results/'+label+'/FINAL.json',r)
   else:r=solve(Problem([v],arm in ['A2','A3']),label,qstart=best['q']if arm in ['A1','A3']else None,extra=dict(Mid_init_only=arm in ['A1','A3'],same_prior_P0=True))
   ct.append(dict(group=group,id=cid,method=arm,status=r['status'],movement_mm=r.get('center_change_mm'),rotation_deg=r.get('rotation_change_deg'),loss_before=r.get('initial_loss'),loss_after=r.get('final_loss')))
  print('VIDEO_REFINED',group,cid,'Conics admissible',len(valid),flush=True)
 save('metrics/'+group+'_ACTUAL_VIDEO_RUNS.json',ct);table('metrics/'+group+'_ACTUAL_VIDEO_RUNS.csv',ct);save('provenance/'+group+'_VIDEO_POSES_FROZEN.json',dict(epoch=time.time(),files=[asset(p)for p in(M/'results'/group).rglob('FINAL.json')],no_HOLDOUT_HERO_body_used=True,source=asset(Path(__file__))));print('GROUP_VIDEO_FROZEN',group,len(ct),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('group',choices=GROUPS);run(a.parse_args().group)
