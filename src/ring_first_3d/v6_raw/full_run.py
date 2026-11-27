"""Manifest-driven process orchestration; scientific stages remain in route.py."""
import argparse,contextlib,csv,fcntl,hashlib,html,importlib.util,json,os,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path
W=Path('/home/liu/ring_first_3d_workspace')
BASE=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-RAW-TO-HERO-001')
TASK='TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001'
OLD=W/'runs/v6_raw_to_hero_001'
LOCK=W/'runs/shared_gpu.lock'

def hash_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()

def atomic_json(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp.'+str(os.getpid()))
 with tmp.open('w') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)

def read(p):return json.loads(Path(p).read_text())

def authorize_tuple(plan_path,tag,identity):
 plan=read(plan_path);legal=plan['legal'];assert plan['budget']==len(legal)
 if len({c['input_sha256'] for c in legal})!=len(legal):raise ValueError('DUPLICATE_FROZEN_TUPLE')
 if not any(c['tag']==tag and c['input_sha256']==identity for c in legal):raise ValueError('UNFROZEN_TUPLE')
 return len(legal)

def valid_cached_native(path,record):
 return bool(record.get('success') and Path(path).is_file() and hash_file(path)==record.get('raw_SHA256'))

def coverage(rows):
 groups=sorted({r['group'] for r in rows});out=lambda r:r.get('video_renderable',r.get('renderable',0))>0
 x=dict(groups_total=len(groups),videos_total=len(rows),videos_with_output=sum(out(r) for r in rows),groups_with_output=sum(any(out(r) for r in rows if r['group']==g) for g in groups),groups_two_videos_output=sum(sum(out(r) for r in rows if r['group']==g)>=2 for g in groups),groups_all_videos_output=sum(all(out(r) for r in rows if r['group']==g) for g in groups),target_denominator_known=sum(r.get('selected_targets') or 0 for r in rows),target_denominator_unknown_videos=sum(r.get('selected_targets') is None for r in rows))
 for k in ['renderable','video_renderable','photo_renderable','native_success','legal_targets','q0','q1']:x[k]=sum(r.get(k,0) for r in rows)
 x['status_counts']={s:sum(r.get('status')==s for r in rows) for s in sorted({r.get('status','PENDING') for r in rows})}
 x['origins']={o:dict(videos=sum(r.get('origin')==o for r in rows),native_success=sum(r.get('native_success',0) for r in rows if r.get('origin')==o),renderable=sum(r.get('renderable',0) for r in rows if r.get('origin')==o)) for o in ['REUSED','NEW']}
 return x

def table(path,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r));p=Path(path);tmp=p.with_suffix('.csv.tmp')
 with tmp.open('w') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])
 os.replace(tmp,p)

def inventory(destination):
 D=Path(destination);D.mkdir(parents=True,exist_ok=True);raw=W/'smart_endoscope_20260805 (1)/raw';registry=Path('/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv');registered={r['video']:r['group'] for r in csv.DictReader(registry.open())};files=sorted(raw.glob('*.mp4'));seen={};rows=[];extra=[]
 for p in files:
  h=hash_file(p);group=registered.get(p.name);rec=dict(case=p.stem,group=group,raw_path=str(p),raw_sha256=h,bytes=p.stat().st_size,duplicate_of=seen.get(h),registered=bool(group));seen.setdefault(h,p.stem)
  try:
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,nb_frames,duration,r_frame_rate','-of','json',str(p)],text=True));s=probe['streams'][0];rec.update(s);rec['status']='READY' if group and not rec['duplicate_of'] else 'DUPLICATE' if rec['duplicate_of'] else 'UNSUPPORTED_UNREGISTERED_SEGMENTATION_POOL';rec['ring_inner_mm']=5 if group and '_R5_' in group else 10 if group and '_R10_' in group else None
  except Exception as ex:rec.update(status='MEDIA_PROBE_FAILED',reason=repr(ex))
  (rows if group else extra).append(rec)
 for name,g in registered.items():
  if not(raw/name).exists():rows.append(dict(case=Path(name).stem,group=g,raw_path=str(raw/name),status='MISSING_RAW',reason='frozen39 registered video not found'))
 photo=[dict(path=str(p),bytes=p.stat().st_size,sha256=hash_file(p),use='STATIC_REFERENCE_NOT_VIDEO') for p in sorted(raw.glob('*.jpg'))]
 groups=sorted({r['group'] for r in rows});rec=dict(task=TASK,base_commit='115e41fe5e57deff2898258d2ee836c83d686982',registry=str(registry),registry_sha256=hash_file(registry),raw_root=str(raw),groups=groups,videos=rows,excluded_unregistered=extra,static_photos=photo,historical_claim=dict(groups=39,videos=102),verified=dict(groups=len(groups),registered_videos=len(rows),all_mp4=len(files),unregistered=len(extra),photos=len(photo)),discrepancy='frozen39 registry and current RAW agree on 39 groups / 79 videos (38x2+1x3); historical 102 is not supported by either. 30 unregistered segmentation-pool videos retained as exceptions, not assigned invented physical groups. Difference 23 has no identifiable registered missing files.',epoch=time.time())
 atomic_json(D/'DATASET_MANIFEST.json',rec);table(D/'RAW_INVENTORY.csv',rows+extra);table(D/'STATIC_PHOTOS.csv',photo)
 return rec

