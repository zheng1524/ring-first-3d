"""Independent endpoint check; no mesh edits and no source .blend loading."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
inp,out=sys.argv[sys.argv.index('--')+1:];a=np.load(inp);V=a['V'];F=a['F']
tree=BVHTree.FromPolygons([Vector(v)for v in V],F.tolist(),all_triangles=True,epsilon=0.)
pairs=tree.overlap(tree);bad=[]
for i,j in pairs:
    if i>=j or np.intersect1d(F[i],F[j]).size:continue
    bad.append([int(i),int(j)])
Path(out).write_text(json.dumps(dict(Blender=bpy.app.version_string,nonadjacent_intersecting_triangle_pairs_N=len(bad),first_pairs=bad[:64],method='BVHTree self-overlap epsilon zero, distinct triangles sharing no vertex',limitation='adjacent/degenerate triangle overlap is not independently certified; no surface repair',geometry_modified=False),indent=2))
