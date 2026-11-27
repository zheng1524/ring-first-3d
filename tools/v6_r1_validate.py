"""Bounded cold/hot validation; no HERO and no algorithm alternatives."""
import argparse,json,os,sys,time,hashlib
from pathlib import Path
import numpy as np

def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def execute(config,case):
 cfg=read(config);blocked=[];denied=[str(Path(x).resolve()) for x in cfg['cache']['deny_read_roots']]
 def audit(event,args):
  if event in ['open','os.listdir','os.scandir'] and args and isinstance(args[0],(str,bytes,os.PathLike)):
   p=os.path.abspath(os.fsdecode(args[0]))
   if any(p==root or p.startswith(root+os.sep) for root in denied):
    blocked.append(p);raise RuntimeError('LEGACY_OUTPUT_READ_FORBIDDEN '+p)
 sys.addaudithook(audit)
 from ring_first_3d.v6_raw import full_run,stage_cache
 root=Path(cfg['run_root']);start=time.time()
 for stage in ['prepare','camera','schedule']:full_run.worker(Path(config),case,stage)
 cold_finished=time.time();cache_paths=[Path(cfg['cache']['root'])/phase/case for phase in ['prepared','matching']]
 probes=[]
 for cache in cache_paths:
  before=read(cache/'COMPLETE.json')
  def forbidden_builder(tmp):raise RuntimeError('HOT_CACHE_UNEXPECTED_REBUILD')
  after=stage_cache.ensure(cache,before['science'],forbidden_builder)
  assert before['content_id']==after['content_id'];probes.append(dict(path=str(cache),content_id=after['content_id'],cache_hit=True))
 # Same public entry: a verified completed camera/plan resumes without matching or BA.
 from ring_first_3d.v6_raw import route
 calls={'decode':0}
 old_capture=route.cv2.VideoCapture
 def forbidden_decode(*args,**kwargs):calls['decode']+=1;raise RuntimeError('HOT_PATH_REDECODE')
 route.cv2.VideoCapture=forbidden_decode
 try:
  for stage in ['prepare','camera','schedule']:full_run.worker(Path(config),case,stage)
 finally:route.cv2.VideoCapture=old_capture
 save(root/'validation'/(case+'.json'),dict(case=case,status='COLD_AND_HOT_EXECUTED',cold_seconds=cold_finished-start,hot_seconds=time.time()-cold_finished,forbidden_old_read_attempts=blocked,hot_decode_calls=calls['decode'],cache_probes=probes,config_sha256=digest(config),execution_commit=os.environ.get('V6_EXECUTION_COMMIT')))
 print('COLD_HOT_COMPLETE',case,flush=True)

def compare(config,case):
 cfg=read(config);root=Path(cfg['run_root']);R=root/'HIST'/case;old=Path(cfg['comparison_r1_root'])/'HIST'/case
 meta=read(root/'prepared'/case/'PREPARED.json');baseline=read(old/'ORIGINAL_VIEW_POOL.json');checks={}
 keys=['id','raw_frame','time_sec','K','RGB_SHA256','Mask_SHA256','original16','view_id','physical_view_id','media_type','working_shape']
 for k in keys:assert [x[k] for x in meta['frames']]==[x[k] for x in baseline],('FRAME_CONTRACT',k)
 checks['frames_rgb_mask_K_mapping_order']='EXACT'
 arrays=[]
 for name in ['FULL_tracks005.npz','FULL_pairs005.npz','tracks005.npz','pairs005.npz']:
  a=np.load(R/'observations'/name);b=np.load(old/'observations'/name);assert set(a.files)==set(b.files),(case,name,'ARRAY_NAMES')
  for k in a.files:
   assert a[k].dtype==b[k].dtype and a[k].shape==b[k].shape,(name,k,'DTYPE_SHAPE')
   ok=np.array_equal(a[k],b[k],equal_nan=True) if np.issubdtype(a[k].dtype,np.inexact) else np.array_equal(a[k],b[k])
   assert ok,(name,k,'VALUES');arrays.append(name+':'+k)
 checks['full_and_component_tracks_pairs_train_held']=dict(status='EXACT',arrays=len(arrays))
 for name in ['COMPONENT.json','inputs/REFERENCE_RECEIPT.json']:
  a=read(R/name);b=read(old/name);assert a==b,(name,'COMPONENT_REFERENCE_DRIFT')
 checks['anchor_B_component_temporal_edges']='EXACT'
 ca=read(R/'PLAN_FROZEN.json');cb=read(old/'PLAN_FROZEN.json')
 assert ca['selected_version']==cb['selected_version'],'INIT_SELECTION_DRIFT'
 key=lambda c:(c['raw_target'],tuple(c['raw_support']),c['rule_version'])
 assert sorted(map(key,ca['legal']))==sorted(map(key,cb['legal'])),'TARGET_SUPPORT_DRIFT'
 cams=[]
 for p in sorted((R/'predictions').glob('local005_camera_*.npz')):
  a=np.load(p);b=np.load(old/'predictions'/p.name)
  delta=float(np.max(np.abs(a['c2w']-b['c2w'])));exact=np.array_equal(a['c2w'],b['c2w'])
  # Numerical-equivalence tolerance, not a scientific gate or selection threshold.
  assert np.allclose(a['c2w'],b['c2w'],rtol=1e-8,atol=1e-7,equal_nan=True),('CAMERA_NUMERIC_DRIFT',delta)
  cams.append(dict(file=p.name,bitwise_equal=exact,max_abs_delta=delta,rtol=1e-8,atol=1e-7))
 check=read(root/'validation'/(case+'.json'));check.update(status='PASS',checks=checks,cameras=cams,selected_version=ca['selected_version'],legal_targets=len(ca['legal']),baseline_plan_sha256=digest(old/'PLAN_FROZEN.json'),new_plan_sha256=digest(R/'PLAN_FROZEN.json'),tuple_hashes_equal=[c['input_sha256'] for c in ca['legal']]==[c['input_sha256'] for c in cb['legal']],source_ids_preserved=True)
 save(root/'validation'/(case+'.json'),check);print(json.dumps(check,indent=2),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['execute','compare']);ap.add_argument('--config',required=True);ap.add_argument('--case',required=True);a=ap.parse_args();globals()[a.action](a.config,a.case)
