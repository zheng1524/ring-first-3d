"""Correct plane-normal perturbation anchors; leave frozen base fits unchanged.

The first D3 script rotated about a median inlier point which need not lie on
the fitted plane. This post-analysis isolates angle sensitivity by projecting
that anchor onto the original plane first. Old results are preserved.
"""
from physical_export import *
def main():
    save('provenance/HEIGHT_SENSITIVITY_CORRECTION.json',dict(**stamp([Path(__file__),R/'metrics/D3_height_ROI_trials.json']),reason='Original median inlier anchor was off-plane. No fit, height, ROI, or prediction changed; original normal-angle sensitivity excluded from scientific interpretation.',base_fits_recomputed=False))
    rows=[]
    for r in load(R/'metrics/D3_height_ROI_trials.json'):
        if 'plane'not in r:continue
        s=source(r['reference']);b=background(r['reference']);p=s['p'];v,u=b['uv'][:,1],b['uv'][:,0];dist=cv2.distanceTransform((p['labels']!=1).astype(np.uint8),cv2.DIST_L2,5)[v,u];lo,hi=r['ROI_pixels'];Q=b['P'][(dist>=lo)&(dist<=hi)&b['quality']];plane=np.array(r['plane']);inliers=abs(Q@plane[:3]+plane[3])<=cfg()['D3_plane_inlier_distance_mm'];anchor0=np.median(Q[inliers],0);anchor=anchor0-(anchor0@plane[:3]+plane[3])*plane[:3];P=s['P'];base=float(np.quantile(P@plane[:3]+plane[3],.95));assert np.isclose(base,r['height_candidate_p95_mm']);assert abs(anchor@plane[:3]+plane[3])<1e-10;values=[]
        for axis in ['x','y']:
            for angle in [-1,0,1]:
                n=Rotation.from_euler(axis,angle,degrees=True).apply(plane[:3]);height=float(np.quantile((P-anchor)@n,.95));values.append(dict(axis=axis,degrees=angle,height_p95_mm=height,change_from_original_mm=height-base));assert angle!=0 or np.isclose(height,base)
        rows.append(dict(reference=r['reference'],video=r['video'],ROI_pixels=r['ROI_pixels'],base_fit_status=r['status'],height_p95_mm=base,off_plane_anchor_distance_mm=float(anchor0@plane[:3]+plane[3]),corrected_anchor_mm=anchor,normal_perturbations=values,offset_pm025_height_mm=[base-.25,base+.25],source_model_unchanged=True))
    save('metrics/D3_height_sensitivity_corrected.json',rows);csvsave('metrics/D3_height_sensitivity_corrected.csv',rows);print('HEIGHT_SENSITIVITY_CORRECTED',len(rows),'frozen base models unchanged',flush=True)
if __name__=='__main__':main()
