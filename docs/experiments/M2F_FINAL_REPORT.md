# M2F FINAL REPORT — admission restoration and metric-depth diagnosis

**Task:** TASK-M2F-ADMISSION-RESTORATION-AND-METRIC-DEPTH-DIAGNOSIS-001  
**Branch:** `exp/TASK-M2F-ADMISSION-RESTORATION-AND-METRIC-DEPTH-DIAGNOSIS-001`  
**Output:** `runs/m2f_metric_depth_diagnosis/`

## 0. Status

```text
HISTORICAL_SELECTION_ACTUALLY_RESTORED      = false
CAMERA_ADMISSION_ACTUALLY_ENFORCED          = false
T10_TARGET_SELECTION_USED                   = true
T11_DIRECTION_SELECTION_USED                = false
T13_SUPPORT_SELECTION_USED                  = true
W0_BRANCH_REPAIR_ACTUALLY_ATTEMPTED         = false
A_TO_B_TARGET_CAMERA_CORRECT                = true
HISTORICAL_REGRESSION_PASS                  = true
ORIGINAL_19_SURFACES_REVIEWED               = true
CAD_HERO_DEPTH_COMPARISON_COMPLETE          = true
RGB_HERO_DEPTH_COMPARISON_COMPLETE          = true (data exists; sparse Polyp points)
SUPPORT_CONTROLLED_EXPERIMENT_COMPLETE      = false
CAMERA_CONTROLLED_EXPERIMENT_COMPLETE       = false
SIX_VIEW_AND_CROSS_SECTION_COMPLETE         = false (19 six-view + 3 multisurface; no strict cross-sections)
ALL_39_GROUPS_ATTEMPTED                     = true
HUMAN_REVIEW_PENDING                        = true
```

The 217 M2E HERO surfaces are reused. They are **conditional**, not all formally admitted: after target/support eligibility checks only **110/217** tuples pass; 107 fail.

## 1. Deterministic A-to-B repair

Old M2E call used source camera A:

```python
rp.render(V,F,Cv,K,Cmap[target],I,ring)
```

Corrected M2F call uses target B camera/K:

```python
rp.render(V,F,Cv,B["K"],Cmap[B_id],I,ring)
```

A behavioral test with non-identical A/B poses changes the valid projection by 1,339 pixels. All 651 corrected rows carry `target_B_camera_used=true`, B K/pose hashes and tuple/mesh identity.

Re-evaluation of 217 targets × 3 T13 supports:

| Metric | Old wrong-A (311) | Corrected B (651) |
|---|---:|---:|
| target coverage mean | 0.482 | **0.833** |
| target coverage median | 0.502 | **0.905** |
| RGB MAE mean | 25.46 | **17.95** |
| RGB MAE median | 23.82 | **15.57** |
| predicted outside target median | 3,790 | **303** |

The old 311 records are retained only as `M2E_ORIGINAL_A_TO_B_INVALID.csv`; they are not formal quality evidence.

## 2. Original 19 surfaces

Groups and counts:

```text
GP_Ip_12.0mm_closed_R10_single_refY   8
GP_Is_9.79mm_closed_R10_single_refY   3
GP_Is_14.0mm_closed_R10_single_refY   8
```

All 19 have six-view Raw/Cleaned images with target/support directions plus true World X/Y/Z, black Ring CAD, fixed group metric bounds. Three multisurface overlays are in `visualization/multisurface_six_views/`.

## 3. CAD-HERO depth

Ring CAD ray depth was cast with the **native K and target pose**; unnormalized `K^-1[u,v,1]` gives axial-Z parameter directly. Valid ring pixels require label=2, finite CAD and HERO depth.

| Group | Targets | CAD-HERO signed median | Ratio median |
|---|---:|---:|---:|
| G01 Ip12 R10 | 8 | 4 near 0 (`−0.36…+2.81`), 4 near **−17 mm** | 0.56–1.07, bimodal |
| Is 9.79 R10 | 3 | `−0.19, +0.03, −0.11 mm` | 0.996–1.001 |
| Is 14 R10 | 8 | `+0.20…+0.70 mm` | 1.011–1.027 |

Effective Ring coverage is 79–98%. Large G01 deviations are not a global constant offset; they are target/support-dependent.

## 4. RGB-HERO depth

