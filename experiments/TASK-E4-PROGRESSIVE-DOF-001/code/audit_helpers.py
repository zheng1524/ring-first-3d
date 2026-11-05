from model import *

def samples(V,F,N=6000):
    rng=np.random.default_rng(20261105);areas=trimesh.triangles.area(V[F]);idx=rng.choice(len(F),N,p=areas/areas.sum());uv=rng.random((N,2));a=np.sqrt(uv[:,0]);w=np.c_[1-a,a*(1-uv[:,1]),a*uv[:,1]]
    return (V[F[idx]]*w[:,:,None]).sum(1)

def dimensions(V,F):
    m=trimesh.Trimesh(V,F,process=False);X=V-V.mean(0);vals,vec=np.linalg.eigh(X.T@X/len(X));vec=vec[:,::-1]
    return dict(center_of_mass_mm=m.center_mass,world_extent_mm=np.ptp(V,axis=0),PCA_extent_mm=np.ptp(X@vec,axis=0),PCA_axes=vec,volume_mm3=float(m.volume),area_mm2=float(m.area))

def gradient_norm(body,q):
    a=body.a;h=float(a['h']);g=np.stack(np.gradient(a['phi'].reshape(a['shape']),h),axis=-1).reshape(-1,3);s=np.exp(q[3:6]);G=g*np.exp(np.mean(q[3:6]))/s;X=body.points(q)
    if len(q)>6:
        centers=body.kernel_centers(q)
        for j in range(2):
            d=X-centers[j];r=np.linalg.norm(d,axis=1)/body.radius;t=np.maximum(1-r,0)
            G+=q[6+j]*(-56/(3*body.radius**2))*(5*r+1)[:,None]*t[:,None]**5*d
    near=abs(body.values(q))<.15
    return dict(near_zero_nodes_N=int(near.sum()),gradient_norm=stats(np.linalg.norm(G[near],axis=1)),strict_distance_field=False,anisotropic_field_is_implicit_not_unit_gradient=True)
