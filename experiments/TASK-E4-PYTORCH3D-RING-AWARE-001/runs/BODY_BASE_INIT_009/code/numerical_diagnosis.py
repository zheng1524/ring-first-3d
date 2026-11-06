"""Read-only after freeze: diagnose finite-difference/soft-contact failures, no optimizer calls."""
from fit_body import *
def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN.json').exists();rows=[]
 for c in['G03','G05','G06','G07']:
  for arm in['B','C']:
   m=load(R/'local_results'/c/(arm+'_SELECTED.json'));p=np.array(m['p']);prob=Problem(c,m['meta'],p,'DEPTH',weak=m.get('selection_status')=='WEAK_BASE_UNTRUNCATED');J=prob.jac(p);small=[]
   h=np.r_[np.full(3,.02),np.full(3,.002),np.full(3,.002),np.full(len(p)-9,.005)]if m['meta']['family']in['ellipsoid','star']else np.r_[np.full(2,.02),np.full(3,.002),.002,np.full(len(p)-6,.005)]
   for k,s in enumerate(h/2):
    a=p.copy();b=p.copy();a[k]+=s;b[k]-=s;small.append((prob.residual(a,False)-prob.residual(b,False))/(2*s))
   K=np.stack(small,axis=1);V,F,full,flag=body(p,m['meta']);t=V[full];P=np.r_[V,t.mean(1),(t[:,0]+t[:,1])/2,(t[:,1]+t[:,2])/2,(t[:,2]+t[:,0])/2];sd=torus_sdf(P,prob.c.meta['R_mid_mm'],prob.c.meta['wire_mm']);sdfactual=scene(prob.c.ringV,prob.c.ringF).compute_signed_distance(o3d.core.Tensor(P.astype(np.float32)),nsamples=3).numpy()
   rows.append(dict(case=c,arm=arm,finite_J=bool(np.isfinite(J).all()and np.isfinite(K).all()),full_J_norm=float(np.linalg.norm(J)),half_step_relative_J_change=float(np.linalg.norm(J-K)/max(1e-12,np.linalg.norm(K))),per_parameter_relative_J_change=np.linalg.norm(J-K,axis=0)/np.maximum(1e-12,np.linalg.norm(K,axis=0)),proxy_penetrating_samples_N=int((sd<0).sum()),proxy_min_distance_mm=float(sd.min()),actual_CAD_min_sample_distance_mm=float(sdfactual.min()),torus_proxy_CAD_disagreement_max_mm=float(abs(sd-sdfactual).max()),optimizer_rerun=False,diagnostic_only=True))
   print('NUMERICAL_DIAG',c,arm,rows[-1]['half_step_relative_J_change'],flush=True)
 save('metrics/POSTERIOR_NUMERICAL_DIAGNOSIS.json',rows);table('metrics/POSTERIOR_NUMERICAL_DIAGNOSIS.csv',rows)
if __name__=='__main__':main()
