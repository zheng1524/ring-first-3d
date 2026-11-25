# M2F8 FINAL REPORT — V6 Generalization & Metric Depth

**Branch:** `exp/TASK-M2F8-V6-GENERALIZATION-001`  
**V6 run root:** `runs/m2f8_v6_general/v6/`  
**Input:** fresh M2F6 2D selections from RAW, 10 videos, 5 groups.

## Answers

1. **Can V6 execute uniformly on 10 videos?** Yes, 10/10 executed through one generalized adapter and the authoritative V5/V6 Ring, track005, local BA, validation, support and HERO sources. The R5 physical CAD is parameterized once (3.1/0.6); R10 remains 5.6/0.6. No group-specific HERO repair was added.
2. **Which videos retain metric depth?** 5/10 videos have at least one VALIDATED camera and 13 HERO surfaces were produced. Their Ring HERO/CAD ratio medians are **0.9977–1.0192**, ratio MAE **0.0169–0.0368**, residual MAE **0.648–1.836 mm**. Seven videos (including Ip8.8/004 and Is14/005) correctly fail support because all cameras are `MODEL_PREDICTED`; no threshold was lowered.
3. **Difference from M2F6?** M2F6's read-only group baseline has 15–16 HERO per group and coverage 0.763–0.946. V6-GENERALIZED has only 13 surfaces total under preserved V6 validation. These are **not paired** comparisons; V6 is not shown superior.
4. **Camera / Support / HERO adapter attribution?** **Not established.** A/B/C/D were not run because the common RAW input was intentionally not frozen. `HERO_ADAPTER_EQUIVALENCE.csv` and `CAMERA_SUPPORT_ABLATION.csv` are explicit NOT_EXECUTED status tables.
5. **Which history is reusable?** The R5/R10 parameterized V6 chain can run, and generated surfaces retain good Ring-region metric depth; the strict V6 validation is not a general success mechanism. No historical module is promoted into the formal M2F6 mainline.

## Key limitations

- 5/10 videos have zero validated cameras; R5 is operational but not uniformly successful (Ip8.8/004 0, Is14/005 0; Is14/004 5, Ip8.8/005 3).
- V6 HERO surfaces are only 13, so coverage/M2F6 comparisons are not like-for-like.
- No shared-input B/C/D and no HERO adapter equivalence.
- The generalized runs have real stage logs/tables but do not yet emit the M2F7 `RUN_STATE.json`/`RUN_TRACE` contract; prior raw trace was not overwritten or backfilled.

## Deliverables

- `V6_GENERALIZATION_REPORT.md`
- `V6_10_VIDEO_COMPARISON.csv`
- `V6_HERO_GEOMETRY.csv`
- `V6_SURFACE_DISTANCES.csv`
- `V6_VISUALIZATION_INDEX.html`
- `SHARED_INPUT_MANIFEST.md` (pre-registration only)
- `HERO_ADAPTER_EQUIVALENCE.csv` (NOT_EXECUTED)
- `CAMERA_SUPPORT_ABLATION.csv` (NOT_EXECUTED)
- `METRIC_DEPTH_ATTRIBUTION.md` (deferred)
