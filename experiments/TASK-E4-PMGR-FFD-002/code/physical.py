from inputs import *
from collision import Collision
from mesh_checks import self_intersections
import subprocess
BLENDER='/home/liu/blender/blender-5.0.1-linux-x64/blender'
def volume(V,F):
    t=V[F];return float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
def blender_check(name,scene,V,F,cad=None):
    ring=ringmesh(scene)if cad is None else cad;inp=R/'runtime'/(name+'_Blender.npz');out=R/'metrics'/(name+'_BLENDER.json');np.savez_compressed(inp,V=V,F=F,CAD_V=ring.vertices,CAD_F=ring.faces)
    p=subprocess.run([BLENDER,'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(R/'code/blender_check.py'),'--',str(inp),str(out)],capture_output=True,text=True,timeout=120)
    (R/'runtime'/(name+'_Blender.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-1000:];return load(out)
def quality(V,F,reference):
    mesh=trimesh.Trimesh(V,F,process=False);tri=V[F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1);si=self_intersections(V,F);reasons=[]
    if not np.isfinite(V).all():reasons.append('NONFINITE')
    if not mesh.is_watertight or not mesh.is_winding_consistent:reasons.append('TOPOLOGY_OR_WINDING')
    if area.min()<1e-8 or volume(V,F)<=0:reasons.append('DEGENERATE_OR_INVERTED_BODY')
    if si['intersections']or si['coplanar_candidates']:reasons.append('SELF_INTERSECTION_OR_UNRESOLVED_COPLANAR')
    return reasons,dict(min_twice_face_area_mm2=float(area.min()),volume_mm3=volume(V,F),volume_ratio=volume(V,F)/volume(reference,F),**si)
def endpoint(col,V,F,name=None):
    z=col.check(V,F,True)
    if z['triangle_collision']and min(z['body_vertex_min_signed_mm'],z['CAD_vertex_min_signed_mm'])>=-col.eps and name:
        b=blender_check(name,col.scene,V,F);z['contact_Blender']=b
        if b['EXACT_intersection_volume_mm3']<=1e-8:z.update(collision=False,distance_mm=0.,numerical_contact=True)
    return z
