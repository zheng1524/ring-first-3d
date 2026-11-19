"""Exact frozen INIT segmentation on new RGB only; no geometry change."""
from context import *
import types,importlib

def main():
 checkfreeze('provenance/DISCOVERY_FROZEN.json');vs=load(N/'config/RAW_CAMERA_CANDIDATES.json');todo=[v for v in vs if v['Mask_pending']];start=time.time();modelroot=Path('/home/liu/polyp_research/experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model');src=DXY/'src/dxy_mid/segmentation.py';snapshot_read([src,modelroot/'model.safetensors'],'SEGMENTATION_IMPLEMENTATION.json')
 if todo:
  mod=types.ModuleType('dxy_mid');mod.__path__=[str(DXY/'src/dxy_mid')];sys.modules.setdefault('dxy_mid',mod);seg=importlib.import_module('dxy_mid.segmentation').INITSegmentation(modelroot,'cuda')
 for i,v in enumerate(todo):
  try:
   dst=Path(v['Mask_source']);lab=np.asarray(Image.open(dst))if dst.exists()else seg.predict(v['RGB_source']);assert lab.shape==(360,640)and set(np.unique(lab))<={0,1,2};Image.fromarray(lab).save(dst);rgb=np.asarray(Image.open(v['RGB_source']).convert('RGB'));np.savez_compressed(v['cache'],RGB=rgb,labels=lab,K=v['K']);v.update(Mask_pending=False,Mask_SHA256=sha(dst),polyp_pixels=int((lab==1).sum()),ring_pixels=int((lab==2).sum()),segmentation_status='FROZEN_INIT_NATIVE_MULTICLASS',segmentation_model_SHA256='981aa596e8906edc4457219581c606d4a5a22bfc6f7e4924d3d9a4b9aff64464')
  except Exception as e:v.update(segmentation_status='FAILED',failure=repr(e));print('SEGMENT_FAIL',v['id'],repr(e),flush=True)
  if i%20==0:print('SEGMENT',i,'/',len(todo),flush=True)
 save('config/SEGMENTED_CANDIDATES.json',vs);save('metrics/SEGMENTATION_RUNTIME.json',dict(new_masks=len(todo),seconds=time.time()-start,original_masks_changed=0));freeze('provenance/SEGMENTED_INPUTS_FROZEN.json',[N/'config/SEGMENTED_CANDIDATES.json',Path(__file__)],GT=False);print('SEGMENTATION_DONE',len(vs),time.time()-start,flush=True)
if __name__=='__main__':main()
