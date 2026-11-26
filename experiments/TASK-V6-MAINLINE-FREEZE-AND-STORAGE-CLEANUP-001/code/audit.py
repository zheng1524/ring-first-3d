"""Read-only dependency and process inventory for this authorized cleanup."""
from pathlib import Path
import os, stat, json, csv, hashlib, subprocess, datetime, collections, re, time
W=Path('/home/liu/ring_first_3d_workspace')
D=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace')
T=Path(__file__).resolve().parents[1]
O=W/'runs/v6_freeze_storage_cleanup_001'
B=W/'runs/v6_full_run_001'
CT=D/'TASK-V6-TRUSTED-CLEAN-001/experiments/TASK-V6-RESTORE-TRUSTED-ONLY-CLEAN-001'
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def table(p,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r));Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader();w.writerows(rows)
def under(p,q):return p==q or q in p.parents
def space():
 s=os.statvfs(W);return dict(checked_beijing=now(),device=W.stat().st_dev,available_bytes=s.f_bavail*s.f_frsize,free_bytes=s.f_bfree*s.f_frsize,df=subprocess.check_output(['df','-B1',str(W)],text=True))
def identity(p):
 s=Path(p).lstat();return dict(path=str(p),device=s.st_dev,inode=s.st_ino,size=s.st_size,blocks=s.st_blocks*512,nlink=s.st_nlink,mtime_ns=s.st_mtime_ns,mode=s.st_mode)
def files(root):
 for a,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if not Path(a,d).is_symlink()]
  for n in names:yield Path(a,n)
def strings(x):
 if isinstance(x,dict):
  for k,v in x.items():
   yield str(k);yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
 elif isinstance(x,str):yield x
def processes():
 result=[];hz=os.sysconf('SC_CLK_TCK');boot=time.time()-float(Path('/proc/uptime').read_text().split()[0])
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
   if not any(x in cmd for x in ['ring_first_3d','polyp_research','ring-first-hero','new-polyp-dxy']):continue
   if 'code/audit.py' in cmd or 'code/plan_cleanup.py' in cmd or 'code/protected_delete.py' in cmd or '/bin/bash -' in cmd:continue
   s=(p/'stat').read_text().rsplit(')',1)[1].split();cwd=os.readlink(p/'cwd');fds=[]
   for fd in (p/'fd').iterdir():
    try:
     target=os.readlink(fd)
     if target.startswith('/'):fds.append(dict(fd=fd.name,target=target))
    except OSError:pass
   maps=sorted(set(line.split()[-1] for line in (p/'maps').read_text().splitlines() if '/' in line))
   result.append(dict(pid=int(p.name),ppid=int(s[1]),start_ticks=int(s[19]),started_beijing=datetime.datetime.fromtimestamp(boot+int(s[19])/hz,datetime.timezone(datetime.timedelta(hours=8))).isoformat(),command=cmd,cwd=cwd,exe=os.readlink(p/'exe'),fds=fds,mapped_files=maps))
  except (OSError,ValueError):pass
 return result
def health(label):
 ps=processes();cfg=read(read(B/'SNAPSHOT.json')['config']);manifest=read(cfg['manifest']);states=[]
 for e in manifest['videos']:
  q=B/'states'/(e['case']+'.json');states.append(read(q) if q.exists() else dict(case=e['case'],group=e['group'],status='PENDING',renderable=0))
 counts=collections.Counter(x['status'] for x in states);out=[x for x in states if x.get('renderable',0)>0]
 readable=[]
 for e in manifest['videos']:
  paths=[s for s in strings(e) if s.startswith('/home/liu/') and Path(s).suffix.lower() in ['.mp4','.mov','.avi']]
  for p in paths:
   try:
    with open(p,'rb') as f:assert f.read(1)
    readable.append(dict(case=e['case'],path=p,readable=True,size=Path(p).stat().st_size))
   except OSError as ex:readable.append(dict(case=e['case'],path=p,readable=False,error=str(ex)))
 logs=[B/'runner.log']+list((B/'logs').glob('*.log'));latest=max(logs,key=lambda p:p.stat().st_mtime)
 def tail(p):
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-4000));return f.read().decode(errors='replace').splitlines()[-12:]
 x=dict(checked_beijing=now(),processes=ps,space=space(),full=dict(queue=read(B/'PROGRESS.json'),counts=dict(counts),normal_with_output=sum(r['status']=='DONE' and r.get('renderable',0)>0 for r in states),normal_without_output=sum(r['status']=='DONE' and not r.get('renderable',0)>0 for r in states),videos_total=len(states),groups_total=len(manifest['groups']),videos_with_output=len(out),groups_with_output=len(set(r['group'] for r in out)),sources=sum(r.get('renderable',0) for r in states),video_coverage=len(out)/len(states),group_coverage=len(set(r['group'] for r in out))/len(manifest['groups']),active=[r for r in states if 'RUNNING' in r['status'] or r['status']=='RENDERING'],latest_log=str(latest),latest_log_mtime_ns=latest.stat().st_mtime_ns,latest_log_tail=tail(latest),runner_log=identity(B/'runner.log'),snapshot=read(B/'SNAPSHOT.json')),raw_future_readability=readable,ring_sift_queue=read(W/'runs/ring_sift_comparison_001/EXPANSION_GPU_QUEUE.json'))
 save(O/f'HEALTH_{label}.json',x);table(T/f'evidence/VIDEOS_{label}.csv',states);return x

