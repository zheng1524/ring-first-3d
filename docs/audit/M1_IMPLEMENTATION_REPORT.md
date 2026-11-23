# M1_IMPLEMENTATION_REPORT — M1-FINAL-CONSOLIDATION-39

**Task:** complete the approved M1 consolidation and run the full 39-group / 79-video W0 validation.
**Base commit:** `26c724ff15a428d028bb2f32685b543a52ab48b2`
**Implementation commit:** `0be83ff6810c18e43d4762975347d0cb5138dbb7`
**Primary run:** `runs/m1_final_39`
**Scope:** M1 only (Input → INIT/Ring observation → Ring CAD → track005 → B0/W0 → held evaluation → admission → output/manifest).
**No M2/M3/M4 algorithm was started.**

---

## 1. Three independent conclusions

```text
ENGINEERING_39_PASS = true
W0_79_COVERAGE_PASS = false
M1_FREEZE_READY = true (engineering/interface scope)
```

- `ENGINEERING_39_PASS=true`: 39/39 groups, 79/79 videos attempted, 790/790 prepared frames, 0 implementation errors, 0 unexpected exceptions, 0 missing required outputs.
- `W0_79_COVERAGE_PASS=false`: **64/79** videos produced a numerically valid W0. 15 videos are not computable for documented data/quality reasons; no W0 was fabricated.
- `M1_FREEZE_READY=true` for the engineering/interface modules. Full 79/79 W0 coverage is **NOT_MET** and is recorded as a data-quality limitation, not a code failure.

---

## 2. Code changes (M1 boundary only)

| File | Change | Why |
|---|---|---|
| `src/ring_first_3d/mainline/native/camera.py` | optional `ring_radius` / `ring_wire` in `torus_contours`, `residual`, `score`, `recover`; defaults 5.6/0.6 | R10/R5 real data; kernel already supported R/r |
| `experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code/unified_camera.py` | pass R/r through `build_namespace` and `ring_candidates`; defaults unchanged | keep Ring initialization/BA residual on the same R/r as evaluation |
| `camera_mainline/code/contour_metrics.py` | optional R/r in `ring_raw_mae` | R5 admission metric must use R5 CAD, not R10 |
| `tools/run_w0_camera.py` | `--prepared-root`, `--workdir`, Ring R/r from PREPARED, `quality_summary.json`, `STATUS.json`, `RUN_MANIFEST.json`, observation export, known-quality status, nonzero exit for blocks | one W0 entry, self-contained output, no TASK-015 writes |
| `tools/prepare_m1_inputs.py` (new) | thin 39-group prepared-input glue; imports `prepare_view`/`sha`/`K` from 005 | reuse frozen INIT; no segmentation rewrite |
| `tools/validate_m1_all_groups.py` (new) | 39-group/79-video runner, W0 numerical checks, status taxonomy, 79-row/39-group aggregation | single formal validation entry; no algorithm |

**Not modified:** `track005.py`, `local_ring_sfm.py`, `dxy_mid/*`, `features019.py`, `ring020_026.py`, `ba_core_r4.py`, `u028c.py`, `tools/run_w0_registration.py`. The frozen algorithms are called unchanged.

### 2.1 Fixed implementation defects found during execution

1. `run_w0_camera.py` manifest referenced the wrong `frozen_calibration/config.json` path (`T005` instead of `T002`); fixed.
2. Known data-quality `RuntimeError('Ring pose graph disconnected; no free SfM fallback')` was uncaught and therefore looked like an implementation error; now mapped to `BLOCKED_QUALITY_GATE` with `STATUS.json`.
3. `main()` return value was ignored, so a known-quality block exited 0; now `sys.exit(main())`.
4. W0 `quality_summary`/`STATUS`/`RUN_MANIFEST` were incomplete or missing; now every completed/blocked video has a diagnostic status.
5. `torus_contours` / `residual` / `recover` / `ring_raw_mae` / `run_w0_camera` hardcoded R10; now parameterized from `ring_mm`.
6. The prepared-input plan test counted Ring types per video row; corrected to per unique group (22 R10 / 17 R5 groups).
7. Validator aggregation turned missing metrics into NaN and crashed; fixed with explicit `_int0` handling and `--aggregate-only`.

No Ring, SIFT, BA, DXY or INIT mathematics was changed.

---

## 3. Input coverage

| Metric | Expected | Actual |
|---|---:|---:|
| Groups | 39 | **39** |
| Videos | 79 | **79** |
| Registered frames | 790 | **790 prepared** |
| Reference photos | 120 | **120 recorded**, not used in M1 |
| R10 groups / videos | 22 / 44 | **22 / 44** |
| R5 groups / videos | 17 / 35 | **17 / 35** |

Source: `/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv`; raw videos in `smart_endoscope_20260805 (1)/raw`.
All 79 videos are 1280×720; prepared cache is 640×360 with the frozen `K`; 790/790 frames have 3-class labels and finite K.

`runs/m1_final_39/INPUT_COVERAGE.csv`: 39 rows, all `VALID`.

---

## 4. W0 execution

Command (single formal entry, 6 workers, single-thread BLAS):

```bash
python tools/validate_m1_all_groups.py \
  --prepared-root runs/m1_final_39/prepared \
  --output-root runs/m1_final_39 \
  --work-root runs/m1_final_39/work --workers 6
```

