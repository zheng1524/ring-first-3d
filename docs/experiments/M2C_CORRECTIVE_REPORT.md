# M2C CORRECTIVE IMPLEMENTATION REPORT

**Task:** TASK-M2C-CORRECTIVE-COMPLETION-001
**Branch:** `exp/TASK-M2C-CORRECTIVE-COMPLETION-001`
**Output:** `runs/m2c_corrective_completion/`

## 0. Status — partial, not a completed A+B run

```text
DETERMINISTIC_ERRORS_FIXED              = true (CAD, final-point depth, endpoint T2/T3 detection)
CACHE_PROVENANCE_VERIFIED               = false
A2_UNIFIED_EXECUTION_COMPLETE           = false
A2_BRANCH_REPAIR_EXECUTED               = false
S0_POLICY_VERIFIED                      = true
S1_TRAJECTORY_POLICY_VERIFIED           = true
S2_LOCAL_COMBINATION_VERIFIED           = true
HERO_ACTUALLY_EXECUTED                  = true (one real target)
HERO_FULL_39_EXECUTED                   = false
BODY_ACTUALLY_EXECUTED                  = false
ALL_39_GROUPS_ATTEMPTED                 = false
DOWNSTREAM_EVALUATION_COMPLETE          = false
REPRESENTATIVE_CASES_COMPLETE           = false
STORAGE_POLICY_VERIFIED                 = true
```

This report does not claim a full 39-group HERO/body experiment. The HERO smoke is real; all other HERO/body rows are explicitly not executed.

## 1. Correctness fixes

### CAD

`ring_cad.py` is the authoritative interface:

```text
R5  = 3.1 mm centerline, 0.6 mm wire
R10 = 5.6 mm centerline, 0.6 mm wire
```

`tools/m2b_global_branch.py` now gets its radius from `ring_cad.params`.
`tools/m2b_visualize.py` now calls:

```python
torus_contours(c2w, K, ring_radius=R, ring_wire=wire)
```

No positional argument binding remains in the current corrected path. Test verifies both R5/R10 and two contours.

### Positive depth

The previous implementation projected all initialization `X` points into every camera. The corrected implementation reads:

```text
final W0 points
final W0 c2w
point_track_ids
tracks005 xy observation mask
```

For each camera it counts only points actually observed by that camera. Held points are triangulated separately from held tracks; source/target fractions come from the actual first/last observed view of each held track, not copied from camera 0/-1. `POSITIVE_DEPTH_VALIDATION.csv` has 766 camera rows; observed-point denominators and negative counts are stored.

Full per-point trace is in `POSITIVE_DEPTH_VALIDATION.csv`; this is not a 100% filtered fraction.

## 2. Trajectory classification

The old endpoint logic was replaced by explicit distances:

```text
d(C_{i-1},C_i), d(C_i,C_{i+1}), d(C_{i-1},C_{i+1})
```

with separate rotation/translation criteria. A T2 is a camera that differs from both neighbors while the neighbors agree; this is not merely a large adjacent angle.

Results across 79 videos:

| Class | Videos |
|---|---:|
| T0 continuous | 4 |
| T1 sampling gap | 48 |
| T2 isolated branch | **7** |
| T3 consecutive branch | **3** |
| T4 unresolved | 17 |

The previous implementation reported 20 T2 / 8 T3; that count was not a valid jump-return detector.

`TRAJECTORY_PER_FRAME.csv` now has 766 per-camera rows (not only 79 video summaries). `TRAJECTORY_REPAIR_RESULTS.csv` marks T2 as `BRANCH_UNRESOLVED`; **no A2 repair was executed**. Consequently `A2_BRANCH_REPAIR_EXECUTED=false`.

## 3. S0/S1/S2

Common base: legal pose/CAD, finite geometry, positive-depth check from corrected per-observation depth, and no confirmed unrepaired branch.

- S0 uses the frozen strict thresholds; it does not add extra cameras.
- S1 uses the corrected trajectory class and actual graph support, not only relaxed Ring/Held thresholds.
- S2 scores each target+3-support combination with real components:
  `Q_RGB`, `Q_overlap`, `Q_baseline`, `Q_risk`.

On the shared 316 target identities:

- S1/S2 support sets differ on **284/316** targets (32 identical);
- S1 eligible cameras: 457; S2 ready targets: 167; S0 ready targets: 47;
- S0 cameras: 71; S1 cameras: 457.

This proves the two selection codes are not identical. It does **not** prove downstream superiority.

`HERO_SUPPORT_SCORE_COMPONENTS.csv` stores the S2 components and score.

## 4. Real HERO result

A legal S0 target/support tuple from G03/005 was run with the formal MVSAnywhere loader:

```text
target: ...005-raw01-12
supports: raw01-15, raw02-24, raw03-04
inference: PASS
time: 1.507 s
peak GPU: 1,508,467,712 bytes (1.51 GB)
native shape: 352 x 640
raw faces: 49,690
POLYP depth coverage: 1.000
depth valid fraction: 1.000
```

Artifacts: `hero_smoke/result/HERO_native.npz`, `RAW_NATIVE_MESH.npz`, `INFERENCE.json`, `hero_smoke/SMOKE_RESULT.json`.

This is one smoke result, not 39-group coverage. `HERO_EXECUTION_RESULTS.csv` marks only this tuple PASS.

## 5. Body and full downstream

`BODY_ACTUALLY_EXECUTED=false`. The historical `body_stage.py` is tied to the previous G01/G03/G05/G06 eight-FIT protocol and old camera directories; it was not adapted to the current 79-video W0 contract. No body metrics are fabricated.

`HOLDOUT_METRICS.csv` and `GT_METRICS.csv` are empty status tables. No GT was read.

## 6. Storage

Current free space is about 18.17 GB (16.9 GiB), 91% used. The HERO smoke wrote only 3.7 MB total output. Further full 3-arm HERO still needs the staged storage plan; no new large cache was created.

## 7. Key answers (limited)

1. **How many branches repaired?** None. Seven T2 and three T3 videos are detected; A2 repair is not executed.
2. **Which trajectories preserved?** A1 W0 cameras retained: 79 videos, 67 FULL / 12 PARTIAL, 766 poses. T0/T1 are retained; T2/T3 marked unresolved.
3. **Did S1 expand coverage?** Eligibility expanded to 457 cameras / 71 videos, but downstream HERO coverage was not run, so no efficacy claim.
4. **Did S2 improve support?** Support sets differ on 284/316; actual HERO comparison not run.
5. **Can S0-excluded cameras produce valid HERO?** Not measured beyond one S0 PASS.
6. **Which cameras are good for contour but not MVS?** Not measured; Body-C not run.
7. **Did added views improve body?** Not measured; Body-CD not run.
8. **39-group quality/coverage/paired metrics?** Only eligibility and W0 coverage; no downstream metrics.
9. **Next cross-video admission?** Do not freeze S1/S2. Use S0 anchors; S1 only for 2D attempts; T2/T3 excluded; require real HERO/body comparison first.

## 8. Why this stopped

Full 39-group HERO/body was not attempted after the one smoke because:
- A2 repair was not completed;
- the historical body pipeline requires adaptation from its 8-FIT protocol to current W0;
- the task's 39-group HERO/body run would need a separate, validated execution batch and substantially more storage.

No `READY`/`ELIGIBLE` table is presented as actual inference.
