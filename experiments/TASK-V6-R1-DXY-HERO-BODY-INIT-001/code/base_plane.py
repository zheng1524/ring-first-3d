"""009 RANSAC reused; direction from camera-facing support, with independent protrusion/contact checks."""
from observations import *
from scipy.spatial import cKDTree
definitions('84a747a19f7b230a1236d8f7d525c1127cffac15','experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_INIT_009/code/base_observations.py',['fit_plane'],globals())
def estimate(sources):
 samples=[s for s in sources if len(s['bg_X'])>=50 and len(s['raw_X'])]
 if not samples:return dict(status='UNOBSERVABLE',plane=None,apply=False,reason='No local background depth evidence',scope='polyp_bias_does_not_move_background')
 P=np.concatenate([s['bg_X']for s in samples]);dist=np.concatenate([s['bg_distance_px']for s in samples]);X=np.concatenate([s['raw_X']for s in samples]);center=np.median(X,axis=0);trials=[]
 # Each physical target counted once for evidence stability, not each ROI or repeated support tuple.
 individual=[]
 for s in samples:
  plane,ids,fraction=fit_plane(s['bg_X'],center)
  if plane is not None:individual.append(dict(source_id=s['meta']['source_id'],case=s['meta']['case'],reference=s['meta']['reference'],plane=plane,inlier_fraction=fraction,N=len(s['bg_X'])))
 for upper in CFG['base_roi_px']:
  Q=P[dist<=upper];pl,ids,frac=fit_plane(Q,center);trials.append(dict(upper_px=upper,N=len(Q),plane=pl,inlier_fraction=frac))
 pl=trials[1]['plane']
 if pl is None:return dict(status='UNOBSERVABLE',plane=None,apply=False,trials=trials,individual=individual)
 # Signed direction uses observing cameras relative to background; NOT the nearly-zero polyp median.
 cam=np.array([s['C'][:3,3]for s in samples]);side=cam@pl[:3]+pl[3]
 if np.median(side)<0:pl=-pl;side=-side
 heights=X@pl[:3]+pl[3];normalchecks=[compare(r['plane'],pl,center)[1:]for r in trials+individual if r['plane']is not None];angles=[r[0]for r in normalchecks];offsets=[r[1]for r in normalchecks]
 # Proximity of actual foreground to this background is only a contact diagnostic.
 near=cKDTree(P).query(X)[0];contact=(abs(heights)<=.5)&(near<=1.)
 direction_ok=float(np.mean(side>1.))>=.8 and np.percentile(heights,80)>.25
 stable=max(angles,default=180)<=CFG['base_normal_stability_deg']and max(offsets,default=99)<=CFG['base_offset_stability_mm']
 fractions=all(r['N']>=100 and r['inlier_fraction']>=.5 for r in trials)
 independent=len({(s['meta']['case'],s['meta']['reference'])for s in samples})
 reliable=direction_ok and stable and fractions and independent>=2 and contact.sum()>=10
 return dict(status='RELIABLE'if reliable else'WEAK',plane=pl,apply=bool(reliable),candidate=bool(direction_ok),scope='local_background_native_depth_unmodified_shared_HERO_bias_possible',keep_side='n dot X + d >= 0',direction_rule='majority observing camera side of local background; separate positive protrusion check',direction_supported=bool(direction_ok),camera_positive_fraction=float(np.mean(side>1)),protrusion_p80_mm=float(np.percentile(heights,80)),trials=trials,individual=individual,unique_targets=independent,max_sign_invariant_normal_deg=max(angles,default=None),max_anchor_offset_mm=max(offsets,default=None),contact_N=int(contact.sum()),contact_denominator=len(X),original_trusted_removed_side_N=int((heights<0).sum()),original_trusted_removed_side_fraction=float((heights<0).mean()),negative_distance_p95_mm=float(np.percentile(-heights[heights<0],95))if(heights<0).any()else 0.,source_ids=[s['meta']['source_id']for s in samples],background_N=len(P),shared_with_HERO=True)
