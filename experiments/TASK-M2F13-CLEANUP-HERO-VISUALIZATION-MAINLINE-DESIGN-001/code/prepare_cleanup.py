"""Refresh only prior-audit retirement candidates; preserve exact consumers and work content."""
import json,csv,re,os,hashlib,tarfile,collections,subprocess
from pathlib import Path
T=Path(__file__).resolve().parent.parent;W=Path('/home/liu/ring_first_3d_workspace');P=Path('/home/liu/polyp_research')
PRE=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F12/experiments/TASK-M2F12-CLEANUP-AND-HISTORICAL-004-CAMERA-RESTORATION-001')
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for k,v in x.items():yield k;yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
patterns=[('TSDF',r'TASK-E3-D0-OPEN3D-TSDF'),('NeuralFusion',r'NEURALFUSION'),('MonoSDF_E0_E2',r'MONOSDF|TASK-NEURAL-E[02]'),('PMGR_FFD',r'TASK-E4-PMGR'),('Hull_H1_H2',r'occlusion_visual_hull_20261024|^ring_vh_v1$'),('Old_fusion_GICP',r'^surface_fusion_v[123]$|^independent_confidence_fusion_v1$|TASK-PHASED-(INCREMENTAL-FUSION|MAIN-SURFACE-CROSSVIDEO)|TASK-VIEW-PARTITION-MAST3R-FUSION'),('Old_Body_structural',r'TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001|TASK-E4-BODY-E'),('UNIFIED_002',r'TASK-E4-UNIFIED-PIPELINE-COMPLETION-002'),('M2_retired_runs',r'^m2e_historical_method_integration$|^m2f(1_|2_|3_|5_unified$|8_v6_general$|9_v6_general$)')]
inventory=read('/tmp/hero_audit_inventory.json')['files'];roots={}
for row in inventory:
 p=Path(row[0]);parts=p.parts
 if '.git'in parts or '/TASK-M2F10/'in str(p)or'/TASK-M2F11/'in str(p):continue
 for i,part in enumerate(parts):
  match=next((name for name,pattern in patterns if re.search(pattern,part,re.I)),None)
  if match:roots[str(Path(*parts[:i+1]))]=match;break
# No whole-project walk: refresh descendants only within prior-identified retirement roots.
protected={};old=read(PRE/'evidence/CLEANUP_PLAN.json')
for p in old['protected_paths']:protected[p]='existing mainline closure: M2F12 CLEANUP_PLAN'
for p in read(T/'evidence/START_CONTENT_STATE.json')['files']:protected[p]='preexisting unrelated/uncommitted content; START_CONTENT_STATE SHA'
for p in read(PRE/'evidence/RESTORATION_SOURCE_LOCK_R3.json')['files']:protected[p]='H004 frozen scientific source consumer'
for p in read(W/'runs/m2f12_historical004/BASELINE_FROZEN.json')['files']:protected[p['path']]='M2F12 frozen baseline'
for manifest in list((W/'runs/m2f10_v6_multiview').rglob('RUN_STATE.json'))+list((W/'runs/m2f11_v6_full_dataset').rglob('RUN_STATE.json')):
 for p in strings(read(manifest)):
  if p.startswith('/')and Path(p).is_file():protected[str(Path(p).resolve())]='M2F10/M2F11 RUN_STATE input: '+str(manifest)
# Explicit formal H2 examples preserve full unknown/ROI, not just display subsets.
hull=P/'ring_anchor_3d/experiments/occlusion_visual_hull_20261024'
for q in list((hull/'meshes').glob('G01_00[45]_H2_nALL.ply'))+list((hull/'diagnostics').glob('G01_00[45]_H2_nALL_faces.npz'))+list((hull/'voxels').glob('*nALL.npz'))+list(hull.rglob('Fig2*'))+list(hull.rglob('Fig9*')):
 if q.is_file():protected[str(q)]='formal full H2 unknown/ROI representative; FORMAL_PREDICTIONS_BEFORE_GT'
