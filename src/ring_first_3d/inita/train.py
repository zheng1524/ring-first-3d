"""Exact 013 inputs → inherited 015 vertex updates, fixed final checkpoint."""
import json,os,sys,subprocess,shutil,time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
from ..policy.contracts import ROOT,require
from ..contracts.identities import sha256
from ..synthetic.io import fetch,save_json,outputs
from ..stress.real import safe_project
from ..multisurface.geometry import scene,transform,cast

def sources(task):return json.loads(Path(task['inita']['assets']['sources']['path']).read_text())
def prior_stage(root,stage,name):
 try:return fetch(root,stage,name)
 except (KeyError,ValueError,OSError):return None

def copy_tree(source,dest):
 dest.mkdir(parents=True,exist_ok=True)
 for p in source.rglob('*'):
  q=dest/p.relative_to(source)
  if p.is_dir():q.mkdir(exist_ok=True)
  elif p.is_symlink():q.symlink_to(p.resolve())
  else:shutil.copyfile(p,q)

def prepare_arm(task,row,arm,out,D=None):
 out.mkdir(parents=True);g=row['case'];inp=out/'inputs'/g;inp.mkdir(parents=True)
 for key,r in row['static'].items():
  if key=='INITIAL.npz':shutil.copyfile(r['path'],inp/key)
  else:(inp/key).symlink_to(r['path'])
 views=[]
 for v in row['FIT']+row['HOLDOUT']:
  meta=dict(v['meta']);cid=meta['id'];fit=v in row['FIT'];train=fit and(arm!='A1'or meta['video']=='004');meta['role']='FIT'if train else'UPDATE_HOLDOUT'if not fit else'CROSS_VIDEO_UNTRAINED_FIT';views.append(meta)
  if D is not None and meta['video']=='005':
   a=dict(np.load(v['cache']['path']));a['T']=D@a['T'];np.savez_compressed(inp/(cid+'.npz'),**a)
  else:(inp/(cid+'.npz')).symlink_to(v['cache']['path'])
  (inp/(cid+'_SIDES.npz')).symlink_to(v['sides']['path'])
 meta=dict(row['meta'],views=views);save_json(inp/'CASE.json',meta);dep=out/'depth_observations';dep.mkdir()
 for cid,r in row['depth'].items():
  meta=next(v for v in views if v['id']==cid)
  if D is not None and meta['video']=='005':
   a=dict(np.load(r['path']));a['T']=D@a['T'];np.savez_compressed(dep/(cid+'.npz'),**a)
  else:(dep/(cid+'.npz')).symlink_to(r['path'])
 save_json(out/'config/PROTOCOL.json',dict(depth=sources(task)['inherited_depth']));save_json(out/'config/ARM.json',dict(tag=arm,loss='D0_013',budget=task['inita']['training_budget']))
 return out

def projection_rows(mesh,row,D=None):
 rt=scene(mesh['V'],mesh['F']);rg=np.load(row['static']['RING.npz']['path']);rs=scene(rg['V'],rg['F']);per=[]
 for v in row['FIT']+row['HOLDOUT']:
  a=np.load(v['cache']['path']);C=a['T'];C=D@C if D is not None and v['meta']['video']=='005'else C;H,W=a['labels'].shape;y,x=np.mgrid[:H,:W];uv=np.c_[x.ravel(),y.ravel()];z,_,_=cast(rt,uv,a['K'],C);rz,_,_=cast(rs,uv,a['K'],C);pred=np.isfinite(z)&(z>0)&(z<rz);label=a['labels'].ravel();target=label==1;known=label!=2;tp=int((pred&target).sum());fn=int((~pred&target).sum());fp=int((pred&~target&known).sum());allfp=int((pred&~target).sum());per.append(dict(id=v['meta']['id'],video=v['meta']['video'],role='FIT'if v in row['FIT']else'HOLDOUT',IoU=tp/max(1,tp+fn+fp),all_pixel_IoU=tp/max(1,tp+fn+allfp),target_N=int(target.sum()),TP=tp,FN=fn,FP=fp,ring_front_conflict_N=int(((label==2)&np.isfinite(rz)&np.isfinite(z)&(z<rz-.05)).sum()),camera_correction_shared=D.tolist()if D is not None else None))
 return per

