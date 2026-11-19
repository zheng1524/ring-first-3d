"""Reuse the mature G01 upstream: Ring + RGB local calibration -> RGB map.

All solvers below are extracted unchanged from hash-locked existing sources.
Only the IO namespace and the selected eight FIT images are adapted.
"""
from pathlib import Path
import ast,traceback,shutil,time
import numpy as np
import cv2
from scipy.optimize import least_squares,minimize_scalar
from scipy.sparse import lil_matrix
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
import pipeline as p
from banks import builder_namespace
from ring_first_3d.mainline.native.camera import recover,observe,residual,torus_contours,RF_CONFIG
from ring_first_3d.mainline.native.geometry import project
from ring_first_3d.mainline.native.io import save_json,sha256
F=p.TASK/'code/frozen_calibration'

def extract(file,names,ns):
    nodes=[n for n in ast.parse(file.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names),(file,names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(file),'exec'),ns)

def stats(x):
    a=np.asarray(x);a=a[np.isfinite(a)]
    return dict(N=len(a),MAE=float(abs(a).mean()) if len(a) else None,p95=float(np.percentile(abs(a),95)) if len(a) else None,maximum=float(abs(a).max()) if len(a) else None)

def namespace(root,fit):
    cfg=p.read(F/'config.json');K=np.array(fit[0]['meta']['K']);assert np.array_equal(K,np.array(cfg['K']))
    original_anchor=fit[4]['meta']['id'];ordered=sorted(fit,key=lambda v:(v['meta']['raw_frame'],v['meta']['id']))
    ledger=[dict(id=v['meta']['id'],raw_frame=v['meta']['raw_frame'],RGB_path=v['meta']['RGB_source'],Mask_path=v['meta']['Mask_source']) for v in ordered]
    arrays={v['meta']['id']:p.check_input(v) for v in fit}
    ns=dict(np=np,cv2=cv2,Rotation=Rotation,least_squares=least_squares,minimize_scalar=minimize_scalar,lil_matrix=lil_matrix,cKDTree=cKDTree,K=K,R=root,project=project,stats=stats,cfg=lambda:cfg,ledger=lambda:ledger,image=lambda a:arrays[a['id']]['RGB'],labels=lambda a:arrays[a['id']]['labels'],save=lambda path,value:save_json(root/path,value),load=lambda path:p.read(root/path),obs=lambda cid:dict(np.load(root/'observations'/(cid+'_ring.npz'))),ring_residual=lambda C,ob,part='train',K0=K:residual(C,ob,K0))
    def freeze(name,files):save_json(root/'metrics'/('freeze_'+name+'.json'),dict(files=[p.asset(q) for q in files],GT_or_HERO_or_old_camera_read=False))
    def verify(name):
        if name=='ring_inputs':return
        for r in p.read(root/'metrics'/('freeze_'+name+'.json'))['files']:assert sha256(r['path'])==r['sha256']
    ns.update(freeze=freeze,verify=verify)
    extract(F/'background_registration.py',['skew','fundamental','epi','vec','pose'],ns)
    extract(F/'v6_common.py',['positive_gauge','spin','unit','triangle'],ns)
    extract(F/'local_ring_sfm.py',['pair_data','canonical_reference','initialize','triangulate_training','BA'],ns)
    extract(F/'track005.py',['main'],ns);ns['__file__']=str(F/'track005.py')
    return ns,ordered,next(i for i,v in enumerate(ordered) if v['meta']['id']==original_anchor)

