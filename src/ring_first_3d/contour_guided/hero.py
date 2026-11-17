"""Non-ellipse observed-boundary → actual apparent contour → visible Mesh faces."""
import numpy as np
from scipy.spatial import cKDTree
import types
from .correspondence import project,target_boundary,explicit_pairs
from ..multisurface.geometry import scene,cast,transform
from ..multisurface import registration as inherited

CONFIG=dict(max_distance_px=40.,mutual_radius_px=4.,max_tangent_px=8.,normal_cos_min=0.7071067811865476)

def visible_contour(V,F,K,C,labels,ring):
 tri=V[F];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);front=np.einsum('ij,ij->i',n,C[:3,3]-tri.mean(1))>0;e=np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1);fi=np.tile(np.arange(len(F)),3);edges,inv=np.unique(e,axis=0,return_inverse=True);adj=np.full((len(edges),2),-1,int)
 for i,k in enumerate(inv):adj[k,0 if adj[k,0]<0 else 1]=fi[i]
 choose=(adj[:,1]<0)|(front[adj[:,0]]!=front[np.maximum(adj[:,1],0)]);edges=edges[choose];faces=adj[choose,0];edges=np.repeat(edges,3,axis=0);faces=np.repeat(faces,3);t=np.tile([.2,.5,.8],len(faces)//3);P=V[edges[:,0]]*(1-t[:,None])+V[edges[:,1]]*t[:,None];uv,z=project(P,K,C);ends,_=project(V[edges.reshape(-1)],K,C);tangent=ends.reshape(-1,2,2)[:,1]-ends.reshape(-1,2,2)[:,0];normal=np.c_[-tangent[:,1],tangent[:,0]];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12);H,W=labels.shape;good=(z>0)&np.isfinite(uv).all(1)&(uv[:,0]>=0)&(uv[:,0]<W)&(uv[:,1]>=0)&(uv[:,1]<H);safe=np.nan_to_num(uv,nan=-10000,posinf=10000,neginf=-10000);zs,_,_=cast(scene(V,F),safe,K,C);zr,_,_=cast(scene(ring['V'],ring['F']),safe,K,C);tol=max(.02,.002*np.ptp(V,axis=0).max());good&=(~np.isfinite(zs)|(zs>=z-tol))&(zr>=z-.05)
 return dict(uv=uv[good],normal=normal[good],edge=edges[good],edge_t=t[good],face=faces[good])

def mesh_candidates(uv,body,K,C,labels,ring,config=CONFIG):
 import cv2
 contour=visible_contour(body['V'],body['F'],K,C,labels,ring);ct,cn,known=target_boundary(labels);p=explicit_pairs(contour['uv'],contour['normal'],ct,cn,known,config);accepted=p['accepted'];N=len(uv);mapped=np.array(uv,float);confidence=np.zeros(N);why=np.full(N,'NO_ACCEPTED_CONTOUR_REGION',dtype='U40');support=np.full(N,-1,int)
 if accepted.any():
  ti=p['target'][accepted];bi=p['source'][accepted];O=ct[ti];B=contour['uv'][bi];distance,ix=cKDTree(O).query(uv,k=min(4,len(O)));distance=np.asarray(distance).reshape(N,-1);ix=np.asarray(ix).reshape(N,-1);w=1/np.maximum(distance,1.)**2;w/=w.sum(1)[:,None];mapped+=np.einsum('nk,nkj->nj',w,(B-O)[ix]);support=p['source'][accepted][ix[:,0]];confidence=np.full(N,float(np.exp(-p['distance'][accepted].mean()/40.)*p['normal_dot'][accepted].mean()));why[:]='VISIBLE_MESH_REGION_CANDIDATE'
 z,face,bary=cast(scene(body['V'],body['F']),mapped,K,C);zr,_,_=cast(scene(ring['V'],ring['F']),mapped,K,C);H,W=labels.shape;within=(mapped[:,0]>=0)&(mapped[:,0]<W)&(mapped[:,1]>=0)&(mapped[:,1]<H);valid=np.isfinite(z)&(z>0)&(z<=zr+.05)&within&(support>=0);Q=np.full((N,3),np.nan);Q[valid]=np.einsum('ni,nij->nj',bary[valid],body['V'][body['F'][face[valid]]]);confidence[~valid]=0;why[(support>=0)&~valid]='NO_VISIBLE_BODY_FACE_OR_RING';contact=cv2.dilate((labels==2).astype(np.uint8),np.ones((3,3),np.uint8))[np.clip(uv[:,1].astype(int),0,H-1),np.clip(uv[:,0].astype(int),0,W-1)]>0
 return dict(points=Q,face=face,bary=bary,mapped_uv=mapped,confidence=confidence,valid=valid,reason=why,contact=contact,boundary_candidate_N=len(accepted),boundary_accepted_N=int(accepted.sum()),boundary_body_uv=contour['uv'][p['source']],boundary_target_uv=ct[p['target']],boundary_accepted=accepted,boundary_reason=p['reasons'],boundary_edge=contour['edge'][p['source']],boundary_edge_t=contour['edge_t'][p['source']],boundary_face=contour['face'][p['source']],support_contour_sample=support)

def mapping_constraints(task,data,body,fits,X,unused):
 cfg=task['fusion'];out=[];ring=body['ring'];config=task.get('contour',CONFIG)
 for i,d in enumerate(data):
  take=np.linspace(0,len(d['V'])-1,min(cfg['registration_samples_per_view'],len(d['V'])),dtype=int);uv=d['uv'][take];P=d['V'][take];inv=np.linalg.inv(X[i]);pre=dict(V=transform(body['V'],inv),F=body['F']);prering=dict(V=transform(ring['V'],inv),F=ring['F']);m=mesh_candidates(uv,pre,d['K'],d['C'],d['labels'],prering,config);target=transform(m['points'],X[i]);dist=np.linalg.norm(transform(P,X[i])-target,axis=1);keep=m['valid']&~m['contact']&(m['confidence']>=cfg['candidate_confidence_min'])&(dist<=cfg['candidate_reject_distance_mm']);out.append(dict(i=i,P=P[keep],Q=target[keep],weight=m['confidence'][keep],target_N=len(P),accepted_N=int(keep.sum()),contact_unknown_N=int(m['contact'].sum()),original_uv=uv,mapped_uv=m['mapped_uv'],face=m['face'],bary=m['bary'],confidence=m['confidence'],accepted=keep,raw_source_points=P,candidate_points=target,**{k:v for k,v in m.items()if k.startswith('boundary_')or k in ['reason','support_contour_sample']}))
 return out

def optimizer(provider=mapping_constraints):
 scope=dict(inherited.optimize.__globals__);scope['mapping_constraints']=provider
 return types.FunctionType(inherited.optimize.__code__,scope,inherited.optimize.__name__,inherited.optimize.__defaults__,inherited.optimize.__closure__)