@contextlib.contextmanager
def gpu_lock(root):
 # A announces priority before acquiring the shared flock; B must yield at its stage boundary.
 priority=LOCK.with_suffix('.A_PRIORITY.json');atomic_json(priority,dict(pid=os.getpid(),task=TASK,epoch=time.time()))
 with LOCK.open('a+') as f:
  print('GPU_WAIT_A_PRIORITY',os.getpid(),flush=True);fcntl.flock(f,fcntl.LOCK_EX)
  try:yield
  finally:
   fcntl.flock(f,fcntl.LOCK_UN)
   if priority.exists() and read(priority).get('pid')==os.getpid():priority.unlink()

def baseline_module():
 spec=importlib.util.spec_from_file_location('ring_first_3d.v6_raw._baseline',BASE/'src/ring_first_3d/v6_raw/route.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def readonly(p,x):
  assert Path(p).is_file(),'REUSE_MISSING_RECEIPT '+str(p)
  assert read(p)==m.clean(x),'REUSE_RECEIPT_DIFFERENCE '+str(p)
 m.save=readonly
 return m

def verify_reuse(case):
 # Execute only the baseline's full cache-verification path with all writes forbidden.
 for p in [OLD/'prepared'/case/'PREPARED.json']+[OLD/'HIST'/case/n for n in ['CAMERA_COMPLETE.json','PLAN_FROZEN.json','HERO_COMPLETE.json']]:
  if not p.is_file():raise ValueError('REUSE_INCOMPLETE_STAGE_CHAIN '+str(p))
 m=baseline_module();assert case in m.ALLOWED
 for fn in ['prepare','cameras','schedule','hero','historical_extra','bind','inference_start']:
  # Base source identity is separately locked in the immutable snapshot receipt.
  assert callable(getattr(m,fn))
 result=m.hero(case,'HIST');return dict(origin='REUSED',run_path=str(OLD/'HIST'/case),source_execution_commit=result['execution_commit'],verification='baseline full RAW/model/config/function/camera/plan/native+mesh cache checks, save is read-only comparison',verified_epoch=time.time())

def recover_inference(tree,R):
 """Adapt scheduling only: original model call remains byte-equivalent AST."""
 import ast
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 init=next(n for n in main.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='runs' for t in n.targets));init.value=ast.parse('_FULL_PREVIOUS_RUNS()',mode='eval').body
 loop=next(n for n in ast.walk(main) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='c')
 # Replace M10 alternate guard (one tuple/Target already enforced) with an exact-tag resume guard.
 loop.body[0]=ast.parse("if any(r.get('tag') == c['tag'] for r in runs):\n    continue").body[0]
 # Inference destination is committed atomically before the per-tuple success ledger.
 for n in ast.walk(main):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='np' and n.func.attr=='savez_compressed':n.func=ast.Name(id='_FULL_ATOMIC_NPZ',ctx=ast.Load())
 return ast.fix_missing_locations(tree)

def previous_runs(R,plan):
 path=R/'metrics/MVS005_supported_runs.json';prior=read(path) if path.exists() else [];by={r['tag']:r for r in prior}
 for c in plan['legal']:
  p=R/'raw'/(c['tag']+'.npz');r=by.get(c['tag'])
  if r and r.get('success') and not valid_cached_native(p,r):raise RuntimeError('NATIVE_CACHE_HASH_DRIFT '+str(p))
  if p.exists() and not r:
   import numpy as np
   a=np.load(p);valid=np.isfinite(a['depth_mm']) & (a['depth_mm']>0)
   assert valid.any() and int(a['reference'])==c['reference'] and a['sources'].tolist()==c['sources']
   journal=[read(q) for q in [R/'inputs'/('TUPLE_'+c['tag']+'.json')]];assert journal[0]['input_sha256']==c['input_sha256']
   r=dict(tag=c['tag'],reference=c['reference_id'],sources=c['source_ids'],success=True,raw_SHA256=hash_file(p),native_shape=list(a['depth_mm'].shape),positive_fraction=float(valid.mean()),recovery='atomic native artifact verified against pre-inference tuple; no repeated inference',GT_used=False);prior.append(r)
 if prior:atomic_json(path,prior)
 return prior

