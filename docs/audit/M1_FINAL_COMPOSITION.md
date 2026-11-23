# M1_FINAL_COMPOSITION — Input + Ring + Single-Video Camera + Quality

**Status:** `PENDING_HUMAN_CONFIRMATION`
**Base commit:** `98873442e01eb2f7b1b4b1d44a16e3709e856d61`
**Scope:** M1-01 … M1-07 only. No M2/M3/M4 work.
**Production code changed in this step:** none. This document is the approval gate.

This document reuses the audit at `98873442`; it does **not** re-audit the 21 historical routes.

---

## 1. Verified data facts (read-only)

Source of truth for the 39 groups: `/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv` (read-only external registry), cross-checked against `smart_endoscope_20260805 (1)/raw` and `smart_endoscope_20260805 (1)/work/group_predictions.csv`.

| Item | Verified value |
|---|---|
| Groups | **39** unique `group_key` (raw `GP_*_single_refY` stems) |
| Videos | **79** (38 groups × 2; one group × 3) |
| Frames in registry | **790** (20/group; one group 30) |
| Reference photos | **120** (36 groups × 3; 3 groups × 4) |
| Ring type | **22 groups R10** (440 frames) + **17 groups R5** (350 frames) |
| Raw video resolution | **79/79 = 1280×720**, all frame indices within frame count |
| Raw video existence | **79/79 present** in `smart_endoscope_20260805 (1)/raw` |
| Current prepared | **5 groups / 10 video dirs** only: G01, G02, G03, G05, G06 |
| Prepared gap | **34 groups / 69 video dirs** |
| Legacy alias mapping | G01=GP_Ip_12.0mm_R10, G02=GP_Ip_4.0mm_R10, G03=GP_Ip_20.0mm_R10, G05=GP_Is_18.0mm_R10, G06=GP_IIa_14.0mm_R10 |
| INIT weights | `.../dxy_remeasurement_20260917/02_segmentation/model/model.safetensors`, sha256 `981aa596...` verified |
| `frozen39` image/mask files | absent (790/790); not used — raw video + frozen INIT is the route |
| `ALL_VIEWS.json` | only 11 groups; **not** a 39-group frame registry |

**Consequence:** the 39-group M1 run must use the `frozen39/inputs.csv` frame registry (790 frames) and generate prepared inputs from raw video with the frozen INIT. The legacy 16-view G03 prepared cache remains a component regression fixture only; it is **not** mixed into the 39-group acceptance matrix.

### 1.1 Ring types are not uniform

- R10: inner diameter 10 mm, CAD centerline R=5.6 mm, wire r=0.6 mm.
- R5: inner diameter 5 mm, CAD centerline R=3.1 mm, wire r=0.6 mm (verified from G07 `RING.npz`: radial min 2.500, max 3.700, z ±0.600).

Current M1 code hardcodes R10 in four places:

| File | Hardcode |
|---|---|
| `src/ring_first_3d/mainline/native/camera.py` | `torus_contours` R=5.6/r=.6; `residual` `rad=5.6,tube=.6`; `recover` `rad=5.6,tube=.6` |
| `.../UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code/unified_camera.py` | `build_namespace` `ring_residual` binds R10 `residual` |
| `camera_mainline/code/contour_metrics.py` | `ring_raw_mae` calls R10 `torus_contours` |
| `tools/run_w0_camera.py` | `ring_cad_mm=[5.6,0.6]` |

The underlying `_kernels.torus_contours(..., R, r)` already supports both. Therefore this is an **interface adaptation**, not a new Ring algorithm.

### 1.2 Camera intrinsics

All 79 raw videos are 1280×720; the frozen 005 config is `K=[[490,0,319.5],[0,490,179.5],[0,0,1]]` for the 640×360 prepared cache. `unified_camera.build_namespace` already asserts `K == K_CFG`.

There is **no per-group K table** in `frozen39`. The plan therefore records K per group and asserts each prepared cache equals the frozen K; any deviation becomes `INVALID_INPUT`, never silent coercion. This is a recorded input contract, not an assumption of algorithmic equivalence.

---

## 2. M1 final composition table

Route IDs refer to `docs/registry/routes.yaml` at commit `98873442`. `planned` versions are created only after approval.

