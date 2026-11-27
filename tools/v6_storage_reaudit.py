"""Read-only storage inventory under the researcher's revised retention policy."""
from pathlib import Path
import os,stat,json,csv,gzip,hashlib,collections,subprocess,time,re
W=Path('/home/liu/ring_first_3d_workspace');P=Path('/home/liu/polyp_research');WT=Path(__file__).resolve().parents[1];WORK=WT.parent
T=WT/'experiments/TASK-V6-R1-STORAGE-REAUDIT-001';H=W/'runs/v6_r1_split_handoff_001'
roots={'workspace':W,'polyp_research':P,'worktree_copies':WORK}
records_ext={'.py','.sh','.bash','.md','.rst','.txt','.json','.jsonl','.csv','.yaml','.yml','.toml','.ini','.cfg','.log','.patch','.diff','.lock','.xml','.html','.js','.css','.cpp','.h','.hpp','.c','.cu','.ipynb','.sql','.cmake','.gitignore','.gitattributes'}
mesh_ext={'.ply','.obj','.stl','.off','.glb','.gltf'}
array_ext={'.npz','.npy','.pkl','.pickle','.h5','.hdf5','.pt','.pth','.ckpt','.bin','.safetensors'}
image_ext={'.png','.jpg','.jpeg','.webp','.gif','.svg','.pdf'}
raw_ext={'.mp4','.mov','.avi','.mkv','.zip','.7z','.rar','.tar','.gz'}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def git_blob_hash(p):
 h=hashlib.sha1(('blob '+str(p.stat().st_size)+'\0').encode())
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()

