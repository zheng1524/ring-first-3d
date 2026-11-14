"""Unknown shared torus pose from known cameras/masks. No scene/model/depth/GT pose reads."""
import json,hashlib,time,cv2,numpy as np
from pathlib import Path
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from torus_geometry import torus_contours
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'config.json').read_text());data=np.load(R/'observations/cameras.npz');cams=data['c2w'];K=data['K'];n=cfg['contour_samples'];rad=cfg['R'];tube=cfg['r']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(name,paths):
    (R/'metrics'/name).write_text(json.dumps({str(p.relative_to(R)):sha(p) for p in paths},indent=2))
def edges(m):
    y,x=np.nonzero(m[:,:-1]!=m[:,1:]);a=np.c_[x+1,y+.5]
    y,x=np.nonzero(m[:-1]!=m[1:]);return np.r_[a,np.c_[x+.5,y+1]]
def observation(scene,i):
    d=R/'synthetic'/scene;m=cv2.imread(str(d/'ring_mask'/f'{i:03d}.png'),0)>0;p=cv2.imread(str(d/'polyp_mask'/f'{i:03d}.png'),0)>0
    q=edges(m);py,px=np.nonzero(p);unknown=cKDTree(np.c_[px+.5,py+.5]);keep=unknown.query(q)[0]>cfg['contact_exclusion_px']+.5;q=q[keep]
    if len(q)<30:raise ValueError('insufficient confirmed background-facing boundary')
    q=q[np.linspace(0,len(q)-1,min(len(q),cfg['fit_boundary_samples']),dtype=int)]
    return dict(q=q,tree=cKDTree(q),unknown=unknown,mask=m,polyp=p,frame=i,raw_edge_count=len(edges(m)))
def decode(a,ref):
    z=np.exp(a[2]);center=ref[:3,3]+ref[:3,:3]@np.array([a[0]*z,a[1]*z,z]);Q=ref[:3,:3]@Rotation.from_rotvec([a[3],a[4],0]).as_matrix();return center,Q

def project(center,Q,i,count=n):
    camera=cams[i];C=Q.T@(camera[:3,3]-center);rot=Q.T@camera[:3,:3]
    if abs(C[2])<tube*1.05 or np.linalg.norm(C)<rad+tube:raise ValueError('self-occluded or camera-in-torus regime')
    p=torus_contours(C,rot,K,R=rad,r=tube,n=count).reshape(-1,2)
    if not np.isfinite(p).all() or np.max(np.abs(p))>1e5:raise ValueError('invalid projection')
    return p

def residual(a,ref,obs):
    center,Q=decode(a,ref);parts=[]
    for ob in obs:
        try:
            p=project(center,Q,ob['frame']);d1=cKDTree(p).query(ob['q'])[0];d2=ob['tree'].query(p)[0]
            # Censor unknown ring projection inside/near observed foreground polyp.
            # Never use the polyp-ring interface as a measured torus boundary.
            d2=np.minimum(d2,np.maximum(0,ob['unknown'].query(p)[0]-cfg['contact_exclusion_px']))
            # Outside image has no censored area and remains penalized.
            parts.extend([d1,d2*np.sqrt(len(d1)/len(d2))])
        except ValueError:parts.extend([np.full(len(ob['q']),1000.),np.full(2*n,1000.)])
    return np.concatenate(parts)

def image_seeds(ob):
    y,x=np.nonzero(ob['mask']);uv=np.c_[x+.5,y+.5];mean=uv.mean(0);e=np.linalg.eigvalsh(np.cov(uv.T));diameter=2*np.sqrt(2*e[-1]);Z=2*(rad+tube)*K[0,0]/max(diameter,10);xy=(mean-K[:2,2])/np.diag(K)[:2];seeds=[]
    for scale in cfg['seed_depth_factors']:
        for tilt in cfg['seed_inclinations_deg']:
            for az in (cfg['seed_azimuths_deg'] if tilt else [0]):
                t=np.deg2rad(tilt);az=np.deg2rad(az);seeds.append(np.array([*xy,np.log(Z*scale),t*np.cos(az),t*np.sin(az)]))
    return seeds

