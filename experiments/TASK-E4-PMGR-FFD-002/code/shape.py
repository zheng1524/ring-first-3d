"""Native Torch FFD, frozen local lattice, live metric nine parameters.

Formula reference (not a PhysicsNeMo runtime):
https://docs.nvidia.com/physicsnemo/latest/physicsnemo/api/nn/functionals/geometry.html
Bernstein and cardinal cubic B-spline tensor products; residual hierarchy.
"""
from inputs import *
import torch,math,itertools
from scipy.linalg import null_space,eigh
from scipy.spatial import cKDTree
from legacy_mesh import laplace
torch.set_num_threads(2)

def lattice_weights(P,origin,extent,n,basis='bernstein'):
    u=(P-origin)/extent;inside=((u>=0)&(u<=1)).all(-1);u=u.clamp(0,1);f=[]
    for k in range(3):
        x=u[:,k]
        if basis=='bernstein':
            f.append(torch.stack([math.comb(n-1,i)*x**i*(1-x)**(n-1-i)for i in range(n)],1))
        else:
            span=torch.floor(x*(n-3)).long().clamp(0,n-4);t=x*(n-3)-span
            v=torch.stack([(1-t)**3,3*t**3-6*t*t+4,-3*t**3+3*t*t+3*t+1,t**3],1)/6
            f.append(torch.zeros((len(P),n),dtype=P.dtype,device=P.device).scatter(1,span[:,None]+torch.arange(4,device=P.device),v))
    W=torch.einsum('ni,nj,nk->nijk',*f).reshape(len(P),-1)*inside[:,None]
    return W

def free_form_deform_points(P,control_displacements,origin,extent,basis='bernstein'):
    n=control_displacements.shape[0];W=lattice_weights(P,origin,extent,n,basis)
    return P+W@control_displacements.reshape(-1,3)

def rotation(v,R0):
    z=v[0]*0;K=torch.stack([z,-v[2],v[1],v[2],z,-v[0],-v[1],v[0],z]).reshape(3,3)
    return R0@torch.matrix_exp(K)

def tensor_vertices(q,unit,R0,a0,fields):
    Q=rotation(q[3:6],R0);a=torch.exp(q[6:9]);local=unit*a0
    if len(q)>9:local=local+torch.einsum('nck,k->nc',fields[:,:,:len(q)-9],q[9:])
    return (local*(a/a0))@Q.T+q[:3]

class Body:
    def __init__(self,row,p,fields=None):
        self.row=row;self.p=np.array(p);self.reference=self.p.copy();self.R0=np.array(row['R0']);mesh=trimesh.creation.icosphere(subdivisions=3);self.unit=np.asarray(mesh.vertices);self.F=np.asarray(mesh.faces);self.a0=np.exp(self.p[6:9]);self.fields=np.zeros((len(self.unit),3,0))if fields is None else fields
        self.edges=mesh.edges_unique
    def vertices(self,q,jac=False,device='cpu'):
        if torch.is_tensor(q):
            args=[torch.as_tensor(x,dtype=q.dtype,device=q.device)for x in [self.unit,self.R0,self.a0,self.fields]];return tensor_vertices(q,*args)
        t=torch.as_tensor(q,dtype=torch.float64);args=[torch.as_tensor(x,dtype=t.dtype)for x in [self.unit,self.R0,self.a0,self.fields]];fn=lambda x:tensor_vertices(x,*args);V=fn(t).detach().numpy()
        return(V,torch.func.jacfwd(fn)(t).detach().numpy())if jac else V

