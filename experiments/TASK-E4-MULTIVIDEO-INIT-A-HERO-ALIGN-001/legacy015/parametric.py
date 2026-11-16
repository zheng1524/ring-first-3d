"""Existing ellipsoid/star and finite-support height family. No morphology dispatch."""
from common import *
from scipy.spatial.transform import Rotation
ICO=trimesh.creation.icosphere(subdivisions=3);SP=np.array(ICO.vertices);SF=np.array(ICO.faces)
def harmonic3(n):
 x,y,z=n.T;return np.c_[x*(x*x-3*y*y),y*(3*x*x-y*y),z*(x*x-y*y),x*y*z,x*(5*z*z-1),y*(5*z*z-1),z*(5*z*z-3)]
def decode_ellipsoid(p,Q0):return p[:3],Q0@Rotation.from_rotvec(p[3:6]).as_matrix(),np.exp(p[6:9])
def initial_parameters(V):
 c=V.mean(0);w,Q=np.linalg.eigh((V-c).T@(V-c)/len(V));order=np.argsort(w)[::-1];Q=Q[:,order]
 if np.linalg.det(Q)<0:Q[:,2]*=-1
 axes=np.sqrt(np.maximum(w[order]*3,.01));return np.r_[c,np.zeros(3),np.log(axes)],Q

def body(p,meta):
 family=meta['family']
 if family in['ellipsoid','star']:
  c,Q,a=decode_ellipsoid(p,np.array(meta['Q0']));P=SP.copy()
  if family=='star':P*=np.exp(.2*np.tanh(harmonic3(P)@p[9:]))[:,None]
  return P*a@Q.T+c,SF,SF,np.zeros(len(SF),bool)
 # Cap footprint and retained height are optimized directly; no hidden full ellipsoid axis.
 Q=np.array(meta['base_Q']);anchor=np.array(meta['anchor']);rot=Rotation.from_rotvec([0,0,p[5]]).as_matrix();Q=Q@rot;center=anchor+Q[:,:2]@p[:2];a,b,h=np.exp(p[2:5]);gamma=.5 if meta.get('stage')=='C0'else p[6];skew=np.zeros(2)if len(p)<9 else p[7:9];nt=48;nr=12;theta=np.arange(nt)*2*np.pi/nt;P=[np.array([[0.,0.,h]])];F=[]
 for j in range(1,nr+1):
  r=j/nr;x=a*r*np.cos(theta);y=b*r*np.sin(theta);height=h*np.maximum(0,1-r*r)**gamma*np.exp(skew[0]*x/a+skew[1]*y/b);P.append(np.c_[x,y,height])
 P=np.concatenate(P)
 for j in range(nt):F.append([0,1+j,1+(j+1)%nt])
 for k in range(nr-1):
  s=1+k*nt;t=s+nt
  for j in range(nt):v=(j+1)%nt;F.extend([[s+j,t+j,t+v],[s+j,t+v,s+v]])
 upper=np.array(F,int);bottom=len(P);P=np.r_[P,[[0,0,0]]];s=1+(nr-1)*nt
 for j in range(nt):F.append([s+j,bottom,s+(j+1)%nt])
 full=np.array(F,int);flag=np.zeros(len(full),bool);flag[len(upper):]=True;return P@Q.T+center,upper,full,flag

def signed_body(P,p,meta):
 if meta['family']in['ellipsoid','star']:
  c,Q,a=decode_ellipsoid(p,np.array(meta['Q0']));q=(P-c)@Q/a;r=np.linalg.norm(q,axis=1);factor=np.ones(len(P))
  if meta['family']=='star':factor=np.exp(.2*np.tanh(harmonic3(q/np.maximum(r[:,None],1e-12))@p[9:]))
  return(r-factor)*a.min()
 Q=np.array(meta['base_Q'])@Rotation.from_rotvec([0,0,p[5]]).as_matrix();center=np.array(meta['anchor'])+Q[:,:2]@p[:2];q=(P-center)@Q;a,b,h=np.exp(p[2:5]);r2=(q[:,0]/a)**2+(q[:,1]/b)**2;gamma=.5 if meta.get('stage')=='C0'else p[6];skew=np.zeros(2)if len(p)<9 else p[7:9];height=h*np.maximum(0,1-r2)**gamma*np.exp(np.clip(skew[0]*q[:,0]/a+skew[1]*q[:,1]/b,-10,10));return np.maximum.reduce([(r2-1)*min(a,b),q[:,2]-height,-q[:,2]])
def torus_sdf(P,Rmid,wire):return np.sqrt((np.linalg.norm(P[:,:2],axis=1)-Rmid)**2+P[:,2]**2)-wire
