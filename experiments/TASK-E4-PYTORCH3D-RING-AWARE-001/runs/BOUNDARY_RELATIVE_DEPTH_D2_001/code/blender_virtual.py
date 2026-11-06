"""Read-only native Blender sources. Fixed scene across all cameras; no source save."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parents[1];name=sys.argv[sys.argv.index('--')+1];cfg=json.loads((R/'config'/(name+'_SCENE.json')).read_text());out=R/'inputs'/name
bpy.ops.wm.open_mainfile(filepath=cfg['source']['path'],load_ui=False,use_scripts=False);ob=bpy.data.objects['球体'];bpy.context.view_layer.update();ob.data.calc_loop_triangles();V=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices])*1000;F=np.array([p.vertices[:]for p in ob.data.loop_triangles],int);V[:,:2]-=(V[:,:2].max(0)+V[:,:2].min(0))/2;V[:,2]-=V[:,2].min();assert not ob.modifiers and not ob.animation_data and not ob.data.shape_keys
(R/'audit_only'/name).mkdir(exist_ok=True);np.savez_compressed(R/'audit_only'/name/'GT.npz',V=V,F=F)
bpy.ops.wm.open_mainfile(filepath=cfg['ring_scene'],load_ui=False,use_scripts=False);ob=bpy.data.objects['ring_R10'];ob.location=cfg['ring_center_mm'];bpy.context.view_layer.update();ob.data.calc_loop_triangles();RV=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices]);RF=np.array([p.vertices[:]for p in ob.data.loop_triangles],int);np.savez_compressed(out/'RING.npz',V=RV,F=RF)
# The old generic Gate A P0, translated with Ring only; never fit to this GT.
old=R.parent/'PROGRESSIVE_HERO_001/inputs/virtual';a=np.load(old/'INITIAL.npz');rc=np.load(old/'RING.npz')['V'].mean(0);np.savez_compressed(out/'INITIAL.npz',V=a['V']+RV.mean(0)-rc,F=a['F'])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.seed=2026110502;sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.unit_settings.scale_length=.001;sc.view_settings.view_transform='Raw';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.film_transparent=False;sc.cycles.pixel_filter_type='BOX';sc.cycles.filter_width=1.;sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1)
def mat(name,col):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();o=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=col;m.node_tree.links.new(e.outputs[0],o.inputs['Surface']);return m
def obj(name,v,f,color):
 m=bpy.data.meshes.new(name);m.from_pydata(v.tolist(),[],f.tolist());m.update();o=bpy.data.objects.new(name,m);sc.collection.objects.link(o);m.materials.append(mat(name,color))
obj('BODY',V,F,(1,0,0,1));obj('CAD',RV,RF,(0,1,0,1));cd=bpy.data.cameras.new('FIXED');cam=bpy.data.objects.new('FIXED',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='PERSP';cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.clip_start=.01;cd.clip_end=1000;logs=[]
for c in cfg['cameras']:
 W,H=c['width'],c['height'];K=np.array(c['K_edge']);T=np.array(c['c2w_mm']);sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=max(1,K[1,1]/K[0,0]);sc.render.pixel_aspect_y=max(1,K[0,0]/K[1,1]);cd.lens=K[0,0]*36/W;cd.shift_x=(W/2-K[0,2])/W;cd.shift_y=(K[1,2]-H/2)/W*K[0,0]/K[1,1];cam.matrix_world=Matrix(T@np.diag([1,-1,-1,1]));bpy.context.view_layer.update();err=[]
 for point in V[::max(1,len(V)//100)]:
  p=world_to_camera_view(sc,cam,Vector(point));uv=np.array([p.x*W-.5,(1-p.y)*H-.5]);x=(point-T[:3,3])@T[:3,:3];q=K@x;err.append(np.linalg.norm(uv-(q[:2]/q[2]-.5)))
 assert max(err)<.001
 sc.render.filepath=str(out/(c['id']+'_LABEL.png'));bpy.ops.render.render(write_still=True);logs.append(dict(view=c['id'],projection_max_px=float(max(err)),same_static_V_F_and_Ring=True))
(R/'metrics'/(name+'_BLENDER.json')).write_text(json.dumps(dict(rows=logs,body_extent_mm=np.ptp(V,axis=0).tolist(),Ring_extent_mm=np.ptp(RV,axis=0).tolist(),Blender=bpy.app.version_string,source_modified=False,native_to_mm=1000,extra_scaling=1),indent=2));print('DONE',name)
