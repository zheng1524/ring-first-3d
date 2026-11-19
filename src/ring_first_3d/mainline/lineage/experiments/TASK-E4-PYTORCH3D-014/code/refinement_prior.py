"""Common coarse restriction prior + area-normalized fine residual.
Exactly invariant to interpolation-only subdivision for coarse/affine displacements.
"""
from components import *
import copy
class SubdivisionPrior:
 def __init__(self,c):
  a=np.load(R/'inputs'/c.name/'SHAPE_REFERENCE.npz');self.anchor=tensor(a['anchors'],torch.int64);self.faces=tensor(a['coarse_faces'],torch.int64);self.interp=tensor(a['interp_vertices'],torch.int64);self.bary=tensor(a['bary'],torch.float32);self.weights=tensor(a['vertex_area_weights'],torch.float32)
  cc=copy.copy(c);cc.V=a['coarse_V'];cc.F=a['coarse_faces'];cc.base=mesh((cc.V-cc.center)/cc.scale,cc.F);self.prior=RelativePrior(cc)
 def __call__(self,m):
  v=m.verts_packed();coarse=v[self.anchor];pr=self.prior(Meshes(verts=[coarse],faces=[self.faces]));interpolated=(coarse[self.interp]*self.bary[:,:,None]).sum(1);detail=((v-interpolated)**2).sum(1);pr['laplacian']=pr['laplacian']+.01*(detail*self.weights).sum()/self.weights.sum().clamp_min(1e-20);return pr
