# M2D FINAL REPORT — W0 repair and real MVS validation

**Task:** TASK-M2D-W0-REPAIR-AND-MVS-VALIDATION-001
**Branch:** `exp/TASK-M2D-W0-REPAIR-AND-MVS-VALIDATION-001`
**Output:** `runs/m2d_w0_mvs_validation/`

## 0. Authoritative status

```text
W0_INPUT_PROVENANCE_VERIFIED          = false
TRAJECTORY_REPAIR_ACTUALLY_EXECUTED    = false
ALL_79_VIDEOS_PROCESSED                = false
FINAL_CAMERA_MANIFEST_FROZEN           = true (A1 retained)
HERO_TUPLE_VALIDATION_PASS             = true (112 unique tuples)
HERO_BATCH_ACTUALLY_EXECUTED           = true (112/112 PASS)
ALL_39_GROUPS_ATTEMPTED                = false (28 groups have valid tuples)
MVS_GEOMETRY_EVALUATION_COMPLETE       = false (A→B/independent complete; B→A partial)
A_TO_B_VISUALIZATION_COMPLETE          = false (8 representative, 28 group sheets; full 336-pair gallery missing)
REPRESENTATIVE_MVS_GALLERY_COMPLETE    = false (8 3-view images only; six-view/Ring gallery incomplete)
HUMAN_REVIEW_PENDING                   = true
```

This is a real MVS run, but **not a completed A2-repair or 39-group downstream study**. The 112 successful HERO tuples are actual native MVSAnywhere outputs, not READY/ELIGIBLE predictions.

## 1. Real HERO execution

- 112 unique validated input tuples; each target + 3 supports;
- 112/112 PASS, 0 FAIL;
- 28/39 groups, 36/79 videos covered;
- target/support frames include M2A bridge frames where needed;
- native resolution 352×640; metric axial-Z depth in mm;
- model/checkpoint loaded once; each output has `HERO_native.npz`, `RAW_NATIVE_MESH.npz`, `CLEANED_NATIVE_MESH.npz`, `INFERENCE.json`, `INPUT_MANIFEST.json`.

The earlier one-target smoke is superseded by this batch. Six bridge-view interface failures were fixed by expanding the prepared-view lookup; they are not reported as scientific failures.

## 2. MVS surface metrics

| Metric | Result |
|---|---:|
| HERO unique tuples | 112 |
| HERO PASS | 112 |
| Target depth valid median | 1.000 |
| Polyp depth coverage median | 1.000 |
| A→B pairs | 336 |
| B→A pairs (B has HERO) | 30 |
| Independent-view pairs | 336 |
| A→B coverage median | 1.000 |
| A→B inside-target-Polyp median | 0.955 |
| A→B colour median absolute difference | 16 (8-bit) |

The 1.000 depth-valid and 1.000 Polyp-coverage medians are **not** accuracy proof. They mean the native depth is finite/positive in the evaluated region. A→B colour error remains substantial (median 16), and B→A is only available for 30 pairs. No GT or independently calibrated surface error was used.

Raw and cleaned meshes are both stored. The current clean rule is identity on the native mesh (no point removal); `cleaned_retention=1.0`. This is explicitly not a claim that a sophisticated cleaning step was applied.

## 3. S0/S1/S2 coverage

Validated target/support tuples:

| Arm | Ready targets | Videos ready | Groups ready |
|---|---:|---:|---:|
| S0 | 8 | 5 | 5 |
| S1 | 55 | 31 | 26 |
| S2 | 63 | 36 | 28 |

112 unique tuples are shared across arms where the exact target/support set is identical. S1/S2 support membership differs on 284/316 previously generated target rows; the M2D ready counts above are the operational counts after target+support+relative-geometry validation.

## 4. Visual assets

- `visualization/all_group_mvs_contact_sheets/` — one group sheet for each of 28 MVS groups, plus per-tuple depth sheets;
- `visualization/representative_mvs/` — 8 automatic representative 3-view meshes;
- `visualization/representative_a_to_b/` — 8 actual target-surface-to-B overlays;
- `VISUALIZATION_INDEX.html` — local browsable index.

A full 79-video camera/Ring projection gallery was not regenerated; that requirement remains incomplete.

## 5. Direct answers

1. **Which camera branches were repaired?** **None.** Seven T2 and three T3 videos were detected; no A2 candidate search/BA was executed. `TRAJECTORY_REPAIR_ACTUALLY_EXECUTED=false`.

2. **Which large changes are real motion?** Not established. T2/T3 are diagnostic; no intermediate-frame verification or BA repair was completed. The old claim that large motion was merely T1 is not repeated.

3. **Which anomalies remain unresolved?** All detected T2/T3 remain unresolved; A1 cameras are retained with `BRANCH_UNRESOLVED` in `camera/W0_FINAL_MANIFEST.csv`.

4. **Can reliable segments be retained?** Yes at the W0/input level: 79 A1 W0 files are retained; 112 tuples from 36 videos produced actual HERO outputs. This is not evidence that all cameras in those videos are correct.

5. **Can S0-excluded cameras produce valid MVS?** S1/S2 add actual target tuples, but there is no paired S0-vs-S1 MVS comparison on identical target/support tuples. Therefore no causal claim.

6. **Did S1 materially expand MVS coverage?** Operationally yes: S0 5 groups/8 targets vs S1 26 groups/55 targets vs S2 28 groups/63 targets. This is coverage, not proven quality.

7. **Did S2 improve local MVS/A→B?** Not established. S2 support sets differ, but a paired same-tuple S1/S2 HERO comparison was not run.

8. **A1/A2 camera MVS comparison?** Not executed; no A2 cameras exist.

9. **Do HERO surfaces coincide in metric space?** Not evaluated. A→B projection coverage is high, but B→A only 30 pairs and no GT surface distance; no claim of metric overlap.

10. **Remaining causes?** A2 camera branching is unresolved; 11 groups had no valid target/support tuple; B→A coverage is partial; A→B colour error is high; independent-view geometry lacks GT. Camera, support selection, depth prediction and visibility are still confounded.

11. **Are HERO surfaces ready for Body?** Not yet. The current evidence supports local MVS visualization, not a validated 39-group body study. Body was intentionally not run in M2D.

## 6. Files

- `camera/W0_FINAL_MANIFEST.json`, `camera/W0_79_VIDEO_RESULTS.csv`, `camera/W0_39_GROUP_SUMMARY.csv`
- `camera/TRAJECTORY_PER_FRAME.csv`, `camera/TRAJECTORY_REPAIR_RESULTS.csv`
- `admission/CAMERA_ROLE_ADMISSION.csv`, `admission/HERO_TARGET_SELECTION.csv`, `admission/HERO_SUPPORT_SELECTION.csv`, `admission/TUPLE_VALIDATION.csv`
- `hero/HERO_EXECUTION_RESULTS.csv`, `hero/HERO_SURFACE_METRICS.csv`, `hero/HERO_ASSET_MANIFEST.json`
- `a_to_b/A_TO_B_METRICS.csv`, `B_TO_A_METRICS.csv`, `INDEPENDENT_VIEW_METRICS.csv`, `PAIR_SELECTION.csv`
- `analysis/GROUP_LEVEL_COMPARISON.csv`, `COVERAGE_COMPARISON.csv`, `PAIRED_COMPARISON.csv`, `REPRESENTATIVE_CASE_SELECTION.csv`, `FAILURE_REGISTRY.csv`, `STORAGE_USAGE.csv`
- `VALIDATION_39.json`, `RESUME_MANIFEST.json`, `VISUALIZATION_INDEX.html`
