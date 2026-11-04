"""Factory-empty Blender process, only supplied CAD/body arrays; never .blend GT."""
import bpy,sys,json,numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from pathlib import Path
def check(inp,out):
    data=np.load(inp);V=data['V'];F=data['F'];CV=data['CAD_V'];CF=data['CAD_F'];bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    def make(name,p,f):
        m=bpy.data.meshes.new(name);m.from_pydata(p.tolist(),[],f.tolist());m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o
    a=make('CURRENT_BODY_NOT_GT',V,F);b=make('FROZEN_RING_CAD',CV,CF);ta=BVHTree.FromPolygons([Vector(v)for v in V],F.tolist(),all_triangles=True,epsilon=0.);tb=BVHTree.FromPolygons([Vector(v)for v in CV],CF.tolist(),all_triangles=True,epsilon=0.);overlap=ta.overlap(tb)
    bpy.context.view_layer.objects.active=a;mod=a.modifiers.new('INDEPENDENT_SOLID_INTERSECTION','BOOLEAN');mod.operation='INTERSECT';mod.solver='EXACT';mod.object=b;ev=a.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();p=np.array([v.co[:]for v in m.vertices]);f=np.array([t.vertices[:]for t in m.loop_triangles],int);volume=abs(float(np.einsum('ij,ij->i',p[f[:,0]],np.cross(p[f[:,1]],p[f[:,2]])).sum()/6))if len(f)else 0.;ev.to_mesh_clear()
    nearest=min(tb.find_nearest(Vector(v))[3]for v in V);result=dict(Blender_version=bpy.app.version_string,build_hash=bpy.app.build_hash.decode(),body_vertices=len(V),CAD_vertices=len(CV),BVH_intersecting_triangle_pairs=len(overlap),first_intersections=overlap[:64],EXACT_intersection_volume_mm3=volume,body_vertex_unsigned_nearest_mm=nearest,GT_or_existing_blend_opened=False,scene_start='--factory-startup')
    Path(out).write_text(json.dumps(result,indent=2));print('BLENDER_COLLISION_RESULT',json.dumps(result))
args=sys.argv[sys.argv.index('--')+1:];check(args[0],args[1])