def shared_correction(task,row,mesh):
 """Independent shared 005 SE3; FIT contour + Ring evidence, never GT."""
 import cv2
 from scipy.ndimage import distance_transform_edt
 V=mesh['V'];F=mesh['F'];targets=[];ring=np.load(row['static']['RING.npz']['path']);RV=ring['V'];rng=np.random.default_rng(20261117);ids=np.linspace(0,len(V)-1,min(512,len(V)),dtype=int)
 for v in row['FIT']:
  if v['meta']['video']!='005':continue
  a=np.load(v['cache']['path']);lab=a['labels'];boundary=np.concatenate([c[:,0]for c in cv2.findContours((lab==1).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]]);boundary=boundary[np.linspace(0,len(boundary)-1,min(256,len(boundary)),dtype=int)];ringuv=np.column_stack(np.nonzero(lab==2))[:,::-1];ringuv=ringuv[np.linspace(0,len(ringuv)-1,min(256,len(ringuv)),dtype=int)]if len(ringuv)else ringuv;targets.append((a['K'],a['T'],boundary,ringuv))
 def matrix(p):
  D=np.eye(4);D[:3,:3]=Rotation.from_rotvec(p[:3]).as_matrix();D[:3,3]=p[3:];return D
 def residual(p):
  D=matrix(p);parts=[]
  for K,C,b,rb in targets:
   P,z=safe_project(V[ids],K,D@C);front=z>0;P=np.where(front[:,None],P,1e4);dt=cKDTree(b).query(P)[0];back=cKDTree(P).query(b)[0];parts.extend([np.minimum(dt,500)/20/np.sqrt(len(P)*len(targets)),np.minimum(back,500)/20/np.sqrt(len(b)*len(targets))]);R,_=safe_project(RV[::16],K,D@C)
   if len(rb):parts.append(np.minimum(cKDTree(rb).query(R)[0],500)/20*np.sqrt(.1/max(1,len(R)*len(targets))))
  parts.append(p/np.r_[np.full(3,np.pi),np.full(3,3.)]*.02);return np.concatenate(parts)
 runs=[];bound=np.r_[np.full(3,np.pi),np.full(3,3.)]
 for yaw in task['inita']['shared_005_starts_deg']:
  p=np.array([0.,0.,np.deg2rad(yaw),0.,0.,0.]);p=np.clip(p,-bound+1e-7,bound-1e-7);fit=least_squares(residual,p,bounds=(-bound,bound),diff_step=.001,x_scale=np.r_[np.full(3,.2),np.ones(3)],loss='soft_l1',f_scale=.1,max_nfev=task['inita']['shared_005_nfev']);runs.append(dict(start_yaw_deg=yaw,p=fit.x.tolist(),cost=float(fit.fun@fit.fun/2),optimizer_success=bool(fit.success),nfev=fit.nfev))
 best=min(runs,key=lambda r:r['cost']);return matrix(best['p']),dict(runs=runs,selected_by='FIT contour/Ring objective only; no HOLDOUT/GT',D=matrix(best['p']).tolist(),scope='one_shared_005_SE3; 004 fixed',not_deployment_certified=True)