def build_one(g,video):
    p.verify();cv2.setNumThreads(1)
    for r in p.read(p.TASK/'audit/MATURE_CALIBRATION_SOURCE_LOCK.json')['files']:assert sha256(r['copy'])==r['sha256']
    base=p.OUT/g/video;previous=base/'bank/ADMISSION.json'
    if previous.exists() and p.read(previous)['status']=='PASS':return
    history=p.TASK/'runs/BEFORE_REF_BUILD_REV1'/g/video
    if base.exists() and not history.exists():history.parent.mkdir(parents=True,exist_ok=True);base.rename(history)
    root=base/'reference_build/REV1';root.mkdir(parents=True,exist_ok=True)
    if (base/'bank/ADMISSION.json').exists():return
    fit=[v for v in p.instance_views(g,video) if v['meta']['role']=='FIT'];assert len(fit)==8
    save_json(root/'INPUT_FREEZE.json',dict(inputs=[v['cache'] for v in fit],IDs=[v['meta']['id'] for v in fit],roles=['FIT']*8,old_camera_used=False,GT_used=False,HERO_used=False,protocol=p.asset(p.TASK/'PROTOCOL_REF_BUILD_REV1.yaml'),RF_CONFIG=RF_CONFIG,source_lock=p.asset(p.TASK/'audit/MATURE_CALIBRATION_SOURCE_LOCK.json')))
    try:
        for folder in ['observations','predictions','metrics','scripts']:(root/folder).mkdir(exist_ok=True)
        shutil.copyfile(F/'v6_common.py',root/'scripts/v6_common.py');shutil.copyfile(F/'config.json',root/'config.json')
        ns,ordered,ref=namespace(root,fit);rings=[]
        for v in ordered:
            cid=v['meta']['id'];a=p.check_input(v);ob=observe(a['labels']);np.savez_compressed(root/'observations'/(cid+'_ring.npz'),**ob)
            raw=recover(a['labels'],a['K'],rgb_geometry=None,initial_pose=None);save_json(root/'predictions'/(cid+'_RING_ONLY.json'),raw);candidates=[]
            for alt in raw['ring_alternatives']:
                Q=np.array(alt['Q']);C=np.eye(4);C[:3,:3]=Q.T;C[:3,3]=-Q.T@np.array(alt['center']);candidates.append(dict(alt,c2r=C))
            rings.append(dict(id=cid,candidates=candidates));print('BOOTSTRAP_RING',g,video,cid,len(candidates),flush=True)
        save_json(root/'predictions/RING_CANDIDATES.json',rings)
        ns['main']();tr=dict(np.load(root/'observations/tracks005.npz'));pack=dict(np.load(root/'observations/pairs005.npz'));edges=ns['pair_data'](tr,pack);results=[];poses={}
        for version in range(ns['cfg']()['pose_initializations']):
            start=time.monotonic()
            try:
                ini,info=ns['initialize'](rings,tr,edges,ref,version);X,tids,support=ns['triangulate_training'](ini,tr);cur,P,ba=ns['BA'](ini,X,tids,support,tr,ref)
                np.savez_compressed(root/'predictions'/f'NATIVE_CALIBRATION_{version}.npz',c2w=cur,K=ns['K'],points=P,track_ids=tids,reference=ref,ids=[v['meta']['id'] for v in ordered]);poses[version]=cur
                results.append(dict(version=version,status='PASS',initialization=info,local_BA=ba,seconds=time.monotonic()-start));print('BOOTSTRAP_LOCAL_CALIBRATION',g,video,version,'PASS',len(P),flush=True)
            except Exception:results.append(dict(version=version,status='FAIL',error=traceback.format_exc(),seconds=time.monotonic()-start));print('BOOTSTRAP_LOCAL_CALIBRATION',g,video,version,'FAIL',results[-1]['error'],flush=True)
            save_json(root/'metrics/LOCAL_CALIBRATION_RUNS.json',results)
        assert poses,'NO_CONNECTED_NATIVE_RING_RGB_CALIBRATION'
        primary=min(poses);cur=poses[primary];rows=[];diagnostic=[];held=set(p.read(p.TASK/'audit/INPUT_FREEZE.json')['files'][0].get('unused',[]))
        target_held={v['meta']['RGB_content_sha'] for v in p.views() if v['meta']['role']!='FIT'}
        for i,v in enumerate(ordered):
            a=p.check_input(v);assert p.arraysha(a['RGB']) not in target_held;path=root/'inputs'/(v['meta']['id']+'.npz');path.parent.mkdir(exist_ok=True);np.savez_compressed(path,RGB=a['RGB'],labels=a['labels'],K=a['K'],T=cur[i]);q=observe(a['labels'])['q_train'];d=cKDTree(torus_contours(cur[i],a['K']).reshape(-1,2)).query(q)[0]
            rows.append(dict(v['meta'],T=cur[i],cache=str(path),RGB_SHA256=sha256(v['meta']['RGB_source'])));diagnostic.append(dict(id=v['meta']['id'],Ring_MAE_px=float(d.mean()),Ring_P95_px=float(np.percentile(d,95)),center_spread_mm=max(float(np.linalg.norm(cur[i,:3,3]-other[i,:3,3])) for other in poses.values())))
        save_json(root/'metrics/CALIBRATION_RING_DIAGNOSTIC.json',dict(primary_initialization=primary,selection='original lowest successful initialization version; no GT/HOLDOUT feedback',views=diagnostic,qualification='Conditional reference calibration, not final camera/Pose GT'))
        builder=builder_namespace(root/'map_builder',rows);data=builder['landmarks']([v['id'] for v in rows],'MAP');N=len(data['X']);assert N>=6,'INSUFFICIENT_FIT_TRIANGULATED_LANDMARKS'
        bank=root/'map_builder/landmarks/MAP.npz';obs=root/'map_builder/landmarks/MAP_OBSERVATIONS.json';assert all(o['view'] in {v['id'] for v in rows} for r in p.read(obs) for o in r['observations'])
        save_json(base/'bank/ADMISSION.json',dict(status='PASS',execution='MATURE_G01_NATIVE_REFERENCE_BUILD_REV1',method='UNCHANGED_RING_RGB_LOCAL_SFM_THEN_FEATURES019',bank=str(bank),sha256=sha256(bank),points=N,observations=p.asset(obs),reference_RGB=[dict(id=v['id'],RGB_source=v['RGB_source'],sha256=v['RGB_SHA256'],pixel_sha256=p.arraysha(p.check_input(next(q for q in fit if q['meta']['id']==v['id']))['RGB']),role='FIT',video=video) for v in rows],primary=primary,calibration_evidence=str(root/'metrics/LOCAL_CALIBRATION_RUNS.json'),protocol=p.asset(p.TASK/'PROTOCOL_REF_BUILD_REV1.yaml'),reasons=[],conditional_calibration_not_camera_GT=True,GT_or_HERO_or_old_camera_read=False))
        print('BOOTSTRAP_BANK_PASS',g,video,N,flush=True)
    except Exception:
        err=traceback.format_exc();save_json(base/'bank/ADMISSION.json',dict(status='FAIL',execution='MATURE_G01_NATIVE_REFERENCE_BUILD_REV1',reasons=['MATURE_NATIVE_REFERENCE_BUILD_FAILED'],error=err,evidence=str(root),protocol=p.asset(p.TASK/'PROTOCOL_REF_BUILD_REV1.yaml')));print('BOOTSTRAP_BANK_FAIL',g,video,err,flush=True)

def main():
    for g in p.GROUPS:
        for video in ['004','005']:
            if p.inherited(g,video):continue
            ad=p.OUT/g/video/'bank/ADMISSION.json'
            if ad.exists() and p.read(ad)['status']=='PASS':continue
            build_one(g,video)

if __name__=='__main__':main()
