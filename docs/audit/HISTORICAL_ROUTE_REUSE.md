# HISTORICAL_ROUTE_REUSE

**Task:** ring-first-3d consolidated audit, first round
**Workspace HEAD:** `8b0c166ef5a2310bcdacbc4eae68198ad6530edc`
**Scope:** determine which existing historical routes are mature, which the 028 experiment reuses, which it bypasses, and which are genuine gaps.

This document does **not** authorize deletion or rewriting. It is an evidence map for the route composition decision.

---

## 1. Mature historical routes found in source

| Capability | Historical route | Canonical source | SHA256 (16) | Engineering / scientific status | Reuse policy |
|---|---|---|---|---|---|
| DXY inner/outer/centerline observation | T01 `dxy_mid` | `/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_component.py::recover` | `1564d689219c6699` | FROZEN / CONDITIONAL | read-only |
| 3-class INIT segmentation | T02 | frozen weights `981aa596...` | not re-verified | FROZEN / CONDITIONAL | read-only |
| Ring CAD analytic projection | T16 + `ring_cad_projection` | `src/ring_first_3d/mainline/native/camera.py::torus_contours` | `0168b331808d01e5` | VERIFIED / CONDITIONAL | MUST_REUSE |
| Ring-First 5-DoF camera candidates | T14 | `experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/cameras.py` | `ba95a389fc672284` | VERIFIED / CONDITIONAL | ADAPTED_REUSE |
| Single-video SIFT tracks | frozen `track005` | `experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/frozen_calibration/track005.py` | `c912da0713a329a3` | FROZEN_SOURCE / CONDITIONAL | MUST_REUSE |
| Single-video B0/W0 BA | frozen `local_ring_sfm` | `experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/frozen_calibration/local_ring_sfm.py::BA` | `673b57af12fcda5d` | FROZEN_SOURCE / CONDITIONAL | MUST_REUSE |
| Cross-video SIFT matching + landmarks | 019 `features019` | `027-CORRECTIVE-R6/replay/features019.py` (byte-identical to lineage 021) | `50cd25fd8df87364` | VERIFIED_HISTORICAL / MIXED | reuse with pinned copy |
| Cross-video shared SE(3) refinement | 020 `shared_se3` / `yaw_1dof` | `camera_mainline/code/shared_se3.py`, `yaw_1dof.py` | `e115bb3ad08cef21`, `8091ba7e32d63281` | EXPERIMENTAL / MIXED | candidate only |
| 021 common-landmark BA | T17 `ba021` | `src/.../lineage/.../TASK-E4-RING-ANCHORED-JOINT-BA-021/code/ba021.py` | `ced95fe580a30f5c` | VERIFIED / MIXED | research candidate |
| 021 identity verification | T18 `identity021` | `.../code/identity021.py` | `791de579b21aa82f` | VERIFIED / CONDITIONAL | AST/adapt |
| Ring observation evidence v2 | 026 `ring_evidence_v2` | `experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/...` | not pinned here | EXPERIMENTAL / MIXED | historical reference |
| Mesh-CAD RingRenderer | 020/026 `ring020_026` | `027-CORRECTIVE-R6/replay/ring020_026.py` | `4c14c86c2cfe52cc` | EXPERIMENTAL / MIXED | candidate only |
| Camera admission | 013-PATCH | `camera_mainline/code/camera_admission.py` + policy | `479726a5c96921fd`, `69b164058cc2569f` | VERIFIED / CONDITIONAL | MUST_REUSE |
| Held-out camera evaluation | 013-PATCH | `camera_mainline/code/evaluate_held_geometry.py` | `308b66a908c8063a` | VERIFIED / CONDITIONAL | MUST_REUSE |
| Ring contour metric | 013-PATCH | `camera_mainline/code/contour_metrics.py` | `7b401cf574280ea1` | VERIFIED / CONDITIONAL | MUST_REUSE |

