"""Read-only preflight failure isolation. No solver invocation, no accepted pose updates."""
from geometric import *

def foot(q,p,key):
 v=p.views[0];C=canon_np(p.C(tt(q),v).detach().numpy());X=p.X[0][key];o=p.rings[0][key];pr=projection(X.reshape(-1,3),C,np.array(v['K']))[0].reshape(-1,2,2);a,b=pr[:,0],pr[:,1];d=b-a;t=((o-a)*d).sum(1)/np.maximum((d*d).sum(1),1e-15);return np.where(t<=0,0,np.where(t>=1,2,1)),t

def channel_cost(p,q):return {k:float(p.fun(q,k)@p.fun(q,k)/2)for k in ['inner','outer','SIFT','prior','all']}
def newmatch_frozen_visibility(p,q,Xold,sel):
 v=p.views[0];C=canon_np(p.C(tt(q),v).detach().numpy());cad=p.cads[v['ring_path']];p.X=[{k:correspondence(cad.V,sel[0][k],C,np.array(v['K']),p.rings[0][k])if len(p.rings[0][k])else np.empty((0,2,3))for k in ['inner','outer']}];out=channel_cost(p,q);p.X=Xold;return out

def main():
 assert not load(M/'config/JACOBIAN_GATE.json')['pass_required_geometric_J'],'This script diagnoses the frozen failed gate only'
 rows=[];points=[];vv=load(M/'config/VIEWS.json')
 for group in GROUPS:
  v=next(v for v in vv if v['group']==group and v['role']=='FIT');p=Problem([v])
  for point,q in [('zero',np.zeros(6)),('nonzero',np.array([.01,-.007,.005,.003,-.004,.006]))]:
   p.relinearize(q);Xold=p.X;sel=p.selection;J=p.jac(q);r=p.fun(q);base=channel_cost(p,q);foot0={k:foot(q,p,k)for k in ['inner','outer']}
   for h in [.001,.0001,.00001]:
    for j in range(6):
     local=[];nearest=[];actual=[];switch=[];states=[];F=[]
     for sign in [1,-1]:
      u=q+np.eye(6)[j]*h*sign;p.X=Xold;p.selection=sel;F.append(p.fun(u));local.append(channel_cost(p,u));states.append({k:foot(u,p,k)for k in ['inner','outer']});nearest.append(newmatch_frozen_visibility(p,u,Xold,sel));p.relinearize(u);actual.append(channel_cost(p,u));change={}
      for k in ['inner','outer']:
       a=set(map(tuple,sel[0][k]));b=set(map(tuple,p.selection[0][k]));change[k]=dict(edges_added=len(b-a),edges_lost=len(a-b),nearest_material_point_changed_N=int(np.any(abs(p.X[0][k]-Xold[0][k])>1e-12,axis=(1,2)).sum()),clamp_branch_changed_N=int((states[-1][k][0]!=foot0[k][0]).sum()))
      switch.append(change);p.X=Xold;p.selection=sel
     fd=(F[0]-F[1])/(2*h);ab=np.linalg.norm(J[:,j]-fd);rel=float(ab/max(np.linalg.norm(J[:,j]),np.linalg.norm(fd),1e-12));delta={k:dict(local_fixed_edge_FD=(local[0][k]-local[1][k])/(2*h),nearest_reassociate_same_visible_edges_FD=(nearest[0][k]-nearest[1][k])/(2*h),full_visible_edges_recomputed_FD=(actual[0][k]-actual[1][k])/(2*h))for k in base}
     rows.append(dict(group=group,view=v['id'],point=point,h=h,axis=j,AD_objective=float(r@J[:,j]),fixed_local_residual_J_relative=rel,objective_FD=delta,plus=switch[0],minus=switch[1],no_optimizer_invoked=True))
     if h==.0001:
      for k in ['inner','outer']:
       bad=(states[0][k][0]!=foot0[k][0])|(states[1][k][0]!=foot0[k][0]);
       for n in np.flatnonzero(bad):points.append(dict(group=group,view=v['id'],point=point,axis=j,key=k,observation_index=int(n),uv=p.rings[0][k][n],CAD_segment_XYZ_mm=Xold[0][k][n],t_zero=float(foot0[k][1][n]),t_plus=float(states[0][k][1][n]),t_minus=float(states[1][k][1][n]),reason='nearest foot clamp active branch crossed; local vector residual piecewise differentiable'))
  print('FAILURE_ISOLATED',group,flush=True)
 save('metrics/FAILURE_BRANCH_ISOLATION.json',rows);table('metrics/FAILURE_BRANCH_ISOLATION.csv',rows);save('metrics/CLAMP_TRANSITION_NATIVE_OBSERVATIONS.json',points);table('metrics/CLAMP_TRANSITION_NATIVE_OBSERVATIONS.csv',points);save('provenance/FAILED_GATE_AND_DIAGNOSIS_FROZEN.json',dict(epoch=time.time(),files=[asset(M/'config/JACOBIAN_GATE.json'),asset(M/'metrics/JACOBIAN_VALIDATION.json'),asset(Path(__file__)),asset(M/'code/geometric.py')],formal_solver_calls=0,stage_B='NOT_RUN_STAGE_A_GATE'));print('DIAGNOSIS_FROZEN',len(rows),len(points),flush=True)
if __name__=='__main__':main()
