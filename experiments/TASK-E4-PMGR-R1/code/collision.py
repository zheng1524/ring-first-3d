"""Whole-triangle FCL distance plus Open3D signs; no sampled-only clearance PASS."""
from inputs import *
import fcl
def fcl_object(V,F):
    m=fcl.BVHModel();m.beginModel(len(V),len(F));m.addSubModel(np.asarray(V,float),np.asarray(F,np.int32));m.endModel();return fcl.CollisionObject(m)
class Collision:
    def __init__(self,scene):
        self.scene=scene;cad=ringmesh(scene);self.V=np.asarray(cad.vertices);self.F=np.asarray(cad.faces);self.obj=fcl_object(self.V,self.F);self.rt=ringscene(scene);self.scale=max(1,float(abs(self.V).max()));self.eps=64*np.finfo(np.float32).eps*self.scale
        self.sample=np.vstack([self.V,self.V[self.F].mean(1)]);tri=self.V[self.F];self.cover=float(np.linalg.norm(tri-np.roll(tri,1,axis=1),axis=2).max()/np.sqrt(3))
    def check(self,V,F,contacts=False):
        obj=fcl_object(V,F);req=fcl.CollisionRequest(num_max_contacts=64 if contacts else 1,enable_contact=contacts);res=fcl.CollisionResult();n=fcl.collide(obj,self.obj,req,res);dr=fcl.DistanceResult();d=fcl.distance(obj,self.obj,fcl.DistanceRequest(enable_nearest_points=True),dr)if not n else-1.
        sd=self.rt.compute_signed_distance(o3d.core.Tensor(np.asarray(V,np.float32))).numpy();body=mesh_scene(V,F);cd=body.compute_signed_distance(o3d.core.Tensor(self.V.astype(np.float32))).numpy();penetrates=bool(n or sd.min()<-self.eps or cd.min()<-self.eps)
        return dict(collision=penetrates,triangle_collision=bool(n),distance_mm=float(d),body_vertex_min_signed_mm=float(sd.min()),CAD_vertex_min_signed_mm=float(cd.min()),numeric_eps_mm=self.eps,body_face=int(dr.b1),CAD_face=int(dr.b2),nearest_points=dr.nearest_points if not n else None,contacts=[dict(body_face=int(c.b1),CAD_face=int(c.b2),position=np.array(c.pos),normal=np.array(c.normal),penetration_depth=float(c.penetration_depth))for c in res.contacts]if contacts else[])
    def constraints(self,V,F,J,activation_distance=.75):
        rt=mesh_scene(V,F);pts=self.sample;hit=rt.compute_closest_points(o3d.core.Tensor(pts.astype(np.float32)));fid=hit['primitive_ids'].numpy().astype(int);uv=hit['primitive_uvs'].numpy();w=np.c_[1-uv.sum(1),uv];q=(V[F[fid]]*w[:,:,None]).sum(1);delta=pts-q;dist=np.linalg.norm(delta,axis=1);sign=np.sign(rt.compute_signed_distance(o3d.core.Tensor(pts.astype(np.float32))).numpy());signed=dist*sign;sel=np.flatnonzero(signed<activation_distance);normal=delta[sel]/np.maximum(dist[sel,None],1e-15)*sign[sel,None];jq=(J[F[fid[sel]]]*w[sel,:,None,None]).sum(1);grad=-np.einsum('ij,ijk->ik',normal,jq)
        # Near-active unique normals/locations retained, not just one minimum.
        return signed[sel],grad,dict(active_constraints_N=len(sel),CAD_sample_indices=sel,body_faces=fid[sel])
    def path(self,A,B,F,depth=0):
        ca=self.check(A,F);cb=self.check(B,F)
        if ca['collision']or cb['collision']:return False,dict(reason='ENDPOINT_PENETRATION',depth=depth)
        move=float(np.linalg.norm(B-A,axis=1).max())
        if min(ca['distance_mm'],cb['distance_mm'])>move+self.eps:return True,dict(reason='LIPSCHITZ_SEPARATION',depth=depth)
        if depth>=8:return False,dict(reason='SWEEP_CLEARANCE_UNCERTAIN',depth=depth)
        M=(A+B)/2;cm=self.check(M,F)
        if cm['collision']:return False,dict(reason='INTERMEDIATE_PENETRATION',depth=depth)
        ok,l=self.path(A,M,F,depth+1)
        if not ok:return ok,l
        return self.path(M,B,F,depth+1)
