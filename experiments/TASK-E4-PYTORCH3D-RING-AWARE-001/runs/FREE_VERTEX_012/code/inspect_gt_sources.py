import bpy,sys,json,numpy as np
from pathlib import Path
r=Path(sys.argv[sys.argv.index('--')+1]);assert(r/'assets_index/SCALE_LOCK_BEFORE_GT.json').exists();rows=[]
for src in json.loads((r/'evaluation_only/GT_CANDIDATE_SOURCES.json').read_text()):
 if not Path(src['path']).exists():rows.append(dict(**src,objects=[]));continue
 bpy.ops.wm.open_mainfile(filepath=src['path']);objects=[];deps=bpy.context.evaluated_depsgraph_get()
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  eo=o.evaluated_get(deps);m=eo.to_mesh();m.calc_loop_triangles();V=np.array([v.co[:]for v in m.vertices]);M=np.array(eo.matrix_world);V=(np.c_[V,np.ones(len(V))]@M.T)[:,:3];F=np.array([t.vertices[:]for t in m.loop_triangles]);bottom=abs(V[:,2]-V[:,2].min())<1e-9;objects.append(dict(name=o.name,vertices=len(V),triangles=len(F),world_min=V.min(0).tolist(),world_max=V.max(0).tolist(),matrix_world=M.tolist(),bottom_vertex_N=int(bottom.sum()),bottom_triangle_N=int(bottom[F].all(1).sum()),modifiers=[x.name for x in o.modifiers],animated=bool(o.animation_data),shape_keys=[]if o.data.shape_keys is None else[(k.name,k.value)for k in o.data.shape_keys.key_blocks]));eo.to_mesh_clear()
 rows.append(dict(**src,unit_system=bpy.context.scene.unit_settings.system,scale_length=bpy.context.scene.unit_settings.scale_length,frame_current=bpy.context.scene.frame_current,objects=objects));print('INSPECT',src['case'],objects,flush=True)
(r/'evaluation_only/GT_SOURCE_INSPECTION.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