def dump(p,a):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
def csvout(p,rows):
 if not rows:return
 op=gzip.open if p.suffix=='.gz' else open
 with op(p,'wt',encoding='utf-8',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');wr.writeheader();wr.writerows(rows)
def within(p,q):return p==q or str(p).startswith(str(q)+os.sep)

site=json.loads(Path('/home/liu/ring-first-hero-core/site_config.local.json').read_text())
protected_dirs=[W/'assets',W/'smart_endoscope_20260805 (1)',W/'.git',W/'.runtime',W/'runtime',W/'src',W/'tools',W/'mainline',W/'runs/v6_r1_full_b_001',W/'cache/v6_r1',H,WT,
 W/'runs/ring_sift_comparison_001',W/'runs/v6_trusted_clean_restore_001',W/'runs/v6_freeze_storage_cleanup_001',W/'runs/m2f5_unified/cad',
 P/'.git',P/'ring_anchor_3d/.venv',P/'ring_anchor_3d/.git',P/'experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model',P/'smart_endoscope_20260805',P/'picture',P/'new picture',P/'models',P/'external',P/'ring-first-3d',P/'result',
 *map(Path,site['readonly_dependency_paths']),Path(site['mvs_root']),Path(site['dino_root'])]
protected_files={Path(site['checkpoint']).resolve():'official HERO checkpoint'}
# Protect precise ongoing downstream inputs, not every historical representative closure.
depmanifests=[]
for name,task in [('TASK-V6-VIRTUAL-REG-001','TASK-V6-VIRTUAL-POLYP-REGISTRATION-001'),('TASK-V6-REG-CLEAN-002','TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002'),('TASK-DOWNSTREAM-001','TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001')]:
 p=WORK/name/'experiments'/task/'evidence/RETAIN_DEPENDENCIES.json'
 if p.exists():
  obj=json.loads(p.read_text());entries=obj if isinstance(obj,list) else obj.get('files',[]);depmanifests.append({'path':str(p),'sha256':sha(p),'entries':len(entries)})
  for x in entries:
   if isinstance(x,dict) and isinstance(x.get('path'),str):protected_files[Path(x['path']).resolve()]=str(p)
for p in (WT/'experiments/TASK-V6-RAW-TO-HERO-MAINLINE-001/evidence/KERNEL_LOCK.json',):
 obj=json.loads(p.read_text());depmanifests.append({'path':str(p),'sha256':sha(p),'entries':len(obj['files'])})
 for name in obj['files']:protected_files[Path(name).resolve()]=str(p)
# R0 caches still supply full selected-pool SIFT identities until B cold/hot validation passes.
needed_preprocess=set()
for base in [W/'runs/v6_full_run_001',W/'runs/v6_raw_to_hero_001']:
 for f in (base/'prepared').glob('*/PREPARED.json'):
  try:
   a=json.loads(f.read_text())
   for row in a['frames']:
    for k in ['RGB_path','Mask_path']:needed_preprocess.add(Path(row[k]).resolve())
  except (ValueError,KeyError):pass
# A path being an output of an old task does not certify that it is an original RAW asset.

protected_prefixes=tuple(str(q)+os.sep for q in protected_dirs)
assert all(root.resolve()==root for root in roots.values()), 'Inventory roots must be canonical; symlink subdirectories are skipped'
def disposition(p,relative,rootlabel):
 parts=p.parts;low=str(p).lower();ext=p.suffix.lower();real=p
 if p.is_symlink():return 'KEEP_LINK_REVIEW_TARGET','Never follow or delete links in this audit'
 if real in protected_files:return 'KEEP_ACTIVE_DEPENDENCY',protected_files[real]
 if str(p).startswith(protected_prefixes):return 'KEEP_RAW_GT_RUNTIME_OR_ACTIVE','Explicit retained runtime/input/current-task root'
 if '.git' in parts or '.venv' in parts or 'site-packages' in parts:return 'KEEP_GIT_OR_ENVIRONMENT','Preserve Git history/shared or unverified environment'
 if any(x.lower() in {'gt','ground_truth','groundtruth','cad','calibration','annotations','annotation','labels'} for x in parts) or p.name.lower() in {'virtual_gt.npz','canonical_ring.npz'}:return 'KEEP_RAW_GT_RUNTIME_OR_ACTIVE','GT/CAD/calibration/annotation identity'
 if any('gt' in re.split(r'[^a-z0-9]+',x.lower()) for x in parts):return 'KEEP_RAW_GT_RUNTIME_OR_ACTIVE','Explicit GT token in file or dataset identity; do not retire true-shape evidence'
 if ext in records_ext or any(x in parts for x in ['scripts','src','tools','vendor','code']):return 'KEEP_SOURCE_CONFIG_METRICS','Retain scripts, source versions, configuration, metrics and explanations'
 if rootlabel=='worktree_copies':
  # Validate only exact tracked duplicate artifacts, leaving unique or edited files untouched.
  relparts=relative.parts
  if len(relparts)<3 or relparts[1] not in {'runs','experiments','docs','references'}:return 'KEEP_WORKTREE_UNIQUE_OR_UNCLASSIFIED','Not a derived artifact namespace'
  canonical=W/Path(*relparts[1:])
  if not canonical.is_file() or canonical.is_symlink() or canonical.stat().st_size!=p.stat().st_size:return 'KEEP_WORKTREE_UNIQUE_OR_UNCLASSIFIED','No same-size canonical original; do not discard unique work'
  return 'VERIFY_WORKTREE_DUPLICATE','Requires SHA and HEAD blob identity; metrics archive if canonical is later retired'
 if real in needed_preprocess:return 'WAIT_R1_CACHE_MIGRATION','Still read by R0/R1 cache provenance; B cold/hot and consumer loading incomplete'
 if within(p,W/'runs/v6_frontend_photo_pilot_001/R1') and ext not in mesh_ext and not any(x in parts for x in ['raw','clean','scenes','figures','visualizations']):return 'KEEP_R1_EQUIVALENCE_BASELINE','R1 cold/hot comparison and approved 205-Target baseline'
 if within(p,W/'runs/v6_full_run_001') or within(p,W/'runs/v6_raw_to_hero_001'):
  if any(x in parts for x in ['prepared','observations','inputs','current_inputs','v5raw']):return 'WAIT_R1_CACHE_MIGRATION','Current optional-import/full-track input needs independent cache loading proof'
 if ext in raw_ext:return 'KEEP_ARCHIVE_OR_VIDEO_PENDING_ORIGIN','Do not confuse original archives/videos with generated exports'
 if p.name.startswith('tail_') and within(p,P/'ring_anchor_3d/experiments/ring_first_v9_ring_guided_recovery/weights'):return 'PROPOSE_RETIRE_DOWNLOAD_FRAGMENTS','Obsolete MASt3R download chunks; complete file separately inventoried'
 if within(p,P/'ring_anchor_3d/experiments/ring_first_v9_ring_guided_recovery/weights') or within(p,P/'ring_anchor_3d/experiments/ring_first_v13_multisource/weights'):return 'PROPOSE_RETIRE_OLD_METHOD_WEIGHTS','MASt3R/RoMa/CoTracker/LightGlue/standalone DINO old-route weights; not current R1 dependency manifest'
 if ext in mesh_ext:return 'PROPOSE_MESH_AFTER_METRICS','User permits old geometry retirement after hashes, geometry metrics and existing science metrics are archived'
 if within(p,P/'experiments'):
  if any(x in parts for x in ['candidates','dense','neighbors','cache']):return 'REVIEW_EARLY_2D_DERIVED','September/October frame selection/risk-resampling derived data; DXY ownership/consumer closure required'
  return 'REVIEW_EARLY_EXPERIMENT_ASSET','Early experiment asset; original data and DXY consumers must be distinguished'
 if within(p,P/'ring_anchor_3d/experiments') or within(p,W/'runs') or within(p,W/'experiments') or within(p,W/'references/obsolete_methods'):
  if ext in array_ext:return 'PROPOSE_RETIRE_NON_R1_ARRAYS','Old generated observations/matching/cameras/native/deformation arrays; retain metadata and metric record; no runtime receipt claims after retirement'
  if ext in image_ext:
   if any(x in parts for x in ['inputs','frames','images','prepared','rgb','masks','data','dataset']):return 'REVIEW_DERIVED_IMAGE_ORIGIN','Needs RAW/annotation-vs-derived provenance before release'
   return 'PROPOSE_RETIRE_OLD_VISUALS','Generated legacy plots/renderings; preserve representative report figure and numerical records first'
 return 'REVIEW_UNCLASSIFIED','No justified deletion classification'

start=os.statvfs(W);starttime=time.time();rows=[];links=[]
for label,root in roots.items():
 for base,dirs,files in os.walk(root,followlinks=False):
  for d in list(dirs):
   p=Path(base)/d
   if p.is_symlink():links.append({'path':str(p),'target':str(p.resolve())});dirs.remove(d)
  for name in files:
   p=Path(base)/name
   try:st=p.lstat()
   except FileNotFoundError:continue
   rel=p.relative_to(root);family=str(root/Path(*rel.parts[:2])) if len(rel.parts)>1 else str(root)
   if label=='polyp_research' and rel.parts[:2]==('ring_anchor_3d','experiments') and len(rel.parts)>2:family=str(root/Path(*rel.parts[:3]))
   action,reason=disposition(p,rel,label)
   rows.append(dict(path=str(p),root=label,family=family,file_type='regular' if stat.S_ISREG(st.st_mode) else 'symlink' if stat.S_ISLNK(st.st_mode) else 'special',size_bytes=st.st_size,allocated_bytes=st.st_blocks*512,device=st.st_dev,inode=st.st_ino,nlink=st.st_nlink,mtime_ns=st.st_mtime_ns,disposition=action,reason=reason,sha256='',retained_at='',git_blob_verified=False,metric_status='NOT_APPLICABLE'))
 print('INVENTORIED',label,len(rows),flush=True)
# Hash proposed files and verify worktree copies against current HEAD content; no status-only inference.
hashes={};gitmaps={};proposed=[];verify_count=0
for x in rows:
 p=Path(x['path']);key=(x['device'],x['inode'],x['size_bytes'],x['mtime_ns'])
 if x['file_type']!='regular' or not (x['disposition'].startswith('PROPOSE') or x['disposition']=='VERIFY_WORKTREE_DUPLICATE' or x['disposition']=='WAIT_R1_CACHE_MIGRATION'):continue
 if key not in hashes:hashes[key]=sha(p)
 x['sha256']=hashes[key]
 if x['disposition']=='VERIFY_WORKTREE_DUPLICATE':
  rel=p.relative_to(WORK);tree=WORK/rel.parts[0];local=Path(*rel.parts[1:]);canonical=W/local
  if tree not in gitmaps:
   raw=subprocess.check_output(['git','ls-tree','-r','-z','HEAD'],cwd=tree);gitmaps[tree]={}
   for a in raw.split(b'\0'):
    if a:
     header,name=a.split(b'\t',1);gitmaps[tree][name.decode()]=header.decode().split()[2]
  blob=git_blob_hash(p)
  if gitmaps[tree].get(str(local))!=blob:x['disposition']='KEEP_WORKTREE_UNIQUE_OR_UNCLASSIFIED';x['reason']='Working file differs from tracked HEAD blob or is untracked';continue
  st=canonical.stat();k=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
  if k not in hashes:hashes[k]=sha(canonical)
  if hashes[k]!=x['sha256']:x['disposition']='KEEP_WORKTREE_UNIQUE_OR_UNCLASSIFIED';x['reason']='Canonical copy content differs';continue
  x.update(disposition='PROPOSE_DUPLICATE_WORKTREE_ARTIFACT',reason='Exact canonical content and tracked blob preserved; no unique edits lost. Canonical must remain until its own metric-retirement gate passes.',retained_at=str(canonical),git_blob_verified=True);verify_count+=1
 if x['disposition'].startswith('PROPOSE'):
  if p.suffix.lower() in mesh_ext:x['metric_status']='NEEDS_GEOMETRY_ARCHIVE'
  proposed.append(x)
 if len(hashes)%1000==0:print('HASHED_INODES',len(hashes),flush=True)
# Allocated space counted once per inode, and only if every hardlink is in the proposal set.
byinode=collections.defaultdict(list)
for x in rows:byinode[(x['device'],x['inode'])].append(x)
recoverable=0;ambiguous_links=0
for key,a in byinode.items():
 candidate=[x for x in a if x['disposition'].startswith('PROPOSE')]
 if candidate and len(candidate)==a[0]['nlink'] and len(candidate)==len(a):recoverable+=a[0]['allocated_bytes']
 elif candidate:ambiguous_links+=1
families=[]
for family in sorted({x['family'] for x in rows}):
 rr=[x for x in rows if x['family']==family];unique={(x['device'],x['inode']):x for x in rr};totals=collections.Counter()
 for x in rr:totals[x['disposition']]+=x['size_bytes']
 families.append(dict(path=family,files=len(rr),logical_bytes=sum(x['size_bytes'] for x in rr),unique_allocated_bytes=sum(x['allocated_bytes'] for x in unique.values()),proposed_logical_bytes=sum(x['size_bytes'] for x in rr if x['disposition'].startswith('PROPOSE')),disposition_bytes=json.dumps(totals,ensure_ascii=False,sort_keys=True)))
summary=dict(status='AUDIT_ONLY_NOT_READY',task='TASK-V6-R1-STORAGE-REAUDIT-001',started_epoch=starttime,finished_epoch=time.time(),free_before_bytes=start.f_bavail*start.f_frsize,filesystem_total_bytes=start.f_blocks*start.f_frsize,files=len(rows),scanned_unique_allocated_bytes=sum(a[0]['allocated_bytes'] for a in byinode.values()),scanned_logical_bytes=sum(x['size_bytes'] for x in rows),proposal_files=len(proposed),proposal_logical_bytes=sum(x['size_bytes'] for x in proposed),proposal_max_recoverable_allocated_bytes=recoverable,proposal_inodes_with_other_links_excluded=ambiguous_links,verified_worktree_duplicate_files=verify_count,disposition_counts=dict(collections.Counter(x['disposition'] for x in rows)),disposition_logical_bytes={k:sum(x['size_bytes'] for x in rows if x['disposition']==k) for k in sorted({x['disposition'] for x in rows})},actual_deleted_this_audit=0,previous_A_batch_not_counted=True)
csvout(T/'FILE_AUDIT.csv.gz',rows);csvout(T/'PROPOSED_FILES.csv.gz',proposed);csvout(T/'DIRECTORY_AUDIT.csv',families);dump(T/'SUMMARY.json',summary);dump(T/'evidence/ACTIVE_DEPENDENCIES.json',dict(site_config=site,protected_dirs=list(map(str,protected_dirs)),protected_files={str(k):v for k,v in protected_files.items()},dependency_manifests=depmanifests));dump(T/'evidence/SYMLINKS.json',links)
print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
