"""At most four official pretrained forwards on two audited frames."""
from pathlib import Path
import sys,os,time,traceback,json,gc
R=Path(__file__).resolve().parents[1];os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['MPLCONFIGDIR']=str(R/'runtime/mpl');os.environ['HF_HUB_OFFLINE']='1';os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
sys.path[:0]=[str(R/'runtime/python'),str(R/'runtime/map-anything')]
from audit import load,save,sha,normal,vis,OLD
import numpy as np,cv2,torch
from PIL import Image
from mapanything.models import MapAnything
from mapanything.utils.image import preprocess_inputs

def main():
 supplement='--m3-only'in sys.argv
 result_file='MAP_M3_SUPPLEMENT_RESULT.json'if supplement else'MAP_RUN_RESULT.json'
 assert not(R/'provenance'/result_file).exists(),'bounded run already attempted'
 q=load(R/'config/map_minimal.json');recovery=R/'provenance/MAP_DOWNLOAD_RECOVERY_RESULT.json';download=load(recovery if recovery.exists() else R/'provenance/MAP_DOWNLOAD_RESULT.json');assert download['success']
 rows=[];start=time.monotonic();meta=dict(arm='M',scene=q['scene'],GT_used=False,CPU_fallback=False,rows=rows)
 try:
  assert torch.cuda.is_available();torch.set_num_threads(2);torch.manual_seed(20261030)
  refs=load(R/'provenance/INPUT_ELIGIBILITY.json')['references'];sources=[];files=[]
  for cid in q['input_ids']:
   c=next(c for c in refs if c['id']==cid);p=np.load(c['pack']);im=np.asarray(Image.open(c['RGB']).convert('RGB'));mask=np.asarray(Image.open(c['Mask']));pose=p['pose'].copy();pose[:3,3]/=1000
   sources.append(dict(c=c,im=im,mask=mask,K=p['K'].copy().astype(np.float32),pose_m=pose.astype(np.float32),depth_m=(p['depth_mm']/1000).astype(np.float32)))
   files +=[Path(c[k])for k in ['RGB','Mask','pack']]
  dinopath=OLD/'surface_benchmark_v1/vendor/dinov2';assert(dinopath/'hubconf.py').exists()
  save('provenance/'+('MAP_M3_BEFORE_FORWARD_FREEZE.json'if supplement else'MAP_BEFORE_FORWARD_FREEZE.json'),dict(files=[dict(path=str(p),sha256=sha(p))for p in files+[R/'code/map_run.py',R/'config/map_minimal.json',R/'runtime/map_checkpoint/model.safetensors',R/'runtime/map_checkpoint/config.json']],official_commit=q['official_code_commit'],checkpoint_revision=q['checkpoint_revision'],targets_excluded=q['targets_excluded'],inputs=q['input_ids'],DINO_source=[dict(path=str(p),sha256=sha(p))for p in sorted(dinopath.rglob('*.py'))],GT_ACCESS='DENY'))
  # Official DINO code already frozen with HERO; no extra foundation weights.
  original_hub=torch.hub.load
  def localhub(repo,name,*args,**kw):
   if repo=='facebookresearch/dinov2':
    assert kw.get('pretrained')is False,'forbid extra weight download';kw.pop('force_reload',None);return original_hub(str(dinopath),name,*args,source='local',**kw)
   raise RuntimeError('unexpected hub model '+str(repo))
  torch.hub.load=localhub;original_dtype=torch.get_default_dtype();torch.set_default_dtype(torch.bfloat16)
  try:model=MapAnything.from_pretrained(str(R/'runtime/map_checkpoint'),local_files_only=True)
  finally:torch.set_default_dtype(original_dtype);torch.hub.load=original_hub
  from safetensors import safe_open
  with safe_open(str(R/'runtime/map_checkpoint/model.safetensors'),framework='pt',device='cpu')as f:keys=set(f.keys())
  aliases={}
  for name,param in model.named_parameters(remove_duplicate=False):aliases.setdefault(id(param),[]).append(name)
  missing=[names for names in aliases.values()if not any(k in keys for k in names)];assert not missing,missing
  # Official safetensors stores shared DPT modules under dense_head aliases.
  # Check actual loaded values rather than rejecting their alternate names.
  named=dict(model.named_parameters(remove_duplicate=False))
  with safe_open(str(R/'runtime/map_checkpoint/model.safetensors'),framework='pt',device='cpu')as f:
   for names in aliases.values():
    key=next(k for k in names if k in keys)
    assert torch.equal(named[key].detach().reshape(-1)[:1].cpu(),f.get_tensor(key).reshape(-1)[:1].to(named[key].dtype)),key
  # Official forward disables AMP in geometric encoders and prediction heads.
  # Keep these FP32; only the two large transformer trunks use BF16 storage.
  for name,child in model.named_children():
   if name not in ['encoder','info_sharing']:child.float()
  with safe_open(str(R/'runtime/map_checkpoint/model.safetensors'),framework='pt',device='cpu')as f:
   named=dict(model.named_parameters(remove_duplicate=False))
   for names in aliases.values():
    key=next(k for k in names if k in keys)
    if named[key].dtype==torch.float32:named[key].data.copy_(f.get_tensor(key))
  model=model.to(device='cuda').eval()
  def fp32_boundary(x):
   if torch.is_tensor(x):return x.float()if x.is_floating_point()else x
   if isinstance(x,list):return [fp32_boundary(v)for v in x]
   if isinstance(x,tuple):return tuple(fp32_boundary(v)for v in x)
   if isinstance(x,dict):return {k:fp32_boundary(v)for k,v in x.items()}
   return x
  # Dtype-only adapters at the two official AMP-disabled method boundaries.
  # No attention, geometry conditioning, renderer or learned weight is replaced.
  original_geometry=model._encode_and_fuse_optional_geometric_inputs
  original_heads=model.downstream_head
  model._encode_and_fuse_optional_geometric_inputs=lambda views,features:original_geometry(views,fp32_boundary(features))
  model.downstream_head=lambda *args,**kwargs:original_heads(*fp32_boundary(args),**fp32_boundary(kwargs))
  meta.update(parameters=sum(p.numel()for p in model.parameters()),load_seconds=time.monotonic()-start,all_learned_parameter_keys_present=True,storage_precision='BF16 encoder/info_sharing; FP32 official AMP-disabled geometry/heads; FP32 boundary casts',FP32_parameters=sum(p.numel()for p in model.parameters()if p.dtype==torch.float32))
  for mode in (['M3']if supplement else q['modes']):
   rec=dict(mode=mode,status='RUNNING',source_ids=q['input_ids'],model_forward_attempted=False,GT_used=False);begin=time.monotonic()
   try:
    raw=[];mask_data=[]
    for i,s in enumerate(sources):
     v=dict(img=s['im'])
     if mode!='M0':v['intrinsics']=s['K'].copy()
     if mode in ['M2','M3']:v.update(camera_poses=s['pose_m'].copy(),is_metric_scale=torch.tensor([True]))
     if mode=='M3':v['depth_z']=s['depth_m'].copy()
     raw.append(v)
    views=preprocess_inputs(raw,resize_mode=q['resize_mode'],size=tuple(q['size_width_height']),verbose=True)
    # Same official geometric preprocessing determines the exact label warp.
    for s,v in zip(sources,views):
     helper=preprocess_inputs([dict(img=s['im'],intrinsics=s['K'].copy())],resize_mode=q['resize_mode'],size=tuple(q['size_width_height']))[0]
     k=helper['intrinsics'][0].numpy();T=k@np.linalg.inv(s['K']);h,w=v['img'].shape[-2:];labels=cv2.warpAffine(s['mask'],T[:2],(w,h),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0);mask_data.append(dict(labels=labels,T=T,K=k))
    torch.cuda.reset_peak_memory_stats();rec['model_forward_attempted']=True
    with torch.inference_mode():pred=model.infer(views,memory_efficient_inference=True,minibatch_size=1,use_amp=True,amp_dtype='bf16',apply_mask=True,mask_edges=True,apply_confidence_mask=False,use_multiview_confidence=False)
    torch.cuda.synchronize();rec['forward_seconds']=time.monotonic()-begin;rec['peak_GPU_allocated_bytes']=torch.cuda.max_memory_allocated();rec['peak_GPU_reserved_bytes']=torch.cuda.max_memory_reserved()
    arrays=[]
    for a in pred:arrays.append({k:v.float().cpu().numpy()for k,v in a.items()if torch.is_tensor(v)})
    first=arrays[0]['camera_poses'][0].astype(float);anchor=sources[0]['pose_m'].astype(float);gauge=anchor@np.linalg.inv(first);folder=R/'local_results/map'/mode;folder.mkdir(parents=True,exist_ok=True);stats=[];PP=[];CC=[];FF=[];offset=0
    for i,(a,s,md)in enumerate(zip(arrays,sources,mask_data)):
     mandatory=['pts3d','depth_z','camera_poses','conf','mask'];assert all(k in a for k in mandatory),a.keys()
     np.savez_compressed(folder/f'view{i}_official_outputs.npz',**a,source_RGB_SHA256=s['c']['files']['RGB']['sha256'],source_Mask=md['labels'],pixel_transform=md['T'],K_preprocessed=md['K'])
     P=a['pts3d'][0];h,w=P.shape[:2];valid=np.isfinite(P).all(-1)&(a['depth_z'][0,...,0]>0)&(a['mask'][0,...,0]>.5)&(md['labels']==1);ids=np.flatnonzero(valid);world=(P.reshape(-1,3)@gauge[:3,:3].T+gauge[:3,3])*1000;C=a['img_no_norm'][0].reshape(-1,3);PP.append(world[ids]);CC.append(C[ids]);grid=np.full((h,w),-1,int);grid.ravel()[ids]=np.arange(len(ids))+offset;offset+=len(ids)
     for tri in [np.stack([grid[:-1,:-1],grid[:-1,1:],grid[1:,:-1]],-1),np.stack([grid[:-1,1:],grid[1:,1:],grid[1:,:-1]],-1)]:
      t=tri.reshape(-1,3);FF.append(t[(t>=0).all(1)])
     stats.append(dict(view=i,shape=list(P.shape),valid_Polyp_points=len(ids),source_Polyp_pixels=int((md['labels']==1).sum()),output_conf_min=float(np.nanmin(a['conf'])),output_conf_max=float(np.nanmax(a['conf'])),depth_z_min_m=float(np.nanmin(a['depth_z'])),depth_z_max_m=float(np.nanmax(a['depth_z'])),output_camera_pose=a['camera_poses'][0].tolist(),input_pose_m=s['pose_m'].tolist(),input_K_preprocessed=md['K'].tolist(),pixel_transform=md['T'].tolist(),all_mandatory_finite=all(np.isfinite(a[k]).all()for k in mandatory)))
    P=np.concatenate(PP);C=np.concatenate(CC);F=np.concatenate(FF);assert len(P)>0 and np.isfinite(P).all()
    np.savez_compressed(folder/'surface.npz',XYZ_mm=P,RGB=C,faces=F,source_input_ids=q['input_ids'],evaluation_gauge_to_frozen_first_camera=gauge,unit='mm',observed_support_definition='predicted valid Polyp pixels from actual input views; not independent geometry certification')
    rec.update(status='SMOKE_PASS_UNCERTIFIED_GEOMETRY',points=len(P),faces=len(F),views=stats,output=str(folder/'surface.npz'),output_SHA256=sha(folder/'surface.npz'),gauge=gauge)
    del pred,arrays;gc.collect();torch.cuda.empty_cache()
   except Exception:
    rec.update(status='FAILED',error=traceback.format_exc());print(rec['error'],flush=True)
   rec['seconds']=time.monotonic()-begin;rows.append(rec);save('provenance/'+('MAP_M3_PROGRESS.json'if supplement else'MAP_PROGRESS.json'),dict(meta,rows=rows));print('MAP_RESULT',mode,rec['status'],rec.get('points'),rec['seconds'],flush=True)
   if rec['status']=='FAILED':break # stop this GPU branch on first runtime fault
  meta['status']='COMPLETED_BOUNDED_FORWARD_TESTS'
 except Exception:meta.update(status='FAILED_BEFORE_FORWARD',error=traceback.format_exc());print(meta['error'],flush=True)
 meta['seconds']=time.monotonic()-start;save('provenance/'+result_file,meta)
if __name__=='__main__':main()
