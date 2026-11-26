"""Frozen native HERO invocation and paired directed-depth diagnostics."""
import ast
import fcntl
import gc
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import cv2
import numpy as np
from .run import BASE,HIST,REPORT,WT,W,read,save,sha,kernels,verify_common,route
from ring_first_3d.v6_raw.policy import tuple_identity
from .core import validate_frozen_similarity


def zbuffer(uv,z,shape):
    valid=np.isfinite(uv).all(1)&np.isfinite(z)&(z>0)
    xy=np.rint(uv[valid]).astype(int);depth=z[valid]
    inside=(xy[:,0]>=0)&(xy[:,0]<shape[1])&(xy[:,1]>=0)&(xy[:,1]<shape[0])
    xy,depth=xy[inside],depth[inside]
    out=np.full(shape,np.inf);np.minimum.at(out,(xy[:,1],xy[:,0]),depth)
    out[~np.isfinite(out)]=np.nan
    return out


def paired_depth(rz,rt,sz,st,polyp):
    valid=lambda a,b:polyp&np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0)
    rv,sv=valid(rz,rt),valid(sz,st);common=rv&sv
    ro=rv&(rz>rt+np.maximum(.5,.01*rt));so=sv&(sz>st+np.maximum(.5,.01*st))
    def stats(x):return dict(median=float(np.median(x)) if len(x) else None,P95=float(np.quantile(x,.95)) if len(x) else None)
    out=dict(target_polyp_pixels=int(polyp.sum()),R_projected_pixels=int(rv.sum()),S_projected_pixels=int(sv.sum()),R_possible_occluded=int(ro.sum()),S_possible_occluded=int(so.sum()),units='R_scale_normalized_units',not_GT=True)
    masks=dict(R_valid=rv,S_valid=sv,all_common=common,both_nonoccluded=common&~ro&~so)
    for name in ['all_common','both_nonoccluded']:
        mask=masks[name];n=int(mask.sum());out[name]=dict(pixels=n,fraction_of_target=n/int(polyp.sum()) if polyp.any() else None,R=stats(abs(rz[mask]-rt[mask])),S=stats(abs(sz[mask]-st[mask])))
    return out,masks


def other_gpu_processes(text,own_pid):
    return [line.strip() for line in text.splitlines() if line.strip() and line.split(",",1)[0].strip()!=str(own_pid)]


