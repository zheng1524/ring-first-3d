"""Preserve and quantify historical finite-precision rotation failure; no pose repair."""
from common import *
def main():
 rows=[]
 for p in sorted((R/'results').glob('*.json')):
  a=load(p);H=np.array(a['T']);e=float(abs(H[:3,:3].T@H[:3,:3]-np.eye(3)).max());det=float(np.linalg.det(H[:3,:3]));x=dict(method=p.stem,rotation_orthogonality_max_abs=e,determinant=det,strict_1e_9_orthogonality_pass=e<1e-9,strict_1e_9_determinant_pass=abs(det-1)<1e-9,no_scale_variable=True,frozen_pose_unchanged=True)
  if 'seed_T'in a:
   S=np.array(a['seed_T']);D=H@np.linalg.inv(S);x.update(seed_orthogonality_max_abs=float(abs(S[:3,:3].T@S[:3,:3]-np.eye(3)).max()),seed_determinant=float(np.linalg.det(S[:3,:3])),increment_rotation_orthogonality_max_abs=float(abs(D[:3,:3].T@D[:3,:3]-np.eye(3)).max()),increment_determinant=float(np.linalg.det(D[:3,:3])))
  rows.append(x)
 save('metrics/FROZEN_ROTATION_NUMERICAL_AUDIT.json',rows);table('metrics/FROZEN_ROTATION_NUMERICAL_AUDIT.csv',rows);print('FROZEN_ROTATION_AUDIT_COMPLETE; strict failures retained, matrices unchanged',flush=True)
if __name__=='__main__':main()
