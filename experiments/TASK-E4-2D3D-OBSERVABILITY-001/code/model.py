"""One compact smooth SDF correction; four parameters, no free mesh vertices."""
from common import *
import torch
from vendor.kaolin_tetmesh import marching_tetrahedra
torch.set_num_threads(2)
def wendland(r):
    t=np.maximum(1-r,0);return t**6*(35*r*r+18*r+3)/3
class Body:
    def __init__(self,field_path=None):
        self.a=dict(np.load(field_path or R/'inputs/BASE_FIELD.npz'));self.P=self.a['P'];self.phi0=self.a['phi'];self.radius=float(self.a['radius']);self.tets=torch.as_tensor(self.a['tets'],dtype=torch.long);self.V=torch.as_tensor(self.P,dtype=torch.float32)
    def values(self,q):return self.phi0+q[3]*wendland(np.linalg.norm(self.P-q[:3],axis=1)/self.radius)
    def mesh(self,q):
        phi=torch.as_tensor(self.values(q),dtype=torch.float32)
        with torch.no_grad():vs,fs=marching_tetrahedra(self.V[None],self.tets,phi[None])
        V=vs[0].numpy().astype(float);F=fs[0].numpy().astype(np.int32)
        if trimesh.Trimesh(V,F,process=False).volume<0:F=F[:,[0,2,1]]
        return V,F
    def save(self,name,q):
        V,F=self.mesh(q);path=R/'local_results'/name;path.mkdir(exist_ok=True,parents=True);np.savez_compressed(path/'MODEL.npz',q=q,V=V,F=F);mesh=trimesh.Trimesh(V,F,process=False);mesh.export(path/'BODY_mm.ply');mm=mesh.copy();mm.vertices*=.001;mm.export(path/'BODY_m.glb');return V,F
def grid_tets(shape):
    ix=np.arange(np.prod(shape)).reshape(shape);corners=[ix[a:shape[0]-1+a,b:shape[1]-1+b,c:shape[2]-1+c].ravel()for a,b,c in [(0,0,0),(1,0,0),(0,1,0),(1,1,0),(0,0,1),(1,0,1),(0,1,1),(1,1,1)]];C=np.stack(corners,1)
    # Freudenthal split: shared face triangulations agree across Cartesian cells.
    lut=np.array([[0,1,3,7],[0,3,2,7],[0,2,6,7],[0,6,4,7],[0,4,5,7],[0,5,1,7]])
    return C[:,lut].reshape(-1,4)
def normals_quality(V,F):
    m=trimesh.Trimesh(V,F,process=False);a=m.face_adjacency;n=m.face_normals;ang=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',n[a[:,0]],n[a[:,1]]),-1,1)))
    return dict(closed=m.is_watertight,winding=m.is_winding_consistent,components=len(m.split(only_watertight=False)),volume_mm3=m.volume,area_mm2=m.area,normal_angle_deg=stats(ang))
