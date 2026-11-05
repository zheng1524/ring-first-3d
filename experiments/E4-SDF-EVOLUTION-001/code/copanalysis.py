"""Narrow phase for pre-existing broad-phase coplanar warnings; no fit edits."""
from inputs import *
from scipy.spatial import cKDTree
def inspect_coplanar(V,F):
    t=V[F];c=t.mean(1);r=np.linalg.norm(t-c[:,None],axis=2).max();p=cKDTree(c).query_pairs(2*r,output_type='ndarray');i,j=p.T;shared=(F[i,:,None]==F[j,None,:]).any((1,2));box=(t[i].min(1)<=t[j].max(1)+1e-9).all(1)&(t[j].min(1)<=t[i].max(1)+1e-9).all(1);p=p[~shared&box];A=t[p[:,0]];B=t[p[:,1]];na=np.cross(A[:,1]-A[:,0],A[:,2]-A[:,0]);nb=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);na/=np.maximum(np.linalg.norm(na,axis=1)[:,None],1e-15);nb/=np.maximum(np.linalg.norm(nb,axis=1)[:,None],1e-15);keep=(abs((na*nb).sum(1))>1-1e-9)&(abs(((B[:,0]-A[:,0])*na).sum(1))<1e-8);rows=[]
    for pair,a,b,n in zip(p[keep],A[keep],B[keep],na[keep]):
        k=np.argmax(abs(n));aa=np.delete(a,k,axis=1);bb=np.delete(b,k,axis=1);area,poly=cv2.intersectConvexConvex(aa.astype(np.float32),bb.astype(np.float32));rows.append(dict(faces=pair,projected_intersection_area_mm2=float(area),A_mm=a,B_mm=b,method='OpenCV intersectConvexConvex float32, narrow-phase projected triangle area',resolution='NO_POSITIVE_AREA_INTERSECTION_DETECTED'if area==0 else'UNRESOLVED_POSITIVE_AREA'))
    return rows
