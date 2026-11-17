"""Independent central finite differences of saved explicit loss, without renderer/GT."""
from pathlib import Path
import json,numpy as np
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state
from ring_first_3d.synthetic.io import fetch
from ring_first_3d.contour_guided.correspondence import project
root=Path.cwd();td=root/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';task=load_task(td/'TASK.yaml');run=td/'runs/CONTOUR_004';assert verify_task(task)['freeze_sha256']==read_state(run)['freeze_sha256'];src=json.loads(Path(task['inita']['assets']['sources']['path']).read_text());rows={r['case']:r for r in src['cases']};checks=[]
for g in ['G01','G05','G11']:
 first=fetch(run,'G1_smoke_train',g+'/A3/contour_evidence/0001/BODY.npz').parent;body=dict(np.load(first/'BODY.npz'));summary=json.loads((first/'SUMMARY.json').read_text());row=rows[g];initial=np.load(row['resolved013_initial']['path']);V0=initial['V'];plane=np.asarray(json.loads(Path(row['static']['BASE_SELECTION.json']['path']).read_text())['selected_plane']);normal=plane[:3];rim=initial['boundary_vertex'];unused=np.setdiff1d(np.arange(len(V0)),np.unique(initial['F']));cap=initial['inferred_base_faces'].any()
 def vertices(q):
  delta=q.copy()
  if cap:
   delta[rim]-=(delta[rim]@normal)[:,None]*normal;V=V0+delta;V[unused]=V0[unused]+delta[rim].mean(0);return V
  return V0+delta
 for video in ['004','005']:
  v=next(v for v in row['FIT']if v['meta']['video']==video);cid=v['meta']['id'];pair=dict(np.load(first/(cid+'.npz')));cfg=np.load(v['cache']['path']);ok=pair['accepted'];edge=pair['edge'][ok];t=pair['edge_t'][ok];target=pair['target_uv'][ok];n=pair['target_normal'][ok];direction=pair['direction'][ok];weight=next(x['weight']for x in summary['views']if x['id']==cid);ramp=.25+.75*min(1.,summary['attempt']/40.)
  def loss(q):
   V=vertices(q);P=V[edge[:,0]]*(1-t[:,None])+V[edge[:,1]]*t[:,None];uv,_=project(P,cfg['K'],cfg['T']);r=np.einsum('ij,ij->i',uv-target,n)/20.;h=np.where(abs(r)<1,.5*r*r,abs(r)-.5);parts=[h[direction==z].mean()for z in [0,1]if(direction==z).any()];return weight*ramp*.01*sum(parts)/len(parts)
  grad=pair['contour_gradient'];coords=np.argsort(abs(grad).ravel())[-6:];q=body['parameters'];eps=1e-5
  for k in coords:
   p=q.copy();m=q.copy();p.flat[k]+=eps;m.flat[k]-=eps;fd=(loss(p)-loss(m))/(2*eps);ad=float(grad.flat[k]);error=abs(ad-fd);relative=error/max(1e-10,abs(fd));assert error<1e-8 and relative<1e-3,(g,cid,k,ad,fd,relative);checks.append(dict(case=g,view=cid,vertex=int(k//3),axis=int(k%3),autodiff_objective_per_mm=ad,finite_difference_objective_per_mm=fd,absolute_error=error,relative_error=relative))
receipt=dict(status='PASS',actual_frozen_E_step=True,checked_coordinates=len(checks),epsilon_mm=1e-5,GT_read=False,max_absolute_error=max(r['absolute_error']for r in checks),max_relative_error=max(r['relative_error']for r in checks),checks=checks);out=td/'evidence';out.mkdir(exist_ok=True);(out/'ACTUAL_CONTOUR_GRADIENT_FINITE_DIFFERENCE.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='checks'},indent=2))
