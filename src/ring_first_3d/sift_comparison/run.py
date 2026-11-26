"""Independent B-task orchestration; A inputs are only read and hashed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import numpy as np
from ring_first_3d.v6_raw import route
from .core import split_tracks, query_manifest, select_tuples, predict_queries, summary, rgb_checks, positive_similarity, transform_cameras

W=Path('/home/liu/ring_first_3d_workspace')
WT=Path(__file__).resolve().parents[3]
TASK='TASK-RING-SIFT-VS-SIFT-COMPARISON-001'
REPORT=WT/'experiments'/TASK
BASE=W/'runs/ring_sift_comparison_001'
HIST=W/'runs/v6_raw_to_hero_001'
CASES=['GP_Ip_12.0mm_closed_R10_single_refY_005','GP_Ip_20.0mm_closed_R10_single_refY_004']
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
read,save,sha=route.read,route.save,route.sha


def kernels(root,meta):
    route.B=BASE/'kernel_runtime'
    m=route.legacy()
    return m,route.bind(m,root,meta)


def prepare(case,cohort="pilot"):
    from .expansion import authorized_cases
    assert case in authorized_cases(cohort),'CASE_NOT_AUTHORIZED'
    root=BASE/case; common=root/'common'; manifest=common/'INPUT_MANIFEST.json'
    if manifest.exists():
        for p,h in read(manifest)['source_hashes'].items():assert sha(p)==h,p
        return common
    common.mkdir(parents=True,exist_ok=True)
    meta=read(HIST/'prepared'/case/'PREPARED.json');a=HIST/'HIST'/case
    source_files=[HIST/'prepared'/case/'PREPARED.json',a/'CAMERA_COMPLETE.json',a/'config.json',a/'inputs/REFERENCE_RECEIPT.json',a/'metrics/GATES.json',Path(meta['raw_path'])]
    source_files+=list((a/'observations').glob('*.npz'))+[a/'predictions/ring_candidates005.json']
    for row in meta['frames']:
        assert sha(row['RGB_path'])==row['RGB_SHA256'];assert sha(row['Mask_path'])==row['Mask_SHA256']
        source_files.extend([Path(row['RGB_path']),Path(row['Mask_path'])])
    assert sha(meta['raw_path'])==meta['raw_sha256']
    shutil.copy2(a/'observations/tracks005.npz',common/'tracks.npz');shutil.copy2(a/'observations/pairs005.npz',common/'pairs.npz')
    save(common/'ledger.json',meta['frames']);save(common/'meta.json',meta)
    tr=np.load(common/'tracks.npz');split=split_tracks(tr['held']);save(common/'split.json',split)
    for part in ['validation','test']:save(common/(part+'_queries.json'),query_manifest(tr['xy'],split[part]))
    tuples=select_tuples(tr['xy'],split['train'])
    for i,t in enumerate(tuples['tuples']):
        t.update(tag=f'B_target_{i}',raw_target=meta['frames'][t['reference']]['raw_frame'],raw_support=[meta['frames'][j]['raw_frame'] for j in t['sources']])
    save(common/'TUPLES_FROZEN.json',tuples)
    outputs=list(common.glob('*'))
    save(manifest,dict(case=case,raw_sha256=meta['raw_sha256'],created_epoch=time.time(),source_commit='115e41fe5e57deff2898258d2ee836c83d686982',source_hashes={str(p):sha(p) for p in source_files},frozen_inputs={str(p):sha(p) for p in outputs},protocol_sha256=sha(REPORT/('EXPANSION_PROTOCOL.md' if cohort=='expanded' else 'COMPARISON_PROTOCOL.md')),cohort=cohort,split_counts={k:len(v) for k,v in split.items()},frames=len(meta['frames']),GT=False,test_historically_consumed=True))
    print('PREPARED',case,{k:len(v) for k,v in split.items()},tuples['tuples'],flush=True)
    return common


def verify_common(case):
    common=BASE/case/'common';m=read(common/'INPUT_MANIFEST.json')
    for p,h in m['frozen_inputs'].items():assert sha(p)==h,'COMMON_INPUT_DRIFT '+p
    return common


def solve_r(case):
    common=verify_common(case);root=BASE/case/'R';meta=read(common/'meta.json');a=HIST/'HIST'/case
    if (root/'receipt.json').exists():
        receipt=read(root/'receipt.json');assert sha(root/'cameras.npz')==receipt['camera_sha256'],'R_CAMERA_DRIFT';return receipt
    assert not (root/'STARTED.json').exists(),'Interrupted R run: preserve and inspect before retry'
    for d in ['inputs','observations','predictions','metrics','v5raw/inputs']:(root/d).mkdir(parents=True,exist_ok=True)
    for p,target in [(root/'scripts',route.V6/'scripts'),(root/'v5raw/scripts',route.V5/'scripts')]:
        if not p.exists():p.symlink_to(target,target_is_directory=True)
    shutil.copy2(a/'config.json',root/'config.json');shutil.copy2(common/'ledger.json',root/'inputs/ledger005.json')
    for p in (a/'observations').glob('*_ring.npz'):shutil.copy2(p,root/'observations'/p.name)
    shutil.copy2(common/'tracks.npz',root/'observations/tracks005.npz');shutil.copy2(common/'pairs.npz',root/'observations/pairs005.npz')
    shutil.copy2(a/'predictions/ring_candidates005.json',root/'predictions/ring_candidates005.json')
    m,mods=kernels(root,meta);mods['v6'].freeze('tracks',[root/'observations/tracks005.npz',root/'observations/pairs005.npz'])
    reference=read(a/'inputs/REFERENCE_RECEIPT.json');save(root/'inputs/REFERENCE_RECEIPT.json',reference)
    save(root/'STARTED.json',dict(epoch=time.time(),common_sha256=sha(common/'INPUT_MANIFEST.json'),source_commit=route.head(),source_sha256=sha(Path(__file__))))
    m.invoke_adapted_v6(mods['lba'],route.V6/'scripts/local_ring_sfm.py',reference['reference_index'],reference['heldout_index'],{'reference':1,'heldout':0})
    runs=read(root/'metrics/local005_solver.json');good=[r['version'] for r in runs if r['success']]
    if good:
        primary=min(good);cam=dict(np.load(root/f'predictions/local005_camera_{primary}.npz'))
        assert set(cam['point_track_ids']).issubset(set(read(common/'split.json')['train']))
        np.savez_compressed(root/'cameras.npz',**cam,component=np.zeros(len(cam['c2w']),int))
        save(root/'predictions/local005_primary.json',dict(primary_version=primary))
        receipt=dict(status='COMPLETED',primary=primary,components=[list(range(len(cam['c2w'])))],registered_union=list(range(len(cam['c2w']))),runs=runs,units='mm',test_not_consumed_in_B_solver=True)
    else:
        n=len(meta['frames']);np.savez_compressed(root/'cameras.npz',c2w=np.full((n,4,4),np.nan),K=route.K,points=np.empty((0,3)),point_track_ids=np.array([],int),component=np.full(n,-1))
        receipt=dict(status='FAILED',components=[],registered_union=[],runs=runs)
    receipt.update(camera_sha256=sha(root/'cameras.npz'),common_sha256=sha(common/'INPUT_MANIFEST.json'))
    save(root/'receipt.json',receipt);print('R_COMPLETE',case,receipt['status'],flush=True)
    return receipt


def evaluate(case):
    common=verify_common(case);root=BASE/case;meta=read(common/'meta.json');_,mods=kernels(root/'R',meta)
    tr=np.load(common/'tracks.npz');tuples=read(common/'TUPLES_FROZEN.json');cameras={};results={};predictions={}
    for arm in ['R','S']:
        cam=np.load(root/arm/'cameras.npz');cameras[arm]=cam
        po=cam['c2w'];numeric=np.isfinite(po).all(axis=(1,2));predictions[arm]={}
        for part in ['validation','test']:
            q=read(common/(part+'_queries.json'))
            pred=predict_queries(tr,po,q,mods['v6'].triangle,mods['v6'].project,route.K)
            save(root/arm/(part+'_predictions.json'),pred);predictions[arm][part]=pred
        gates=rgb_checks(predictions[arm]['validation'],len(po));save(root/arm/'RGB_CHECKS.json',gates)
        targets=[i for i in tuples['graph_eligible_targets'] if numeric[i] and sum(numeric[j] and tuples['train_overlap'][i][j]>=15 for j in range(len(po)) if j!=i)>=3]
        fixed=[dict(t,complete=bool(numeric[[t['reference']]+t['sources']].all())) for t in tuples['tuples']]
        results[arm]=dict(numeric_camera_ids=np.flatnonzero(numeric).tolist(),numeric_cameras=int(numeric.sum()),rgb_pass_ids=[g['frame'] for g in gates if g['passed']],rgb_pass=sum(g['passed'] for g in gates),graph_three_support_targets=targets,fixed_tuples=fixed,test={name:summary([p for p in predictions[arm]['test'] if p['category']==cat]) for name,cat in [('background',0),('polyp',1)]},camera_receipt=read(root/arm/'receipt.json'))
    pairing={}
    for key in ['numeric_camera_ids','rgb_pass_ids','graph_three_support_targets']:
        a,b=set(results['R'][key]),set(results['S'][key]);pairing[key]=dict(intersection=sorted(a&b),R_only=sorted(a-b),S_only=sorted(b-a),neither=sorted(set(range(len(meta['frames'])))-(a|b)))
    for cat,name in [(0,'background'),(1,'polyp')]:
        paired=[i for i,(a,b) in enumerate(zip(predictions['R']['test'],predictions['S']['test'])) if a['category']==cat and a['status']=='OK' and b['status']=='OK']
        pairing[name]=dict(total=sum(p['category']==cat for p in predictions['R']['test']),common_predicted=len(paired),R=summary([predictions['R']['test'][i] for i in paired]),S=summary([predictions['S']['test'][i] for i in paired]))
    for arm in ['R','S']:
        receipt=results[arm]['camera_receipt']
        union=receipt.get('registered_union_indices',receipt.get('registered_union',results[arm]['numeric_camera_ids']))
        results[arm]['registered_union_ids']=union
        results[arm]['registered_union_count']=len(union)
        results[arm]['downstream_component_scope']='largest connected component; all components preserved separately' if arm=='S' else 'single connected Ring RGB component'
    a,b=set(results['R']['registered_union_ids']),set(results['S']['registered_union_ids'])
    pairing['registered_union']=dict(intersection=sorted(a&b),R_only=sorted(a-b),S_only=sorted(b-a),neither=sorted(set(range(len(meta['frames'])))-(a|b)))
    # Only shared training 3D tracks define a single whole-video similarity.
    r,s=cameras['R'],cameras['S'];ri={int(t):i for i,t in enumerate(r['point_track_ids'])};si={int(t):i for i,t in enumerate(s['point_track_ids'])};ids=sorted(set(ri)&set(si)&set(read(common/'split.json')['train']))
    try:
        sim=positive_similarity(s['points'][[si[t] for t in ids]],r['points'][[ri[t] for t in ids]])
        sim.update(status='FROZEN',track_ids=ids,units='R_scale_normalized_units; R one unit = one mm; not independent S metric scale',camera_hashes={a:sha(root/a/'cameras.npz') for a in ['R','S']})
        if (root/'NORMALIZATION_FROZEN.json').exists():
            from .core import validate_frozen_similarity
            old=read(root/'NORMALIZATION_FROZEN.json')
            validate_frozen_similarity(old,sim['camera_hashes'],s['c2w'],np.load(root/'S/cameras_normalized.npz')['c2w'])
            if old!=sim:raise RuntimeError('FROZEN_NORMALIZATION_CHANGE_REFUSED')
        else:
            save(root/'NORMALIZATION_FROZEN.json',sim)
            np.savez_compressed(root/'S/cameras_normalized.npz',c2w=transform_cameras(s['c2w'],sim),K=route.K,points=sim['scale']*s['points']@np.array(sim['rotation']).T+sim['translation'],point_track_ids=s['point_track_ids'])
    except ValueError as e:
        if (root/'NORMALIZATION_FROZEN.json').exists():raise RuntimeError('EXISTING_NORMALIZATION_INVALID') from e
        save(root/'NORMALIZATION_FROZEN.json',dict(status='NOT_EVALUABLE',reason=str(e),common_training_points=len(ids)))
    out=dict(case=case,frames=len(meta['frames']),physical_groups=1,GT=False,arms=results,pairing=pairing,normalization=read(root/'NORMALIZATION_FROZEN.json'),stability=dict(status='NOT_EXECUTED',reason='paired perturbation repeats not in this feasibility budget'),historical_Q0_Q1=read(HIST/'HIST'/case/'metrics/GATES.json'))
    save(root/'CAMERA_RESULTS.json',out);print('EVALUATED',case,{a:(results[a]['numeric_cameras'],results[a]['rgb_pass']) for a in results},flush=True)
    return out


def main():
    from .expansion import authorized_cases,inference_limit,batch
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['prepare','R','S','evaluate','hero','report','poses','ring','cpu-batch','hero-batch','expanded-report'],required=True)
    parser.add_argument('--cohort',choices=['pilot','expanded'],default='pilot')
    parser.add_argument('--case',choices=authorized_cases('expanded'))
    args=parser.parse_args();cases=[args.case] if args.case else authorized_cases(args.cohort)
    assert set(cases).issubset(authorized_cases(args.cohort)),'CASE_NOT_AUTHORIZED_BY_COHORT'
    if args.stage in ['cpu-batch','hero-batch']:
        assert args.cohort=='expanded','EXPANSION_REQUIRES_EXPLICIT_COHORT'
        return batch(args.stage.split('-')[0],cases)
    if args.stage=='expanded-report':
        from .expanded_report import report_expanded
        return report_expanded()
    if args.stage=='report':
        from .report import report
        return report()
    for case in cases:
        if args.stage=='prepare':prepare(case,args.cohort)
        elif args.stage=='R':solve_r(case)
        elif args.stage=='S':
            from .colmap_arm import solve
            solve(verify_common(case),BASE/case/'S')
        elif args.stage=='evaluate':evaluate(case)
        elif args.stage=='hero':
            from .surfaces import hero
            hero(case,limit=inference_limit(args.cohort),respect_A=args.cohort=='expanded')
        elif args.stage=='poses':
            from .pose_metrics import evaluate_pose
            evaluate_pose(case)
        elif args.stage=='ring':
            from .ring_diagnostic import diagnose_ring
            diagnose_ring(case)
