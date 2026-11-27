"""Two immutable stage caches; science identity excludes storage paths and commits."""
import contextlib,fcntl,hashlib,json,os,shutil,time
from pathlib import Path
import numpy as np
from .full_run import atomic_json,read,hash_file

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def content_identity(path):
 p=Path(path)
 if p.suffix=='.npz':
  result={}
  with np.load(p,allow_pickle=False) as arrays:
   for name in sorted(arrays.files):
    a=np.asarray(arrays[name]);h=hashlib.sha256()
    if np.issubdtype(a.dtype,np.floating):
     h.update(np.isnan(a).tobytes());a=a.copy();a[np.isnan(a)]=0
    h.update(np.ascontiguousarray(a).tobytes());result[name]=dict(shape=list(a.shape),dtype=a.dtype.str,values=h.hexdigest())
  return digest(result)
 if p.suffix=='.json':return digest(read(p))
 return hash_file(p)

def cache_identity(science,payload,files):
 return digest(dict(science=science,payload=payload,files={k:v['content_id'] for k,v in files.items() if k!='PROVENANCE.json'}))

def ensure(root,science,builder):
 """Builder writes immutable relative payloads; completion is committed last."""
 root=Path(root);root.parent.mkdir(parents=True,exist_ok=True)
 with root.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);status='CACHE_MISS';receipt=root/'COMPLETE.json'
  if root.exists():
   try:
    old=read(receipt)
    if old['science']!=science:status='STALE'
    else:
     for name,x in old['files'].items():
      p=root/name
      assert p.resolve().is_relative_to(root.resolve()),'INVALID_CACHE_PATH'
      assert hash_file(p)==x['sha256'] and content_identity(p)==x['content_id'],'CACHE_FILE_CORRUPT'
     assert old['content_id']==cache_identity(science,old['payload'],old['files']),'CACHE_RECEIPT_CORRUPT'
     print('CACHE_HIT',root,flush=True);return old
   except (OSError,ValueError,KeyError,AssertionError):status='CORRUPT'
   os.replace(root,root.with_name(root.name+'.'+status+'.'+str(time.time_ns())))
  print(status,root,flush=True);tmp=root.with_name(root.name+'.building.'+str(time.time_ns()));tmp.mkdir()
  payload=builder(tmp)
  files={str(p.relative_to(tmp)):dict(sha256=hash_file(p),content_id=content_identity(p),bytes=p.stat().st_size) for p in sorted(tmp.rglob('*')) if p.is_file()}
  identity=cache_identity(science,payload,files)
  result=dict(science=science,payload=payload,files=files,content_id=identity,build_status=status,created_epoch=time.time())
  os.replace(tmp,root);atomic_json(root/'COMPLETE.json',result);return result

def link_or_copy(source,dest):
 source=Path(source);dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():
  assert hash_file(dest)==hash_file(source),'DESTINATION_DRIFT';return
 if source.suffix=='.json':shutil.copyfile(source,dest);return
 try:os.link(source,dest)
 except OSError:shutil.copyfile(source,dest)

def config(r):return r.FULL_CONFIG.get('cache',{}) if r.FULL_CONFIG else {}

def prep_science(r,raw_hash):
 import inspect
 return dict(stage='RAW-selection-INIT-v1',raw_sha256=raw_hash,K=r.K.tolist(),functions={fn:hashlib.sha256(inspect.getsource(getattr(r,fn)).encode()).hexdigest() for fn in ['build_raw_preprocessing','historical_extra','frame_indices']},files={str(p.relative_to(r.INIT_PATH)):hash_file(p) for p in r.INIT_PATH.rglob('*') if p.is_file()},segmentation=hash_file('/home/liu/new-polyp-dxy/src/dxy_mid/segmentation.py'),selection=hash_file(r.V6/'scripts/setup_audit.py'))