| 阶段 | 现有 route_id@version | 入口 | 输入输出 | REUSE/ADAPT/GAP | smoke test |
|---|---|---|---|---|---|
| **M1-01 Input identity / 39-group registry** | `rf-input-prepared@1` + planned `rf-m1-input-39@1` | new thin `tools/prepare_m1_inputs.py`; reuses `prepare.py::prepare_view` (005) | `frozen39/inputs.csv` + raw videos → `prepared/{group}_{video}/PREPARED.json` + `INPUT_COVERAGE.csv` | **ADAPT** (orchestration/contract only; INIT math reused) | 39 groups/79 videos/790 frames/120 photos; 22 R10 + 17 R5; prepared 39/39 |
| **M1-02 INIT segmentation + Ring observation** | `rf-init-segmentation@1` + `rf-dxy-ring-observation@1` | `prepare.py::segment/prepare_view`; `dxy_mid._engine.ring_component.recover` | raw frame → 3-class labels (0/1/2) → I/O/C evidence | **REUSE** | one R10 and one R5 frame: labels⊆{0,1,2}; non-empty inner/outer/centerline |
| **M1-03 Ring CAD geometry** | `rf-native-ring-cad@1` → planned `@2` | `native/camera.py::torus_contours/residual/recover`; `_kernels.torus_contours(R,r)` | c2w + K + ring R/r → I/O curves / residual | **ADAPT** (optional R/r parameters, defaults 5.6/0.6; math unchanged) | R10 5.6/0.6 matches legacy; R5 3.1/0.6 matches G07 CAD; no second projector |
| **M1-04 Single-video RGB tracking** | `rf-frozen-tracks005@1` | `track005.py::main` via `unified_camera.build_namespace` | prepared views → `tracks005.npz` / `pairs005.npz` | **REUSE** | one new group: tracks non-empty, held split present, no NaN |
| **M1-05 Ring+RGB single-video camera / BA** | `rf-w0-camera@1` → planned `@2` + `rf-frozen-ba-local-ring-sfm@1` | `tools/run_w0_camera.py --stage all` | prepared + tracks + ring evidence → B0/W0 c2w + admission | **REUSE core BA + ADAPT boundary** (`--prepared-root`, `--workdir`, ring R/r, manifest) | G03 legacy regression 0.828765/0.980167/3.209369; one R5 group W0 outputs complete |
| **M1-06 Camera quality / admission** | `rf-camera-admission@1` + `evaluate_held_geometry` + `contour_metrics` | `camera_admission.py::decide`; `contour_metrics.ring_raw_mae` | per-view metrics → ACCEPT/QUARANTINE/REJECT/INSUFFICIENT_EVIDENCE | **REUSE + ADAPT** (pass ring R/r to the existing metric; no threshold change) | G03/005 16/16 ACCEPT; R5 group statuses finite; all four statuses preserved |
| **M1-07 Output / status / manifest / 39 runner** | `rf-provenance@1` + planned `rf-m1-39-runner@1` | new thin `tools/validate_m1_all_groups.py` | per-video outputs → `SUMMARY.json`, `RUN_MANIFEST.json`, `CROSS_GROUP_39.csv`, `VALIDATION_39.json`, `EXECUTION_FAILURES.csv` | **ADAPT** (orchestration/status only) | 39 group rows; 79 video rows; 0 missing outputs; 0 unexpected exceptions |
| **M1-08 Reference photos (metadata only)** | no route (M1 does not use photos) | input registry | 120 photo IDs → coverage record | **REUSE metadata only** | 120/120 recorded; `reference_photos_used=false` |

### 2.1 Decisions

- **No algorithmic GAP for M1.** Every scientific capability already exists: frozen INIT, DXY Ring observation, analytic torus, `track005`, `local_ring_sfm.BA`, admission, held evaluation.
- The missing pieces are **engineering boundaries**: 39-group input registry, per-ring parameter threading, W0 manifest/status closure, and the 39-group runner.
- The 028 cross-video code (`u028c.py`, `ba_core_r4`, `features019`, `ring020_026`) is **out of M1 scope** and is not modified by Round 2.
- `track005.py`, `local_ring_sfm.py`, `dxy_mid`, `features019`, `ba_core_r4`, `u028c.py` are **not modified**.

### 2.2 True GAPs / recorded gaps

| GAP | Status | Why it does not block M1 now |
|---|---|---|
| G1: no 39-group input registry/runner | **Glue gap**, explicitly allowed by task | Thin runner + `prepare_view` reuse; no new algorithm |
| G2: per-ring CAD interface | **ADAPT**, not GAP | Kernel already takes R/r; only wrapper signatures need optional params |
| G3: per-group K table | **Recorded input contract** | All 79 videos 1280×720; frozen K asserted per prepared cache; deviation → INVALID_INPUT |
| G4: reference photos not used | **M1 boundary** | Record IDs and `used=false`; no claim of use |
| G5: 39-group acceptance on dev box | **Execution cost** | 790 frames + 79 W0 runs; Round 2/3 budget, not a scientific gap |

