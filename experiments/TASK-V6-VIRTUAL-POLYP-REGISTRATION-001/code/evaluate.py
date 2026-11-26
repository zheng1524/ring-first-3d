"""Postfreeze evaluator only. One shared 004/GT gauge, no alignment or filtering."""
import csv
import numpy as np
from common import *
from ring_first_3d.sim.geometry import transform,scene,closest,pose_error
from ring_first_3d.multisurface.geometry import sample_mesh
from ring_first_3d.contracts.coordinates import project

def stats(values):
 a=np.asarray(values,float);n=len(a);finite=np.isfinite(a)
 # Preserve the full denominator: nonfinite values count as infinite errors.
 a=np.where(finite,a,np.inf)
 return dict(N=n,missing=int((~finite).sum()),median_mm=float(np.median(a))if n else None,p95_mm=float(np.sort(a)[min(n-1,int(np.ceil(.95*n))-1)])if n else None,mean_mm=float(np.mean(a))if n else None,coverage_fraction=float((a<=CFG['coverage_mm']).sum()/n)if n else 0.)

def mesh_for(video,frames,poses,T0):
 vs=[];fs=[];offset=0
 for r in frames:
  if r['role']!='FIT' or r['video']!=video:continue
  a=np.load(RUN/'public/meshes'/(r['id']+'.npz'));V=transform(a['V'],T0@poses[r['id']]);vs.append(V);fs.append(a['F']+offset);offset+=len(V)
 return np.concatenate(vs),np.concatenate(fs)

def safe_project(P,K,C):
 pc=(P-C[:3,3])@C[:3,:3];q=pc@K.T;uv=q[:,:2]/q[:,2:];uv[pc[:,2]<=0]=np.inf;return uv

