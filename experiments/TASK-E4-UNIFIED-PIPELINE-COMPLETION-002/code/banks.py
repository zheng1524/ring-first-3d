"""Unchanged historical map builder; explicit restoration of archived coordinates."""
from pathlib import Path
import ast,itertools,time,traceback
import numpy as np
import cv2
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import pipeline as p
from inputs import BUILDER
from ring_first_3d.mainline.native.io import save_json,sha256

def restore_native(X,H):
    H=np.asarray(H,float);assert np.allclose(H[3],[0,0,0,1]) and np.allclose(H[:3,:3].T@H[:3,:3],np.eye(3),atol=1e-7) and np.linalg.det(H[:3,:3])>.999999
    native=(np.asarray(X)-H[:3,3])@H[:3,:3]
    assert np.max(abs(native@H[:3,:3].T+H[:3,3]-X))<1e-5
    return native

def builder_namespace(root,views):
    root.mkdir(parents=True,exist_ok=True)
    ns=dict(np=np,cv2=cv2,itertools=itertools,least_squares=least_squares,R=root,VIEWS={v['id']:v for v in views},save=lambda path,value:save_json(root/path,value),table=lambda path,rows:p.table(root/path,rows))
    names=['features','match_desc','matches','project','fundamental','sampson','landmarks']
    nodes=[n for n in ast.parse(BUILDER.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(BUILDER),'exec'),ns)
    return ns

def build(group=None,video=None):
    p.verify();cv2.setNumThreads(1)
    for c in p.read(p.TASK/'audit/CALIBRATION_INPUTS.json'):
        g,vi=c['group'],c['video']
        if group and g!=group or video and vi!=video:continue
        out=p.OUT/g/vi/'bank';out.mkdir(parents=True,exist_ok=True)
        if (out/'ADMISSION.json').exists():continue
        if p.inherited(g,vi):
            old=next(b for b in p.read(p.OLD/'runs/RF_ONLY_V1/BANK_ADMISSION.json') if b['group']==g and b['video']==vi)
            save_json(out/'ADMISSION.json',dict(status='PASS',execution='FROZEN_REFERENCE',bank=old['path'],sha256=old['sha256'],evidence=p.asset(p.OLD/'runs/RF_ONLY_V1/BANK_ADMISSION.json'),views=c['views'],reasons=[]));continue
        try:
            recipe=c['archive_recipe'];root=out/'build';root.mkdir(exist_ok=True)
            if recipe:
                for r in [recipe['map'],recipe['observations'],recipe['stored_H']]:assert sha256(r['path'])==r['sha256']
                old=dict(np.load(recipe['map']['path']));obs=p.read(recipe['observations']['path']);ids={v['id'] for v in c['views']}
                keep=[i for i,row in enumerate(obs) if all(o['view'] in ids for o in row['observations'])]
                H=np.array(p.read(recipe['stored_H']['path'])['T']);X=restore_native(old['X'],H)
                data={k:v[keep] if v.ndim and len(v)==len(obs) else v for k,v in old.items()};data['X']=X[keep];data['original_archive_landmark_id']=np.array(keep)
                np.savez_compressed(root/'MAP.npz',**data);save_json(root/'OBSERVATIONS.json',[obs[i] for i in keep]);save_json(root/'COORDINATE_RESTORATION.json',dict(recipe=recipe,H=H,H_inverse=np.linalg.inv(H),native_reconstruction_max_abs_mm=float(abs(X@H[:3,:3].T+H[:3,3]-old['X']).max()),input_landmarks=len(obs),kept_landmarks=len(keep),removed_unbound_or_HOLDOUT=len(obs)-len(keep),cross_video_coupling_removed=True,no_new_registration=True))
                method='ORIGINAL_NATIVE_MAP_RESTORED_FROM_RECORDED_H'
            elif len(c['views'])>=3:
                ns=builder_namespace(root,c['views']);data=ns['landmarks']([v['id'] for v in c['views']],'MAP')
                (root/'landmarks/MAP.npz').rename(root/'MAP.npz');(root/'landmarks/MAP_OBSERVATIONS.json').rename(root/'OBSERVATIONS.json');method='UNCHANGED_FEATURES019_MULTIVIEW_TRIANGULATION'
            else:
                save_json(out/'ADMISSION.json',dict(status='FAIL',execution='NEW_AUDIT',reasons=c['missing'] or ['INSUFFICIENT_NATIVE_POSED_FIT_REFERENCES_MIN3'],available_native_posed_FIT=len(c['views']),no_PnP_fallback=True));print('BANK_FAIL',g,vi,flush=True);continue
            bank=root/'MAP.npz';N=len(np.load(bank)['X']);assert N>=6,'INSUFFICIENT_TRIANGULATED_LANDMARKS'
            ids={o['view'] for row in p.read(root/'OBSERVATIONS.json') for o in row['observations']};look={v['id']:v for v in c['views']};assert ids<=look.keys();assert all(look[k]['role']=='FIT' and look[k]['video']==vi for k in ids)
            save_json(out/'ADMISSION.json',dict(status='PASS',execution='NEW_BUILD_OR_RECOVERY',method=method,bank=str(bank),sha256=sha256(bank),observations=p.asset(root/'OBSERVATIONS.json'),builder=p.asset(BUILDER),reference_RGB=[dict(id=k,RGB_source=look[k]['RGB_source'],sha256=look[k]['RGB_SHA256'],pixel_sha256=look[k]['RGB_array_SHA256'],role='FIT',video=vi) for k in sorted(ids)],points=N,reasons=[],conditional_calibration_not_camera_GT=True,GT_or_HERO_read=False));print('BANK_PASS',g,vi,N,flush=True)
        except Exception:
            err=traceback.format_exc();save_json(out/'ADMISSION.json',dict(status='FAIL',reasons=['BANK_BUILD_ERROR'],error=err));print('BANK_ERROR',g,vi,err,flush=True)

if __name__=='__main__':build()
