from common import *
ROOT=Path(__file__).resolve().parents[1]
READS=set()
def install():
 plan=load(ROOT/'config/VIEW_PLAN.json');blocked=set()
 for r in plan:
  if r['role']=='HOLDOUT':
   blocked.update(str(Path(p).resolve())for p in [r['meta']['RGB_source'],r['meta']['Mask_source'],r['cache']])
 def audit(event,args):
  if event!='open'or not isinstance(args[0],(str,bytes)):return
  p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if isinstance(args[2],int)else 0;writing=any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if writing:return
  if s in blocked or p.is_relative_to(ROOT/'holdout'):raise PermissionError('018_HOLDOUT_INPUT_FORBIDDEN_DURING_OPTIMIZATION '+s)
  if p.is_relative_to(ROOT):READS.add(s)
 sys.addaudithook(audit)
def flush(name):save('provenance/'+name+'_OPTIMIZER_READS.json',dict(task_data_read_paths=sorted(READS),HOLDOUT_access=False,protection='strict file read rejection plus FIT-only Case; installed for uniform contact-Sobolev R2 runs'))
