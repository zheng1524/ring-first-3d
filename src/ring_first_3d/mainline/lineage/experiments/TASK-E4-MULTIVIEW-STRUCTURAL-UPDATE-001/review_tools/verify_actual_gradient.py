"""Read-only verification of saved real metric optimization state, never reads GT."""
from pathlib import Path
import sys,json
import numpy as np
import torch,yaml
ROOT=Path(__file__).resolve().parents[3];TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from body_update import objective,balanced_weights
from data_adapter import simulation_data
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.synthetic.io import save_json
p=sys.argv[1];folder=Path(p);step=folder/'STEP_000';task=yaml.safe_load((TD/'TASK.yaml').read_text());initial,views,ring,base,chart=simulation_data(task,'FIT')
body=dict(np.load(step/'BODY_BEFORE.npz'));record=np.load(step/'BODY_AFTER.npz');V=torch.tensor(body['V'],dtype=torch.float64,device='cuda:0',requires_grad=True);rest=torch.tensor(initial['V'],dtype=V.dtype,device=V.device);pairs={v['id']:dict(np.load(step/(v['id']+'.npz'))) for v in views};weights=balanced_weights(views)
loss,per,parts=objective(V,body,rest,views,pairs,weights,task['structural']['update'],True);g=torch.autograd.grad(loss,V)[0].detach().cpu().numpy();saved=record['full_gradient'];assert np.allclose(g,saved,atol=1e-12,rtol=1e-9)
rng=np.random.default_rng(20261117);ids=np.unique(np.r_[np.argsort(abs(g).ravel())[-24:],rng.choice(g.size,24,replace=False)]);h=1e-5;rows=[]
for index in ids:
 i,j=np.unravel_index(index,g.shape);A=V.detach().clone();B=V.detach().clone();A[i,j]+=h;B[i,j]-=h
 with torch.no_grad():a=float(objective(A,body,rest,views,pairs,weights,task['structural']['update'])[0]);b=float(objective(B,body,rest,views,pairs,weights,task['structural']['update'])[0])
 fd=(a-b)/(2*h);rows.append(dict(vertex=int(i),coordinate=int(j),saved_analytic=float(g[i,j]),central_difference=fd,absolute_error=abs(fd-g[i,j])))
result=dict(verification='Saved exact STEP000 complete FIT objective, real Face/bary, fixed assignment',source_body_sha256=sha256(step/'BODY_BEFORE.npz'),full_gradient_saved_max_error=float(abs(g-saved).max()),epsilon_mm=h,coordinates=len(rows),max_absolute_error=max(r['absolute_error'] for r in rows),GT_read=False,parameters_changed=False,rows=rows)
assert result['max_absolute_error']<1e-6
save_json(TD/'evidence/ACTUAL_GRADIENT_FINITE_DIFFERENCE.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