def train(task,attempt,smoke=False):
 root=attempt.parents[1];cfg=task['inita'];rows=[];selected=[r for r in sources(task)['cases']if not smoke or r['case']in cfg['smoke_cases']]
 for row in selected:
  g=row['case'];out=attempt/g;out.mkdir();start=time.monotonic()
  if not smoke and g in cfg['smoke_cases']:
   src=fetch(root,'G1_smoke_train',g+'/CASE_PREDICTIONS_FROZEN.json').parent;copy_tree(src,out);records=json.loads((out/'CASE_PREDICTIONS_FROZEN.json').read_text());rows.extend(records['records']);continue
  shutil.copyfile(row['A0']['path'],out/'A0_WORLD.npz');records=[dict(case=g,arm='A0',status='NUMERIC',world_mesh=str(out/'A0_WORLD.npz'),source_sha256=row['A0']['sha256'],reference_immutable=True)]
  if row['status']!='READY':
   records.extend(dict(case=g,arm=a,status='NOT_EVALUABLE',reason=row['status'],world_mesh=None)for a in ['A1','A2'])
  else:
   for arm in ['A1','A2']:
    ar=prepare_arm(task,row,arm,out/arm);env=dict(os.environ,E4_RUN_DIR=str(ar));log=ar/'TRAIN_STDOUT.txt'
    with log.open('w')as f:code=subprocess.call([sys.executable,str(ROOT/'tools/research/_init_a_train.py'),g],env=env,stdout=f,stderr=subprocess.STDOUT)
    final=ar/'local_results'/g/'FINAL.npz'
    if code or not final.is_file():records.append(dict(case=g,arm=arm,status='FAILED_NAN',reason='Historical trainer returned '+str(code),log=str(log),world_mesh=None));continue
    world=out/(arm+'_WORLD.npz');shutil.copyfile(final,world);m=dict(np.load(world));score=projection_rows(m,row);save_json(out/(arm+'_PROJECTION.json'),score);info=json.loads((ar/'metrics'/(g+'_RUN.json')).read_text());records.append(dict(case=g,arm=arm,status='NUMERIC',world_mesh=str(world),world_sha256=sha256(world),training=info,projection=score,initial_sha256=row['resolved013_initial']['sha256'],GT_read=False))
    print('INIT_A',g,arm,info['status'],info['accepted'],flush=True)
   a2=next(r for r in records if r['arm']=='A2')
   if a2['status']=='NUMERIC':
    means={v:np.mean([p['IoU']for p in a2['projection']if p['role']=='FIT'and p['video']==v])for v in ['004','005']};trigger=means['005']<means['004']-cfg['shared_trigger']['delta_FIT_IoU']or means['005']<cfg['shared_trigger']['absolute_005_FIT_IoU'];save_json(out/'SHARED_005_TRIGGER.json',dict(FIT_IoU_by_video=means,triggered=bool(trigger),GT_used=False))
    if trigger:
     D,fit=shared_correction(task,row,dict(np.load(out/'A2_WORLD.npz')));save_json(out/'SHARED_005_SE3.json',fit);ar=prepare_arm(task,row,'A2S',out/'A2S',D);env=dict(os.environ,E4_RUN_DIR=str(ar))
     with(ar/'TRAIN_STDOUT.txt').open('w')as f:code=subprocess.call([sys.executable,str(ROOT/'tools/research/_init_a_train.py'),g],env=env,stdout=f,stderr=subprocess.STDOUT)
     final=ar/'local_results'/g/'FINAL.npz'
     if code or not final.exists():records.append(dict(case=g,arm='A2S',status='FAILED_NAN',world_mesh=None,reason='Shared-005 historical trainer '+str(code)))
     else:
      world=out/'A2S_WORLD.npz';shutil.copyfile(final,world);score=projection_rows(dict(np.load(world)),row,D);save_json(out/'A2S_PROJECTION.json',score);records.append(dict(case=g,arm='A2S',status='NUMERIC',world_mesh=str(world),world_sha256=sha256(world),shared_005_D=D.tolist(),projection=score,training=json.loads((ar/'metrics'/(g+'_RUN.json')).read_text()),GT_read=False))
  for rec in records:
   if rec['status']=='NUMERIC':rec['world_mesh_relative']=str(Path(rec['world_mesh']).relative_to(attempt));rec['world_sha256']=sha256(Path(rec['world_mesh']));rec['world_mesh']=None
  save_json(out/'CASE_PREDICTIONS_FROZEN.json',dict(records=records,FIT_only=True,GT_read=False,seconds=time.monotonic()-start));rows.extend(records)
 save_json(attempt/'BODY_PREDICTIONS_FROZEN.json',dict(records=rows,cohort='SMOKE_3'if smoke else'ALL_11',GT_read=False,initialization='EXACT_013_MESH',historical_measurement_fallback=0));return outputs(attempt,dict(status='PASS',records=len(rows),numeric=sum(r['status']=='NUMERIC'for r in rows),cohort=len(selected),GT_read_by_predictor=False))
