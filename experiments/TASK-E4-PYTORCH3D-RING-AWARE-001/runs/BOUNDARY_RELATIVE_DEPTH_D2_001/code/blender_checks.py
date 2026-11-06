import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(sys.argv[sys.argv.index('--')+1]);cfg=json.loads((root/'config/PROTOCOL.json').read_text());out=[]
for name in cfg['cases']:
 r=np.load(root/'inputs'/name/'RING.npz');rt=BVHTree.FromPolygons([Vector(x)for x in r['V']],r['F'].tolist(),all_triangles=True,epsilon=0.)
 states=[('P0',0,root/'inputs'/name/'INITIAL.npz')]+[(a,s,root/'local_results'/name/a/('STEP_%04d.npz'%s))for a in cfg['arms']for s in[50,100,200,300]]
 if name.startswith('virtual'):
  gtpath=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/audit_only/NATIVE_CAD_GT.npz')if name=='virtual_IIa'else root/'audit_only'/name/'GT.npz';states=[('GT',0,gtpath)]+states
 for arm,step,path in states:
  a=np.load(path);V=a['V'];F=a['F'];bt=BVHTree.FromPolygons([Vector(x)for x in V],F.tolist(),all_triangles=True,epsilon=0.);hits=bt.overlap(rt);bad=[[int(i),int(j)]for i,j in bt.overlap(bt)if i<j and not np.intersect1d(F[i],F[j]).size];out.append(dict(case=name,arm=arm,step=step,Ring_pair_N=len(hits),self_pair_N=len(bad),Ring_pairs=hits[:64],self_pairs=bad[:256],self_pairs_truncated=len(bad)>256,Blender=bpy.app.version_string,geometry_modified=False));print(name,arm,step,len(hits),len(bad),flush=True)
(root/'metrics/BLENDER_CHECKS.json').write_text(json.dumps(out,indent=2))
