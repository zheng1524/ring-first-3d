import json,csv,hashlib,os,re,subprocess,collections,tarfile,io
from pathlib import Path
W=Path('/home/liu/ring_first_3d_workspace');T=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F12/experiments/TASK-M2F12-CLEANUP-AND-HISTORICAL-004-CAMERA-RESTORATION-001');(T/'code').mkdir(exist_ok=True);(T/'archive').mkdir(exist_ok=True)
roots=[W/'runs'/n for n in ['m2e_historical_method_integration','m2f1_w0_admission_restoration','m2f1_strict_restoration','m2f2_root_cause_corrective','m2f3_admission_convergence','m2f5_unified','m2f8_v6_general','m2f9_v6_general']]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
D=json.load(open('/tmp/hero_audit_inventory.json'))['files']
protected=set();closures=[W/'docs/cleanup_003/EXTRACTED_INPUT_CLOSURE.json',W/'manifests/LOCAL_DEPENDENCIES.json']
closures+=list((W/'runs/m2f10_v6_multiview').rglob('RUN_STATE.json'))
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for k,v in x.items():yield k;yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
for p in closures:
 for s in strings(json.loads(p.read_text())):
  if s.startswith('/') and Path(s).is_file():protected.add(str(Path(s).resolve()))
tracked=set(subprocess.check_output(['git','-C',str(W),'ls-files'],text=True).splitlines())
selected=[]; reps={}
for root in roots:
 fs=sorted(r for r in D if r[0].startswith(str(root)+'/'))
 for r in fs:
  p=Path(r[0]);parts=p.relative_to(root).parts
  if p.name=='RAW_NATIVE_MESH.npz' or (p.suffix=='.ply' and 'hero' in parts):
   group=next((v for v in parts if v.startswith('GP_')),'unknown');reps.setdefault((str(root),group),str(p.parent))
 for r in fs:
  p=Path(r[0]);s=str(p)
  derived=p.name in {'FACE_EVIDENCE.npz','RAW_NATIVE_MESH.npz','HERO_native.npz','NATIVE_RGB_LABELS.npz'} or p.suffix=='.ply'
  if not derived or p.is_symlink() or not p.is_file():continue
  if any(s.startswith(v+'/') for v in reps.values()):continue
  if s in protected or str(p.relative_to(W)) in tracked:continue
  if any(k in s.lower() for k in ['/cad/','/gt/','/ground_truth/','/initial/','/reference_banks/']):continue
  st=p.stat()
  if st.st_nlink!=1:continue
  selected.append(dict(path=s,root=str(root),size=st.st_size,blocks=st.st_blocks*512,inode=st.st_ino,sha256=sha(p),reason='authorized retired run derived HERO/mesh; representative retained; camera/landmark/RAW/source untouched'))
# Compact archive: all involved current source wrappers, run summary/config/state/logs,
# plus retirement module source/report and representative PNG; originals remain.
keep={}
for p in W.joinpath('tools').glob('*.py'):
 if any(k in p.name for k in ['m2e','m2f1','m2f2','m2f3','m2f5','m2f8','m2f9']):keep[str(p)]=p
for root in roots:
 for p in root.rglob('*'):
  if p.is_file() and not p.is_symlink() and p.suffix in {'.json','.yaml','.yml','.csv','.log','.md','.py','.sh','.jsonl','.txt'} and p.stat().st_size<2*2**20:
   keep[str(p)]=p
 for p in sorted(root.rglob('*.png'))[:2]:keep[str(p)]=p
mods=list(csv.DictReader(open(W/'docs/audits/TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001/MODULE_VERSION_MATRIX.csv')))
retired={'T39','T40','T41','N05','N07','N13'}
for m in mods:
 if m['module_id'] in retired or m['module_id'].startswith('SU'):
  for key in ['source_path','evidence']:
   p=Path(m[key])
   if p.is_file() and p.stat().st_size<4*2**20:
    keep[str(p)]=p
  src=Path(m['source_path'])
  for p in src.parent.glob('*.py'):
   if p.stat().st_size<2*2**20:keep[str(p)]=p
manifest=[]
archive=T/'archive/RETIRED_MINIMAL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tf:
 for path,p in sorted(keep.items()):
  member=path.lstrip('/');tf.add(p,arcname=member,recursive=False);manifest.append({'source':path,'member':member,'sha256':sha(p),'size':p.stat().st_size})
with tarfile.open(archive) as tf:
 for row in manifest:assert hashlib.sha256(tf.extractfile(row['member']).read()).hexdigest()==row['sha256']
(T/'evidence/ARCHIVE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
plan={'roots':list(map(str,roots)),'protected_paths':sorted(protected),'representative_directories':list(reps.values()),'archive':str(archive),'archive_sha256':sha(archive),'files':selected}
(T/'evidence/CLEANUP_PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
print('archive',len(manifest),archive.stat().st_size,'selected',len(selected),'allocated GiB',sum(r['blocks']for r in selected)/2**30,'protected',len(protected),'reps',len(reps))
print(collections.Counter({str(root):sum(r['blocks']for r in selected if r['root']==str(root))/2**30 for root in roots}))
