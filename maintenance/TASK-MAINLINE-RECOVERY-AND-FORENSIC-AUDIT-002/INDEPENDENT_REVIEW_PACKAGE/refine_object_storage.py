import pathlib,json,subprocess,gzip,os,collections
O=pathlib.Path(__file__).resolve().parent;d=json.load(open(O/'GIT_OBJECT_AUDIT.json'));pm={}
def git(root,*args):
 p=subprocess.run(['git','-C',root,*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),timeout=600);return p.stdout.decode(errors='replace')
for c in d['clones']:
 common=pathlib.Path(c['common_dir']);c['query_worktree']=c['owner'];c['owner']=str(common.parent);root=c['query_worktree'];objects=pathlib.Path(c['objects']);local={};tables=[]
 for p in objects.glob('pack/*.idx'):
  text=git(root,'verify-pack','-v',str(p));tables.append(text)
  for s in text.splitlines():
   a=s.split()
   if len(a)>=5 and len(a[0])==40 and a[1] in ['blob','tree','commit','tag']:local[a[0]]=dict(kind=a[1],logical=int(a[2]),representation_bytes=int(a[3]),storage='pack')
 for bucket in objects.iterdir():
  if len(bucket.name)==2 and all(ch in '0123456789abcdef' for ch in bucket.name) and bucket.is_dir():
   for p in bucket.iterdir():
    if len(p.name)==38:local[bucket.name+p.name]=dict(kind='loose',logical=None,representation_bytes=p.stat().st_size,storage='loose')
 with gzip.open(O/(c['clone_id']+'_physical_verify_pack.txt.gz'),'wt')as f:f.write('\n'.join(tables))
 pm[c['clone_id']]=local;c['physically_stored_object_count']=len(local)
 accessible={s.split()[0] for s in gzip.open(O/(c['clone_id']+'_objects_all_batch_check.txt.gz'),'rt') if s.split()}
 c['accessible_but_not_physically_stored_here_count']=len(accessible-set(local));c['accessible_but_not_physically_stored_here_sample']=sorted(accessible-set(local))[:30]
 reach={s.split()[0] for s in git(root,'rev-list','--objects','--all').splitlines() if s.split()};reflog={s.split()[0] for s in gzip.open(O/(c['clone_id']+'_reachable_all_reflog.txt.gz'),'rt') if s.split()}
 c['reachable_only_via_reflog_count']=len((reflog-reach)&set(local));c['physical_objects_not_refs_or_reflogs_count']=len(set(local)-reflog);c['physical_objects_not_refs_or_reflogs_sample']=sorted(set(local)-reflog)[:30]
for c in d['clones']:
 mine=pm[c['clone_id']];other=set().union(*(set(v) for k,v in pm.items() if k!=c['clone_id']));unique=set(mine)-other
 c['accessible_unique_object_count']=c.pop('unique_object_count');c['accessible_unique_objects_uncompressed_bytes']=c.pop('unique_objects_uncompressed_bytes');c['accessible_unique_objects_disk_record_bytes']=c.pop('unique_objects_disk_record_bytes');c['accessible_unique_object_SHAs']=c.pop('unique_object_SHAs')
 c['physical_unique_object_count']=len(unique);c['physical_unique_object_representation_bytes']=sum(mine[k]['representation_bytes'] for k in unique);c['physical_unique_object_SHAs']=sorted(unique);c['unique_object_caveat']='Accessible object counts include alternates. Physical unique objects enumerate only own loose files/pack indices; byte sum is per-object representation estimate, NOT reclaimable disk bytes.'
# Exact pack matches separate from inode match.
packs=[dict(c=p['clone_id'],**v) for p in d['clones']for v in p['packs']]
d['pack_comparison']=[dict(a=a['path'],b=b['path'],sha256=a['sha256'],same_inode=(a['device'],a['inode'])==(b['device'],b['inode'])) for i,a in enumerate(packs)for b in packs[i+1:]if a['sha256']==b['sha256']]
d['interpretation_correction']='harness objects/info/alternates points to old nested clone. Independent .git directory is not evidence of a self-contained clone. No alternate detachment attempted.'
commitsets={c['clone_id']:set(git(c['query_worktree'],'rev-list','--all').splitlines()) for c in d['clones']}
for c in d['clones']:
 mine=commitsets[c['clone_id']];other=set().union(*(v for k,v in commitsets.items() if k!=c['clone_id']))
 c['unique_ref_reachable_commit_count']=len(mine-other);c['unique_ref_reachable_commit_SHAs']=sorted(mine-other)
json.dump(d,open(O/'GIT_OBJECT_AUDIT.json','w'),ensure_ascii=False,indent=2)
print([(c['clone_id'],c['physically_stored_object_count'],c['accessible_but_not_physically_stored_here_count'],c['physical_unique_object_count'],c['reachable_only_via_reflog_count'],c['physical_objects_not_refs_or_reflogs_count'])for c in d['clones']])