| Metric | Value |
|---|---:|
| attempted videos | 79 |
| W0 generated | 64 |
| W0 numerically valid | 64 |
| quality accepted | 22 |
| quality limited | 42 |
| not computable | 15 |
| implementation errors | 0 |
| unexpected exceptions | 0 |
| missing required outputs | 0 |

### 4.1 Why 15 videos have no W0

| Reason | Videos |
|---|---:|
| `BLOCKED_QUALITY_GATE` / `Ring pose graph disconnected; no free SfM fallback` | 11 |
| `INSUFFICIENT_EVIDENCE` / `INSUFFICIENT_RING_OBSERVATION` | 4 |

These are upstream observation/connectivity conditions, recorded with `STATUS.json`, `stdout.log`, `stderr.log`. They are **not** implementation errors and no W0 was invented.

The full 15-row list is in `M1_39_GROUP_VALIDATION.md` and `W0_79_VIDEO_RESULTS.csv`.

### 4.2 R10/R5 split

| Ring | videos | W0 generated | accepted | limited | not computable |
|---|---:|---:|---:|---:|---:|
| R10 | 44 | 41 | 14 | 27 | 3 |
| R5 | 35 | 23 | 8 | 15 | 12 |

R5 is the dominant coverage limitation: 12/35 not computable, mostly ring observation/connectivity.

---

## 5. Scientific quality (only 64 generated W0 videos)

| Metric | Value |
|---|---:|
| total W0 poses | 640 |
| ACCEPT | 57 |
| QUARANTINE | 210 |
| INSUFFICIENT_EVIDENCE | 373 |
| REJECT | 0 |
| Ring MAE mean, median across videos | 1.530 px |
| Held median, median across videos | 2.684 px |
| Held P95, median across videos | 15.502 px |
| positive-depth fraction, minimum | 1.000 |
| trajectory jumps, total | 157 |
| maximum adjacent rotation | 173.23 deg |

The high trajectory-jump count and 173° branch are **scientific quality findings**. They are not hidden and are passed to `M2_DEVELOPMENT_HANDOFF.md`.

Historical G03/005 16-view baseline was run separately as a component regression and remains:

```text
16/16 ACCEPT
Ring MAE 0.828765 px
Held median 0.980167 px
Held P95 3.209369 px
```

It is **not** mixed into the 39-group matrix: the 39-group run uses the 790 `frozen39` frames.

---

## 6. Tests run

| Test | Result |
|---|---|
| `tests/test_m1_39_inputs.py` | 3 PASS |
| `tests/test_ring_cad_r10_r5.py` | 3 PASS (R10 bitwise kernel; R5 G07 2.5–3.7 / 3.1–0.6) |
| `tests/test_m1_runner_status.py` | 12 PASS |
| `tests/test_m1_prepared_contract.py` | 2 PASS (79 dirs / 790 frames / labels / K) |
| `tests/test_w0_manifest_closure.py` | 1 PASS |
| G03/005 16-view W0 smoke | 16/16 ACCEPT; 0.828765 / 0.980167 / 3.209369 |
| R5 real-video smoke | 10 W0 poses; R/r=3.1/0.6; finite matrices; 0 ACCEPT, 10 INSUFFICIENT_EVIDENCE |

`EXECUTION_FAILURES.csv` contains only its header: no implementation error to list.

---

## 7. Outputs

Primary run root: `runs/m1_final_39/`

- `W0_79_VIDEO_RESULTS.csv` — exactly 79 rows
- `W0_39_GROUP_SUMMARY.csv` — exactly 39 rows
- `VALIDATION_39.json`
- `EXECUTION_FAILURES.csv`
- `INPUT_COVERAGE.csv`
- `SOURCE_CHANGE_MANIFEST.json`
- per-video `W0.npz`, `camera_result.npz`, `B0.npz`, `admission.csv`, `quality_summary.json`, `RUN_MANIFEST.json`, `STATUS.json`, observations and logs.

Evidence package: `W0_79_EVIDENCE_PACKAGE.zip` (built from the primary run; contains all generated W0/camera_result/admission/quality/manifest plus blocked-video diagnostics).

---

## 7.1 Independent clean rerun

A second full 79-video W0 run was executed in `runs/m1_final_39_clean` using the same final code and the hash-verified 790-frame prepared input.

| Check | Result |
|---|---|
| video rows | 79 / 79 |
| execution status equality | **79/79 identical** |
| W0 generated equality | **79/79 identical** |
| W0 files byte-identical | **64/64** |
| W0 files different | **0** |
| metric max absolute difference | **0.0** |
| ENGINEERING_39_PASS | true (both runs) |
| W0_79_COVERAGE_PASS | false (both runs) |

The prepared caches were reused after 790/790 hash validation; all W0 cameras were recomputed, not copied. `FULL_CLEAN_RERUN_W0=true`, `prepared_reused=true`. Evidence: `runs/m1_final_39_clean/CLEAN_RERUN_COMPARISON.json`.

## 8. Remaining issues (not implementation errors)

1. 15/79 videos are not computable from the registered frames under the frozen Ring/tracking route; 11 disconnected Ring pose graphs, 4 insufficient Ring observations.
2. R5 coverage is lower than R10 (23/35 vs 41/44).
3. 42/64 generated W0 videos are quality-limited; only 22 have at least one ACCEPT.
4. Trajectory branch jumps are widespread (157 total; max 173°); these are M2 inputs, not M1 code errors.
5. Full 79/79 W0 coverage is **NOT_MET**; `W0_79_COVERAGE_PASS=false`.

No further historical audit is opened. These are classified as data-quality/branch issues for M2.
