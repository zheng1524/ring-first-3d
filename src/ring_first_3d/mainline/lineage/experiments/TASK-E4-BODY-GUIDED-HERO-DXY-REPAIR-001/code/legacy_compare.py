"""Post-freeze DT+AMS comparison ONLY; no output may enter E1/E2 fitting."""
from common import *
reuse(OLD/'code/geometry.py',['ellipse_descriptor','ellipse_coords','ellipse_curve'],globals())
def main():
    assert (R/'provenance/ALL_PREDICTIONS_FROZEN.json').exists()
    guard('evaluation');rows=[];yy,xx=np.mgrid[:360,:640];uv=np.c_[xx.ravel(),yy.ravel()]
    for d in load(R/'provenance/DXY_GENERATED.json'):
        cid=d['source'];s=source(cid);e=ellipse_descriptor(s['labels']==1);oldq=ellipse_coords(uv,e);oldmask=(np.sum(oldq**2,axis=1)<=1).reshape(360,640)
        B=np.array(d['basis_px']);c=np.array(d['center_px']);q=(uv-c)@np.linalg.inv(B).T;newmask=(np.sum(q*q,axis=1)<=1).reshape(360,640)
        full=s['labels']==1;known=s['labels']!=2;axes=np.linalg.svd(B,compute_uv=False)
        rows.append(dict(source=cid,center_shift_px=float(np.linalg.norm(c-e['center'])),old_semiaxes_px=e['axes'],DXY_semiaxes_px=axes,major_semiaxis_change_px=float(axes[0]-e['axes'][0]),minor_semiaxis_change_px=float(axes[1]-e['axes'][1]),geometry_IoU_known=float((oldmask&newmask&known).sum()/max(1,((oldmask|newmask)&known).sum())),old_vs_original_mask_IoU=float((oldmask&full).sum()/max(1,((oldmask|full)&known).sum())),DXY_vs_original_mask_IoU=float((newmask&full).sum()/max(1,((newmask|full)&known).sum())),comparison_only=True,old_DT_AMS_used_in_new_prediction=False))
    table('metrics/DXY_VS_OLD_DT_AMS.csv',rows)
    save('provenance/LEGACY_COMPARISON_ONLY.json',dict(epoch=time.time(),source=asset(OLD/'code/geometry.py'),functions=['ellipse_descriptor','ellipse_coords','ellipse_curve'],predictions_already_frozen=True,results_not_used_for_fitting=True))
if __name__=='__main__':main()
