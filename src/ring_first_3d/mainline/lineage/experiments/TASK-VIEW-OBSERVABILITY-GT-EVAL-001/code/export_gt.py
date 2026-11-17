"""Blender EVALUATION-ONLY: explicit audited objects, no registration/GT cameras."""
import bpy,numpy as np,json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
assert(R/'provenance/PREDICTIONS_FROZEN.json').exists()
audit=json.loads(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/multigroup_surface_gt_vnext/gt_mapping/GT_ASSET_AUDIT.json').read_text());records=[]
out=R/'evaluation_only';out.mkdir(exist_ok=True)
for rec in audit['groups']:
    if rec['group']not in ['G01','G06','G07','G08']:continue
    p=Path(rec['source']);h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==rec['SHA256']
    bpy.ops.wm.open_mainfile(filepath=str(p));scene=bpy.context.scene;obj=scene.objects[rec['selected_object']];ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();factor=float(scene.unit_settings.scale_length)*1000;P=np.array([list(obj.matrix_world@v.co)for v in mesh.vertices])*factor;F=np.array([list(t.vertices)for t in mesh.loop_triangles]);ev.to_mesh_clear()
    cached=np.load(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/multigroup_surface_gt_vnext/gt_mapping')/(rec['group']+'_TRUSTED_GT.npz'));assert np.array_equal(P,cached['vertices_mm'])and np.array_equal(F,cached['faces'])
    np.savez_compressed(out/(rec['group']+'_verified_gt.npz'),vertices_mm=P,faces=F)
    records.append(dict(group=rec['group'],source=str(p),sha256=h,selected_object=obj.name,world_to_mm=factor,unit_system=scene.unit_settings.system,objects=[dict(name=o.name,type=o.type,vertex_groups=[v.name for v in o.vertex_groups]if o.type=='MESH'else[],custom_properties={k:str(v)for k,v in o.items()})for o in scene.objects],cached_export_exact=True,Blender=bpy.app.version_string,real_deployment_transform=None))
    print('GT_VERIFIED',rec['group'],len(P),len(F),flush=True)
(out/'BLENDER_VERIFICATION.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
