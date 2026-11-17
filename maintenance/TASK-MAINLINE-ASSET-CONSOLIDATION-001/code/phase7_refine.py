"""Remove our redundant staging copies, retaining code/protocols and curated evidence."""
import json,hashlib,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1]
results=[json.loads((R/'mainline/validation/replays/003'/n/'RESULT.json').read_text())for n in ['ring-first','hero','body-initialization','body-update','stalk-growth-g01','stalk-growth-g03','a-to-b','depth-supervised-pytorch']]
assert all(x['status']=='PASS'for x in results)
assert json.loads((R/'mainline/validation/regression/RESULT.json').read_text())['status']=='PASS'
p=T/'COPY_VERIFICATION.json';v=json.loads(p.read_text());assert v['all_copy_hashes_verified']
with gzip.open(T/'COPY_VERIFICATION_BEFORE_PHASE7.json.gz','wt')as f:json.dump(v,f)
drop=[];keep=[]
for x in v['files']:
    original=x['original_path'];rel=Path(x['new_path'])
    staged_extra=original.startswith('experiments/')and x['source_commit']=='bac3fc89ef95db522b63cf6bb98e6914b9382864'and x['reason']=='Retained historical evidence / approved visualization interface'
    retain=not staged_extra or 'TASK-E4-G01-G03-GROWTH-RECOVERY-001'in original or rel.suffix in {'.md','.py','.yaml','.yml'}or rel.name in {'TASK_FREEZE.json','CODE_LOCK.json','SOURCE_LOCK.json'}
    (keep if retain else drop).append(x)
manifest=dict(scope='Only redundant copies newly staged by this maintenance task; original histories/worktrees unchanged',delete=[dict(path=str(R/x['new_path']),sha256=x['new_sha256'],retained_git_commit=x['source_commit'],retained_git_path=x['original_path'],reason='Redundant historical intermediate; full original remains in retained workspace and immutable Git history')for x in drop],original_worktrees_removed=[],reason_original_worktrees_retained='Contain unique scientific assets, ignored runs or explicit LOCAL_ONLY input/runtime bindings; no blanket removal')
(T/'PHASE7_DELETE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');receipts=[]
for x in drop:
    q=R/x['new_path'];assert q.is_relative_to(R/'src/ring_first_3d/mainline/lineage')and not q.is_symlink();assert hashlib.sha256(q.read_bytes()).hexdigest()==x['new_sha256'];n=q.stat().st_size;q.unlink();receipts.append(dict(path=str(q),sha256=x['new_sha256'],bytes=n,status='DELETED_NEW_REDUNDANT_STAGING_COPY',retained_commit=x['source_commit']))
v.update(files=keep,exact_copies=sum(not x['modified']for x in keep),adapted_copies=sum(x['modified']for x in keep));p.write_text(json.dumps(v,indent=2)+'\n');(R/'mainline/manifests/SOURCE_PROVENANCE.json').write_text(json.dumps(dict(files=keep,source_status='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False),indent=2)+'\n');(T/'PHASE7_CLEANUP_RECEIPTS.json').write_text(json.dumps(dict(operations=receipts,logical_bytes=sum(x['bytes']for x in receipts),important_original_assets_deleted=0),indent=2)+'\n')
print('Removed redundant newly staged historical intermediates',len(drop),'retained curated copies',len(keep))
