"""Four low-dimensional shape families; all distances/ray parameters in mm axial Z."""
from common import *
def harmonic3(n):
    x,y,z=n.T
    return np.c_[x*(x*x-3*y*y),y*(3*x*x-y*y),z*(x*x-y*y),x*y*z,x*(5*z*z-1),y*(5*z*z-1),z*(5*z*z-3)]
def radial_factor(n,b):return np.exp(.2*np.tanh(harmonic3(n)@b))
def size(family):return {'ellipsoid':9,'star':16,'cap':10,'height':11}[family]
def decode(p,R0):return p[:3],R0@Rotation.from_rotvec(p[3:6]).as_matrix(),np.exp(p[6:9])
def height(x,y,a,p):
    r2=(x/a[0])**2+(y/a[1])**2
    return a[2]*np.maximum(0,1-r2)**2*np.exp(p[9]*x/a[0]+p[10]*y/a[1])
def sphere_mesh(nt,nv,cut=-1.):
    # Northern pole and latitude rings down to bottom; cap leaves last ring open.
    q=np.linspace(1,cut,nv+1)[1:];closed=cut==-1.;q=q[:-1]if closed else q
    theta=np.arange(nt)*2*np.pi/nt;P=[np.array([[0.,0.,1.]])]
    for z in q:P.append(np.c_[np.sqrt(1-z*z)*np.cos(theta),np.sqrt(1-z*z)*np.sin(theta),np.full(nt,z)])
    P=np.concatenate(P);F=[]
    for j in range(nt):F.append([0,1+j,1+(j+1)%nt])
    for k in range(len(q)-1):
        s=1+k*nt;t=s+nt
        for j in range(nt):v=(j+1)%nt;F.extend([[s+j,t+j,t+v],[s+j,t+v,s+v]])
    if closed:
        last=len(P);P=np.r_[P,[[0,0,-1]]];s=1+(len(q)-1)*nt
        for j in range(nt):F.append([s+j,last,s+(j+1)%nt])
    return P,np.asarray(F,int)
@lru_cache(None)
def unit_sphere(high=False):return sphere_mesh(96 if high else 24,48 if high else 12)
def mesh(p,R0,family,high=False):
    c,Q,a=decode(p,R0)
    if family=='height':
        nt=96 if high else 24;nr=32 if high else 12;theta=np.arange(nt)*2*np.pi/nt;P=[np.array([[0.,0.,a[2]]])];F=[]
        for j in range(1,nr+1):
            r=j/nr;x=a[0]*r*np.cos(theta);y=a[1]*r*np.sin(theta);P.append(np.c_[x,y,height(x,y,a,p)])
        P=np.concatenate(P)
        for j in range(nt):F.append([0,1+j,1+(j+1)%nt])
        for k in range(nr-1):
            s=1+k*nt;t=s+nt
            for j in range(nt):v=(j+1)%nt;F.extend([[s+j,t+j,t+v],[s+j,t+v,s+v]])
        F=np.array(F,int)
    else:
        P,F=sphere_mesh(96 if high else 24,48 if high else 12,float(p[9]))if family=='cap'else unit_sphere(high)
        P=P.copy()
        if family=='star':P*=radial_factor(P,p[9:])[:,None]
        P*=a
    return P@Q.T+c,F
def quadratic_interval(o,d,r=1.):
    A=(d*d).sum(1);B=(o*d).sum(1);C=(o*o).sum(1)-r*r;disc=B*B-A*C;ok=(A>1e-20)&(disc>=0)
    root=np.sqrt(np.maximum(disc,0));lo=(-B-root)/np.maximum(A,1e-20);hi=(-B+root)/np.maximum(A,1e-20)
    return lo,hi,ok
