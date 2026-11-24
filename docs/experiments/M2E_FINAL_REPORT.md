# M2E FINAL REPORT — historical method integration

**Task:** TASK-M2E-HISTORICAL-METHOD-INTEGRATION-001  
**Branch:** `exp/TASK-M2E-HISTORICAL-METHOD-INTEGRATION-001`  
**Output:** `runs/m2e_historical_method_integration/`

## 0. Status

```text
HISTORICAL_METHODS_INTEGRATED       = true
UNIFIED_FRAME_REGISTRY_VERIFIED     = false
HISTORICAL_REGRESSION_PASS          = true
T10_T11_TARGET_SELECTION_EXECUTED   = true
T13_SUPPORT_SELECTION_EXECUTED      = true
HERO_BATCH_ACTUALLY_EXECUTED        = true
HISTORICAL_CLEANING_EXECUTED        = true
STANDARD_A_TO_B_BATCH_EXECUTED      = true
SIX_VIEW_GALLERY_COMPLETE           = true (8 groups)
ALL_39_GROUPS_ATTEMPTED             = true
GENERIC_PIPELINE_VERIFIED           = true
HUMAN_REVIEW_PENDING                = true
```

`UNIFIED_FRAME_REGISTRY_VERIFIED` is false because the local W0 data does not expose a source-video hash for all views; view/RGB/mask/K/c2w identity was registered, but the full required source-video binding is incomplete.

## 1. Actual execution

| Item | Result |
|---|---:|
| FRAME_REGISTRY rows | 766 |
| T10/T11 target records | 622 |
| T13 support records | 316 |
| T13 READY targets | **217** |
| T13 insufficient supports | 99 |
| Actual HERO targets | **217** |
| HERO PASS | **217** |
| M2E groups / videos | **39 / 71** |
| Historical cleaning | **217** |
| Standard A→B pairs | **311** |
| A→B targets | 217 |
| Six-view groups | 8 |
| M2D groups / videos / targets | 28 / 36 / 112 |

`T10` used `quality_features` + `quality_diversity`; `T11` direction quota was executed and recorded. `T13` used the historical `support_pairs` with the historical SIFT 6000/contrast .01 descriptors and mutual BF matching. ORB was rejected as a substitute. T13 insufficient supports were not padded.

## 2. A→B result

Historical standard `reprojection.render/evaluate` was used for 311 real pairs (all 217 targets at least once; first 8 groups all three supports). The standard definition is `common_pixels / target_polyp_pixels`.

| Metric | M2E |
|---|---:|
| Target coverage median | **0.502** |
| Target coverage mean | 0.482 |
| RGB MAE median | **23.82** |
| RGB MAE mean | 25.46 |
| predicted outside target p50 | 3,790 pixels |

The low/wide coverage and large outside-target counts are real results. They are not converted into a success claim. The earlier M2-D vertex-in-frame coverage is not comparable and is not used.

A current five-panel figure exists:

`runs/m2e_historical_method_integration/visualization/figures/A_to_B/GP_IIa_14.0mm_closed_R10_single_refY_004-raw02-11__to__GP_IIa_14.0mm_closed_R10_single_refY_004-raw02-17.png`

## 3. Historical regression and cleaning

Four historical targets (G01/G03/G05/G06) remain bitwise identical for depth/V/F; see `HISTORICAL_REGRESSION_RESULTS.csv`.

All 217 M2E HERO outputs were cleaned with `cleaning.py::classify_native` and R5/R10 CAD. Cleaning retained Raw; `REJECTED=0` in the current runs, with UNKNOWN preserved. This is conservative cleaning, not a claim that all difficult surface points were removed.

## 4. Six-view

Eight auto-selected groups were rendered with `_mesh_renderer.actual_mesh_image`, real triangles, black Ring CAD, fixed metric bounds, Raw vs Conservative Cleaned, six views:

`runs/m2e_historical_method_integration/visualization/six_view/`

The selection covers R5/R10 and coverage/MAE extremes. It is representative, not all 39 groups.

## 5. Direct answers

1. **Did historical target selection improve current MVS?** Not established. T10/T11 changed target selection and T13 support sets, but no controlled paired M2D-vs-M2E set with the same standard evaluator exists. M2E has more coverage (39 vs 28 groups), not proven better geometry.
2. **Does T13 work generically?** Yes operationally: 217 READY targets from 39 groups/71 videos; 99 insufficient supports were explicitly rejected. No fixed G01/G03/G05/G06 gate.
3. **Did local shape/multiview consistency improve vs M2D?** Not measured. No paired same-target standard A→B/multisurface comparison; multisurface consistency is `NOT_EVALUATED`.
4. **Is remaining degradation mainly camera?** Not isolated. A2 remains unresolved, source-video hashes missing, and standard A→B has low coverage/high outside-target; camera, support, depth and visibility remain confounded.
5. **Is there a unified reusable MVS line?** Partially: T10/T11/T13/HERO/cleaning/standard A→B/six-view are wired through one parameterized batch; independent views, source-video hash binding and multisurface consistency are not complete.

## 6. Not executed

- Independent B selection/evaluation (`NOT_EXECUTED`);
- multisurface consistency (`NOT_EVALUATED`);
- all-79-video HERO (71 videos have T13 READY targets);
- A2 camera repair;
- Body (out of scope).

## 7. Deliverables

- `camera/FRAME_REGISTRY.csv`, `CAMERA_PROVENANCE_VALIDATION.csv`, `TRAJECTORY_REPAIR_RESULTS.csv`
- `target/TARGET_SELECTION_RESULTS.csv`, `T11_DIRECTION_QUOTA.csv`
- `support/SUPPORT_SELECTION_RESULTS.csv`, `SUPPORT_CANDIDATES.csv`, `HISTORICAL_SUPPORT_COMPARISON.csv`
- `hero/HERO_EXECUTION_RESULTS.csv`
- `cleaning/CLEANING_METRICS.csv`
- `a_to_b/A_TO_B_METRICS.csv`, `INDEPENDENT_VIEW_METRICS.csv`
- `multisurface/MULTISURFACE_CONSISTENCY.csv`
- `analysis/GROUP_LEVEL_COMPARISON.csv`, `COVERAGE_COMPARISON.csv`, `FAILURE_REGISTRY.csv`, `REPRESENTATIVE_CASE_SELECTION.csv`
- `VALIDATION_39.json`, `VISUALIZATION_INDEX.html`
- `METHOD_MIGRATION_MAP.csv`, `HERO_EXECUTION_RESULTS.csv` and `HERO/HISTORICAL_REGRESSION_RESULTS.csv`
