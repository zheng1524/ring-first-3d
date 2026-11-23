# M2B_FINAL_REPORT — Correct Ring Observation Semantics & Global Branch Audit

**Task:** `TASK-M2B-RING-OBSERVATION-AND-GLOBAL-BRANCH-001`
**Base:** `aff1d40f885f27cfc9d07ee661e7dabd215e0f2b` (M2-A)
**Branch:** `exp/TASK-M2B-RING-OBSERVATION-AND-GLOBAL-BRANCH-001`
**Implementation commit:** `de5b8fa84bfb9c9ce95e2741332606abf6508ab0`
**Output:** `runs/m2b_ring_global_branch/`
**DXY frozen read:** `75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`

## 0. Result at a glance

```text
M2B_ENGINEERING_PASS       = true
RING_OBSERVATION_FIXED     = true
W0_GENERATED               = 79/79
W0_FULL                    = 69
W0_PARTIAL                 = 10
W0_NOT_COMPUTABLE          = 0
W0_POSES                   = 766
ACCEPT                     = 72
QUARANTINE                 = 274
INSUFFICIENT_EVIDENCE      = 420
REJECT                     = 0
IMPLEMENTATION_ERRORS      = 0
G03_A1_MAX_ADJ_ROTATION    = 2.276 deg  (A0 was 119.365 deg)
GLOBAL_BRANCH_UNIVERSAL    = false      (A2 controlled on G03 only)
HUMAN_REVIEW               = PENDING
```

| Metric | M2-A | M2-B |
|---|---:|---:|
| W0 generated | 78 | **79** |
| FULL | 67 | **69** |
| PARTIAL | 11 | **10** |
| NOT_COMPUTABLE | 1 | **0** |
| W0 poses | 753 | **766** |
| ACCEPT | 61 | **72** |
| QUARANTINE | 221 | **274** |
| INSUFFICIENT | 471 | **420** |
| REJECT | 0 | 0 |

R10: 44/44 W0, 40 FULL / 4 PARTIAL, 40 ACCEPT. R5: 35/35 W0, 29 FULL / 6 PARTIAL, 32 ACCEPT.

---

## A. Ring observation semantics

### A.1 DXY distinction, read directly from the frozen source

`observable_boundary.py::observable_P` rejects a **polyp** boundary pixel when its 3x3 neighborhood actually contains Ring mask (`actual_ring_contacts_original_polyp_pixel_boundary`). That is correct for DXY's polyp-size measurement: a Ring-occluded polyp edge is not an observed free polyp edge.

It is **not** a rule that Ring boundary points near a polyp are invalid for camera estimation. M2-A applied that rule to `observe()`:

```python
near = cv2.dilate(pm, ...)
unknown = near[ix[:,1], ix[:,0]]
q_train = sample(bd[~unknown], 128)
```

This systematically deleted Ring boundary observations exactly where the Ring contacts the polyp. M2-B changes the default to `ring_mode='all'`; the old behavior is retained only as `ring_mode='legacy'` for A0 controls.

### A.2 R0 → R1 on the four known videos

| Video | R0 OK frames | R1 OK frames | R0 mean q | R1 mean q |
|---|---:|---:|---:|---:|
| `GP_IIa_14...R5/005` | 6/10 | **10/10** | 33.0 | 128.0 |
| `GP_IIa_22...R5/004` | 9/10 | **10/10** | 79.4 | 128.0 |
| `GP_IIa_22...R5/005` | 3/10 | **10/10** | 11.8 | 128.0 |
| `GP_Is_18...R5/005` | **0/10** | **10/10** | 0.0 | 128.0 |

All 40 frames now have 128 sampled real Ring boundary points. `ring_boundary_contact_polyp` and `ring_boundary_contact_background` are retained as diagnostics, never as exclusion rules. `unknown_boundary` remains only as a diagnostic field.

The sampling function is unchanged from the frozen implementation; it is deterministic and never duplicates points or uses CAD points as observations. The full boundary count and sampled count are both recorded.

### A.3 What changed after R1

| Video | R1 W0 | R1 ACCEPT | Ring MAE | Held median | Held P95 | Max adjacent rot |
|---|---:|---:|---:|---:|---:|---:|
| `GP_IIa_14...R5/005` | 10 | 0 | 1.079 | 1.032 | 3.297 | 7.20° |
| `GP_IIa_22...R5/004` | 10 | **3** | 1.685 | 2.507 | 10.711 | 10.28° |
| `GP_IIa_22...R5/005` | 10 | **1** | 2.113 | 2.140 | 8.247 | 15.58° |
| `GP_Is_18...R5/005` | 10 | 0 | 1.218 | **23.183** | **77.598** | 54.98° |

`Is_18/005` is no longer `INSUFFICIENT_RING_OBSERVATION`: it has 10 real Ring observations and a 10-pose W0. It is still not accepted because its held RGB evidence is poor (`HELD_TRACKS` mostly 9–19; Held median 23.2 px, P95 77.6 px). The new failure reason is RGB/held evidence, not missing Ring.