def first_depth(p,R0,family,rays):
    """rays=(camera C, R*(K^-1[u,v,1])); returned t is camera axial Z, not range."""
    c,Q,a=decode(p,R0);o=(rays[:,:3]-c)@Q;d=rays[:,3:]@Q;on=o/a;dn=d/a
    if family in ['ellipsoid','cap']:
        lo,hi,ok=quadratic_interval(on,dn)
        if family=='cap':
            vl=ok&(lo>0)&((on+lo[:,None]*dn)[:,2]>=p[9]-1e-10);vh=ok&(hi>0)&((on+hi[:,None]*dn)[:,2]>=p[9]-1e-10)
            return np.minimum(np.where(vl,lo,np.inf),np.where(vh,hi,np.inf))
        return np.where(ok&(hi>0),np.where(lo>0,lo,hi),np.inf)
    if family=='star':
        lo,hi,ok=quadratic_interval(on,dn,np.exp(.2));lo=np.maximum(0,lo);ok&=hi>lo
        def f(t):
            q=on[:,None,:]+t[:,:,None]*dn[:,None,:];r=np.linalg.norm(q,axis=2);n=q/np.maximum(1e-15,r[:,:,None]);factor=radial_factor(n.reshape(-1,3),p[9:]).reshape(r.shape)
            return r-factor
    else:
        lo,hi,ok=quadratic_interval(on[:,:2],dn[:,:2]);az=(dn[:,:2]**2).sum(1)<1e-16
        ok=np.where(az,(on[:,:2]**2).sum(1)<=1,ok);lo=np.where(az,0,lo);hi=np.where(az,1e4,hi)
        hmax=a[2]*np.exp(abs(p[9])+abs(p[10]));dz=d[:,2];z0=o[:,2];parallel=abs(dz)<1e-14
        zlo=(0-z0)/np.where(parallel,1,dz);zhi=(hmax-z0)/np.where(parallel,1,dz)
        slo=np.minimum(zlo,zhi);shi=np.maximum(zlo,zhi);slo=np.where(parallel,-1e4,slo);shi=np.where(parallel,1e4,shi);ok&=~parallel|((z0>=0)&(z0<=hmax))
        lo=np.maximum.reduce([lo,slo,np.zeros(len(lo))]);hi=np.minimum(hi,shi);ok&=hi>lo
        def f(t):
            q=o[:,None,:]+t[:,:,None]*d[:,None,:];return q[:,:,2]-height(q[:,:,0],q[:,:,1],a,p)
    lo=np.where(ok,lo,0);hi=np.where(ok,hi,0);grid=lo[:,None]+(hi-lo)[:,None]*np.linspace(0,1,33)
    values=f(grid);br=(values[:,:-1]*values[:,1:]<=0)&ok[:,None];has=br.any(1);idx=br.argmax(1);ii=np.arange(len(lo));left=grid[ii,idx];right=grid[ii,idx+1];fl=values[ii,idx]
    # Search earliest sign change in interval, including both crossing orientations for open graphs.
    for _ in range(28):
        mid=(left+right)/2;fm=f(mid[:,None])[:,0];same=(fl*fm)>0;left=np.where(same,mid,left);fl=np.where(same,fm,fl);right=np.where(same,right,mid)
    return np.where(has,(left+right)/2,np.inf)
def support_residual_points(p,R0,family,X):
    c,Q,a=decode(p,R0);x=(X-c)@Q
    if family=='height':
        q=x[:,:2]/a[:2];r=np.linalg.norm(q,axis=1);scale=np.maximum(1,r);q=q/scale[:,None];target=np.c_[q*a[:2],height(q[:,0]*a[0],q[:,1]*a[1],a,p)]
    else:
        q=x/a;r=np.linalg.norm(q,axis=1);n=q/np.maximum(1e-12,r[:,None])
        if family=='cap':
            nz=np.maximum(n[:,2],p[9]);phi=np.arctan2(n[:,1],n[:,0]);n=np.c_[np.sqrt(np.maximum(0,1-nz*nz))*np.cos(phi),np.sqrt(np.maximum(0,1-nz*nz))*np.sin(phi),nz]
        target=n*a
        if family=='star':target*=radial_factor(n,p[9:])[:,None]
    return (x-target)@Q.T
def bounds(base,kind,family):
    lo=np.r_[base[:3]-10,np.full(3,-.8),np.log([.25,.25,.05 if kind=='IIa'else .25])];hi=np.r_[base[:3]+10,np.full(3,.8),np.log([15,15,3 if kind=='IIa'else 15])]
    if family=='height':hi[8]=np.log(5);lo=np.r_[lo,[-.25,-.25]];hi=np.r_[hi,[.25,.25]]
    if family=='star':lo=np.r_[lo,np.full(7,-.2)];hi=np.r_[hi,np.full(7,.2)]
    if family=='cap':lo=np.r_[lo,-.65];hi=np.r_[hi,.4]
    return lo,hi
def geometry_diagnostics(p,R0,family):
    P,F=mesh(p,R0,family,True);m=trimesh.Trimesh(P,F,process=False);c,Q,a=decode(p,R0);normals=m.face_normals
    return dict(vertices=len(P),faces=len(F),components=len(m.split(only_watertight=False)),watertight=bool(m.is_watertight),center_mm=c,rotation=Q,axes_mm=a,model_axis_full_extents_mm=np.ptp((P-c)@Q,axis=0),world_bounds_mm=m.bounds,axis_ratio=float(a.max()/a.min()),peak_above_model_plane_mm=float(np.max(((P-c)@Q)[:,2])),area_mm2=float(m.area),degenerate_faces=int((m.area_faces<1e-12).sum()),self_intersection='EXCLUDED_BY_POSITIVE_RADIAL_OR_SINGLE_VALUED_FAMILY; no unconstrained deformation',hidden_surface='ellipsoid/star closed backside PRIOR_INFERRED; cap/height open, no generated underside',finite=bool(np.isfinite(P).all()))
