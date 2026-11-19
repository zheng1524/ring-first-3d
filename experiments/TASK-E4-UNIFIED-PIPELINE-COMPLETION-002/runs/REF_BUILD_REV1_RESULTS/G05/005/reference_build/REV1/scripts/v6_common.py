from pathlib import Path
import sys,os,json,datetime,ast,hashlib
R=Path(__file__).resolve().parents[1];E=R.parent;REPO=E.parent.parent;V5=E/'ring_first_v5_geometry_crossvideo';V4=E/'surface_reconstruction_v4';F1=E/'surface_fusion_v1';F2=E/'surface_fusion_v2';F3=E/'surface_fusion_v3';DXY=Path('/home/liu/new-polyp-dxy')
sys.path.insert(0,str(V5/'scripts'));import g5_common as previous
import numpy as np,cv2,trimesh
from scipy.optimize import least_squares,minimize_scalar
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
sha,clean,stats=previous.sha,previous.clean,previous.stats
K=previous.K.copy();project,unproject=previous.project,previous.unproject
cast,o3scene=previous.cast,previous.o3scene
ring_residual=previous.torus_residual;contours=previous.contour_project
extract=previous.extract

def save(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False))
def load(p):return json.loads((R/p).read_text())
def cfg():return load('config.json')
def ledger():return load('inputs/ledger005.json')
def freeze(n,ps):save('metrics/freeze_'+n+'.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files={str(Path(p).resolve()):sha(p) for p in sorted(set(map(Path,ps)))},GT_selection=False,historical_measurement_fallback=0))
def verify(n):
 x=load('metrics/freeze_'+n+'.json');assert all(sha(p)==h for p,h in x['files'].items()),n

def image(a):return cv2.imread(a['RGB_path'])[:,:,::-1].copy()
def labels(a):return cv2.imread(a['Mask_path'],0)
def obs(id):return dict(np.load(R/f'observations/{id}_ring.npz'))
def positive_gauge(po):
 p=po.copy()
 if p[2,3]<0:
  T=np.eye(4);T[:3,:3]=Rotation.from_euler('x',np.pi).as_matrix();p=T@p
 return p

def spin(p,t):
 T=np.eye(4);T[:3,:3]=Rotation.from_euler('z',t).as_matrix();return T@p

def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)

def triangle(poses,uvs,K0=K):
 A=[]
 for po,uv in zip(poses,uvs):
  P=np.linalg.inv(po)[:3];v=np.linalg.inv(K0)@np.r_[uv,1.];A.extend([v[0]*P[2]-P[0],v[1]*P[2]-P[1]])
 _,_,v=np.linalg.svd(A);return v[-1,:3]/v[-1,3]

def depth_mesh(z,mask,po,rgb):
 valid=mask&np.isfinite(z)&(z>0);y,x=np.nonzero(valid);P=unproject(z[valid],po,np.c_[x,y],K);ids=np.full(z.shape,-1,int);ids[valid]=np.arange(len(P));faces=[]
 for a in [np.stack([ids[:-1,:-1],ids[:-1,1:],ids[1:,:-1]],-1),np.stack([ids[:-1,1:],ids[1:,1:],ids[1:,:-1]],-1)]:
  t=a[(a>=0).all(2)];t=t[np.ptp(z[valid][t],axis=1)<=.75];faces.extend(t)
 return trimesh.Trimesh(P,np.array(faces,int).reshape(-1,3),vertex_colors=np.c_[rgb[valid],np.full(len(P),255)],process=False)
