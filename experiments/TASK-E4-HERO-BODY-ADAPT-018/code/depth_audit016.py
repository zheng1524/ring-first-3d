"""Native fixed IDs, missing-ray zero-gradient mechanism; no observation filtering."""
from common import *
import open3d as o3d
def main():
 counts=[];rows=[]
 for p in(R/'depth_observations').glob('*.npz'):
  a=np.load(p);counts.append(dict(source=p.stem,N=len(a['z']),fixed_pair_N=len(a['pairs']),native_shape=a['native_shape'],asset=asset(p)))
 save('metrics/ACTUAL_HERO_CACHE_DENOMINATORS.json',counts);table('metrics/ACTUAL_HERO_CACHE_DENOMINATORS.csv',counts)
 old=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015';sel=load(R/'config/VIEW_SELECTION_016.json')
 for n in ['G03','G01']:
  rg=np.load(R/'inputs'/n/'RING.npz');rs=scene(rg['V'],rg['F']);paths=[('SHARED_START',old/'arms/Init-A/local_results'/n/'FINAL.npz'),('OLD_B',old/'arms/Stalk-B/local_results'/n/'FINAL.npz'),('COHERENT',R/'arms/MECH_COHERENT/local_results'/n/'FINAL.npz')]
  for tag,p in paths:
   z=np.load(p);s=scene(z['V'],z['F'])
   for cid in sel[n]['OLD']:
    dp=R/'depth_observations'/(cid+'.npz')
    if not dp.exists():continue
    a=np.load(dp);ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(a['K']).T;T=a['T'];rw=ray@T[:3,:3].T;rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),rw].astype(np.float32);hit=s.cast_rays(o3d.core.Tensor(rays));t=hit['t_hit'].numpy();fid=hit['primitive_ids'].numpy();ring=rs.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();valid=np.isfinite(t)&(t>0)&(t<ring-.05);tri=z['V'][z['F'][np.clip(fid,0,len(z['F'])-1)]];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);den=(normal*rw).sum(1);cos=abs(den)/np.maximum(1e-30,np.linalg.norm(normal,axis=1)*np.linalg.norm(rw,axis=1));stable=(cos>.001)&(np.linalg.norm(normal,axis=1)>2e-14);active=valid&stable;az=(normal*(tri[:,0]-T[:3,3])).sum(1)/np.where(stable,den,1.);sat=active&(abs(az-a['z'])>=5.);rows.append(dict(case=n,tag=tag,source=cid,fixed_N=len(t),first_valid_N=int(valid.sum()),active_stable_N=int(active.sum()),grazing_or_degenerate_N=int((valid&~stable).sum()),missing_or_CAD_blocked_N=int((~valid).sum()),robust_saturated_active_N=int(sat.sum()),inactive_depth_gradient='exact zero from constant9.5 branch',fixed_denominator_preserved=True))
    folder=R/'local_results/depth_mechanism';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(n+'_'+tag+'_'+cid+'.npz'),pixel_id=a['pixel_id'],uv=a['uv'],RGB_uv=a['RGB_uv'],HERO_z=a['z'],predicted_axial_z=t,valid=valid,saturated=sat,face_id=fid)
 save('metrics/DEPTH_MISSING_GRADIENT_CAUSES.json',rows);table('metrics/DEPTH_MISSING_GRADIENT_CAUSES.csv',rows);print('FIXED_NATIVE_RAY_COUNTS',len(counts),sorted({x['N']for x in counts}),flush=True)
if __name__=='__main__':main()
