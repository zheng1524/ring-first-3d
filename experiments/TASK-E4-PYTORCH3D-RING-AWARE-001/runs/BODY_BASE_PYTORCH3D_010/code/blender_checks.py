"""Independent Blender CAD intersections/self-intersections on unmodified exported meshes."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(sys.argv[sys.argv.index('--')+1]);rows=[]
for m in json.loads((r/'metrics/ALL_STAGE_SUMMARY.json').read_text()):
 rr=np.load(r/'inputs'/m['case']/'RING.npz');rt=BVHTree.FromPolygons([Vector(v)for v in rr['V']],rr['F'].tolist(),all_triangles=True,epsilon=0.)
 z=np.load(m['path']);V=z['V'];F=z['F_solid'];body=BVHTree.FromPolygons([Vector(v)for v in V],F.tolist(),all_triangles=True,epsilon=0.);rp=body.overlap(rt);sp=[[int(i),int(j)]for i,j in body.overlap(body)if i<j and not np.intersect1d(F[i],F[j]).size];row=dict(case=m['case'],route=m['route'],label=m['label'],step=m['step'],Ring_triangle_pair_N=len(rp),nonadjacent_self_pair_N=len(sp),Ring_pairs=rp[:64],self_pairs=sp[:128],Blender=bpy.app.version_string,geometry_modified=False);rows.append(row);print(m['case'],m['route'],m['label'],len(rp),len(sp),flush=True)
(r/'metrics/BLENDER_GEOMETRY.json').write_text(json.dumps(rows,indent=2))