---

## 3. Allowed file changes for Round 2

Only these files may be created/modified:

**Production boundary (minimal):**
- `src/ring_first_3d/mainline/native/camera.py` — optional `ring_radius/ring_wire` in `torus_contours`, `residual`, `score`, `recover`; defaults unchanged.
- `experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code/unified_camera.py` — pass ring R/r through `build_namespace`/`ring_candidates`; defaults unchanged.
- `camera_mainline/code/contour_metrics.py` — optional ring R/r in `ring_raw_mae`; defaults unchanged.
- `tools/run_w0_camera.py` — `--prepared-root`, `--workdir`, ring R/r plumbing, `quality_summary.json`, manifest closure, known-quality status.

**New thin glue (no algorithms):**
- `tools/prepare_m1_inputs.py` — 39-group frame registry → prepared cache; imports `prepare_view`/`sha` from 005.
- `tools/validate_m1_all_groups.py` — 39 groups / 79 videos orchestration, status, outputs, aggregation.

**Tests / registry / docs:**
- `tests/test_m1_39_inputs.py`
- `tests/test_ring_cad_r10_r5.py`
- `tests/test_w0_manifest_closure.py`
- `tests/test_m1_runner_status.py`
- `docs/registry/routes.yaml` (planned versions + hashes after implementation)
- `docs/audit/M1_FINAL_COMPOSITION.md`, `M1_IMPLEMENTATION_REPORT.md`, `M1_39_GROUP_VALIDATION.md`, `M1_FREEZE_CANDIDATES.md`, `M2_DEVELOPMENT_PLAN.md`

**Explicitly not modified:**
`track005.py`, `local_ring_sfm.py`, `dxy_mid/*`, `features019.py`, `ring020_026.py`, `ba_core_r4.py`, `u028c.py`, `tools/run_w0_registration.py`, any 028 run output.

---

## 4. 39-group engineering acceptance

A group is **executed** if every existing video in that group is passed to `tools/run_w0_camera.py` through the same runner, or terminated by a verifiable upstream input/quality rule that writes a status.

Group status vocabulary:

```text
COMPLETED_VALID
COMPLETED_LIMITED
INSUFFICIENT_EVIDENCE
BLOCKED_QUALITY_GATE
INVALID_INPUT
IMPLEMENTATION_ERROR
NOT_EXECUTED_DEPENDENCY
```

Each status carries `stage`, `reason`, `error_type`, `input_identity`, `module_version`.

`ENGINEERING_39_PASS = true` only if:

```text
expected_groups == 39
discovered_groups == 39
input_valid_groups == 39
executed_groups == 39
completed_groups + quality_limited_groups + insufficient_evidence_groups == 39
implementation_error_groups == 0
unexpected_exception_count == 0
missing_output_groups == 0
```

Quality-limited or insufficient-evidence groups are legal and do **not** fail engineering acceptance. Any `IndexError`, `KeyError`, `ModuleNotFoundError`, shape mismatch, wrong coordinate convention, cross-group cache read, or missing required output **does** fail acceptance.

---

## 5. Round 3 freeze conditions

M1 may be frozen only after a clean Round 3 rerun in a fresh output root:

1. 39/39 input coverage and 79/79 video execution.
2. 0 implementation errors and 0 missing outputs.
3. Same statuses as Round 2 (or explained deterministic differences).
4. R10 legacy G03 regression still passes; R5 smoke passes.
5. Manifest input/output hashes are self-contained.
6. No cross-task writes; no test injects undeclared `sys.path`.
7. Registry records `route_id`, version, source commit/hash, config hash, entrypoint, dependencies, contract, smoke test, evidence.

Modules that do not meet these conditions stay `NOT_FROZEN` with evidence.

---

## 6. Approval request

Before any production-code change, confirm:

- [ ] **A1.** Approve the M1 composition table above (M1-01 … M1-08).
- [ ] **A2.** Approve the explicit file whitelist in §3; no other production files.
- [ ] **A3.** Approve per-ring R/r parameterization as **ADAPT v2** (optional parameters, defaults unchanged; no Ring math change).
- [ ] **A4.** Approve the 39-group input rule: `frozen39/inputs.csv` 790 frames + raw videos + frozen INIT; legacy 5-group prepared caches are component regression only, not mixed into the 39 matrix.
- [ ] **A5.** Approve the status taxonomy and `ENGINEERING_39_PASS` criteria in §4.
- [ ] **A6.** Approve Round 3 clean rerun + M1 freeze + `M2_DEVELOPMENT_PLAN.md` handoff.

**Until A1-A6 are confirmed, no production code is modified and no 39-group execution is claimed.**
