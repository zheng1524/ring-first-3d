"""RAW-only composition. Scientific Ring/SIFT/BA/HERO kernels are called in place."""
import ast,hashlib,importlib.util,inspect,json,os,subprocess,sys,time,traceback,fcntl
from pathlib import Path
import cv2,numpy as np
from .policy import frame_indices,admit_camera,choose_sources,tuple_identity
W=Path('/home/liu/ring_first_3d_workspace');WT=Path(__file__).resolve().parents[3]
TASK='TASK-V6-RAW-TO-HERO-MAINLINE-001';T=WT/'experiments'/TASK;B=W/'runs/v6_raw_to_hero_001'
M10=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F10')
E=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');V6=E/'ring_first_v6_local_reconstruction';V5=E/'ring_first_v5_geometry_crossvideo'
CORE=Path('/home/liu/ring-first-hero-core');MODEL_SHA='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d'
INIT_PATH=Path('/home/liu/polyp_research/experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model')
K=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1.]])
GROUPS=['GP_IIa_14.0mm_closed_R10_single_refY','GP_Ip_12.0mm_closed_R10_single_refY','GP_Ip_20.0mm_closed_R10_single_refY','GP_Ip_8.8mm_closed_R5_single_refY','GP_Is_14.0mm_closed_R5_single_refY']
ALLOWED={g+'_'+v for g in GROUPS for v in ['004','005']}
SIGNATURES={}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  for a in iter(lambda:f.read(1024**2),b''):h.update(a)
 return h.hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v)for v in x]
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float)and not np.isfinite(x):return None
 if isinstance(x,Path):return str(x)
 return x
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False))
def read(p):return json.loads(Path(p).read_text())
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()
def environment():
 sys.dont_write_bytecode=True
 for k in ['HF_HOME','HF_MODULES_CACHE','TORCH_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']:os.environ[k]=str(B/'runtime'/k)
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 rt=read(CORE/'site_config.local.json');sys.path[:0]=rt['readonly_dependency_paths']+[str(W/'src'),str(M10),'/home/liu/new-polyp-dxy/src']
def protocol_signature(stage):
 if stage in SIGNATURES:return SIGNATURES[stage]
 names={'prepare':['prepare','historical_extra','frame_indices'],'camera':['cameras','bind'],'schedule':['schedule','admit_camera','choose_sources','tuple_identity'],'hero':['hero','inference_start','tuple_identity']}[stage]
 files=[V6/'scripts/setup_audit.py',Path('/home/liu/new-polyp-dxy/src/dxy_mid/segmentation.py')]+[p for p in INIT_PATH.rglob('*')if p.is_file()]
 if stage!='prepare':
  files += [M10/'tools/m2f8_v6_general.py',M10/'tools/run_w0_camera.py',V5/'config.json',V6/'config.json']
  files += [V5/'scripts'/n for n in ['g5_common.py','ring_observations.py','ring_candidates_new.py','branch_seed_policy.py']]
  files += [V6/'scripts'/n for n in ['v6_common.py','track005.py','local_ring_sfm.py','validate_select.py','select_supported_views.py','run_mvs005_supported.py','package_surfaces.py']]
 if stage=='hero':
  files += [E/'surface_fusion_v1/scripts/run_mvs_adapter3.py',Path(read(CORE/'site_config.local.json')['checkpoint'])]
 hashes={str(p):sha(p)for p in files}
 if stage=='hero':assert hashes[str(Path(read(CORE/'site_config.local.json')['checkpoint']))]==MODEL_SHA,'OFFICIAL_MODEL_DRIFT'
 payload=dict(stage=stage,entry_functions={n:hashlib.sha256(inspect.getsource(globals()[n]).encode()).hexdigest()for n in names},files=hashes,K=K.tolist(),model=MODEL_SHA)
 key=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();save(B/'protocols'/(stage+'_'+key+'.json'),payload);SIGNATURES[stage]=key;return key

