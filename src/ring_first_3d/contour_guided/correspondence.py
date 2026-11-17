"""Detached visibility/assignment; calibrated projection keeps real 3D derivatives."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter,distance_transform_edt,binary_dilation

def project(V,K,C):
 cam=(V-C[:3,3])@C[:3,:3];p=cam@K.T
 return p[:,:2]/np.maximum(p[:,2:],1e-12),cam[:,2]

def project_torch(V,K,C):
 import torch
 k=torch.as_tensor(K,dtype=V.dtype,device=V.device);c=torch.as_tensor(C,dtype=V.dtype,device=V.device);a=(V-c[:3,3])@c[:3,:3];p=a@k.T
 return p[:,:2]/p[:,2:].clamp_min(1e-12)

def target_boundary(labels,max_samples=512):
 import cv2
 mask=labels==1;curves=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
 uv=np.concatenate([c[:,0]for c in curves if len(c)>2]).astype(float)if curves else np.empty((0,2))
 if len(uv)>max_samples:uv=uv[np.linspace(0,len(uv)-1,max_samples,dtype=int)]
 sd=gaussian_filter(distance_transform_edt(~mask)-distance_transform_edt(mask),1.);gy,gx=np.gradient(sd);xy=np.rint(uv).astype(int);N=np.c_[gx[xy[:,1],xy[:,0]],gy[xy[:,1],xy[:,0]]]if len(uv)else np.empty((0,2));N/=np.maximum(1e-12,np.linalg.norm(N,axis=1)[:,None]);amb=binary_dilation(labels==2,iterations=3);known=~amb[xy[:,1],xy[:,0]]if len(uv)else np.empty(0,bool)
 return uv,N,known

def explicit_pairs(body_uv,body_normals,target_uv,target_normals,target_known,config):
 """Two directions, local normal compatibility and approximate mutuality. No ellipse."""
 n=len(body_uv);m=len(target_uv)
 if not n or not m:return dict(source=np.empty(0,int),target=np.empty(0,int),direction=np.empty(0,int),accepted=np.empty(0,bool),distance=np.empty(0),normal_dot=np.empty(0),tangent=np.empty(0),reasons=np.empty(0,dtype='U32'))
 db,j=cKDTree(target_uv).query(body_uv);dt,i=cKDTree(body_uv).query(target_uv);bi=np.r_[np.arange(n),i];ti=np.r_[j,np.arange(m)];di=np.r_[np.zeros(n,int),np.ones(m,int)];delta=body_uv[bi]-target_uv[ti];distance=np.linalg.norm(delta,axis=1);normal=target_normals[ti];ndot=abs(np.einsum('ni,ni->n',body_normals[bi],normal));tangent=abs(delta[:,0]*normal[:,1]-delta[:,1]*normal[:,0]);mutual=np.linalg.norm(body_uv[bi]-body_uv[i[ti]],axis=1)<=config['mutual_radius_px'];reason=np.full(len(bi),'ACCEPTED',dtype='U32')
 for bad,label in [(~target_known[ti],'RING_BOUNDARY_UNKNOWN'),(distance>config['max_distance_px'],'OUTSIDE_CAPTURE_RANGE'),(ndot<config['normal_cos_min'],'NORMAL_DIRECTION_CONFLICT'),(tangent>config['max_tangent_px'],'TANGENTIAL_MISMATCH'),(~mutual,'NOT_MUTUALLY_CONSISTENT')]:reason[(reason=='ACCEPTED')&bad]=label
 return dict(source=bi,target=ti,direction=di,accepted=reason=='ACCEPTED',distance=distance,normal_dot=ndot,tangent=tangent,reasons=reason)

class ExplicitContour:
 def __init__(self,c,legacy,config):self.c=c;self.legacy=legacy;self.config=config;self.pairs={};self.previous={};self.records={};self.generation=0
 def rebuild(self,V):
  self.generation+=1;W=V.detach().cpu().numpy()
  for cid in self.c.fit:
   self.legacy.last.pop(cid,None);self.legacy(V,cid);s=self.legacy.last.get(cid);d=self.c.views[cid]
   if s is None:self.pairs[cid]=None;self.records[cid]=dict(candidate_N=0,accepted_N=0,reason='NO_VISIBLE_BODY_CONTOUR');continue
   eid=s['eid'];t=s['t'];P=W[eid[:,0]]*(1-t[:,None])+W[eid[:,1]]*t[:,None];uv,_=project(P,d['K'],d['T']);ends,_=project(W[eid.reshape(-1)],d['K'],d['T']);tan=ends.reshape(-1,2,2)[:,1]-ends.reshape(-1,2,2)[:,0];N=np.c_[-tan[:,1],tan[:,0]];N/=np.maximum(1e-12,np.linalg.norm(N,axis=1)[:,None]);ct,cn,known=target_boundary(d['labels']);p=explicit_pairs(uv,N,ct,cn,known,self.config);si,ti=p['source'],p['target'];keep=p['accepted'];prev=self.previous.get(cid,{});keys=[(int(eid[z,0]),int(eid[z,1]),round(float(t[z]),4),int(di))for z,di in zip(si,p['direction'])];tracked=np.array([k in prev for k in keys]);target_shift=np.array([np.linalg.norm(ct[z]-prev[k])if k in prev else np.nan for k,z in zip(keys,ti)]);self.previous[cid]={k:ct[z].copy()for k,z,ok in zip(keys,ti,keep)if ok}
   face_lookup={tuple(sorted((int(a),int(b)))):(fi,j)for fi,f in enumerate(self.c.F)for j,(a,b)in enumerate([(f[0],f[1]),(f[1],f[2]),(f[2],f[0])])};face=np.array([face_lookup.get(tuple(e),(-1,-1))[0]for e in eid[si]],int)
   arrays=dict(edge=eid[si],edge_t=t[si],face=face,body_uv=uv[si],target_uv=ct[ti],target_normal=cn[ti],body_normal=N[si],normal_residual_px=np.einsum('ni,ni->n',uv[si]-ct[ti],cn[ti]),tracked=tracked,target_tracking_shift_px=target_shift,**p)
   self.pairs[cid]=arrays;reasons={x:int((p['reasons']==x).sum())for x in np.unique(p['reasons'])};self.records[cid]=dict(candidate_N=len(si),accepted_N=int(keep.sum()),rejections=reasons,bidir_distance_mean_px=[float(p['distance'][p['direction']==z].mean())for z in [0,1]],normal_MAE_px=float(abs(arrays['normal_residual_px'][keep]).mean())if keep.any()else None,tracked_N=int((tracked&keep).sum()))
 def __call__(self,V,cid):
  import torch
  p=self.pairs.get(cid)
  if p is None or not p['accepted'].any():return V.sum()*0
  ok=p['accepted'];e=torch.as_tensor(p['edge'][ok],dtype=torch.long,device=V.device);t=torch.as_tensor(p['edge_t'][ok],dtype=V.dtype,device=V.device);target=torch.as_tensor(p['target_uv'][ok],dtype=V.dtype,device=V.device);n=torch.as_tensor(p['target_normal'][ok],dtype=V.dtype,device=V.device);P=V[e[:,0]]*(1-t[:,None])+V[e[:,1]]*t[:,None];uv=project_torch(P,self.c.views[cid]['K'],self.c.views[cid]['T']);r=((uv-target)*n).sum(1)/20.;h=torch.where(abs(r)<1,.5*r*r,abs(r)-.5);di=p['direction'][ok];parts=[h[torch.as_tensor(di==z,device=V.device)].mean()for z in [0,1]if (di==z).any()];return sum(parts)/len(parts)
