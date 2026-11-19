"""Task-local orchestration of frozen APIs. No camera/model/optimizer changes.

All camera solves are diagnostic until source, Ring fit, and map ancestry gates
pass. The original candidate winner is never replaced after rejection.
"""
from pathlib import Path
import argparse
import csv
import json
import time
import traceback
import hashlib
import numpy as np
from ring_first_3d.mainline.native.io import save_json, sha256
from ring_first_3d.policy.contracts import require

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[1]
SOURCES = ROOT/'src/ring_first_3d/mainline/lineage/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/inputs/SOURCES.json'
GROUPS = ['G01','G02','G03','G05','G06']

def read(p): return json.loads(Path(p).read_text())

def table(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def cases(): return [c for c in read(SOURCES)['cases'] if c['case'] in GROUPS]

def camera_gate(result, ring_mae, map_status):
    reasons=[]
    if result['candidate_source'] != 'originalRF5DoF_RGB_yaw':
        reasons.append('FORBIDDEN_PNP_OR_UNRESOLVED_YAW')
    if map_status != 'PASS': reasons.append('RGB_MAP_ANCESTRY_NOT_ADMITTED')
    if not np.isfinite(ring_mae) or ring_mae > 3.:
        reasons.append('RING_REPROJECTION_ABOVE_FROZEN_3PX')
    C=np.asarray(result['c2w_mm'])
    from ring_first_3d.mainline.native.geometry import validate_camera
    try: validate_camera(C, np.eye(3))
    except ValueError: reasons.append('INVALID_SE3')
    return dict(status='FAIL' if reasons else 'PASS', reasons=reasons)

def check_input(row):
    m=row['meta'];p=Path(row['cache']['path'])
    require(sha256(p)==row['cache']['sha256'],'INPUT_SHA',str(p))
    a=dict(np.load(p,allow_pickle=False))
    require(a['labels'].shape==(360,640) and a['RGB'].shape==(360,640,3),'INPUT_SHAPE',m['id'])
    require(np.isin(a['labels'],[0,1,2]).all(),'INPUT_LABELS',m['id'])
    require(np.allclose(a['K'],m['K'],atol=0,rtol=0),'K_IDENTITY',m['id'])
    for k,name in [('RGB','RGB_content_sha'),('labels','Mask_content_sha')]:
        if m.get(name): require(hashlib.sha256(a[k].tobytes()).hexdigest()==m[name],'PIXEL_SHA',m['id']+':'+k)
    return a

def audit():
    rows=[];banks=[];views=[]
    for c in cases():
        alias={}
        for role in ['FIT','HOLDOUT']:
            for v in c[role]:
                m=v['meta']
                for k in [m['id']]+m.get('aliases',[])+m.get('raw_candidate_aliases',[]):
                    require(k not in alias or alias[k][0]==role,'SPLIT_ALIAS',k)
                    alias[k]=(role,m['id'],m['video'])
        for video in sorted({v['meta']['video'] for r in ['FIT','HOLDOUT'] for v in c[r]}):
            p=TASK/'audit/reference_banks'/f"{c['case']}_{video}.npz"
            if not p.exists():
                banks.append(dict(group=c['case'],video=video,path=str(p),status='FAIL',reason='NO_FROZEN_SAME_VIDEO_RGB_MAP',points=0,strict_current_fit_tracks=0,held_tracks=0,unbound_observation_views=[]))
                continue
            obs=read(p.with_name(p.stem+'_OBSERVATIONS.json'))
            ids={o['view'] for r in obs for o in r['observations']}
            held=[i for i,r in enumerate(obs) if any(o['view'] in alias and alias[o['view']][0]=='HOLDOUT' for o in r['observations'])]
            clean=[i for i,r in enumerate(obs) if len(r['observations'])>=2 and all(o['view'] in alias and alias[o['view']][0]=='FIT' and alias[o['view']][2]==video for o in r['observations'])]
            # Original RGB code explicitly warns old canonical calibration may
            # inherit HOLDOUT; a lack of matching names is not a no-leak proof.
            # Preserve bank and diagnostic results, do not certify by assumption.
            banks.append(dict(group=c['case'],video=video,path=str(p),sha256=sha256(p),status='FAIL',reason='CALIBRATION_FIT_ANCESTRY_AND_GAUGE_UNCERTIFIED',points=len(obs),strict_current_fit_tracks=len(clean),held_tracks=len(held),unbound_observation_views=sorted(ids-set(alias)),original_prepare='021 prepare.py: non-G01 maps built from historical FIT; G01 map inherited calibration; current physical aliases incomplete',cross_video_bank_forbidden=True))
        for role in ['FIT','HOLDOUT']:
            for v in c[role]:
                m=v['meta'];a=check_input(v)
                out=dict(group=c['case'],video=m['video'],id=m['id'],role=role,cache=v['cache']['path'],cache_sha256=sha256(v['cache']['path']),RGB_path=m['RGB_source'],RGB_sha256=sha256(m['RGB_source']),Mask_path=m['Mask_source'],Mask_sha256=sha256(m['Mask_source']),RGB_array_sha256=hashlib.sha256(a['RGB'].tobytes()).hexdigest(),Mask_array_sha256=hashlib.sha256(a['labels'].tobytes()).hexdigest(),K=json.dumps(a['K'].tolist()),initial=c['initial']['path'],initial_sha256=sha256(c['initial']['path']),ring=c['static']['RING.npz']['path'],ring_sha256=sha256(c['static']['RING.npz']['path']),GT_path=c['GT']['path'],GT_sha256_recorded=c['GT']['sha256'],raw_frame=m.get('raw_frame'),frame_binding=m.get('frame_binding'),historical_camera_source=m.get('pose_source'),historical_camera_not_used_as_output=True)
                rows.append(out);views.append(v)
    table(TASK/'audit/INPUT_MANIFEST.csv',rows)
    save_json(TASK/'audit/RGB_MAP_AUDIT.json',banks)
    save_json(TASK/'audit/SELECTED_VIEWS.json',views)
    srcs=[ROOT/'src/ring_first_3d/mainline/native'/n for n in ['camera.py','rgb.py','geometry.py','hero.py','_kernels.py','upstream_source_lock.json']]
    srcs += sorted((TASK/'code').glob('*.py'))
    save_json(TASK/'audit/SOURCE_LOCK.json',[dict(path=str(p),sha256=sha256(p)) for p in srcs])
    save_json(TASK/'TASK_FREEZE.json',dict(task_sha256=sha256(TASK/'TASK.yaml'),sources_sha256=sha256(SOURCES),selected_views_sha256=sha256(TASK/'audit/SELECTED_VIEWS.json'),input_manifest_sha256=sha256(TASK/'audit/INPUT_MANIFEST.csv'),code_lock_sha256=sha256(TASK/'audit/SOURCE_LOCK.json'),GT_geometry_read=False,created_epoch=time.time()))
    print('AUDIT_FROZEN',len(rows),'views',len(banks),'videos',flush=True)

def verify_freeze():
    f=read(TASK/'TASK_FREEZE.json')
    for p,key in [(TASK/'TASK.yaml','task_sha256'),(SOURCES,'sources_sha256'),(TASK/'audit/SELECTED_VIEWS.json','selected_views_sha256'),(TASK/'audit/INPUT_MANIFEST.csv','input_manifest_sha256'),(TASK/'audit/SOURCE_LOCK.json','code_lock_sha256')]:
        require(sha256(p)==f[key],'FREEZE_SHA',str(p))
    for r in read(TASK/'audit/SOURCE_LOCK.json'):
        require(sha256(r['path'])==r['sha256'],'SOURCE_SHA',r['path'])

def cameras():
    import cv2
    from scipy.spatial import cKDTree
    from ring_first_3d.mainline.native.camera import recover, observe, torus_contours
    from ring_first_3d.mainline.native.rgb import pnp
    cv2.setNumThreads(1);verify_freeze()
    require(read(TASK/'logs/REGRESSION_RESULT.json')['status']=='PASS','REGRESSION','247 tests')
    require(read(TASK/'logs/NEW_TESTS.json')['status']=='PASS','REGRESSION','Task tests')
    banks={(r['group'],r['video']):r for r in read(TASK/'audit/RGB_MAP_AUDIT.json')}
    for v in read(TASK/'audit/SELECTED_VIEWS.json'):
        m=v['meta'];out=TASK/'runs'/m['case']/m['video']/'camera'/m['id'];out.mkdir(parents=True,exist_ok=True)
        if (out/'ADMISSION.json').exists():continue
        t=time.monotonic()
        try:
            a=check_input(v);b=banks[(m['case'],m['video'])]
            rr=pnp(a['RGB'],a['labels'],a['K'],dict(np.load(b['path']))) if Path(b['path']).exists() else None
            result=recover(a['labels'],a['K'],rr,initial_pose=None)
            # CAD support curves in image, observed Ring boundary -> CAD error.
            curves=torus_contours(np.asarray(result['c2w_mm']),a['K'])
            if isinstance(curves,tuple):curves=np.concatenate(curves)
            curves=np.asarray(curves).reshape(-1,2);curves=curves[np.isfinite(curves).all(1)]
            ob=observe(a['labels']);d=cKDTree(curves).query(ob['q_train'])[0]
            mae=float(d.mean());gate=camera_gate(result,mae,b['status'])
            result.update(seconds=time.monotonic()-t,source_view=m['id'],role=m['role'],GT_used=False,historical_pose_seed_used=False,pure_PnP_replacement_used=False,ring_boundary_MAE_px=mae,ring_boundary_p95_px=float(np.percentile(d,95)))
            save_json(out/'CAMERA_RESULT.json',result)
            if rr is not None:save_json(out/'RGB_GEOMETRY.json',rr)
            save_json(out/'ADMISSION.json',dict(**gate,diagnostic_only=gate['status']!='PASS',input_cache=v['cache'],map=b,source_lock=str(TASK/'audit/SOURCE_LOCK.json'),result=str(out/'CAMERA_RESULT.json'),seconds=time.monotonic()-t))
            print(m['id'],gate['status'],result['candidate_source'],'RingMAE',round(mae,4),'seconds',round(time.monotonic()-t,2),flush=True)
        except Exception:
            error=traceback.format_exc();(out/'ERROR.txt').write_text(error)
            save_json(out/'ADMISSION.json',dict(status='FAIL',reasons=['EXECUTION_ERROR'],error=error,seconds=time.monotonic()-t))
            print(m['id'],'FAIL',error.splitlines()[-1],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit','camera']);args=p.parse_args()
    {'audit':audit,'camera':cameras}[args.stage]()
