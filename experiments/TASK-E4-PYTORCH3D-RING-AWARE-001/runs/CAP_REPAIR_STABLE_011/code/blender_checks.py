import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(sys.argv[sys.argv.index('--')+1]);rows=[]
for m in json.loads((r/'metrics/ALL_STAGE_SUMMARY.json').read_text()):
 rr=np.load(r/'inputs'/m['case']/'RING.npz');z=np.load(m['path']);V=z['V'];F=z['F_solid'];t=BVHTree.FromPolygons([Vector(v)for v in V],F.tolist(),all_triangles=True,epsilon=0.);ring=BVHTree.FromPolygons([Vector(v)for v in rr['V']],rr['F'].tolist(),all_triangles=True,epsilon=0.);rp=t.overlap(ring);sp=[(i,j)for i,j in t.overlap(t)if i<j and not np.intersect1d(F[i],F[j]).size];rows.append(dict(case=m['case'],label=m['label'],step=m['step'],Ring_pairs_N=len(rp),self_intersections_N=len(sp),self_pairs=sp[:128],Ring_pairs=rp[:64],Blender=bpy.app.version_string,geometry_modified=False));print(m['case'],m['label'],m['step'],len(rp),len(sp),flush=True)
(r/'metrics/BLENDER_GEOMETRY.json').write_text(json.dumps(rows,indent=2))
