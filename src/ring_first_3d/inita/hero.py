"""Actual frozen Init-A Mesh projection adapter for the inherited surface optimizer."""
import json,types,time
from pathlib import Path
import numpy as np
import cv2
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import ROOT,require,PolicyError
from ..contracts.identities import sha256
from ..multisurface.geometry import transform,scene,cast,vertex_normals
from ..multisurface import registration as inherited
from ..stress.real import validate_view,load_view,overlap_targets,safe_project,holdout_metrics
from ..multisurface.evaluate import fixed_stats
from .train import sources,copy_tree

def parameters(task):
 import yaml
 cfg=yaml.safe_load(Path(task['inita']['assets']['hero_policy_source']['path']).read_text())['fusion'];return dict(fusion=cfg)

def mesh_ellipse(V,F,K,C):
 """Apparent Mesh contour, not an ellipsoid fitted in three dimensions."""
 tri=V[F];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);front=(n*(C[:3,3]-tri.mean(1))).sum(1)>0;edges=np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1);faces=np.tile(np.arange(len(F)),3);unique,inv=np.unique(edges,axis=0,return_inverse=True);ad=np.full((len(unique),2),-1,int)
 for i,k in enumerate(inv):ad[k,0 if ad[k,0]<0 else 1]=faces[i]
 take=(ad[:,1]<0)|(front[ad[:,0]]!=front[np.maximum(ad[:,1],0)]);ids=np.unique(unique[take]);uv,z=safe_project(V[ids],K,C);uv=uv[(z>0)&np.isfinite(uv).all(1)];require(len(uv)>=5,'MESH_PROJECTION','No finite visible actual Mesh contour');(cx,cy),(diam0,diam1),angle=cv2.fitEllipse(uv.astype(np.float32));theta=np.deg2rad(angle);U=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]);B=U@np.diag([diam0/2,diam1/2]);M=np.linalg.inv(B@B.T);q=np.arange(128)*2*np.pi/128;curve=np.array([cx,cy])+np.c_[np.cos(q),np.sin(q)]@B.T;return np.array([cx,cy]),M,np.array([diam0/2,diam1/2]),curve

def mapping_constraints(task,data,body,fits,X,unused):
 from ..sim.mapping import candidates
 cfg=task['fusion'];out=[]
 for i,d in enumerate(data):
  ix=np.linspace(0,len(d['V'])-1,min(cfg['registration_samples_per_view'],len(d['V'])),dtype=int);uv=d['uv'][ix];Pi=d['V'][ix];preV=transform(body['V'],np.linalg.inv(X[i]));ellipse=mesh_ellipse(preV,body['F'],d['K'],d['C']);pre=dict(V=preV,F=body['F'],p=None,R0=None);ns=dict(ellipse_projection=lambda p,R0,K,C:ellipse);m=candidates(uv,fits[d['id']],pre,d['K'],d['C'],ns,.97,True,scene(preV,body['F']));target=transform(m['points'],X[i]);dist=np.linalg.norm(transform(Pi,X[i])-target,axis=1);contact=cv2.dilate((d['labels']==2).astype(np.uint8),np.ones((3,3),np.uint8))[uv[:,1].astype(int),uv[:,0].astype(int)]>0;keep=m['valid']&~contact&(m['confidence']>=cfg['candidate_confidence_min'])&(dist<=cfg['candidate_reject_distance_mm']);quality=1. if fits[d['id']]['formal']['quality'].get('strict_stable',False)else .5
  out.append(dict(i=i,P=Pi[keep],Q=target[keep],weight=m['confidence'][keep]*quality,target_N=len(Pi),accepted_N=int(keep.sum()),contact_unknown_N=int(contact.sum()),original_uv=uv,mapped_uv=m['mapped_uv'],face=m['face'],bary=m['bary'],confidence=m['confidence'],accepted=keep,raw_source_points=Pi,candidate_points=target))
 return out

def inherited_mesh_optimizer():
 # Byte-identical optimizer; replace only its typed projected-Body data provider.
 scope=dict(inherited.optimize.__globals__);scope['mapping_constraints']=mapping_constraints
 return types.FunctionType(inherited.optimize.__code__,scope,inherited.optimize.__name__,inherited.optimize.__defaults__,inherited.optimize.__closure__)

