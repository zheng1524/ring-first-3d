"""Existing real-P0 camera interface + installed nvdiffrast public API.

Reference pipeline: NVlabs/nvdiffrast samples/torch/cube.py::render.
No copied NVIDIA implementation; the installed licensed library performs
rasterize/interpolate/antialias. Camera intrinsics/poses are immutable.
"""
from inputs import *
import torch
import nvdiffrast.torch as dr
import torch.nn.functional as TF
CTX=None
def tensor(x,dtype=torch.float32):return torch.as_tensor(np.asarray(x).copy(),device='cuda',dtype=dtype)
def context():
    global CTX
    if CTX is None:CTX=dr.RasterizeCudaContext()
    return CTX
def clips(V,K,T,size):
    w,h=size;P=(V-tensor(T[:3,3]))@tensor(T[:3,:3]);H=P@tensor(K).T;z=P[:,2];near=.1;far=1000.
    return torch.stack([2*(H[:,0]+.5*z)/w-z,z-2*(H[:,1]+.5*z)/h,(far+near)/(far-near)*z-2*far*near/(far-near),z],1),P
class Renderer:
    def __init__(self,scene):
        cad=ringmesh(scene);self.RV=tensor(cad.vertices);self.RF=np.asarray(cad.faces)
    def render(self,V,F,K,T,size=(320,180),cad=True,aa=True):
        nf=len(F);allV=torch.cat([V,self.RV])if cad else V;allF=np.vstack([F,self.RF+len(V)])if cad else F;tri=tensor(allF,torch.int32);clip,P=clips(allV,K,T,size)
        rast,_=dr.rasterize(context(),clip[None],tri,resolution=[size[1],size[0]],grad_db=False)
        attr=torch.stack([torch.cat([torch.ones(len(V),device=V.device),torch.zeros(len(allV)-len(V),device=V.device)]),P[:,2]],1)[None]
        image,_=dr.interpolate(attr,rast,tri)
        # Native antialiasing is locally differentiable. Raster-event finite
        # differences are recorded separately, never claimed globally smooth.
        alpha=dr.antialias(image[...,:1].contiguous(),rast,clip[None],tri)if aa else image[...,:1]
        fid=rast[0,:,:,3].flip(0).long()-1
        return dict(alpha=alpha[0,:,:,0].flip(0),z=image[0,:,:,1].flip(0),hard=(fid>=0)&(fid<nf),fid=fid)
