"""Retain official auxiliary masks through bitwise-verified repeated inference.

No auxiliary output is fed back into any already frozen Body prediction.
"""
from pathlib import Path
import os,sys,tempfile,shutil,time
import numpy as np
import pipeline as p
from ring_first_3d.mainline.native.io import sha256,save_json
T=p.TASK;R=p.ROOT;O=T/'runs/RF_ONLY_V1'

def main():
    assert p.read(O/'PREDICTIONS_FROZEN_BEFORE_GT.json')['all_training_complete']
    rt=p.read(R/'mainline/configs/SITE.local.json');sys.path[:0]=rt['readonly_dependency_paths'];runtime=O/'HERO_runtime'
    for key in ['HF_HOME','HF_MODULES_CACHE','TORCH_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']:os.environ[key]=str(runtime/key)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    from ring_first_3d.mainline.native.hero import load_official,infer
    torch.set_num_threads(2);torch.manual_seed(20261115);model,receipt=load_official(rt['mvs_root'],rt['checkpoint'],rt['dino_root'],p.read(R/'src/ring_first_3d/mainline/native/upstream_source_lock.json'))
    class Capture:
        def preprocess_and_run(self,**kwargs):self.last=model.preprocess_and_run(**kwargs);return self.last
    cap=Capture();lookup={v['meta']['id']:v for v in p.read(T/'audit/SELECTED_VIEWS.json')};rows=[]
    save_json(O/'HERO_AUX_CAPTURE_PROTOCOL.json',dict(source_sha256=sha256(Path(__file__)),scope='same 32 frozen target/support tuples; auxiliary output retention only',GT_read=False,Body_predictions_frozen=True,bitwise_tolerance_source=str(R/'mainline/configs/REPLAY_TOLERANCES.json'),tolerance='BITWISE',new_predictions_or_parameter_selection=False))
    for target in p.read(O/'HERO_TARGETS_FROZEN.json')['targets']:
        group,video=target['group'],target['video'];frames=[];cid=target['ids'][0];original=O/group/video/'hero'/cid;aux=O/group/video/'hero_auxiliary'/cid;aux.mkdir(parents=True,exist_ok=False)
        for name in target['ids']:
            v=lookup[name];a=p.check_input(v);C=np.array(p.read(O/group/video/'camera'/name/'CAMERA_RESULT.json')['c2w_mm']);frames.append(dict(id=name,RGB=a['RGB'],labels=a['labels'],K=a['K'],c2w_mm=C))
        with tempfile.TemporaryDirectory(prefix='hero_aux_',dir='/dev/shm') as tmp:
            rec=infer(cap,frames,Path(tmp));repeat=np.load(Path(tmp)/'HERO_native.npz')['depth_mm'];first=np.load(original/'HERO_native.npz')['depth_mm'];equal=np.array_equal(first,repeat)
            if not equal:shutil.copytree(tmp,aux/'REPEAT_DIFFERENCE')
            arrays={k:a.detach().float().cpu().numpy() for k,a in cap.last.items() if hasattr(a,'detach')}
            np.savez_compressed(aux/'OFFICIAL_AUXILIARY.npz',**arrays)
            labels=np.load(original/'NATIVE_RGB_LABELS.npz')['labels'];masked=arrays['depth_masked']*1000;model_valid=np.isfinite(masked)&(masked>0);original_polyp=labels==1;bad=int((original_polyp&~model_valid).sum());np.savez_compressed(aux/'MODEL_DEPTH_VALIDITY.npz',valid=model_valid)
            row=dict(group=group,video=video,id=cid,repeat_bitwise_equal=equal,max_abs_depth_difference_mm=float(abs(first-repeat).max()),Polyp_pixels=int(original_polyp.sum()),model_invalid_Polyp_pixels=bad,raw_depth_shape=list(first.shape),sky_output_is_model_logit_not_calibrated_confidence=True,source_original=str(original),new_Body_training_input=False,seconds=rec['seconds'])
            rows.append(row);save_json(aux/'RECEIPT.json',row);print('HERO_AUX',cid,'bitwise',equal,'invalid_Polyp',bad,flush=True)
    p.table(T/'metrics/HERO_AUXILIARY_AUDIT.csv',rows);save_json(O/'HERO_AUXILIARY_COMPLETE.json',dict(status='PASS' if all(r['repeat_bitwise_equal'] and r['model_invalid_Polyp_pixels']==0 for r in rows) else 'PARTIAL',unique_targets=32,additional_repeat_inferences=len(rows),model_receipt=receipt,rows=rows,GT_read=False,Body_predictions_unchanged=True))

if __name__=='__main__':main()