def ensure_prepared(r,case,runroot,raw,raw_hash,signature):
 import copy,cv2
 cfg=config(r);root=Path(cfg['root'])/'prepared'/case;science=prep_science(r,raw_hash)
 def build(tmp):
  oldroot=cfg.get('legacy_import_root') if cfg.get('allow_legacy_reads',False) else None
  meta=None
  if oldroot:
   state=Path(oldroot)/'states'/(case+'.json')
   if state.exists():
    source=Path(read(state)['run_path'])/'inputs/INPUT_IDENTITY.json';candidate=read(source)
    try:
     assert candidate['raw_sha256']==raw_hash and np.array_equal(candidate['K'],r.K)
     assert candidate['original16']==r.frame_indices(candidate['frame_count'])
     assert candidate['selection_source_sha256']==science['selection']
     assert all(hash_file(p)==h for p,h in candidate['INIT_files'].items())
     assert sorted(x['raw_frame'] for x in candidate['frames'])==sorted(set(candidate['original16']+candidate['selected_extra']))
     # Legacy provenance must point at a frozen prepare signature, not a handwritten compatibility flag.
     protocol=Path(oldroot)/'protocols'/('prepare_'+candidate['protocol_signature']+'.json')
     if not protocol.exists():
      protocol=Path('/home/liu/ring_first_3d_workspace/runs/v6_raw_to_hero_001/protocols')/protocol.name
     desc=read(protocol);assert desc['stage']=='prepare' and desc['K']==r.K.tolist()
     assert desc['entry_functions']==cfg['legacy_prepare_functions'],'LEGACY_PREPARE_CODE_MISMATCH'
     for row in candidate['frames']:
      for key in ['RGB','Mask']:
       assert hash_file(row[key+'_path'])==row[key+'_SHA256']
     meta=candidate;atomic_json(tmp/'PROVENANCE.json',dict(mode='legacy_import',source=str(source),sha256=hash_file(source),protocol=str(protocol),protocol_sha256=hash_file(protocol),execution_commit=r.head()))
    except (AssertionError,OSError,KeyError,ValueError) as ex:print('LEGACY_PREPROCESS_REJECTED',case,repr(ex),flush=True)
  if meta is not None:
   for row in meta['frames']:
    for key in ['RGB','Mask']:link_or_copy(row[key+'_path'],tmp/Path(row[key+'_path']).name)
  if meta is None:
   meta=r.build_raw_preprocessing(case,tmp,raw,raw_hash,signature)
   atomic_json(tmp/'PROVENANCE.json',dict(mode='RAW_COLD_BUILD',raw_sha256=raw_hash,execution_commit=r.head()))
  # A completion receipt/provenance is not part of scientific normalized content.
  for name in ['PREPARED.json','SELECTION.json']:
   if (tmp/name).exists():(tmp/name).unlink()
  meta={k:copy.deepcopy(meta[k]) for k in ['case','raw_path','raw_sha256','frame_count','frames','original16','selected_extra','K','ring_inner_mm','INIT_files','selection_source_sha256']}
  framekeys=['id','source','source_id','raw_frame','time_sec','native_BGR_sha256','RGB_path','Mask_path','RGB_SHA256','Mask_SHA256','K','original16','exact_sequential_identity']
  meta['frames']=[{k:a[k] for k in framekeys} for a in meta['frames']]
  for row in meta['frames']:
   for key in ['RGB','Mask']:row[key+'_path']=Path(row[key+'_path']).name
  atomic_json(tmp/'METADATA.json',meta);return dict(case=case,raw_sha256=raw_hash)
 receipt=ensure(root,science,build);meta=read(root/'METADATA.json')
 for i,row in enumerate(meta['frames']):
  for key in ['RGB','Mask']:row[key+'_path']=str(root/row[key+'_path'])
  rgb=cv2.imread(row['RGB_path']);assert rgb is not None
  row.update(view_id=case+':raw:'+str(row['raw_frame']),physical_view_id=hashlib.sha256(rgb.tobytes()).hexdigest(),media_type='video',video_id=case,original_index=i,video_raw_frame=row['raw_frame'],working_shape=[360,640],coordinate_system=case)
 meta.update(protocol_signature=signature,execution_commit=r.head(),preprocessing_reuse=dict(source=str(root/'COMPLETE.json'),content_id=receipt['content_id'],original_execution_commit='see cache PROVENANCE.json',selection_and_INIT_semantics_unchanged=True),preprocessing_content_id=receipt['content_id'],original_video_frames=copy.deepcopy(meta['frames']),original_video_target_count=len(meta['frames'])-1)
 r.save(runroot/'PREPARED.json',meta);return meta

