"""Pinned Blender EXACT Boolean only; no scene/GT loading or geometry repair."""
import sys,json
from pathlib import Path
import bpy,bmesh,numpy as np
request=Path(sys.argv[sys.argv.index('--')+1]);r=json.loads(request.read_text())
for key in ['body','sweep','output']:r[key]=str((request.parent/r[key]).resolve())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
materials=[bpy.data.materials.new('FROZEN_BODY'),bpy.data.materials.new('EXPOSED_SWEEP')]
def obj(name,path,material):
    a=np.load(path);m=bpy.data.meshes.new(name);m.from_pydata(a['V'].tolist(),[],a['F'].tolist());m.update()
    o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o)
    for mat in materials:m.materials.append(mat)
    for p in m.polygons:p.material_index=material
    return o
a=obj('frozen_body',r['body'],0);b=obj('embedded_sweep',r['sweep'],1)
bpy.context.view_layer.objects.active=a
modifier=a.modifiers.new('EXACT_LOCAL_EMBEDDED_UNION','BOOLEAN');modifier.operation='UNION';modifier.solver='EXACT';modifier.object=b
modifier.use_self=False;modifier.use_hole_tolerant=False
bpy.ops.object.modifier_apply(modifier=modifier.name)
m=a.data;m.calc_loop_triangles()
rawV=np.array([v.co[:]for v in m.vertices],float);rawF=np.array([t.vertices[:]for t in m.loop_triangles],np.int64)
np.savez_compressed(Path(r['output']).with_name('RAW_EXACT_BOOLEAN.npz'),V=rawV,F=rawF)
# Stitch numerical aliases at the Boolean intersection, never delete crossing faces
# or fill a boundary. BEAUTY triangulation avoids collinear ngon ears.
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
bm.to_mesh(m);bm.free();m.update();m.calc_loop_triangles();V=np.array([v.co[:]for v in m.vertices],float)
F=np.array([t.vertices[:]for t in m.loop_triangles],np.int64)
source=np.array([m.polygons[t.polygon_index].material_index for t in m.loop_triangles],np.int64)
np.savez_compressed(r['output'],V=V,F=F,face_operand=source)
Path(r['output']).with_suffix('.json').write_text(json.dumps(dict(backend='Blender',version=bpy.app.version_string,solver='EXACT',operation='UNION',self_operand_repair=False,hole_fill=False,face_deletion_by_intersection=False,numerical_alias_stitch_mm=1e-8,triangulation='BEAUTY',raw_vertices=len(rawV),raw_triangles=len(rawF),faces=len(F)),indent=2))

