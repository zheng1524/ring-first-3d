"""Read-only Blender asset export. Never save the source .blend or run its scripts."""
import bpy,sys,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'config/SCENE_INPUTS.json').read_text());meta=[]
bpy.ops.wm.open_mainfile(filepath=cfg['source'],load_ui=False,use_scripts=False);ob=bpy.data.objects['球体'];bpy.context.view_layer.update();ob.data.calc_loop_triangles();V=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices])*1000;F=np.array([p.vertices[:]for p in ob.data.loop_triangles],int)
# Exactly the historical millimeter centering, with no subtype-specific geometry editing.
V[:,:2]-=(V[:,:2].max(0)+V[:,:2].min(0))/2;V[:,2]-=V[:,2].min();mods=[dict(name=m.name,type=m.type,render=m.show_render)for m in ob.modifiers]
np.savez_compressed(R/'inputs/BASE_SOURCE_MESH.npz',V=V,F=F)
meta.append(dict(role='BODY',V=len(V),F=len(F),modifiers=mods,shape_keys=bool(ob.data.shape_keys),animation=bool(ob.animation_data),native_matrix=np.array(ob.matrix_world).tolist(),extent_mm=np.ptp(V,axis=0).tolist()))
bpy.ops.wm.open_mainfile(filepath=cfg['Ring_scene'],load_ui=False,use_scripts=False);ob=bpy.data.objects['ring_R10'];ob.location=cfg['seed']['ring_center_mm'];bpy.context.view_layer.update();ob.data.calc_loop_triangles();CV=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices]);CF=np.array([p.vertices[:]for p in ob.data.loop_triangles],int);np.savez_compressed(R/'inputs/RING_CAD.npz',V=CV,F=CF)
meta.append(dict(role='RING',V=len(CV),F=len(CF),matrix_world=np.array(ob.matrix_world).tolist(),modifiers=[dict(name=m.name,type=m.type,render=m.show_render)for m in ob.modifiers],extent_mm=np.ptp(CV,axis=0).tolist()))
(R/'metrics/BLENDER_ASSET_EXPORT.json').write_text(json.dumps(dict(objects=meta,Blender=bpy.app.version_string,source_write=False),indent=2));print('EXPORTED',meta,flush=True)
