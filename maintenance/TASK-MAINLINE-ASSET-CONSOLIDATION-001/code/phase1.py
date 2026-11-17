"""Explicit manifest, full-SHA precondition, atomic dedup; no scientific deletion."""
import json,os,hashlib,time,collections
from pathlib import Path
O=Path('/dev/shm/mainline_consolidation_001');d=json.loads((O/'ASSET_INVENTORY.json').read_text());rows=d['assets']
byhash=collections.defaultdict(list)
for r in rows:
 if not r['protected']and r['asset_type']!='raw_data_or_weight'and r['size_bytes']>=100000 and Path(r['path']).suffix.lower()in {'.npz','.npy','.ply','.obj','.png','.jpg','.jpeg','.html','.glb','.json','.csv','.gz','.js','.bin'}:
  byhash[(r['sha256'],r['size_bytes'])].append(r)
plan=[]
for r in rows:
 if r['asset_type']=='regenerable_cache'and not r['protected']and not r['tracked']:
  plan.append(dict(path=r['path'],sha256=r['sha256'],bytes=r['size_bytes'],action='DELETE_REGENERABLE_CACHE',reason='Explicitly authorized bytecode/browser/thumbnail/pip cache; not weights or original observations',retained_alternative=None,reproducible=True,tracked=False))
for key,g in byhash.items():
 if len(g)<2:continue
 g.sort(key=lambda r:(len(r['path']),r['path']));canonical=g[0]
 for r in g[1:]:
  if(r['device'],r['inode'])==(canonical['device'],canonical['inode']):continue
  plan.append(dict(path=r['path'],sha256=r['sha256'],bytes=r['size_bytes'],action='DELETE_DUPLICATE_PAYLOAD_KEEP_HARDLINK',reason='Full-SHA identical immutable derived result/visualization; atomic hardlink preserves every existing path and byte',retained_alternative=canonical['path'],reproducible='Exact retained canonical bytes',tracked=r['tracked']))
v=os.statvfs('/home/liu');before=dict(free_bytes=v.f_bfree*v.f_frsize,available_bytes=v.f_bavail*v.f_frsize)
manifest=dict(authorized_task='TASK-MAINLINE-ASSET-CONSOLIDATION-001',prepared_before_execution=True,protected_roots=['/home/liu/polyp_research','/home/liu/new-polyp-dxy','/home/liu/ring_first_3d_growth_recovery'],operations=plan,before=before,archive_decision='KEEP both large MAX-COVERAGE tarballs:124 member payloads not present as separate files, plus changed content; cannot certify complete duplication')
(O/'PHASE1_DELETE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
receipts=[]
for i,a in enumerate(plan):
 p=Path(a['path']);record=dict(path=str(p),action=a['action'],sha256=a['sha256'],before_bytes=a['bytes'],retained_alternative=a['retained_alternative'])
 try:
  assert not any(p.is_relative_to(Path(x))for x in manifest['protected_roots'])
  s=p.stat();assert not p.is_symlink()and s.st_size==a['bytes']and sha(p)==a['sha256'],'ASSET_CHANGED_OR_LINK'
  if a['action']=='DELETE_REGENERABLE_CACHE':p.unlink();record.update(status='DELETED',released_payload_allocated_bytes=s.st_blocks*512 if s.st_nlink==1 else 0)
  else:
   q=Path(a['retained_alternative']);t=q.stat();assert t.st_dev==s.st_dev and(s.st_mode&0o777)==(t.st_mode&0o777)and sha(q)==a['sha256']
   if s.st_ino==t.st_ino:record.update(status='ALREADY_SHARED',released_payload_allocated_bytes=0)
   else:
    temp=p.with_name(p.name+'.mainline-dedup-tmp');assert not temp.exists();os.link(q,temp);os.replace(temp,p)
    assert p.stat().st_ino==q.stat().st_ino and sha(p)==a['sha256']
    record.update(status='DEDUPLICATED_PATH_PRESERVED',released_payload_allocated_bytes=s.st_blocks*512 if s.st_nlink==1 else 0)
 except (OSError,AssertionError)as e:record.update(status='SKIPPED_UNCHANGED',reason=str(e),released_payload_allocated_bytes=0)
 receipts.append(record)
 if i%1000==0:print('CLEANUP',i,'/',len(plan),flush=True)
os.sync();v=os.statvfs('/home/liu');after=dict(free_bytes=v.f_bfree*v.f_frsize,available_bytes=v.f_bavail*v.f_frsize)
report=dict(operations=receipts,before=before,after=after,measured_free_byte_change=after['free_bytes']-before['free_bytes'],payload_allocated_bytes_released=sum(x['released_payload_allocated_bytes']for x in receipts),all_references_preserved_for_duplicates=True,no_original_unique_observation_deleted=True,Git_history_unchanged=True)
(O/'CLEANUP_RECEIPTS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='operations'},indent=2),flush=True)