`IIa_14/005` is the opposite diagnostic class: Ring MAE 1.08, Held median 1.03, but 0 ACCEPT; its held track counts are below 20. It is a candidate for `GEOMETRY_GOOD_EVIDENCE_LIMITED`, pending human review.

No R5/R10 CAD size or inner/outer contour identity assumption was changed. CAD identity is assigned by contour area, not by array index.

---

## B. G03 branch consistency

### B.1 Controlled A0 / A1 / A2

A0 = M2-A W0; A1 = R1 Ring + existing init/BA; A2 = R1 Ring + discrete global branch selection + existing BA.

| Video | Method | W0 | ACCEPT | Ring MAE | Held med | Held P95 | Max adj rot | Max adj trans | jumps |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G03/004 | A0 M2A | 10 | 3 | 1.441 | 1.321 | 6.096 | **119.365°** | 87.147 mm | 4 |
| G03/004 | A1 Ring | 10 | 0 | 2.927 | **1.527** | **6.022** | **2.276°** | 9.632 mm | 4 |
| G03/004 | A2 Global | 10 | 3 | 1.837 | 3.290 | 9.572 | 7.409° | 7.061 mm | 3 |
| G03/005 | A0 M2A | 10 | 6 | 0.519 | 0.921 | 3.230 | 1.842° | 8.223 mm | 4 |
| G03/005 | A1 Ring | 10 | 6 | 0.755 | **0.857** | **3.355** | 1.743° | 8.530 mm | 4 |
| G03/005 | A2 Global | 10 | 3 | 2.557 | 1.169 | 4.386 | 1.784° | 10.090 mm | 4 |

**A1 fixes the 119.365° jump to 2.276°.** It also keeps the best Held median/P95 on G03/004 (1.527/6.022) and preserves G03/005 at 6 ACCEPT. A2 is a real global search and reaches 3 ACCEPT on G03/004, but its Held median/P95 (3.290/9.572) and max rotation (7.409°) are worse than A1. Therefore **A1, not A2, is the selected final G03 result**. This is a geometric-quality decision, not an ACCEPT-count decision.

### B.2 Global candidate selection, not hand-picked branches

`GLOBAL_BRANCH_CANDIDATES.csv` and `GLOBAL_BRANCH_SELECTION.csv` record every candidate, Ring error, initial candidate, selected candidate, and total energy. The selection uses:

- all real Ring candidates generated by the frozen `recover` path;
- all real RGB graph edges from `pair_data`, including non-adjacent pairs;
- a temporal consistency term based on actual raw-frame gaps;
- discrete coordinate descent over the whole trajectory;
- the existing frozen BA for continuous refinement (no independent BA was written).

On G03/004 the discrete search changed 3 candidates; on G03/005 it changed 5. A2 energy was lower than the A1 assignment in both cases, but lower discrete energy did **not** imply better held-out RGB; this is reported, not hidden.

### B.3 Important limitation

**A2 was not applied to all 79 videos.** The full 79-video final regression uses R1 + the existing candidate initialization, with A2 only as a controlled G03/004 and G03/005 experiment. `GLOBAL_BRANCH_UNIVERSAL=false`. The task requested one unified candidate algorithm for all groups; this part is not complete. It is not claimed otherwise.

---

## C. Full 39-group / 79-video regression

All 79 videos were actually run under R1 (`ring_mode='all'`, all real Ring boundaries). 67 completed directly. 12 had a disconnected RGB graph; 9 were solved by C3 largest real component, 2 by existing real bridge frames, and 1 by a 4-frame C3B local component. No old W0 was reused for these 12.

| Method | Attempts | W0 | FULL | PARTIAL | ACCEPT |
|---|---:|---:|---:|---:|---:|
| A0 M2-A | 79 | 64 | 64 | 0 | 57 |
| R1 all-boundary | 79 | 67 | 67 | 0 | 72* |
| R1 C3 | 9 | 9 | 0 | 9 | 0 |
| R1 C3B | 1 | 1 | 0 | 1 | 0 |
| R1 bridge | 2 | 2 | 2 | 0 | 0 |
| M2-B final | 79 | **79** | **69** | **10** | **72** |

*The 72 ACCEPT total is the final table total; R1-direct videos contribute 72, C3/C3B/bridge 0.

Per-video and per-group records:

- `W0_79_VIDEO_RESULTS.csv` (79 rows)
- `W0_39_GROUP_SUMMARY.csv` (39 rows)
- `VALIDATION_39.json`
- `IMPLEMENTATION_ERRORS.csv` (header only)
- `TRAJECTORY_BEFORE_AFTER.csv` (A0→A1 for all 79)

No baseline-success video was overwritten. All final W0 matrices pass the numerical checks (79/79); `W0_FULL` means all 10 originally registered frames are present; `W0_PARTIAL` means only a real connected subset (4–9 frames) was solved.

---

## D. Non-ACCEPT visual audit

