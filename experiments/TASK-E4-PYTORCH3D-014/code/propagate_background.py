"""One fixed within-video background-only propagation pass, no threshold tuning."""
from expand_cameras import *
def main():
 views=load(R/'config/DERIVED_VIEWS.json');old=load(R/'config/EXISTING_VIEWS.json');raw=load(R/'config/NEW_RAW_VIEWS.json');runs=[]
 for sid in sorted(set(v['sid']for v in raw)):
  have=[v for v in views if v['sid']==sid];todo=[v for v in raw if v['sid']==sid and v['id']not in set(x['id']for x in have)]
  if not todo:continue
  anchors=[v for v in old if v['sid']==sid]+have
  if len(anchors)<2:runs.append(dict(sid=sid,available_BG_pose_anchors=len(anchors),success=0,reason='NO_TWO_METRIC_BG_POSES; Ring yaw remains unobservable without correspondence'));continue
  # Deterministic temporal spread, at most sixteen anchors per video.
  anchors=anchors[::max(1,len(anchors)//16)][:16];lm,pairs=landmarks(anchors);K=np.array(anchors[0]['K']);N=0
  for v in todo:
   T,rec=pnp(v,lm,K)
   if T is None:continue
   out=dict(v,RGB_sha=v['RGB_SHA256'],Mask_sha=v['Mask_SHA256'],K=K,T=T,available_camera=True,original013=False,HERO_sources=[],aliases=[v['id']],qualification=rec['qualification'],pose_source='ONE_PASS_SAME_VIDEO_BG_TRIANGULATION_PNP',admission='INPUT_INTEGRITY_ONLY',is_photo=False)
   np.savez_compressed(R/'inputs'/v['case']/(v['id']+'.npz'),RGB=np.array(Image.open(v['RGB_path']).convert('RGB')),labels=np.array(Image.open(v['Mask_path'])),K=K,T=T);views.append(out);N+=1;save('new_views/'+sid+'/predictions/'+v['id']+'_PROPAGATED.json',rec)
  runs.append(dict(sid=sid,available_BG_pose_anchors=len(anchors),BG_landmarks=len(lm['X']),attempted=len(todo),success=N));print('PROPAGATE',sid,N,len(todo),flush=True)
 save('config/DERIVED_VIEWS.json',views);save('metrics/BACKGROUND_PROPAGATION.json',runs);save('provenance/BACKGROUND_PROPAGATION_FREEZE.json',dict(epoch=time.time(),code=asset(Path(__file__)),views=asset(R/'config/DERIVED_VIEWS.json'),one_pass=True,GT_used=False))
if __name__=='__main__':main()
