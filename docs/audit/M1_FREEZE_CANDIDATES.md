# M1_FREEZE_CANDIDATES — M1-FINAL-CONSOLIDATION-39

**Source commit:** `0be83ff6810c18e43d4762975347d0cb5138dbb7`
**Base commit before M1 changes:** `26c724ff15a428d028bb2f32685b543a52ab48b2`
**Primary run:** `runs/m1_final_39`
**Freeze scope:** engineering/interface modules that passed the 39-group execution and tests.
**Full-data W0 coverage:** `64/79 = NOT_MET` (15 documented data-quality blocks).

## 1. Freeze decisions

| Module | route@version | Status | Why |
|---|---|---|---|
| M1-01 Input | `rf-m1-input-39@1` | **FROZEN** | 39 groups / 79 videos / 790 frames prepared; 0 identity errors |
| M1-02 INIT segmentation | `rf-init-segmentation@1` | **FROZEN** | reused `prepare_view`; weight sha256 `981aa596...`; 790 masks 3-class |
| M1-03 Ring CAD | `rf-native-ring-cad@2` | **FROZEN** | R10 bitwise unchanged; R5 3.1/0.6 verified; no second projector |
| M1-04 RGB tracks | `rf-frozen-tracks005@1` | **FROZEN** | unchanged source; used on all 79 videos |
| M1-05 single-video BA | `rf-frozen-ba-local-ring-sfm@1` | **FROZEN** | unchanged source; 64 numerically valid W0; G03 16-view regression |
| M1-06 W0 | `rf-w0-camera@2` | **FROZEN (engineering)** | 79 attempted; 0 implementation errors; self-contained outputs |
| M1-07 admission | `rf-camera-admission@1` | **FROZEN** | unchanged policy; 57/210/373/0 statuses |
| M1-08 validator | `rf-m1-39-runner@1` | **FROZEN** | 79-row/39-group tables; numerical checks; explicit statuses |
| M1-W0-FULL-COVERAGE | — | **NOT_FROZEN** | `W0_79_COVERAGE_PASS=false`; 15 data-quality blocks |

The W0 **code/interface** is frozen. The claim “all 79 videos have W0” is **not** made and must not be inferred from the frozen W0 entry.

## 2. Frozen source hashes

| File | SHA256 |
|---|---|
| `tools/prepare_m1_inputs.py` | `e9d9a41ad3577520f3c49dc91f72530cc8ff5a591b7c3a50e79f26cdb391b4d9` |
| `src/ring_first_3d/mainline/native/camera.py` | `26055b957040ca8419ba6e278e091288ecd99299dbba0c295fbba578fb9c9e51` |
| `experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code/unified_camera.py` | `ba69aca8cd404e28f0cc4c81babfa5d9abdfef2971a3ae3dd43a08b881783d20` |
| `camera_mainline/code/contour_metrics.py` | `989ca724528b5d7f3e40eb61d6f3d4c6c08b9703231f344b66b3669aa8606559` |
| `tools/run_w0_camera.py` | `17d09a4940ed531b342ebd436c407e7de6c4f59cfb17ad7f3361f4c894236336` |
| `tools/validate_m1_all_groups.py` | `feb2a712cb9e0e91c37f2d7ecff049e5f56d090bd7badbebf35f8e0d4abd8e36` |
| `track005.py` (reused) | `c912da0713a329a3c954fc7b1dfbdcf43459493432ccbc782d7742cd26e514ac` |
| `local_ring_sfm.py` (reused) | `673b57af12fcda5dad082eb7397574d46f0bdce2c097956c0682d8dac2cd8541` |
| `camera_admission.py` (reused) | `479726a5c96921fde40e1a15dc3383c9d4fb349a1a998ee7b186080b2a341073` |
| `CAMERA_ADMISSION_POLICY.yaml` | `69b164058cc2569f992c2cc380b8f27d39c92fdebcb05b6a19eb0dcf6c2732e1` |
| frozen config | `d2f61b29b454a7f7e48b5d5f1254cd806ff9348335f220fb1e5f11ddedc61ddc` |

## 3. Contracts

- Input: `frozen39/inputs.csv` + local raw video; group_key is canonical; legacy Gxx are aliases only.
- Camera: c2w, mm, world = Ring CAD frame; K fixed 640×360 same for all prepared caches; 79 raw videos 1280×720.
- Ring: R10 `(5.6, 0.6)`, R5 `(3.1, 0.6)`; R/r passed from `PREPARED.json`.
- H/FIT/HOLDOUT: M1 has no cross-video H; admission is per-view.
- Outputs: `W0.npz`, `camera_result.npz`, `B0.npz`, `admission.csv`, `quality_summary.json`, `RUN_MANIFEST.json`, `STATUS.json`.
- Status: `COMPLETED_VALID`, `COMPLETED_LIMITED`, `INSUFFICIENT_EVIDENCE`, `BLOCKED_QUALITY_GATE`, `INVALID_INPUT`, `IMPLEMENTATION_ERROR`, `NOT_EXECUTED_DEPENDENCY`.

## 4. Verification evidence

| Evidence | Result |
|---|---|
| 39-group / 79-video run | 39/39 groups, 79/79 attempted, 790/790 frames |
| implementation errors | **0** |
| unexpected exceptions | **0** |
| missing required outputs | **0** |
| cross-group contamination | **0** |
| W0 generated / numerically valid | **64 / 64** |
| quality accepted / limited | 22 / 42 |
| not computable | 15 (11 disconnected graph, 4 insufficient ring) |
| R10 / R5 W0 | 41/44, 23/35 |
| G03/005 16-view regression | 16/16 ACCEPT; 0.828765 / 0.980167 / 3.209369 |
| R10/R5 CAD tests | PASS |
| tests | 21 PASS across 5 files |
| clean W0 rerun | 79/79 statuses identical; 64/64 W0 byte-identical; metric diff 0.0; `ENGINEERING_39_PASS=true` |

## 5. What is deliberately not frozen

- Full 79/79 W0 coverage (`W0_79_COVERAGE_PASS=false`).
- R5 full coverage (23/35).
- Any cross-video H/BA/local-camera correction (M2/M3/M4).
- `features019`/`ring020_026`/`ba_core_r4`/`u028c` remain outside M1.

No module is marked frozen merely because “the script finished”. Freezing is limited to the engineering/interface scope above.
