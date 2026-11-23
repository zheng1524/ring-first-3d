# M1_39_GROUP_VALIDATION

**Task:** M1-FINAL-CONSOLIDATION-39
**Primary run:** `runs/m1_final_39` (fresh prepared + 79 W0)
**Base commit before implementation:** `26c724ff15a428d028bb2f32685b543a52ab48b2`
**Implementation commit:** `0be83ff6810c18e43d4762975347d0cb5138dbb7`
**Status:** engineering validation complete; full W0 coverage not met.

## 1. Three independent conclusions

```text
ENGINEERING_39_PASS = true
W0_79_COVERAGE_PASS = false
M1_FREEZE_READY = true (engineering/interface scope)
```

- `ENGINEERING_39_PASS=true`: 39 groups discovered, 79 videos attempted, 790/790 prepared frames, 0 implementation errors, 0 unexpected exceptions, 0 missing required outputs, 0 cross-group contamination.
- `W0_79_COVERAGE_PASS=false`: **64/79** videos generated a numerically valid W0; 15 videos are not computable for documented data/quality reasons (11 `Ring pose graph disconnected`, 4 `INSUFFICIENT_RING_OBSERVATION`). No W0 was fabricated.
- `M1_FREEZE_READY=true` for the engineering/interface modules; full 79/79 W0 coverage is **NOT_MET**.

## 2. Input coverage

| Item | Expected | Actual |
|---|---:|---:|
| Groups | 39 | 39 |
| Videos | 79 | 79 |
| Registered frames | 790 | 790 prepared |
| Reference photos | 120 | 120 recorded, not used |
| R10 groups / videos | 22 / 44 | 22 / 44 |
| R5 groups / videos | 17 / 35 | 17 / 35 |

`INPUT_COVERAGE.csv` has 39 rows, all `VALID`. `W0_79_VIDEO_RESULTS.csv` has exactly 79 rows.

## 3. Video execution and W0 coverage

| Metric | Value |
|---|---:|
| attempted videos | 79 |
| W0 generated | 64 |
| W0 numerically valid | 64 |
| W0 quality accepted | 22 |
| W0 quality limited | 42 |
| W0 not computable | 15 |
| implementation errors | 0 |
| unexpected exceptions | 0 |
| missing required outputs | 0 |

### 3.1 R10 / R5 split

| Ring | videos | W0 generated | accepted videos | limited videos | not computable |
|---|---:|---:|---:|---:|---:|
| R10 | 44 | 41 | 14 | 27 | 3 |
| R5 | 35 | 23 | 8 | 15 | 12 |

R5 coverage is lower: 23/35. The 12 R5 non-computable videos are dominated by the ring observation / graph connectivity limits; this is a data-quality result, not an implementation error.

### 3.2 Videos without W0

