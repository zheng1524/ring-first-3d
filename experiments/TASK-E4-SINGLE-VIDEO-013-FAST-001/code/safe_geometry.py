"""PMGR checks and exact candidate rollback contract; no qualification gate by type."""
from common import *
from pmgr_self import self_intersections
import open3d as o3d

def points(V,F,edges):return np.r_[V,V[F].mean(1),V[edges].mean(1)]
class GeometryGuard:
 def __init__(self,c,chart):
  self.c=c;self.chart=chart;self.F=c.F_solid;self.V0=np.array(c.V);self.edges=np.unique(np.sort(np.r_[self.F[:,[0,1]],self.F[:,[1,2]],self.F[:,[2,0]]],axis=1),axis=0);self.rs=scene(c.ringV,c.ringF);self.manager=trimesh.collision.CollisionManager();self.manager.add_object('Ring',trimesh.Trimesh(c.ringV,c.ringF,process=False));self.cross0=np.cross(c.V[self.F[:,1]]-c.V[self.F[:,0]],c.V[self.F[:,2]]-c.V[self.F[:,0]]);self.area0=np.linalg.norm(self.cross0,axis=1);self.sd0=self.ring_distance(c.V);self.lastsd=self.sd0.copy();self.reverse0=self.reverse(c.V);self.lastreverse=self.reverse0.copy();self.col0=self.collision(c.V);self.initial_self=self_intersections(c.V,self.F);self.topology=trimesh.Trimesh(c.V,self.F,process=False);self.plane=chart.plane;self.eps=1e-5
 def collision(self,V):return bool(self.manager.in_collision_single(trimesh.Trimesh(V,self.F,process=False)))
 def ring_distance(self,V):return self.rs.compute_signed_distance(o3d.core.Tensor(points(V,self.F,self.edges).astype(np.float32)),nsamples=3).numpy().astype(float)
 def reverse(self,V):return scene(V,self.F).compute_signed_distance(o3d.core.Tensor(np.asarray(self.c.ringV[::16],np.float32)),nsamples=3).numpy().astype(float)
 def inspect(self,V,old):
  why=[];move=float(np.linalg.norm(V-old,axis=1).max());tri=V[self.F];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1);ratio=area/np.maximum(self.area0,1e-20);dot=np.einsum('ij,ij->i',cross,self.cross0);info=dict(max_step_mm=move,min_area_ratio=float(ratio.min()),minimum_normal_dot=float(dot.min()),Ring_surface_collision=None,Ring_min_signed_mm=None,self_intersections=None,coplanar_warnings=None)
  if not np.isfinite(V).all():why.append('NONFINITE')
  if move>self.chart.tau+1e-8:why.append('STEP_TRUST')
  if np.linalg.norm(V-self.V0,axis=1).max()>float(getattr(self.chart,'total_trust_D',.25))*self.chart.D+1e-8:why.append('TOTAL_TRUST')
  if ratio.min()<.1:why.append('AREA_DEGENERACY')
  if(dot<=0).any():why.append('FACE_ORIENTATION')
  if self.chart.cap:
   h=V@self.plane[:3]+self.plane[3];boundary=np.unique(self.F[self.c.inferred]);info.update(min_base_height_mm=float(h.min()),max_cap_plane_distance_mm=float(abs(h[boundary]).max()))
   if h.min()<-1e-7 or abs(h[boundary]).max()>1e-7:why.append('BASE_HALFSPACE_OR_BOUNDARY')
  if why:return why,info,None
  sd=self.ring_distance(V);limit=np.maximum(np.minimum(self.sd0,0),np.minimum(self.lastsd,0))-self.eps;collision=self.collision(V);info.update(Ring_min_signed_mm=float(sd.min()),Ring_surface_collision=collision,Ring_violation_sample_N=int((sd<limit).sum()))
  if(sd<limit).any():why.append('RING_WORSENING')
  if not self.col0 and collision:why.append('NEW_CAD_COLLISION')
  rev=self.reverse(V);rlimit=np.maximum(np.minimum(self.reverse0,0),np.minimum(self.lastreverse,0))-self.eps;info.update(reverse_Ring_min_signed_mm=float(rev.min()),reverse_Ring_inside_N=int((rev<0).sum()))
  if(rev<rlimit).any():why.append('RING_CONTAINMENT_WORSENING')
  if not why:
   si=self_intersections(V,self.F);info.update(self_intersections=si['intersections'],coplanar_warnings=si['coplanar_candidates'])
   if si['intersections']>0:why.append('NONADJACENT_SELF_INTERSECTION')
  return why,info,(sd,rev)
