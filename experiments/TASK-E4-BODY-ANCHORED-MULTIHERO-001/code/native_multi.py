"""Fixed-camera axial depth correction and qualified native correspondences."""
from common import *
import open3d as o3d
from scipy.optimize import least_squares
CFG=load(R/'config/PROTOCOL.json')

def raycast(s,C,K,uv):
 r=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;r=r@C[:3,:3].T
 return {k:v.numpy()for k,v in s.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],r.shape),r].astype(np.float32))).items()}
def project(X,C,K):
 x=(X-C[:3,3])@C[:3,:3];p=x@K.T
 return p[:,:2]/np.maximum(p[:,2,None],1e-12),x[:,2]
def corrected(X,C,theta):
 x=(X-C[:3,3])@C[:3,:3];A=np.c_[np.ones(len(x)),x[:,:2]/x[:,2,None]];d=A@theta
 return C[:3,3]+(X-C[:3,3])*(1+d/x[:,2])[:,None]
def face_normals(V,F):
 n=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
class Source:
 def __init__(self,record):
  self.rec=record;self.id=record['id'];self.m=dict(np.load(record['mesh']));self.o=dict(np.load(record['obs']));self.C=self.o['T'];self.K=self.o['K'];self.theta=np.zeros(3);self.z0=self.o['z'].astype(float);self.uv=self.o['uv'];self.ray=np.c_[self.uv,np.ones(len(self.uv))]@np.linalg.inv(self.K).T;self.A=np.c_[np.ones(len(self.uv)),self.ray[:,:2]];self.ray=self.ray@self.C[:3,:3].T
  # Full native depth coordinates are never inferred from an archived 360-row mesh.
  assert np.max(np.linalg.norm(self.C[:3,3]+self.ray*self.z0[:,None]-self.o['X'],axis=1))<1e-3
  pack=np.load(record['pack']);self.labels=pack['labels'];self.Kmask=pack['K'];self.normal0=self.o['normal'];self.sub=np.linspace(0,len(self.uv)-1,min(CFG['correspondence_samples'],len(self.uv)),dtype=int);self.w=0.;self.peer_conflict=np.zeros(len(self.uv),bool)
 def points(self,theta=None):
  theta=self.theta if theta is None else theta;return self.C[:3,3]+self.ray*(self.z0+self.A@theta)[:,None]
 def vertices(self,theta=None):return corrected(self.m['V'],self.C,self.theta if theta is None else theta)
 def normals(self):
  # The three-param map has an analytic Jacobian in camera space; inverse transpose normals.
  X=self.o['X'];x=(X-self.C[:3,3])@self.C[:3,:3];z=x[:,2];b,a,c=self.theta;r=x[:,:2]/z[:,None];d=b+a*r[:,0]+c*r[:,1];grad=np.c_[a/z,c/z,-(a*r[:,0]+c*r[:,1])/z];ray=x/z[:,None];J=np.eye(3)[None]*(1+d/z)[:,None,None]+ray[:,:,None]*grad[:,None,:]-ray[:,:,None]*np.c_[np.zeros((len(z),2)),d/z][:,None,:];n=self.normal0@self.C[:3,:3];n=np.linalg.solve(J.transpose(0,2,1),n);n=n@self.C[:3,:3].T;return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
 def mask_at(self,X):
  uv,z=project(X,self.C,self.Kmask);p=np.rint(uv).astype(int);h,w=self.labels.shape;inside=(p[:,0]>=0)&(p[:,0]<w)&(p[:,1]>=0)&(p[:,1]<h)&(z>0);out=np.zeros(len(X),bool);out[inside]=self.labels[p[inside,1],p[inside,0]]==1;return out

def source_weights(ss,center):
 blocks={};parent={s.id:set(s.rec['parent_sha'])for s in ss}
 for s in ss:
  d=s.C[:3,3]-center;d=d/np.linalg.norm(d);az=np.arctan2(d[1],d[0]);el=np.arcsin(d[2]);b=(int((az+np.pi)/(np.pi/4))%8,int(np.clip((el+np.pi/2)/(np.pi/3),0,2)));blocks[s.id]=b
 raw={s.id:1/(1+sum(len(parent[s.id]&parent[t.id])/max(1,len(parent[s.id]|parent[t.id]))for t in ss if t.id!=s.id))for s in ss}
 for s in ss:s.w=raw[s.id]/sum(raw[t.id]for t in ss if blocks[t.id]==blocks[s.id])/len(set(blocks.values()))
 return [dict(source=s.id,block=blocks[s.id],weight=s.w,correlation_raw=raw[s.id],parent_sha=sorted(parent[s.id]))for s in ss]

