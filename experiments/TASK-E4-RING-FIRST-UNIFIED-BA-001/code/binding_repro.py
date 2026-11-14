"""Exact first-call Ceres/Python Jacobian initialization crash reproducer; no predictions."""
from joint_ba import *
o=Joint('G05','B1',one='G05_v004_raw00117');o.actual();p=o.build()
if '--warm' in sys.argv:
 j=p.evaluate_jacobian();print('PREWARM',j.num_rows,j.num_cols,flush=True)
solver(p,'BINDING_REPRO_'+str('--warm'in sys.argv),2,False)
