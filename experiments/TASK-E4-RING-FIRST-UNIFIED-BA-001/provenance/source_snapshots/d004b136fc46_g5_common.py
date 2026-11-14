from pathlib import Path
import os,sys,json,ast,hashlib,datetime
R=Path(__file__).resolve().parents[1]; E=R.parent; REPO=E.parent.parent; PRIOR=E/'surface_reconstruction_v4'; F3=E/'surface_fusion_v3'; F2=E/'surface_fusion_v2'; F1=E/'surface_fusion_v1'; SYN=E/'ring_first_v4_synthetic_audit'; DXY=Path('/home/liu/new-polyp-dxy')
sys.path.insert(0,str(PRIOR/'scripts'));import v4_common as old
import numpy as np,cv2,trimesh
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares, minimize_scalar
prev=old.prev
sha,stats,clean=old.sha,old.stats,old.clean
cast,o3scene,project,unproject,depth_mesh=old.cast,old.o3scene,old.project,old.unproject,old.depth_mesh
K=old.K.copy()
def save(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False))
def load(p):return json.loads((R/p).read_text())
def freeze(n,ps):save('metrics/freeze_'+n+'.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files={str(Path(p).resolve()):sha(p) for p in sorted(set(map(Path,ps)))},GT_selected_parameters=False,historical_measurement_fallback=0))
def verify(n):
 a=load('metrics/freeze_'+n+'.json');assert all(sha(p)==h for p,h in a['files'].items()),n

def cfg():return load('config.json')
def ledger():return load('inputs/ledger.json')
def image(a):return cv2.imread(a['RGB_path'])[:,:,::-1].copy()
def labels(a):return cv2.imread(a['Mask_path'],0)
def extract(path,names,ns):
 for node in ast.parse(Path(path).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
 return ns
GEO=extract(REPO/'ring_anchor_3d/scripts/geometry.py',['torus_contours'],dict(np=np,cv2=cv2));contours=GEO['torus_contours']
def contour_project(pose,n=256,K0=K):return contours(pose[:3,3],pose[:3,:3],K0,R=5.6,r=.6,n=n)
def torus_residual(pose,ob,part='train',K0=K):
 from matplotlib.path import Path as Poly
 q=ob['q_'+part];p=ob['p_'+part];b=ob['b_'+part]
 try:
  cr=contour_project(pose,256,K0);assert np.isfinite(cr).all();areas=[abs(cv2.contourArea(x.astype(np.float32))) for x in cr];i=np.argmax(areas);a,bcr=Poly(cr[i]),Poly(cr[1-i]);inside=lambda uv:a.contains_points(uv)&~bcr.contains_points(uv);tree=cKDTree(cr.reshape(-1,2));dq=tree.query(q)[0];dp=tree.query(p)[0]*(~inside(p));db=tree.query(b)[0]*inside(b);return np.r_[dq,dp*np.sqrt(len(q)/max(1,len(p))),db*np.sqrt(len(q)/max(1,len(b)))]
 except (ValueError,AssertionError):return np.full(len(q)+len(p)+len(b),1000.)
def obs(id):return dict(np.load(R/f'observations/{id}.npz'))
def torus_sdf(X):return np.sqrt((np.linalg.norm(X[:,:2],axis=1)-5.6)**2+X[:,2]**2)-.6