There are **694 non-ACCEPT cameras** (274 QUARANTINE + 420 INSUFFICIENT_EVIDENCE; 0 REJECT).

### D.1 Every camera is addressable

- `visualization/C_nonaccept_w0/per_video_contact_sheets/` — 79 contact sheets; every W0 camera of every video, with ACCEPT/QUARANTINE/INSUFFICIENT colors, all real Ring boundary points, Ring–Polyp contact in magenta, Ring–Background boundary, CAD inner/outer (area-identified) and centerline.
- `visualization/D_camera_ring_3d/per_video/` — 79 four-view 3D camera/Ring overviews (perspective/top/side/front), same metric Ring frame, no independent scaling.
- `visualization/NONACCEPT_INDEX.html` — browsable index of all 79 videos, both 2D and 3D.
- `visualization/C_nonaccept_w0/{quarantine,insufficient,reject}/index.html` — filtered indexes.

The 2D sheets show the actual admission reason (e.g. `HELD_TRACKS=10<20`, `HELD_P95=...`, `RING_RAW_MAE=...`) and numeric Ring/Held values. No missing reasons are replaced with zero.

### D.2 Diagnostic classes (independent of formal admission)

`NONACCEPT_DIAGNOSTIC_CLASS.csv` (694 rows):

| class | count |
|---|---:|
| MULTIPLE_FAILURES | 348 |
| GEOMETRY_GOOD_EVIDENCE_LIMITED | 133 |
| RGB_MISMATCH | 84 |
| RING_MISMATCH | 67 |
| UNRESOLVED | 58 |
| BRANCH_INCONSISTENT | 4 |
| POSE_INVALID | 0 |

`GEOMETRY_GOOD_EVIDENCE_LIMITED` is only a diagnostic label for numerically good Ring/Held but held evidence <20; it is **not** an ACCEPT and never a human approval. All remain `HUMAN_REVIEW_PENDING`.

### D.3 What the audit shows

- The dominant formal reason is not gross Ring mismatch: 420 INSUFFICIENT cameras are mostly `HELD_TRACKS<20`. Many are `GEOMETRY_GOOD_EVIDENCE_LIMITED`.
- There are real RGB failures: `GP_Is_18...R5/005` has Ring MAE 1.22 px but Held 23.2/77.6 px; Ring fit alone is misleading.
- There are real Ring mismatches (67 cameras) and 4 branch-inconsistent cameras; these are not hidden by the gate.
- The 72 ACCEPT cameras are not assumed correct by the visualizer; `G03/004` A1 has a coherent branch but 0 ACCEPT, and the A0 119° branch is retained as failure evidence.

---

## E. Visual evidence paths

- `visualization/A_ring_observation/complete_boundary_before_after/` — R0 vs R1 for the four videos; Is_18 shows q_train 0 → 128.
- `visualization/A_ring_observation/ring_polyp_contact_examples/` — contact boundary examples.
- `visualization/B_global_branch/G03_detailed/` — A0/A1/A2 3D trajectories.
- `visualization/B_global_branch/trajectory_before_after/` — G03 before/after.
- `visualization/C_nonaccept_w0/` — 79 all-camera sheets + indexes.
- `visualization/D_camera_ring_3d/` — 79 all-camera 3D sheets.
- `visualization/E_summary/representative_contact_sheet.png`, `failure_gallery.png`, `success_gallery.png`.

---

## F. Engineering / reproducibility

- `tools/m2a_merge.py` was fixed to initialize `q={}` before the candidate branch; a clean rebuild reproduced M2-A 79/39 tables (78 W0, 67 FULL, 11 PARTIAL, 1 NOT_COMPUTABLE) without exceptions. The rebuild log is `logs/m2a_merge_rebuild.log`; the frozen M2-A tables were restored after verification.
- M2-B contract test: 6 PASS (`tests/test_m2b_contracts.py`), including 79 numeric W0 checks, G03 A0/A1/A2 assertions, and 79+79 visual index counts.
- Default Python/venv: `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`; OpenCV SIFT path verified.
- `IMPLEMENTATION_ERRORS.csv` is header-only.
- `cross_group_contamination=0` checked across 92 prepared manifests; `undeclared_dependencies` remains explicitly `NOT_AUDITED` outside M2-B scope.

## Evidence package

`runs/m2b_ring_global_branch/M2B_RING_GLOBAL_BRANCH_EVIDENCE.zip` (25.76 MB) contains 83 W0 artifacts, all tables, 204 visual files, logs, the source manifest, and the G03 A1/A2 packets. SHA256 is in `M2B_RING_GLOBAL_BRANCH_EVIDENCE.sha256`.

## G. Remaining gaps

1. **A2 global branch is not universal.** It is implemented and controlled on G03 only. Full 79 final uses R1 + existing init. This is the main unresolved task requirement.
2. `Is_18/005` has W0 but poor held RGB; it is not a success.
3. 10 partial W0 cannot be used as full 10-frame cross-video anchors.
4. Human review remains pending; no `HUMAN_APPROVED` is claimed.