def atomic_npz(path,**arrays):
 import numpy as np
 p=Path(path);tmp=p.with_name(p.name+'.tmp.npz');np.savez_compressed(tmp,**arrays);os.replace(tmp,p)

def worker(config,case,stage):
 os.environ['V6_FULL_CONFIG']=str(config)
 from . import route as r
 cfg=read(config);root=Path(cfg['run_root']);R=root/'HIST'/case
 entry=next(v for v in read(cfg['manifest'])['videos'] if v['case']==case)
 raw=W/'smart_endoscope_20260805 (1)/raw'/(case+'.mp4')
 assert entry['raw_path']==str(raw) and hash_file(raw)==entry['raw_sha256'],'FROZEN_RAW_MANIFEST_DRIFT'
 assert entry['ring_inner_mm']==(5 if '_R5_' in case else 10),'FROZEN_RING_IDENTITY_DRIFT'
 if stage=='reuse':
  os.environ.pop('V6_FULL_CONFIG',None)
  atomic_json(root/'states'/(case+'.reuse.json'),verify_reuse(case));return
 if stage in ['prepare','hero']:
  with gpu_lock(root):getattr(r,stage)(case,*(['HIST'] if stage=='hero' else []))
 elif stage=='camera':
  if (R/'CAMERA_STARTED.json').exists() and not (R/'CAMERA_COMPLETE.json').exists():
   archive=root/'interrupted'/case;archive.mkdir(parents=True,exist_ok=True);dest=archive/str(time.time_ns());shutil.move(str(R),dest)
   atomic_json(archive/'RECOVERY.json',dict(reason='interrupted camera process; preserve failed attempt; recompute same RAW and same fixed science',preserved_path=str(dest),epoch=time.time()))
  r.cameras(case,'HIST')
 elif stage=='schedule':r.schedule(case,'HIST')
 elif stage=='render':summarize_video(cfg,case)


def summarize_video(cfg,case):
 import numpy as np,trimesh
 from . import nearviews
 root=Path(cfg['run_root']);statepath=root/'states'/(case+'.json');state=read(statepath);R=Path(state['run_path']);plan=read(R/'PLAN_FROZEN.json');results=read(R/'metrics/MVS005_supported_runs.json');by={r['tag']:r for r in results};rows=[]
 for c in plan['legal']:
  p=R/'meshes'/(c['tag']+'_Polyp.ply');rec=dict(tag=c['tag'],raw_target=c['raw_target'],raw_support=c['raw_support'],input_sha256=c['input_sha256'],rule=c['rule_version'],mesh_path=str(p),status='NATIVE_FAILED',reason=by.get(c['tag'],{}).get('failure','NO_RESULT'))
  rec.update(target_media_type=c.get('target_media_type','video'),target_view_id=c.get('target_view_id'),support_view_ids=c.get('support_view_ids'))
  if by.get(c['tag'],{}).get('success'):
   try:
    if not valid_cached_native(R/'raw'/(c['tag']+'.npz'),by[c['tag']]):raise ValueError('native hash mismatch')
    mesh=trimesh.load(p,process=False)
    if not len(mesh.faces) or not np.isfinite(mesh.vertices).all():raise ValueError('empty or nonfinite original mesh')
    rec.update(status='RENDERABLE',reason='',mesh_sha256=hash_file(p),vertices=len(mesh.vertices),faces=len(mesh.faces))
   except Exception as ex:rec.update(status='NONRENDERABLE',reason=repr(ex))
  rows.append(rec)
 O=root/'display'/case;O.mkdir(parents=True,exist_ok=True);n=sum(r['status']=='RENDERABLE' for r in rows)
 atomic_json(O/'RESULTS.json',rows);atomic_json(O/'SUMMARY.json',dict(case=case,variant='HIST',renderable=n))
 nearviews.T=root;nearviews.LABEL['HIST']='V6 HIST';(root/'figures').mkdir(exist_ok=True)
 state.update(status='DONE',selected_targets=plan.get('original_target_count',len(plan['all_targets'])),legal_targets=len(plan['legal']),native_success=sum(bool(x.get('success')) for x in results),renderable=n,q0=sum(r['status']=='RENDERABLE' and r['rule']=='Q0' for r in rows),q1=sum(r['status']=='RENDERABLE' and r['rule']=='Q1' for r in rows),finished_epoch=time.time(),figure=('figures/HIST__'+case+'__近景逐源.png') if n else '',source_results=str(O/'RESULTS.json'))
 state.update(video_renderable=sum(r['status']=='RENDERABLE' and r['target_media_type']=='video' for r in rows),photo_renderable=sum(r['status']=='RENDERABLE' and r['target_media_type']=='photo' for r in rows))
 state['status']='RENDERING';atomic_json(statepath,state)
 crop=nearviews.make(O,kinds=('近景逐源',),full_range_link=False);atomic_json(O/'CROP_COUNTS.json',crop)
 state['status']='DONE';atomic_json(statepath,state)
 if state['origin']=='NEW':
  # These are redundant exports only; preserve all native depths, cameras and PLY meshes.
  temps=list((R/'meshes').glob('*_points.ply'))+list((R/'predictions').glob('*_surface.npz'))
  receipt=R/'REGENERABLE_EXPORTS_REMOVED.json'
  previous=read(receipt).get('files',[]) if receipt.exists() else []
  removed=[dict(path=str(p),bytes=p.stat().st_size,sha256=hash_file(p),recreate='original package_surfaces from retained native + ledger + cameras') for p in temps]
  atomic_json(receipt,dict(files=previous+removed,original_meshes_preserved=True,original_native_preserved=True))
  for p in temps:p.unlink()

