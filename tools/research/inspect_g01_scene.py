"""Read-only Blender inventory; never infer a deployment transform from shape."""
import bpy
import json,sys,hashlib
from pathlib import Path
import numpy as np

r=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
p=Path(r['blend']['path'])
assert hashlib.sha256(p.read_bytes()).hexdigest()==r['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(p))
s=bpy.context.scene;scale=s.unit_settings.scale_length*1000
deps=bpy.context.evaluated_depsgraph_get();rows=[]
for obj in bpy.data.objects:
    row=dict(name=obj.name,type=obj.type,in_active_scene=obj.name in s.objects,
             matrix_world=[list(x)for x in obj.matrix_world],custom_properties={k:str(obj[k])for k in obj.keys()})
    if obj.type=='MESH':
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
        # Match the registered historical exporter exactly: NumPy float64
        # homogeneous transform, not mathutils float32 multiplication.
        M=np.array(evaluated.matrix_world);V=np.array([v.co[:]for v in mesh.vertices])
        V=(np.c_[V,np.ones(len(V))]@M.T)[:,:3]*scale
        F=np.array([list(t.vertices)for t in mesh.loop_triangles],dtype=np.int64)
        row.update(vertices=len(V),faces=len(F),bounds_mm=[V.min(0).tolist(),V.max(0).tolist()])
        if obj.name=='球体':np.savez_compressed(Path(r['output'])/'fresh_body_mm.npz',V=V,F=F)
        evaluated.to_mesh_clear()
    rows.append(row)
out=dict(source_sha256=r['blend']['sha256'],Blender=bpy.app.version_string,
         unit_system=s.unit_settings.system,scale_length=s.unit_settings.scale_length,
         unit_to_mm=scale,objects=rows,scenes=[x.name for x in bpy.data.scenes],
         active_scene=s.name,active_camera=s.camera.name if s.camera else None,
         note='Inventory only. Object names or identity author matrix do not certify real Ring deployment.')
(Path(r['output'])/'BLENDER_SCENE_INVENTORY.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
