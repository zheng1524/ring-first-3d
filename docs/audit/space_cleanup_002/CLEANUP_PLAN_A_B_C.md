# CLEANUP PLAN A / B / C — human approval required

**Deletion executed: false.** All sizes are allocated bytes from `du`; hardlink/duplicate caveats are stated.

Current free: **4,562,894,848 bytes = 4.25 GiB**. Full audit: `DISK_SPACE_AUDIT.md`.

## Plan A — conservative

Only temporary/caches, no research results, no model weights, no Git history.

| Candidate | Allocated | Why |
|---|---:|---|
| `/tmp/dsh-workspace-changes-GGsTeP` | 2,027,819,008 | DSH temporary workspace snapshot |
| `/tmp/dsh-workspace-changes-m3e6pM` | 2,025,791,488 | DSH temporary workspace snapshot |
| `/home/liu/.cache/pip/http-v2` | 960,344,064 | pip HTTP cache |
| `/home/liu/.npm/_cacache` | 571,695,104 | npm cache |
| `/home/liu/.cache/mozilla` | 536,461,312 | browser cache |
| `/home/liu/.cache/torch` | 338,415,616 | torch download cache; verify no active load |

Expected reclaim: **6,460,526,592 bytes = 6.02 GiB**.  
Expected free after: **11.02 GB / 10.27 GiB**.

Impact: no research result or current source. `/tmp` snapshots may affect DSH undo history; close/accept that risk before deleting. Pip/npm/browser caches may need redownload. `torch` cache must be checked against HERO source lock; current HERO weights are elsewhere.

## Plan B — recommended

Plan A plus:

- 3 Git temporary packs: 984,506,368 + 380,686,336 + 114,253,824 = **1,479,446,528 bytes**;
- 11 historical worktrees under `/home/liu/ring_first_3d_*` = **11.34 GB** (see candidate rows);
- `/home/liu/research_storage_cleanup` = **820,326,400 bytes** (old cleanup archives);
- `surface_fusion_v3/vendor/open3d/...pybind...so` exact vendor duplicate = **802,250,752 bytes** (keep `.venv` copy).

Expected reclaim: **21,109,108,736 bytes = 19.66 GiB**.  
Expected free after: **25.67 GB / 23.90 GiB**.

**Preconditions for Plan B:**

1. Git temp packs: no active git/gc/repack process; verify no `.idx`/refs point to them; use Git-safe handling, not blind `rm`; do not run `git gc`/`prune` under this task.
2. Historical worktrees: confirm each is not the only copy of HERO/body/lineage source and that `assets/retained_sources` contains the needed minimum. Current code grep found no direct reference to these roots, but this is not proof.
3. `research_storage_cleanup`: verify its archives are already represented in M1/M2 evidence; it is old (2026-10-30).
4. open3d vendor duplicate: remove only the vendor copy; keep `.venv` copy; exact SHA256 confirmed.

Plan B does **not** include raw/annotation copies, HERO/DINO weights, conda envs, `.local`, or current workspace. It reaches the 20 GB target at the lower bound, but not enough for full 3-arm HERO + body peak.

## Plan C — deep, high risk

Plan B plus selected large legacy assets (not auto-approved):

- `workspace/smart_endoscope_20260805 (1)` raw/annotation copy: 4.03 GB; duplicate status **unverified**; original ZIP/tree must remain;
- MASt3R weight: 2.75 GB; historical, not current HERO checkpoint;
- `ring_first_v13_multisource`: 2.6 GB; historical; contains old weights/ROMА assets;
- conda `息肉检测`: 9.2 GB; annotation GUI uses it, but not current Ring-First `.venv`;
- `/home/liu/.local/lib` legacy Python 3.8: 5.9 GB.

Expected reclaim: **about 43.58 GiB** cumulative, expected free ~47.83 GiB, but requires separate dependency audit and a restore path. **Not recommended for automatic deletion.**

## Non-negotiable protected assets

- raw ZIPs/trees and `assets/protected_raw_data`;
- frozen DXY;
- current workspace source and `.git`;
- current `.venv`;
- MVSAnywhere HERO checkpoint, DINOv2 weights, MVS source;
- M1/M2-A/M2-B/M2-C formal tables, W0 cameras, manifests, prepared/clean data, local review.
