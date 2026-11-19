"""Explicit Ring-First-only source policy, with unchanged numerical candidates."""
import argparse
from pathlib import Path
import copy
import json
import time
import numpy as np
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.native.io import sha256,save_json
from ring_first_3d.mainline.native.camera import torus_contours,observe
T=p.TASK;R=p.ROOT;OUT=T/'runs/RF_ONLY_V1'
OLD_VIEWS=Path('/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/geometric_pose_optimization/config/VIEWS.json')

def prepare():
    p.verify_freeze();OUT.mkdir(parents=True,exist_ok=False)
    old=p.read(OLD_VIEWS);lookup={v['id']:v for v in old}
    for c in p.read(T/'audit/map_reference_identity/FOUR_GROUP_INPUTS.json'):
        for k in ['sources','views']:
            for v in c.get(k,[]):lookup[v.get('id',v.get('view_id'))]=v.get('meta',v)
    held={r['meta']['RGB_content_sha'] for r in p.read(T/'audit/SELECTED_VIEWS.json') if r['meta']['role']!='FIT'}
    bankrows=[];inputs=[]
    for p0 in sorted((T/'audit/reference_banks').glob('*.npz')):
        group,video=p0.stem.split('_');obs=p.read(p0.with_name(p0.stem+'_OBSERVATIONS.json'));ids={x['view'] for row in obs for x in row['observations']};evidence=[];bad=[]
        for k in sorted(ids):
            m=lookup.get(k,{});h=m.get('RGB_content_sha');role=m.get('role')
            evidence.append(dict(id=k,role=role,video=m.get('video'),RGB_array_SHA256=h))
            if role!='FIT' or m.get('video')!=video or not h:bad.append(k+':UNBOUND_REFERENCE')
            if h in held:bad.append(k+':CURRENT_HOLDOUT_OVERLAP')
        if group=='G01' and video=='005':bad.append('INHERITED_CROSS_VIDEO_MAP_GAUGE_UNCERTIFIED')
        bankrows.append(dict(group=group,video=video,status='FAIL' if bad else 'PASS',reasons=bad,path=str(p0),sha256=sha256(p0),calibration_FIT_ancestry=evidence,conditional_calibration_not_pose_GT=True))
    for d in (T/'runs').glob('G*/0*/camera/*/CAMERA_RESULT.json'):inputs.append(dict(path=str(d),sha256=sha256(d)))
    save_json(OUT/'BANK_ADMISSION.json',bankrows)
    save_json(OUT/'FREEZE.json',dict(protocol_sha256=sha256(T/'PROTOCOL_RF_ONLY.yaml'),code_sha256=sha256(Path(__file__)),original_freeze_sha256=sha256(T/'TASK_FREEZE.json'),old_reference_views=dict(path=str(OLD_VIEWS),sha256=sha256(OLD_VIEWS)),bank_admission_sha256=sha256(OUT/'BANK_ADMISSION.json'),numerical_inputs=inputs,epoch=time.time(),GT_read=False))

def cameras():
    f=p.read(OUT/'FREEZE.json');assert sha256(T/'PROTOCOL_RF_ONLY.yaml')==f['protocol_sha256'];assert sha256(Path(__file__))==f['code_sha256']
    for a in f['numerical_inputs']:assert sha256(a['path'])==a['sha256']
    banks={(r['group'],r['video']):r for r in p.read(OUT/'BANK_ADMISSION.json')};rows=[]
    for v in p.read(T/'audit/SELECTED_VIEWS.json'):
        m=v['meta'];src=T/'runs'/m['case']/m['video']/'camera'/m['id']/'CAMERA_RESULT.json';original=p.read(src)
        # Predeclared source-family selection, no tuning, no new camera solve.
        candidates=[q for q in original['candidates'] if q['source']=='originalRF5DoF_RGB_yaw']
        b=banks.get((m['case'],m['video']),dict(status='FAIL',reasons=['NO_SAME_VIDEO_RGB_MAP']))
        out=OUT/m['case']/m['video']/'camera'/m['id'];out.mkdir(parents=True,exist_ok=True)
        if not candidates:
            save_json(out/'ADMISSION.json',dict(status='FAIL',reasons=['NO_RESOLVED_RING_FIRST_CANDIDATE'],original_result=str(src),original_sha256=sha256(src),bank=b));continue
        chosen=min(candidates,key=lambda q:q['FIT_objective']);a=p.check_input(v);C=np.array(chosen['C']);q=observe(a['labels'])['q_train'];curves=torus_contours(C,a['K']).reshape(-1,2);d=cKDTree(curves).query(q)[0]
        result=dict(c2w_mm=C,candidate_source=chosen['source'],FIT_objective=chosen['FIT_objective'],ring_boundary_MAE_px=float(d.mean()),ring_boundary_p95_px=float(np.percentile(d,95)),original_mixed_winner=original['candidate_source'],original_result=str(src),original_sha256=sha256(src),selected_candidate_index=original['candidates'].index(chosen),selection_protocol='RF_ONLY_V1',original_camera_candidate_max_abs_delta_mm=0.,GT_used=False,PnP_used_as_final_camera=False,reference_view=m['id'],role=m['role'])
        gate=p.camera_gate(result,result['ring_boundary_MAE_px'],b['status']);save_json(out/'CAMERA_RESULT.json',result);save_json(out/'ADMISSION.json',dict(**gate,bank=b,source_policy='RF_ONLY_V1',result=str(out/'CAMERA_RESULT.json')))
        rows.append(dict(group=m['case'],video=m['video'],id=m['id'],role=m['role'],status=gate['status'],ring_MAE_px=result['ring_boundary_MAE_px'],reasons=';'.join(gate['reasons']),result=str(out/'CAMERA_RESULT.json')))
    p.table(OUT/'CAMERA_METRICS.csv',rows);print('RF_ONLY',len(rows),'resolved;',sum(r['status']=='PASS' for r in rows),'admitted',flush=True)

if __name__=='__main__':
    x=argparse.ArgumentParser();x.add_argument('stage',choices=['prepare','camera']);a=x.parse_args();{'prepare':prepare,'camera':cameras}[a.stage]()