def inference_start(case,variant,R,c,poses,rows,meta,mods):
 rr=c['reference'];src=c['sources'];fs=[]
 for i in [rr]+src:
  a=rows[i];assert sha(a['RGB_path'])==a['RGB_SHA256']and sha(a['Mask_path'])==a['Mask_SHA256'],'INFERENCE_INPUT_FILE_DRIFT'
  fs.append(dict(RGB=mods['v6'].image(a),labels=mods['v6'].labels(a),K=K,c2w_mm=poses[i],raw_frame=a['raw_frame']))
 assert tuple_identity(fs,meta['raw_sha256'],MODEL_SHA)==c['input_sha256'],'TUPLE_DRIFT'
 path=B/'INFERENCE_STARTS.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('a+')as f:
  fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);prior=[json.loads(x)for x in f if x.strip()]
  if len(prior)>=273:raise RuntimeError('GLOBAL_INFERENCE_BUDGET_273_EXHAUSTED')
  if any(x['case']==case and x['variant']==variant and x['tag']==c['tag']for x in prior):raise RuntimeError('NO_UNRECEIPTED_RETRY')
  rec=dict(ordinal=len(prior)+1,case=case,variant=variant,tag=c['tag'],input_sha256=c['input_sha256'],epoch=time.time(),execution_commit=head(),resource_retry=0)
  f.write(json.dumps(rec)+'\n');f.flush();os.fsync(f.fileno());fcntl.flock(f,fcntl.LOCK_UN)
 save(R/'inputs'/('TUPLE_'+c['tag']+'.json'),dict(**rec,frames=[dict(raw_frame=a['raw_frame'],RGB_sha256=hashlib.sha256(a['RGB'].tobytes()).hexdigest(),Mask_sha256=hashlib.sha256(a['labels'].tobytes()).hexdigest(),K=a['K'],C=a['c2w_mm'])for a in fs]))

def legacy():
 environment();p=M10/'tools/m2f8_v6_general.py';assert sha(p)=='6ad695b0ffd66699a41306d4d38c1853a5d65b6a372d758a54ce284e7a586412','M2F10_ADAPTER_DRIFT';sp=importlib.util.spec_from_file_location('retained_m2f10',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

def historical_extra(gray,blurs,original):
 """Execute the original V6 appearance selector block, without setup_audit's old assets/writes."""
 source=V6/'scripts/setup_audit.py';tree=ast.parse(source.read_text());nodes=[];active=False
 for node in tree.body:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='original'for t in node.targets):active=True
  if active:
   if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='cap'for t in node.targets):break
   nodes.append(node)
 assert len(nodes)==6,[ast.unparse(n)[:60]for n in nodes]
 ns=dict(np=np,orig=[dict(raw_frame=i)for i in original],allsmall=gray,blurs=blurs,frames=[{}for _ in gray])
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source)+'::original_selection','exec'),ns)
 return ns['selected'],dict(source=str(source),sha256=sha(source),selected=ns['selected'],candidates=[dict(frame=i,score=s,novelty=d)for s,i,d in ns['scores']],min_original_separation_frames=18,min_extra_separation_frames=36,maximum_extra=6)

