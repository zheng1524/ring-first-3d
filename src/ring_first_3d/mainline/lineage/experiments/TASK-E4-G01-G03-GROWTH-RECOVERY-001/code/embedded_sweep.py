"""The same cubic five-control,16-station RMF sweep, with an internal proximal end."""
import numpy as np
import torch
import torch.nn.functional as TF
from bspline_sweep import basis
from rmf import double_reflection
from lengths import spline,measure
from ring_first_3d.multisurface.geometry import scene
from ring_collision_gate import signed
import open3d as o3d

def prepare(original,C,A,info):
    # Rebase the recovered proposal to its immutable pre-update STEP024 rim.
    loop=info['root_loop'];rim=original['V'][loop];shift=rim.mean(0)-C[0];C=C+shift
    d=spline(C).derivative()(0);d=d/np.linalg.norm(d)
    m=measure(C,original);exit_point=np.array(m['exit_point']);engine=scene(original['V'],original['F_solid'])
    root=C[0];rays=np.c_[np.stack([root,root]),np.stack([d,-d])].astype(np.float32)
    hits=engine.cast_rays(o3d.core.Tensor(rays),nthreads=2)['t_hit'].numpy().astype(float)
    if not np.isfinite(hits).all()or(hits<=0).any():raise ValueError('LOCAL_THICKNESS_NOT_EVALUABLE')
    thickness=float(hits.sum());radii=TF.softplus(torch.tensor(A)).numpy();radius=float(np.sqrt(info['axes'][0].prod()))
    depth=min(.5*radius,.25*thickness);proximal=exit_point-depth*d
    if float(signed(engine,proximal[None])[0])>=-1e-5:raise ValueError('PROXIMAL_EMBEDDING_NOT_INSIDE')
    u=np.linspace(0,1,5);target=C+(1-u[:,None])**2*(proximal-C[0])
    return dict(control=target.tolist(),radii_logits=A.tolist(),initial_axis=info['frame_r'][0].tolist(),
        embedding_depth_target_mm=depth,local_thickness_mm=thickness,root_radius_mm=radius,
        exit_reference=exit_point.tolist(),direction=d.tolist(),proximal=proximal.tolist(),
        proposal_rebase_translation_mm=shift.tolist(),attachment_region_radius_mm=2.5*radius,
        overlap_transition_mm=radius,initial_exposed_length_mm=m['exposed_stalk_length_mm'],
        thickness_ray_hits_mm=hits.tolist(),root_loop=loop.tolist(),parent_faces=info['removed_faces'].tolist())

class EmbeddedSweep(torch.nn.Module):
    def __init__(self,configuration,device='cpu'):
        super().__init__();self.config=configuration;self.samples=16;self.angles=16
        C=torch.tensor(configuration['control'],dtype=torch.float64,device=device)
        self.register_buffer('proximal',C[0].clone());self.control_tail=torch.nn.Parameter(C[1:].clone())
        self.radii=torch.nn.Parameter(torch.tensor(configuration['radii_logits'],dtype=C.dtype,device=device))
        self.register_buffer('reference_control',C);self.register_buffer('reference_radii',self.radii.detach().clone())
        self.register_buffer('initial_axis',torch.tensor(configuration['initial_axis'],dtype=C.dtype,device=device))
        B,D=basis();self.register_buffer('B',torch.tensor(B,dtype=C.dtype,device=device));self.register_buffer('D',torch.tensor(D,dtype=C.dtype,device=device))
        faces=[]
        # Analytic closed proximal cap; entirely internal, removed by Boolean union.
        root_center=15*16+1;tip=15*16
        for j in range(16):faces.append([root_center,(j+1)%16,j])
        for k in range(14):
            for j in range(16):
                z=(j+1)%16;a=k*16;b=a+16
                faces.extend([[a+j,a+z,b+z],[a+j,b+z,b+j]])
        for j in range(16):faces.append([14*16+j,14*16+(j+1)%16,tip])
        self.F=np.array(faces,np.int64)
    def controls(self): return torch.cat([self.proximal[None],self.control_tail])
    def generate(self):
        C=self.controls();center=self.B@C;tangent=self.D@C;r,s,t=double_reflection(center,tangent,self.initial_axis)
        axes=TF.softplus(self.B@self.radii);theta=torch.arange(16,dtype=C.dtype,device=C.device)*(2*np.pi/16)
        rings=center[:15,None]+axes[:15,0,None,None]*torch.cos(theta)[None,:,None]*r[:15,None]+axes[:15,1,None,None]*torch.sin(theta)[None,:,None]*s[:15,None]
        V=torch.cat([rings.reshape(-1,3),center[-1:],center[:1]])
        return V,dict(centerline=center,axes=axes,frame_r=r,frame_s=s,frame_t=t,control=C)
    def continuation(self,fraction):
        ref=self.reference_control;exit_point=ref.new_tensor(self.config['exit_reference'])
        target=exit_point+fraction*(ref-exit_point);target[0]=self.proximal
        with torch.no_grad():self.control_tail.copy_(target[1:])
    def priors(self,info,clearance_value=None):
        C=info['control'];axes=info['axes'];zero=C.sum()*0
        bend=(C[2:]-2*C[1:-1]+C[:-2]).square().mean()
        radius=(axes[1:]-axes[:-1]).square().mean()+.05*(self.radii-self.reference_radii).square().mean()
        embed=(C[0]-self.proximal).square().sum() # exactly fixed, never hides extra length
        return dict(bend=bend,radius=radius,embed=embed,clearance=zero if clearance_value is None else clearance_value)

