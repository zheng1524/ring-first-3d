import json,hashlib,os,shutil,time,ast
from pathlib import Path
import numpy as np
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1];CFG=json.loads((T/'config/PROTOCOL.json').read_text());RUN=T/'runs'/CFG['batch']
WORK=Path('/home/liu/ring_first_3d_workspace');FULL=WORK/'runs/v6_full_run_001'
V001=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-VIRTUAL-REG-001/experiments/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001');VRUN=V001/'runs/RUN_001'
CLEANWT=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-TRUSTED-CLEAN-001');CLEAN_T=CLEANWT/'experiments/TASK-V6-RESTORE-TRUSTED-ONLY-CLEAN-001';CLEAN_RUN=WORK/'runs/v6_trusted_clean_restore_001'
V6=V001/'inputs/V6_KERNELS'
def read(p):return json.loads(Path(p).read_text())
def clean(x):
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,Path):return str(x)
 if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v)for v in x]
 if isinstance(x,float)and not np.isfinite(x):return None
 return x
def save(p,x):
 p=Path(p);assert T==p.resolve() or T in p.resolve().parents,('WRITE_OUTSIDE_TASK',p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def verify(records):
 for r in records:assert sha(r['path'])==r['sha256'],('DRIFT',r['path'])
def resource():
 free=shutil.disk_usage(T).free;used=sum(p.stat().st_size for p in T.rglob('*')if p.is_file());assert free>=CFG['reserve_bytes'] and used<CFG['task_bytes_cap']-32*1024**2,('RESOURCE_DEFERRED',free,used)
 return dict(free_bytes=free,task_bytes=used,nice=os.getpriority(os.PRIO_PROCESS,0),affinity=sorted(os.sched_getaffinity(0)))
def original(path,names,ns):
 ns['__file__']=str(path);tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];assert {n.name for n in nodes}==set(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns

def stage_freeze(stage,folder,inputs=()):
 sources=list((T/'code').glob('*.py'))+[V6/'track005.py',V6/'v6_common.py',V001/'code/registration.py',V001/'config.json']
 sources += [ROOT/'src/ring_first_3d'/p for p in ['v6_raw/surface_clean.py','v6_raw/trusted_restore.py','mainline/native/cleaning.py','mainline/native/_clean_kernels.py','mainline/native/cleaning_protocol.json','sim/geometry.py','contracts/coordinates.py']]
 rec=dict(stage=stage,before_execution=True,epoch=time.time(),resource=resource(),sources=[dict(path=str(p),sha256=sha(p))for p in sources],inputs=[dict(path=str(p),sha256=sha(p))for p in inputs]);save(Path(folder)/(stage+'_START.json'),rec);return rec