def hero(case,limit=8,respect_A=False):
    common=verify_common(case);root=BASE/case;meta=read(common/'meta.json');tuples=read(common/'TUPLES_FROZEN.json')['tuples'];normal=read(root/'NORMALIZATION_FROZEN.json')
    if (root/'HERO_DEPTH_RESULTS.json').exists() and all((root/a/'hero/RESULT.json').exists() and read(root/a/'hero/RESULT.json')['status']=='COMPLETED' for a in ['R','S']):
        for arm in ['R','S']:
            for path,h in read(root/arm/'hero/RESULT.json')['outputs'].items():assert sha(path)==h,'CACHED_HERO_DRIFT '+path
        return read(root/'HERO_DEPTH_RESULTS.json')
    checkpoint=Path(read(route.CORE/'site_config.local.json')['checkpoint']);assert sha(checkpoint)==route.MODEL_SHA
    for arm in ['R','S']:
        dest=root/arm/'hero'
        if (dest/'RESULT.json').exists():
            previous=read(dest/'RESULT.json')
            if previous['status']!='NOT_EXECUTED_GPU_BUSY':continue
            starts=BASE/'INFERENCE_STARTS.jsonl'
            attempts=[json.loads(x) for x in starts.read_text().splitlines()] if starts.exists() else []
            assert not any(x['case']==case and x['arm']==arm for x in attempts),'BUSY_RETRY_WITH_PRIOR_ATTEMPT'
            shutil.copy2(dest/'RESULT.json',dest/('BUSY_RECEIPT_'+sha(dest/'RESULT.json')[:12]+'.json'))
        dest.mkdir(parents=True,exist_ok=True)
        camera=root/arm/('cameras_normalized.npz' if arm=='S' else 'cameras.npz')
        if not camera.exists() or (arm=='S' and normal.get('status')!='FROZEN'):
            save(dest/'RESULT.json',dict(status='NOT_EVALUABLE',reason='NO_FROZEN_GLOBAL_SCALE',tuples=tuples));continue
        cam=dict(np.load(camera));poses=cam['c2w']
        if arm=='S':validate_frozen_similarity(normal,{a:sha(root/a/'cameras.npz') for a in ['R','S']},np.load(root/'S/cameras.npz')['c2w'],poses)
        valid=[];skipped=[];rows=meta['frames']
        for t in tuples:
            if not np.isfinite(poses[[t['reference']]+t['sources']]).all():skipped.append(dict(t,status='NOT_EVALUABLE',reason='FIXED_TUPLE_CAMERA_MISSING'));continue
            fs=[dict(RGB=cv2.cvtColor(cv2.imread(rows[i]['RGB_path']),cv2.COLOR_BGR2RGB),labels=cv2.imread(rows[i]['Mask_path'],0),K=route.K,c2w_mm=poses[i],raw_frame=rows[i]['raw_frame']) for i in [t['reference']]+t['sources']]
            c=dict(t,reference_id=rows[t['reference']]['id'],source_ids=[rows[i]['id'] for i in t['sources']],scope='B_NO_GT_FIXED_TUPLE',input_sha256=tuple_identity(fs,meta['raw_sha256'],route.MODEL_SHA))
            valid.append(c)
        for d in ['inputs','predictions','metrics','raw','meshes','v5raw/inputs']:(dest/d).mkdir(parents=True,exist_ok=True)
        for p,target in [(dest/'scripts',route.V6/'scripts'),(dest/'v5raw/scripts',route.V5/'scripts')]:
            if not p.exists():p.symlink_to(target,target_is_directory=True)
        shutil.copy2(HIST/'HIST'/case/'config.json',dest/'config.json');save(dest/'inputs/ledger005.json',rows)
        np.savez_compressed(dest/'predictions/local005_camera_0.npz',**cam)
        save(dest/'predictions/local005_primary.json',dict(primary_version=0));save(dest/'inputs/MVS_supported_cases.json',valid)
        save(dest/'PLAN_FROZEN.json',dict(camera_sha256=sha(camera),normalization_sha256=sha(root/'NORMALIZATION_FROZEN.json'),tuples=valid,skipped=skipped,model_sha256=route.MODEL_SHA,epoch=time.time(),settings=dict(size=[352,640],sources=3,refine=1,FP16=True,fast_cost_volume=False)))
        if not valid:
            save(dest/'RESULT.json',dict(status='NOT_EVALUABLE',reason='NO_COMPLETE_FIXED_TUPLE',skipped=skipped));continue
        lock_path=W/'runs/shared_gpu.lock';lock_path.parent.mkdir(exist_ok=True)
        if respect_A:
            from .expansion import active_priority_jobs
            jobs=active_priority_jobs()
            if jobs:
                save(dest/'RESULT.json',dict(status='NOT_EXECUTED_GPU_BUSY',reason='ACTIVE_A_SCHEDULER_PRIORITY',jobs=jobs,planned=valid,skipped=skipped));continue
        with lock_path.open('a+') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                save(dest/'RESULT.json',dict(status='NOT_EXECUTED_GPU_BUSY',reason='shared_gpu.lock held; A priority',planned=valid,skipped=skipped));continue
            busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
            busy=other_gpu_processes(busy,os.getpid())
            if busy:
                save(dest/'RESULT.json',dict(status='NOT_EXECUTED_GPU_BUSY',reason=busy,planned=valid,skipped=skipped));continue
            m,mods=kernels(dest,meta);mods['v6'].freeze('supported_view_selection',[dest/'inputs/MVS_supported_cases.json'])
            import run_mvs005_supported as native
            native.R=dest;native.V5=dest/'v5raw'
            def start(c):
                receipt=BASE/'INFERENCE_STARTS.jsonl'
                with receipt.open('a+') as f:
                    fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);old=[json.loads(x) for x in f if x.strip()]
                    assert limit in [8,40] and len(old)<limit,'AUTHORIZED_INFERENCE_BUDGET_EXHAUSTED'
                    assert not any(x['case']==case and x['arm']==arm and x['tag']==c['tag'] for x in old),'NO_SILENT_RETRY'
                    # Recheck all four image/mask hashes at inference boundary.
                    for i in [c['reference']]+c['sources']:
                        assert sha(rows[i]['RGB_path'])==rows[i]['RGB_SHA256'];assert sha(rows[i]['Mask_path'])==rows[i]['Mask_SHA256']
                    rec=dict(case=case,arm=arm,tag=c['tag'],input_sha256=c['input_sha256'],epoch=time.time(),code_commit=route.head(),source_sha256=sha(__file__),ordinal=len(old)+1,gpu_lock=str(lock_path))
                    f.write(json.dumps(rec)+'\n');f.flush();os.fsync(f.fileno())
            tree,adapter=m.adapt_supported_hero_schedule(route.V6/'scripts/run_mvs005_supported.py')
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
            native.__dict__['_M2F10_TUPLE_RECEIPT']=start
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(route.V6/'scripts/run_mvs005_supported.py'),'exec'),native.__dict__)
            native.main()
            import torch
            gc.collect();torch.cuda.empty_cache()
            results=read(dest/'metrics/MVS005_supported_runs.json')
            for c in valid:
                raw=dest/'raw'/(c['tag']+'.npz')
                if not raw.exists():continue
                z=np.load(raw)['depth_mm'];i=c['reference'];full=cv2.resize(z.astype(float),(640,360),interpolation=cv2.INTER_LINEAR)
                mesh=mods['v6'].depth_mesh(full,cv2.imread(rows[i]['Mask_path'],0)==1,poses[i],mods['v6'].image(rows[i]))
                mesh.export(dest/'meshes'/(c['tag']+'_Polyp.ply'))
            save(dest/'RESULT.json',dict(status='COMPLETED',runs=results,skipped=skipped,adapter=adapter,outputs={str(p):sha(p) for p in list((dest/'raw').glob('*.npz'))+list((dest/'meshes').glob('*.ply'))}))
            print('HERO',case,arm,sum(r['success'] for r in results),flush=True)
    evaluate_depth(case)