def evaluate(condition):
 folder=RUN/'predictions'/condition;fr=read(folder/'FREEZE.json')
 assert sha(RUN/'GENERATION_FREEZE.json')==fr['public_input_freeze']
 for name in ['registration.py','common.py','v6_adapter.py']:
  assert sha(T/'code'/name)==fr['sources']['code/'+name],('PREDICTOR_SOURCE_DRIFT',name)
 for asset in read(T/'evidence/ASSET_IDENTITIES.json'):
  assert sha(T/'inputs'/Path(asset['source']).name)==asset['sha256']
 assert read(RUN/'tracks/ADAPTER.json')['frames']==[r for r in read(RUN/'public/FRAMES.json')if r['role']=='FIT']
 check_freeze(fr['predictions']);check_freeze(read(RUN/'GENERATION_FREEZE.json')['public']);assert sha(RUN/'tracks/observations/tracks005.npz')==fr['tracks_sha256'];assert sha(T/'config.json')==fr['config_sha256'];check_freeze(read(RUN/'GENERATION_FREEZE.json')['private'])
 truth=read(RUN/'private/TRUTH.json');frames=read(RUN/'public/FRAMES.json');obs=read(RUN/'public/conditions'/(condition+'.json'));poses={r['id']:np.array(r['C'])for r in obs['frames']};target=np.load(RUN/'private/GT_TARGETS.npz');P=target['P'];union=target['visible004']|target['visible005'];overlap=target['visible004']&target['visible005'];gt=np.load(T/'inputs/virtual_GT.npz');gs=scene(gt['V'],gt['F']);lm=np.load(folder/'LANDMARKS.npz');tr=np.load(RUN/'tracks/observations/tracks005.npz');fitframes=read(RUN/'tracks/ADAPTER.json')['frames'];D=np.array(truth['injections'][condition][next(r['id']for r in frames if r['video']=='005')]['D']);outputs=[]
 for method in ['M0','M1','M2']:
  record=read(folder/(method+'.json'));t=record['T_005']
  if t is None:
   outputs.append(dict(condition=condition,method=method,status=record['solver']['status'],rotation_deg=None,translation_mm=None,coverage_fraction=0.,surface_N=int(union.sum()),surface_missing=int(union.sum())));continue
  t=np.array(t);error=pose_error(t@D);cams={r['id']:(np.eye(4)if r['video']=='004'else t)@poses[r['id']]for r in frames};surfaces={};closestpoints={};single={};back={}
  for v in ['004','005']:
   V,F=mesh_for(v,frames,poses,np.eye(4) if v=='004'else t);surfaces[v]=(V,F);ms=scene(V,F);Q,_,_=closest(ms,P);closestpoints[v]=Q;domain=target['visible'+v];single[v]=stats(np.linalg.norm(Q[domain]-P[domain],axis=1));sample,_,_=sample_mesh(V,F,12000,CFG['GT_seed']);G,_,_=closest(gs,sample);back[v]=stats(np.linalg.norm(G-sample,axis=1))
  d=np.minimum(np.linalg.norm(closestpoints['004']-P,axis=1),np.linalg.norm(closestpoints['005']-P,axis=1));joint=stats(d[union]);ov=stats(np.linalg.norm(closestpoints['004'][overlap]-closestpoints['005'][overlap],axis=1))
  repro=[];holdrecords=[];hold_errors={v:[]for v in ["004","005"]}
  for r in frames:
   if r['role']=='FIT':continue
   cid=r['id'];q=P[target[cid]];Ctrue=np.array(truth['frames'][cid]['C']);K=np.array(r['K']);uv=safe_project(q,K,Ctrue);pred=safe_project(q,K,cams[cid]);e=np.linalg.norm(pred-uv,axis=1);repro.extend(e);hold_errors[r["video"]].extend(e);holdrecords.append(dict(id=cid,video=r['video'],N=len(e),MAE_px=float(e.mean()),p95_px=float(np.quantile(e,.95))))
  # Automatic modulo-5 tracks: never used in the solve; evaluate all eligible held tracks.
  auto=[];auto3=[]
  for i in np.flatnonzero(lm['held']):
   tid=lm['track_ids'][i];A,B=lm['points'][i];Q=transform(B[None],t)[0];auto3.append(np.linalg.norm(Q-A))
   for j,r in enumerate(fitframes):
    if r['video']=='004' and np.isfinite(tr['xy'][tid,j]).all():auto.append(np.linalg.norm(safe_project(Q[None],np.array(r['K']),cams[r['id']])[0]-tr['xy'][tid,j]))
  auto=np.array(auto);repro=np.array(repro)
  out=dict(condition=condition,method=method,status=record['solver']['status'],**error,train_tracks=record['train_tracks'],held_tracks=record['held_tracks'],surface_N=joint['N'],surface_missing=joint['missing'],surface_uncovered_at_02mm=int((d[union]>CFG['coverage_mm']).sum()),surface_median_mm=joint['median_mm'],surface_p95_mm=joint['p95_mm'],coverage_fraction=joint['coverage_fraction'],overlap_N=ov['N'],overlap_median_mm=ov['median_mm'],overlap_p95_mm=ov['p95_mm'],held_view_N=len(repro),held_view_MAE_px=float(np.mean(repro)),held_view_p95_px=float(np.quantile(repro,.95)),auto_held_N=len(auto),auto_held_MAE_px=float(auto.mean())if len(auto)else None,auto_held_p95_px=float(np.quantile(auto,.95))if len(auto)else None,single_video=single,prediction_to_GT=back,automatic_held_3D=stats(auto3),hold_views=holdrecords,pose_pass=error['rotation_deg']<=CFG['accept_rotation_deg'] and error['translation_mm']<=CFG['accept_translation_mm'])
  for video in ['004','005']:
   out['held_'+video+'_p95_px']=float(np.quantile(hold_errors[video],.95))
   h=[x for x in holdrecords if x['video']==video];out['held_'+video+'_N']=sum(x['N']for x in h);out['held_'+video+'_MAE_px']=sum(x['N']*x['MAE_px']for x in h)/out['held_'+video+'_N']
  # Preserve the entire 83 held RGB track denominator, including unavailable/failed triangulations.
  out['auto_held_total_tracks']=int(tr['held'].sum());out['auto_held_unavailable_or_rejected_tracks']=int(tr['held'].sum()-lm['held'].sum());out['auto_held_evaluable_fraction']=float(lm['held'].sum()/max(tr['held'].sum(),1))
  save(folder/(method+'_REGISTERED.json'),dict(cameras=cams,transforms={'004':np.eye(4),'005':t},mesh_contract='All per-view camera meshes use C_global=T_video@C_local. Vertices X_global=C_global@V_camera. No scaling or deformation.',frames=[dict(id=r['id'],mesh=str(RUN/'public/meshes'/(r['id']+'.npz')),camera=cams[r['id']])for r in frames]));outputs.append(out)
 save(folder/'EVALUATION.json',outputs);return outputs

def aggregate():
 rows=[]
 for c in cases():
  p=RUN/'predictions'/c/'EVALUATION.json'
  if p.exists():rows+=read(p)
 base={r['method']:r for r in rows if r['condition']=='V0'}
 for r in rows:
  if 'single_video' not in r:continue
  b=base['M0'];before=next(x for x in rows if x['condition']==r['condition'] and x['method']=='M0');r['single005_p95_change_vs_M0_mm']=r['single_video']['005']['p95_mm']-before['single_video']['005']['p95_mm'];r['single005_p95_mm']=r['single_video']['005']['p95_mm'];r['single004_p95_mm']=r['single_video']['004']['p95_mm'];r['added005_p95_vs_clean_mm']=r['single005_p95_mm']-b['single_video']['005']['p95_mm'];r['added_joint_p95_vs_clean_mm']=r['surface_p95_mm']-b['surface_p95_mm'];r['coverage_delta_vs_clean']=r['coverage_fraction']-b['coverage_fraction']
 save(T/'evidence/RESULTS.json',rows)
 keys=list(dict.fromkeys(k for r in rows for k,v in r.items()if not isinstance(v,(dict,list))))
 with (T/'evidence/RESULTS.csv').open('w')as f:
  writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows([{k:v for k,v in r.items()if not isinstance(v,(dict,list))}for r in rows])
if __name__=='__main__':
 import sys
 for c in sys.argv[1:] or cases():
  for r in evaluate(c):print(c,r['method'],r.get('rotation_deg'),r.get('translation_mm'),r.get('surface_p95_mm'),flush=True)
 aggregate()
