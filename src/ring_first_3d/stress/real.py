"""Source-bound native HERO adapter and GT-free minimal real pilot.

Only raw network geometry and exact image candidates are reused. All 3D Body
models are fitted afresh using this task's FIT images, not historic final shapes.
"""
import json,time,copy
from pathlib import Path
import numpy as np
import cv2
from scipy.spatial.transform import Rotation
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import require,PolicyError
from ..contracts.identities import sha256
from ..contracts.coordinates import validate_c2w,project,unproject
from ..multisurface.geometry import transform,vertex_normals,scene,closest,cast
from ..multisurface.evaluate import fixed_stats

def manifest(task):return json.loads(Path(task['stress']['assets']['real_manifest']['path']).read_text())

def safe_project(V,K,C):
 p=(np.asarray(V)-C[:3,3])@C[:3,:3];z=p[:,2];q=p@K.T;uv=q[:,:2]/np.where(abs(q[:,2:])>1e-12,q[:,2:],1.);return uv,z

def native_pixels(uv,K_native,K_full):
 p=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K_native).T@K_full.T
 return np.floor(p[:,:2]/p[:,2:]+.5).astype(int)

def load_view(row,sigma):
 a=row['assets'];raw=dict(np.load(a['raw_mesh']['path']));pack=dict(np.load(a['pack']['path']));cache=dict(np.load(a['cache']['path']));dxy=json.loads(Path(a['dxy']['path']).read_text());K=pack['K'];C=pack['pose'];H,W=pack['labels'].shape;A=K@np.linalg.inv(cache['K'])
 formal=bool(dxy.get('available'));center=(A@np.r_[dxy['center_px'],1.])[:2]if formal else None;basis=A[:2,:2]@np.asarray(dxy['basis_px'])if formal else None
 if not formal:
  from ..sim.geometry import ellipse_proxy
  fit=ellipse_proxy(pack['labels']==1);center=fit['center_px'];basis=fit['basis_px']
 fit=dict(id=row['id'],video=row['video'],role=row['role'],formal=dict(available=formal,quality=dxy.get('quality',{})),center_px=np.asarray(center).tolist(),basis_px=np.asarray(basis).tolist(),mapping_fit='FORMAL_DXY_AFFINE_PIXEL_TRANSPORT'if formal else'MASK_ELLIPSE_PROXY',pixel_transform=A.tolist(),source_DXY_sha256=a['dxy']['sha256'])
 uv=raw['uv'];pix=native_pixels(uv,K,cache['K']);RGB=cache['RGB'][pix[:,1],pix[:,0]]
 return dict(id=row['id'],video=row['video'],role=row['role'],V=raw['V'],F=raw['F'],uv=uv,K=K,C=C,sigma=np.r_[np.full(3,np.deg2rad(sigma[0])),np.full(3,sigma[1])],normals=vertex_normals(raw['V'],raw['F']),labels=pack['labels'],RGB=RGB,fit=fit,source=row,initialization_labels=cache['labels'],initialization_K=cache['K'],initialization_fit=dxy)

