"""Optimizer-equivalent bounded fixed-denominator evaluation, never used for selection."""
from common import *
from evaluate import pointcast

def cost(r):return np.minimum(2*(np.sqrt(1+r*r)-1),19.)
def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN.json').exists();rows=[]
 for c in load(R/'config/CASE_LOCK.json'):
  name=c['name'];rr=np.load(R/'inputs'/name/'RING.npz');rs=scene(rr['V'],rr['F'])
  for arm in['A','B','C']:
   p=R/'inputs'/name/'INITIAL.npz'if arm=='A'else R/'local_results'/name/(arm+'_SELECTED.npz');m=np.load(p);rt=scene(m['V'],m['F'])
   for v in c['views']:
    op=R/'depth_observations'/(v['id']+'.npz')
    if not op.exists():continue
    o=np.load(op);ray=np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T;X=(ray*o['z'][:,None])@o['T'][:3,:3].T+o['T'][:3,3];_,_,z=pointcast(rt,X,o['K'],o['T']);_,_,rz=pointcast(rs,X,o['K'],o['T']);hit=np.isfinite(z)&(z>0)&(z<rz-.05);err=np.where(hit,z-o['z'],0.);absolute=np.where(hit,cost(err/.5),19.);pair=o['pairs'];good=hit[pair].all(1);delta=(np.where(hit,z,0)[pair[:,0]]-np.where(hit,z,0)[pair[:,1]])-(o['z'][pair[:,0]]-o['z'][pair[:,1]]);relative=np.where(good,cost(delta/.5),19.);rows.append(dict(case=name,arm=arm,source=v['id'],role=v['role'],fixed_ray_N=len(hit),hit_N=int(hit.sum()),fixed_pair_N=len(pair),pair_hit_N=int(good.sum()),fixed_bounded_absolute_cost=float(absolute.mean())if len(hit)else None,fixed_bounded_relative_cost=float(relative.mean())if len(pair)else None,abs_HERO_conditional_mm=stats(err[hit]),relative_HERO_conditional_mm=stats(delta[good]),GT_accuracy='NOT_EVALUABLE',missing_cost_equals_max_hit_cost=19.))
 table('metrics/FIXED_DENOMINATOR_DEPTH.csv',rows);save('metrics/FIXED_DENOMINATOR_DEPTH.json',rows);save('metrics/DEPTH_SCORE_AUDIT.json',dict(current='same bounded soft_l1(error/.5mm), maximum/missing19, fixed original denominator; no losing high-error hit can lower its own bounded cost',legacy_field='fixed_censored_relative_mm and diagnose.fixed_denominator_relative_score use inherited 2.5mm miss proxy, not bounded against arbitrary hit errors; preserve but do not rank or claim improvement from that field',candidate_selection_did_not_use_legacy_field=True,optimizer_unchanged=True,real_GT_read=False))
if __name__=='__main__':main()