def evaluate_depth(case):
    root=BASE/case;common=verify_common(case);meta=read(common/'meta.json');_,mods=kernels(root/'R',meta)
    tuples=read(common/'TUPLES_FROZEN.json')['tuples'];loaded={};records=[]
    for arm in ['R','S']:
        for t in tuples:
            p=root/arm/'hero/raw'/(t['tag']+'.npz')
            if p.exists():loaded[(arm,t['tag'])]=np.load(p)
    for source in tuples:
        for target in tuples:
            if source==target:continue
            if any((a,t['tag']) not in loaded for a in ['R','S'] for t in [source,target]):
                records.append(dict(source=source['tag'],target=target['tag'],status='NOT_EVALUABLE',reason='MISSING_PAIRED_NATIVE_OUTPUT'));continue
            arrays={};polyp=None
            for arm in ['R','S']:
                a,b=loaded[(arm,source['tag'])],loaded[(arm,target['tag'])]
                z=a['depth_mm'];lab=cv2.resize(cv2.imread(meta['frames'][source['reference']]['Mask_path'],0),(z.shape[1],z.shape[0]),interpolation=cv2.INTER_NEAREST)
                ok=(lab==1)&np.isfinite(z)&(z>0);y,x=np.nonzero(ok)
                points=mods['v6'].unproject(z[ok],a['c2w'][source['reference']],np.c_[x,y],a['K_index_native'])
                uv,d=mods['v6'].project(points,b['c2w'][target['reference']],b['K_index_native'])
                arrays[arm+'_projected']=zbuffer(uv,d,b['depth_mm'].shape);arrays[arm+'_target']=b['depth_mm']
                polyp=cv2.resize(cv2.imread(meta['frames'][target['reference']]['Mask_path'],0),(b['depth_mm'].shape[1],b['depth_mm'].shape[0]),interpolation=cv2.INTER_NEAREST)==1
            result,masks=paired_depth(arrays['R_projected'],arrays['R_target'],arrays['S_projected'],arrays['S_target'],polyp)
            result.update(source=source['tag'],target=target['tag'],source_raw=source['raw_target'],target_raw=target['raw_target'],status='EVALUABLE' if result['all_common']['pixels'] else 'NOT_EVALUABLE',visibility='nearest forward-splatted source depth; possible target occlusion separately reported; raw unfiltered depth',no_error_feedback=True)
            out=root/'depth'/f'{source["tag"]}_to_{target["tag"]}.npz';out.parent.mkdir(exist_ok=True)
            np.savez_compressed(out,**arrays,**masks,polyp=polyp);result['arrays_path']=str(out);records.append(result)
    save(root/'HERO_DEPTH_RESULTS.json',records)
