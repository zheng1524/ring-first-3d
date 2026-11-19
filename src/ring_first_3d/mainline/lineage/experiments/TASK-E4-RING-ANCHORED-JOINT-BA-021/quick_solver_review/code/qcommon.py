from pathlib import Path
import sys
Q=Path(__file__).resolve().parents[1];P=Q.parent
sys.path.insert(0,str(P/'code'))
from common import *
R=P
from scipy.spatial.transform import Rotation

def qsave(p,v):save(str((Q/str(p)).relative_to(P)),v)
def qtable(p,v):table(str((Q/str(p)).relative_to(P)),v)
def finishq(fig,path,dpi=130):
 p=Q/path;p.parent.mkdir(exist_ok=True,parents=True);fig.savefig(p,dpi=dpi,bbox_inches='tight')
def qguard():
 def guard(event,args):
  if event=='open'and isinstance(args[0],(str,bytes)):
   p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if isinstance(args[2],int)else 0;writing=any(c in mode for c in'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
   if writing and str(p).startswith('/home/liu/')and not p.is_relative_to(Q):raise PermissionError('QUICK_LOCAL_WRITES_ONLY:'+str(p))
   if not writing and(p.name=='BODY018.npz'or'/hero_fit/'in str(p)or'/holdout/hero/'in str(p)or p.suffix=='.blend'):raise PermissionError('NO_BODY_HERO_GT_IN_BA:'+str(p))
 sys.addaudithook(guard)
