"""P1-B: native Ring depth vs fixed CAD, with NO residual-based selection."""
from common import *

def main():
    cfg=load(R/'config/PREREGISTERED.json');rows=[];uv=grid();root=R/'local_results/ring';root.mkdir(exist_ok=True)
    for scene,refs in selected().items():
        for ref in refs:
            c,p,r=source(ref);labels=p['labels'];native=p['depth_mm'];mask=labels==2
            sc=SameCameraScene(ring(c['ring']),p['K'],p['pose'],(640,360),str(VENDOR));hit=sc.cast(uv)
            cad=hit['t_hit'].numpy().reshape(360,640);normal=hit['primitive_normals'].numpy()
            d=vis.camera_rays(uv,p['K'],p['pose'])[:,3:];d/=np.linalg.norm(d,axis=1)[:,None]
            incidence=abs((normal*d).sum(1)).reshape(360,640)
            finite=np.isfinite(cad)&(cad>0);native_valid=np.isfinite(native)&(native>0)
            inner=cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8))>0
            cadinner=cv2.erode(finite.astype(np.uint8),np.ones((3,3),np.uint8))>0
            loose=mask&finite&native_valid
            reliable=inner&cadinner&native_valid&(incidence>=cfg['ring_min_incidence'])
            residual=native-cad
            for tier,valid in [('RING_INTERSECTION_DIAGNOSTIC',loose),('RING_INTERIOR_INCIDENCE',reliable)]:
                stat=residual_stats(residual[valid]);parity=((uv[:,0]//40+uv[:,1]//40)%2).reshape(360,640)
                halves=[float(np.median(residual[valid&(parity==k)])) if (valid&(parity==k)).any() else None for k in [0,1]]
                rows.append(dict(scene=scene,source=ref,tier=tier,Ring_Mask_N=int(mask.sum()),
                    CAD_hit_on_Ring_N=int((mask&finite).sum()),native_Ring_depth_N=int((mask&native_valid).sum()),
                    valid_Ring_pixel_N=stat['N'],coverage_of_Ring_Mask=stat['N']/int(mask.sum()) if mask.any() else None,
                    CAD_mask_support_fraction=float((mask&finite).sum()/mask.sum()) if mask.any() else None,
                    **stat,tile_half0_median=halves[0],tile_half1_median=halves[1],
                    status='EVALUABLE_CONDITIONAL_ON_FROZEN_CAMERA' if stat['N'] else 'NOT_EVALUABLE_NO_NATIVE_RING_SUPPORT',
                    selection='Ring identity eroded1px/CAD incidence>=0.2; NO Z-residual filter',
                    native_HERO_modified=False,Polyp_depth_substituted=False))
            np.savez_compressed(root/(ref+'.npz'),native_Ring_Z_mm=np.where(mask&native_valid,native,np.nan),
                CAD_Z_mm=np.where(finite,cad,np.nan),source_Ring_Mask=mask,reliable_Ring=reliable,
                residual_mm=np.where(loose,residual,np.nan),incidence=incidence)
            print('RING_NATIVE_AUDIT',ref,'mask',int(mask.sum()),'reliable',int(reliable.sum()),flush=True)
    table('metrics/RING_DEPTH_RESIDUALS.csv',rows)
    save('metrics/P1_RING_GATE.json',dict(status='DIAGNOSTICS_RECORDED',source_N=6,evaluable_source_N=sum(x['N']>0 for x in rows if x['tier']=='RING_INTERIOR_INCIDENCE'),
        source_Ring_qualification_independent_of_Polyp=True,residual_based_selection=False,GT_used=False,GPU='NOT_AUTHORIZED'))

if __name__=='__main__':main()
