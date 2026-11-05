"""Original frozen camera/material settings; rebuild meshes for differing DMTet topology."""
import bpy,sys,json,numpy as np,os
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['E4_CURRENT_RUN']).resolve();cams=json.loads((R/'inputs/CAMERAS.json').read_text());base=np.load(R/'inputs/BASE_SOURCE_MESH.npz');gt=np.load(R/'audit_only/TARGET_GT.npz');cad=np.load(R/'inputs/RING_CAD.npz')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.seed=2026110502;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.unit_settings.scale_length=.001;scene.view_settings.view_transform='Raw';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False;scene.cycles.pixel_filter_type='BOX';scene.cycles.filter_width=1.
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1)
def material(name,col):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();o=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=col;m.node_tree.links.new(e.outputs[0],o.inputs['Surface']);return m
def mesh(name,V,F,mat):
    m=bpy.data.meshes.new(name);m.from_pydata(V.tolist(),[],F.tolist());m.update();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);m.materials.append(mat);return o
bodymat=material('BODY',(1,0,0,1));ring=mesh('FROZEN_RING_CAD',cad['V'],cad['F'],material('RING',(0,1,0,1)));body=None
camdata=bpy.data.cameras.new('FROZEN_CAMERA');cam=bpy.data.objects.new('FROZEN_CAMERA',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='PERSP';camdata.sensor_fit='HORIZONTAL';camdata.sensor_width=36;camdata.clip_start=.01;camdata.clip_end=1000
logs=[]
for name,data in [('BASE',base),('TARGET',gt)]:
    V=data['V'];F=data['F']
    if body is not None:bpy.data.objects.remove(body,do_unlink=True)
    body=mesh(name+'_DMTET_MESH',V,F,bodymat);bpy.context.view_layer.update()
    for c in cams:
        W,H=c['width'],c['height'];K=np.array(c['K_edge']);T=np.array(c['c2w_mm']);scene.render.resolution_x=W;scene.render.resolution_y=H;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=max(1,K[1,1]/K[0,0]);scene.render.pixel_aspect_y=max(1,K[0,0]/K[1,1]);camdata.lens=K[0,0]*36/W;camdata.shift_x=(W/2-K[0,2])/W;camdata.shift_y=(K[1,2]-H/2)/W*(K[0,0]/K[1,1]);cam.matrix_world=Matrix(T@np.diag([1,-1,-1,1]));bpy.context.view_layer.update()
        errors=[]
        for point in V[::max(1,len(V)//100)]:
            p=world_to_camera_view(scene,cam,Vector(point));uv=np.array([p.x*W-.5,(1-p.y)*H-.5]);x=(point-T[:3,3])@T[:3,:3];q=K@x;q=q[:2]/q[2]-.5;errors.append(float(np.linalg.norm(uv-q)))
        assert max(errors)<.001
        out=R/'inputs'/f'{name}__{c["id"]}.png';scene.render.filepath=str(out);bpy.ops.render.render(write_still=True);logs.append(dict(state=name,view=c['id'],max_point_error_px=max(errors),body_identity='the same frozen state mesh for all five views',Ring_identity='identical frozen CAD in both states',vertices=len(V),faces=len(F)))
(R/'metrics/BLENDER_RENDER_IDENTITY.json').write_text(json.dumps(dict(Blender=bpy.app.version_string,unit='mm',view_transform='Raw linear emission',rows=logs,source_overwritten=False,topology_handling='recreate actual DMTet vertex and face arrays per state, never zip meshes with different topology'),indent=2));print('BLENDER_MASKS_DONE',R.name,flush=True)