def refresh(cfg,status):
 root=Path(cfg['run_root']);manifest=read(cfg['manifest']);rows=[]
 for v in manifest['videos']:
  p=root/'states'/(v['case']+'.json');row=read(p) if p.exists() else dict(case=v['case'],group=v['group'],status='PENDING' if v['status']=='READY' else v['status'],origin='',renderable=0,selected_targets=None)
  R=Path(row.get('run_path',str(root/'HIST'/v['case'])))
  if (R/'PLAN_FROZEN.json').exists():
   plan=read(R/'PLAN_FROZEN.json');row.update(selected_targets=plan.get('original_target_count',len(plan['all_targets'])),legal_targets=len(plan['legal']))
  ledger=R/'metrics/MVS005_supported_runs.json'
  if ledger.exists():
   # A successful atomic native write precedes each atomic ledger entry. No dependence on PNG completion.
   rr=read(ledger);row['native_success']=len({x['tag'] for x in rr if x.get('success') and (R/'raw'/(x['tag']+'.npz')).is_file()})
  rows.append(row)
 cov=coverage(rows);cov.update(status=status,updated_epoch=time.time(),pid=os.getpid(),disk_free_bytes=shutil.disk_usage(root).free,output_coverage_not_accuracy=True,manifest_sha256=hash_file(cfg['manifest']));atomic_json(root/'PROGRESS.json',cov);table(root/'VIDEO_RESULTS.csv',rows)
 groups=[dict(group=g,videos=sum(r['group']==g for r in rows),videos_with_output=sum(r['group']==g and r.get('renderable',0)>0 for r in rows),renderable=sum(r.get('renderable',0) for r in rows if r['group']==g)) for g in manifest['groups']];table(root/'GROUP_RESULTS.csv',groups)
 style='<meta charset="utf-8"><style>body{font-family:system-ui;max-width:1400px;margin:25px auto}img{max-width:100%}td,th{padding:6px;border:1px solid #bbb}section{margin:25px 0}</style>'
 intro=f'<h1>V6 HIST 全量 · {status}</h1><p>更新时间 {time.strftime("%Y-%m-%d %H:%M:%S")}。输出覆盖，不代表表面积覆盖或正确率。各视频坐标独立；只展示原始全源近景逐源六视图。</p><p>组 {cov["groups_with_output"]}/{cov["groups_total"]}；视频 {cov["videos_with_output"]}/{cov["videos_total"]}；Target {cov["renderable"]}/{cov["target_denominator_known"]}（已知分母；另 {cov["target_denominator_unknown_videos"]} 视频分母未知）。</p><p><a href="PROGRESS.json">实时状态</a> · <a href="VIDEO_RESULTS.csv">视频表</a> · <a href="GROUP_RESULTS.csv">组表</a> · <a href="clean/index.html">三源clean小试</a></p>'
 if cfg.get('frontend'):intro+=f'<p>视频帧Target非空Raw：{cov["video_renderable"]}；照片Target注册输出：{cov["photo_renderable"]}。上方总面源包含照片，不能除以视频帧分母解释视频恢复；本页为运行监测，最终三栏对照见小试首页。</p>'
 parts=[style,intro,'<table><tr><th>物理组</th><th>有输出视频/全部</th><th>可渲染Target</th></tr>'];(root/'groups').mkdir(exist_ok=True)
 for g in groups:
  name=g['group'];parts.append(f'<tr><td><a href="groups/{name}.html">{name}</a></td><td>{g["videos_with_output"]}/{g["videos"]}</td><td>{g["renderable"]}</td></tr>');gp=[style,f'<h1>{name}</h1><a href="../index.html">全量进度</a>']
  for r in rows:
   if r['group']!=name:continue
   gp.append('<section><h2>'+html.escape(r['case'])+'</h2><p>'+html.escape(str({k:r.get(k) for k in ['status','origin','selected_targets','legal_targets','native_success','renderable','q0','q1','reason']}))+'</p>')
   if r.get('figure'):gp.append('<img loading="lazy" src="../'+r['figure']+'">')
   gp.append('</section>')
  (root/'groups'/(name+'.html')).write_text(''.join(gp))
 (root/'index.html').write_text(''.join(parts)+'</table>')
 report=f'# V6 HIST 全量输出覆盖：{status}\n\n更新时间 {time.strftime("%Y-%m-%d %H:%M:%S")}；并非精度/表面积覆盖。\n\n组有输出 {cov["groups_with_output"]}/{cov["groups_total"]}；至少两视频有输出组 {cov["groups_two_videos_output"]}；组内全部视频有输出 {cov["groups_all_videos_output"]}。视频 {cov["videos_with_output"]}/{cov["videos_total"]}。\n\nTarget {cov["renderable"]}/{cov["target_denominator_known"]} 已知非诊断选帧分母；另 {cov["target_denominator_unknown_videos"]} 视频分母未知（含待运行、选帧失败）。\n\n```json\n'+json.dumps(cov,ensure_ascii=False,indent=2)+'\n```\n\n全部原面保留，近景裁切不改变面源计数。原生成功、可渲染、Q0/Q1及复用/新增见表。注册表核实为39组79视频；102历史说法的差异及全部109视频/120照片清单见DATASET_MANIFEST。\n'
 (root/('FINAL_COVERAGE_REPORT.md' if status in ['COMPLETE','COMPLETE_WITH_FAILURES'] else 'CURRENT_COVERAGE_REPORT.md')).write_text(report)
 return rows

