"""Exact original torus apparent-contour equations; camera-dependent tangent locus."""
from ucommon import *
import torch
from torch.func import jacfwd
D=torch.float64;torch.set_num_threads(1)
S=np.r_[np.full(3,.6),np.full(3,np.deg2rad(5))]
def tt(x):return torch.as_tensor(np.asarray(x),dtype=D)
def skew(v):
 z=v[0]*0;x,y,w=v.unbind();return torch.stack([z,-w,y,w,z,-x,-y,x,z]).reshape(3,3)
def exp_t(q):
 xi=q*tt(S);A=torch.cat([torch.cat([skew(xi[3:]),xi[:3,None]],1),torch.zeros((1,4),dtype=D)],0);return torch.matrix_exp(A)
def exp(q):return exp_t(tt(q)).numpy()
def pose_t(q,RF,H0):return exp_t(q[6:])@tt(H0)@exp_t(q[:6])@tt(RF)
def canonical_t(C):
 a=-torch.atan2(C[1,3],C[0,3]);c,s=a.cos(),a.sin();z=a*0;o=z+1;G=torch.stack([c,-s,z,z,s,c,z,z,z,z,o,z,z,z,z,o]).reshape(4,4);return G@C

def torus_uv_t(C,K,theta,branch,R=5.6,r=.6,canonical=True):
 if canonical:C=canonical_t(C)
 th=tt(theta);br=tt(branch);a=C[0,3]*th.cos()+C[1,3]*th.sin()-R;b=C[2,3];ll=(a*a+b*b).sqrt();phi=torch.atan2(b,a)+br*torch.acos(r/ll)
 X=torch.stack([(R+r*phi.cos())*th.cos(),(R+r*phi.cos())*th.sin(),r*phi.sin()],-1);p=(X-C[:3,3])@C[:3,:3];q=p@tt(K).T;return q[:,:2]/q[:,2:]
def curves(C,K,n=1024):
 a=-np.arctan2(C[1,3],C[0,3]);G0=np.eye(4);G0[:3,:3]=Rotation.from_euler('z',a).as_matrix();Cc=G0@C;uv=torus_original(Cc[:3,3],Cc[:3,:3],K,n=n);th=np.arange(n)*2*np.pi/n
 aa=Cc[0,3]*np.cos(th)+Cc[1,3]*np.sin(th)-5.6;bb=Cc[2,3];ll=np.hypot(aa,bb);phi=np.arctan2(bb,aa)[None]+np.array([-1,1])[:,None]*np.arccos(.6/ll)[None];X=np.stack([(5.6+.6*np.cos(phi))*np.cos(th),(5.6+.6*np.cos(phi))*np.sin(th),.6*np.sin(phi)],-1)@G0[:3,:3]
 ar=[abs(cv2.contourArea(p.astype(np.float32)))for p in uv];return dict(inner=uv[int(np.argmin(ar))],outer=uv[int(np.argmax(ar))],branches=dict(inner=int(np.argmin(ar)),outer=int(np.argmax(ar))),X=X,uv=uv,th=th)

def nearest(obs,curve):
 a=curve;b=np.roll(curve,-1,axis=0);v=b-a;allidx=[];allt=[];dist=[]
 for s in range(0,len(obs),128):
  dd=obs[s:s+128,None]-a[None];t=np.clip((dd*v[None]).sum(-1)/np.maximum((v*v).sum(-1),1e-20),0,1);e=((dd-t[...,None]*v[None])**2).sum(-1);j=e.argmin(1);i=np.arange(len(j));allidx.extend(j);allt.extend(t[i,j]);dist.extend(np.sqrt(e[i,j]))
 return np.array(allidx),np.array(allt),np.array(dist)
def correspondence(C,K,observations,n=1024):
 cr=curves(C,K,n);theta=[];branch=[];uv=[];channel=[]
 for name in ['inner','outer']:
  ob=observations[name];j,t,d=nearest(ob,cr[name]);theta.extend((j+t)*2*np.pi/n);branch.extend(np.full(len(j),[-1,1][cr['branches'][name]]));uv.extend(ob);channel.extend([name]*len(j))
 return dict(theta=np.array(theta),branch=np.array(branch),observed=np.array(uv).reshape(-1,2),channel=channel)
def robust(r,J=None,weight=1.):
 # Vector Huber with delta1. Maps norm-squared to exactly2Huber, not an IRLS approximation.
 n=np.maximum(np.linalg.norm(r,axis=1),1e-14);h=n>1;s=np.ones(len(r));s[h]=np.sqrt(2*n[h]-1)/n[h];res=r*s[:,None]*np.sqrt(weight)
 if J is None:return res.reshape(-1)
 ds=np.zeros(len(r));ds[h]=1/(n[h]*np.sqrt(2*n[h]-1))-np.sqrt(2*n[h]-1)/n[h]**2;A=s[:,None,None]*np.eye(2)[None]+(ds/n)[:,None,None]*r[:,:,None]*r[:,None,:];return res.reshape(-1),(np.einsum('nij,njk->nik',A,J)*np.sqrt(weight)).reshape(2*len(r),-1)
class PoseCache:
 def __init__(self,RF,H0):self.RF=np.array(RF);self.H0=np.array(H0);self.key=None;self.last=None
 def get(self,local,H,derivative=False):
  q=np.r_[local,H]
  if self.key is None or not np.array_equal(q,self.key):self.key=q.copy();self.last=[pose_t(tt(q),self.RF,self.H0).numpy(),None]
  if derivative and self.last[1]is None:self.last[1]=jacfwd(lambda x:pose_t(x,self.RF,self.H0))(tt(q)).numpy()
  return self.last

def project_dC(X,C,K,dC=None):
 p=(X-C[:3,3])@C[:3,:3];q=p@K.T;uv=q[:2]/q[2]
 A=(K[:2]*q[2]-q[:2,None]*K[2])/q[2]**2
 JX=A@C[:3,:3].T
 if dC is None:return uv,JX,p[2]
 dp=np.einsum('i,ijd->jd',X-C[:3,3],dC[:3,:3])-C[:3,:3].T@dC[:3,3];return uv,A@dp,JX,p[2]