def support(scene,model):
    V=model.vertices(model.p);records=[];blocks=[];rt=mesh_scene(V,model.F)
    for cid in protocol()['scenes'][scene]['P2']:
        s=source(cid);uv,z=vis.project_camera(V,s['K'],s['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);rz=cast(rt,uv,s['K'],s['T'])[0];cz=cast(ringscene(scene),uv,s['K'],s['T'])[0]
        inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)&(s['labels'][px[:,1],px[:,0]]==1)
        d=cKDTree(obs(cid)['X']).query(V)[0];ok=inside&~(np.isfinite(rz)&(rz<z-.05))&(z<=cz+.05)&(d<=.75)
        records.append(ok);blocks.append(GATE[cid]['block'])
    unique=sorted(set(blocks));count=sum(np.any(np.array(records)[np.array(blocks)==b],axis=0)for b in unique);gate=count>=2
    return dict(per_source=np.array(records),partition_count=count,P3_gate=gate,source_ids=protocol()['scenes'][scene]['P2'],qualification='conditional evidence proxy, not physical truth')

def construct_basis(scene,model,kind):
    V,J=model.vertices(model.p,True);_,Q,a=decode(model.p,model.R0);L,mass,_=laplace(V,model.F);localJ=np.einsum('nck,cd->ndk',J,Q);W=np.repeat(mass,3);U,s,_=np.linalg.svd(np.sqrt(W)[:,None]*localJ.reshape(-1,9),full_matrices=False);constraints=[x for x in U[:,s>s[0]*1e-8].T];fields=[];labels=[];sup=support(scene,model);stage_sizes=[12,48,96]
    if kind=='spectral':
        normal=model.unit/model.a0;normal/=np.linalg.norm(normal,axis=1)[:,None];g=(localJ*normal[:,:,None]).sum(1);u,ss,_=np.linalg.svd(np.sqrt(mass)[:,None]*g,full_matrices=False);Z=null_space(u[:,ss>ss[0]*1e-8].T);A=(L.toarray()/np.sqrt(mass)[:,None])/np.sqrt(mass)[None,:];ev,vec=eigh(Z.T@A@Z,subset_by_index=[0,159]);candidates=[normal*(Z@vec[:,i]/np.sqrt(mass))[:,None]for i in range(len(ev))]
        candidate_groups=[candidates,candidates,candidates]
    else:
        P=torch.tensor(model.unit*model.a0,dtype=torch.float64);origin=torch.tensor(-model.a0*1.05);extent=torch.tensor(model.a0*2.1);candidate_groups=[]
        for n,base in [(3,'bernstein'),(4,'bernstein'),(6,'bspline')]:
            b=lattice_weights(P,origin,extent,n,base).numpy();coords=np.stack(np.meshgrid(*[np.arange(n)]*3,indexing='ij'),-1).reshape(-1,3);cands=[]
            for ijk in sorted(itertools.product(range(n),repeat=3),key=lambda x:(sum(k*k for k in x),x)):
                val=np.prod(np.cos(np.pi*(coords+.5)*np.array(ijk)/n),axis=1)
                for c in range(3):
                    field=np.zeros((len(P),3));field[:,c]=b@val;cands.append(field)
            candidate_groups.append(cands)
    diagnostics=[]
    for st,target in enumerate(stage_sizes):
        if st==2:
            mask=np.repeat(sup['P3_gate'],3);C=np.asarray(constraints)*mask[None,:];_,ss,vt=np.linalg.svd(C,full_matrices=False);projectors=[v for v in vt[ss>max(ss[0]*1e-8,1e-10)]]if len(ss)else[]
        else:projectors=constraints
        for index,f in enumerate(candidate_groups[st]):
            if len(fields)>=target:break
            if st==2:
                # Fixed multi-partition/HERO-supported residual; PhysicsNeMo's
                # point_weights semantics. Unknown back does not gain new detail.
                f=f*sup['P3_gate'][:,None]
                if np.linalg.norm(f)<1e-9:continue
            v=f.reshape(-1)*np.sqrt(W)
            for _ in range(2):
                for old in projectors:v-=old*np.dot(old,v)
            norm=np.linalg.norm(v)
            if norm<1e-8:continue
            constraints.append(v/norm)
            if st==2:projectors.append(v/norm)
            ff=(v/np.sqrt(W)).reshape(-1,3);ff/=np.linalg.norm(ff,axis=1).max();fields.append(ff);labels.append(dict(stage=st+1,candidate_index=index,kind=kind,pre_normalization_independent_norm=float(norm)))
        diagnostics.append(dict(stage=st+1,requested=target,available=len(fields),status='READY'if len(fields)>=target else'STAGE_BLOCKED_INSUFFICIENT_SUPPORTED_MODES'))
    out=np.stack(fields,-1)if fields else np.zeros((len(V),3,0));return dict(fields=out,F=model.F,V0=V,mass=mass,labels=labels,stages=diagnostics,support=sup,normalization='maximum vertex field norm=1, coefficients in reference local millimetres',lattices='Bernstein3/4 + supported cubic B-spline6; weighted orthogonal residual projection of affine/earlier spans')