def ensure_matching(r,R,meta,mods):
 from .frontend_kernels import RECEIPTS
 from .frontend_policy import match_partners
 import inspect
 cfg=config(r);root=Path(cfg['root'])/'matching'/meta['case'];names=['observations/tracks005.npz','observations/pairs005.npz','metrics/track005.json'];configuration=r.read(R/'config.json')
 science=dict(stage='full-original-video-pool-tracking-v1',preprocessing=meta['preprocessing_content_id'],views=[dict(id=a['id'],raw_frame=a['raw_frame'],RGB=a['RGB_SHA256'],Mask=a['Mask_SHA256']) for a in meta['frames']],config=configuration,kernels={n:hash_file(r.V6/'scripts'/n) for n in ['track005.py','v6_common.py']})
 science['adapted_tracking_ast']=RECEIPTS[mods['track'].__name__+'.main']['adapted_ast_sha256']
 science['match_partners']=hashlib.sha256(inspect.getsource(match_partners).encode()).hexdigest()
 science['numpy_version']=np.__version__
 def build(tmp):
  oldroot=cfg.get('legacy_import_root') if cfg.get('allow_legacy_reads',False) else None;source=None
  if oldroot:
   state=Path(oldroot)/'states'/(meta['case']+'.json')
   if state.exists():
    old=Path(read(state)['run_path'])
    try:
     oldmeta=r.read(old/'inputs/INPUT_IDENTITY.json');assert [a['id'] for a in oldmeta['frames']]==[a['id'] for a in meta['frames']]
     assert all(a['RGB_SHA256']==b['RGB_SHA256'] and a['Mask_SHA256']==b['Mask_SHA256'] for a,b in zip(oldmeta['frames'],meta['frames']))
     assert r.read(old/'config.json')==configuration
     assert all(match_partners(i,meta['frames'],configuration['pair_offsets'])==[i+k for k in configuration['pair_offsets'] if i+k<len(meta['frames'])] for i in range(len(meta['frames'])))
     for frozen in ['tracking_protocol','tracks']:
      for p,h in r.read(old/'metrics'/('freeze_'+frozen+'.json'))['files'].items():assert hash_file(p)==h
     for n in science['kernels']:assert hash_file(old/'scripts'/n)==science['kernels'][n]
     with np.load(old/names[0]) as a:assert list(a['ids'])==[x['id'] for x in meta['frames']] and a['xy'].shape[1]==len(meta['frames'])
     source=old
    except (AssertionError,OSError,KeyError,ValueError) as ex:print('LEGACY_TRACK_REJECTED',meta['case'],repr(ex),flush=True)
  if source is None:mods['track'].main();source=R
  for name in names:link_or_copy(source/name,tmp/name)
  atomic_json(tmp/'PROVENANCE.json',dict(source=str(source),mode='legacy_import' if source!=R else 'SIFT_COLD_BUILD',execution_commit=r.head()))
  print('MATCH_CACHE_BUILT',meta['case'],'legacy_import' if source!=R else 'SIFT_COLD_BUILD',flush=True)
  return dict(views=[a['id'] for a in meta['frames']],full_pool=True)
 receipt=ensure(root,science,build)
 with np.load(root/names[0]) as arrays:
  assert list(arrays['ids'])==[a['id'] for a in meta['frames']] and arrays['xy'].shape[1]==len(meta['frames']),'FULL_POOL_MATCH_IDENTITY'
 for name in names:link_or_copy(root/name,R/name)
 mods['v6'].freeze('tracking_protocol',[r.V6/'scripts/track005.py',r.V6/'scripts/v6_common.py',R/'config.json'])
 mods['v6'].freeze('tracks',[R/name for name in names])
 r.save(R/'MATCH_CACHE.json',dict(cache=str(root),content_id=receipt['content_id'],full_pool=True,view_order=receipt['payload']['views']))
 return receipt
