"""Independent read-only final raw-mesh intersection checks, no scene/GT loading."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(sys.argv[sys.argv.index('--')+1]);out=[]
for name in ['virtual','real']:
    r=np.load(root/'inputs'/name/'RING.npz');rv=r['V'];rf=r['F'];rt=BVHTree.FromPolygons([Vector(x)for x in rv],rf.tolist(),all_triangles=True,epsilon=0.)
    cfg=json.loads((root/'config/PROTOCOL.json').read_text())
    for arm,path in [('P0',root/'inputs'/name/'INITIAL.npz'),('A',Path(cfg['A_frozen_root'])/'local_results'/name/'RingAware/FINAL.npz')]+[(a,root/'local_results'/name/a/'FINAL.npz')for a in['B','C','D']if(root/'local_results'/name/a/'FINAL.npz').exists()]:
        a=np.load(path);V=a['V'];F=a['F'];bt=BVHTree.FromPolygons([Vector(x)for x in V],F.tolist(),all_triangles=True,epsilon=0.)
        hits=bt.overlap(rt);bad=[]
        for i,j in bt.overlap(bt):
            if i<j and not np.intersect1d(F[i],F[j]).size:bad.append([int(i),int(j)])
        out.append(dict(case=name,arm=arm,Ring_intersecting_triangle_pair_N=len(hits),nonadjacent_self_intersection_pair_N=len(bad),first_Ring_pairs=hits[:32],first_self_pairs=bad[:32],Blender=bpy.app.version_string,geometry_modified=False,limitation='BVH epsilon=0 triangle overlap; adjacent/degenerate self intersection and full Boolean volume not certified'))
(root/'metrics/BLENDER_GEOMETRY_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(out,flush=True)
