"""Cubic B-spline elliptical sweep with shared actual attachment rim vertices."""
import numpy as np
import torch
import torch.nn.functional as TF
from scipy.interpolate import BSpline
from rmf import double_reflection,unit

def basis(samples=16,controls=5):
    knots=np.r_[np.zeros(4),np.linspace(0,1,controls-2)[1:-1],np.ones(4)]
    x=np.linspace(0,1,samples);eye=np.eye(controls)
    B=BSpline(knots,eye,3)(x);D=BSpline(knots,eye,3).derivative()(x)
    return B,D

def boundary_loop(F,patch):
    q=F[np.asarray(patch,int)];directed=np.r_[q[:,[0,1]],q[:,[1,2]],q[:,[2,0]]];_,iv,c=np.unique(np.sort(directed,1),axis=0,return_inverse=True,return_counts=True);rim=directed[c[iv]==1]
    outgoing={int(a):int(b)for a,b in rim}
    if len(outgoing)!=len(rim)or set(outgoing)!=set(outgoing.values()):raise ValueError('NON_DISK_ATTACHMENT')
    start=min(outgoing);loop=[start];nxt=outgoing[start]
    while nxt!=start and len(loop)<=len(rim):loop.append(nxt);nxt=outgoing[nxt]
    if len(loop)!=len(rim):raise ValueError('MULTIPLE_ATTACHMENT_LOOPS')
    return np.array(loop)

