"""Fresh official inference, target + three frozen same-video FIT supports."""
from pathlib import Path
import os,sys,time,traceback
import numpy as np
import pipeline as p
from ring_first_3d.mainline.native.io import save_json,sha256
T=p.TASK;R=p.ROOT;OUT=T/'runs/RF_ONLY_V1'

def main():
    rt=p.read(R/'mainline/configs/SITE.local.json');sys.path[:0]=rt['readonly_dependency_paths']
    runtime=OUT/'HERO_runtime';runtime.mkdir(exist_ok=True)
    for key in ['HF_HOME','HF_MODULES_CACHE','TORCH_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']:os.environ[key]=str(runtime/key)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    from ring_first_3d.mainline.native.hero import load_official,infer
    torch.set_num_threads(2);torch.manual_seed(20261115)
    assert torch.cuda.is_available()
    targets=[];views=p.read(T/'audit/SELECTED_VIEWS.json')
    for group in p.GROUPS:
        for video in ['004','005']:
            fit=[v for v in views if v['meta']['case']==group and v['meta']['video']==video and v['meta']['role']=='FIT']
            for i,v in enumerate(fit):
                selected=[fit[(i+k)%len(fit)] for k in [0,2,4,6]]
                if len({q['meta']['id'] for q in selected})!=4:continue
                admission=[OUT/group/video/'camera'/q['meta']['id']/'ADMISSION.json' for q in selected]
                if not all(a.exists() and p.read(a)['status']=='PASS' for a in admission):continue
                targets.append(dict(group=group,video=video,selected=selected,admissions=admission))
    save_json(OUT/'HERO_TARGETS_FROZEN.json',dict(protocol=str(T/'PROTOCOL_RF_ONLY.yaml'),protocol_sha256=sha256(T/'PROTOCOL_RF_ONLY.yaml'),targets=[dict(group=r['group'],video=r['video'],ids=[v['meta']['id'] for v in r['selected']],camera_admissions=[dict(path=str(a),sha256=sha256(a)) for a in r['admissions']]) for r in targets],GT_read=False))
    assert len(targets)<=32
    if not targets:return
    model,receipt=load_official(rt['mvs_root'],rt['checkpoint'],rt['dino_root'],p.read(R/'src/ring_first_3d/mainline/native/upstream_source_lock.json'))
    save_json(OUT/'HERO_MODEL_RECEIPT.json',receipt)
    class Capture:
        def preprocess_and_run(self,**kwargs):
            result=model.preprocess_and_run(**kwargs);self.last=result;return result
    capture=Capture();deadline=time.monotonic()+3600
    for target in targets:
        assert time.monotonic()<deadline,'HERO_BUDGET'
        group,video=target['group'],target['video'];m=target['selected'][0]['meta'];out=OUT/group/video/'hero'/m['id']
        if (out/'ADMISSION.json').exists():continue
        pending=out.with_name(out.name+'.pending');pending.mkdir(parents=True,exist_ok=False)
        try:
            frames=[]
            for v in target['selected']:
                a=p.check_input(v);cid=v['meta']['id'];cam=OUT/group/video/'camera'/cid/'CAMERA_RESULT.json';r=p.read(cam)
                frames.append(dict(id=cid,RGB=a['RGB'],labels=a['labels'],K=a['K'],c2w_mm=np.array(r['c2w_mm'])))
            rec=infer(capture,frames,pending)
            dep=np.load(pending/'HERO_native.npz')['depth_mm'];valid=np.isfinite(dep)&(dep>0)
            np.savez_compressed(pending/'DEPTH_VALIDITY.npz',valid=valid,definition='finite positive raw axial Z; not absolute depth accuracy')
            keys={k:dict(type=type(a).__name__,shape=list(a.shape) if hasattr(a,'shape') else None) for k,a in capture.last.items()}
            for k,a in capture.last.items():
                if ('conf' in k.lower()) and hasattr(a,'detach'):
                    np.savez_compressed(pending/('MODEL_'+k+'.npz'),values=a.float().detach().cpu().numpy())
            save_json(pending/'MODEL_OUTPUT_KEYS.json',keys)
            native=dict(np.load(pending/'RAW_NATIVE_MESH.npz'));np.savez_compressed(pending/'Raw_XYZ.npz',XYZ_mm=native['V'],uv=native['uv'],native_pixel_id=native['native_pixel_id'])
            save_json(pending/'SOURCE.json',dict(target=m['id'],group=group,video=video,frames=[v['meta']['id'] for v in target['selected']],input_caches=[v['cache'] for v in target['selected']],camera_results=[dict(path=str(OUT/group/video/'camera'/v['meta']['id']/'CAMERA_RESULT.json'),sha256=sha256(OUT/group/video/'camera'/v['meta']['id']/'CAMERA_RESULT.json')) for v in target['selected']],model_receipt=str(OUT/'HERO_MODEL_RECEIPT.json'),depth_convention='axial_Z_mm',GT_used=False,confidence_available=any('conf' in k.lower() for k in keys),historical_depth_fallback=False))
            assert len(native['F'])>0 and len(native['V'])>0
            save_json(pending/'ADMISSION.json',dict(status='PASS',valid_pixels=int(valid.sum()),polyp_vertices=len(native['V']),faces=len(native['F']),source='SOURCE.json',inference='INFERENCE.json',source_SHA256=sha256(pending/'SOURCE.json')))
            pending.rename(out);print(group,video,m['id'],'HERO_PASS',rec['seconds'],flush=True)
        except Exception:
            error=traceback.format_exc();save_json(pending/'ADMISSION.json',dict(status='FAIL',error=error));pending.rename(out);print(group,video,m['id'],'HERO_FAIL',error,flush=True)
        torch.cuda.empty_cache()

if __name__=='__main__':main()