def run(config):
 cfg=read(config)
 if cfg.get('approval_required'):raise RuntimeError('PILOT_REVIEW_REQUIRED_BEFORE_FULL_RUN')
 root=Path(cfg['run_root']);root.mkdir(parents=True,exist_ok=True);(root/'states').mkdir(exist_ok=True);(root/'logs').mkdir(exist_ok=True)
 with (root/'RUNNER.lock').open('a+') as guard:
  fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB);atomic_json(root/'PID.json',dict(pid=os.getpid(),started_epoch=time.time(),snapshot=str(Path(__file__).resolve()),execution_commit=os.environ.get('V6_EXECUTION_COMMIT'),command=sys.argv))
  manifest=read(cfg['manifest']);oldcases={p.name for p in (OLD/'HIST').iterdir() if (p/'HERO_COMPLETE.json').exists()} if cfg.get('reuse_old_results',True) else set()
  # New physical case first proves the new job is actually computing; all remaining rows remain queued.
  ordered=sorted(manifest['videos'],key=lambda v:(v['case'] in oldcases,v['case']))
  stop='RUNNING'
  try:
   for v in ordered:
    case=v['case'];sp=root/'states'/(case+'.json');s=read(sp) if sp.exists() else dict(case=case,group=v['group'],origin='NEW',status='PENDING',renderable=0,selected_targets=None,run_path=str(root/'HIST'/case))
    if s['status']=='DONE' or s['status'].endswith('_FAILED'):continue
    if v['status']!='READY':s.update(status=v['status'],reason=v.get('reason',v['status']));atomic_json(sp,s);continue
    if (root/'PAUSE_REQUESTED').exists():stop='PAUSED';break
    if shutil.disk_usage(root).free<cfg['minimum_free_bytes']:stop='LOW_DISK_PAUSED';break
    if case in oldcases and s['status']=='PENDING':
     s.update(status='VERIFY_REUSE');atomic_json(sp,s)
     with (root/'logs'/(case+'__reuse.log')).open('a') as log:rc=subprocess.call([sys.executable,'-m','ring_first_3d.v6_raw.full_run','worker','--config',str(config),'--case',case,'--stage','reuse'],stdout=log,stderr=subprocess.STDOUT)
     if rc==0:s.update(read(root/'states'/(case+'.reuse.json')));s['status']='REUSE_VERIFIED'
     else:s.update(origin='NEW',reuse_rejection_log=str(log.name),status='PENDING')
     atomic_json(sp,s)
    atomic_json(sp,s)
    stages=['render'] if s.get('origin')=='REUSED' else ['prepare','camera','schedule','hero','render']
    for stage in stages:
     if (root/'PAUSE_REQUESTED').exists():stop='PAUSED';break
     if shutil.disk_usage(root).free<cfg['minimum_free_bytes']:stop='LOW_DISK_PAUSED';break
     s=read(sp);s.update(status=stage.upper()+'_RUNNING',current_stage=stage,updated_epoch=time.time());atomic_json(sp,s);refresh(cfg,'RUNNING');print('STAGE_START',case,stage,flush=True)
     with (root/'logs'/(case+'__'+stage+'.log')).open('a') as log:rc=subprocess.call([sys.executable,'-m','ring_first_3d.v6_raw.full_run','worker','--config',str(config),'--case',case,'--stage',stage],stdout=log,stderr=subprocess.STDOUT)
     s=read(sp)
     if rc:
      s.update(status='RESOURCE_INTERRUPTED' if rc<0 or rc in [137,143] else stage.upper()+'_FAILED',reason=f'process exit {rc}; log {log.name}');atomic_json(sp,s);break
     if stage=='prepare':s.update(selected_targets=read(root/'prepared'/case/'PREPARED.json').get('original_video_target_count',len(read(root/'prepared'/case/'PREPARED.json')['frames'])-1));atomic_json(sp,s)
     if stage=='schedule':p=read(root/'HIST'/case/'PLAN_FROZEN.json');s.update(legal_targets=len(p['legal']),selected_targets=p.get('original_target_count',len(p['all_targets'])));atomic_json(sp,s)
     if stage=='hero':
      results=read(root/'HIST'/case/'metrics/MVS005_supported_runs.json');s.update(native_success=sum(bool(x.get('success')) for x in results));atomic_json(sp,s)
     print('STAGE_END',case,stage,rc,flush=True)
    refresh(cfg,'RUNNING')
    if stop!='RUNNING':break
   if stop=='RUNNING':
    rows=refresh(cfg,'RUNNING');stop='COMPLETE' if all(r['status']=='DONE' for r in rows) else 'PARTIAL_RESUMABLE' if any(r['status']=='RESOURCE_INTERRUPTED' for r in rows) else 'COMPLETE_WITH_FAILURES'
  except BaseException as ex:
   stop='INTERRUPTED';atomic_json(root/'RUNNER_EXCEPTION.json',dict(error=repr(ex),traceback=traceback.format_exc(),epoch=time.time()));raise
  finally:refresh(cfg,stop);print('QUEUE_EXIT',stop,flush=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['inventory','run','worker','refresh','retry']);ap.add_argument('--config');ap.add_argument('--destination');ap.add_argument('--case');ap.add_argument('--stage');a=ap.parse_args()
 if a.action=='inventory':print(inventory(a.destination)['verified'])
 elif a.action=='run':run(Path(a.config))
 elif a.action=='worker':worker(Path(a.config),a.case,a.stage)
 elif a.action=='retry':
  cfg=read(a.config);p=Path(cfg['run_root'])/'states'/(a.case+'.json');old=read(p)
  assert old['status'].endswith('_FAILED') or old['status']=='RESOURCE_INTERRUPTED','NOT_A_FAILED_VIDEO'
  atomic_json(p.with_name(p.stem+'.retry.'+str(time.time_ns())+'.json'),dict(prior=old,reason='explicit engineering resume; no support changes; successful tuple hashes rechecked'))
  old['status']='PENDING';atomic_json(p,old)
 else:refresh(read(a.config),'PARTIAL')
if __name__=='__main__':main()
