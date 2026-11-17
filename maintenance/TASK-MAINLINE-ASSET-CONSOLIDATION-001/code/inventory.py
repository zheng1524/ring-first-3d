import os,sys,json,csv,hashlib,subprocess,time,re,collections
from pathlib import Path
OUT=Path('/dev/shm/mainline_consolidation_001');HOME=Path('/home/liu')
roots=sorted(p for p in HOME.glob('ring_first_3d*')if p.is_dir())+[HOME/'ring-first-hero-core',HOME/'polyp_research/ring-first-3d',HOME/'polyp_research/ring_anchor_3d']
cache=[HOME/'.cache/mozilla',HOME/'.cache/google-chrome-headless',HOME/'.cache/google-chrome',HOME/'.cache/pip',HOME/'.cache/thumbnails']
roots +=[p for p in cache if p.exists()]
def command(cmd,cwd):
 r=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);return dict(command=cmd,cwd=str(cwd),code=r.returncode,stdout=r.stdout,stderr=r.stderr)
evidence=[command(['df','-h'],HOME),command(['git','count-objects','-vH'],HOME/'ring_first_3d_growth_recovery'),command(['git','worktree','list','--porcelain'],HOME/'ring_first_3d_growth_recovery'),command(['git','branch','-a'],HOME/'ring_first_3d_growth_recovery')]
for p in roots:
 evidence +=[command(['du','-sh',str(p)],HOME)]
evidence +=[command(['bash','-c','du -ah . | TMPDIR=/dev/shm sort -rh | head -200'],HOME/'ring_first_3d_e4_sdf_localization')]
(OUT/'INITIAL_COMMANDS.json').write_text(json.dumps(evidence,indent=2))
rows=[];byinode={};references=collections.defaultdict(set);stats=[];errors=[];t0=time.time()
skip={'.git','.venv','venv','node_modules','.mypy_cache'}
rawext={'.mp4','.avi','.mov','.mkv','.blend','.pth','.pt','.ckpt','.safetensors'}
for root in roots:
 tracked=set()
 if (root/'.git').exists():
  x=subprocess.run(['git','ls-files','-z'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if x.returncode==0:tracked=set(os.fsdecode(s)for s in x.stdout.split(b'\0')if s)
 n0=len(rows);b0=0
 for directory,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if d not in skip and not Path(directory,d).is_symlink()]
  for name in files:
   p=Path(directory,name)
   try:
    s=p.lstat()
    if not p.is_file()or p.is_symlink():continue
    key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in byinode:
     h=hashlib.sha256()
     with p.open('rb')as f:
      for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
     byinode[key]=h.hexdigest()
    protected=p.is_relative_to(HOME/'polyp_research')or p.is_relative_to(HOME/'ring_first_3d_growth_recovery')or any(z in str(p)for z in ['GROWTH_PROPOSAL_024','STEP_024'])
    task=next((x for x in p.parts if x.startswith('TASK-')),'UNASSIGNED')
    kind='source'if p.suffix in {'.py','.sh','.cpp','.h','.cu'}else'configuration'if p.suffix in {'.yaml','.yml','.toml'}else'raw_data_or_weight'if p.suffix.lower()in rawext else'final_result'if any(x in name.upper()for x in ['FINAL','TECHNICAL_REPORT','RESULT_CARD','FAILURE','GATES','UPDATES'])else'visualization'if p.suffix.lower()in {'.png','.jpg','.jpeg','.html','.glb'}else'derived_or_unclassified'
    iscache='__pycache__'in p.parts or any(p.is_relative_to(c)for c in cache)
    row=dict(path=str(p),task_id=task,size_bytes=s.st_size,sha256=byinode[key],tracked=str(p.relative_to(root))in tracked,asset_type='regenerable_cache'if iscache else kind,dependencies=[],reproducible=True if iscache else'UNVERIFIED',scientific_value='PROTECTED_UNIQUE_OR_MAINLINE'if protected or kind=='raw_data_or_weight'else'REQUIRES_DEPENDENCY_REVIEW',proposed_action='KEEP',reason='Protected location or not yet proven disposable',workspace=str(root),device=s.st_dev,inode=s.st_ino,allocated_bytes=s.st_blocks*512,protected=protected)
    rows.append(row);b0+=s.st_size
    if p.suffix.lower()in {'.py','.sh','.json','.yaml','.yml','.toml','.md'}and s.st_size<2000000:
     try:
      text=p.read_text(errors='replace')
      for ref in re.findall(r'/home/liu/[^\s\x22\x27<>`\\,;\)\]\}]+',text):references[ref].add(str(p))
     except OSError:pass
   except OSError as e:errors.append(dict(path=str(p),error=str(e)))
 stats.append(dict(root=str(root),files=len(rows)-n0,logical_bytes=b0))
 print('INVENTORY',root.name,len(rows)-n0,round(b0/1e9,3),'GB',round(time.time()-t0,1),'sec',flush=True)
for row in rows:row['dependencies']=sorted(references.get(row['path'],[]))
groups=collections.defaultdict(list)
for i,r in enumerate(rows):groups[(r['sha256'],r['size_bytes'])].append(i)
dups=[dict(sha256=h,size_bytes=b,paths=[rows[i]['path']for i in ids],physical_inodes=len({(rows[i]['device'],rows[i]['inode'])for i in ids}),logical_duplicate_bytes=b*(len(ids)-1))for(h,b),ids in groups.items()if len(ids)>1]
for name,obj in [('ASSET_INVENTORY.json',dict(roots=[str(p)for p in roots],assets=rows,workspace_stats=stats,errors=errors,excluded_directories=sorted(skip),git_objects_managed_separately=True)),('DUPLICATE_ASSET_REPORT.json',dict(groups=dups,identity='full SHA256 and byte size, never filename')),('DEPENDENCY_REFERENCE_GRAPH.json',dict(edges=[dict(target=k,referenced_by=sorted(v))for k,v in references.items()],limitations='Static absolute references; dynamic imports audited separately. No static reference does not prove an asset unused.')),('READ_ONLY_SCAN_SUMMARY.json',dict(files=len(rows),logical_bytes=sum(r['size_bytes']for r in rows),duplicate_groups=len(dups),workspace_stats=stats,seconds=time.time()-t0,threshold_counts={str(n):sum(r['size_bytes']>n for r in rows)for n in [1000000,10000000,100000000]},disk_statvfs=dict(zip(['f_bsize','f_frsize','f_blocks','f_bfree','f_bavail'],os.statvfs(HOME)[:5]))))]:
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
with(OUT/'ASSET_INVENTORY.csv').open('w')as f:
 w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows({**r,'dependencies':json.dumps(r['dependencies'])}for r in rows)
print('DONE',len(rows),time.time()-t0,flush=True)