The project-level technical registry (`docs/registry/TECHNICAL_ROUTE_MATRIX.md`, `MODULE_REGISTRY.json`) covers T01-T43. The recent cross-video work (019/020/026/027/028) is **not** in `EXPERIMENT_INDEX.csv` and is **not** in `registry/routes.yaml`. That is the registry gap D27.

---

## 2. Duplicate copies found

All duplicates below are byte-identical, so there is no algorithmic divergence yet. The problem is provenance ambiguity and future drift risk, not a current numerical difference.

| Module | Copies | SHA256 | Canonical choice |
|---|---:|---|---|
| `features019.py` | 4: R6 replay, R5 replay, lineage 021, 019 historical subset | `50cd25fd8df87364` (all) | lineage 021 copy or a new pinned copy; do not import from an experiment replay by relative accident |
| `ring020_026.py` | 2: R6 replay, 026 replay_020 | `4c14c86c2cfe52cc` (all) | one pinned copy; currently an experiment-only route |
| `fixed_track_tri.py` | 7: 027-CORRECTIVE, R2-R6, pilot | `6fd1656ae99e7e94` (all) | one pinned copy; add finite/failure handling in a new version |
| F/Sampson implementations | 4 active + 1 in `r6_core`: `features019.fundamental/sampson`, `geometry_1dof.fundamental/sampson`, `u028c.sampson_px/epipolar_score`, `shared_se3.sampson_px` | different code, same math | `geometry_1dof.py` is the camera_mainline canonical; adapt 028 to it |
| Ring residual formula | `ring_energy.ring_residuals` and inline `u028c.ring_vector` | different code, same formula | `ring_energy.ring_residuals`; 028 should call it, not copy it |

The 028 route imports `features019` from `027-CORRECTIVE-R6/replay` and `fixed_track_tri` from `027-CORRECTIVE-R6/core`. Since the copies are byte-identical, this is currently safe, but it is an **implicit dependency on an experiment directory**. The consolidated route must pin one source path and hash it.

---

## 3. What 028 bypassed, and whether the bypass is justified

### 3.1 Ring geometry — **not justified**

- Formal M1 uses the analytic torus: `native/camera.py::torus_contours` (R=5.6 mm, r=0.6 mm).
- 028 uses `ring020_026.RingRenderer`, which loads the actual CAD mesh (`RING.npz`), computes occluding edges by face visibility, raycasts visibility, and splits inner/outer by depth-contour proximity.
- These are different definitions. The historical 010 result already recorded a ~1.3 px systematic outer offset between DXY ellipse and CAD silhouette.
- Therefore the 028 Ring scores cannot be compared to the M1 Ring metric without an equivalence study. The correct action is an **ADAPT boundary**: either prove the two are numerically equivalent on the same CAD/pose/K, or choose one definition and re-express the other side. This is not a rewrite; it is a boundary decision.

### 3.2 `track005` — **partially justified, but the route split must be explicit**

- `track005.main()` is a single-video tracking entry (train/held split), called through `unified_camera.build_namespace`.
- 028 does not call it. Instead `features019.landmarks` builds per-video landmark tracks and `features019.matches` builds cross-video matches.
- Cross-video matching is genuinely outside `track005`'s capability, so a new cross-video matcher is not a duplicate. But `features019.landmarks` also performs within-video track construction, which overlaps `track005`'s role.
- Decision needed: either (a) use `track005` for within-video tracks and `features019.matches` only for cross-video links, or (b) register `features019` as the single route for both. Do not keep two unregistered within-video track builders in the same pipeline.

### 3.3 `local_ring_sfm.BA` — **GAP for H+X, but the bypass must be labelled**

- `local_ring_sfm.BA(poses, X, tids, support, tr, ref)` has no cross-video H and no shared H+X block. A joint H+X BA is a real missing capability.
- 028's `ba_core_r4` is therefore not a rewrite of the single-video BA; it is a new capability. However:
  - it also re-implements Ring residual blocks that already exist in `local_ring_sfm`'s Ring objective;
  - it was developed without a GAP approval record;
  - it is not converged.
