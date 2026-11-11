from pathlib import Path
import os,sys
M=Path(__file__).resolve().parents[1];P=M.parent
os.environ['E4_RUN_DIR']=str(M)
sys.path.insert(0,str(P/'code'))
from common import *
from scipy.spatial.transform import Rotation
GROUPS=['G01','G03','G05','G06']
for n in ['features','matches','landmarks','ring_evidence','results','optimization']:(M/n).mkdir(exist_ok=True)

def canon_np(C):
 a=-np.arctan2(C[1,3],C[0,3]);G=np.eye(4);G[:2,:2]=[[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]];return G@C

def projection(X,C,K):
 q=(np.asarray(X)-C[:3,3])@C[:3,:3];p=q@K.T;return p[:,:2]/p[:,2:],q[:,2]

def snapshot():
 f=[P/'config/FOUR_GROUP_INPUTS.json',P/'config/VIEWS.json',P/'results/B3.json',P/'quick_solver_review/provenance/DELIVERY_MANIFEST.json']+list((P/'code').glob('*.py'))
 for g in load(P/'config/FOUR_GROUP_INPUTS.json'):
  f += [Path(g['ring']['path'])]+[Path(v['cache'])for v in g['views']]
 save('provenance/UPSTREAM_FROZEN.json',dict(files=[asset(p)for p in dict.fromkeys(f)],new_outputs_only=str(M)))

def guard_fit():
 def hook(event,args):
  if event!='open'or not isinstance(args[0],(str,bytes)):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if isinstance(args[2],int)else 0
  if (any(k in mode for k in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))and str(p).startswith('/home/liu/')and not p.is_relative_to(M):raise PermissionError('NEW_EXPERIMENT_WRITES_ONLY '+str(p))
  if not any(k in mode for k in 'wax+')and (p.suffix=='.blend'or p.name in ['BODY018.npz','OBS_TRUSTED.npz','TRUSTED_HERO.npz']):raise PermissionError('NO_GT_BODY_HERO_IN_POSE_FIT '+str(p))
 sys.addaudithook(hook)
