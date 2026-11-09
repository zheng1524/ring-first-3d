from common import *
from scipy import sparse
def self_intersections(V,F):
    t=V[F];cent=t.mean(1);r=np.linalg.norm(t-cent[:,None],axis=2).max();pairs=cKDTree(cent).query_pairs(2*r,output_type='ndarray')
    if not len(pairs):return dict(intersections=0,coplanar_candidates=0)
    i,j=pairs.T;shared=(F[i,:,None]==F[j,None,:]).any((1,2));box=(t[i].min(1)<=t[j].max(1)+1e-9).all(1)&(t[j].min(1)<=t[i].max(1)+1e-9).all(1);i=i[~shared&box];j=j[~shared&box];A=t[i];B=t[j];found=np.zeros(len(A),bool)
    for a,b in [(A,B),(B,A)]:
        e1=b[:,1]-b[:,0];e2=b[:,2]-b[:,0]
        for k in range(3):
            o=a[:,k];d=a[:,(k+1)%3]-o;p=np.cross(d,e2);det=(e1*p).sum(1);good=abs(det)>1e-10;inv=np.zeros(len(det));inv[good]=1/det[good];s=o-b[:,0];u=(s*p).sum(1)*inv;q=np.cross(s,e1);v=(d*q).sum(1)*inv;tt=(e2*q).sum(1)*inv
            found|=good&(u>1e-7)&(v>1e-7)&(u+v<1-1e-7)&(tt>1e-7)&(tt<1-1e-7)
    # Near-coplanar overlapping AABBs are unresolved warnings, not certified
    # intersections. Conservative candidate rejection includes these warnings.
    na=np.cross(A[:,1]-A[:,0],A[:,2]-A[:,0]);nb=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);na/=np.maximum(np.linalg.norm(na,axis=1)[:,None],1e-15);nb/=np.maximum(np.linalg.norm(nb,axis=1)[:,None],1e-15)
    cop=(abs((na*nb).sum(1))>1-1e-9)&(abs(((B[:,0]-A[:,0])*na).sum(1))<1e-8)
    cop_found=0
    for axis in range(3):
        select=cop&(np.argmax(abs(na),axis=1)==axis)
        if not select.any():continue
        axes=[k for k in range(3)if k!=axis];aa=A[select][:,:,axes];bb=B[select][:,:,axes];hit=np.ones(len(aa),bool)
        for tri in[aa,bb]:
            for k in range(3):
                e=tri[:,(k+1)%3]-tri[:,k];normal=np.c_[-e[:,1],e[:,0]];pa=np.einsum('nvc,nc->nv',aa,normal);pb=np.einsum('nvc,nc->nv',bb,normal);overlap=np.minimum(pa.max(1),pb.max(1))-np.maximum(pa.min(1),pb.min(1));hit&=overlap>1e-9*np.linalg.norm(normal,axis=1)
        cop_found+=int(hit.sum())
    return dict(intersections=int(found.sum())+cop_found,proper_crossings=int(found.sum()),coplanar_intersections=cop_found,coplanar_candidates=int(cop.sum()))
