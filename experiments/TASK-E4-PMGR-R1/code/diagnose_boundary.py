"""Read-only check of asymmetry between observed and predicted Ring bands."""
from postprocess import *

def main():
    _,_,m=restore('G01_004');oo=Observations('G01_004',m);u=load(R/'metrics/ALL_UPDATE_PROPOSALS.json')[-1];d=dict(np.load(u['snapshot']));z=oo.linearize(d['q_before'],None,True);rows=[]
    for cid,mp in z['mapping'].items():
        s=source(cid);px=np.clip(np.rint(mp['uv']).astype(int),[0,0],[639,359]);ring=s['labels']==2;dt=cv2.distanceTransform((~ring).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);dist=dt[px[:,1],px[:,0]];e=mp['contour_error_px'];inner=cv2.dilate(ring.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)[px[:,1],px[:,0]]
        rows.append(dict(source=cid,predicted_boundary_N=len(e),predicted_in_observed_excluded_Ring_band_N=int(inner.sum()),boundary_error_sum_Ring_band_fraction=float(e[inner].sum()/max(e.sum(),1e-10)),large_error_gt10_N=int((e>10).sum()),large_error_Ring_distance_median_px=float(np.median(dist[e>10]))if(e>10).any()else None,all_Ring_distance_px=stats(dist),scope='POSTHOC_READONLY_NO_GATE_CHANGE'))
    save('metrics/RING_CONTOUR_ASYMMETRY_DIAGNOSTIC.json',rows)

if __name__=='__main__':main()