| group_id | video | ring | status | stage | reason |
|---|---:|---:|---|---|---|
| `GP_IIa_14.0mm_closed_R5_single_refY` | 4 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_IIa_14.0mm_closed_R5_single_refY` | 5 | R5 | INSUFFICIENT_EVIDENCE | ring | INSUFFICIENT_RING_OBSERVATION |
| `GP_IIa_22.0mm_closed_R5_single_refY` | 4 | R5 | INSUFFICIENT_EVIDENCE | ring | INSUFFICIENT_RING_OBSERVATION |
| `GP_IIa_22.0mm_closed_R5_single_refY` | 5 | R5 | INSUFFICIENT_EVIDENCE | ring | INSUFFICIENT_RING_OBSERVATION |
| `GP_Ip_2.9mm_closed_R10_single_refY` | 5 | R10 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Ip_2.9mm_closed_R5_single_refY` | 5 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Ip_4.0mm_closed_R5_single_refY` | 6 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Ip_6.2mm_closed_R5_single_refY` | 5 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Is_10.5mm_closed_R5_single_refY` | 5 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Is_18.0mm_closed_R10_single_refY` | 5 | R10 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Is_18.0mm_closed_R5_single_refY` | 5 | R5 | INSUFFICIENT_EVIDENCE | ring | INSUFFICIENT_RING_OBSERVATION |
| `GP_Is_4.8mm_closed_R5_single_refY` | 4 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Is_4.8mm_closed_R5_single_refY` | 5 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Is_7.0mm_closed_R5_single_refY` | 5 | R5 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |
| `GP_Is_9.79mm_closed_R10_single_refY` | 4 | R10 | BLOCKED_QUALITY_GATE | ring_first | Ring pose graph disconnected; no free SfM fallback |

## 4. 39-group summary

| group_id | ring | videos | W0 gen/valid | frames | W0 poses | accept | quarantine | insufficient | reject | impl | execution | quality |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `GP_IIa_14.0mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 1 | 2 | 17 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_IIa_14.0mm_closed_R5_single_refY` | R5 | 2 | 0/0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | INSUFFICIENT_EVIDENCE | NOT_COMPUTABLE |
| `GP_IIa_22.0mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 12 | 8 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_IIa_22.0mm_closed_R5_single_refY` | R5 | 2 | 0/0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | INSUFFICIENT_EVIDENCE | NOT_COMPUTABLE |
| `GP_IIa_4.5mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 4 | 16 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_IIa_5.2mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 1 | 7 | 12 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_IIa_9.5mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 6 | 14 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_IIa_9.5mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 0 | 0 | 20 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_10.3mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 8 | 12 | 0 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_12.0mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 1 | 15 | 4 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_12.0mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 0 | 14 | 6 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_2.9mm_closed_R10_single_refY` | R10 | 2 | 1/1 | 20 | 10 | 0 | 0 | 10 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_2.9mm_closed_R5_single_refY` | R5 | 2 | 1/1 | 20 | 10 | 0 | 0 | 10 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_20.0mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 9 | 11 | 0 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_4.0mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 4 | 16 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_4.0mm_closed_R5_single_refY` | R5 | 3 | 2/2 | 30 | 20 | 1 | 2 | 17 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_4.7mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 0 | 0 | 20 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_5.6mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 4 | 8 | 8 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_6.2mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 8 | 12 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_6.2mm_closed_R5_single_refY` | R5 | 2 | 1/1 | 20 | 10 | 0 | 3 | 7 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Ip_6.4mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 5 | 15 | 0 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_7.1mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 3 | 14 | 3 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_8.8mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 1 | 19 | 0 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_8.8mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 1 | 13 | 6 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Ip_9.7mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 3 | 15 | 2 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_10.5mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 3 | 17 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Is_10.5mm_closed_R5_single_refY` | R5 | 2 | 1/1 | 20 | 10 | 0 | 1 | 9 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Is_14.0mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 9 | 1 | 10 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_14.0mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 3 | 4 | 13 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_18.0mm_closed_R10_single_refY` | R10 | 2 | 1/1 | 20 | 10 | 0 | 0 | 10 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Is_18.0mm_closed_R5_single_refY` | R5 | 2 | 1/1 | 20 | 10 | 2 | 6 | 2 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_4.8mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 5 | 15 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Is_4.8mm_closed_R5_single_refY` | R5 | 2 | 0/0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | BLOCKED_QUALITY_GATE | NOT_COMPUTABLE |
| `GP_Is_6.5mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 2 | 0 | 18 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_7.0mm_closed_R5_single_refY` | R5 | 2 | 1/1 | 20 | 10 | 2 | 2 | 6 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_7mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 2 | 18 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Is_8.8mm_closed_R10_single_refY` | R10 | 2 | 2/2 | 20 | 20 | 0 | 2 | 18 | 0 | 0 | COMPLETED_LIMITED | LIMITED |
| `GP_Is_8.8mm_closed_R5_single_refY` | R5 | 2 | 2/2 | 20 | 20 | 1 | 0 | 19 | 0 | 0 | COMPLETED_VALID | ACCEPTED |
| `GP_Is_9.79mm_closed_R10_single_refY` | R10 | 2 | 1/1 | 20 | 10 | 0 | 0 | 10 | 0 | 0 | COMPLETED_LIMITED | LIMITED |

## 5. Pose and quality totals (only generated W0)

| Metric | Value |
|---|---:|
| Total W0 poses | 640 |
| ACCEPT | 57 |
| QUARANTINE | 210 |
| INSUFFICIENT_EVIDENCE | 373 |
| REJECT | 0 |
| Ring MAE mean median | 1.530 px |
| Held median median | 2.684 px |
| Held P95 median | 15.502 px |
| Positive depth fraction (min) | 1.000 |
| Trajectory jump count total | 157 |
| Max adjacent rotation (max) | 173.23 deg |

The high trajectory-jump count and the 173 deg branch are **scientific quality findings**, not code exceptions. They are carried into `M2_DEVELOPMENT_HANDOFF.md` as branch-risk evidence.

## 6. Files

- `runs/m1_final_39/W0_79_VIDEO_RESULTS.csv`
- `runs/m1_final_39/W0_39_GROUP_SUMMARY.csv`
- `runs/m1_final_39/VALIDATION_39.json`
- `runs/m1_final_39/EXECUTION_FAILURES.csv`
- `runs/m1_final_39/INPUT_COVERAGE.csv`
- per-video `W0.npz`, `camera_result.npz`, `admission.csv`, `quality_summary.json`, `RUN_MANIFEST.json`, `STATUS.json` under `runs/m1_final_39/<group>/<video>/`

`EXECUTION_FAILURES.csv` contains only the header: there are no implementation errors to list.

## 7. Clean rerun

A full clean W0 rerun (`runs/m1_final_39_clean`) was executed from the same final code and the hash-verified 790-frame prepared input:

- 79/79 video rows, 79/79 identical execution statuses;
- 64/64 generated W0 files byte-identical, 0 different;
- metric max absolute difference 0.0;
- `ENGINEERING_39_PASS=true` in both runs;
- `W0_79_COVERAGE_PASS=false` in both runs.

Evidence: `runs/m1_final_39_clean/CLEAN_RERUN_COMPARISON.json`. Prepared caches were reused after 790/790 hash validation; W0 was recomputed on all 79 videos.
