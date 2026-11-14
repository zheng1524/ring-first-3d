from v6_common import *
from background_registration import epi,vec,pose
from scipy.sparse import lil_matrix
cv2.setNumThreads(2)

def pair_data(tr,pack):
 out=[];held=tr['held']
 for k,(i,j) in enumerate(pack['ij']):
  rows=pack[f'pair{k}'];rows=rows[~held[rows[:,0].astype(int)]];n=len(rows)
  if n<12:continue
  cv2.setRNGSeed(cfg()['seed']);F,ok=cv2.findFundamentalMat(rows[:,1:3],rows[:,3:5],cv2.FM_RANSAC,1.5,.999)
  if ok is None:continue
  rows=rows[ok.ravel().astype(bool)]
  if len(rows)>=12:out.append(dict(i=int(i),j=int(j),rows=rows))
 return out

def canonical_reference(p):
 p=positive_gauge(p);a=np.arctan2(p[1,3],p[0,3]);return spin(p,-a)

def initialize(ring,tr,edges,ref,version):
 n=len(ring);pp=[None]*n;branch=np.full(n,-1,int);cand=ring[ref]['candidates'];select=0
 if version:
  base=np.array(cand[0]['normal']);alts=[i for i,c in enumerate(cand) if np.degrees(np.arccos(np.clip(abs(base@c['normal']),-1,1)))>10];select=alts[0] if alts else min(1,len(cand)-1)
 pp[ref]=canonical_reference(np.array(cand[select]['c2r']));branch[ref]=select;history=[]
 for step in range(n-1):
  possibilities=[]
  for e in edges:
   if (pp[e['i']] is None)==(pp[e['j']] is None):continue
   possibilities.append((len(e['rows']),e))
  if not possibilities:break
  e=max(possibilities,key=lambda x:x[0])[1];i,j=e['i'],e['j'];rows=e['rows'];p,q=rows[:,1:3],rows[:,3:5]
  if pp[i] is None:i,j=j,i;p,q=q,p
  starts=[]
  for ci,c in enumerate(ring[j]['candidates']):
   base=positive_gauge(np.array(c['c2r']))
   def score(t):
    po=spin(base,t);ee=epi(pp[i],po,p,q,K);return float(np.mean(2*(np.sqrt(1+ee*ee)-1)))
   grid=np.linspace(-np.pi,np.pi,cfg()['yaw_grid'],endpoint=False);vals=[score(t) for t in grid];best=grid[int(np.argmin(vals))];f=minimize_scalar(score,bounds=(best-np.pi/36,best+np.pi/36),method='bounded');po=spin(base,f.x);P=[]
   for u,v in zip(p[::max(1,len(p)//50)],q[::max(1,len(q)//50)]):P.append(triangle([pp[i],po],[u,v]))
   P=np.array(P);_,a=project(P,pp[i],K);_,b=project(P,po,K);pos=float(((a>0)&(b>0)).mean());starts.append((f.fun+5*max(0,.95-pos),ci,f.x,po,pos))
  starts.sort(key=lambda x:x[0]);cost,ci,yaw,po,pos=starts[0];pp[j]=po;branch[j]=ci;history.append(dict(from_frame=i,to_frame=j,candidate=ci,alpha_rad=yaw,training_cost=cost,positive_fraction=pos))
 if any(p is None for p in pp):raise RuntimeError('Ring pose graph disconnected; no free SfM fallback')
 pp=np.array(pp);base=pp.copy();others=[i for i in range(n) if i!=ref]
 def alpha_res(x):
  cur=base.copy()
  for i,v in zip(others,x):cur[i]=spin(base[i],v)
  out=[epi(cur[e['i']],cur[e['j']],e['rows'][:,1:3],e['rows'][:,3:5],K) for e in edges];full=np.zeros(n);full[others]=x;out.append(np.diff(full)/np.deg2rad(30));return np.concatenate(out)
 fit=least_squares(alpha_res,np.zeros(n-1),loss='soft_l1',f_scale=1.,max_nfev=cfg()['global_alpha_nfev']);out=base.copy()
 for i,v in zip(others,fit.x):out[i]=spin(base[i],v)
 return out,dict(reference_branch=select,branches=branch,initialization_steps=history,alpha_nfev=fit.nfev,alpha_training_loss=float(np.mean(abs(alpha_res(fit.x)))))

def triangulate_training(poses,tr):
 X=[];tids=[];support=[];xy=tr['xy']
 order=sorted(np.flatnonzero(~tr['held']),key=lambda t:(-np.isfinite(xy[t,:,0]).sum(),int(t)))
 for t in order:
  frames=np.flatnonzero(np.isfinite(xy[t,:,0]));P=triangle(poses[frames],xy[t,frames]);uv=np.array([project(P[None],poses[i],K)[0][0] for i in frames]);z=np.array([project(P[None],poses[i],K)[1][0] for i in frames]);er=np.linalg.norm(uv-xy[t,frames],axis=1);rays=unit(P-poses[frames,:3,3]);angle=float(np.degrees(np.arccos(np.clip((rays@rays.T).min(),-1,1))))
  if (z>0).mean()<.8 or np.median(er)>6. or angle<.5:continue
  X.append(P);tids.append(t);support.append(frames)
  if len(X)>=cfg()['BA_max_train_tracks']:break
 if len(X)<15:raise RuntimeError('insufficient positive Ring-initialized scene points')
 return np.array(X),np.array(tids),support

def BA(poses,X,tids,support,tr,ref):
 n=len(poses);others=[i for i in range(n) if i!=ref];lookup={i:j for j,i in enumerate(others)};nc=6*len(others);x0=np.r_[np.concatenate([vec(poses[i]) for i in others]),X.ravel()];ob=[obs(a['id']) for a in ledger()];pi=[];fi=[];uv=[]
 for j,(t,frames) in enumerate(zip(tids,support)):
  for i in frames:pi.append(j);fi.append(i);uv.append(tr['xy'][t,i])
 pi,fi,uv=np.array(pi),np.array(fi),np.array(uv);counts=np.bincount(fi,minlength=n);rglen=[len(ring_residual(poses[i],ob[i])) for i in range(n)];nf=len(fi);rows=3*nf+sum(rglen)+6*(n-1);sp=lil_matrix((rows,len(x0)),dtype=int)
 for j,(point,frame) in enumerate(zip(pi,fi)):
  row=[2*j,2*j+1,2*nf+j];sp[row,nc+point*3:nc+point*3+3]=1
  if frame!=ref:sp[row,lookup[frame]*6:lookup[frame]*6+6]=1
 row=3*nf
 for i,nn in enumerate(rglen):
  if i!=ref:sp[row:row+nn,lookup[i]*6:lookup[i]*6+6]=1
  row+=nn
 for i in range(n-1):
  for j in [i,i+1]:
   if j!=ref:sp[row:row+6,lookup[j]*6:lookup[j]*6+6]=1
  row+=6
 def decode(x):
  cur=poses.copy()
  for i in others:cur[i]=pose(x[lookup[i]*6:lookup[i]*6+6])
  return cur,x[nc:].reshape(-1,3)
 def residual(x):
  cur,P=decode(x);pc=np.einsum('ni,nij->nj',P[pi]-cur[fi,:3,3],cur[fi,:3,:3]);q=pc@K.T;den=np.where(abs(q[:,2])>.01,q[:,2],.01);feat=(q[:,:2]/den[:,None]-uv).ravel();positive=10*np.maximum(0,.1-pc[:,2]);out=[feat,positive]
  for i in range(n):out.append(ring_residual(cur[i],ob[i])*np.sqrt(max(1,counts[i])/max(1,rglen[i])))
  for i in range(n-1):
   dc=(cur[i+1,:3,3]-poses[i+1,:3,3])-(cur[i,:3,3]-poses[i,:3,3]);r0=Rotation.from_matrix(cur[i,:3,:3]@poses[i,:3,:3].T).as_rotvec();r1=Rotation.from_matrix(cur[i+1,:3,:3]@poses[i+1,:3,:3].T).as_rotvec();out.append(np.r_[dc/10.,(r1-r0)/np.deg2rad(30)])
  return np.concatenate(out)
 fit=least_squares(residual,x0,jac_sparsity=sp.tocsr(),loss='soft_l1',f_scale=1.,max_nfev=cfg()['BA_max_nfev'],diff_step=1e-5,ftol=1e-5,xtol=1e-5,gtol=1e-5);cur,P=decode(fit.x);res=residual(fit.x);return cur,P,dict(success=fit.success,nfev=fit.nfev,train_track_ids=tids,train_feature_residual=stats(res[:2*nf]),training_soft_l1_objective=float(np.mean(2*(np.sqrt(1+res*res)-1))),train_observations=nf,trained_points=len(X),optimized_reference=False,ring_model_static=True)

def main():
 verify('tracks');freeze('local_solver_protocol',[Path(__file__),R/'scripts/v6_common.py',R/'config.json',V5/'scripts/background_registration.py',V5/'scripts/branch_seed_policy.py']);tr=np.load(R/'observations/tracks005.npz');pack=np.load(R/'observations/pairs005.npz');ring=load('predictions/ring_candidates005.json');edges=pair_data(tr,pack);ref=next(i for i,a in enumerate(ledger()) if a['raw_frame']==459);out=[]
 for v in range(cfg()['pose_initializations']):
  rec=dict(version=v,success=False)
  try:
   po,ini=initialize(ring,tr,edges,ref,v);np.savez_compressed(R/f'predictions/local005_initial_{v}.npz',c2w=po,K=K);print('LOCAL_INIT',v,'connected',len(po),'alpha cost',ini['alpha_training_loss'],flush=True);X,ids,support=triangulate_training(po,tr);print('POINTS_INIT',v,len(X),flush=True);cur,P,ba=BA(po,X,ids,support,tr,ref);np.savez_compressed(R/f'predictions/local005_camera_{v}.npz',c2w=cur,K=K,points=P,point_track_ids=ids,reference=ref,ids=tr['ids'],units='mm',status='MODEL_PREDICTED');rec.update(success=True,initialization=ini,BA=ba);print('LOCAL_BA',v,ba['training_soft_l1_objective'],'points',len(P),'nfev',ba['nfev'],flush=True)
  except Exception:
   import traceback;rec['failure']=traceback.format_exc();print(rec['failure'],flush=True)
  out.append(rec);save('metrics/local005_solver.json',out)
 freeze('local_cameras',[R/'metrics/local005_solver.json']+list((R/'predictions').glob('local005*.npz')));print('LOCAL005_FINISHED',flush=True)
if __name__=='__main__':main()
