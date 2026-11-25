"""Execute an exact, pre-reviewed M2F12 retired-output manifest; no glob deletion."""
import hashlib,json,os,datetime,sys
from pathlib import Path

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def validate(row,roots,protected):
 p=Path(row['path']);root=Path(row['root'])
 if str(root) not in roots or not p.is_absolute() or root not in p.parents:raise ValueError('outside authorized roots')
 if p.is_symlink() or p.resolve()!=p or not p.is_file():raise ValueError('not a direct regular file')
 if str(p) in protected:raise ValueError('protected dependency')
 s=p.stat()
 if s.st_nlink!=1 or s.st_ino!=row['inode'] or s.st_size!=row['size'] or sha(p)!=row['sha256']:raise ValueError('identity drift')
 return p

def main():
 planpath=Path(sys.argv[1]);plan=json.loads(planpath.read_text());receipt=planpath.with_name('CLEANUP_EXECUTED.json')
 if receipt.exists():raise ValueError('refuse replay of executed manifest')
 if sha(plan['archive'])!=plan['archive_sha256']:raise ValueError('archive changed')
 protected=set(plan['protected_paths'])
 # Validate the whole batch before any unlink; repeat per file immediately before unlink.
 for r in plan['files']:validate(r,plan['roots'],protected)
 s=os.statvfs(plan['roots'][0]);before=s.f_bavail*s.f_frsize
 result=dict(started=datetime.datetime.now().astimezone().isoformat(),before_available_bytes=before,archive_sha256=plan['archive_sha256'],deleted=[],errors=[])
 receipt.write_text(json.dumps(result,indent=2))
 for r in plan['files']:
  try:validate(r,plan['roots'],protected).unlink();result['deleted'].append(r)
  except Exception as e:result['errors'].append(dict(path=r['path'],error=str(e)));break
 os.sync();s=os.statvfs(plan['roots'][0]);result['after_available_bytes']=s.f_bavail*s.f_frsize
 result['net_df_release_bytes']=result['after_available_bytes']-before
 result['completed']=datetime.datetime.now().astimezone().isoformat()
 receipt.write_text(json.dumps(result,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k not in ['deleted']},indent=2));print('deleted',len(result['deleted']))
 if result['errors']:raise SystemExit(1)
if __name__=='__main__':main()