def predict(task,attempt,smoke=False):
 root=attempt.parents[1];cfg=parameters(task);rows=[];cohort=task['inita']['smoke_cases']if smoke else task['inita']['cases'];stage='G1_smoke_train'if smoke else'G1_all_train';bodies=json.loads(fetch(root,stage,'BODY_PREDICTIONS_FROZEN.json').read_text())['records'];by={(r['case'],r['arm']):r for r in bodies};optimize=inherited_mesh_optimizer()
 for group in sources(task)['real_groups']:
  g=group['group']
  if g not in cohort:continue
  out=attempt/g;out.mkdir();start=time.monotonic()
  if not smoke and g in task['inita']['smoke_cases']:
   source=fetch(root,'G2_smoke_hero',g+'/HERO_PREDICTIONS_FROZEN.json').parent;copy_tree(source,out);rows.append(json.loads((out/'HERO_PREDICTIONS_FROZEN.json').read_text()));continue
  fit=[r for r in group['views']if r['role']=='FIT'];record=dict(case=g,target_cases=11,FIT_views=len(fit),videos=sorted({r['video']for r in fit}),records=[],absolute_accuracy='NOT_EVALUABLE_NO_INDEPENDENT_GT')
  if len(fit)<2 or any(by.get((g,a),{}).get('status')!='NUMERIC'for a in ['A1','A2']):record.update(status='NOT_EVALUABLE',reason='No >=2 source-bound complete HERO Meshes or A1/A2 unavailable');save_json(out/'HERO_PREDICTIONS_FROZEN.json',record);rows.append(record);continue
  for r in group['views']:validate_view(r)
  data=[load_view(r,task['inita']['HERO_frame_prior_deg_mm'])for r in fit];fits={d['id']:d['fit']for d in data};rawinfo=[]
  for d in data:np.savez_compressed(out/(d['id']+'_ORIGINAL.npz'),V=d['V'],F=d['F']);rawinfo.append(dict(id=d['id'],video=d['video'],vertices=len(d['V']),faces=len(d['F'])))
  for method in ['M0','BODY_A0','BODY_A1','BODY_A2','ICP']:
   mo=out/method;mo.mkdir();started=time.monotonic();arm=method.removeprefix('BODY_')if method.startswith('BODY_')else'A2';brec=by[g,arm];body=dict(np.load(fetch(root,stage,brec['world_mesh_relative'])));digest=sha256(fetch(root,stage,brec['world_mesh_relative']))
   try:
    if method=='M0':X=[np.eye(4)for _ in data];details=dict(optimizer_success=True);maps=[]
    elif method=='ICP':X,details=inherited.icp(cfg,data);maps=[]
    else:X,details,maps=optimize(cfg,data,body,fits,True,.5,None)
    final=mapping_constraints(cfg,data,body,fits,X,None);pairs=inherited.pair_constraints(cfg,data,X,inherited.graph(data));diagnostic=dict(body_rate=sum(m['accepted_N']for m in final)/sum(m['target_N']for m in final),pair_rate=sum(p['accepted_N']for p in pairs)/max(1,sum(p['target_N']for p in pairs)),per_view=[{k:m[k]for k in ['i','target_N','accepted_N','contact_unknown_N']}for m in final]);motions=[]
    for i,(d,T)in enumerate(zip(data,X)):
     V=transform(d['V'],T);e=d['F'][:,[0,1]];preserve=float(np.max(abs(np.linalg.norm(V[e[:,0]]-V[e[:,1]],axis=1)-np.linalg.norm(d['V'][e[:,0]]-d['V'][e[:,1]],axis=1))));require(preserve<1e-8,'MESH_RIGIDITY',d['id']);np.savez_compressed(mo/(d['id']+'.npz'),V=V,F=d['F']);np.savez_compressed(mo/(d['id']+'_CANDIDATES.npz'),**{k:v for k,v in final[i].items()if isinstance(v,np.ndarray)});motions.append(dict(id=d['id'],maximum_motion_mm=float(np.linalg.norm(V-d['V'],axis=1).max()),mean_motion_mm=float(np.linalg.norm(V-d['V'],axis=1).mean()),edge_change_max_mm=preserve))
    rr=dict(method=method,status='NUMERIC',corrections={d['id']:T.tolist()for d,T in zip(data,X)},details=details,correspondence=diagnostic,motions=motions,body_arm=arm,body_world_sha256=digest,GT_aligned_Body_used=False)
   except PolicyError as e:
    if e.code!='MESH_PROJECTION':raise
    rr=dict(method=method,status='FAILED_NAN',reason=str(e))
   except (ValueError,RuntimeError,np.linalg.LinAlgError)as e:rr=dict(method=method,status='FAILED_NAN',reason=str(e))
   rr['seconds']=time.monotonic()-started;record['records'].append(rr);save_json(mo/'PREDICTION.json',rr);print('HERO_INITA',g,method,rr['status'],flush=True)
   require(sha256(fetch(root,stage,brec['world_mesh_relative']))==digest,'BODY_IMMUTABLE',g)
  record.update(status='NUMERIC',source_meshes=rawinfo,seconds=time.monotonic()-start);save_json(out/'HERO_PREDICTIONS_FROZEN.json',record);rows.append(record)
 save_json(attempt/'ALL_HERO_PREDICTIONS_FROZEN.json',dict(groups=rows,Body_frozen=True,camera_optimized=False,GT_read=False));return outputs(attempt,dict(status='PASS',groups=len(rows),numeric_groups=sum(r['status']=='NUMERIC'for r in rows),GT_read_by_predictor=False))

