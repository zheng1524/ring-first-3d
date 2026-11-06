import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(sys.argv[sys.argv.index('--')+1]);rows=[]
for c in json.loads((r/'config/CASE_LOCK.json').read_text()):
 n=c['name'];z=np.load(r/'inputs'/n/'INITIAL.npz');rr=np.load(r/'inputs'/n/'RING.npz');F=z['F_solid'];body=BVHTree.FromPolygons([Vector(x)for x in z['V']],F.tolist(),all_triangles=True,epsilon=0.);ring=BVHTree.FromPolygons([Vector(x)for x in rr['V']],rr['F'].tolist(),all_triangles=True,epsilon=0.);pairs=body.overlap(ring);selfpairs=[(i,j)for i,j in body.overlap(body)if i<j and not np.intersect1d(F[i],F[j]).size];rows.append(dict(case=n,Ring_pairs_N=len(pairs),nonadjacent_self_N=len(selfpairs),self_pairs=selfpairs[:64],geometry_modified=False));print(n,len(pairs),len(selfpairs),flush=True)
(r/'metrics/INITIAL_BLENDER.json').write_text(json.dumps(rows,indent=2))