def prepare(case):
 assert case in ALLOWED,'CASE_NOT_AUTHORIZED'
 environment();sig=protocol_signature('prepare');R=B/'prepared'/case;receipt=R/'PREPARED.json';raw=W/'smart_endoscope_20260805 (1)/raw'/(case+'.mp4');rh=sha(raw)
 if receipt.exists():
  x=read(receipt);assert x['raw_sha256']==rh and x['protocol_signature']==sig,'PREPARED_PROTOCOL_DRIFT'
  for f in x['frames']:
   assert sha(f['RGB_path'])==f['RGB_SHA256']and sha(f['Mask_path'])==f['Mask_SHA256']
  print('REUSE_CURRENT_RAW_CACHE',case,flush=True);return x
 R.mkdir(parents=True,exist_ok=True);cap=cv2.VideoCapture(str(raw));gray=[];blurs=[];pts=[]
 while True:
  ok,im=cap.read()
  if not ok:break
  sm=cv2.resize(im,(160,90),interpolation=cv2.INTER_AREA);g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY);gray.append(g);blurs.append(float(cv2.Laplacian(g,cv2.CV_64F).var()));pts.append(cap.get(cv2.CAP_PROP_POS_MSEC))
 cap.release();probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','json',str(raw)],text=True));pts=[float(x['best_effort_timestamp_time'])for x in probe['frames']];assert len(pts)==len(gray)and np.isfinite(pts).all()and np.all(np.diff(pts)>=0),'PTS_BINDING';original=frame_indices(len(gray));extra,selection=historical_extra(gray,blurs,original);selected=sorted(set(original+extra));assert len(selected)<=22
 save(R/'SELECTION.json',dict(original=original,extra=extra,rule='original V6 novelty to original16 times capped clarity; no depth/pose',**{k:v for k,v in selection.items()if k!='selected'}))
 from dxy_mid.segmentation import INITSegmentation
 import torch
 torch.set_num_threads(4);model=INITSegmentation(str(INIT_PATH),'cuda'if torch.cuda.is_available()else'cpu');rows=[];cap=cv2.VideoCapture(str(raw));i=0
 while True:
  ok,im=cap.read()
  if not ok:break
  if i in selected:
   id=f'raw_{i:06d}';p=R/(id+'.png');q=R/(id+'_mask.png');work=cv2.resize(im,(640,360),interpolation=cv2.INTER_AREA);assert cv2.imwrite(str(p),work);lab=model.predict(str(p));assert lab.shape==(360,640)and np.isin(lab,[0,1,2]).all();assert cv2.imwrite(str(q),lab)
   rows.append(dict(id=id,source=raw.name,source_id=case[-3:],raw_frame=i,time_sec=pts[i],native_BGR_sha256=hashlib.sha256(im.tobytes()).hexdigest(),RGB_path=str(p),Mask_path=str(q),RGB_SHA256=sha(p),Mask_SHA256=sha(q),K=K.tolist(),original16=i in original,exact_sequential_identity=True));print('RAW_INIT',case,i,flush=True)
  i+=1
 cap.release();assert i==len(gray)
 x=dict(protocol_signature=sig,case=case,raw_path=str(raw),raw_sha256=rh,frame_count=i,frames=rows,original16=original,selected_extra=extra,K=K,ring_inner_mm=5 if '_R5_'in case else 10,INIT_files={str(p):sha(p)for p in INIT_PATH.rglob('*')if p.is_file()},execution_commit=head(),selection_source_sha256=sha(V6/'scripts/setup_audit.py'))
 save(receipt,x);return clean(x)

def bind(m,R,meta):
 mods=m.source_modules(3.1 if meta['ring_inner_mm']==5 else 5.6)
 for mod in [mods['v6'],mods['track'],mods['lba']]:mod.R=R;mod.V5=R/'v5raw'
 return mods