def correspond(s,V,F,body,ring,full=False):
 ii=np.arange(len(s.uv))if full else s.sub;X=s.points()[ii];n=s.normals()[ii];uv=s.uv[ii];ans=raycast(body,s.C,s.K,uv);z=ans['t_hit'].astype(float);hit=np.isfinite(z);cz=raycast(ring,s.C,s.K,uv)['t_hit'];known=s.mask_at(X)&(s.z0[ii]+s.A[ii]@s.theta>0)&(s.z0[ii]+s.A[ii]@s.theta<cz-.05)
 near=body.compute_closest_points(o3d.core.Tensor(X.astype(np.float32)));Q=near['points'].numpy().astype(float);face=near['primitive_ids'].numpy().astype(int);bn=face_normals(V,F)[face];dist=np.linalg.norm(X-Q,axis=1);q_uv,qz=project(Q,s.C,s.K);qvis=raycast(body,s.C,s.K,q_uv)['t_hit'];qr=raycast(ring,s.C,s.K,q_uv)['t_hit'];visible=(abs(qvis-qz)<.1)&(qz<qr-.05);normal=(n*bn).sum(1)>CFG['normal_cos'];consistent=known&visible&normal&s.mask_at(Q)&(np.linalg.norm(q_uv-uv,axis=1)<=CFG['reprojection_px'])&hit&(abs(z-(s.z0[ii]+s.A[ii]@s.theta))<=CFG['overlap_mm']);matched=consistent&(dist<=CFG['overlap_mm'])&~s.peer_conflict[ii]
 # Conflict here means qualified Body first-layer disagreement, not physical ground truth.
 conflict=known&s.peer_conflict[ii]
 state=np.full(len(ii),1,np.uint8);state[conflict]=2;state[matched]=0;state[~known]=3
 return dict(index=ii,X=X,normal=n,Q=Q,face=face,distance=dist,hit=hit,z=z,known=known,normal_ok=normal,matched=matched,state=state,cad_z=cz,visible=visible)

def bias_proposal(s,corr):
 ok=corr['matched'];ii=corr['index'][ok];normal=corr['normal'][ok];Q=corr['Q'][ok];J=(normal*s.ray[ii]).sum(1)[:,None]*s.A[ii];sv=np.linalg.svd(J,compute_uv=False);cond=float(sv[0]/max(sv[-1],1e-15))if len(sv)==3 else float('inf');rank=int(np.linalg.matrix_rank(J))if len(J)else 0
 rec=dict(source=s.id,matches=len(ii),rank=rank,condition=cond,singular_values=sv.tolist(),status='INSUFFICIENT_CONSTRAINT',before=s.theta.tolist())
 if len(ii)<CFG['min_bias_matches']or rank<3 or cond>CFG['max_bias_condition']:return s.theta.copy(),rec
 r0=((s.o['X'][ii]-Q)*normal).sum(1);sc=np.array(CFG['bias_prior_sigma_mm']);lam=CFG['bias_prior_weight'];norm=np.sqrt(len(ii));reg=np.sqrt(lam)/sc
 def fun(t):return np.r_[(r0+J@t)/CFG['surface_sigma_mm']/norm,t*reg]
 def jac(t):return np.r_[J/CFG['surface_sigma_mm']/norm,np.diag(reg)]
 bound=np.array(CFG['bias_bounds_mm']);sol=least_squares(fun,s.theta,jac=jac,bounds=(-bound,bound),method='trf',loss='soft_l1',f_scale=1./norm,max_nfev=50,ftol=1e-9,xtol=1e-9,gtol=1e-9);t=sol.x;inc=np.max(abs(s.A@(t-s.theta)));t=s.theta+(t-s.theta)*min(1,CFG['round_depth_limit_mm']/max(inc,1e-15));scale=min(1,CFG['cumulative_depth_limit_mm']/max(np.max(abs(s.A@t)),1e-15));t=t*scale;rec.update(status='PROPOSED',candidate=t.tolist(),nfev=sol.nfev,fixed_cost_before=float(np.sum(fun(s.theta)**2)),fixed_cost_after=float(np.sum(fun(t)**2)),fixed_correspondence=True);return t,rec

