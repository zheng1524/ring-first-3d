# M2A_FINAL_REPORT — W0 Observability, RGB Graph Connectivity & Geometric Visual Audit

**Task:** `TASK-M2A-W0-OBSERVABILITY-GRAPH-RECOVERY-001`
**Base:** `45e19c440c9c72efd5f5acf73851bf9909fb45ee` (M1 final)
**Implementation commit:** `c6f60917aa8532e198afaefca83cca137470af48`
**Branch:** `exp/TASK-M2A-W0-OBSERVABILITY-GRAPH-RECOVERY-001`
**Output:** `runs/m2a_w0_recovery/`
**M1 `runs/m1_final_39/` is preserved untouched.**

## 0. Result at a glance

```text
M2A_ENGINEERING_PASS = true
W0_GENERATED         = 78/79
W0_FULL              = 67/79
W0_PARTIAL           = 11
W0_NOT_COMPUTABLE    = 1
IMPLEMENTATION_ERRORS = 0
J2_USED              = false
HUMAN_REVIEW         = PENDING (no human approval claimed)
```

| Metric | Baseline M1 | M2A |
|---|---:|---:|
| W0 generated | 64 | **78** |
| Full W0 | 64 | **67** |
| Partial W0 | 0 | **11** |
| Not computable | 15 | **1** |
| W0 poses | 640 | **753** |
| ACCEPT | 57 | **61** |
| QUARANTINE | 210 | **221** |
| INSUFFICIENT_EVIDENCE | 373 | **471** |
| REJECT | 0 | 0 |
| Videos with >=1 ACCEPT | 22 | **24** |

The single unrecovered video is `GP_Is_18.0mm_closed_R5_single_refY/005`: all 10 registered frames have `q_train=0`; no real Ring boundary survives the polyp-adjacency filter, and no raw-video replacement frame with `q_train>=20` was found. It is `NOT_COMPUTABLE`, not an implementation error.

---

## Q1. 4 段 Ring 失败视频，每段多少帧不足 20 点？

All four videos have 10 registered frames.

| group / video | OK (q>=20) | insufficient | q=0 frames | q range |
|---|---:|---:|---:|---:|
| `GP_IIa_14.0mm_closed_R5_single_refY/005` | **6/10** | 4 | 3 | 0–98 |
| `GP_IIa_22.0mm_closed_R5_single_refY/004` | **9/10** | 1 | 1 | 0–121 |
| `GP_IIa_22.0mm_closed_R5_single_refY/005` | **3/10** | 7 | 5 | 0–31 |
| `GP_Is_18.0mm_closed_R5_single_refY/005` | **0/10** | 10 | 10 | 0–0 |

Per-frame rows are in `RING_FRAME_DIAGNOSTICS.csv` (40 rows). DXY inner/outer points exist in most failed frames (e.g. 1452/2432 inner/outer points for the Is_18 video), but the frozen raw-boundary filter removes all of them near the polyp. This is an observation-availability failure, not a missing image.

## Q2. 跳过/替换无效帧后恢复了多少 W0？

| Video | Strategy | New W0 poses | Result |
|---|---|---:|---|
| `GP_IIa_22...R5/004` | B1: keep 9 q>=20 frames | 9 | partial |
| `GP_IIa_14...R5/005` | B1 failed → C3B largest component (5) | 5 | partial |
| `GP_IIa_22...R5/005` | B1 failed → B1R two real ring-visible bridge frames (5 total) | 5 | partial |
| `GP_Is_18...R5/005` | replacement search: no q>=20 real frame | 0 | **not computable** |

3/4 Ring-failed videos now have W0; none is `FULL` because the original 10-frame set cannot be fully recovered from the registered frames.

## Q3. J2 是否被复用？

**No. `J2_USED=false`; `J2_APPLICABILITY=J2_NOT_APPLICABLE`; `J2_RESULT=NOT_RUN`.**

Reasons are recorded in `J2_REUSE_RECORD.json`:

1. The corrected J2 report says J2 is slightly worse than B0 on inner/outer/raw/held metrics and was `nfev=60, success=False`.
2. `j2_obs_correct.py` hardcodes `R_CAD=5.6, r_CAD=0.6`; it is not R5-compatible.
3. J2 consumes `inner_pts/vis` observations; it does not provide a Ring-First initialization path for `q_train=0` videos.
4. B1/B1R/C1/C3/C2/C2B recovered 14/15 failed videos without J2.
5. No J2 weight, threshold, or barrier was tuned; no J2 improvement is claimed.

The J2 source hash is in `J2_REUSE_RECORD.json`. If a future R5-adapter and a q_train=0 initialization route are developed, J2 can be revisited as B2 under a separate controlled experiment.

