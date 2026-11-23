"""Same Ring-First five-parameter solve and RGB yaw/normal disambiguation.

No camera BA, Body, HERO, or DXY runtime is imported. A supplied real RGB map
is required to resolve the Ring's axial symmetry; ring-only output says so.
"""
import types
import builtins
import cv2
import numpy as np
from scipy.optimize import least_squares, minimize_scalar
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from . import _kernels
from .geometry import project

RF_CONFIG = dict(seed_depth_factors=[.85,1.,1.2],seed_inclinations_deg=[0,35,60],seed_azimuths_deg=[0,90,180,270],seed_retain=2,max_nfev=35,huber_px=1.,numerical_success_max_training_px=3.)

def bind(fn, ns):
    ns.setdefault('__builtins__',vars(builtins))
    return types.FunctionType(fn.__code__, ns, fn.__name__, fn.__defaults__)

def torus_contours(C, K, n=256, ring_radius=5.6, ring_wire=.6):
    fn=bind(_kernels.torus_contours,{"np":np})
    return fn(np.asarray(C)[:3,3],np.asarray(C)[:3,:3],np.asarray(K),
              R=float(ring_radius),r=float(ring_wire),n=n)

def residual(C, ob, K, ring_radius=5.6, ring_wire=.6):
    ns=dict(np=np,cv2=cv2,cKDTree=cKDTree,K=K,rad=float(ring_radius),tube=float(ring_wire),
            contour_project=lambda C,n=256,K0=K:torus_contours(C,K0,n,ring_radius,ring_wire),
            __builtins__=vars(builtins))
    # Kernel defaults were originally bound to the work-camera K.
    fn=types.FunctionType(_kernels.torus_residual.__code__,ns,"torus_residual",("train",np.asarray(K)))
    return fn(np.asarray(C),ob,K0=np.asarray(K))

def edge(mask):
    y,x=np.nonzero(mask[:,:-1]!=mask[:,1:]);a=np.c_[x+.5,y]
    y,x=np.nonzero(mask[:-1]!=mask[1:]);return np.r_[a,np.c_[x,y+.5]]

def sample(a,n):
    return a[np.linspace(0,len(a)-1,min(n,len(a)),dtype=int)] if len(a) else a

def observe(labels, ring_mode='all'):
    """Ring observations.

    ring_mode='all' uses every true Ring Mask boundary point, including the
    Ring-Polyp contact. ring_mode='legacy' reproduces the old M2-A behavior
    that removed points near the polyp; it is kept only for A0 controls.
    Contact/background labels are diagnostics, never an exclusion rule.
    """
    if labels.shape!=(360,640):raise ValueError("Frozen Ring-First work size is 640x360")
    if not np.isin(labels,[0,1,2]).all():raise ValueError("Labels must be 0 Background, 1 Polyp, 2 Ring")
    rm=labels==2;pm=labels==1;bd=edge(rm)
    near=cv2.dilate(pm.astype(np.uint8),np.ones((5,5),np.uint8))>0
    ix=np.clip(np.floor(bd+.5).astype(int),[0,0],[639,359]);contact=near[ix[:,1],ix[:,0]]
    q_all=bd
    q_legacy=bd[~contact]
    q_train=sample(q_all if ring_mode=='all' else q_legacy,128)
    ob=dict(mask=rm,q_train=q_train,unknown_boundary=bd[contact],ring_mode=ring_mode,
            ring_boundary_all=bd,ring_boundary_contact_polyp=bd[contact],
            ring_boundary_contact_background=bd[~contact],
            ring_boundary_sampled=q_train,q_train_original=len(q_legacy),
            q_train_corrected=len(q_all),ring_boundary_all_count=len(q_all),
            ring_boundary_contact_polyp_count=int(contact.sum()),
            ring_boundary_contact_background_count=int((~contact).sum()))
    roi=cv2.dilate(rm.astype(np.uint8),np.ones((17,17),np.uint8))>0
    for key,m in [('p',rm),('b',(labels==0)&roi)]:
        y,x=np.nonzero(m);ob[key+'_train']=sample(np.c_[x,y],192)
    return ob

def score(C, ob, K, rgb_geometry=None, ring_radius=5.6, ring_wire=.6):
    r=residual(C,ob,K,ring_radius,ring_wire)/3.;n=abs(r)
    val=float(np.mean(np.where(n<=1,.5*n*n,n-.5))) if len(r) else 1e6
    rr=rgb_geometry
    if rr and rr['fit_pnp_inliers']:
        rows=rr['fit_pnp_inliers'];uv,z=project(np.array([x['X'] for x in rows]),C,K)
        e=np.linalg.norm(uv-np.array([x['uv'] for x in rows]),axis=1)/3.
        val+=.2*float(np.mean(np.where(e<=1,.5*e*e,e-.5)))+float(np.maximum(.1-z,0).mean())*100
    return val

