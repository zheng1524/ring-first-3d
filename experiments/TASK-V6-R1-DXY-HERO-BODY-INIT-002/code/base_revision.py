"""Retain 009/001 estimates, downgrade multi-source distance conflicts before fitting."""
from common import *
import base_plane as legacy_base
from observations import CFG

def estimate(sources):
 result=legacy_base.estimate(sources)
 if result.get('plane') is None:return result
 plane=np.asarray(result['plane']);by=[]
 for s in sources:
  X=s['raw_X'];h=X@plane[:3]+plane[3];negative=np.maximum(-h,0)
  score=float(np.minimum(negative/CFG['base_conflict_soft_scale_mm'],1).mean())if len(X)else 0.
  by.append(dict(source_id=s['meta']['source_id'],case=s['meta']['case'],reference=s['meta']['reference'],N=len(X),cut_N=int((h<0).sum()),far_cut_N=int((negative>CFG['base_conflict_soft_scale_mm']).sum()),distance_weighted_fraction=score,p95_negative_mm=float(np.percentile(negative[negative>0],95))if(negative>0).any()else 0.))
 # Equal source mass: a dense source cannot dominate the decision. Independent
 # targets, not repeated ROI fits, supply the agreement/disagreement evidence.
 scores=np.array([x['distance_weighted_fraction']for x in by]);score=float(scores.mean())if len(scores)else 0.
 unique={}
 for r in by:unique.setdefault((r['case'],r['reference']),[]).append(r['distance_weighted_fraction'])
 conflict_fraction=float(np.mean([max(v)>CFG['base_conflict_score_limit']for v in unique.values()]))if unique else 0.
 conflict=score>CFG['base_conflict_score_limit']and conflict_fraction>=CFG['base_conflict_source_fraction']
 result.update(original_001_status=result['status'],conflict_policy='joint distance-and-source-consistency diagnostic; never delete cut-side points',cut_side_sources=by,distance_weighted_cut_fraction=score,conflicted_target_fraction=conflict_fraction,conflict_strength=float(np.exp(-score/CFG['base_conflict_score_limit'])))
 if conflict:
  result.update(status='WEAK',apply=False,candidate=bool(result.get('direction_supported')),reason='Foreground distance and multi-target cut-side evidence contradict hard support; retain reversible candidate only',downgraded_for_conflict=True)
 else:result['downgraded_for_conflict']=False
 return result
