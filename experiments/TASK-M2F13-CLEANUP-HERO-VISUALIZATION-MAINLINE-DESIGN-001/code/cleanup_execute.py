"""M2F12 exact-manifest guard adapted only for explicitly counted shared hardlinks."""
import hashlib,json,os,time,sys
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def validate(row,roots,protected):
 p=Path(row['path']);root=Path(row['root'])
 if str(root)not in roots or not p.is_absolute()or root not in p.parents:raise ValueError('outside authorized roots')
 if p.is_symlink()or p.resolve()!=p or not p.is_file():raise ValueError('not direct regular file')
 if str(p)in protected:raise ValueError('protected consumer/work')
 s=p.stat()
 if s.st_ino!=row['inode']or s.st_dev!=row['device']or not 1<=s.st_nlink<=row['nlink']or s.st_size!=row['size']or sha(p)!=row['sha256']:raise ValueError('identity drift')
 return p
def main(planpath):
 p=Path(planpath);plan=json.loads(p.read_text());receipt=p.with_name('CLEANUP_EXECUTED.json');assert not receipt.exists(),'No replay'
 assert sha(plan['archive'])==plan['archive_sha256'];protected=set(plan['protected_paths'])
 for r in plan['files']:validate(r,plan['roots'],protected)
 fs=os.statvfs(plan['roots'][0]);out=dict(execution_code_sha256=sha(__file__),plan_sha256=sha(planpath),execution_source='uncommitted exact adapter bytes; source hash authoritative, final commit supplied after execution',start_epoch=time.time(),before_available_bytes=fs.f_bavail*fs.f_frsize,archive_sha256=plan['archive_sha256'],deleted=[],errors=[])
 receipt.write_text(json.dumps(out,indent=2))
 journal=receipt.with_suffix('.jsonl')
 with journal.open('x')as f:
  for r in plan['files']:
   try:
    q=validate(r,plan['roots'],protected);last=q.stat().st_nlink==1;q.unlink();item=dict(r,last_inode_link_removed=last);out['deleted'].append(item);f.write(json.dumps(item)+'\n');f.flush()
   except Exception as ex:out['errors'].append(dict(path=r['path'],error=repr(ex)));break
 os.sync();fs=os.statvfs(plan['roots'][0]);out.update(after_available_bytes=fs.f_bavail*fs.f_frsize,end_epoch=time.time());out['net_df_release_bytes']=out['after_available_bytes']-out['before_available_bytes'];out['last_link_allocated_bytes']=sum(x['blocks']for x in out['deleted']if x['last_inode_link_removed']);receipt.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items()if k!='deleted'});print('DELETED',len(out['deleted']));assert not out['errors']
if __name__=='__main__':main(sys.argv[1])
