"""Original native depth vs original Raw discretization, diagnostic only; no filtering."""
from common import *
import open3d as o3d

def main():
 rows=[]
 for r in load(R/'config/VIEW_PLAN.json'):
  root=R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id'];a=np.load(root/'OBS_TRUSTED.npz');m=np.load(root/'FULL_HERO.npz');V,F=m['V'],m['F'];K,T=a['K'],a['T'];ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(K).T;world=ray@T[:3,:3].T;rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),world].astype(np.float32);z=scene(V,F).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();good=np.isfinite(z);res=z[good]-a['z'][good];rows.append(dict(group=r['group'],view=r['view_id'],role=r['role'],trusted_native_N=len(z),original_Raw_first_hit_N=int(good.sum()),Raw_vs_native_axial_mm=stats(res),normal_finite_N=int(np.isfinite(a['normal']).all(1).sum()),diagnostic_only=True,changes_to_observations=False))
 save('metrics/RAW_DISCRETIZATION_VS_NATIVE_DIAGNOSTIC.json',rows);table('metrics/RAW_DISCRETIZATION_VS_NATIVE_DIAGNOSTIC.csv',rows);print('SOURCE_RAW_DISCRETIZATION_AUDIT_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