def validate_view(row):
 a=row['assets']
 require(all(not r.get('missing')and Path(r['path']).is_file()and sha256(r['path'])==r['sha256']for r in a.values()),'REAL_SOURCE','Missing or changed native asset: '+row['id'])
 native=dict(np.load(a['native']['path']));raw=dict(np.load(a['raw_mesh']['path']));pack=dict(np.load(a['pack']['path']));points=dict(np.load(a['points']['path']));cache=dict(np.load(a['cache']['path']));dxy=json.loads(Path(a['dxy']['path']).read_text());K=np.asarray(row['K']);C=np.asarray(row['C']);validate_c2w(C)
 require(row['unit']=='mm'and row['depth_definition']=='axialZ','COORDINATES','Real HERO must declare axial mm')
 require(str(native['reference_view'])==row['id'] and np.array_equal(native['source_views'],row['source_ids']),'SOURCE_IDENTITY','Actual HERO reference/support IDs')
 require(np.array_equal(native['depth_mm'],pack['depth_mm'])and np.allclose(native['K_index_native'],K)and np.allclose(native['reference_pose_mm'],C)and np.allclose(pack['pose'],C)and np.allclose(raw['T'],C),'REAL_CAMERA','Native depth/K/pose must bind source')
 require(np.array_equal(raw['V'],points['XYZ_mm'])and np.array_equal(raw['F'],points['original_faces'])and np.array_equal(raw['uv'],points['source_uv']),'MESH_SOURCE','Preserve original complete HERO topology')
 A=np.diag([1.,352/360,1.]);A[1,2]=.5*352/360-.5;require(np.allclose(A@cache['K'],K),'PIXEL_COORDINATES','Pixel-center native affine')
 H,W=pack['labels'].shape;y,x=np.mgrid[:H,:W];pix=native_pixels(np.c_[x.ravel(),y.ravel()],K,cache['K']);expected=cache['labels'][pix[:,1],pix[:,0]].reshape(H,W)
 require(np.array_equal(pack['labels'],expected),'MASK_IDENTITY','Exact nearest native sampling of original Mask')
 import hashlib
 require(hashlib.sha256(cache['RGB'].tobytes()).hexdigest()==dxy['RGB_content_SHA']and hashlib.sha256(cache['labels'].tobytes()).hexdigest()==dxy['Mask_content_SHA'],'DXY_CACHE_IDENTITY','DXY same raw image and Mask')
 require(a['source_RGB']['sha256']==row['target_RGB_SHA'],'SOURCE_IDENTITY','HERO actual reference image SHA')
 uv=raw['uv'];z=pack['depth_mm'][uv[:,1],uv[:,0]];V=unproject(uv,z,K,C);error=float(np.linalg.norm(V-raw['V'],axis=1).max());require(error<1e-5,'REAL_COORDINATES','Raw HERO native axial backprojection')
 proj,depth=project(raw['V'],K,C);reproj=float(np.linalg.norm(proj-uv,axis=1).max());require(reproj<1e-5,'REAL_COORDINATES','Source pixel projection identity')
 return dict(id=row['id'],role=row['role'],video=row['video'],status='PASS',vertices=len(raw['V']),faces=len(raw['F']),axial_backprojection_max_mm=error,reprojection_max_px=reproj,formal_DXY_available=bool(dxy.get('available')),formal_quality=dxy.get('quality'),no_absolute_GT=True)

def audit(task,attempt):
 records=[];started=time.monotonic()
 for group in manifest(task)['groups']:
  rows=[]
  for row in group['views']:
   try:rows.append(validate_view(row))
   except (PolicyError,OSError,ValueError,KeyError)as e:rows.append(dict(id=row['id'],role=row['role'],video=row['video'],status='NOT_EVALUABLE',reason=str(e)))
  fit=[r for r in rows if r['role']=='FIT'];ready=all(r['status']=='PASS'for r in rows)and len(fit)>=2
  support={sid for r in group['views']if r['role']=='FIT'for sid in r['source_ids']};leaks=[r['id']for r in group['views']if r['role']=='HOLDOUT'and r['id']in support]
  records.append(dict(group=group['group'],difficult_group=group['difficult_group'],status='READY'if ready else'NOT_EVALUABLE',views=rows,FIT=len(fit),HOLDOUT=sum(r['role']=='HOLDOUT'for r in rows),heldout_targets_in_FIT_HERO_support=leaks,absolute_3D_accuracy='NOT_EVALUABLE',world_status=group['world_status']))
 save_json(attempt/'REAL_AUDIT.json',dict(groups=records,seconds=time.monotonic()-started,read_only=True,GT_read=False,history_measurement_fallback=0));return outputs(attempt,dict(status='PASS',groups=records,group_failures_do_not_block_simulation=True))