def cameras(case,variant):
 m=legacy();meta=prepare(case);sig=protocol_signature('camera');R=B/variant/case
 if(R/'CAMERA_COMPLETE.json').exists():
  receipt=read(R/'CAMERA_COMPLETE.json');assert receipt['input_sha256']==sha(B/'prepared'/case/'PREPARED.json')and receipt['protocol_signature']==sig,'CAMERA_PROTOCOL_DRIFT'
  for p,h in receipt['outputs'].items():assert sha(p)==h
  print('REUSE_CURRENT_CAMERAS',variant,case,flush=True);return R
 assert not(R/'CAMERA_STARTED.json').exists(),'Interrupted camera run needs a new attempt directory, never silent overwrite'
 for d in ['inputs','observations','predictions','metrics','raw','meshes','scenes','visualizations','v5raw/inputs']:(R/d).mkdir(parents=True,exist_ok=True)
 for p,target in [(R/'scripts',V6/'scripts'),(R/'v5raw/scripts',V5/'scripts')]:
  if not p.exists():p.symlink_to(target,target_is_directory=True)
 rows=meta['frames'];save(R/'inputs/ledger005.json',rows);save(R/'inputs/INPUT_IDENTITY.json',meta)
 cfg=read(V6/'config.json');cfg['ring_R_mm']=3.1 if meta['ring_inner_mm']==5 else 5.6;save(R/'config.json',cfg)
 state=dict(protocol_signature=sig,task=TASK,variant=variant,case=case,execution_commit=head(),input_sha256=sha(B/'prepared'/case/'PREPARED.json'),started_epoch=time.time(),stages=[]);save(R/'CAMERA_STARTED.json',state)
 try:
  mods=bind(m,R,meta);rings=m.build_ring(R,rows,cfg['ring_R_mm'],mods);state['stages'].append('current_Ring_observations_candidates');save(R/'RUN_STATE.json',state)
  mods['track'].main();state['stages'].append('current_SIFT_tracks')
  tr=np.load(R/'observations/tracks005.npz');pairs=np.load(R/'observations/pairs005.npz')
  if variant=='HIST':
   ref=next(i for i,r in enumerate(rows)if r['raw_frame']==meta['original16'][8]);held=next(i for i,r in enumerate(rows)if r['raw_frame']==meta['original16'][9]);reference=dict(policy='original V6 16-frame anchor index8 and diagnostic index9 generalized to actual RAW',ref=ref,held=held)
  elif variant=='GRAPH':
   edges=mods['lba'].pair_data(tr,pairs);counts=[len(np.load(R/'observations'/(a['id']+'_ring.npz'))['q_train'])for a in rows];ref,held,reference=m.select_v6_reference(rows,rings,edges,counts)
  else:raise ValueError('UNKNOWN_VARIANT')
  reference.update(reference_index=ref,heldout_index=held,reference_raw=rows[ref]['raw_frame'],diagnostic_raw=rows[held]['raw_frame'],diagnostic_image_used_in_camera_BA=True);save(R/'inputs/REFERENCE_RECEIPT.json',reference)
  m.invoke_adapted_v6(mods['lba'],V6/'scripts/local_ring_sfm.py',ref,held,{'reference':1,'heldout':0});state['stages'].append('current_Ring_RGB_BA')
  import validate_select
  validate_select.R=R;validate_select.V5=R/'v5raw';validate_select.contours=mods['v6'].contours
  m.invoke_adapted_v6(validate_select,V6/'scripts/validate_select.py',ref,held,{'reference':1,'heldout':1});state['stages'].append('original_upstream_validation')
  outputs=[R/'config.json',R/'inputs/ledger005.json',R/'inputs/REFERENCE_RECEIPT.json',R/'metrics/local_validation.json',R/'predictions/local005_primary.json',R/'observations/tracks005.npz',R/'predictions/ring_candidates005.json']+list((R/'predictions').glob('local005_camera_*.npz'))
  state.update(status='COMPLETED',outputs={str(p):sha(p)for p in outputs});save(R/'CAMERA_COMPLETE.json',state)
 except Exception as ex:
  state.update(status='FAILED',error=repr(ex),traceback=traceback.format_exc());save(R/'CAMERA_FAILURE.json',state);raise
 finally:save(R/'RUN_STATE.json',state)
 return R