## Q4. 11 段图不连通视频原来各有几个分量？

C0 is the frozen `pair_offsets=[1,2,4]` `pair_data` graph (held filtering + >=12 rows).

| group / video | C0 components | C0 sizes |
|---|---:|---|
| `GP_IIa_14...R5/004` | 3 | 8,1,1 |
| `GP_Ip_2.9...R10/005` | 2 | 9,1 |
| `GP_Ip_2.9...R5/005` | 4 | 6,2,1,1 |
| `GP_Ip_4.0...R5/006` | 3 | 8,1,1 |
| `GP_Ip_6.2...R5/005` | 2 | 6,4 |
| `GP_Is_10.5...R5/005` | 2 | 8,2 |
| `GP_Is_18...R10/005` | 4 | 4,4,1,1 |
| `GP_Is_4.8...R5/004` | 2 | 6,4 |
| `GP_Is_4.8...R5/005` | 3 | 8,1,1 |
| `GP_Is_7.0...R5/005` | 4 | 7,1,1,1 |
| `GP_Is_9.79...R10/004` | 4 | 4,3,2,1 |

## Q5. 增加 RGB 匹配后修复了多少连接？

C1 tried all 45 frame pairs. Raw MAGSAC edges increased, but the **actual `pair_data` graph** (held + >=12 track rows) is stricter:

| group / video | C1 actual components | sizes |
|---|---:|---|
| `GP_IIa_14...R5/004` | 3 | 8,1,1 |
| `GP_Ip_2.9...R10/005` | 2 | 9,1 |
| `GP_Ip_2.9...R5/005` | 4 | 6,2,1,1 |
| `GP_Ip_4.0...R5/006` | 2 | 8,2 |
| `GP_Ip_6.2...R5/005` | **1** | **10** |
| `GP_Is_10.5...R5/005` | 2 | 9,1 |
| `GP_Is_18...R10/005` | 3 | 8,1,1 |
| `GP_Is_4.8...R5/004` | 2 | 6,4 |
| `GP_Is_4.8...R5/005` | 2 | 8,2 |
| `GP_Is_7.0...R5/005` | 5 | 6,1,1,1,1 |
| `GP_Is_9.79...R10/004` | 3 | 7,2,1 |

C1 alone fully connected **1/11** (`GP_Ip_6.2...R5/005`). C3 then recovered the largest real component for 8 videos; C2/C2B added real bridge frames for the remaining two. Overall **11/11 graph-failed videos have W0**, but only 3 are full (C1, C2, C2B) and 8 are partial (C3).

## Q6. 补充真实桥接帧后恢复情况

| Video | Method | Bridge frames | W0 poses | Result |
|---|---|---:|---:|---|
| `GP_Is_10.5...R5/005` | C2B | `raw20, raw546, raw771` (3) | 13 | full, limited |
| `GP_Is_9.79...R10/004` | C2 | 2 real frames | 12 | full, limited |
| `GP_IIa_22...R5/005` | B1R | 2 real ring-visible frames | 5 | partial |

C2B's bridge chain was verified by real RGB matches: `20–546=15`, `546–771=13`, `771–component=33` inliers. No synthetic frames were used.

## Q7. 新方法有没有让原来成功的视频退化？

**No observed baseline degradation.** Recovery was applied only to videos with baseline `w0_generated=false`; all 64 baseline-success rows keep their original W0 poses, admission counts and metrics. This is checked in the merge table (`recovery_method=BASELINE`, `new_w0_poses == baseline_w0_poses`).

The global W0 count increases from 64 to 78; full from 64 to 67; partial adds 11; one remains not computable.

## Q8. 自动状态与可视化是否一致？

Auto status: **24 AUTO_ACCEPTED, 54 AUTO_LIMITED, 1 AUTO_INSUFFICIENT**, all with `HUMAN_REVIEW_PENDING`.

The visual audit shows the intended four classes:

- success: G03/005 and R5 `GP_Ip_10.3/005`;
- limited but numerically valid: C3/C3B/B1R partials;
- failure: `GP_Is_18...R5/005` no W0;
- ACCEPT but trajectory-suspicious: `GP_Ip_20...R10/004` (119.4° adjacent rotation, 3 ACCEPT).

The 3D plots show large branch jumps (median 2 per video, max 173.2°). **A visually good ring overlay does not prove a good 3D pose**; the Ring symmetry and branch jumps require joint review. No `HUMAN_APPROVED` is claimed; `HUMAN_REVIEW_TEMPLATE.csv` is provided.

## Q9. 哪几张图最能说明成功/失败？

Highest priority: `visualization/F_summary/representative_contact_sheet.png` (six real cases, RGB + CAD overlay + 3D + metrics/status).

