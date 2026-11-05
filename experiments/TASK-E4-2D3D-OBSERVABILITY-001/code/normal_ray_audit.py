"""Strict common outside-origin first-hit contract; preliminary audit is retained."""
from model import *
def main():
    assert load(R/'metrics/ALL_PREDICTIONS_FREEZE.json')['all_predictions_frozen_before_this_first_native_GT_evaluation']
    a=np.load(R/'inputs/BASE_SOURCE_MESH.npz');V,F=a['V'],a['F'];n=trimesh.Trimesh(V,F,process=False).vertex_normals;origin=V+.8*n;rays=o3d.core.Tensor(np.c_[origin,-n].astype(np.float32));base=scene(V,F);gt=np.load(R/'audit_only/NATIVE_CAD_GT.npz');target=scene(gt['V'],gt['F']);z0=base.cast_rays(rays)['t_hit'].numpy();zg=target.cast_rays(rays)['t_hit'].numpy();outside0=signed(base,origin)>0;outsideGT=signed(target,origin)>0;rows=[]
    for arm in ['ORIGINAL','SUBPIXEL_TARGET']:
        a=np.load(R/'local_results'/arm/'FINAL/MODEL.npz');rt=scene(a['V'],a['F']);zp=rt.cast_rays(rays)['t_hit'].numpy();outsidePred=signed(rt,origin)>0;valid=np.isfinite(z0)&np.isfinite(zg)&np.isfinite(zp)&(z0<=1.6)&(zg<=1.6)&(zp<=1.6)&outside0&outsideGT&outsidePred
        err=np.full(len(V),np.nan);np.subtract(zg,zp,out=err,where=valid);np.savez_compressed(R/'audit_only'/(arm+'_STRICT_NORMAL_RAYS.npz'),valid=valid,error=err,GT_origin_outside=outsideGT)
        rows.append(dict(arm=arm,fixed_N=len(V),valid_N=int(valid.sum()),missing_N=int((~valid).sum()),GT_origin_inside_N=int((~outsideGT).sum()),error_mm=stats(err)))
    save('metrics/STRICT_NORMAL_RAY_VALIDATION.json',dict(rows=rows,definition='identical initial normals, X+0.8n and direction -n; origin must be outside initial/GT/pred and first hit within1.6mm; failures NaN',supersedes='NATIVE_POSTERIOR.normal_rays omitted outside-origin condition; that preliminary table and arrays remain retained',predictions_and_main_nearest_surface_metrics_unchanged=True))
    print('STRICT_RAYS_DONE',rows,flush=True)
if __name__=='__main__':main()
