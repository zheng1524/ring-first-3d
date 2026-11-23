# M2_DEVELOPMENT_HANDOFF — Cross-Video View Selection & 2D Identity

**Source:** M1-FINAL-CONSOLIDATION-39
**Source commit:** `0be83ff6810c18e43d4762975347d0cb5138dbb7`
**Primary M1 run:** `runs/m1_final_39`
**M2 scope:** cross-video joint view selection, direct 2D identity, camera-availability policy.
**M2 explicitly does not start:** cross-video H initialization, H+X Joint BA, local camera correction, HERO/body reconstruction.

---

## 1. 39-group / 79-video W0 coverage

| Metric | Value |
|---|---:|
| groups | 39 |
| videos | 79 |
| W0 generated | 64 |
| W0 numerically valid | 64 |
| W0 quality accepted (>=1 ACCEPT) | 22 |
| W0 quality limited (0 ACCEPT) | 42 |
| not computable | 15 |
| implementation errors | 0 |

The 15 not-computable videos are not M2 inputs. They are documented in `W0_79_VIDEO_RESULTS.csv` with `failure_stage`/`failure_reason`: 11 disconnected Ring pose graphs, 4 insufficient Ring observations.

## 2. Videos with at least one ACCEPT camera (22)

These are the primary M2 anchors. Each has 10 W0 poses unless noted.

| group_id | video | ring | ACCEPT |
|---|---|---:|---:|
| `GP_IIa_14.0mm_closed_R10_single_refY` | 4 | R10 | 1 |
| `GP_IIa_5.2mm_closed_R10_single_refY` | 1 | R10 | 1 |
| `GP_Ip_10.3mm_closed_R5_single_refY` | 5 | R5 | 8 |
| `GP_Ip_12.0mm_closed_R10_single_refY` | 4 | R10 | 1 |
| `GP_Ip_20.0mm_closed_R10_single_refY` | 4 | R10 | 3 |
| `GP_Ip_20.0mm_closed_R10_single_refY` | 5 | R10 | 6 |
| `GP_Ip_4.0mm_closed_R5_single_refY` | 7 | R5 | 1 |
| `GP_Ip_5.6mm_closed_R10_single_refY` | 4 | R10 | 1 |
| `GP_Ip_5.6mm_closed_R10_single_refY` | 5 | R10 | 3 |
| `GP_Ip_6.4mm_closed_R10_single_refY` | 5 | R10 | 1 |
| `GP_Ip_6.4mm_closed_R10_single_refY` | 6 | R10 | 4 |
| `GP_Ip_7.1mm_closed_R10_single_refY` | 4 | R10 | 3 |
| `GP_Ip_8.8mm_closed_R10_single_refY` | 4 | R10 | 1 |
| `GP_Ip_8.8mm_closed_R5_single_refY` | 5 | R5 | 1 |
| `GP_Ip_9.7mm_closed_R5_single_refY` | 4 | R5 | 3 |
| `GP_Is_14.0mm_closed_R10_single_refY` | 4 | R10 | 6 |
| `GP_Is_14.0mm_closed_R10_single_refY` | 5 | R10 | 3 |
| `GP_Is_14.0mm_closed_R5_single_refY` | 4 | R5 | 3 |
| `GP_Is_18.0mm_closed_R5_single_refY` | 4 | R5 | 2 |
| `GP_Is_6.5mm_closed_R10_single_refY` | 4 | R10 | 2 |
| `GP_Is_7.0mm_closed_R5_single_refY` | 4 | R5 | 2 |
| `GP_Is_8.8mm_closed_R5_single_refY` | 4 | R5 | 1 |

Only 8/22 are R5; R10 dominates the accepted set.

## 3. Videos with W0 but no ACCEPT camera (42)

These have numerically valid W0 and full per-view admission evidence, but all views are `QUARANTINE` or `INSUFFICIENT_EVIDENCE`. They are useful for:

- within-video diagnostic comparisons;
- local Ring/RGB consistency;
- later camera-availability policy research (M2-C).

They must **not** be silently promoted to cross-video anchors. Their `camera_result.npz` still contains all cameras; use `admission_status` per view.

## 4. Videos with no W0 (15)

Use `W0_79_VIDEO_RESULTS.csv` filter `w0_generated == false`. Reasons:

