# Independent forensic observations — second agent

This reviewer collected Git metadata, file identities and metric source evidence directly. No deletion, migration, training, fetch, gc, prune, repack or scientific code change was performed. The only expected new Git registration is the parent-created audit branch/worktree. This is an independent challenge report, not permission to retire assets.

## Git relationship verified

Three main-project object stores are A=`/home/liu/ring_first_3d/.git`, B=`/home/liu/polyp_research/ring-first-3d/.git`, C=`/home/liu/ring_first_3d_harness/.git`. A has39 working trees, B has1, C has15 including mainline/audit. **C borrows B through objects/info/alternates. They are not three self-contained clones.** C accesses15,536 objects absent from its own physical store. B cannot be retired or relocated while that binding remains.

The mother `/home/liu/polyp_research/.git` and independent `/home/liu/ring-first-hero-core/.git` are two additional stores. Vendor Git repositories and independent DXY are recorded separately as external dependencies, not mainline clone consolidation candidates. All five main scans passed `git fsck --full --no-reflogs --unreachable` (exit0), with unreferenced objects retained. No detached heads were observed in the55 project worktrees. Exact maps, refs, reflogs, physically-local versus alternate objects, pack hashes and live remote results are in GIT_OBJECT_AUDIT.json; worktree-file lists retain untracked and ignored paths.

## Protected working state

There are19 tracked local modifications across four roots: mother polyp14, e3_sdf_full3, e3_sdf_multi1, structural_update1. There are also untracked scientific source/results and ignored predictions/checkpoints. Particularly e4_sdf_localization has6,257 untracked and94,941 ignored entries at collection time. These are evidence, not garbage. The audit worktree's growing untracked outputs are an expected mutable exception. Mother polyp live remote access failed128, so synchronization is UNKNOWN, despite no local-tracking-only commits. Other queried remotes were readable. New audit branch name may be absent remotely even when its starting commit already exists there; branch publication and commit reachability are separate fields.

## Duplicates and unique assets

Sixteen same-inode pairs were independently hashed; all pairs match. Disk allocation must count their inode once. This does not authorize deleting either path, since references may depend on both. Physical per-store objects were enumerated using own pack indices and loose files, avoiding alternate double-counting. Object representation-byte totals are not pack-reclaim estimates. No unique-asset absence is inferred from clean Git status.

## Metric challenge verified at source

Growth evaluate.py independently samples12,000 points in each direction with seeds20261117/20261118 and computes point-to-triangle distances. Independent per-model scale-fixed SE3 alignment and fixed INITIAL-to-GT alignment answer different questions. G01 ITERATION_024 to RECOVERY: independent Chamfer MAE0.334905749→0.303622948mm, fixed-frame MAE0.335971902→0.356987893mm. Fscore@0.5mm0.906155464→0.887551678 and GT coverage0.865833333→0.854083333 worsen. Shape-average improvement alone cannot justify world-location improvement, universal geometric improvement or G03 acceptance. No history was recalculated.

## Retirement decisions

- **IR-001 REJECT** — Immediate retirement/move of nested old clone B. harness objects/info/alternates directly points at B/objects; 15536 accessible objects are not physically stored in harness. Keep B at current path. Future separate authorized migration must materialize and validate complete object closure before alternate removal.

- **IR-002 REJECT** — Retire dirty worktrees or old polyp project. 19 tracked modifications across four roots; untracked and ignored source/results/checkpoints remain. Preserve snapshot, provenance, owner review, and recovery test before any proposal.

- **IR-003 NEEDS_MORE_EVIDENCE** — Retire clean historical worktrees merely because commits are pushed. All historical working trees contain ignored scientific assets except harness_main_ready; clean status is not unique-asset absence. Per-asset hash/dependency closure, external data rebinding and cold archive restore validation required.

- **IR-004 NEEDS_MORE_EVIDENCE** — Mother polyp repository is fully synchronized. ls-remote returned128; remote live state unverified, local tracking refs insufficient. Read-only remote access repair and later tip/ancestry verification.

- **IR-005 REJECT** — MAE improvement proves 3D world placement and all geometric metrics improve. Different SE3 frames; G01 MAE improves only independent frame while fixed frame worsens, Fscore and coverage also decrease. Keep all protocols separate and paired on fixed denominators.

- **IR-006 ACCEPT** — Sampled existing hardlinks have identical bytes and must be counted once. 16 actual same-inode pairs have recomputed SHA256 equality. No deletion authorization; no new disk savings claimed.

- **IR-007 REJECT** — Delete unreferenced/dangling objects or LFS as cache. All five fsck checks returned0 but unreferenced physical objects exist; no audit of their scientific content establishes disposability. Retain exact stores including refs/reflogs and dangling material.

- **IR-008 NEEDS_MORE_EVIDENCE** — Retire empty clean harness_main_ready worktree. Snapshot status has0 tracked changes,0 untracked,0 ignored, yet global absolute-path and recovery closure still required. Potential candidate after full dependency check; current task authorizes no retirement.

## Limits / pending review

The full parent audit package still needs direct challenge once produced. Hash sampling is not a substitute for the complete asset inventory. No retirement is approved for execution. Keep unresolved evidence and disagreements explicitly; do not convert NEEDS_MORE_EVIDENCE to acceptance. Original current working-tree snapshots, source files and metrics are linked by recomputed hashes in INDEPENDENT_CHECKS.json.

## Direct parent inventory challenge (second pass)

32 sampled regular files (16 inherited current-scan inode hashes and16 recomputed rows) independently match SHA256 and stat identities. This sample does not certify every file.

- **IR-009 REJECT_PENDING_FIX** — SYMLINKS.csv.gz is complete. Independent SQLite query finds53263 symlinks but first export has0 entries: WHERE kind="symlink" resolves right side as existing symlink column in SQLite. Export with parameterized value or single-quoted SQL string; retain finding and corrected count.

- **IR-010 NEEDS_MORE_EVIDENCE** — Extension-based value labels certify raw origin or global uniqueness. category() labels all blend/video UNIQUE_RAW_DATA and pt/ckpt UNIQUE_MODEL_WEIGHT without source-role proof; may include synthetic scenes and repeated checkpoints. Mark classification as conservative protection heuristic, not semantic or uniqueness certification. Unknown stays preserved.

