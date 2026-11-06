"""Independent raw CAD/body triangle QA, no GT or source scene edits."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(sys.argv[sys.argv.index('--')+1]);rows=[]
for c in json.loads((r/'config/CASE_LOCK.json').read_text()):
 n=c['name'];rr=np.load(r/'inputs'/n/'RING.npz');rt=BVHTree.FromPolygons([Vector(x)for x in rr['V']],rr['F'].tolist(),all_triangles=True,epsilon=0.)
 for arm in['A','B','C']:
  z=np.load(r/'inputs'/n/'INITIAL.npz'if arm=='A'else r/'local_results'/n/(arm+'_SELECTED.npz'));V=z['V'];F=z['F_solid']if'F_solid'in z else z['F'];t=BVHTree.FromPolygons([Vector(x)for x in V],F.tolist(),all_triangles=True,epsilon=0.);ri=t.overlap(rt);si=[[int(i),int(j)]for i,j in t.overlap(t)if i<j and not np.intersect1d(F[i],F[j]).size];rows.append(dict(case=n,arm=arm,Ring_intersection_pair_N=len(ri),Ring_pairs=ri[:64],nonadjacent_self_pair_N=len(si),self_pairs=si[:128],geometry_modified=False,Blender=bpy.app.version_string));print(n,arm,len(ri),len(si),flush=True)
(r/'metrics/BLENDER_GEOMETRY.json').write_text(json.dumps(rows,indent=2))
