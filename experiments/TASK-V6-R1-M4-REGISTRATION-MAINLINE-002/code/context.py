"""One stable M4 scope over SHA-pinned scientific kernels."""
import sys,os,time,json,hashlib
from pathlib import Path
from pinned import T,ROOT,prepare,resolve,PINS
prepare()
OLD=resolve('002','config/PROTOCOL.json').parents[1]
sys.path.insert(0,str(OLD/'code'))
import common2 as c
CFG=dict(c.CFG,**json.loads((T/'config/PROTOCOL.json').read_text()))
RUN=T/'runs'/CFG['batch'];FULL=Path(CFG['upstream_root'])
c.T=T;c.ROOT=ROOT;c.CFG=CFG;c.RUN=RUN;c.FULL=FULL
c.V001=resolve('001','config.json').parent;c.V6=c.V001/'inputs/V6_KERNELS'
c.CLEAN_T=resolve('clean','config/SOURCES_FROZEN.json').parents[1]
from common2 import read,save,sha,verify,resource,np,WORK,V6
def freeze(stage,out,inputs=()):
 sources=list((T/'code').glob('*.py'))+list((T/'runtime/pinned').rglob('*.py'))+list((T/'runtime/pinned').rglob('*.json'))+[T/'config/PROTOCOL.json']
 sources+=list((ROOT/'src/ring_first_3d/mainline/native').glob('*.py'))
 save(out/(stage+'_START.json'),dict(stage=stage,before_execution=True,resolved_config=CFG,epoch=time.time(),resource=resource(),sources=[dict(path=str(p),sha256=sha(p))for p in sources],inputs=[dict(path=str(p),sha256=sha(p))for p in inputs]))
c.stage_freeze=freeze
def cache_key(value):return hashlib.sha256(json.dumps(c.clean(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def group_out(g):return RUN/'groups'/g
def prior_run():
 # Restore the committed small archive once; no historical worktree is needed.
 import tarfile
 p=T/'runtime/regression';old=ROOT/'experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001'
 a=old/'evidence/RUN_EVIDENCE.tar.gz';manifest=read(old/'evidence/ARCHIVE_MANIFEST.json');assert sha(a)==manifest['sha256']
 if not (p/'RESTORED.json').exists():
  p.mkdir(parents=True,exist_ok=True)
  with tarfile.open(a)as tf:
   assert all(not x.name.startswith('/')and '..'not in Path(x.name).parts for x in tf.getmembers());tf.extractall(p)
  save(p/'RESTORED.json',dict(archive_sha256=sha(a)))
 return p/'runs/R1_001/real'
