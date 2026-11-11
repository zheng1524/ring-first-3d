"""Independent source/identity checks on the frozen FIT landmark arrays."""
from common import *
def main():
 vv={v['id']:v for v in load(R/'config/VIEWS.json')};rows=[]
 for name,video in [('CROSS_004','004'),('INDEPENDENT_005','005')]:
  X=np.load(R/'landmarks'/(name+'.npz'))['X'];obs=load(R/'landmarks'/(name+'_OBSERVATIONS.json'));err=[];n=0
  for x,t in zip(X,obs):
   assert len(t['observations'])>=3
   for o in t['observations']:
    v=vv[o['view']];assert v['video']==video and v['role']=='FIT';a=np.load(R/'features'/(o['view']+'.npz'));assert np.allclose(a['xy'][o['feature_id']],o['uv'],atol=1e-6);C=np.asarray(v['T']);p=(x-C[:3,3])@C[:3,:3];assert p[2]>0;q=p@np.asarray(v['K']).T;q=q[:2]/q[2];err.append(np.linalg.norm(q-o['uv']));n+=1
  assert max(err)<2.;rows.append(dict(video=video,landmarks=len(X),actual_observations=n,recomputed_own_native_camera_reprojection_px=stats(err),only_own_video_FIT=True,no_intervideo_T_used=True))
 pairs=load(R/'features/CROSS_NAMED_3D_TRACK_PAIRS.json')['matches'];evidence_N=0
 for p in pairs:
  for o in p['evidence']:
   a=np.load(R/'matches'/(o['a']+'__'+o['b']+'.npz'));k=o['match_index'];assert a['RGB_RANSAC'][k];assert np.array_equal(a['index_pairs'][k],[o['a_feature'],o['b_feature']]);assert np.allclose(a['p'][k],o['p'])and np.allclose(a['q'][k],o['q']);evidence_N+=1
 save('metrics/LANDMARK_PROVENANCE_VERIFICATION.json',dict(rows=rows,named_pairs=len(pairs),actual_cross_image_feature_ID_links=evidence_N,all_verified=True,body=False,HERO=False,HOLDOUT=False,GT=False));print('LANDMARK_NATIVE_CAMERA_AND_ID_CHECKS_PASSED',rows,evidence_N,flush=True)
if __name__=='__main__':main()
