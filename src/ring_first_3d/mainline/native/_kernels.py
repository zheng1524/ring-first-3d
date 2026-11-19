import numpy as np
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])

# Exact project-owned function text, extracted without algorithm changes.
# Globals are bound by camera.py / geometry.py; no old workspace imports.

def torus_contours(C,rot,K,R=5.6,r=.6,n=256):
    """Exact perspective apparent contours n(X) dot (C-X)=0.
    Valid in the top-view, open-hole, non-self-occluded regime checked by gate.
    theta is a curve parameter, never a claimed physical correspondence.
    rot maps camera coordinates to ring coordinates.
    """
    th=np.arange(n)*2*np.pi/n; a=C[0]*np.cos(th)+C[1]*np.sin(th)-R
    b=C[2]; length=np.sqrt(a*a+b*b)
    if np.any(length<=r):raise ValueError('invalid torus apparent-contour regime')
    phi=np.arctan2(b,a)[None,:]+np.array([-1,1])[:,None]*np.arccos(r/length)[None,:]
    X=np.stack([(R+r*np.cos(phi))*np.cos(th),(R+r*np.cos(phi))*np.sin(th),r*np.sin(phi)],-1)
    cam=(X-C) @ rot; uv=cam @ K.T
    return uv[...,:2]/uv[...,2:]

def decode(a,ref):
    z=np.exp(a[2]);center=ref[:3,3]+ref[:3,:3]@np.array([a[0]*z,a[1]*z,z]);Q=ref[:3,:3]@Rotation.from_rotvec([a[3],a[4],0]).as_matrix();return center,Q

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

def torus_residual(pose,ob,part='train',K0=K):
 from matplotlib.path import Path as Poly
 q=ob['q_'+part];p=ob['p_'+part];b=ob['b_'+part]
 try:
  cr=contour_project(pose,256,K0);assert np.isfinite(cr).all();areas=[abs(cv2.contourArea(x.astype(np.float32))) for x in cr];i=np.argmax(areas);a,bcr=Poly(cr[i]),Poly(cr[1-i]);inside=lambda uv:a.contains_points(uv)&~bcr.contains_points(uv);tree=cKDTree(cr.reshape(-1,2));dq=tree.query(q)[0];dp=tree.query(p)[0]*(~inside(p));db=tree.query(b)[0]*inside(b);return np.r_[dq,dp*np.sqrt(len(q)/max(1,len(p))),db*np.sqrt(len(q)/max(1,len(b)))]
 except (ValueError,AssertionError):return np.full(len(q)+len(p)+len(b),1000.)

def unproject(z,pose,uv,K):return (np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T*z[:,None])@pose[:3,:3].T+pose[:3,3]

def depth_mesh(depth,mask,pose,K,color):
 import trimesh
 valid=mask&np.isfinite(depth)&(depth>0);y,x=np.nonzero(valid);uv=np.c_[x,y];P=unproject(depth[y,x],pose,uv,K);ids=np.full(valid.shape,-1,int);ids[y,x]=np.arange(len(x));a=ids[:-1,:-1];b=ids[:-1,1:];c=ids[1:,:-1];d=ids[1:,1:];faces=[]
 for t in [np.stack([a,b,c],-1),np.stack([b,d,c],-1)]:
  good=np.all(t>=0,axis=-1);tri=t[good];z=depth[y,x];tri=tri[np.ptp(z[tri],axis=1)<=cfg()['mesh_max_depth_jump_mm']];faces.extend(tri)
 return trimesh.Trimesh(P,np.array(faces,int).reshape(-1,3),vertex_colors=np.c_[color[y,x],np.full(len(x),255)],process=False)
