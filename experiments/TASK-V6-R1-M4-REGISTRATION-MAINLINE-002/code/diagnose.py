"""Development regression only: FIT influence, no held selection per group."""
from context import *
from solver2 import solve_methods
from metrics2 import bidirectional
from ring_first_3d.sim.geometry import transform,pose_error
def main():
 old=prior_run();rows=[];freeze('DIAGNOSE',T/'evidence')
 for g in CFG['regression_groups']:
  p=old/g;lm=np.load(p/'LANDMARKS.npz');ix=np.flatnonzero(lm['fit']);A,B=lm['xyz'][ix,0],lm['xyz'][ix,1];ring=read(p/'RING_PRIOR.json');base=solve_methods(A,B,ring,methods=['M4'])['M4'];original=read(p/'PREDICTIONS.json')['M4'];assert np.max(abs(np.array(base['T'])-original['T']))<1e-12
  residual=np.linalg.norm(transform(B,np.array(base['T']))-A,axis=1);k=max(1,int(np.ceil(.05*len(A))));remove=np.argsort(residual)[-k:];keep=np.ones(len(A),bool);keep[remove]=False
  test=solve_methods(A[keep],B[keep],ring,methods=['M4'])['M4'];delta=pose_error(np.array(test['T'])@np.linalg.inv(base['T']))if test['T']is not None else None
  frames=read(p/'FRAMES.json');C=np.load(p/'CAMERAS.npz')['c2w'];tr=dict(np.load(p/'tracks/observations/tracks005.npz'));metrics={}
  for name,r in [('original',base),('trim5_diagnostic',test)]:
   metrics[name]=bidirectional(frames,C,tr,lm['xyz'],np.array(r['T'])if r['T']is not None else None)[0]
  leverage=np.linalg.norm(B-B.mean(0),axis=1);leverage_remove=np.argsort(leverage)[-k:];keep2=np.ones(len(A),bool);keep2[leverage_remove]=False;leverage_fit=solve_methods(A[keep2],B[keep2],ring,methods=['M4'])['M4']
  row=dict(group=g,FIT_tracks=len(A),removed_global_tracks=ix[remove],residual_mm=dict(median=np.median(residual),p95=np.percentile(residual,95),max=residual.max()),trim_delta=delta,leverage_delta=pose_error(np.array(leverage_fit['T'])@np.linalg.inv(base['T']))if leverage_fit['T']is not None else None,old_replay_identical=True,old=base,trim=test,metrics=metrics,held_used_for_fitting=False,normalization='original robust coordinate mean 1/N; trim diagnostic renormalizes to 1/(N-k), independent quadratic Ring unchanged')
  rows.append(row);save(T/'evidence/FIT_DIAGNOSIS.json',rows);print(g,'trim',delta,'held',[[metrics[m][d]['conditional_MAE']for d in ['A_to_B','B_to_A']]for m in metrics],flush=True)
if __name__=='__main__':main()
