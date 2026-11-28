"""All-video M4 orchestration; one group track domain, fixed-camera edges."""
from context import *
from connections import pair_view,connect
from real2 import make_tracks,triangulate,ring_prior
from solver2 import solve_methods
from metrics2 import bidirectional,ring_pixels,summarize
import shutil,itertools,traceback,argparse

def matches(g,asset,out):
 key=cache_key(dict(files=asset['files'],frames=CFG['frames_per_video'],features=CFG['features'],ratio=CFG['ratio'],kernel=sha(V6/'track005.py')))
 receipt=out/'MATCH_CACHE.json'
 if receipt.exists():
  r=read(receipt);assert r['key']==key,'MATCH_CACHE_MISMATCH';verify(r['files']);return
 old=prior_run()/g;can_reuse=g in CFG['regression_groups']and len(asset['videos'])==2
 if can_reuse:
  oldasset=read(ROOT/'experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/config'/g/'ASSETS.json');verify(oldasset['files'])
  for a,b in zip(asset['videos'],oldasset['videos']):assert a['case']==b['case']and a['pool']==b['pool']and a['camera_sha256']==sha(b['camera'])
  for name in ['FRAMES.json','CAMERAS.npz','TRACK_FROZEN.json','tracks/observations/tracks005.npz','tracks/BA_DEPENDENCIES.npz']:
   dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/name,dst)
  frames=read(out/'FRAMES.json')
  # Legacy pair frame labels remain A/B for exact replay; case is authoritative.
  origin='VERIFIED_SIX_GROUP_TRACK_CACHE'
 else:
  import real2
  oldrun=real2.RUN;real2.RUN=RUN/'matching'
  try:make_tracks(g)
  finally:real2.RUN=oldrun
  temp=RUN/'matching/real'/g
  for name in ['FRAMES.json','CAMERAS.npz','TRACK_FROZEN.json','tracks']:
   shutil.move(str(temp/name),str(out/name))
  origin='NEW_SHARED_ALL_VIDEO_TRACKS'
 files=[dict(path=str(out/n),sha256=sha(out/n))for n in ['FRAMES.json','CAMERAS.npz','tracks/observations/tracks005.npz','tracks/BA_DEPENDENCIES.npz']]
 save(receipt,dict(key=key,origin=origin,files=files,held_rule='original full connected track mod5; shared across all video edges'))

def pair_asset(asset,a,b):
 return dict(asset,videos=[dict(next(v for v in asset['videos']if v['case']==case),side=side)for case,side in [(a,'A'),(b,'B')]])

def solve_edge(g,asset,out,frames,C,tr,a,b):
 folder=out/'edges'/(a.rsplit('_',1)[-1]+'__'+b.rsplit('_',1)[-1]);folder.mkdir(parents=True,exist_ok=True)
 ff,cc,tt=pair_view(frames,C,tr,a,b);key=cache_key(dict(match=sha(out/'MATCH_CACHE.json'),a=a,b=b,solver=sha(OLD/'code/solver2.py'),real=sha(OLD/'code/real2.py'),decision=sha(T/'config/DECISION.json'),cfg=CFG))
 if (folder/'EDGE.json').exists():
  r=read(folder/'EDGE.json');assert r['cache_key']==key;verify(r['files']);return r
 freeze('SOLVE_M4',folder,[out/'MATCH_CACHE.json',T/'config/DECISION.json'])
 # Reusing old triangulation/prior is safe only for the identical pair/domain.
 if g in CFG['regression_groups']and len(asset['videos'])==2:
  old=prior_run()/g;lm=np.load(old/'LANDMARKS.npz');xyz,fit=lm['xyz'],lm['fit'];details=read(old/'TRIANGULATION.json');ring=read(old/'RING_PRIOR.json');origin='VERIFIED_FROZEN_DLT_RING'
 else:xyz,fit,details=triangulate(ff,cc,tt);ring=ring_prior(pair_asset(asset,a,b),ff,cc);origin='NEW_DLT_RING'
 results=solve_methods(xyz[fit,0],xyz[fit,1],ring,methods=['M4']);np.savez_compressed(folder/'LANDMARKS.npz',xyz=xyz,fit=fit,held=tt['held'],category=tt['category']);save(folder/'TRIANGULATION.json',details);save(folder/'RING_PRIOR.json',ring);save(folder/'PREDICTIONS.json',results)
 rec=dict(parent=a,child=b,cache_key=key,landmark_origin=origin,FIT_tracks=int(fit.sum()),FIT_track_ids=np.flatnonzero(fit),results=results,files=[dict(path=str(folder/n),sha256=sha(folder/n))for n in ['LANDMARKS.npz','TRIANGULATION.json','RING_PRIOR.json','PREDICTIONS.json']],folder=str(folder))
 save(folder/'EDGE.json',rec);print('EDGE',g,a.rsplit('_',1)[-1],b.rsplit('_',1)[-1],int(fit.sum()),results['M4']['quality'],flush=True);return rec

