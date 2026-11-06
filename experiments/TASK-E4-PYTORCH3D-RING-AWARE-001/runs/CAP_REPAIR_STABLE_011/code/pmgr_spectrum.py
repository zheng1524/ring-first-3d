from common import *
from scipy import sparse
def laplace(V,F):
    tri=V[F];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1)/2
    assert area.min()>1e-9
    I=[];J=[];W=[]
    for k in range(3):
        a=tri[:,(k+1)%3]-tri[:,k];b=tri[:,(k+2)%3]-tri[:,k];w=(a*b).sum(1)/(4*area)
        i=F[:,(k+1)%3];j=F[:,(k+2)%3];I.extend([i,j]);J.extend([j,i]);W.extend([w,w])
    A=sparse.coo_matrix((np.concatenate(W),(np.concatenate(I),np.concatenate(J))),shape=(len(V),len(V))).tocsr()
    L=sparse.diags(np.asarray(A.sum(1)).ravel())-A;mass=np.bincount(F.ravel(),weights=np.repeat(area/3,3),minlength=len(V))
    return L,mass,area
