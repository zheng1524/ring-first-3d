"""CPU-only actual Adam-step and complete-state audit; do not relabel M0 as M1."""
from common import *
import torch


def main():
    p=TASK/'checkpoints/G01_previous_M0_handoff.pt';state=torch.load(p,map_location='cpu',weights_only=False)
    steps=sorted({int(v['step'])for v in state['optimizer']['state'].values()})
    assert steps==[state['step']]==[11000]
    required=['model','optimizer','scheduler','step','loss_step','torch_rng','cuda_rng','python_rng','numpy_rng','input_freeze']
    assert all(k in state for k in required)and state['loss_step']==state['step']
    rr=rows(PREV/'metrics/single_M0_TRAINING.csv');row=next(r for r in rr if int(r['step'])==state['step'])
    g01_equal=[]
    for cid in ORDERS['G01_004']:
        a=PREV/'frozen_inputs'/(cid+'.npz');b=TASK/'groups/G01_004/frozen_inputs'/(cid+'.npz')
        x=np.load(a);y=np.load(b);assert set(x.files)==set(y.files)
        for k in x.files:assert np.array_equal(x[k],y[k],equal_nan=True),(cid,k)
        g01_equal.append(dict(source=cid,all_array_values_identical=True,prior_sha256=sha(a),new_sha256=sha(b)))
    result=dict(historical_formal_M1_updates=0,M1_resource_25_not_formal=True,
        new_user_approved_baseline=1000,target=10000,prior_M0_not_relabelled_M1=True,
        recoverable_M0_optimizer_step=state['step'],Adam_state_steps=steps,complete_fields=required,
        LR_at_checkpoint=[g['lr']for g in state['optimizer']['param_groups']],scheduler=state['scheduler'],
        wall_seconds_to_preserved_M0_checkpoint=float(row['session_wall_seconds']),gradient_accumulation=False,
        G01_new_M1='fresh same official initialization; no historical formal M1 state exists; prior M0 retained as comparison',
        G01_inputs=g01_equal,checkpoint=asset(p),GT=False)
    (TASK/'provenance/ACTUAL_M1_AND_M0_STATE_AUDIT.json').write_text(json.dumps(clean(result),indent=2)+'\n')
    print('STATE_AUDIT',state['step'],'M0 Adam; historical M1=0; G01 inputs identical')


if __name__=='__main__':main()
