import os
os.environ['E4_OPTIMIZER_ONLY']='1'
from common import *
blocked=[]
old=REPO/'experiments/E4-SDF-LOCALIZATION-BLENDER-001'
for path in [R/'audit_only/NATIVE_CAD_GT.npz',old/'inputs/BASE_FIELD.npz',old/'audit_only/TARGET_GT.npz',Path('/home/liu/polyp_research/experiments/geometric_validation_v1/assets/IIa6.5.blend')]:
    try:
        with open(path,'rb'):pass
        raise AssertionError('GT_LEAK:'+str(path))
    except PermissionError:blocked.append(str(path))
for name in ['BASE_FIELD.npz','BASE_SOURCE_MESH.npz','RING_CAD.npz','CAMERAS.json']:
    with open(R/'inputs'/name,'rb')as f:f.read(1)
save('metrics/FIREWALL.json',dict(passed=True,blocked=blocked,allowed_initial_only='new independent ellipsoid field; frozen Ring/cameras/target 2D labels',old_native_SDF_blocked=True))
print('FIREWALL_PASS',flush=True)
