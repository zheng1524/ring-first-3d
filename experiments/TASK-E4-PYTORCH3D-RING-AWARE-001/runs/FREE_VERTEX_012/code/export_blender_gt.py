"""Evaluation-only: exact source identities, original evaluated meshes, no prediction edits."""
import bpy,sys,json,hashlib,numpy as np
from pathlib import Path
r=Path(sys.argv[sys.argv.index('--')+1]);assert(r/'assets_index/SCALE_LOCK_BEFORE_GT.json').exists();lock=json.loads((r/'evaluation_only/GT_SOURCE_LOCK.json').read_text());out=[]
for c in lock:
 if c.get('status')!='MATCHED' or c.get('kind')!='blend':continue
 p=Path(c['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==c['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));deps=bpy.context.evaluated_depsgraph_get();verts=[];faces=[];offset=0;records=[]
 for name in c['body_objects']:
  o=bpy.data.objects.get(name);assert o is not None and o.type=='MESH',name;eo=o.evaluated_get(deps);m=eo.to_mesh();m.calc_loop_triangles();M=np.array(eo.matrix_world);V=np.array([v.co[:]for v in m.vertices]);V=(np.c_[V,np.ones(len(V))]@M.T)[:,:3]*c['unit_to_mm'];F=np.array([t.vertices[:]for t in m.loop_triangles],int);verts.append(V);faces.append(F+offset);offset+=len(V);records.append(dict(name=name,matrix_world=M.tolist(),modifiers=[x.name for x in o.modifiers],original_vertex_N=len(o.data.vertices),evaluated_vertex_N=len(V)));eo.to_mesh_clear()
 directory=r/'evaluation_only'/c['case'];directory.mkdir(exist_ok=True);np.savez_compressed(directory/'ORIGINAL_BLENDER_GT_MM.npz',V=np.concatenate(verts),F=np.concatenate(faces));meta=dict(case=c['case'],path=str(p),source_sha256=c['sha256'],source_identity=c['identity'],unit_to_mm=c['unit_to_mm'],unit_evidence=c['unit_evidence'],scene_unit_system=bpy.context.scene.unit_settings.system,scene_scale_length=bpy.context.scene.unit_settings.scale_length,body_objects=records,author_base=c.get('author_base'),GT_used_only_after_prediction_and_scale_freeze=True,geometry_modified=False,Blender=bpy.app.version_string);(directory/'GT_EXTRACTION.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));out.append(meta);print('GT_EXPORTED',c['case'],len(np.concatenate(verts)),flush=True)
(r/'evaluation_only/BLENDER_EXPORTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