def protections():
 roots=[]
 def add(p,reason,consumer):
  p=Path(p);roots.append(dict(path=str(p),real_path=str(p.resolve()),reason=reason,consumer=consumer,exists=p.exists()))
 for p,reason in [(W/'runs/v6_full_run_001','完整当前全量及未来输出'),(W/'runs/v6_raw_to_hero_001','old_readonly_root及基线结果池'),(W/'runs/v6_trusted_clean_restore_001','最新四源clean完整证据'),(W/'runs/ring_sift_comparison_001','活动/待运行Ring+SIFT对比'),(W/'runs/m2f5_unified/cad','V6及clean共享CAD'),(W/'runs/m2f6_unified','必要历史对照与准备祖先'),(W/'assets','真实/虚拟配准祖先、GT及明确保留资产'),(W/'src','现用及未提交源码'),(W/'tools','现用及未提交源码'),(W/'experiments','手写分析、身份与已交付小证据'),(W/'mainline','主体Graph/ARAP/Sweep'),(W/'.runtime','共享运行库'),(W/'.git','全部Git历史'),(W/'runs/shared_gpu.lock','活动和未来队列锁'),(W/'runs/shared_gpu.A_PRIORITY.json','活动队列优先权'),(D,'全部工作树及其独有修改/结果'),(Path('/home/liu/polyp_research'),'原数据、标定、现用权重、历史内核和共享环境；本轮不在P删除'),(Path('/home/liu/new-polyp-dxy'),'DXY独立冻结'),(Path('/home/liu/ring-first-hero-core'),'HERO入口、模型配置与下游祖先'),(O,'本轮清理证据'),(W/'runs/m2f13_hero_all/archives','既有精简证据包，不能重复计历史释放')]:add(p,reason,'人工保护范围/方法依赖')
 for p in (W/'runs/m2f10_v6_multiview').iterdir():
  if p.is_dir() and p.name.startswith('M2F11-'):add(p,'M2F11部分运行及尚未单独交付成果','M2F11')
 manifests=[]
 for wt,task in [('TASK-V6-VIRTUAL-REG-001','TASK-V6-VIRTUAL-POLYP-REGISTRATION-001'),('TASK-DOWNSTREAM-001','TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001')]:
  p=D/wt/'experiments'/task/'evidence/RETAIN_DEPENDENCIES.json';manifests.append(p)
  for s in strings(read(p)):
   if s.startswith('/home/liu/'):add(s,'保留依赖清单逐路径',str(p))
 # Current baseline comparison receipts enumerate the actual old source closure.
 for root in [W/'runs/v6_raw_to_hero_001/evaluation/BASELINE',CT,D/'TASK-V6-RAW-TO-HERO-001/experiments/TASK-V6-RAW-TO-HERO-MAINLINE-001',D/'TASK-RING-SIFT-COMPARISON-001/experiments/TASK-RING-SIFT-VS-SIFT-COMPARISON-001']:
  for p in root.rglob('*.json'):
   if p.stat().st_size>10*1024**2:continue
   try:x=read(p)
   except (ValueError,OSError):continue
   for s in strings(x):
    if s.startswith(str(W/'runs')) and any('/'+q in s for q in ['m2f','m2e','m2d']):add(s,'当前基线/对比/clean身份清单引用',str(p))
 # Follow symlinks used by every protected current output tree and worktree.
 symlinks=[]
 for root in [W/'runs/v6_full_run_001',W/'runs/v6_raw_to_hero_001',W/'runs/ring_sift_comparison_001',D]:
  for a,ds,fs in os.walk(root,followlinks=False):
   for n in ds+fs:
    p=Path(a,n)
    if p.is_symlink():
     target=p.resolve();symlinks.append(dict(path=str(p),target=str(target)))
     if under(target,W/'runs'):add(target,'保留树符号链接的真实目标',str(p))
   ds[:]=[d for d in ds if not Path(a,d).is_symlink()]
 unique={}
 for r in roots:unique.setdefault((r['path'],r['consumer']),r)
 rows=list(unique.values());save(T/'PROTECTED_PATHS.json',dict(created_beijing=now(),paths=rows,dependency_manifests=[dict(path=str(p),sha256=sha(p)) for p in manifests]));table(T/'PROTECTED_PATHS.csv',rows);save(T/'evidence/SYMLINK_TARGETS.json',symlinks)
 return rows

def inventory():
 names=['m2f10_v6_multiview','m2f12_historical004','m2f13_hero_all','m2f7_hist_g01','m2f8_v6_general','m2f9_v6_general','m2e_historical_method_integration','m2f1_w0_admission_restoration','m2f1_strict_restoration','m2f2_root_cause_corrective','m2f3_admission_convergence','m2f5_unified','m2f_metric_depth_diagnosis']
 rows=[]
 for name in names:
  root=W/'runs'/name
  for p in files(root):
   r=identity(p);r.update(root=str(root),route=name,regular=stat.S_ISREG(r['mode']) and p.resolve()==p,real_path=str(p.resolve()));rows.append(r)
 save(O/'INVENTORY_BEFORE.json',rows)
 summary=[]
 for name in names:
  rr=[r for r in rows if r['route']==name];ins={ (r['device'],r['inode']):r for r in rr }
  summary.append(dict(route=name,path=str(W/'runs'/name),files=len(rr),unique_allocated_bytes=sum(x['blocks'] for x in ins.values())))
 table(T/'evidence/ROOTS_BEFORE.csv',summary);return rows

if __name__=='__main__':
 import sys
 O.mkdir(exist_ok=True);action=sys.argv[1]
 if action=='before':
  h=health('BEFORE');p=protections();i=inventory();print('READ_ONLY_BEFORE',h['full']['counts'],len(p),'protection entries',len(i),'inventory leaves')
 elif action=='health':
  h=health(sys.argv[2]);print(h['checked_beijing'],h['full']['counts'],h['full']['sources'])
