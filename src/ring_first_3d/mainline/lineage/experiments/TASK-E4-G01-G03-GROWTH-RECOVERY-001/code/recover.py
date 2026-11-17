"""Invert saved spline samples, and reconstruct the actual rejected topology."""
import numpy as np
import torch
from io_utils import source_folder,read,body,sha
from bspline_sweep import BSplineSweep,basis

def restore(case):
    folder=source_folder(case);current=body(folder/'STEP_024/BODY.npz')
    saved=body(folder/'GROWTH_PROPOSAL_024/BODY.npz')
    info=body(folder/'GROWTH_PROPOSAL_024/SWEEP.npz')
    record=next(r for r in read(folder/'UPDATES.json')['growth']if r['iteration']==24)
    chosen=record['candidates'][0]
    assert np.array_equal(np.sort(chosen['patch']),np.sort(info['removed_faces'])), 'SAVED_SEED_PATCH_MISMATCH'
    sweep=BSplineSweep(current,chosen['patch'],chosen['delta'],min(6.,np.linalg.norm(chosen['delta'])),device='cpu')
    B,_=basis();C=np.linalg.lstsq(B,info['centerline'],rcond=None)[0]
    A=np.linalg.lstsq(B,np.log(np.expm1(info['axes'])),rcond=None)[0]
    with torch.no_grad():
        sweep.control.copy_(torch.tensor(C));sweep.radii.copy_(torch.tensor(A))
        # First saved RMF normal is the projected original axis; equivalent for transport.
        sweep.initial_axis.copy_(torch.tensor(info['frame_r'][0]))
    # Saved proposal includes a rejected Graph update; faithfully reproduce it first.
    n=len(current['V']);V=torch.tensor(saved['V'][:n],dtype=torch.float64)
    regenerated,details=sweep.generate(V)
    restored=sweep.body(regenerated.detach().numpy(),current)
    errors={k:float(np.max(np.abs(details[k].detach().numpy()-info[k])))for k in ['centerline','axes','frame_r','frame_s','frame_t']}
    errors['BODY_vertex_max_mm']=float(np.linalg.norm(restored['V']-saved['V'],axis=1).max())
    topology=all(np.array_equal(restored[k],saved[k])for k in ['F','F_solid','boundary_vertex','inferred_base_faces'])
    assert max(errors.values())<=1e-5 and topology, ('UNRECOVERABLE_HISTORY',errors,topology)
    report=dict(case=case,iteration=24,seed=chosen['seed'],errors=errors,topology_identical=topology,
        historical_rejected_graph_vs_STEP024_max_mm=float(np.linalg.norm(saved['V'][:n]-current['V'],axis=1).max()),
        original_body='STEP_024/BODY.npz',warm_start='REJECTED_CANDIDATE_WARM_START',Adam_state_restored=False,
        evidence={name:dict(path=str(folder/name),sha256=sha(folder/name))for name in ['STEP_024/BODY.npz','STEP_024/GRAPH.npz','UPDATES.json','GROWTH_PROPOSAL_024/BODY.npz','GROWTH_PROPOSAL_024/SWEEP.npz']})
    return current,saved,info,C,A,chosen,report

if __name__=='__main__':
    from ring_first_3d.multisurface.geometry import scene
    from ring_collision_gate import signed
    for case in ['G01','G03']:
        current,saved,info,C,A,chosen,report=restore(case)
        report['historical_centerline_signed_distance_mm']=signed(scene(current['V'],current['F_solid']),info['centerline']).tolist()
        print(report,flush=True)
