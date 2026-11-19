"""Pre-GT camera failure evidence; no parameter selection or extra solve."""
from pathlib import Path
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.native.camera import torus_contours,observe
from ring_first_3d.mainline.native.io import save_json

def main():
    folder=p.TASK/'visualization/FAILURE_DIAGNOSTICS';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for v in p.views():
        m=v['meta'];root=p.OUT/m['case']/m['video']/'camera'/m['id'];ad=root/'ADMISSION.json'
        if not ad.exists() or p.read(ad)['status']=='PASS':continue
        a=p.check_input(v);data=p.read(root/'ALL_CANDIDATES.json') if (root/'ALL_CANDIDATES.json').exists() else {};rgb=p.read(root/'RGB_GEOMETRY.json') if (root/'RGB_GEOMETRY.json').exists() else {};cands=[r for r in data.get('candidates',[]) if r['source']=='originalRF5DoF_RGB_yaw'];q=observe(a['labels'])['q_train'];errors=[float(cKDTree(torus_contours(np.array(c['C']),a['K']).reshape(-1,2)).query(q)[0].mean()) for c in cands]
        row=dict(group=m['case'],video=m['video'],id=m['id'],role=m['role'],reasons=p.read(ad)['reasons'],RGB_features=rgb.get('features_N'),RGB_matches=len(rgb.get('matches',[])),RGB_PnP_input_inliers=len(rgb.get('fit_pnp_inliers',[])),RF_legal_candidates=len(cands),minimum_Ring_MAE_over_existing_legal_candidates_px=min(errors) if errors else None,threshold_px=3.,cause='Original RGB RANSAC did not produce six input inliers' if not cands else 'All existing RF candidate Ring errors exceed fixed 3px gate' if min(errors)>3 else 'Original source-family selection failed Ring gate',root_physical_cause_proven=False,GT_or_HERO_used=False,admission=str(ad));rows.append(row)
        fig,axs=plt.subplots(1,3,figsize=(15,4));axs[0].imshow(a['RGB']);axs[0].set_title('Frozen actual RGB');axs[1].imshow(a['RGB'],alpha=.6);axs[1].contour(a['labels']==2,levels=[.5],colors='cyan');axs[1].contour(a['labels']==1,levels=[.5],colors='lime');axs[1].set_title('Observed Ring cyan / Polyp green')
        result=root/'CAMERA_RESULT.json'
        if result.exists():
            C=np.array(p.read(result)['c2w_mm']);curves=torus_contours(C,a['K']);axs[2].imshow(a['RGB'],alpha=.4)
            for curve in curves:axs[2].plot(*curve.T,c='yellow',lw=.8)
            d=cKDTree(curves.reshape(-1,2)).query(q)[0];sc=axs[2].scatter(*q.T,c=d,vmin=0,vmax=12,s=12,cmap='magma');fig.colorbar(sc,ax=axs[2],label='Observed Ring -> CAD [px]');axs[2].set_title(f'MAE {d.mean():.5f}px / P95 {np.percentile(d,95):.5f}px\nClipped >12px: {(d>12).sum()} / {len(d)}')
        else:axs[2].imshow(a['RGB'],alpha=.3);axs[2].text(.5,.5,f'Yaw NOT_RESOLVED\nRGB matches {row["RGB_matches"]}; input inliers {row["RGB_PnP_input_inliers"]}\nNo final PnP substitute',ha='center',transform=axs[2].transAxes,color='red')
        for ax in axs:ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_xlabel('u [px]');ax.set_ylabel('v [px]')
        fig.suptitle(m['id']+' '+m['role']+' | unchanged thresholds | input SHA '+v['cache']['sha256'][:12]);fig.tight_layout(rect=(0,0,1,.86));fig.savefig(folder/(m['id']+'.png'),dpi=125);plt.close(fig)
    p.table(p.TASK/'metrics/CAMERA_FAILURE_DIAGNOSTICS.csv',rows);save_json(p.TASK/'metrics/CAMERA_FAILURE_DIAGNOSTICS.json',rows);print('CAMERA_FAILURE_DIAGNOSTICS',len(rows),flush=True)
def component_analysis():
    rows=[]
    for v in p.views():
        m=v['meta'];root=p.OUT/m['case']/m['video']/'camera'/m['id'];f=root/'CAMERA_RESULT.json'
        if not f.exists() or p.read(root/'ADMISSION.json')['status']=='PASS':continue
        a=p.check_input(v);q=observe(a['labels'])['q_train'];n,comp,areas,centers=cv2.connectedComponentsWithStats((a['labels']==2).astype(np.uint8),8);C=np.array(p.read(f)['c2w_mm']);d=cKDTree(torus_contours(C,a['K']).reshape(-1,2)).query(q)[0]
        # Each half-pixel boundary has one Ring-labelled adjacent pixel.
        # Associate to that component without deleting/reweighting any point.
        labels=[]
        for u,w in q:
            x=np.clip([int(np.floor(u)),int(np.ceil(u))],0,639);y=np.clip([int(np.floor(w)),int(np.ceil(w))],0,359);labels.append(int(comp[np.ix_(y,x)].max()))
        labels=np.array(labels);assert (labels>0).all()
        for i in range(1,n):
            ix=labels==i;rows.append(dict(group=m['case'],video=m['video'],id=m['id'],role=m['role'],component=i,area_px=int(areas[i,cv2.CC_STAT_AREA]),centroid_u_px=float(centers[i,0]),centroid_v_px=float(centers[i,1]),observed_boundary_N=int(ix.sum()),fixed_total_boundary_N=len(q),component_Ring_MAE_px=float(d[ix].mean()) if ix.any() else None,component_Ring_p95_px=float(np.percentile(d[ix],95)) if ix.any() else None,contribution_to_original_total_MAE_px=float(d[ix].sum()/len(q)),input_or_prediction_changed=False))
    p.table(p.TASK/'metrics/RING_COMPONENT_DIAGNOSTICS.csv',rows);save_json(p.TASK/'metrics/RING_COMPONENT_DIAGNOSTICS.json',rows)
    print('RING_COMPONENT_DIAGNOSTICS',rows,flush=True)

if __name__=='__main__':main();component_analysis()