def initialize(task,data,ring,ns,out):
 from ..sim.initialize import ellipse_target
 from ..sim.geometry import cast as old_cast
 ids=[d['id']for d in data];rs=scene(ring['V'],ring['F']);cfg=task['stress'];fits={d['id']:d['fit']for d in data};records=[];models={}
 class Problem:
  solve=ns['solve']
  def __init__(self,arm):
   self.scene='REAL_TASK_FIT_ONLY';self.arm=arm;self.variant='FRESH_2D_ONLY';self.ids=ids;self.R0=np.eye(3);self.base=np.asarray(cfg['real_initial_base']);self.lo=np.r_[np.full(3,-12.),np.full(3,-.8),np.log(np.full(3,.25))];self.hi=np.r_[np.full(3,12.),np.full(3,.8),np.log(np.full(3,15.))];self.weights=np.full(len(ids),1/len(ids));self.calls=0;self.invalid_calls=0;self.targets=[]
   for d in data:
    H,W=d['initialization_labels'].shape;gx,gy=np.meshgrid(np.arange(W//4)*4+1.5,np.arange(H//4)*4+1.5);grid=np.c_[gx.ravel(),gy.ravel()];target=d['initialization_labels']==1 if arm=='E2'else ellipse_target((H,W),d['initialization_fit']);cad=old_cast(rs,grid,d['initialization_K'],d['C'])[0];self.targets.append(ns['target_data'](target,d['initialization_labels'],cad,d['C'],d['initialization_K']))
   self.N=sum(128+len(t['boundary'])+len(t['grid']) for t in self.targets)+9 if all('grid'in t for t in self.targets)else 1000
  def residual(self,p):
   self.calls+=1
   try:
    rr=[]
    for t,d,w in zip(self.targets,data,self.weights):rr.extend(x*np.sqrt(w)for x in ns['two_d_parts'](p,self.R0,t,d['initialization_K'],d['C'],rs))
    prior=np.r_[(p[:3]-self.base[:3])/10,p[3:6]/.8,(p[6:9]-self.base[6:9])/1.2]*np.sqrt(.05);r=np.r_[np.concatenate(rr),prior]
    if not np.isfinite(r).all():raise ValueError('Nonfinite FIT-only residual')
    return r
   except (ValueError,np.linalg.LinAlgError):self.invalid_calls+=1;return np.full(self.N,1000.)
 for arm in ['E1','E2']:
  if arm=='E1'and not all(d['fit']['formal']['available']for d in data):records.append(dict(arm=arm,status='NOT_EVALUABLE_DXY'));continue
  prob=Problem(arm);r=prob.solve(0);r['status']='NUMERIC_DIAGNOSTIC'if np.isfinite(r['p']).all()and r['objective']<1000 else'FAILED_NAN';records.append(r)
  if r['status']=='NUMERIC_DIAGNOSTIC':
   V,F=ns['mesh'](np.asarray(r['p']),np.asarray(r['R0']),True);b=dict(V=V,F=F,p=np.asarray(r['p']),R0=np.asarray(r['R0']));models[arm]=b;np.savez_compressed(out/(arm+'_BODY.npz'),**b)
 primary='E1'if'E1'in models else'E2'if'E2'in models else None
 if primary is None:raise ValueError('SCIENTIFIC_BODY_INITIALIZATION_FAILED: no finite FIT-only real Body')
 save_json(out/'INITIALIZATION.json',dict(arms=records,primary=primary,FIT_ids=ids,GT_read=False,selection='Formal E1 priority, explicit E2 only if unavailable; no GT or old model input'))
 return models[primary],primary

def predict(task,attempt):
 from ..multisurface.registration import model_namespace,optimize,icp
 from ..multisurface.fusion import owned_model
 from .handlers import diagnostic
 root=attempt.parents[1];auditby={r['group']:r for r in json.loads(fetch(root,'G0_real_audit','REAL_AUDIT.json').read_text())['groups']};ns=model_namespace(task);groups=[]
 for group in manifest(task)['groups']:
  g=group['group'];out=attempt/g;out.mkdir();started=time.monotonic()
  if auditby[g]['status']!='READY':groups.append(dict(group=g,status='NOT_EVALUABLE',reason='Native source/interface audit did not pass',records=[]));continue
  try:
   data=[load_view(r,task['stress']['real_frame_prior_sigma_deg_mm'])for r in group['views']if r['role']=='FIT'];ring=dict(np.load(group['assets']['ring']['path']));body,arm=initialize(task,data,ring,ns,out);fits={d['id']:d['fit']for d in data};save_json(out/'IMAGE_FITS.json',list(fits.values()));digest=sha256(out/(arm+'_BODY.npz'));records=[]
   for method in task['fusion']['methods']:
    mo=out/method;mo.mkdir();t0=time.monotonic()
    try:
     if method=='M0':X=[np.eye(4)for d in data];details=dict(optimizer_success=True)
     elif method=='ICP':X,details=icp(task,data)
     else:X,details,_=optimize(task,data,body,fits,method=='BODY_HIER',task['fusion']['tolerance_mm'],ns)
     maps,diag=diagnostic(task,data,body,fits,X,ns);meshes=[]
     for i,(d,T)in enumerate(zip(data,X)):
      V=transform(d['V'],T);np.savez_compressed(mo/(d['id']+'.npz'),V=V,F=d['F']);meshes.append(dict(V=V,F=d['F']));edge=d['F'][:,[0,1]];require(np.max(abs(np.linalg.norm(V[edge[:,0]]-V[edge[:,1]],axis=1)-np.linalg.norm(d['V'][edge[:,0]]-d['V'][edge[:,1]],axis=1)))<1e-8,'MESH_RIGIDITY',d['id']);np.savez_compressed(mo/(d['id']+'_CANDIDATES.npz'),**{k:v for k,v in maps[i].items()if isinstance(v,np.ndarray)})
     model,own,summary=owned_model(body,meshes,[d['video']for d in data],task['fusion']);np.savez_compressed(mo/'FUSED_MODEL.npz',**model);np.savez_compressed(mo/'SURFACE_OWNERSHIP.npz',**{k:v for k,v in own.items()if not isinstance(v,bool)})
     record=dict(method=method,status='NUMERIC',corrections={d['id']:T.tolist()for d,T in zip(data,X)},details=details,correspondence=diag,ownership=summary)
    except PolicyError:raise
    except(ValueError,RuntimeError,np.linalg.LinAlgError)as e:record=dict(method=method,status='FAILED_NAN',reason=str(e))
    record['seconds']=time.monotonic()-t0;records.append(record);save_json(mo/'PREDICTION.json',record);print('REAL',g,method,record['status'],flush=True)
   require(sha256(out/(arm+'_BODY.npz'))==digest,'BODY_IMMUTABLE',g)
   groups.append(dict(group=g,status='NUMERIC',primary_body=arm,Body_sha256=digest,records=records,FIT_ids=[d['id']for d in data],HOLDOUT_ids=[r['id']for r in group['views']if r['role']=='HOLDOUT'],seconds=time.monotonic()-started,GT_read=False,camera_optimization=False))
  except PolicyError:raise
  except (ValueError,RuntimeError,np.linalg.LinAlgError)as e:groups.append(dict(group=g,status='FAILED_NAN',reason=str(e),records=[],seconds=time.monotonic()-started))
 save_json(attempt/'REAL_PREDICTIONS_FROZEN.json',dict(groups=groups,GT_read=False,new_HERO_inference=0,DXY_calls=0,history_measurement_fallback=0));return outputs(attempt,dict(status='PASS',groups=groups,real_groups_target=3,GT_read=False))

def overlap_targets(data):
 # Freeze baseline image-mask-supported query vertices. These are observable
 # support regions, not known material correspondences or independent GT.
 pairs=[]
 for i,d in enumerate(data):
  take=np.linspace(0,len(d['V'])-1,min(192,len(d['V'])),dtype=int);P=d['V'][take]
  for j,e in enumerate(data):
   if i==j:continue
   uv,z=safe_project(P,e['K'],e['C']);pix=np.rint(uv).astype(int);H,W=e['labels'].shape;inside=(z>0)&(pix[:,0]>=0)&(pix[:,0]<W)&(pix[:,1]>=0)&(pix[:,1]<H);ix=np.where(inside)[0];valid=inside.copy();valid[ix]&=e['labels'][pix[ix,1],pix[ix,0]]==1
   pairs.append(dict(first=i,second=j,family='within_video'if d['video']==e['video']else'cross_video',source_vertex=take[valid].tolist()))
 return pairs

def holdout_metrics(mesh,row,ring_scene):
 data=load_view(row,[.3,.1]);H,W=data['labels'].shape;y,x=np.mgrid[1:H:4,1:W:4];uv=np.c_[x.ravel(),y.ravel()];labels=data['labels'][uv[:,1],uv[:,0]];target=labels==1
 z,face,bary=cast(scene(mesh['V'],mesh['F']),uv,data['K'],data['C']);rz,_,_=cast(ring_scene,uv,data['K'],data['C']);pred=np.isfinite(z)&(z>0)&(z<rz-.05);intersection=int((target&pred).sum());union=int((target|pred).sum());native=np.load(row['assets']['pack']['path']);ref=native['depth_mm'][uv[:,1],uv[:,0]];valid=target&np.isfinite(ref)&(ref>0);err=np.full(int(valid.sum()),np.nan);err[pred[valid]]=abs(z[valid][pred[valid]]-ref[valid][pred[valid]])
 return dict(id=row['id'],video=row['video'],image_grid_N=len(uv),mask_target_N=int(target.sum()),predicted_visible_N=int(pred.sum()),mask_recall=intersection/max(1,int(target.sum())),mask_IoU=intersection/max(1,union),missed_mask_N=int((target&~pred).sum()),false_positive_N=int((pred&~target).sum()),heldout_HERO_axial_difference_mm=fixed_stats(err),axial_difference_is_not_GT=True,ring_contact_unknown_grid_N=int((labels==2).sum()))

def evaluate(task,attempt):
 root=attempt.parents[1];frozen=json.loads(fetch(root,'real_predict','REAL_PREDICTIONS_FROZEN.json').read_text());mb={g['group']:g for g in manifest(task)['groups']};rows=[]
 for group in frozen['groups']:
  g=group['group'];src=mb[g]
  if group['status']!='NUMERIC':rows.append(dict(group=g,status=group['status'],reason=group.get('reason'),absolute_GT_accuracy=None));continue
  data=[load_view(r,[.3,.1])for r in src['views']if r['role']=='FIT'];pairs=overlap_targets(data);save_json(attempt/(g+'_FIXED_OVERLAP_TARGETS.json'),pairs);ring=dict(np.load(src['assets']['ring']['path']));rs=scene(ring['V'],ring['F'])
  for rec in group['records']:
   r=dict(group=g,method=rec['method'],status=rec['status'],FIT_views=len(data),HOLDOUT_views=sum(v['role']=='HOLDOUT'for v in src['views']),absolute_GT_accuracy=None,GT_status='NOT_EVALUABLE_NO_INDEPENDENT_GT',no_GT_alignment=True)
   if rec['status']!='NUMERIC':r['reason']=rec['reason'];rows.append(r);continue
   meshes=[dict(np.load(fetch(root,'real_predict',g+'/'+rec['method']+'/'+d['id']+'.npz')))for d in data];scenes=[scene(m['V'],m['F'])for m in meshes];family={'within_video':[],'cross_video':[]}
   for p in pairs:
    P=meshes[p['first']]['V'][p['source_vertex']];Q,_,_=closest(scenes[p['second']],P)if len(P)else(np.empty((0,3)),None,None);family[p['family']].append(np.linalg.norm(P-Q,axis=1))
   r.update({k:fixed_stats(np.concatenate(v)if v else[])for k,v in family.items()});r['overlap_query_semantics']='Fixed baseline projected-mask support; nearest surfaces, not certified material matches';r['overlap_within0p2mm']={k:float((np.concatenate(v)<=.2).mean())if v and sum(map(len,v))else None for k,v in family.items()};r['correspondence']=rec['correspondence'];r['ownership']=rec['ownership'];r['seconds']=rec['seconds'];r['fixed_source_vertices']=sum(len(d['V'])for d in data)
   anomalies=[]
   for d,m in zip(data,meshes):
    V=m['V'];sd=rs.compute_signed_distance(__import__('open3d').core.Tensor(V.astype(np.float32)),nsamples=3).numpy();uv,z=safe_project(V,d['K'],d['C']);shift=np.linalg.norm(uv-d['uv'],axis=1)
    anomalies.append(dict(id=d['id'],vertices=len(V),faces=len(m['F']),ring_penetration_N=int((sd<-.02).sum()),behind_source_camera_N=int((z<=0).sum()),source_reprojection_displacement_px=fixed_stats(shift),original_topology_preserved=np.array_equal(m['F'],d['F'])))
   r['geometry_anomalies']=anomalies;fused=dict(np.load(fetch(root,'real_predict',g+'/'+rec['method']+'/FUSED_MODEL.npz')));r['HOLDOUT']=[holdout_metrics(fused,v,rs)for v in src['views']if v['role']=='HOLDOUT'];rows.append(r)
 save_json(attempt/'REAL_METRICS.json',dict(rows=rows,groups_target=3,GT_read=False,absolute_accuracy='NOT_EVALUABLE',no_historical_final_Body_used=True,holdout_excluded_from_Body_and_registration=True,real_prior_is_heuristic_not_calibrated=True));return outputs(attempt,dict(status='PASS',rows=len(rows),groups_numeric=sum(g['status']=='NUMERIC'for g in frozen['groups']),groups_target=3,GT_read=False))
