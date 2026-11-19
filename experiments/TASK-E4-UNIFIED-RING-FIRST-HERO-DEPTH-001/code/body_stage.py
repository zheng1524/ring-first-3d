"""Minimal loss/IO adapter to the existing 36-step graph/sweep optimizer."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,difflib,json,time,traceback
import numpy as np
import torch
import yaml
import pipeline as p
from ring_first_3d.mainline.paths import activate,LINEAGE
from ring_first_3d.mainline.native.io import sha256,save_json
from ring_first_3d.synthetic.raster import ray_map
T=p.TASK;OUT=T/'runs/RF_ONLY_V1';SD=activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
from common import INITIALIZE
from body_hooks import historical_depth,mesh

def setup(group):
    source=next(c for c in p.cases() if c['case']==group);video='004';folder=OUT/group/video/'body';folder.mkdir(parents=True,exist_ok=True)
    fit=[v for v in p.read(T/'audit/SELECTED_VIEWS.json') if v['meta']['case']==group and v['meta']['video']==video and v['meta']['role']=='FIT']
    assert len(fit)==8
    ring=dict(np.load(source['static']['RING.npz']['path']));initial=INITIALIZE(source['initial']['path'],ring,ring);views=[];depthroot=folder/'DEPTH_INPUT';depthroot.mkdir(exist_ok=True)
    for v in fit:
        m=v['meta'];cid=m['id'];admission=OUT/group/video/'camera'/cid/'ADMISSION.json';assert p.read(admission)['status']=='PASS'
        a=p.check_input(v);C=np.array(p.read(admission.parent/'CAMERA_RESULT.json')['c2w_mm']);views.append(dict(id=cid,video=video,role='FIT',direction_block=m.get('direction_block',0),K=a['K'],C=C,labels=a['labels'],RGB=a['RGB']))
        hero=OUT/group/video/'hero'/cid;assert p.read(hero/'ADMISSION.json')['status']=='PASS'
        d=dict(np.load(hero/'HERO_native.npz'));raw=dict(np.load(hero/'RAW_NATIVE_MESH.npz'));uv=raw['uv'].astype(np.int64);z=d['depth_mm'][uv[:,1],uv[:,0]];K=d['K_index_native']
        cad=ray_map(ring['V'],ring['F'],K,C,(352,640))['z'];cad_z=cad[uv[:,1],uv[:,0]]
        f=depthroot/'hero_fit'/cid;f.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(f/'OBS_TRUSTED.npz',uv=uv,z=z,K=K,T=C,weight=np.ones(len(uv)),cad_z=cad_z,native_shape=[352,640])
        hs=p.read(hero/'SOURCE.json');parent=[]
        for name in hs['frames'][1:]:
            ref=next(x for x in fit if x['meta']['id']==name);parent.append(dict(path=ref['meta']['RGB_source'],sha256=sha256(ref['meta']['RGB_source'])))
        save_json(f/'SOURCE.json',dict(parent_RGB=parent,new_HERO=str(hero),new_HERO_SHA256=sha256(hero/'HERO_native.npz'),filter='all finite positive native Polyp pixels; no historic depth; fixed weight 1; existing 018 first-hit/Ring rejection'))
    norm=p.read(source['static']['NORMALIZATION.json']['path']);chart=p.read(source['static']['CHART.json']['path']);base=p.read(source['static']['BASE_SELECTION.json']['path'])
    cfg=yaml.safe_load((SD.parent/'TASK.yaml').read_text())['structured']['update']
    case=SimpleNamespace(name=group+'_004',V=initial['V'],center=np.array(norm['center']),scale=norm['scale_mm'],fit=[v['meta']['id'] for v in fit],views={v['meta']['id']:dict(meta=v['meta']) for v in fit})
    return source,folder,initial,views,ring,base,chart,cfg,case,depthroot

def main(group,arm,mode):
    source,folder,initial,views,ring,base,chart,cfg,case,depthroot=setup(group)
    target=folder/arm
    if mode=='train':assert not target.exists(),'No overwrite; use frozen outputs for resume'
    diag=folder/('CONTRACT_'+arm);diag.mkdir(exist_ok=True)
    depth=historical_depth(case,chart,depthroot,diag)
    V=torch.tensor(initial['V'],dtype=torch.float64,device='cuda',requires_grad=True)
    h,info,data=depth.term(mesh(V,initial['F'],case),case.fit[0],True);h.backward();gradient=V.grad.detach().cpu().numpy()
    save_json(diag/'DEPTH_GRADIENT_CONTRACT.json',dict(loss=float(h.detach()),gradient_finite=bool(np.isfinite(gradient).all()),gradient_norm=float(np.linalg.norm(gradient)),depth_info=info,axial_Z=True,actual_initial_mesh=source['initial'],GT_read=False))
    np.savez_compressed(diag/'DEPTH_CORRESPONDENCE.npz',**data,vertex_gradient=gradient)
    assert np.isfinite(gradient).all() and np.linalg.norm(gradient)>0,'DEPTH_NO_GRADIENT'
    if mode=='contract':print('CONTRACT_PASS',group,arm,info,flush=True);return
    def depth_loss(V,body):
        if arm=='B1':return V.sum()*0
        value=V.sum()*0
        for cid in case.fit:
            loss,_,_=depth.term(mesh(V,body['F'],case),cid)
            value=value+.01*depth.w[cid]*loss
        return value
    original=(SD/'optimizer.py').read_text();adapted=original.replace('from ring_collision_gate import RingCollisionGate','from body_hooks import RingGateAdapter as RingCollisionGate')
    token="+cfg['lambda_attachment']*attach\n";assert adapted.count(token)==1
    adapted=adapted.replace(token,"+cfg['lambda_attachment']*attach+depth_loss(V,body)\n")
    adapted=adapted.replace('HERO_read=False','HERO_read=DEPTH_ENABLED')
    adapted=adapted.replace("energies={k:float(v.detach())for k,v in parts.items()}","energies={k:float(v.detach())for k,v in parts.items()},HERO_depth=float(depth_loss(V,body).detach())")
    (diag/'optimizer_adapter.py').write_text(adapted)
    (diag/'ADAPTER.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),adapted.splitlines(True),fromfile='frozen002/optimizer.py',tofile='task_adapter/optimizer.py')))
    save_json(diag/'RUN_FREEZE.json',dict(arm=arm,group=group,video='004',original_optimizer_sha256=sha256(SD/'optimizer.py'),adapter_sha256=sha256(diag/'optimizer_adapter.py'),adapter_diff_sha256=sha256(diag/'ADAPTER.diff'),configuration=cfg,initial=source['initial'],normalization=source['static']['NORMALIZATION.json'],views=[dict(id=v['id'],C=v['C'],K=v['K']) for v in views],depth_enabled=arm=='B2',depth_lambda=.01,depth_sigma_mm=.5,GT_used=False,growth_scope='Unchanged 002 evidence requires >=2 videos; per-video fitting therefore cannot invent eligible growth. Boolean never activated without eligible growth; history preserved.'))
    ns=dict(__name__='task_optimizer_adapter',__file__=str(diag/'optimizer_adapter.py'),depth_loss=depth_loss,DEPTH_ENABLED=arm=='B2');exec(compile(adapted,str(diag/'optimizer_adapter.py'),'exec'),ns)
    try:
        final=ns['train'](initial,views,ring,base,chart,cfg,target,'DEFORM_SWEEP')
        save_json(target/'TASK_PREDICTION_FROZEN.json',dict(status='PASS',arm=arm,mesh='FINAL.npz',sha256=sha256(target/'FINAL.npz'),GT_read=False,source_freeze=str(diag/'RUN_FREEZE.json'),vertex_displacement_MAE_mm=float(np.linalg.norm(final['V'][:len(initial['V'])]-initial['V'],axis=1).mean()),vertex_displacement_p95_mm=float(np.percentile(np.linalg.norm(final['V'][:len(initial['V'])]-initial['V'],axis=1),95))))
    except Exception:
        target.mkdir(parents=True,exist_ok=True);save_json(target/'FAILURE.json',dict(status='FAIL',error=traceback.format_exc(),GT_read=False));print(traceback.format_exc(),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('group',choices=['G01','G03','G05','G06']);ap.add_argument('arm',choices=['B1','B2']);ap.add_argument('--mode',choices=['contract','train'],default='contract');a=ap.parse_args();main(a.group,a.arm,a.mode)
