from common import *
assert load(R/'assets_index/PREDICTIONS_FROZEN.json')['all_expected_finals'];checks=load(R/'metrics/BLENDER_CHECKS.json');rows=[]
for name in['virtual_Ip','virtual_Is','virtual_IIa']:
 p=OLD/'audit_only/NATIVE_CAD_GT.npz'if name=='virtual_IIa'else R/'audit_only'/name/'GT.npz';a=np.load(p);V,F=a['V'],a['F'];m=trimesh.Trimesh(V,F,process=False);r=next(x for x in checks if x['case']==name and x['arm']=='GT');confirmed=[]
 for i,j in r['self_pairs']:
  cm=trimesh.collision.CollisionManager();cm.add_object('one',trimesh.Trimesh(V[F[i]],[[0,1,2]],process=False));yes=cm.in_collision_single(trimesh.Trimesh(V[F[j]],[[0,1,2]],process=False))
  if yes:confirmed.append([i,j])
 rows.append(dict(case=name,source=asset(p),watertight=bool(m.is_watertight),winding=bool(m.is_winding_consistent),components=len(m.split(only_watertight=False)),BVH_nonadjacent_pairs=r['self_pair_N'],FCL_confirmed_pairs=confirmed,FCL_confirmed_N=len(confirmed),not_repaired=True,solid_GT_certified=bool(m.is_watertight and m.is_winding_consistent and r['self_pair_N']==0)))
save('metrics/NATIVE_GT_SOLID_AUDIT.json',rows);print(rows)