def evaluate(task,attempt,smoke=False):
 root=attempt.parents[1];stage='G2_smoke_hero'if smoke else'G2_all_hero';groups=json.loads(fetch(root,stage,'ALL_HERO_PREDICTIONS_FROZEN.json').read_text())['groups'];srcby={g['group']:g for g in sources(task)['real_groups']};metrics=[]
 for g in groups:
  name=g['case'];src=srcby[name]
  if g['status']!='NUMERIC':metrics.append(dict(case=name,status=g['status'],reason=g['reason'],methods=[],absolute_accuracy='NOT_EVALUABLE'));continue
  data=[load_view(v,[.3,.1])for v in src['views']if v['role']=='FIT'];pairs=overlap_targets(data);save_json(attempt/(name+'_FIXED_HERO_OVERLAP.json'),pairs);ring=np.load(src['assets']['ring']['path']);rs=scene(ring['V'],ring['F']);arms=[]
  for rec in g['records']:
   row={k:rec[k]for k in ['method','status']};row.update(FIT_views=len(data),HOLDOUT_views=sum(v['role']=='HOLDOUT'for v in src['views']),absolute_GT_accuracy=None)
   if rec['status']!='NUMERIC':row['reason']=rec['reason'];arms.append(row);continue
   meshes=[dict(np.load(fetch(root,stage,name+'/'+rec['method']+'/'+d['id']+'.npz')))for d in data];scenes=[scene(m['V'],m['F'])for m in meshes];family={'within_video':[],'cross_video':[]}
   from ..multisurface.geometry import closest
   for p in pairs:
    P=meshes[p['first']]['V'][p['source_vertex']];Q,_,_=closest(scenes[p['second']],P)if len(P)else(np.empty((0,3)),None,None);family[p['family']].append(np.linalg.norm(P-Q,axis=1))
   row.update({k:fixed_stats(np.concatenate(v)if v else[])for k,v in family.items()});Vs=[];Fs=[];offset=0
   for m in meshes:Vs.append(m['V']);Fs.append(m['F']+offset);offset+=len(m['V'])
   full=dict(V=np.concatenate(Vs),F=np.concatenate(Fs));row['HOLDOUT']=[holdout_metrics(full,v,rs)for v in src['views']if v['role']=='HOLDOUT'];row.update(correspondence=rec['correspondence'],motions=rec['motions'],Body_frozen=True,all_source_vertices=sum(len(m['V'])for m in meshes),all_source_faces=sum(len(m['F'])for m in meshes),overlap_semantics='Fixed baseline projected-mask support, not certified material identity');arms.append(row)
  metrics.append(dict(case=name,status='NUMERIC',methods=arms,videos=g['videos'],partial_single_video=len(g['videos'])<2,absolute_accuracy='NOT_EVALUABLE_NO_INDEPENDENT_GT'))
 save_json(attempt/'HERO_METRICS.json',dict(groups=metrics,target_physical_cases=11,no_GT_alignment=True,GT_aligned_Body_used=False));return metrics
