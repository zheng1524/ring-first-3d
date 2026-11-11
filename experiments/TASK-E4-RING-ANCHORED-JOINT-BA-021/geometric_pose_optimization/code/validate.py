"""Six-DoF geometric Jacobians: fixed local visibility/correspondence vs central FD."""
from geometric import *

def main():
 if not(M/'provenance/INPUTS_FROZEN.json').exists():raise RuntimeError('prepare inputs first')
 guard_fit();vv=load(M/'config/VIEWS.json');rows=[];infos=[]
 for group in GROUPS:
  v=next(v for v in vv if v['group']==group and v['role']=='FIT');p=Problem([v]);q=np.zeros(6)
  for point,q in [('zero',np.zeros(6)),('nonzero',np.array([.01,-.007,.005,.003,-.004,.006]))]:
   p.relinearize(q)
   for part in ['inner','outer','SIFT','prior','all']:
    J=p.jac(q,part);r=p.fun(q,part)
    for h in p.protocol['jacobian_steps']:
     F=np.stack([(p.fun(q+np.eye(6)[j]*h,part)-p.fun(q-np.eye(6)[j]*h,part))/(2*h)for j in range(6)],1)if len(r)else np.zeros((0,6));cols=[]
     for j in range(6):
      ab=float(np.linalg.norm(J[:,j]-F[:,j]));rel=ab/max(np.linalg.norm(J[:,j]),np.linalg.norm(F[:,j]),1e-12);cols.append(dict(axis=j,relative=float(rel),absolute=ab,pass_local=bool(rel<=.001 or ab<=1e-5)))
     rows.append(dict(group=group,view=v['id'],point=point,part=part,h=h,N=len(r),columns=cols,relative_Frobenius=float(np.linalg.norm(J-F)/max(np.linalg.norm(J),np.linalg.norm(F),1e-12)),pass_all6=all(a['pass_local']for a in cols),unobserved=len(r)==0))
  p.relinearize(np.zeros(6));C=np.array(v['T']);G=np.eye(4);G[:3,:3]=Rotation.from_euler('z',37,degrees=True).as_matrix();gauge=float(np.max(abs(canon_np(C)-canon_np(G@C))));dynamic=[];J=p.jac(np.zeros(6));r=p.fun(np.zeros(6))
  for j in range(6):
   d=np.eye(6)[j]*1e-4;fp=p.true_cost(d);fm=p.true_cost(-d);dynamic.append(dict(axis=j,AD_local=float(r@J[:,j]),FD_relinearized=(fp-fm)/2e-4,finite=bool(np.isfinite([fp,fm]).all())))
  infos.append(dict(group=group,view=v['id'],data_information=p.information(np.zeros(6)),yaw_canonical_invariance_max_abs=gauge,actual_relinearized_objective_directions=dynamic));print('JACOBIAN_DONE',group,flush=True)
 gate=all(a['pass_all6']for a in rows if a['h']<=.0001)and all(a['yaw_canonical_invariance_max_abs']<1e-10 for a in infos)
 save('metrics/JACOBIAN_VALIDATION.json',rows);table('metrics/JACOBIAN_VALIDATION.csv',rows);save('metrics/OBSERVABILITY_GATE_SAMPLES.json',infos);save('config/JACOBIAN_GATE.json',dict(pass_required_geometric_J=gate,all6_dofs=True,groups=GROUPS,multistep=[.001,.0001,.00001],fixed_correspondence_relinearization_explicit=True,severe_error=not gate))
 print('GEOMETRIC_JACOBIAN_GATE',gate,flush=True)
 if not gate:save('STAGE_GATE_DECISION.json',dict(status='PAUSED_FOR_HUMAN_DIAGNOSIS',stage='GEOMETRIC_JACOBIAN',stage_B='NOT_RUN_STAGE_A_GATE',reason='geometric Jacobian failed frozen numerical standard'))
if __name__=='__main__':main()