class BSplineSweep(torch.nn.Module):
    def __init__(self,body,patch,direction,length=1.,samples=16,angles=16,controls=5,device='cpu'):
        super().__init__();self.patch=np.array(patch,int);self.loop=boundary_loop(body['F'],patch);self.samples=samples;self.angles=angles;self.nold=len(body['V'])
        self.register_buffer('rim_ids',torch.as_tensor(self.loop,device=device));rim=torch.as_tensor(body['V'][self.loop],dtype=torch.float64,device=device);root=rim.mean(0)
        d=torch.as_tensor(np.array(direction,copy=True),dtype=torch.float64,device=device);d=unit(d)
        e=unit(rim[0]-root-((rim[0]-root)@d)*d);self.register_buffer('initial_axis',e)
        rr=torch.linalg.vector_norm(rim-root,dim=1);radius=rr.mean().clamp_min(.05)
        C=root[None]+torch.linspace(0,length,controls,dtype=root.dtype,device=device)[:,None]*d
        self.control=torch.nn.Parameter(C);self.register_buffer('reference_control',C.clone());self.radii=torch.nn.Parameter(torch.full((controls,2),float(torch.log(torch.expm1(radius))),dtype=root.dtype,device=device))
        B,D=basis(samples,controls);self.register_buffer('B',torch.as_tensor(B,dtype=root.dtype,device=device));self.register_buffer('D',torch.as_tensor(D,dtype=root.dtype,device=device))
        # Reuse the original boundary orientation. No independent floating surface.
        n=len(self.loop);faces=[];root_indices=self.loop.tolist();next_ring=list(range(self.nold,self.nold+angles))
        i=j=0
        while i<n or j<angles:
            if j==angles or(i<n and(i+1)/n<=(j+1)/angles):faces.append([root_indices[i%n],root_indices[(i+1)%n],next_ring[j%angles]]);i+=1
            else:faces.append([root_indices[i%n],next_ring[(j+1)%angles],next_ring[j%angles]]);j+=1
        for k in range(samples-2):
            a=self.nold+k*angles;b=a+angles
            for j in range(angles):z=(j+1)%angles;faces.extend([[a+j,a+z,b+z],[a+j,b+z,b+j]])
        # Smooth taper to a shared terminal point, not a visual spherical shell.
        tip=self.nold+(samples-1)*angles
        a=self.nold+(samples-2)*angles
        for j in range(angles):faces.append([a+j,a+(j+1)%angles,tip])
        self.added_faces=np.array(faces,int);keep=np.ones(len(body['F']),bool);keep[self.patch]=False
        self.keep=keep;self.old_extra=body['F_solid'][len(body['F']):]
        self.face_array=np.r_[body['F'][keep],self.added_faces];self.solid_array=np.r_[self.face_array,self.old_extra]
        self.parent_face=int(self.patch[0]);self.parent_faces=self.patch.copy()
        # Arc-length correspondence from the physical polygon to the ellipse.
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.roll(body['V'][self.loop],-1,axis=0)-body['V'][self.loop],axis=1))];q=np.arange(angles)*arc[-1]/angles;ii=np.minimum(np.searchsorted(arc,q,side='right')-1,len(self.loop)-1);frac=(q-arc[ii])/np.maximum(1e-12,arc[ii+1]-arc[ii]);self.register_buffer('rim_interp_ids',torch.as_tensor(np.c_[self.loop[ii],self.loop[(ii+1)%len(self.loop)]],device=device));self.register_buffer('rim_interp_fraction',torch.as_tensor(frac,dtype=root.dtype,device=device))
    def generate(self,V):
        root=V[self.rim_ids].mean(0);C=torch.cat([root[None],self.control[1:]])
        center=self.B@C;tangent=self.D@C;r,s,t=double_reflection(center,tangent,self.initial_axis)
        radii=TF.softplus(self.B@self.radii);theta=torch.arange(self.angles,dtype=V.dtype,device=V.device)*(2*np.pi/self.angles)
        rings=center[:,None]+radii[:,0,None,None]*torch.cos(theta)[None,:,None]*r[:,None]+radii[:,1,None,None]*torch.sin(theta)[None,:,None]*s[:,None]
        # First generated station is an elliptical transition near the shared rim;
        # positions at station0 are the actual original boundary, unchanged IDs.
        u=self.rim_interp_fraction[:,None];actual_rim=V[self.rim_interp_ids[:,0]]*(1-u)+V[self.rim_interp_ids[:,1]]*u;offset=actual_rim-rings[0];blend=(1-torch.linspace(0,1,self.samples,dtype=V.dtype,device=V.device))**8;rings=rings+blend[:,None,None]*offset[None];rings=rings[1:];tail=center[-1]+t[-1]*torch.minimum(radii[-1].mean(),V.new_tensor(.5))
        vertices=torch.cat([V,rings.reshape(-1,3),tail[None]])
        return vertices,dict(centerline=center,axes=radii,frame_r=r,frame_s=s,frame_t=t)
    def penalties(self,V,info):
        C=info['centerline'];a=info['axes'];bend=((C[2:]-2*C[1:-1]+C[:-2])**2).mean();rad=((a[1:]-a[:-1])**2).mean()+.1*((a/a[0].detach().clamp_min(.05)-1)**2).mean()
        # Adjacent face normal continuity at the exact shared attachment edge.
        F=torch.as_tensor(self.solid_array,dtype=torch.long,device=V.device);tri=V[F];norm=unit(torch.linalg.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],dim=1));edges={}
        for i,f in enumerate(self.solid_array):
            for j in range(3):edges.setdefault(tuple(sorted((int(f[j]),int(f[(j+1)%3])))),[]).append(i)
        pairs=[edges[tuple(sorted((int(a),int(b))))]for a,b in zip(self.loop,np.roll(self.loop,-1))]
        pairs=[p for p in pairs if len(p)==2];P=torch.as_tensor(pairs,device=V.device,dtype=torch.long)
        attach=(1-(norm[P[:,0]]*norm[P[:,1]]).sum(1)).square().mean() if len(pairs) else V.sum()*0
        return bend,rad,attach
    def body(self,V,template):
        out={k:v.copy()for k,v in template.items()};out.update(V=V,F=self.face_array,F_solid=self.solid_array,boundary_vertex=np.r_[template['boundary_vertex'],np.zeros(len(V)-self.nold,bool)],inferred_base_faces=np.r_[template['inferred_base_faces'][:len(template['F'])][self.keep],np.zeros(len(self.added_faces),bool),template['inferred_base_faces'][len(template['F']):]])
        return out
