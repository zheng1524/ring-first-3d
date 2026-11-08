"""Independent dense barycentric material test; never changes frozen predictions."""
from common import *
import open3d as o3d

def main():
 rows=[];weights=[]
 for i in range(33):
  for j in range(33-i):weights.append([i/32,j/32,1-(i+j)/32])
 W=np.array(weights)
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];r=np.load(R/'inputs'/n/'RING.npz');rt=scene(r['V'],r['F']);lo=r['V'].min(0);hi=r['V'].max(0)
  for tag in ['FINAL011','FINAL012','FINAL013']:
   z=np.load(R/'local_results/metric'/n/(tag+'.npz'));tri=z['V'][z['F_solid']];ids=np.flatnonzero((tri.min(1)<=hi).all(1)&(tri.max(1)>=lo).all(1));mins=[];inside=0;N=0;worst=None
   for batch in np.array_split(ids,max(1,int(np.ceil(len(ids)/24)))):
    if not len(batch):continue
    P=np.einsum('wc,fcd->fwd',W,tri[batch]).reshape(-1,3);sd=rt.compute_signed_distance(o3d.core.Tensor(P.astype(np.float32)),nsamples=3).numpy();k=int(np.argmin(sd));mins.append(float(sd[k]));inside+=int((sd<-1e-4).sum());N+=len(sd)
    if worst is None or sd[k]<worst[0]:worst=(float(sd[k]),P[k])
   pen=max(0.,-min(mins))if mins else 0.;row=dict(case=n,label=tag,dense_barycentric_divisions=32,weights_per_face=len(W),candidate_face_N=len(ids),sample_N=N,penetrating_over0p0001mm_N=inside,maximum_sampled_material_penetration_mm=pen,not_continuous_certification=True,world_unit='mm',postfreeze_diagnostic_only=True);rows.append(row);print(n,tag,pen,inside,flush=True)
   if worst is not None:np.savez_compressed(R/'local_results'/('DENSE_RING_'+n+'_'+tag+'.npz'),point=worst[1],depth_mm=pen)
 save('metrics/DENSE_RING_AUDIT.json',rows);table('metrics/DENSE_RING_AUDIT.csv',rows)
if __name__=='__main__':main()
