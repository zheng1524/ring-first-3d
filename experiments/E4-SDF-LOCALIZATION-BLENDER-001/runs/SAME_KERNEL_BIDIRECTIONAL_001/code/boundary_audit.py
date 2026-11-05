"""Post-freeze measurement of GT edge vs foreground-pixel contour conventions."""
from model import *
from renderer import Renderer
def main():
    assert (R/'metrics/PREDICTION_FREEZE.json').exists()
    a=np.load(R/'audit_only/TARGET_GT.npz');renderer=Renderer();rows=[]
    for cid in protocol()['fit_views']:
        d=renderer.data[cid];r=renderer.silhouette(a['V'],a['F'],cid);target=d['target'];inside=cv2.distanceTransform(target.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);outside=cv2.distanceTransform((~target).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);gy,gx=np.gradient(outside-inside);di,idx=d['tree'].query(r['uv']);co=d['contour'][idx];pix=np.rint(co).astype(int);normal=np.c_[gx[pix[:,1],pix[:,0]],gy[pix[:,1],pix[:,0]]];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12);signed_offset=np.einsum('ij,ij->i',r['uv']-co,normal)
        rows.append(dict(view=cid,GT_edge_samples_N=len(di),signed_outward_offset_px=stats(signed_offset),mean_signed_outward_offset_px=float(np.mean(signed_offset)),outward_fraction=float(np.mean(signed_offset>0)),nearest_pixel_contour_distance_px=stats(di),interpretation='GT projected geometric edge relative to nearest foreground-pixel-center contour, using target outward distance-gradient normals; diagnostic only, no changed loss'))
    save('metrics/GT_PIXEL_CONTOUR_OFFSET.json',dict(after_prediction_freeze=True,no_parameter_sweep=True,rows=rows));print('PIXEL_CONTOUR_AUDIT',R.name,[(x['view'],x['mean_signed_outward_offset_px'])for x in rows],flush=True)
if __name__=='__main__':main()