- Decision: keep `local_ring_sfm` as the frozen single-video BA; register `rf-joint-ba-hx-028@1` as a **GAP research candidate**, not as a replacement. Any future formal joint BA must be a new version with a controlled recovery test.

### 3.4 Camera admission — **not justified**

- The formal W0 entry produces `accepted_cameras.npz` and an `admission_status` array precisely so downstream geometry can restrict to ACCEPT.
- 028 reads `camera_result.npz` and ignores both.
- This is a plain contract violation. The fix is an admission filter at the boundary, not an algorithm change.

### 3.5 Canonical lineage — **import path should be pinned**

`src/ring_first_3d/mainline/lineage/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/features019.py` is byte-identical to the R6 copy. The lineage directory is the version-isolated source closure described in `docs/architecture/SYSTEM_OVERVIEW.md`; importing from an experiment replay is weaker. Pin the lineage copy (or a new `src/` copy with a recorded hash), not the replay.

---

## 4. Reuse / adapt / gap decisions

| Module | Decision | Boundary work | Do not do |
|---|---|---|---|
| `dxy_mid.ring_component.recover` | REUSE read-only | hash check at freeze | do not copy its ellipse fitting |
| `native/camera.py::torus_contours` | REUSE | expose a single `project_ring(c2w,K)` boundary | do not write a second torus projector |
| `ring020_026` mesh CAD | ADAPT or retire | equivalence test vs analytic torus on same pose/K | do not let two Ring definitions coexist unregistered |
| `track005` | REUSE for single-video | call through `unified_camera` namespace | do not rewrite SIFT tracking |
| `local_ring_sfm.BA` | REUSE for single-video | none | do not replace B0/W0 with `ba_core_r4` |
| `features019` | REUSE with pinned copy | pin path + hash; validate match cache against RGB hash | do not edit the historical copy in place |
| `fixed_track_tri` | ADAPT | add finite/failure checks and identity-keyed output | do not silently drop failed identities |
| `camera_admission` | REUSE | feed `accepted_cameras.npz` into downstream geometry | do not add per-group thresholds |
| `geometry_1dof` | REUSE | make it the single F/Sampson implementation | do not duplicate F in 028/shared_se3 |
| `ring_energy.ring_residuals` | REUSE | 028 `ring_vector` calls it | do not inline the formula |
| `ba_core_r4` | GAP candidate | register; add convergence/recovery tests; no freeze | do not call it the formal BA |
| 020 `shared_se3` | candidate | group-agnosticization + live matches required before use | do not use its G03 fixture as a cross-group result |
| `identity021` | reference only | compare on G01 background identities | do not claim equivalence without a test |

---

## 5. Historical assets that must be preserved

The following are research evidence, not cleanup candidates:

- `experiments/TASK-E4-W0-CROSSVIDEO-019*` through `028*` (including failed and superseded runs).
- `027-CORRECTIVE-R2..R6` controlled synthetic scenes and defect tests.
- `026` Ring geometry/uncertainty experiments, including the withdrawn 0.51°/0.156 mm result and the corrected 2.985°/0.698 mm number.
- `021` common-landmark BA and identity verification.
- `cam-ring-rgb-joint@1` and `ring-cad-inner-outer@1` historical evidence.
- The `TASK-015` consolidation intermediates (now containing G06 W0 writes) — preserve, but do not treat as a frozen package.

No historical directory, result, failed run, or source copy is deleted in this consolidation. Cleanup, if any, happens only after a preservation manifest and human approval.

---

## 6. Summary

- The mature M1 modules are real and should be reused: DXY observation, analytic torus, frozen tracks, frozen single-video BA, admission, held evaluation.
- The cross-video 019/020/021/026/027/028 code is research evidence, with byte-identical copies but no registered canonical path.
- 028 bypasses three mature modules (analytic torus, track005, local_ring_sfm) and one gate (admission). The first three are architectural decisions that need explicit registration; the gate bypass is a defect.
- No historical route is deleted or rewritten in this round.