- `Ring pose graph disconnected; no free SfM fallback` (11);
- `INSUFFICIENT_RING_OBSERVATION` (4).

They are `BLOCKED_QUALITY_GATE` or `INSUFFICIENT_EVIDENCE`, never `IMPLEMENTATION_ERROR`. M2 must report them as upstream-blocked, not retry a different pipeline.

## 5. Trajectory branch risk

W0 is numerically valid for 64 videos, but branch jumps are common:

| Metric | Value |
|---|---:|
| total trajectory jumps | 157 |
| median jumps per video | 2 |
| max adjacent rotation | 173.23 deg |
| max adjacent translation | 87.15 mm |

Highest-risk examples:

| group | video | max rot | max trans | jumps | ACCEPT |
|---|---|---:|---:|---:|---:|
| `GP_IIa_9.5mm_closed_R10_single_refY` | 4 | 173.23° | 15.37 mm | 4 | 0 |
| `GP_Ip_8.8mm_closed_R5_single_refY` | 4 | 137.26° | 69.43 mm | 6 | 0 |
| `GP_Ip_20.0mm_closed_R10_single_refY` | 4 | 119.37° | 87.15 mm | 4 | 3 |
| `GP_IIa_22.0mm_closed_R10_single_refY` | 5 | 119.13° | 69.08 mm | 1 | 0 |
| `GP_Is_10.5mm_closed_R10_single_refY` | 4 | 104.20° | 58.28 mm | 3 | 0 |

M2 view selection must treat these videos as branch-risk. It should prefer a single coherent branch, not simply concatenate all W0 cameras.

## 6. Which videos are safe for immediate cross-video work

Recommended initial M2 subset:

1. `GP_Ip_20.0mm_closed_R10_single_refY` (both 004/005 have ACCEPT; 3/6)
2. `GP_Is_14.0mm_closed_R10_single_refY` (both 004/005 have ACCEPT; 6/3)
3. `GP_Ip_5.6mm_closed_R10_single_refY` (both 004/005 have ACCEPT; 1/3)
4. `GP_Ip_6.4mm_closed_R10_single_refY` (005/006 have ACCEPT; 1/4)

These are R10. R5 accepted pairs are rarer; use them only after the R10 pilot is stable.

Videos with only one accepted side can be used for one-directional diagnostics, not full cross-video H. Videos with 0 ACCEPT or no W0 must not be used as anchors.

## 7. Frozen M1 interfaces M2 must call

- Input: `runs/m1_final_39/prepared/{group}_{video}/PREPARED.json`.
- W0: `runs/m1_final_39/{group}/{video}/W0.npz` (`c2w`, `ids`, `K`, `ring_cad_mm`).
- All cameras + admission: `camera_result.npz` (`c2w`, `ids`, `admission_status`, `raw_frames`).
- Per-view: `admission.csv`, `quality_summary.json`.
- Provenance: `RUN_MANIFEST.json` (`prepared`, `tracks`, `code`, `config`, `artifacts`).
- Summary: `W0_79_VIDEO_RESULTS.csv`, `W0_39_GROUP_SUMMARY.csv`.

Do not read `accepted_cameras.npz` alone as the full camera evidence; it is a filtered convenience file. `camera_result.npz` is the authoritative all-camera artifact.

## 8. M2 reuse plan

- Cross-video matching: reuse `features019` (pinned copy; `50cd25fd...`), not a new SIFT matcher.
- 2D identity: reuse `features019.matches` + `identity021` as reference; no requirement that all features be triangulated first.
- View selection: use W0 `admission_status`, Ring/RGB quality, direction coverage, and cross-video match connectivity. No per-group thresholds.
- 39-group regression is mandatory for M2; videos blocked at M1 remain `NOT_EXECUTED_DEPENDENCY` with the M1 reason, not a new code failure.
- H initialization/Joint BA remain M3/M4; M2 must not modify `track005`, `local_ring_sfm`, DXY, or M1 frozen files.

## 9. M2 acceptance outline

```text
expected_groups == 39
discovered_groups == 39
expected_videos == 79
M1-blocked videos reported with M1 status, not implementation errors
M2 implementation_errors == 0
every M2-eligible video actually attempted
```

Scientific outcomes (identity count, cross-video overlap, H observability) may vary by group and must be reported separately from engineering execution.
