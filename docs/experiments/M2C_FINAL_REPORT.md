# M2C FINAL REPORT — W0 trajectory correctness and downstream admission

**Task:** `TASK-M2C-W0-TRAJECTORY-AND-DOWNSTREAM-ADMISSION-001`
**Base:** `888503ab8d6ad7064b4c83961185475ebc2348d1` (M2-B)
**Output:** `runs/m2c_trajectory_admission/`
**Implementation commit:** `87ef712e110837802d5c339dd677691449261aaa`
**This is a partial execution report, not a completed A+B study.** Downstream HERO/body and corrected-CAD A2 were not executed; statuses below are the authoritative result.

```text
A_CORRECTNESS_PASS                 = true
A_TRAJECTORY_REPAIR_COMPLETE       = false
A_UNIFIED_39_EXECUTION_COMPLETE    = true
B_S0_EXECUTION_COMPLETE            = false
B_S1_EXECUTION_COMPLETE            = false
B_S2_EXECUTION_COMPLETE            = false
B_DOWNSTREAM_EVALUATION_COMPLETE   = false
B_REPRESENTATIVE_CASES_COMPLETE    = false
HUMAN_REVIEW_PENDING               = true
```

## 1. What was actually run

| Item | Result |
|---|---|
| Groups / videos | 39 / 79 |
| A1 W0 generated | **79/79** |
| A1 FULL / PARTIAL | **67 / 12** |
| A1 W0 poses | 766 |
| A1 ACCEPT / QUARANTINE / INSUFFICIENT | **71 / 275 / 420** |
| Implementation errors | 0 |
| DXY clean frames | 29 (1,549 pixels changed) |
| CAD contract rows | 79, all R5=3.1 mm / R10=5.6 mm, wire=0.6 mm |
| Point-depth rows | 766 |
| S0 eligible cameras / videos | 71 / 25 |
| S1 eligible cameras / videos | 348 / 63 |
| S2 eligible cameras / videos | 348 / 63 |
| HERO execution | **NOT_EXECUTED_RESOURCE** |
| Body execution | **NOT_EXECUTED_DEPENDENCY_HERO** |

A1 uses DXY `ring_holes.run`, the unified CAD contract, complete Ring boundary observations, point-based positive depth, and all 45 frame pairs. The 12 graph-disconnected videos use the same real-component/bridge policy as before.

## Q1. DXY clean modules reused?

`ring_holes.run` (`ring_enclosed_small_background_v1`) is reused directly from the frozen DXY source. It fills only small background holes enclosed by actual Ring material, preserves the central hole, and asserts the Polyp mask is unchanged.

- 790 frames processed;
- 29 frames changed;
- 1,549 changed pixels;
- no Polyp mask change;
- no large morphological closing; no Ring central-hole fill.

The raw labels are never overwritten: `clean_labels/` is a sidecar, and `MASK_CLEAN_PER_FRAME.csv` records raw/clean Ring pixel counts, changed pixels, holes, and operation.

## Q2. CAD contract

New authoritative interface:

```text
src/ring_first_3d/mainline/native/ring_cad.py
R = ring_mm / 2 + 0.6
```

All 79 A1 W0 records validate:

```text
R5  centerline 3.1 mm, wire 0.6 mm
R10 centerline 5.6 mm, wire 0.6 mm
```

`CAD_CONTRACT_VALIDATION.csv` has 79 rows, all `radius_ok` and `wire_ok`. Projection uses explicit keyword arguments:

```python
torus_contours(c2w, K, ring_radius=R, ring_wire=r)
```

The old M2-B visualization bug (`R=ring_mm/2` and positional binding) is not reused for the local corrected review; the committed M2-B archived images were not regenerated in this task. This is a known evidence defect.

## Q3. Does complete Ring observation preserve metric geometry?

A1 produces 79/79 W0. Median Ring MAE and Held values are recorded per video in `A_correctness/W0_79_VIDEO_RESULTS.csv`; no all-data average is used as a substitute for per-video results.

The complete boundary plus DXY clean does not restore every camera to ACCEPT: 71 cameras are accepted, 275 quarantined, 420 insufficient.

## Q4. Trajectory classes (all 79 videos, actual raw-frame timestamps)

| Class | Count |
|---|---:|
| T0 continuous | 4 |
| T1 sampling gap | 34 |
| T2 isolated branch | 20 |
| T3 consecutive branch | 8 |
| T4 unresolved | 13 |

`T1` is detected from actual `dt` and motion speed, not from the old fixed 10°/5 mm threshold. T2 is a jump-and-return pattern. The 20 T2 and 8 T3 videos are **not repaired** in this run; they are preserved as unresolved evidence.

## Q5. Branch repair

**0 branches were repaired with a corrected-CAD A2 run.** M2-B A2 used the wrong CAD radius and was not reused. `GLOBAL_BRANCH_CANDIDATES.csv` / `GLOBAL_BRANCH_SELECTION.csv` are explicitly `NOT_EXECUTED` placeholders, not candidate rankings.