def schedule(case,variant):
 R=cameras(case,variant);m=legacy();sig=protocol_signature('schedule');meta=read(B/'prepared'/case/'PREPARED.json');rows=meta['frames'];mods=bind(m,R,meta)
 if(R/'PLAN_FROZEN.json').exists():
  oldplan=read(R/'PLAN_FROZEN.json');assert oldplan['protocol_signature']==sig and oldplan['parent_sha256']==sha(R/'CAMERA_COMPLETE.json'),'PLAN_PARENT_DRIFT';assert oldplan['cases_sha256']==sha(R/'inputs/MVS_supported_cases.json'),'PLAN_CASES_DRIFT';return oldplan
 val=read(R/'metrics/local_validation.json');primary=val['primary'];per=next(v['per_frame']for v in val['versions']if v['version']==primary);old=set();new=set();gates=[]
 for i,r in enumerate(per):
  a,b,reasons=admit_camera(r);assert a==(r['status']=='VALIDATED')
  if a:old.add(i)
  if b:new.add(i)
  gates.append(dict(id=rows[i]['id'],raw_frame=rows[i]['raw_frame'],old_pass=a,new_pass=b,reasons=reasons,metrics=r,rule='Q1: center-spread warning only; all other original V6 checks unchanged'))
 save(R/'metrics/GATES.json',gates);refdata=read(R/'inputs/REFERENCE_RECEIPT.json');ref=refdata['reference_index'];held=refdata['heldout_index'];cam=np.load(R/f'predictions/local005_camera_{primary}.npz');poses=cam['c2w'];center=next(x['P_estimate_mm']for x in val['coverage']if x['version']==primary);order=m.diverse_target_order(poses,center,ref,held);cases=[]
 if new-{ref,held}:
  q=json.loads(json.dumps(val))
  for v in q['versions']:
   if v['version']==primary:
    for i,r in enumerate(v['per_frame']):r['status']='VALIDATED'if i in new else'MODEL_PREDICTED'
  original_load=mods['v6'].load
  mods['v6'].load=lambda path:q if path=='metrics/local_validation.json'else original_load(path)
  tree,adapt=m.adapt_all_supported_targets(V6/'scripts/select_supported_views.py',ref,held,order)
  try:exec(compile(tree,str(V6/'scripts/select_supported_views.py'),'exec'),dict(__name__='v6_current_selection',__file__=str(V6/'scripts/select_supported_views.py'),_M2F9_REFERENCE_INDEX=ref,_M2F9_HELDOUT_INDEX=held,_M2F10_TARGET_INDICES=order))
  finally:mods['v6'].load=original_load
  for c in read(R/'inputs/MVS_supported_cases.json'):
   src,original=choose_sources(c['source_diagnostics'],old,new);c.update(sources=src,source_ids=[rows[i]['id']for i in src],old_rule_generated=original,rule_version='Q0'if original else'Q1',target_own_old_pass=c['reference']in old,target_own_new_pass=c['reference']in new,addition_reasons=[]if original else[dict(raw_frame=rows[i]['raw_frame'],reasons=gates[i]['reasons'])for i in src if i not in old]);cases.append(c)
 # Keep all rejected target plans, but inference receives only true 3-source tuples.
 missing={c['reference']for c in cases}
 for i in order:
  if i not in missing:cases.append(dict(reference=i,reference_id=rows[i]['id'],sources=[],source_ids=[],reason='NO_Q1_SUPPORT_POOL',rule_version='Q1',old_rule_generated=False))
 legal=[]
 for c in cases:
  rr=c['reference'];src=c['sources'];c['raw_target']=rows[rr]['raw_frame'];c['raw_support']=[rows[i]['raw_frame']for i in src]
  if len(src)!=3:c['failure_reason']='FEWER_THAN_THREE_UPSTREAM_ADMITTED_SUPPORTS';continue
  fs=[dict(RGB=mods['v6'].image(rows[i]),labels=mods['v6'].labels(rows[i]),K=K,c2w_mm=poses[i],raw_frame=rows[i]['raw_frame'])for i in [rr]+src]
  c['input_sha256']=tuple_identity(fs,meta['raw_sha256'],MODEL_SHA);legal.append(c)
 save(R/'inputs/MVS_supported_cases.json',legal);mods['v6'].freeze('supported_view_selection',[R/'inputs/MVS_supported_cases.json'])
 out=dict(protocol_signature=sig,parent_sha256=sha(R/'CAMERA_COMPLETE.json'),cases_sha256=sha(R/'inputs/MVS_supported_cases.json'),case=case,variant=variant,execution_commit=head(),cameras_sha256=sha(R/f'predictions/local005_camera_{primary}.npz'),input_sha256=sha(B/'prepared'/case/'PREPARED.json'),old_cameras=len(old),new_cameras=len(new),numeric_cameras=len(rows),old_legal_targets=sum(c['old_rule_generated']for c in legal),new_legal_targets=len(legal),budget=len(legal),all_targets=cases,legal=legal,no_depth_in_selection=True,model_sha256=MODEL_SHA)
 assert len(legal)<=21 and len({c['input_sha256']for c in legal})==len(legal);save(R/'PLAN_FROZEN.json',out);print('BUDGET_FROZEN',variant,case,out['old_cameras'],out['new_cameras'],len(legal),flush=True);return out