def recover(labels, K, rgb_geometry=None, initial_pose=None, ring_radius=5.6, ring_wire=.6, ring_mode='all'):
    """Run the frozen RF5DoF + yaw path. A numeric solution is not pose GT."""
    K=np.asarray(K,float);ob=observe(labels,ring_mode)
    if len(ob['q_train'])<20:raise ValueError('INSUFFICIENT_RING_OBSERVATION')
    ns=dict(np=np,Rotation=Rotation,least_squares=least_squares,K=K,rad=float(ring_radius),tube=float(ring_wire),cfg=dict(RF_CONFIG))
    for name in ['decode','image_seeds','solve']:ns[name]=bind(getattr(_kernels,name),ns)
    def rfun(a,ref,obs):
        c,Q=ns['decode'](a,ref);C=np.eye(4);C[:3,:3]=Q.T;C[:3,3]=-Q.T@c
        return residual(C,ob,K,ring_radius,ring_wire)
    ns['residual']=rfun;seeds=ns['image_seeds'](ob)
    rr=rgb_geometry or dict(C=None,fit_pnp_inliers=[])
    for C in [rr['C'],initial_pose]:
        if C is None:continue
        C=np.array(C);Q=C[:3,:3].T;c=-Q@C[:3,3];normal=Q[:,2]
        if normal[2]<0:normal=-normal
        axis=np.cross([0,0,1],normal);rot=axis*np.arccos(np.clip(normal[2],-1,1))/max(np.linalg.norm(axis),1e-9)
        if c[2]>5:seeds.append(np.r_[c[:2]/c[2],np.log(c[2]),rot[:2]])
    result=ns['solve']([ob],np.eye(4),seeds)
    alternatives=[{k:v for k,v in result.items() if k not in ['alternatives','ambiguity_alternatives']}]+result['alternatives']
    poses=[]
    for a in alternatives:
        C=np.eye(4);Q=np.array(a['Q']);C[:3,:3]=Q.T;C[:3,3]=-Q.T@np.array(a['center']);poses.append(C)
    candidates=[]
    flip=np.eye(4);flip[:3,:3]=Rotation.from_euler('x',np.pi).as_matrix()
    if rr['fit_pnp_inliers']:
        for i,C in enumerate(poses):
            for f in [False,True]:
                base=(flip if f else np.eye(4))@C
                def pose(a):
                    H=np.eye(4);H[:3,:3]=Rotation.from_euler('z',a).as_matrix();return H@base
                grid=np.linspace(-np.pi,np.pi,72,endpoint=False)
                a=min(grid,key=lambda t:score(pose(t),ob,K,rr,ring_radius,ring_wire))
                fit=minimize_scalar(lambda t:score(pose(t),ob,K,rr,ring_radius,ring_wire),bounds=(a-np.pi/36,a+np.pi/36),method='bounded',options={'maxiter':20})
                candidates.append(dict(C=pose(fit.x),FIT_objective=score(pose(fit.x),ob,K,rr,ring_radius,ring_wire),source='originalRF5DoF_RGB_yaw',normal_branch=i,normal_flip=f,yaw_rad=fit.x))
    else:
        candidates=[dict(C=C,FIT_objective=score(C,ob,K,None,ring_radius,ring_wire),source='RING_ONLY_YAW_UNRESOLVED')for C in poses]
    for tag,C in [('REAL_RGB_PNP_LM',rr['C']),('HISTORICAL_FROZEN',initial_pose)]:
        if C is not None:candidates.append(dict(C=np.array(C),FIT_objective=score(np.array(C),ob,K,rr,ring_radius,ring_wire),source=tag))
    chosen=min(candidates,key=lambda c:c['FIT_objective'])
    return dict(c2w_mm=chosen['C'],candidate_source=chosen['source'],FIT_objective=chosen['FIT_objective'],
                status='NUMERIC_RGB_REGISTERED_CONDITIONAL' if rr['fit_pnp_inliers'] else 'RING_ONLY_YAW_UNRESOLVED',
                calibrated_pose_truth=False,candidates=candidates,ring_alternatives=alternatives,
                parameters_updated='Ring5DoF and RGB yaw/normal selection; no Ceres or per-frame BA')