def predict(g):
 out=group_out(g);asset=read(out/'ASSETS.json');verify(asset['files']);videos=[v['case']for v in asset['videos']];ref=asset['reference'];decision=read(T/'config/DECISION.json');assert decision['method']=='M4_ORIGINAL'
 if not videos:save(out/'REGISTRATION.json',dict(reference=None,videos={},edges=[],status='NO_OUTPUT'));return
 if len(videos)==1:save(out/'REGISTRATION.json',dict(reference=ref,videos=connect(videos,ref,{}),edges=[],status='SINGLE_VIDEO_ONLY'));return
 matches(g,asset,out);frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=dict(np.load(out/'tracks/observations/tracks005.npz'));edges={};records=[]
 # Attempt direct reference edges first. Fallback uses a connected video, never held scores.
 for a,b in [(ref,v)for v in videos if v!=ref]+[(a,b)for a,b in itertools.combinations(videos,2)if ref not in [a,b]]:
  connected=connect(videos,ref,edges)
  if a!=ref:
   if (connected[a]['T']is None)==(connected[b]['T']is None):continue
   if connected[a]['T']is None:a,b=b,a
  rec=solve_edge(g,asset,out,frames,C,tr,a,b);records.append(rec)
  if rec['results']['M4']['T']is not None:edges[(a,b)]=np.array(rec['results']['M4']['T'])
 result=connect(videos,ref,edges);used=set(int(i)for r in records for i in r['FIT_track_ids']);assert not np.any(tr['held'][list(used)])
 status='CONNECTED'if all(r['T']is not None for r in result.values())else'PARTIAL_UNCONNECTED'
 save(out/'REGISTRATION.json',dict(reference=ref,videos=result,edges=records,status=status,method='M4_ORIGINAL',decision_sha256=sha(T/'config/DECISION.json'),used_FIT_global_track_ids=sorted(used),global_held_track_ids=np.flatnonzero(tr['held']),no_cross_edge_held_reuse_as_fit=True))
 save(out/'TRANSFORM_FREEZE.json',dict(registration_sha256=sha(out/'REGISTRATION.json'),inputs=[dict(path=str(out/n),sha256=sha(out/n))for n in ['ASSETS.json','MATCH_CACHE.json']],decision_sha256=sha(T/'config/DECISION.json')))

def evaluate_edges(g):
 out=group_out(g);asset=read(out/'ASSETS.json');reg=read(out/'REGISTRATION.json');rows=[]
 if not reg['edges']:save(out/'EDGE_EVALUATION.json',[]);return
 frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=dict(np.load(out/'tracks/observations/tracks005.npz'))
 for r in reg['edges']:
  a,b=r['parent'],r['child'];folder=Path(r['folder']);ff,cc,tt=pair_view(frames,C,tr,a,b);lm=np.load(folder/'LANDMARKS.npz');metrics={};allrows={}
  for m,pred in r['results'].items():
   t=np.array(pred['T'])if pred['T']is not None else None;bi,obs=bidirectional(ff,cc,tt,lm['xyz'],t);rp,_=ring_pixels(pair_asset(asset,a,b),ff,cc,t)
   for d in ['A_to_B','B_to_A']:
    vals=np.array([x['error_px']for x in obs if x['direction']==d]);finite=vals[np.isfinite(vals)];bi[d]['conditional_median']=float(np.median(finite))if len(finite)else None;bi[d]['all_fraction_le6']=float((vals<=6).mean())if len(vals)else None
   metrics[m]=dict(bidir=bi,ring=rp);allrows[m]=obs;save(folder/(m+'_HELD.json'),obs)
  common={}
  for d in ['A_to_B','B_to_A']:
   domains=[{(x['track'],x['frame'])for x in obs if x['direction']==d and np.isfinite(x['error_px'])}for obs in allrows.values()];ids=set.intersection(*domains)
   common[d]=dict(ids=sorted(ids),methods={m:summarize([x['error_px']for x in obs if x['direction']==d and (x['track'],x['frame'])in ids])for m,obs in allrows.items()})
  row=dict(parent=a,child=b,FIT_tracks=r['FIT_tracks'],methods=metrics,common_finite=common);rows.append(row)
 save(out/'EDGE_EVALUATION.json',rows)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--group');args=parser.parse_args()
 for row in read(T/'config/INVENTORY.json')['groups']:
  g=row['group']
  if args.group and args.group!=g:continue
  try:predict(g);evaluate_edges(g);print('REGISTERED',g,read(group_out(g)/'REGISTRATION.json')['status'],flush=True)
  except Exception as e:save(group_out(g)/'REGISTRATION_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('FAILURE',g,repr(e),flush=True)
