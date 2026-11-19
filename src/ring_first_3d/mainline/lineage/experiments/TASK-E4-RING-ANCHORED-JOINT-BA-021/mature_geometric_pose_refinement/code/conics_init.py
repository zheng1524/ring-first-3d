"""Execute upstream estimate_pose unchanged; explicit -Z=>OpenCV and yaw gauge adaptation."""
from gcommon import *
import ast,itertools
SRC=M/'vendor/conics/conics/_conic.py';tree=ast.parse(SRC.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='estimate_pose');ns=dict(np=np,itertools=itertools);exec(compile(ast.Module(body=[node],type_ignores=[]),str(SRC),'exec'),ns);estimate_pose=ns['estimate_pose']

def ellipse_matrix(e):
 c,s=np.cos(np.deg2rad(e['angle_deg'])),np.sin(np.deg2rad(e['angle_deg']));A=np.array([[c,-s],[s,c]])@np.diag([1/e['major_radius']**2,1/e['minor_radius']**2])@np.array([[c,s],[-s,c]]);center=np.array([e['cx'],e['cy']]);E=np.zeros((3,3));E[:2,:2]=A;E[:2,2]=-A@center;E[2,:2]=E[:2,2];E[2,2]=center@A@center-1;return E

def align(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=float(a@b)
 if c<-1+1e-10:
  u=np.eye(3)[np.argmin(abs(a))];u-=a*(u@a);return Rotation.from_rotvec(u/np.linalg.norm(u)*np.pi).as_matrix()
 A=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0.]])
 return np.eye(3)+A+A@A/max(1+c,1e-15)

def candidates(e,K,r,Cgauge):
 E=ellipse_matrix(e);Q=K.T@E@K;Q=(Q+Q.T)/2;R,t,n,c,s1,s2,s3,mask=estimate_pose(Q,r,0.);out=[];R0=Cgauge[:3,:3].T
 for j in np.flatnonzero(mask):
  center=-c[j,:,0];normal=n[j,:,0]
  for sign in [1,-1]:
   N=sign*normal;RR=align(R0[:,2],N)@R0;C=np.eye(4);C[:3,:3]=RR.T;C[:3,3]=-RR.T@center
   if center[2]<=0 or not np.isfinite(C).all():continue
   if any(np.linalg.norm(C-a['C'])<1e-6 for a in out):continue
   out.append(dict(C=C,official_solution_index=int(j),official_mask=True,official_n=normal,official_c_negativeZ=c[j,:,0],opencv_circle_center_positiveZ=center,normal_sign=sign,Ring_yaw_from='gauge only; RGB still required',radius_mm=r,source=asset(SRC)))
 return out

def mid_for(v):
 p=P/('ring'if v['group']=='G01'else'group_ring_evidence')/(v['id']+'.json');d=load(p);d=d.get('original_DXY',d);return d.get('centerline'),asset(p)

def fit_ellipse(p):
 (x,y),(d1,d2),ang=cv2.fitEllipse(np.asarray(p,np.float32).reshape(-1,1,2));return dict(cx=x,cy=y,major_radius=d1/2,minor_radius=d2/2,angle_deg=ang)
