"""Wang et al.2008 Table I Double Reflection, differentiable PyTorch."""
import torch

def unit(x):return x/torch.linalg.vector_norm(x,dim=-1,keepdim=True).clamp_min(1e-12)

def double_reflection(points,tangents=None,initial=None):
    if tangents is None:
        tangents=torch.cat([points[1:2]-points[:1],points[2:]-points[:-2],points[-1:]-points[-2:-1]])
    norms=torch.linalg.vector_norm(tangents,dim=1)
    if bool((norms<1e-10).any()):raise ValueError('DEGENERATE_TANGENT')
    t=unit(tangents)
    if initial is None:
        axis=torch.eye(3,dtype=t.dtype,device=t.device)[torch.argmin(abs(t[0])).item()];r=unit(axis-(axis@t[0])*t[0])
    else:r=unit(initial-(initial@t[0])*t[0])
    rs=[r]
    for i in range(len(points)-1):
        v1=points[i+1]-points[i];c1=v1@v1
        if float(c1.detach())<1e-18:raise ValueError('DEGENERATE_CENTERLINE_SEGMENT')
        rl=r-2*(v1@r)/c1*v1;tl=t[i]-2*(v1@t[i])/c1*v1
        v2=t[i+1]-tl;c2=v2@v2
        r=rl if float(c2.detach())<1e-18 else rl-2*(v2@rl)/c2*v2
        r=unit(r-(r@t[i+1])*t[i+1]);rs.append(r)
    r=torch.stack(rs);s=unit(torch.linalg.cross(t,r,dim=1));return r,s,t