def weak_anchors(s,corr,V,F,body,ring):
 # Candidate faces must be visible in this same source, project in foreground and be near its residual ray.
 tri=V[F];cent=tri.mean(1);n=face_normals(V,F);pu,pz=project(cent,s.C,s.K);vis=raycast(body,s.C,s.K,pu)['t_hit'];cz=raycast(ring,s.C,s.K,pu)['t_hit'];visible=(abs(vis-pz)<.15)&(pz<cz-.05)&s.mask_at(cent);validfaces=np.where(visible)[0];ids=np.where((corr['state']==1)&corr['known']&~corr['hit'])[0];out=[]
 if not len(validfaces)or not len(ids):return np.empty((0,2),int)
 tree=cKDTree(pu[validfaces]);ds,jj=tree.query(s.uv[corr['index'][ids]],k=min(12,len(validfaces)));ds=np.atleast_2d(ds);jj=np.atleast_2d(jj)
 if len(ids)>1 and ds.shape[0]!=len(ids):ds=ds.T;jj=jj.T
 for row,idx in enumerate(ids):
  fi=validfaces[np.ravel(jj[row])];dd=np.ravel(ds[row]);X=corr['X'][idx];nn=corr['normal'][idx];ad=(dd<=CFG['weak_projection_px'])&(np.linalg.norm(cent[fi]-X,axis=1)<=CFG['weak_distance_mm'])&((n[fi]*nn).sum(1)>CFG['normal_cos'])
  for f in fi[ad]:
   # Disallow a path across observed Ring/background: 16 actual mask samples.
   line=np.linspace(s.uv[corr['index'][idx]],pu[f],16);r=np.c_[line,np.ones(16)]@np.linalg.inv(s.K).T;pts=s.C[:3,3]+(r@s.C[:3,:3].T)*pz[f]
   if s.mask_at(pts).all():out.append([idx,int(f)]);break
 return np.asarray(out,int).reshape(-1,2)

def peer_conflicts(ss,ring):
 """Conservative free-space proxy: >=2 independent direction blocks, normal and CAD qualified.
 Behind a peer surface is occlusion/unknown, never negative evidence.
 """
 grids={};norms={}
 for s in ss:
  h,w=map(int,s.o['native_shape']);grid=np.full((h,w),np.nan);normal=np.full((h,w,3),np.nan);grid[s.uv[:,1],s.uv[:,0]]=s.z0+s.A@s.theta;normal[s.uv[:,1],s.uv[:,0]]=s.normals();grids[s.id]=grid;norms[s.id]=normal
 for s in ss:
  X=s.points();n=s.normals();count=np.zeros(len(X),np.int16);used=[]
  for t in sorted(ss,key=lambda a:a.id):
   if s.id==t.id:continue
   d=t.C[:3,3]-s.C[:3,3]
   if np.linalg.norm(d)<1.:continue
   direction=t.C[:3,3]-X.mean(0);direction/=np.linalg.norm(direction)
   if any(np.dot(direction,p[0])>np.cos(np.radians(15))or len(set(t.rec['parent_sha'])&p[1])/max(1,len(set(t.rec['parent_sha'])|p[1]))>.75 for p in used):continue
   uv,z=project(X,t.C,t.K);ij=np.rint(uv).astype(int);h,w=grids[t.id].shape;inside=(ij[:,0]>=0)&(ij[:,0]<w)&(ij[:,1]>=0)&(ij[:,1]<h)&(z>0);ii=np.flatnonzero(inside);uu=ij[ii];dep=grids[t.id][uu[:,1],uu[:,0]];tn=norms[t.id][uu[:,1],uu[:,0]];good=np.isfinite(dep)&((tn*n[ii]).sum(1)>CFG['normal_cos']);ii=ii[good];dep=dep[good]
   if not len(ii):continue
   cz=raycast(ring,t.C,t.K,uv[ii])['t_hit'];violate=(z[ii]<dep-CFG['overlap_mm'])&(z[ii]<cz-.05)&(dep<cz-.05)&t.mask_at(X[ii]);count[ii[violate]]+=1;used.append((direction,set(t.rec['parent_sha'])))
  s.peer_conflict=count>=2
 return {s.id:int(s.peer_conflict.sum())for s in ss}

def geometry_score(ss,V,F,ring):
 body=scene(V,F);rows=[]
 for s in ss:
  cr=correspond(s,V,F,body,ring,full=True);active=cr['hit']&cr['known']&(cr['z']<cr['cad_z']-.05);e=np.abs(cr['z']-(s.z0+s.A@s.theta));N=len(e);pen=np.where(active,np.minimum(e,10.),10.);rows.append(dict(source=s.id,N=N,hit=int(active.sum()),matched=int(cr['matched'].sum()),unknown=int((cr['state']==3).sum()),conflict=int((cr['state']==2).sum()),unexplained=int((cr['state']==1).sum()),fixed_penalty_mm=float(pen.mean()),MAE_mm=float(e[active].mean())if active.any()else None,median_mm=float(np.median(e[active]))if active.any()else None,p95_mm=float(np.quantile(e[active],.95))if active.any()else None))
 return dict(N=sum(r['N']for r in rows),hit=sum(r['hit']for r in rows),matched=sum(r['matched']for r in rows),score=sum(s.w*r['fixed_penalty_mm']for s,r in zip(ss,rows)),sources=rows)
