"""Exact piecewise-linear halfspace clipping. No refitting, rescaling, or smoothing."""
from common import *
from planes import normalize

def basis(n):
 x=np.eye(3)[np.argmin(abs(n))];u=np.cross(n,x);u/=np.linalg.norm(u);return np.c_[u,np.cross(n,u)]

def ear_clip(ids,xy):
 ids=list(ids);q=xy[ids];area=np.cross(q,np.roll(q,-1,axis=0)).sum()/2
 if area>0:ids.reverse()
 tris=[];budget=len(ids)**2
 def cross(a,b):return a[0]*b[1]-a[1]*b[0]
 while len(ids)>3:
  found=False
  for j in range(len(ids)):
   a,b,c=ids[j-1],ids[j],ids[(j+1)%len(ids)];A,B,C=xy[[a,b,c]]
   if cross(B-A,C-B)>=-1e-12:continue
   others=[v for v in ids if v not in[a,b,c]];Q=xy[others]
   inside=(np.array([cross(B-A,x-A)for x in Q])<=1e-11)&(np.array([cross(C-B,x-B)for x in Q])<=1e-11)&(np.array([cross(A-C,x-C)for x in Q])<=1e-11)
   if inside.any():continue
   tris.append([a,b,c]);ids.pop(j);found=True;break
  budget-=1
  if not found or budget<=0:raise ValueError('CAP_EAR_CLIPPING_FAILED_no_geometry_repair')
 if len(ids)==3:tris.append(ids)
 return tris

def clip(V,F,plane):
 V=np.asarray(V,float);F=np.asarray(F,int);plane=normalize(plane);d=V@plane[:3]+plane[3];P=V.tolist();orig=list(range(len(V)));edges=[[-1,-1]for _ in V];new={};out=[];faceids=[]
 def intersection(a,b):
  if abs(d[a])<1e-10:return int(a)
  if abs(d[b])<1e-10:return int(b)
  key=tuple(sorted([int(a),int(b)]))
  if key not in new:
   t=d[a]/(d[a]-d[b]);x=V[a]+t*(V[b]-V[a]);new[key]=len(P);P.append(x.tolist());orig.append(-1);edges.append(list(key))
  return new[key]
 for fid,f in enumerate(F):
  poly=[]
  for i in range(3):
   a,b=int(f[i]),int(f[(i+1)%3]);ia=d[a]>=-1e-10;ib=d[b]>=-1e-10
   if ia:poly.append(a)
   if ia!=ib:poly.append(intersection(a,b))
  poly=list(dict.fromkeys(poly))
  for i in range(1,len(poly)-1):
   tri=[poly[0],poly[i],poly[i+1]]
   if np.linalg.norm(np.cross(np.array(P[tri[1]])-P[tri[0]],np.array(P[tri[2]])-P[tri[0]]))>1e-12:out.append(tri);faceids.append(fid)
 if not out:raise ValueError('CLIP_REMOVED_ENTIRE_BODY')
 Fup=np.array(out,int);used=np.unique(Fup);remap=np.full(len(P),-1,int);remap[used]=np.arange(len(used));P=np.asarray(P)[used];origin=np.asarray(orig)[used];edge=np.asarray(edges)[used];Fup=remap[Fup]
 counts={};direct={}
 for tri in Fup:
  for a,b in zip(tri,np.roll(tri,-1)):
   key=tuple(sorted([a,b]));counts[key]=counts.get(key,0)+1;direct[key]=(int(a),int(b))
 boundary=[direct[k]for k,v in counts.items()if v==1];loops=[];pending=set(boundary)
 while pending:
  a,b=next(iter(pending));loop=[a];pending.remove((a,b));cursor=b
  while cursor!=a:
   loop.append(cursor);nexts=[v for u,v in pending if u==cursor]
   if len(nexts)!=1:raise ValueError('NONMANIFOLD_CUT_BOUNDARY')
   nex=nexts[0];pending.remove((cursor,nex));cursor=nex
  loops.append(loop)
 if len(loops)>1:raise ValueError('MULTIPLE_CUT_LOOPS_REQUIRE_AUDIT_no_hole_fill')
 caps=[];xy=P@basis(plane[:3])
 for loop in loops:caps.extend(ear_clip(loop,xy))
 full=np.r_[Fup,np.array(caps,int).reshape(-1,3)];flag=np.arange(len(full))>=len(Fup);boundarymask=np.zeros(len(P),bool)
 for loop in loops:boundarymask[loop]=True
 result=dict(V=P,F=Fup,F_solid=full,inferred_base_faces=flag,boundary_vertex=boundarymask,original_vertex_ID=origin,intersection_original_edge_ID=edge,original_face_ID=np.r_[faceids,[-1]*len(caps)],plane=plane)
 above=(V[F]@plane[:3]+plane[3]>=-1e-10).all(1);kept=set(faceids);assert all(i in kept for i in np.flatnonzero(above));assert np.array_equal(P[origin>=0],V[origin[origin>=0]])
 return result
