"""GT generation only: unedited native mesh; source .blend stays read-only."""
import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source='/home/liu/polyp_research/experiments/geometric_validation_v1/assets/IIa6.5.blend'
bpy.ops.wm.open_mainfile(filepath=source,load_ui=False,use_scripts=False)
ob=bpy.data.objects['球体'];bpy.context.view_layer.update();ob.data.calc_loop_triangles()
assert len(ob.modifiers)==0 and not ob.data.shape_keys and not ob.animation_data
V=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices])*1000
F=np.array([t.vertices[:]for t in ob.data.loop_triangles],int)
offset=np.r_[(V[:,:2].max(0)+V[:,:2].min(0))/2,V[:,2].min()];V-=offset
np.savez_compressed(R/'audit_only/NATIVE_CAD_GT.npz',V=V,F=F)
(R/'metrics/NATIVE_EXPORT.json').write_text(json.dumps(dict(source=source,object='球体',native_vertices=len(V),native_faces=len(F),source_vertex_scale_to_mm=1000,scene_translation_mm=(-offset).tolist(),no_local_edit=True,no_GT_SDF_generated_for_optimizer=True,source_saved=False,Blender=bpy.app.version_string),indent=2))