# Imported runtime and necessary model are deliberate canonical shared dependencies.
canonical_runtime=[P/'ring_anchor_3d/.venv',P/'ring_anchor_3d/experiments/surface_fusion_v1/vendor',P/'ring_anchor_3d/experiments/surface_fusion_v1/weights',P/'ring_anchor_3d/experiments/surface_fusion_v3/vendor']
keep_archive={};candidates=[];retained=[];missing=[]
metadata={'.py','.sh','.md','.json','.jsonl','.csv','.yaml','.yml','.toml','.ini','.txt','.log','.patch','.diff'}
derived={'.npz','.npy','.ply','.obj','.glb','.gltf','.pt','.pth','.ckpt','.png','.html','.js'}
for root,route in sorted(roots.items()):
 R=Path(root)
 if not R.exists():missing.append(dict(root=root,route=route));continue
 files=sorted(p for p in R.rglob('*')if p.is_file()and not p.is_symlink()and '.git'not in p.parts)
 # Retain two real representative derived panels/meshes per root, together with all metadata.
 reps=[]
 for suffix in ['.png','.ply']:
  reps+=sorted((p for p in files if p.suffix==suffix and p.stat().st_size<4*2**20),key=lambda p:str(p))[:1]
 for p in files:
  s=str(p);low=s.lower();st=p.stat();reason=None
  if p.resolve()!=p:reason='symlink ancestor; not a deletion candidate'
  elif any(r==p or r in p.parents for r in canonical_runtime):reason='canonical shared HERO/Open3D runtime or model: CORE/site_config.local.json and M2F12 hero_check'
  elif s in protected:reason=protected[s]
  elif any(x in p.parts for x in ['.git','vendor','.venv','runtime','weights','checkpoints']):reason='runtime/model/checkpoint ownership requires individual review'
  elif p.suffix in metadata:reason='exact source/config/input identity/negative-result metadata for retired route'
  elif re.search(r'(^|[/_])(gt|cad|ground_truth|calibration|annotation|graph|arap|sweep|camera|cameras|tracks|landmarks|reference_banks|initial)([/_.]|$)',low):reason='protected GT/CAD or retained camera/landmark/Body lineage asset'
  elif p.suffix.lower()in{'.mp4','.avi','.mov','.zip','.jpg','.jpeg','.safetensors'}:reason='protected original data/container or model'
  elif any(x in p.parts for x in ['raw','inputs','images','masks','labels','evaluation_inputs','provenance']):reason='input/ancestry evidence retained for exact reproduction; not derived output deletion'
  elif p in reps:reason='minimal representative real result for this retired root'
  elif p.suffix not in derived:reason='individual unknown file kind; explicit exception'
  if reason:
   retained.append(dict(path=s,root=root,route=route,bytes=st.st_size,blocks=st.st_blocks*512,reason=reason))
   if p.suffix in metadata and st.st_size<8*2**20 and not any(x in p.parts for x in ['vendor','runtime','.venv','.git']):keep_archive[s]=p
   if p in reps or 'formal full H2' in reason:keep_archive[s]=p
  else:candidates.append(dict(path=s,root=root,route=route,size=st.st_size,blocks=st.st_blocks*512,inode=st.st_ino,device=st.st_dev,nlink=st.st_nlink,sha256=sha(p),reason='authorized retired derived output; metadata and representative archived; no protected consumer'))
# Baseline explicit source snapshots already hold all listed retired algorithm sources; archive manifest references exact prior pack.
archive=W/'runs/m2f13_hero_all/archives/RETIRED_FINAL_EVIDENCE.tar.gz';members=[]
with tarfile.open(archive,'w:gz')as tar:
 for s,p in sorted(keep_archive.items()):
  member=s.lstrip('/');tar.add(p,arcname=member,recursive=False);members.append(dict(path=s,member=member,sha256=sha(p),bytes=p.stat().st_size))
with tarfile.open(archive)as tar:
 for row in members:assert hashlib.sha256(tar.extractfile(row['member']).read()).hexdigest()==row['sha256']
plan=dict(roots=list(roots),protected_paths=sorted(protected),archive=str(archive),archive_sha256=sha(archive),files=candidates)
for name,value in [('CLEANUP_PLAN',plan),('RETIRED_ROOTS',roots),('RETAINED_PATHS',retained),('MISSING_RETIRED_ROOTS',missing),('ARCHIVE_MEMBERS',members)]:
 (T/f'evidence/{name}.json').write_text(json.dumps(value,indent=2))
summary={r:dict(deletable_files=sum(x['route']==r for x in candidates),deletable_bytes=sum(x['blocks']for x in candidates if x['route']==r),retained_bytes=sum(x['blocks']for x in retained if x['route']==r))for r,_ in patterns}
(T/'evidence/CLEANUP_PREVIEW.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print('ARCHIVE',archive.stat().st_size,'MEMBERS',len(members),'FILES',len(candidates),'ROOTS',len(roots))
