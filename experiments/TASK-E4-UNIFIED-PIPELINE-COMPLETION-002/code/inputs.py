"""Bind original same-video calibration inputs without reading HERO/GT shapes."""
from pathlib import Path
import json,re,copy
import numpy as np
from PIL import Image
import pipeline as p
from ring_first_3d.mainline.native.io import save_json,sha256
OLD_REPO=Path('/home/liu/polyp_research/ring-first-3d/experiments')
EXISTING=OLD_REPO/'TASK-E4-PYTORCH3D-014/config/EXISTING_VIEWS.json'
VIEWS21=OLD_REPO/'TASK-E4-RING-ANCHORED-JOINT-BA-021/config/VIEWS.json'
HISTORY_H=OLD_REPO/'TASK-E4-RING-ANCHORED-JOINT-BA-021/results/B3.json'
BUILDER=p.ROOT/'src/ring_first_3d/mainline/lineage/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/features019.py'

def calibration_admission(v,g,video,held):
    bad=[]
    if v.get('role')!='FIT':bad.append('NOT_ARCHIVED_FIT')
    if v.get('video')!=video or v.get('case',v.get('group',g))!=g:bad.append('WRONG_VIDEO_OR_GROUP')
    for k in ['RGB_source','Mask_source']:
        if not p.resolve_asset(v.get(k,'')).is_file():bad.append('MISSING_'+k)
    if bad:return bad,None
    rgb=np.array(Image.open(p.resolve_asset(v['RGB_source'])).convert('RGB'));lab=np.array(Image.open(p.resolve_asset(v['Mask_source'])))
    if rgb.shape!=(360,640,3) or lab.shape!=(360,640):bad.append('WRONG_INPUT_SHAPE')
    if p.arraysha(rgb) in held:bad.append('CURRENT_HOLDOUT_PIXEL_OVERLAP')
    if not np.isin(lab,[0,1,2]).all():bad.append('BAD_LABELS')
    return bad,dict(RGB=rgb,labels=lab,K=np.array(v['K']),T=np.array(v['T']))

def audit():
    assert not (p.TASK/'audit/INPUT_FREEZE.json').exists(),'Frozen audit cannot be overwritten'
    p.prior.verify_freeze()
    selected=p.views();save_json(p.TASK/'audit/SELECTED_VIEWS.json',selected)
    held={v['meta']['RGB_content_sha'] for v in selected if v['meta']['role']!='FIT'}
    # The pre-expansion archive has native posed RGB, not new 014 PnP targets.
    archive=p.read(EXISTING);v21=p.read(VIEWS21);candidates=[];rejected=[];seen=set()
    for g in p.GROUPS:
        for video in ['004','005']:
            rows=[v for v in archive if v.get('case')==g and v.get('video')==video]
            # Original G01 native 005 map observations are bound to this exact
            # archived catalog. Stored cross-video H is removed, never estimated.
            mapfile=p.OLD/'audit/reference_banks'/f'{g}_{video}.npz'
            obsfile=mapfile.with_name(mapfile.stem+'_OBSERVATIONS.json')
            recipe=None
            if video=='005' and mapfile.exists():
                ids={o['view'] for row in p.read(obsfile) for o in row['observations']}
                rows+= [v|dict(case=g) for v in v21 if v['id'] in ids and v.get('video')==video]
                recipe=dict(method='RESTORE_ARCHIVED_NATIVE_MAP',map=p.asset(mapfile),observations=p.asset(obsfile),stored_H=p.asset(HISTORY_H),H_direction='native005_to_archived004; apply its inverse to map XYZ only',no_new_transform_estimated=True)
            admitted=[]
            for v in rows:
                if v['id'] in seen:continue
                seen.add(v['id']);bad,a=calibration_admission(v,g,video,held)
                if bad:rejected.append(dict(group=g,video=video,id=v['id'],reasons=bad));continue
                cache=p.TASK/'audit/calibration'/g/video/(v['id']+'.npz');cache.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(cache,**a)
                row=dict(v,group=g,case=g,cache=str(cache),RGB_source=str(p.resolve_asset(v['RGB_source'])),Mask_source=str(p.resolve_asset(v['Mask_source'])),RGB_SHA256=sha256(p.resolve_asset(v['RGB_source'])),Mask_SHA256=sha256(p.resolve_asset(v['Mask_source'])),RGB_array_SHA256=p.arraysha(a['RGB']),Mask_array_SHA256=p.arraysha(a['labels']),calibration_pose_only=True,not_final_camera=True)
                admitted.append(row)
            save_json(p.TASK/'audit/calibration'/g/video/'VIEWS.json',admitted)
            candidates.append(dict(group=g,video=video,views=admitted,archive_recipe=recipe,missing=[] if admitted else ['NO_INDEPENDENT_SAME_VIDEO_ARCHIVED_RING_POSED_FIT_REFERENCE','Current 005 RGB exists but 014 extension poses used 004 fallback landmarks; not an independent native calibration']))
    save_json(p.TASK/'audit/CALIBRATION_INPUTS.json',candidates);save_json(p.TASK/'audit/REJECTED_CALIBRATION.json',rejected)
    raw=p.read(p.OLD/'audit/RAW_DATA_INVENTORY.json')
    for r in raw['files']:
        assert Path(r['path']).is_file() and sha256(r['path'])==r['sha256']
    save_json(p.TASK/'audit/RAW_DATA_INVENTORY.json',raw)
    files=[p.asset(p.TASK/'TASK.yaml'),p.asset(p.TASK/'audit/SELECTED_VIEWS.json'),p.asset(p.TASK/'audit/CALIBRATION_INPUTS.json'),p.asset(EXISTING),p.asset(VIEWS21),p.asset(HISTORY_H)]
    for c in candidates:
        for v in c['views']:files.extend(p.asset(v[k]) for k in ['cache','RGB_source','Mask_source'])
    scientific=[p.asset(p.ROOT/'src/ring_first_3d/mainline/native'/n) for n in ['camera.py','rgb.py','hero.py','geometry.py','_kernels.py','upstream_source_lock.json']]
    scientific.extend(p.asset(p.OLD/'code'/n) for n in ['body_stage.py','body_hooks.py','hero_stage.py','evaluate_stage.py','pipeline.py'])
    scientific.append(p.asset(BUILDER));save_json(p.TASK/'audit/INPUT_FREEZE.json',dict(files=files,scientific_sources=scientific,GT_geometry_read=False,baseline_commit='2fe2c3cbda40bd4d0f8a15a3d71dad3f494a1c7f'))
    p.table(p.TASK/'audit/CALIBRATION_INPUT_MANIFEST.csv',[{k:v.get(k) for k in ['group','video','id','role','RGB_source','RGB_SHA256','Mask_source','Mask_SHA256','RGB_array_SHA256','cache','pose_source']} for c in candidates for v in c['views']])
    print('INPUT_FROZEN',[(c['group'],c['video'],len(c['views'])) for c in candidates],flush=True)

if __name__=='__main__':audit()
