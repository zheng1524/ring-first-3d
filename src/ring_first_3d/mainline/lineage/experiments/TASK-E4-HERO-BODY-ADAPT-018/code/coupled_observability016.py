"""Coupled contour Jacobian, not just misleading independent 3x3 vertex blocks."""
from common import *
from scipy import sparse,linalg
from prepare016 import weights

def main():
 old=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015';summary=[]
 for n in ['G01','G03']:
  root=R/'arms/DIAGNOSTIC';r=load(root/'metrics'/(n+'_CORRESPONDENCES.json'));z=np.load(root/'metrics'/(n+'_CAUSAL_TAPE.npz'));N=len(z['V']);meta=load(root/'inputs'/n/'CASE.json');fit=[v['id']for v in meta['views']if v['role']=='FIT'];w=weights(meta['views'],fit);counts={i:sum(x['view']==i for x in r)for i in fit};J=np.zeros((len(r),3*N));res=[]
  for i,x in enumerate(r):
   ww=np.sqrt(w[x['view']]/counts[x['view']]);j=np.asarray(x['jacobian_row_pixel_per_mm'])*ww
   for a,b in zip(x['edge_vertex_ids'],x['edge_barycentric']):J[i,3*a:3*a+3]+=b*j
   res.append(x['residual_px']*ww)
  active=np.flatnonzero(np.linalg.norm(J,axis=0)>1e-12);u,s,vt=linalg.svd(J[:,active],full_matrices=False,lapack_driver='gesdd');threshold=max(s[0]*.01,1e-5);rank=int((s>threshold).sum());mech=np.load(old/'arms/Stalk-B/local_results'/n/'MECHANISM_0001.npz');d=mech['actual_vertex_delta'].ravel();coeff=vt@d[active];weak=float(np.linalg.norm(coeff[s<=threshold])/max(1e-30,np.linalg.norm(d[active])));rate=J@d;rr=np.array(res);summary.append(dict(case=n,full_DOF=3*N,active_contour_coordinates=len(active),numerical_effective_rank=rank,relative_singular_cutoff=.01,unconstrained_or_weak_coordinates_lower_bound=3*N-rank,first_actual_B_step_weak_fraction_on_active_coordinates=weak,first_order_improving_residual_fraction=float((rate<0).mean()),first_order_residual_l2_change=float(np.linalg.norm(rr+rate)-np.linalg.norm(rr)),interpretation='Frozen nearest-contour assignments; rank is conditional and local. Other losses and changing visibility not included; not a proof that anatomical stalk is identifiable.'))
  np.savez_compressed(R/'metrics'/(n+'_COUPLED_JACOBIAN.npz'),J=J,active_coordinates=active,singular_values=s,Vt=vt,actual_first_delta=d,residual=rr)
 save('metrics/COUPLED_OBSERVABILITY.json',summary);table('metrics/COUPLED_OBSERVABILITY.csv',summary);print('COUPLED_OBSERVABILITY_COMPLETE',summary,flush=True)
if __name__=='__main__':main()
