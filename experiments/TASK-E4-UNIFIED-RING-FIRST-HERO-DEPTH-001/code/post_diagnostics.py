"""Frozen-state diagnostics; never update parameters or consult GT to select."""
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.paths import activate
from ring_first_3d.mainline.native.io import save_json,sha256
activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
from ring_first_3d.contour_guided.correspondence import target_boundary
from body_hooks import historical_depth,mesh
T=p.TASK;O=T/'runs/RF_ONLY_V1'

def main():
    assert p.read(O/'PREDICTIONS_FROZEN_BEFORE_GT.json')['all_training_complete'];bounds=[];gradients=[]
    for folder in O.glob('G*/004/evaluation/projections/*'):
        group=folder.parents[3].name;arm=folder.name
        for file in folder.glob('*.npz'):
            if file.stem.endswith('_BOUNDARY_DISTRIBUTION'):continue
            a=dict(np.load(file));known=~a['unknown'];P,_,_=target_boundary(np.where(a['predicted'],1,0),100000);Q,_,_=target_boundary(np.where(a['target'],1,0),100000);P=P[known[P[:,1].astype(int),P[:,0].astype(int)]];Q=Q[known[Q[:,1].astype(int),Q[:,0].astype(int)]]
            dp=cKDTree(Q).query(P)[0] if len(P) and len(Q) else np.array([360.]);dq=cKDTree(P).query(Q)[0] if len(P) and len(Q) else np.array([360.]);d=np.r_[dp,dq]
            out=file.with_name(file.stem+'_BOUNDARY_DISTRIBUTION.npz');np.savez_compressed(out,pred_to_target_px=dp,target_to_pred_px=dq,pred_boundary_uv=P,target_boundary_uv=Q)
            bounds.append(dict(group=group,video='004',arm=arm,id=file.stem,Boundary_MAE_px=float(d.mean()),Boundary_median_px=float(np.median(d)),Boundary_p95_px=float(np.percentile(d,95)),Boundary_max_px=float(d.max()),pred_boundary_N=len(P),target_boundary_N=len(Q),evidence=str(out)))
    selected=p.read(T/'audit/SELECTED_VIEWS.json')
    for c in p.cases():
        group=c['case'];b=O/group/'004/body'
        if not (b/'B2/TASK_PREDICTION_FROZEN.json').exists():continue
        fit=[v for v in selected if v['meta']['case']==group and v['meta']['video']=='004' and v['meta']['role']=='FIT'];norm=p.read(c['static']['NORMALIZATION.json']['path']);chart=p.read(c['static']['CHART.json']['path']);initial=dict(np.load(c['initial']['path']));case=SimpleNamespace(name=group+'_004',V=initial['V'],center=np.array(norm['center']),scale=norm['scale_mm'],fit=[v['meta']['id'] for v in fit],views={v['meta']['id']:dict(meta=v['meta']) for v in fit});d=historical_depth(case,chart,b/'DEPTH_INPUT',O/group/'004/evaluation/depth_gradient')
        for stage in ['INITIAL','FINAL']:
            source=b/'B2'/(stage+'.npz');body=dict(np.load(source));V=torch.tensor(body['V'],dtype=torch.float64,device='cuda',requires_grad=True)
            for cid in case.fit:
                V.grad=None;loss,info,_=d.term(mesh(V,body['F'],case),cid);weighted=.01*d.w[cid]*loss;weighted.backward();g=V.grad.detach().cpu().numpy()
                assert np.isfinite(g).all()
                gradients.append(dict(group=group,video='004',arm='B2',stage=stage,id=cid,source_mesh_sha256=sha256(source),fixed_N=info['fixed_N'],active_N=info['active_N'],nonzero_residual_N=info['robust_nonzero_derivative_N'],weighted_depth_loss=float(weighted.detach()),vertex_gradient_norm=float(np.linalg.norm(g)),nonzero_vertex_gradient_N=int((np.linalg.norm(g,axis=1)>1e-12).sum()),parameters_updated=False))
    p.table(T/'metrics/BOUNDARY_DISTRIBUTIONS.csv',bounds);p.table(T/'metrics/DEPTH_GRADIENT_EVIDENCE.csv',gradients)
    save_json(T/'metrics/DIAGNOSTIC_SCOPE.json',dict(boundary_distribution_fixed_model=True,depth_gradient_endpoint_states_only=True,does_not_certify_every_intermediate_iteration=True,no_GT_tuning=True,no_prediction_mutation=True))
    print('POST_DIAGNOSTICS',len(bounds),'boundary distributions;',len(gradients),'gradient records',flush=True)

if __name__=='__main__':main()