- Success: `visualization/D_ring_projection/accepted/...GP_Ip_20...005...png`, `.../GP_Ip_10.3...005...png`; `visualization/E_camera_3d/accepted/...`.
- Failure: `visualization/D_ring_projection/failed/GP_Is_18...005...png` (ring mask without W0).
- ACCEPT-but-branch: `visualization/E_camera_3d/branch_risk/GP_Ip_20...004.png`.
- Graph recovery: `visualization/C_pose_graph/C1/GP_Is_10.5...005.png` (9+1 before C2B) and `C2B/...` (13 connected).
- Limited recovery: `visualization/E_camera_3d/quarantine/...` for C3B/C2B.

All 38 PNGs are under `runs/m2a_w0_recovery/visualization/` and in the evidence zip.

## Q10. 是否可以开始正式跨视频联合选帧与二维身份？

**Yes, with a restricted anchor set.** M2 can start:

- 78 videos have numerically valid W0; 67 are full and 11 partial.
- 24 videos have >=1 ACCEPT camera; 54 are limited; 1 has no W0.
- Recommended first M2 subset: R10 full-videos with both sides accepted (e.g. `GP_Ip_20...R10` 004/005, `GP_Is_14...R10` 004/005, `GP_Ip_5.6...R10` 004/005, `GP_Ip_6.4...R10` 005/006).
- Use `camera_result.npz` (all cameras + `admission_status`) and `RUN_MANIFEST.json`, not only `accepted_cameras.npz`.
- Treat 11 partial W0 as local/diagnostic only; do not treat partial counts as full recovery.
- Treat branch-jump videos as branch-risk; select a coherent branch in M2, not a concatenation of all cameras.
- Do not start H/Joint BA until M2 view selection and 2D identity are frozen.

---

## Engineering and evidence

### Fixed evaluation issue

M1 `positive_depth_fraction` checked whether the world origin was in front of the camera. M2A adds a real point-based diagnostic (`POSITIVE_DEPTH_DIAGNOSTICS.csv`):

- 78/78 W0 files have finite `points` and `c2w`;
- all 78 have `positive_depth_points_fraction = 1.0`;
- source fraction min 0.9935; target fraction min 0.9231;
- max |new - old world-origin| = 0.0769.

The old M1 field is retained unchanged; the new diagnostic is separate.

### Method comparison

| method | attempts | W0 | full | partial | not computable | ACCEPT |
|---|---:|---:|---:|---:|---:|---:|
| BASELINE | 79 | 64 | 64 | 0 | 15 | 57 |
| B1 | 3 | 1 | 0 | 1 | 2 | 0 |
| B1R | 1 | 1 | 0 | 1 | 0 | 0 |
| C1 | 11 | 1 | 1 | 0 | 10 | 3 |
| C3 | 10 | 8 | 0 | 8 | 2 | 1 |
| C3B | 1 | 1 | 0 | 1 | 0 | 0 |
| C2 | 2 | 1 | 1 | 0 | 1 | 0 |
| C2B | 1 | 1 | 1 | 0 | 0 | 0 |

### Tests and regression

- M2A artifact contract: 4 PASS.
- `tests/test_m1_39_inputs.py`, `test_ring_cad_r10_r5.py`, `test_m1_runner_status.py`, `test_m1_prepared_contract.py`, `test_w0_manifest_closure.py`: all PASS.
- Default M1 G03/005 regression after adding optional `pair_offsets`: 16/16 ACCEPT; 0.828765/0.980167/3.209369, unchanged.
- `IMPLEMENTATION_ERRORS.csv` has only the header.

### Evidence

- `RING_FRAME_DIAGNOSTICS.csv` (40 frames)
- `POSE_GRAPH_DIAGNOSTICS.csv` / `POSE_GRAPH_EDGES.csv` / `ACTUAL_GRAPH_COMPONENTS.csv`
- `W0_79_VIDEO_RESULTS.csv` (79 rows) / `W0_39_GROUP_SUMMARY.csv` (39 rows)
- `METHOD_COMPARISON.csv`
- `VALIDATION_39.json`
- `POSITIVE_DEPTH_DIAGNOSTICS.csv`
- `J2_REUSE_RECORD.json`
- `HUMAN_REVIEW_TEMPLATE.csv`
- `visualization/` (38 PNGs, including the contact sheet)
- `M2A_W0_RECOVERY_EVIDENCE.zip` (12.3 MB) + SHA256 in `M2A_W0_RECOVERY_EVIDENCE.sha256`

`cross_group_contamination=0` was actually checked across 97 prepared manifests. `undeclared_dependencies` is recorded as declared for the modules used (native camera, unified camera, track005, local_ring_sfm, features019, dxy_mid) and `NOT_AUDITED` outside the M2A scope; it is not silently written as zero.
