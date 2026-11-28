"""Task-local I/O and exact historical AST loader; no historical main execution."""
import ast,hashlib,json,subprocess,sys,os
from pathlib import Path
import numpy as np
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1]
BASE='80d00ad3530abfd782e27a2c1981a272bf9739e7'
WORK=Path('/home/liu/ring_first_3d_workspace')
M4=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-M4-002/experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002')
FULL=WORK/'runs/v6_r1_full_b_001'
def clean(x):
 if isinstance(x,(np.ndarray,np.generic)):return clean(x.tolist())
 if isinstance(x,Path):return str(x)
 if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [clean(v)for v in x]
 if isinstance(x,float)and not np.isfinite(x):return None
 return x
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);assert T in p.resolve().parents
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n');q.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(clean(x),sort_keys=True).encode()).hexdigest()
def asset(p,h=None):
 p=Path(p);s=sha(p);assert h is None or s==h,('DRIFT',str(p));return dict(path=str(p),sha256=s,bytes=p.stat().st_size)
def snapshot(commit,path):
 p=T/'runtime/pinned'/commit/path
 if not p.exists():
  raw=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 lock=T/'evidence/SOURCE_LOCK.json';rec=read(lock)if lock.exists()else{}
 key=commit+':'+path;s=sha(p)
 if key in rec:assert rec[key]['sha256']==s
 else:rec[key]=dict(commit=commit,path=path,sha256=s);save(lock,rec)
 return p
def definitions(commit,path,names,ns):
 p=snapshot(commit,path);tree=ast.parse(p.read_bytes());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
 return ns
def code_key():return digest({n:sha(T/'code'/n)for n in ['core.py','geometry.py','observations.py','base_plane.py','fit.py','pipeline.py']})
