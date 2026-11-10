"""Read-only cross-HERO diagnostic after all predictions frozen. Never an optimizer input."""
from common import *
ROOT=R

def main():
 assert(ROOT/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json').exists();plan=load(ROOT/'config/VIEW_PLAN.json');rows=[];scale=.5
 for group in ['G06','G05','G01','G03']:
  rr=[r for r in plan if r['group']==group and r['role']=='FIT'];obs={r['view_id']:dict(np.load(ROOT/'hero_fit'/r['view_id']/'OBS_TRUSTED.npz'))for r in rr};parents={r['view_id']:{x['sha256']for x in load(ROOT/'hero_fit'/r['view_id']/'SOURCE.json')['parent_RGB']}|{r['RGB_SHA256']}for r in rr};rv=np.load(ROOT/'inputs'/group/'RING.npz');ring=scene(rv['V'],rv['F'])
  for r in rr:
   sid=r['view_id'];a=obs[sid];X=a['X']
   for t in rr:
    tid=t['view_id']
    if sid==tid:continue
    b=obs[tid];T=b['T'];P=(X-T[:3,3])@T[:3,:3];uv=P@b['K'].T;uv=uv[:,:2]/uv[:,2:];pix=np.floor(uv+.5).astype(int);h,w=map(int,b['native_shape']);inside=(P[:,2]>0)&(pix[:,0]>=0)&(pix[:,0]<w)&(pix[:,1]>=0)&(pix[:,1]<h);grid=np.full((h,w),np.nan);grid[b['uv'][:,1],b['uv'][:,0]]=b['z'];depth=np.full(len(X),np.nan);depth[inside]=grid[pix[inside,1],pix[inside,0]];valid=inside&np.isfinite(depth);ix=np.flatnonzero(valid);known=np.zeros(len(X),bool);behindCAD=np.zeros(len(X),bool)
    if len(ix):
     ray=np.c_[uv[ix],np.ones(len(ix))]@np.linalg.inv(b['K']).T;rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32)
     import open3d as o3d
     cad=ring.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();behindCAD[ix]=P[ix,2]>=cad-.05;known[ix]=~behindCAD[ix]
    dz=P[:,2]-depth;shared=len(parents[sid]&parents[tid])/max(1,len(parents[sid]|parents[tid]));rows.append(dict(group=group,source=sid,target=tid,source_trusted_N=len(X),target_trusted_projection_N=int(valid.sum()),Ring_behind_N=int(behindCAD.sum()),known_unoccluded_N=int(known.sum()),support_proxy_N=int((known&(abs(dz)<=scale)).sum()),front_disagreement_proxy_N=int((known&(dz < -scale)).sum()),behind_observed_surface_N=int((known&(dz>scale)).sum()),unknown_N=int((~known&~behindCAD).sum()),signed_axial_difference_mm=stats(dz[known]),shared_upstream_RGB_Jaccard=shared,diagnostic_tolerance_mm=scale,physical_error_truth=False,used_for_loss_weights_selection=False))
 save('evaluation/metrics/SOURCE_CONFLICT_DIAGNOSTIC.json',rows);table('evaluation/metrics/SOURCE_CONFLICT_DIAGNOSTIC.csv',rows)
if __name__=='__main__':
 main()
 from missing018 import main as missing_main
 missing_main()
