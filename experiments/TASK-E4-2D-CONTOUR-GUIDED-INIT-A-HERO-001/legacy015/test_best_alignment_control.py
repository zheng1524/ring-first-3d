"""End-to-end original rigid search on a known transformed copy of an OWN mesh.
No project Blender GT; this is a numerical pipeline control, not a new case.
"""
from best_rigid015 import *
import time
p=R/'arms/NUMERIC_CONTROL/inputs/G03/INITIAL.npz';z=np.load(p);V,F=z['V'],z['F'];rot=Rotation.from_rotvec([.27,-.19,.38]).as_matrix();shift=np.array([1.3,-.8,.7]);GV=V@rot.T+shift;t=time.time();T,diagnostic=align(V,F,GV,F,10.);res=float(abs(apply(V,T)-GV).max());ok=res<1e-3 and np.linalg.det(T[:3,:3])>.999999;save('metrics/BEST_RIGID_END_TO_END_CONTROL.json',dict(pass_test=ok,source=asset(p),copy_transformed_by_known_R=rot,copy_t_mm=shift,recovered_T=T,maximum_material_correspondence_error_mm=res,seconds=time.time()-t,all96starts=True,scale_fixed=1.,Blender_read=False,note='Own frozen prediction transformed for numerical control only; not a scientific reconstruction comparison'));assert ok;print('BEST_RIGID_END_TO_END_PASS',res,time.time()-t,flush=True)
