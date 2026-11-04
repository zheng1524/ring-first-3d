"""One fixed icosphere, cotan spectrum, M-orthogonal normal deformation."""
from inputs import *
from scipy import sparse
from scipy.sparse.linalg import eigsh
def p0mesh(row):
    s=trimesh.creation.icosphere(subdivisions=3,radius=1);c,Q,a=decode(np.array(row['p']),np.array(row['R0']));u=np.asarray(s.vertices);V=(u*a)@Q.T+c
    n=(u/a)@Q.T;n/=np.linalg.norm(n,axis=1)[:,None]
    return V,np.asarray(s.faces),n
def laplace(V,F):
    tri=V[F];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1)/2
    assert area.min()>1e-9
    I=[];J=[];W=[]
    for k in range(3):
        a=tri[:,(k+1)%3]-tri[:,k];b=tri[:,(k+2)%3]-tri[:,k];w=(a*b).sum(1)/(4*area)
        i=F[:,(k+1)%3];j=F[:,(k+2)%3];I.extend([i,j]);J.extend([j,i]);W.extend([w,w])
    A=sparse.coo_matrix((np.concatenate(W),(np.concatenate(I),np.concatenate(J))),shape=(len(V),len(V))).tocsr()
    L=sparse.diags(np.asarray(A.sum(1)).ravel())-A;mass=np.bincount(F.ravel(),weights=np.repeat(area/3,3),minlength=len(V))
    return L,mass,area
def build(row):
    V,F,n=p0mesh(row);L,mass,area=laplace(V,F);lam,Phi=eigsh(L,k=158,M=sparse.diags(mass),sigma=-1e-8,which='LM',v0=np.linspace(1,2,len(V)),tol=1e-10)
    order=np.argsort(lam);lam=lam[order];Phi=Phi[:,order]
    raw_orth=float(np.max(abs(Phi.T@(mass[:,None]*Phi)-np.eye(len(lam)))))
    c,Q,a=decode(np.array(row['p']),np.array(row['R0']));unit=(V-c)@Q/a
    p=np.array(row['p']);R0=np.array(row['R0']);G=[]
    for j in range(9):
        h=1e-5;pa=p.copy();pb=p.copy();pa[j]+=h;pb[j]-=h
        ca,qa,aa=decode(pa,R0);cb,qb,ab=decode(pb,R0);G.append(((unit*aa)@qa.T+ca-((unit*ab)@qb.T+cb))/(2*h))
    G=np.stack(G,2);g=(G*n[:,:,None]).sum(1)
    U,sv,_=np.linalg.svd(np.sqrt(mass)[:,None]*g,full_matrices=False);r=int((sv>sv[0]*1e-8).sum());old=U[:,:r]
    fields=[];freq=[];raw_indices=[];dropped=[]
    for k in range(1,len(lam)):
        v=np.sqrt(mass)*Phi[:,k];v-=old@(old.T@v)
        if fields:
            B=np.stack(fields,1);v-=B@(B.T@v);v-=B@(B.T@v)
        norm=np.linalg.norm(v)
        if norm<1e-7:dropped.append(k);continue
        v/=norm
        if v[np.argmax(abs(v))]<0:v=-v
        fields.append(v);freq.append(lam[k]);raw_indices.append(k)
        if len(fields)==128:break
    assert len(fields)==128
    weighted=np.stack(fields,1);phi=weighted/np.sqrt(mass)[:,None];phi/=np.max(abs(phi),axis=0)
    overlap=np.max(abs(old.T@(np.sqrt(mass)[:,None]*phi)))
    return dict(V=V,F=F,n=n,phi=phi,lam=np.array(freq),mass=mass,area=area,G=G,L=L.toarray(),raw_lam=lam,raw_indices=np.array(raw_indices),raw_orth=np.array(raw_orth),p0_normal_rank=np.array(r),tangent_overlap=np.array(overlap),dropped=np.array(dropped))
def shape(b,a):return b['V']+b['n']*(b['phi']@a)[:,None]
def geom(V,F):
    m=trimesh.Trimesh(V,F,process=False);t=V[F];cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(cross,axis=1)/2
    return dict(volume_mm3=float(m.volume),area_mm2=float(area.sum()),min_area_mm2=float(area.min()),components=int(len(m.split(only_watertight=False))),extent_mm=np.ptp(V,axis=0).tolist())
