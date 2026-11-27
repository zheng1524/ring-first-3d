"""Bind immutable 002 kernels to an independently frozen R1 input/output scope."""
import sys,json,hashlib,time,os
from pathlib import Path
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1]
OLD=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-REG-CLEAN-002/experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002')
sys.path.insert(0,str(OLD/'code'))
import common2 as c
CFG=dict(c.CFG,**json.loads((T/'config/PROTOCOL.json').read_text()));RUN=T/'runs/R1_001';FULL=c.WORK/'runs/v6_r1_full_b_001';SNAPSHOT=FULL/'snapshots/29874fe61f59c429fb83d2377ab707c847992ef8'
c.T=T;c.ROOT=ROOT;c.CFG=CFG;c.RUN=RUN;c.FULL=FULL
from common2 import read,save,sha,verify,resource,np,WORK,V6

def freeze(stage,out,inputs=()):
 sources=list((T/'code').glob('*.py'))+list((OLD/'code').glob('*.py'))+[V6/'track005.py',V6/'v6_common.py']
 sources += [OLD/'config/PROTOCOL.json',c.V001/'code/registration.py',c.V001/'config.json',T/'config/PROTOCOL.json']
 sources += [ROOT/'src/ring_first_3d'/p for p in ['mainline/native/cleaning.py','mainline/native/_clean_kernels.py','mainline/native/cleaning_protocol.json','v6_raw/surface_clean.py','v6_raw/trusted_restore.py','mainline/native/camera.py','mainline/native/_kernels.py','sim/geometry.py']]
 save(out/(stage+'_START.json'),dict(stage=stage,before_execution=True,resolved_config=CFG,epoch=time.time(),resource=resource(),sources=[dict(path=str(p),sha256=sha(p))for p in sources],inputs=[dict(path=str(p),sha256=sha(p))for p in inputs]))
c.stage_freeze=freeze
