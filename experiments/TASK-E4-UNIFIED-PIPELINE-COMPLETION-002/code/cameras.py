"""Original RF numerics and RF_ONLY selection. No final PnP/historical pose."""
from pathlib import Path
import time,traceback
import numpy as np
import cv2
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.native.camera import recover,observe,torus_contours
from ring_first_3d.mainline.native.rgb import pnp
from ring_first_3d.mainline.native.io import save_json,sha256

def solve(group=None,video=None):
    p.verify();assert p.read(p.TASK/'logs/TESTS.json')['status']=='PASS';cv2.setNumThreads(1)
    for v in p.views():
        m=v['meta'];g,vi,cid=m['case'],m['video'],m['id']
        if group and g!=group or video and vi!=video:continue
        if p.inherited(g,vi) and not (g=='G03' and m['role']!='FIT' and p.read(p.inherited_file(g,vi,'camera/'+cid+'/ADMISSION.json'))['status']!='PASS'):continue
        out=p.OUT/g/vi/'camera'/cid;out.mkdir(parents=True,exist_ok=True)
        if (out/'ADMISSION.json').exists():continue
        b=p.read(p.OUT/g/vi/'bank/ADMISSION.json')
        if b['status']!='PASS':save_json(out/'ADMISSION.json',dict(status='NOT_RUN',reasons=['REFERENCE_BANK_FAIL'],bank=str(p.OUT/g/vi/'bank/ADMISSION.json')));continue
        start=time.monotonic()
        try:
            a=p.check_input(v);assert sha256(b['bank'])==b['sha256'];rr=pnp(a['RGB'],a['labels'],a['K'],dict(np.load(b['bank'])));result=recover(a['labels'],a['K'],rr,initial_pose=None);save_json(out/'ALL_CANDIDATES.json',result);save_json(out/'RGB_GEOMETRY.json',rr)
            legal=[q for q in result['candidates'] if q['source']=='originalRF5DoF_RGB_yaw']
            if not legal:
                save_json(out/'ADMISSION.json',dict(status='FAIL',reasons=['NO_RESOLVED_RING_FIRST_RGB_YAW'],bank=str(p.OUT/g/vi/'bank/ADMISSION.json'),RGB_matches=len(rr['matches']),RGB_inliers=len(rr['fit_pnp_inliers']),seconds=time.monotonic()-start));continue
            ch=min(legal,key=lambda q:q['FIT_objective']);C=np.array(ch['C']);d=cKDTree(torus_contours(C,a['K']).reshape(-1,2)).query(observe(a['labels'])['q_train'])[0]
            r=dict(c2w_mm=C,candidate_source=ch['source'],FIT_objective=ch['FIT_objective'],ring_boundary_MAE_px=float(d.mean()),ring_boundary_p95_px=float(np.percentile(d,95)),original_mixed_winner=result['candidate_source'],GT_used=False,PnP_used_as_final_camera=False,historical_pose_seed_used=False,source_view=cid,role=m['role'],seconds=time.monotonic()-start)
            gate=p.camera_gate(r,r['ring_boundary_MAE_px'],b['status']);save_json(out/'CAMERA_RESULT.json',r);save_json(out/'ADMISSION.json',dict(**gate,bank=str(p.OUT/g/vi/'bank/ADMISSION.json'),input=v['cache'],source_version=p.asset(p.ROOT/'src/ring_first_3d/mainline/native/camera.py'),result=str(out/'CAMERA_RESULT.json')))
            if p.inherited(g,vi):
                old=p.read(p.inherited_file(g,vi,'camera/'+cid+'/CAMERA_RESULT.json'));delta=float(abs(np.array(old['c2w_mm'])-C).max());save_json(out/'OLD_REPLAY_COMPARISON.json',dict(max_abs_pose_difference=delta,old_Ring_MAE_px=old['ring_boundary_MAE_px'],new_Ring_MAE_px=r['ring_boundary_MAE_px'],old_prediction_unchanged=True,threshold_unchanged=True))
            print('CAMERA',g,vi,cid,gate['status'],r['ring_boundary_MAE_px'],flush=True)
        except Exception:
            err=traceback.format_exc();save_json(out/'ADMISSION.json',dict(status='FAIL',reasons=['CAMERA_EXECUTION_ERROR'],error=err));print('CAMERA_ERROR',cid,err,flush=True)

if __name__=='__main__':solve()
