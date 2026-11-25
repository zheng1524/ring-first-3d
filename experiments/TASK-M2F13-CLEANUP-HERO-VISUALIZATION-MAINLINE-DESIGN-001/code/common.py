import os,sys,json,hashlib,importlib.util
from pathlib import Path
import numpy as np
T=Path(__file__).resolve().parent.parent;W=Path('/home/liu/ring_first_3d_workspace');B=W/'runs/m2f13_hero_all';B12=W/'runs/m2f12_historical004'
P12=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F12/experiments/TASK-M2F12-CLEANUP-AND-HISTORICAL-004-CAMERA-RESTORATION-001')
CORE=Path('/home/liu/ring-first-hero-core');sys.path.insert(0,str(P12/'code'));sys.dont_write_bytecode=True
import hero_check as oldhero
read=oldhero.read;sha=oldhero.sha
rt=read(CORE/'site_config.local.json');sys.path[:0]=rt['readonly_dependency_paths']+[str(W/'src')]
for k in ['HF_HOME','HF_MODULES_CACHE','TORCH_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']:os.environ[k]=str(B/'runtime'/k)
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
MODEL_SHA='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d'
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def frame_identity(fs,raw_sha):
 return [dict(raw_video_sha256=raw_sha,raw_frame=f['raw_frame'],id=f['id'],RGB_sha256=hashlib.sha256(f['RGB'].tobytes()).hexdigest(),Mask_sha256=hashlib.sha256(f['labels'].tobytes()).hexdigest(),K=np.asarray(f['K']).tolist(),C=np.asarray(f['c2w_mm']).tolist())for f in fs]
def combo_id(identity):
 payload=dict(model=MODEL_SHA,shape=[352,640],refine=1,fast_cost_volume=False,frames=[{k:v for k,v in x.items()if k!='id'}for x in identity])
 return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
