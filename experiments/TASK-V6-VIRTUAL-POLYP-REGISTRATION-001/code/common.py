import json,hashlib
from pathlib import Path
import numpy as np
T=Path(__file__).resolve().parents[1]
RUN=T/'runs'/'RUN_001'
CFG=json.loads((T/'config.json').read_text())
V6=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/scripts')
def read(p):return json.loads(Path(p).read_text())
def clean(x):
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [clean(v) for v in x]
 if isinstance(x,float) and not np.isfinite(x):return None
 return x
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def freeze(paths):return {str(Path(p).relative_to(T)):sha(p) for p in sorted(paths)}
def check_freeze(record):
 for p,h in record.items():assert sha(T/p)==h,('INPUT_DRIFT',p)
def cases():return ['V0','V1']+['V2_'+str(s) for s in CFG['seeds']]
