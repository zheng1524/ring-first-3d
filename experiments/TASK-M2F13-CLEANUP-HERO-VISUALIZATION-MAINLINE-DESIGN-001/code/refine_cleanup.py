"""Apply read-only review findings to an exact candidate list; no deletion."""
import json,tarfile,collections,re
from pathlib import Path
from cleanup_execute import sha
T=Path(__file__).resolve().parent.parent
plan=json.loads((T/'evidence/CLEANUP_PLAN.json').read_text());retained=json.loads((T/'evidence/RETAINED_PATHS.json').read_text());start=json.loads((T/'evidence/START_CONTENT_STATE.json').read_text())['files'];removed=[];kept=[]
for r in retained:
 p=Path(r['path']);su='/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/runs/STRUCTURAL_003/'in str(p)
 if su and p.suffix=='.npz' and p.name not in ['FINAL.npz','INITIAL.npz','GRAPH.npz']and not re.search(r'(^|[_/])(GT|CAD|GROUND_TRUTH)([_/.]|$)',str(p),re.I):
  assert str(p)not in start,'Do not delete unrelated captured work'
  s=p.stat();row=dict(path=str(p),root=r['root'],route=r['route'],size=s.st_size,blocks=s.st_blocks*512,inode=s.st_ino,device=s.st_dev,nlink=s.st_nlink,sha256=sha(p),reason='retired SU003 self-referencing fit cache; current Graph/ARAP/Sweep do not consume it; six FINAL and INITIAL retained')
  plan['files'].append(row);removed.append(row);plan['protected_paths']=[x for x in plan['protected_paths']if x!=str(p)]
 else:kept.append(r)
# Keep the last complete saved checkpoint in each retired E0/E2 directory; remove obsolete steps only.
by=collections.defaultdict(list)
for r in kept:
 p=Path(r['path'])
 if r['route']=='MonoSDF_E0_E2' and 'checkpoints'in p.parts and p.suffix in ['.pt','.pth','.ckpt']and str(p)not in plan['protected_paths']:by[str(p.parent)].append(r)
checkpoint_removed=[]
for directory,rr in by.items():
 rr=sorted(rr,key=lambda r:r['path'])
 for r in [x for x in rr if Path(x['path']).name=='step000.pt' and Path(x['path']).with_name('FINAL_LAST_SAFE_step000.pt').exists() and sha(x['path'])==sha(Path(x['path']).with_name('FINAL_LAST_SAFE_step000.pt'))]:
  p=Path(r['path']);s=p.stat()
  if p.is_symlink()or p.resolve()!=p:continue
  plan['files'].append(dict(path=str(p),root=r['root'],route=r['route'],size=s.st_size,blocks=s.st_blocks*512,inode=s.st_ino,device=s.st_dev,nlink=s.st_nlink,sha256=sha(p),reason='byte-identical redundant checkpoint; exact FINAL_LAST_SAFE and STOP_UNSAFE retained'));checkpoint_removed.append(str(p))
kept=[r for r in kept if r['path']not in checkpoint_removed]
assert len({r['path']for r in plan['files']})==len(plan['files'])
(T/'evidence/CLEANUP_PLAN.json').write_text(json.dumps(plan,indent=2));(T/'evidence/RETAINED_PATHS.json').write_text(json.dumps(kept,indent=2));(T/'evidence/RETIRED_CLOSURE_EXCEPTIONS.json').write_text(json.dumps(dict(old_recursive_manifest_is_historical_not_actual_consumer=True,removed_SU003_paths=removed,checkpoint_intermediates_removed=checkpoint_removed,preserved_SU004='STRUCTURAL_004/attempts/0009-G5_real_update-842b9067/{G01,G03,G05}/DEFORM_GROW/FINAL.npz',actual_current_core='STRUCTURED-BODY-UPDATE-002 DEFORM_SWEEP INITIAL/STEP_024 GRAPH+BODY/UPDATES; mainline/results FINAL_SWEEP_PARAMETERS/LOCAL_CONFIGURATION/CHOSEN_GATES'),indent=2))
# Small code/report-only companion is uploaded; full verified metadata archive stays local.
source=T/'archive/RETIRED_SOURCE_AND_REPORTS.tar.gz';members=[]
for r in json.loads((T/'evidence/ARCHIVE_MEMBERS.json').read_text()):
 p=Path(r['path'])
 if p.suffix in ['.py','.sh','.md','.toml','.yaml','.yml']or (p.suffix=='.json'and p.name.lower()in ['config.json','provenance.json','run_state.json']):members.append(r)
with tarfile.open(source,'w:gz')as tar:
 for r in members:tar.add(r['path'],arcname=r['member'],recursive=False)
with tarfile.open(source)as tar:
 for r in members:assert __import__('hashlib').sha256(tar.extractfile(r['member']).read()).hexdigest()==r['sha256']
(T/'evidence/ARCHIVE_RECEIPT.json').write_text(json.dumps(dict(full_archive=plan['archive'],full_sha256=plan['archive_sha256'],full_bytes=Path(plan['archive']).stat().st_size,full_verified_members=len(json.loads((T/'evidence/ARCHIVE_MEMBERS.json').read_text())),source_archive=str(source),source_sha256=sha(source),source_bytes=source.stat().st_size,source_verified_members=len(members)),indent=2))
print('SU cache deletions',len(removed),'checkpoint intermediates',len(checkpoint_removed),'all candidates',len(plan['files']),'source archive',source.stat().st_size)
