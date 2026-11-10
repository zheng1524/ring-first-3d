"""Existing static virtual GT/CAD, same cameras; direct320 Blender target cache."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[1]
native=json.loads((R/'metrics/VIRTUAL_NATIVE_PROJECTION_GATE.json').read_text());g=np.load(native['GT_source']['path']);ring=np.load(R/'inputs/virtual_Ip/RING.npz');out=R/'local_results/virtual_render320';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.seed=20261110;sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.unit_settings.scale_length=.001;sc.view_settings.view_transform='Raw';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.film_transparent=False;sc.cycles.pixel_filter_type='BOX';sc.cycles.filter_width=1.;sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1)
def obj(name,V,F,color):
 m=bpy.data.meshes.new(name);m.from_pydata(V.tolist(),[],F.tolist());m.update();o=bpy.data.objects.new(name,m);sc.collection.objects.link(o);mat=bpy.data.materials.new(name);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();output=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=color;mat.node_tree.links.new(em.outputs[0],output.inputs['Surface']);m.materials.append(mat)
obj('BODY',g['V'],g['F'],(1,0,0,1));obj('FIXED_CAD',ring['V'],ring['F'],(0,1,0,1));cd=bpy.data.cameras.new('FIXED');cam=bpy.data.objects.new('FIXED',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='PERSP';cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.clip_start=.01;cd.clip_end=1000;records=[]
meta=json.loads((R/'inputs/virtual_Ip/CASE.json').read_text())
for v in meta['views']:
 a=np.load(R/'inputs/virtual_Ip'/(v['id']+'.npz'));K=a['K'].copy();K[:2,2]+=.5;K[:2]*=.5;T=a['T'];W,H=320,180;sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=max(1,K[1,1]/K[0,0]);sc.render.pixel_aspect_y=max(1,K[0,0]/K[1,1]);cd.lens=K[0,0]*36/W;cd.shift_x=(W/2-K[0,2])/W;cd.shift_y=(K[1,2]-H/2)/W*K[0,0]/K[1,1];cam.matrix_world=Matrix(T@np.diag([1,-1,-1,1]));bpy.context.view_layer.update();sc.render.filepath=str(out/(v['id']+'.png'));bpy.ops.render.render(write_still=True);records.append(dict(view=v['id'],K_edge320=K.tolist(),c2w_mm=T.tolist(),same_static_geometry=True))
(out/'BLENDER_RENDER_CONTRACT.json').write_text(json.dumps(dict(rows=records,Blender=bpy.app.version_string,body_and_CAD_geometry_unchanged=True,source_GT=native['GT_source'],purpose='repair sensor-grid target generation; no geometry/pose/parameter search'),indent=2)+'\n')
