import pathlib,json,subprocess,csv,os,datetime,hashlib,collections,gzip
O=pathlib.Path(__file__).resolve().parent;d=json.load(open(O/'GIT_OBJECT_AUDIT.json'));rows=list(csv.DictReader(open(O/'CLONE_WORKTREE_MATRIX.csv')))
def g(r,*a):
 p=subprocess.run(['git','-C',r,*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'),timeout=120);return p.stdout.decode(errors='replace').strip()
cs={c['clone_id']:set(g(c['query_worktree'],'rev-list','--all').splitlines())for c in d['clones']}
for c in d['clones']:
 c['unique_ref_reachable_commit_SHAs']=sorted(cs[c['clone_id']]-set().union(*(v for k,v in cs.items()if k!=c['clone_id'])));c['unique_ref_reachable_commit_count']=len(c['unique_ref_reachable_commit_SHAs'])
 remote={}
 for rr in c.get('live_remotes',{}).values():
  if rr['rc']==0:remote.update({a[1]:a[0]for s in rr['refs'].splitlines()if len(a:=s.split())==2})
 c['live_branch_publication']={b:dict(local_tip=g(c['query_worktree'],'rev-parse','refs/heads/'+b),remote_tip=remote.get('refs/heads/'+b),status='REMOTE_UNVERIFIED'if not remote else'BRANCH_NAME_ABSENT_ON_LIVE_REMOTE'if 'refs/heads/'+b not in remote else'EXACT_TIP_EQUAL'if remote['refs/heads/'+b]==g(c['query_worktree'],'rev-parse','refs/heads/'+b)else'BRANCH_TIP_DIFFERS_NEEDS_ANCESTRY')for b in c['branches_not_in_local_remote_tracking_refs']}
 for r in rows:
  if r.get('common_dir')==c['common_dir']:
   r['clone_owner']=c['owner'];r['clone_id']=c['clone_id'];r['unique_ref_reachable_commits_clone']=c['unique_ref_reachable_commit_count'];r['alternate_object_dependency']=c['alternates']or''
 # exact filesystem existence of every registered worktree; detects nonmatching names/prunable absent dirs.
 wt=[]
 for block in c['worktree_porcelain'].split('\n\n'):
  z={}
  for s in block.splitlines():
   k,_,v=s.partition(' ');z[k]=v or True
  if 'worktree'in z:z['filesystem_exists']=pathlib.Path(z['worktree']).exists();wt.append(z)
 c['registered_worktree_filesystem_checks']=wt
json.dump(d,open(O/'GIT_OBJECT_AUDIT.json','w'),ensure_ascii=False,indent=2)
fields=list(dict.fromkeys(k for r in rows for k in r))
with open(O/'CLONE_WORKTREE_MATRIX.csv','w')as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
lines=['flowchart LR']
for c in d['clones']:
 lines.append(f'  {c["clone_id"]}["{c["clone_id"]}: {c["owner"]} ({len(c["worktrees"])} worktrees)"]')
 for i,w in enumerate(c['worktrees']):lines.append(f'  {c["clone_id"]} --- {c["clone_id"]}_W{i}["{w}"]')
 if c['alternates']:
  target=next((x['clone_id']for x in d['clones']if x['objects']==c['alternates'].strip()),None)
  if target:lines.append(f'  {c["clone_id"]} -->|"objects/info/alternates: borrowed objects"| {target}')
(O/'GIT_RELATIONSHIPS.mmd').write_text('\n'.join(lines)+'\n')
# Independent evidence samples: recompute current bytes, no copied payloads.
paths=[pathlib.Path('/home/liu/ring_first_3d_growth_recovery/experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001')/p for p in ['code/evaluate.py','metrics/BODY_METRICS.csv','TECHNICAL_REPORT.md','RESULT_CARD.md']]
paths += [pathlib.Path('/home/liu/ring_first_3d_e3_sdf_full/experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001/metrics/single_M0_TRAINING.csv'),pathlib.Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001/TECHNICAL_REPORT.md')]
samples=[]
for p in paths:
 s=p.stat();h=hashlib.sha256(p.read_bytes()).hexdigest();samples.append(dict(path=str(p),sha256=h,hash_status='HASH_RECOMPUTED',size=s.st_size,mtime_ns=s.st_mtime_ns))
findings=[dict(id='IR-001',severity='CRITICAL',result='REJECT',claim='Immediate retirement/move of nested old clone B',evidence='harness objects/info/alternates directly points at B/objects; 15536 accessible objects are not physically stored in harness.',remedy='Keep B at current path. Future separate authorized migration must materialize and validate complete object closure before alternate removal.'),dict(id='IR-002',severity='HIGH',result='REJECT',claim='Retire dirty worktrees or old polyp project',evidence='19 tracked modifications across four roots; untracked and ignored source/results/checkpoints remain.',remedy='Preserve snapshot, provenance, owner review, and recovery test before any proposal.'),dict(id='IR-003',severity='HIGH',result='NEEDS_MORE_EVIDENCE',claim='Retire clean historical worktrees merely because commits are pushed',evidence='All historical working trees contain ignored scientific assets except harness_main_ready; clean status is not unique-asset absence.',remedy='Per-asset hash/dependency closure, external data rebinding and cold archive restore validation required.'),dict(id='IR-004',severity='HIGH',result='NEEDS_MORE_EVIDENCE',claim='Mother polyp repository is fully synchronized',evidence='ls-remote returned128; remote live state unverified, local tracking refs insufficient.',remedy='Read-only remote access repair and later tip/ancestry verification.'),dict(id='IR-005',severity='HIGH',result='REJECT',claim='MAE improvement proves 3D world placement and all geometric metrics improve',evidence='Different SE3 frames; G01 MAE improves only independent frame while fixed frame worsens, Fscore and coverage also decrease.',remedy='Keep all protocols separate and paired on fixed denominators.'),dict(id='IR-006',severity='MEDIUM',result='ACCEPT',claim='Sampled existing hardlinks have identical bytes and must be counted once',evidence='16 actual same-inode pairs have recomputed SHA256 equality.',remedy='No deletion authorization; no new disk savings claimed.'),dict(id='IR-007',severity='HIGH',result='REJECT',claim='Delete unreferenced/dangling objects or LFS as cache',evidence='All five fsck checks returned0 but unreferenced physical objects exist; no audit of their scientific content establishes disposability.',remedy='Retain exact stores including refs/reflogs and dangling material.'),dict(id='IR-008',severity='MEDIUM',result='NEEDS_MORE_EVIDENCE',claim='Retire empty clean harness_main_ready worktree',evidence='Snapshot status has0 tracked changes,0 untracked,0 ignored, yet global absolute-path and recovery closure still required.',remedy='Potential candidate after full dependency check; current task authorizes no retirement.').copy()]
checks=dict(review_role='Independent second agent; observed metadata and evidence directly. Parent conclusions not treated as facts.',audit_time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),read_only_scope=True,source_writes=[],allowed_writes=str(O),git_mutation_exception='Parent created one audit worktree/branch before scan. This reviewer only reads Git metadata; no fetch/gc/prune/repack performed.',git_roots_records=len(rows),actual_project_and_external_roots=sum(not bool(r.get('nested_nonrepository_directory'))for r in rows),clones=len(d['clones']),clone_summary=[{k:c[k]for k in ['clone_id','owner','common_dir','objects','alternates','git_storage','physically_stored_object_count','accessible_but_not_physically_stored_here_count','physical_unique_object_count','physical_unique_object_representation_bytes','unique_ref_reachable_commit_count','reachable_only_via_reflog_count','physical_objects_not_refs_or_reflogs_count','fsck_rc']}for c in d['clones']],dirty_roots=[dict(path=r['path'],tracked_changes=r.get('tracked_changes'),untracked=r.get('untracked'),ignored=r.get('ignored'))for r in rows if r.get('dirty')=='True'],independent_hash_samples=samples,findings=findings,review_status='INDEPENDENT_OBSERVATIONS_COMPLETE; parent final package challenge pending',limitations=['No source retirement approved.','Hash sample confirms only listed pairs, not whole asset inventory.','Remote ancestry for absent local remote objects cannot be established without fetch; no fetch permitted by read-only-source approach.','Objectsize disk representation bytes cannot be interpreted as reclaimable pack allocation.','Global unique-assets claims require parent inventory cross-check, not filename comparisons.'])
json.dump(checks,open(O/'INDEPENDENT_CHECKS.json','w'),ensure_ascii=False,indent=2)
text='''# Independent forensic observations — second agent

This reviewer collected Git metadata, file identities and metric source evidence directly. No deletion, migration, training, fetch, gc, prune, repack or scientific code change was performed. The only expected new Git registration is the parent-created audit branch/worktree. This is an independent challenge report, not permission to retire assets.

## Git relationship verified

Three main-project object stores are A=`/home/liu/ring_first_3d/.git`, B=`/home/liu/polyp_research/ring-first-3d/.git`, C=`/home/liu/ring_first_3d_harness/.git`. A has39 working trees, B has1, C has15 including mainline/audit. **C borrows B through objects/info/alternates. They are not three self-contained clones.** C accesses15,536 objects absent from its own physical store. B cannot be retired or relocated while that binding remains.

The mother `/home/liu/polyp_research/.git` and independent `/home/liu/ring-first-hero-core/.git` are two additional stores. Vendor Git repositories and independent DXY are recorded separately as external dependencies, not mainline clone consolidation candidates. All five main scans passed `git fsck --full --no-reflogs --unreachable` (exit0), with unreferenced objects retained. No detached heads were observed in the54 project worktrees. Exact maps, refs, reflogs, physically-local versus alternate objects, pack hashes and live remote results are in GIT_OBJECT_AUDIT.json; worktree-file lists retain untracked and ignored paths.

## Protected working state

There are19 tracked local modifications across four roots: mother polyp14, e3_sdf_full3, e3_sdf_multi1, structural_update1. There are also untracked scientific source/results and ignored predictions/checkpoints. Particularly e4_sdf_localization has6,257 untracked and94,941 ignored entries at collection time. These are evidence, not garbage. The audit worktree's growing untracked outputs are an expected mutable exception. Mother polyp live remote access failed128, so synchronization is UNKNOWN, despite no local-tracking-only commits. Other queried remotes were readable. New audit branch name may be absent remotely even when its starting commit already exists there; branch publication and commit reachability are separate fields.

## Duplicates and unique assets

Sixteen same-inode pairs were independently hashed; all pairs match. Disk allocation must count their inode once. This does not authorize deleting either path, since references may depend on both. Physical per-store objects were enumerated using own pack indices and loose files, avoiding alternate double-counting. Object representation-byte totals are not pack-reclaim estimates. No unique-asset absence is inferred from clean Git status.

## Metric challenge verified at source

Growth evaluate.py independently samples12,000 points in each direction with seeds20261117/20261118 and computes point-to-triangle distances. Independent per-model scale-fixed SE3 alignment and fixed INITIAL-to-GT alignment answer different questions. G01 ITERATION_024 to RECOVERY: independent Chamfer MAE0.334905749→0.303622948mm, fixed-frame MAE0.335971902→0.356987893mm. Fscore@0.5mm0.906155464→0.887551678 and GT coverage0.865833333→0.854083333 worsen. Shape-average improvement alone cannot justify world-location improvement, universal geometric improvement or G03 acceptance. No history was recalculated.

## Retirement decisions

'''
for f in findings:text+=f"- **{f['id']} {f['result']}** — {f['claim']}. {f['evidence']} {f['remedy']}\n\n"
text+='''## Limits / pending review

The full parent audit package still needs direct challenge once produced. Hash sampling is not a substitute for the complete asset inventory. No retirement is approved for execution. Keep unresolved evidence and disagreements explicitly; do not convert NEEDS_MORE_EVIDENCE to acceptance. Original current working-tree snapshots, source files and metrics are linked by recomputed hashes in INDEPENDENT_CHECKS.json.
'''
(O/'INDEPENDENT_FINDINGS.md').write_text(text)
print('FINAL INDEPENDENT',len(rows),len(d['clones']),len(findings),'packmatches',len(d['pack_comparison']))
print([(c['clone_id'],c['unique_ref_reachable_commit_count'])for c in d['clones']])
