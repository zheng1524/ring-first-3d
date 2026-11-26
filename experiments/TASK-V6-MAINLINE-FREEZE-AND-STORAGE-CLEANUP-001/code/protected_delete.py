"""Exact leaf unlink; reuse historical identity guard, strengthen live protection.

Never invoke the old cleanup main/old deletion list. No recursive directory removal.
"""
from audit import *
import importlib.util
OLD=D/'TASK-M2F13/experiments/TASK-M2F13-CLEANUP-HERO-VISUALIZATION-MAINLINE-DESIGN-001/code/cleanup_execute.py'
spec=importlib.util.spec_from_file_location('old_leaf_identity_guard',OLD);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)

def protected(p,paths):return any(str(q) in paths for q in [p,*p.parents])
def open_inodes(proc_root=Path('/proc')):
 result=set()
 for process in proc_root.iterdir():
  if not process.name.isdigit():continue
  try:entries=list((process/'fd').iterdir())
  except OSError:entries=[]
  try:
   for line in (process/'maps').read_text().splitlines():
    fields=line.split();major,minor=fields[3].split(':');inode=int(fields[4])
    if inode:result.add((os.makedev(int(major,16),int(minor,16)),inode))
  except (OSError,ValueError,IndexError):pass
  for entry in entries:
   try:
    s=entry.stat()
    if stat.S_ISREG(s.st_mode):result.add((s.st_dev,s.st_ino))
   except OSError:pass
 return result
def validate(row,roots,protected_paths,opened):
 p=Path(row['path'])
 if protected(p,protected_paths) or protected(p.resolve(),protected_paths):raise ValueError('protected prefix/target')
 if (row['device'],row['inode']) in opened:raise ValueError('currently open inode')
 p=legacy.validate(row,roots,protected_paths)
 s=p.lstat()
 if s.st_mtime_ns!=row['mtime_ns'] or s.st_blocks*512!=row['blocks'] or not stat.S_ISREG(s.st_mode):raise ValueError('metadata drift')
 return p
def unlink_leaf(row,roots,protected_paths,opened):
 p=validate(row,roots,protected_paths,opened)
 fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  s=os.stat(p.name,dir_fd=fd,follow_symlinks=False)
  if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(row['device'],row['inode'],row['size'],row['mtime_ns']):raise ValueError('pre-unlink drift')
  if not stat.S_ISREG(s.st_mode):raise ValueError('not regular leaf')
  os.unlink(p.name,dir_fd=fd)
  return dict(row,last_inode_link_removed=s.st_nlink==1,reclaimed_allocated_bytes=s.st_blocks*512 if s.st_nlink==1 else 0,deleted_beijing=now())
 finally:os.close(fd)
def verify_static():
 x=read(O/'STATIC_BEFORE.json')
 for row in x['files']:
  p=Path(row['path']);s=p.stat()
  if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(row['device'],row['inode'],row['size'],row['mtime_ns']):
   if not (row.get('allow_identical_atomic_rewrite') and row.get('sha256') and sha(p)==row['sha256']):raise ValueError('static identity drift '+str(p))
  if row.get('sha256') and sha(p)!=row['sha256']:raise ValueError('static hash drift '+str(p))
 return len(x['files'])
def execute(planpath):
 plan=read(planpath);receipt=O/'EXECUTION.json';assert not receipt.exists(),'NO_REPLAY'
 assert sha(T/'PROTECTED_PATHS.json')==plan['protected_sha256']
 assert sha(O/'STATIC_BEFORE.json')==plan['static_sha256']
 assert sha(OLD)==plan['historical_guard_sha256']
 p=read(T/'PROTECTED_PATHS.json');paths={r[k] for r in p['paths'] for k in ['path','real_path']}
 result=dict(start_beijing=now(),plan_sha256=sha(planpath),execution_source_sha256=sha(__file__),before=space(),batches=[],deleted=[],exceptions=[])
 save(receipt,result)
 with (O/'UNLINK_JOURNAL.jsonl').open('x') as journal:
  for route in plan['batch_order']:
   assert sha(T/'PROTECTED_PATHS.json')==plan['protected_sha256'];verify_static();opened=open_inodes();before=space();rows=[r for r in plan['files'] if r['route']==route];batch=[]
   for ordinal,row in enumerate(rows):
    if ordinal%64==0:opened=open_inodes()
    try:
     item=unlink_leaf(row,plan['roots'],paths,opened);result['deleted'].append(item);batch.append(item);journal.write(json.dumps(item,ensure_ascii=False)+'\n');journal.flush()
    except (ValueError,OSError) as ex:result['exceptions'].append(dict(path=row['path'],reason=repr(ex)))
   os.fsync(journal.fileno());result['batches'].append(dict(route=route,before=before,after=space(),deleted_files=len(batch),reclaimed_allocated_bytes=sum(r['reclaimed_allocated_bytes'] for r in batch),static_dependencies_verified=True));save(receipt,result);print('BATCH',route,len(batch),sum(r['reclaimed_allocated_bytes'] for r in batch),flush=True)
 result.update(end_beijing=now(),after=space(),static_files_verified=verify_static());result['reclaimed_allocated_bytes']=sum(r['reclaimed_allocated_bytes'] for r in result['deleted']);result['net_df_bytes']=result['after']['available_bytes']-result['before']['available_bytes'];save(receipt,result)
 print('EXECUTED',len(result['deleted']),result['reclaimed_allocated_bytes'],'NET_DF',result['net_df_bytes'],'EXCEPTIONS',len(result['exceptions']))
if __name__=='__main__':
 import sys
 execute(Path(sys.argv[1]))
