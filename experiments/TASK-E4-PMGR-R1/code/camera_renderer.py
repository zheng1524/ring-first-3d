"""nvdiffrast first triangle rasterization; CV +Z, top-down pixel centers, mm."""
from inputs import *
import torch
import nvdiffrast.torch as dr
torch.set_num_threads(2)
CTX=None
def context():
    global CTX
    if CTX is None:CTX=dr.RasterizeCudaContext()
    return CTX
def tensor(x,dtype=torch.float32):return torch.as_tensor(np.asarray(x).copy(),device='cuda',dtype=dtype)
def clips(V,K,T,size):
    w,h=size;P=(V-tensor(T[:3,3]))@tensor(T[:3,:3]);proj=P@tensor(K).T;z=P[:,2];near=.1;far=1000.
    x=2*(proj[:,0]+.5*z)/w-z;y=z-2*(proj[:,1]+.5*z)/h
    clip=torch.stack([x,y,(far+near)/(far-near)*z-2*far*near/(far-near),z],1)
    return clip,P
class Renderer:
    def __init__(self,scene):
        ring=ringmesh(scene);self.RV=tensor(ring.vertices);self.RF=np.asarray(ring.faces);self.calls=0
    def render(self,V,F,K,T,size=(320,180),cad=True):
        self.calls+=1;nf=len(F);Vall=torch.cat([V,self.RV])if cad else V
        fall=np.vstack([F,self.RF+len(V)])if cad else F;tri=tensor(fall,torch.int32)
        clip,P=clips(Vall,K,T,size);rast,_=dr.rasterize(context(),clip[None],tri,resolution=[size[1],size[0]],grad_db=False)
        attr=torch.stack([torch.cat([torch.ones(len(V),device='cuda'),torch.zeros(len(Vall)-len(V),device='cuda')]),P[:,2]],1)[None]
        image,_=dr.interpolate(attr,rast,tri);alpha=dr.antialias(image[:,:,:,:1].contiguous(),rast,clip[None],tri)
        fid=rast[0,:,:,3].flip(0).long()-1;hard=(fid>=0)&(fid<nf)
        return dict(alpha=alpha[0,:,:,0].flip(0),z=image[0,:,:,1].flip(0),hard=hard,fid=fid)
def first_at(V,F,uv,K,T):
    rt=mesh_scene(V,F);result=rt.cast_rays(o3d.core.Tensor(vis.camera_rays(uv,K,T).astype(np.float32)));return result