`TRAJECTORY_REPAIR_RESULTS.csv` marks T2 as `BRANCH_UNRESOLVED`; no interpolation is presented as a recovered camera.

## Q6. Did A1 break previously reliable trajectories?

A0 (M2-B) had 69 FULL / 10 PARTIAL / 72 ACCEPT. A1 has 67 FULL / 12 PARTIAL / 71 ACCEPT. The difference is reported in `analysis/REGRESSION_CASES.csv` and `A_correctness/RING_OBSERVATION_COMPARISON.csv`; A1 is not claimed to be uniformly better.

## Stage B: admission eligibility only

S0 is the strict historical policy:

```text
Ring MAE <= 2 px; Held median <= 4 px; Held P95 <= 8 px;
held tracks >= 20; big-error <= 10%; adjacent rotation <= 10 deg;
adjacent translation <= 5 mm; point positive depth.
```

S1 retains numerical/CAD validity, real trajectory evidence, and RGB consistency, but allows Ring MAE up to 3 px, Held median up to 6 px, P95 up to 20 px, and 6+ held tracks. S2 additionally requires at least two real graph supports; target/support selection ranks by actual RGB graph support and frame diversity.

| Arm | Eligible cameras | Videos with any | Ready targets | Ready 4-view supports |
|---|---:|---:|---:|---:|
| S0 | 71 | 25 | 30 | 16 |
| S1 | 348 | 63 | 137 | 129 |
| S2 | 348 | 63 | 137 | 129 |

S1/S2 have the same camera count because every S1 camera has at least two real graph supports in this dataset; their **support sets and rankings differ**. This is not evidence that S1/S2 produce better depth.

### Q7–Q11: downstream results

**Not measured.** HERO-S and body execution are `NOT_EXECUTED`, so this report cannot answer whether S1/S2 improve HERO depth, body reconstruction, or whether expanded admission causes body degradation. No HERO depth, body mesh, or GT metric is reported. Empty metric tables are explicitly status-only, not zero-error results.

## Q12. Which gates are necessary?

A1 and the eligibility tables support only these statements:

- numerical/CAD validity and point positive depth are hard gates;
- Ring MAE > 2 px alone should not be treated as a camera failure, but remains a soft quality/weight term;
- held tracks < 20 is an evidence-sufficiency limitation, not proof of geometric error;
- T2/T3 branch errors remain a separate hard exclusion until repaired;
- S1/S2 eligibility expands the candidate pool from 71 to 348 cameras, but downstream utility is unproven.

No new policy is frozen.

## Q13. Group-level statistics

`analysis/GROUP_LEVEL_COMPARISON.csv` and `VIDEO_LEVEL_COMPARISON.csv` use all 39 groups/79 videos as fixed denominators. `COVERAGE_COMPARISON.csv` reports eligibility coverage. `PAIRED_COMPARISON.csv` is eligibility-paired only; no downstream paired metric exists.

## Q14. Representative cases

`analysis/REPRESENTATIVE_CASE_SELECTION.csv` selects one extreme per trajectory class by maximum adjacent rotation, automatically. These are analysis targets, not tuned examples. No full HERO/body representative gallery exists.

## Q15. W0 admission for the next stage

Recommended interim position:

1. Use S0 for cross-video **anchor** eligibility.
2. Use S1 only for **2D matching attempts** and controlled local HERO support exploration, not as a 3D anchor.
3. Use S2 only after target/support relative geometry is validated by actual HERO.
4. Keep T2/T3 `BRANCH_UNRESOLVED` out of HERO support until a corrected A2 repair exists.
5. Do not freeze S1/S2 before a real HERO/body comparison.

## Deliverables

- `A_correctness/`: `CAD_CONTRACT_VALIDATION.csv/json`, `MASK_CLEAN_PER_FRAME.csv`, `RING_OBSERVATION_COMPARISON.csv`, `POSITIVE_DEPTH_DIAGNOSTICS.csv`, `TRAJECTORY_DIAGNOSTICS.csv`, `TRAJECTORY_REPAIR_RESULTS.csv`, `W0_79_VIDEO_RESULTS.csv`, `W0_39_GROUP_SUMMARY.csv`, `GLOBAL_BRANCH_*` (explicit NOT_EXECUTED).
- `B_admission/`: `CAMERA_ROLE_ADMISSION.csv`, `S0_S1_S2_ELIGIBILITY.csv`, `HERO_TARGET_SELECTION.csv`, `HERO_SUPPORT_SELECTION.csv`, execution/status tables.
- `analysis/`: coverage, group/video, paired, regression, representative selection, failure registry.
- `VALIDATION_39.json`: authoritative statuses.

## Remaining failures

- A2 corrected-CAD universal branch repair: not run.
- HERO-S: not run.
- Body initialization/update: not run.
- Full 79-video corrected visual gallery: not generated for A1.
- M2-B archived visual CAD bug: not regenerated; only the local correction exists.