Actual W0 points observed in the target camera were transformed to target axial Z and compared at the corresponding native pixel. The available RGB points are sparse and mostly background: e.g. one G01 target had 87 comparisons but only 2 Polyp points. Therefore RGB-HERO is usable as a targeted check, not a dense truth surface. Per-target counts and signed/MAE values are in `RGB_HERO_DEPTH_COMPARISON.csv`.

Observed pattern: Is 9.79 remains close to CAD; G01 remains bimodal; no evidence supports a single global HERO depth scale correction.

## 5. Admission and selection reality

- Frame registry: **766** views.
- Raw and clean mask hashes differ on only **28** views; clean sidecar is distinct where available.
- Source-video hash: **missing locally** for all views.
- T10/T11 target records: 622; T11 executed but final HERO targets remained the T10 list.
- T13 support records: 316; 217 READY.
- Post-hoc target+support eligibility: **110/217 READY**, 107 not.
- M2E HERO execution was therefore not gated by admission; this is an unresolved engineering defect.
- A2 branch repair and controlled support/camera replacements were not executed.

## 6. Direct answers

1. **Why does G01 deviate from Ring?** Four of eight G01 surfaces are ~17 mm closer to the camera than the Ring CAD, four are near zero. It is a target/support-dependent depth branch, not a constant scale. Camera/support causality cannot be separated because A2 repair and controlled support replacement were not run.
2. **Is Is 9.79 stable?** In the three existing surfaces, CAD-HERO signed medians are −0.19, +0.03 and −0.11 mm, ratios ~1.00. This is stable near Ring for these inputs; support-combination stability was not experimentally tested.
3. **Is Is 14 abnormal?** All eight surfaces are +0.2…+0.7 mm from CAD, ratio 1.01–1.03. The anomaly is not a global depth scale error; it is local shape/orientation/visibility or camera related, not isolated here.
4. **Did correct admission improve quality?** Cannot be concluded. Admission is post-check only (110/217); no formally gated new HERO batch exists. The large A→B improvement after correction is from fixing the B camera, not from admission.
5. **Does T13 high score guarantee metric depth?** No. G01 contains both near-Ring and −17 mm surfaces under T13-selected tuples. Epipolar consistency does not determine metric translation/depth.
6. **CAD/RGB/HERO pattern?** Is 9.79 is CAD-consistent; Is 14 is small-offset; G01 bimodal with large negative CAD-HERO difference. RGB validation points are too sparse/background-heavy for a dense independent conclusion.
7. **Can support changes repair depth?** Not tested; `SUPPORT_SENSITIVITY.csv` is explicitly NOT_EXECUTED.
8. **Did camera repair improve MVS?** Not tested; no A2 cameras and `CAMERA_ONLY_COMPARISON.csv` is NOT_EXECUTED.
9. **Deterministic vs unresolved?** Fixed: B camera in A→B, true six-view directions, 19-surface review. Unresolved: admission enforcement, T11 final use, A2 repair, source-video hash, independent B, support/camera controlled experiments.
10. **Ready for body?** No. Depth attribution remains confounded; admission and A2 are incomplete.

## 7. Files

- `evaluation/M2E_ORIGINAL_A_TO_B_INVALID.csv`, `M2E_CORRECTED_A_TO_B.csv`, `M2F_A_TO_B.csv`
- `depth_diagnosis/CAD_HERO_DEPTH_COMPARISON.csv`, `RGB_HERO_DEPTH_COMPARISON.csv`, `DEPTH_SCALE_DIAGNOSTICS.csv`, `SURFACE_RING_SPATIAL_METRICS.csv`
- `selection/HERO_TUPLE_VALIDATION.csv`, `T10_TARGET_SELECTION.csv`, `T11_DIRECTION_SELECTION.csv`, `T13_SUPPORT_CANDIDATES.csv`
- `engineering/FRAME_REGISTRY.csv`, `INPUT_IDENTITY_VALIDATION.csv`, `REGRESSION_TEST_RESULTS.json`, `METHOD_REUSE_RECEIPTS.csv`
- `visualization/original_19_surfaces/`, `multisurface_six_views/`, `depth_diagnosis/`, `figures/A_to_B/`
- `VALIDATION_39.json`, `VISUALIZATION_INDEX.html`