def solve(obs,ref,seeds):
    score=lambda a:float(np.mean(2*(np.sqrt(1+residual(a,ref,obs)**2)-1)))
    ranked=sorted([(score(a),a) for a in seeds],key=lambda x:x[0]);fits=[]
    for _,a in ranked[:cfg['seed_retain']]:
        fit=least_squares(residual,a,args=(ref,obs),loss='soft_l1',f_scale=cfg['huber_px'],max_nfev=cfg['max_nfev'],diff_step=1e-4,bounds=([-3,-3,np.log(5),-1.55,-1.55],[3,3,np.log(500),1.55,1.55]),ftol=2e-7,xtol=2e-7,gtol=2e-7)
        center,Q=decode(fit.x,ref);loss=score(fit.x);fits.append(dict(center=center.tolist(),normal=Q[:,2].tolist(),Q=Q.tolist(),parameters=fit.x.tolist(),loss=loss,nfev=int(fit.nfev),optimizer_success=bool(fit.success),jac_singular=np.linalg.svd(fit.jac,compute_uv=False).tolist()))
    fits.sort(key=lambda f:f['loss']);best=fits[0];best['alternatives']=[{k:v for k,v in f.items() if k not in ['alternatives']} for f in fits[1:]]
    best['numerical_success']=bool(np.isfinite(best['loss']) and best['loss']<cfg['numerical_success_max_training_px']**2)
    best['ambiguity_alternatives']=[f for f in best['alternatives'] if f['loss']<=best['loss']*1.05+.02 and np.degrees(np.arccos(np.clip(abs(np.array(f['normal'])@best['normal']),0,1)))>10]
    return best

def predict():
    inputs=[R/'config.json',R/'observations/cameras.npz']+list((R/'scripts').glob('*.py'))
    for s in ['S0','S1']:
        inputs+=list((R/'synthetic'/s/'ring_mask').glob('*.png'))+list((R/'synthetic'/s/'polyp_mask').glob('*.png'))
    freeze('protocol_freeze.json',inputs);start=time.time()
    for s in ['S0','S1']:
        obs=[observation(s,i) for i in range(cfg['frames'])];singles=[]
        for i,ob in enumerate(obs):
            result=solve([ob],cams[i],image_seeds(ob));result['frame']=i;singles.append(result)
            print(s,'M0',i,'objective',result['loss'],'ambiguity',len(result['ambiguity_alternatives']),flush=True)
            (R/'predictions'/f'{s}_M0.json').write_text(json.dumps(singles,indent=2))
        train=[obs[i] for i in cfg['train']];ref=cams[cfg['train'][0]];seeds=image_seeds(train[0])
        for i in cfg['train']:
            for candidate in [singles[i]]+singles[i]['alternatives'][:2]:
                center=np.array(candidate['center']);Q=np.array(candidate['Q']);p=np.linalg.solve(ref[:3,:3],center-ref[:3,3]);normal=ref[:3,:3].T@Q[:,2]
                if normal[2]<0:normal=-normal
                v=np.cross([0,0,1],normal);angle=np.arccos(np.clip(normal[2],-1,1));w=v*angle/max(np.linalg.norm(v),1e-9)
                seeds.append(np.array([p[0]/p[2],p[1]/p[2],np.log(p[2]),w[0],w[1]]))
        result=solve(train,ref,seeds);(R/'predictions'/f'{s}_M1.json').write_text(json.dumps(result,indent=2));print(s,'M1',result['loss'],flush=True)
    freeze('prediction_freeze.json',list((R/'predictions').glob('*.json'))+list((R/'scripts').glob('*.py'))+[R/'config.json']);(R/'metrics/runtime.json').write_text(json.dumps(dict(seconds=time.time()-start,GT_pose_read=False,inputs='known cameras, masks, known R/r only')))
if __name__=='__main__':predict()