def hero(case,variant):
 plan=schedule(case,variant);sig=protocol_signature('hero');m=legacy();R=B/variant/case;meta=read(B/'prepared'/case/'PREPARED.json');mods=bind(m,R,meta)
 if(R/'HERO_COMPLETE.json').exists():
  x=read(R/'HERO_COMPLETE.json');assert x['plan_sha256']==sha(R/'PLAN_FROZEN.json')and x['protocol_signature']==sig,'HERO_PROTOCOL_DRIFT'
  for p,h in x['outputs'].items():assert sha(p)==h
  return x
 assert not(R/'HERO_STARTED.json').exists(),'No silent retries; interrupted inference needs an explicit identical-input recovery receipt'
 save(R/'HERO_STARTED.json',dict(execution_commit=head(),plan_sha256=sha(R/'PLAN_FROZEN.json'),new_inference_budget=plan['budget'],epoch=time.time()))
 import run_mvs005_supported
 run_mvs005_supported.R=R;run_mvs005_supported.V5=R/'v5raw'
 if plan['legal']:
  primary=read(R/'predictions/local005_primary.json')['primary_version'];poses=np.load(R/f'predictions/local005_camera_{primary}.npz')['c2w'];assert sha(R/f'predictions/local005_camera_{primary}.npz')==plan['cameras_sha256']
  tree,adapt=m.adapt_supported_hero_schedule(V6/'scripts/run_mvs005_supported.py');node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');run_mvs005_supported.__dict__['_M2F10_TUPLE_RECEIPT']=lambda c:inference_start(case,variant,R,c,poses,meta['frames'],meta,mods);exec(compile(ast.Module(body=[node],type_ignores=[]),str(V6/'scripts/run_mvs005_supported.py'),'exec'),run_mvs005_supported.__dict__);run_mvs005_supported.main()
 else:save(R/'metrics/MVS005_supported_runs.json',[]);mods['v6'].freeze('MVS_supported_raw',[R/'metrics/MVS005_supported_runs.json'])
 # Original package kernel needs an empty preview ledger; all current output is scheduled exactly once.
 save(R/'inputs/MVS_cases.json',[]);save(R/'metrics/MVS005_runs.json',[]);mods['v6'].freeze('MVS_raw',[R/'metrics/MVS005_runs.json'])
 if any(r['success']for r in read(R/'metrics/MVS005_supported_runs.json')):
  import package_surfaces
  package_surfaces.R=R;package_surfaces.V5=R/'v5raw';tree,receipt=m.adapt_independent_package(V6/'scripts/package_surfaces.py');node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');exec(compile(ast.Module(body=[node],type_ignores=[]),str(V6/'scripts/package_surfaces.py'),'exec'),package_surfaces.__dict__);package_surfaces.main();save(R/'inputs/PACKAGE_ADAPTER.json',receipt)
 results=read(R/'metrics/MVS005_supported_runs.json');out=dict(protocol_signature=sig,case=case,variant=variant,execution_commit=head(),plan_sha256=sha(R/'PLAN_FROZEN.json'),budget=plan['budget'],completed=sum(r['success']for r in results),failed=[r for r in results if not r['success']],outputs={str(p):sha(p)for p in list((R/'raw').glob('*.npz'))+list((R/'meshes').glob('*_Polyp.ply'))});save(R/'HERO_COMPLETE.json',out);print('HERO_COMPLETE',variant,case,out['completed'],flush=True);return out

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--variant',choices=['HIST','GRAPH'],default='HIST');ap.add_argument('--stage',choices=['prepare','camera','schedule','hero','all'],default='all');a=ap.parse_args()
 if a.stage=='prepare':prepare(a.case)
 if a.stage in ['camera','all']:cameras(a.case,a.variant)
 if a.stage in ['schedule','all']:schedule(a.case,a.variant)
 if a.stage in ['hero','all']:hero(a.case,a.variant)
