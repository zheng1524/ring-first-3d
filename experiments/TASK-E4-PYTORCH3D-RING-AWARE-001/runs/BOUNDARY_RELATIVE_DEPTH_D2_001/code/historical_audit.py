from common import *
from evaluate import *
assert load(R/'assets_index/PREDICTIONS_FROZEN.json')['all_expected_finals']
g=np.load(OLD/'audit_only/NATIVE_CAD_GT.npz');grt=scene(g['V'],g['F']);gps=area_samples(g['V'],g['F']);rows=[]
for arm in['P0','B','C','D']:
 p=R.parent/'PROGRESSIVE_HERO_001/inputs/virtual/INITIAL.npz'if arm=='P0'else R.parent/'PROGRESSIVE_HERO_001/local_results/virtual'/arm/'FINAL.npz';a=np.load(p);ps=area_samples(a['V'],a['F']);err=np.r_[distance(scene(a['V'],a['F']),gps),distance(grt,ps)];rows.append(dict(historical_arm=arm,source=asset(p),maximum_height_from_GT_base_mm=float(a['V'][:,2].max()-g['V'][:,2].min()),minimum_z_mm=float(a['V'][:,2].min()),GT_height_mm=float(np.ptp(g['V'][:,2])),Chamfer_mm=stats(err),not_same_condition_ablation=True,not_used_as_current_B_E_control=True))
save('metrics/HISTORICAL_C_D_ONLY.json',dict(rows=rows,interpretation='prior GLOBAL6+local differs from this LOCAL-only D2; visually higher bulge is not evidence of better full 3D geometry',no_selection=True))
