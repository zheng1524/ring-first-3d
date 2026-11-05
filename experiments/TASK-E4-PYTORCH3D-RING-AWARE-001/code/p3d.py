from common import *
import torch
from pytorch3d.structures import Meshes
from pytorch3d.renderer import MeshRenderer,MeshRasterizer,SoftSilhouetteShader,RasterizationSettings,BlendParams
from pytorch3d.utils import cameras_from_opencv_projection
from pytorch3d.loss import mesh_edge_loss,mesh_normal_consistency,mesh_laplacian_smoothing
device=torch.device('cuda:0')
torch.set_num_threads(2)
def tensor(x,dtype=torch.float32):return torch.as_tensor(x,dtype=dtype,device=device)
def mesh(V,F):return Meshes(verts=[tensor(V)],faces=[tensor(F,torch.int64)])
def regularizers(m):return dict(edge=mesh_edge_loss(m),normal=mesh_normal_consistency(m),laplacian=mesh_laplacian_smoothing(m,method='uniform'))
def renderer(size):
    return MeshRenderer(rasterizer=MeshRasterizer(raster_settings=RasterizationSettings(image_size=size,blur_radius=float(np.log(1./1e-4-1.)*1e-4),faces_per_pixel=50)),shader=SoftSilhouetteShader(blend_params=BlendParams(sigma=1e-4)))

class Case:
    def __init__(self,name):
        self.name=name;self.meta=getcase(name); a=np.load(R/'inputs'/name/'INITIAL.npz'); self.V=a['V'];self.F=a['F'];self.center=self.V.mean(0);self.scale=float(abs(self.V-self.center).max()); self.base=mesh((self.V-self.center)/self.scale,self.F)
        a=np.load(R/'inputs'/name/'RING.npz');self.ringV=a['V'];self.ringF=a['F'];self.ring=mesh((self.ringV-self.center)/self.scale,self.ringF)
        self.size=(180,320);self.renderer=renderer(self.size)
        self.hard=MeshRasterizer(raster_settings=RasterizationSettings(image_size=self.size,blur_radius=0.,faces_per_pixel=1))
        self.views={}
        for v in self.meta['views']:
            a=np.load(R/'inputs'/name/(v['id']+'.npz'));lab=a['labels'];h,w=lab.shape;K=a['K'].copy();T=a['T'].copy()
            A=np.diag([320/w,180/h,1.]);A[:2,2]=np.array([320/w,180/h])*.5-.5;Ks=A@K
            # P3D raster pixel centers are half-integers; original ray indices are integers.
            Ke=Ks.copy();Ke[:2,2]+=.5
            rot=T[:3,:3].T;tv=(rot@self.center-rot@T[:3,3])/self.scale
            cam=cameras_from_opencv_projection(tensor(rot[None]),tensor(tv[None]),tensor(Ke[None]),tensor(np.array(self.size)[None]))
            sid=np.load(R/'inputs'/name/(v['id']+'_SIDES.npz'))
            classes=cv2.resize(sid['classes'],(320,180),interpolation=cv2.INTER_NEAREST)
            ls=cv2.resize(lab,(320,180),interpolation=cv2.INTER_NEAREST)
            with torch.no_grad():rz=self.hard(self.ring,cameras=cam).zbuf[0,...,0];finite=rz>0
            self.views[v['id']]=dict(meta=v,cam=cam,K=K,Ksmall=Ks,T=T,labels=lab,small=ls,rgb=a['RGB'],target=tensor(ls==1),classes=tensor(classes,torch.int64),ring_observed=tensor(ls==2,torch.bool),cad_z=torch.where(finite,rz,torch.full_like(rz,float('inf'))),cad_finite=finite)
        self.fit=[v['id']for v in self.meta['views']if v['role']=='FIT']
    def fragments(self,m,cid):return self.renderer.rasterizer(m,cameras=self.views[cid]['cam'])
    def baseline(self,fr,cid):return self.renderer.shader(fr,self.base,cameras=self.views[cid]['cam'])[0,...,3]
    def aware(self,fr,cid,return_aux=False):
        d=self.views[cid];valid=fr.pix_to_face[0]>=0;p=torch.sigmoid(-fr.dists[0]/1e-4)*valid
        z=fr.zbuf[0];rz=d['cad_z'];tau=.05/self.scale
        visibility=torch.where(d['cad_finite'][...,None],torch.sigmoid((rz[...,None]-z)/tau),torch.ones_like(z))
        alpha=1.-torch.prod(1.-p*visibility,dim=-1)
        # Negative supervision can relax through either 2D evidence OR CAD.
        # Foreground is never masked; a body in front of CAD remains penalizable.
        protected=((d['classes']==1)|(d['classes']==2)|(d['classes']==4))&(d['target']==0)
        front=(p*visibility).amax(dim=-1)
        w=torch.where(protected,torch.where(d['cad_finite'],front,torch.zeros_like(front)),torch.ones_like(front))
        loss=((alpha-d['target'])**2*w).mean()
        return (loss,alpha,w,visibility,p)if return_aux else loss
    def loss(self,m,cid,arm):
        fr=self.fragments(m,cid)
        if arm=='Baseline':return ((self.baseline(fr,cid)-self.views[cid]['target'])**2).mean()
        return self.aware(fr,cid)
    def mm(self,m):return m.verts_packed().detach().cpu().numpy()*self.scale+self.center,m.faces_packed().detach().cpu().numpy()
