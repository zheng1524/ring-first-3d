"""Allowlisted objective-only adapter to byte-identical historical train_mesh.main."""
from _bootstrap import ROOT
from pathlib import Path
import os,sys,json
sys.path.insert(0,str(ROOT/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/legacy015'))
from _policy_worker import install_io_guard
from ring_first_3d.policy.contour_contracts import permissions
freeze=json.loads(Path(os.environ['CONTOUR_POLICY_FREEZE']).read_text())['fingerprint']['task']
install_io_guard(Path(os.environ['E4_RUN_DIR']),permissions(freeze,'G1_all_train',Path(os.environ['CONTOUR_POLICY_RUN'])))
import train_mesh
from ring_first_3d.contour_guided import objective
train_mesh.MultiObjective=objective.objective_class(train_mesh)
if __name__=='__main__':
 train_mesh.main()
 import torch,numpy as np
 final=Path(os.environ['E4_RUN_DIR'])/'local_results'/sys.argv[1]/'FINAL.npz';a=np.load(final);q=torch.as_tensor(a['parameters'],dtype=torch.float64,device=train_mesh.device).requires_grad_(True);objective.INSTANCE.finalize(q)
