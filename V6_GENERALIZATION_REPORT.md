# M2F8 — V6 Generalization Report

**Status:** `EXECUTED_PARTIAL`  
**Branch:** `exp/TASK-M2F8-V6-GENERALIZATION-001`  
**Input:** fresh M2F6 2D selection from RAW, 10 videos, 5 groups  
**V6 runs:** `runs/m2f8_v6_general/v6/`  
**B (shared-input causal):** not started because the human explicitly deferred freezing the common RAW input.

## 1. Did V6 execute uniformly on 10 videos?

**Yes, with one shared generalized adapter.** All 10 videos used the same V6/V5 source modules (`track005`, `local_ring_sfm`, `validate_select`, `select_supported_views`, official `run_mvs_adapter3`), the same validation thresholds, and the same R5/R10 ring formulas parameterized by physical CAD (3.1/0.6 or 5.6/0.6). No group-specific repair branch was added.

| Group | Video | Ring | V6 v0 VALIDATED | v1 | HERO unsupported | HERO surfaces |
|---|---|---|---:|---:|---:|---:|
| IIa14 | 004 | R10 | 1 | 0 | 2 | 2 |
| IIa14 | 005 | R10 | 0 | 0 | 2 | 0 |
| Ip12 | 004 | R10 | 0 | 0 | 2 | 0 |
| Ip12 | 005 | R10 | 3 | 0 | 2 | 2 |
| Ip20 | 004 | R10 | 4 | 0 | 3 | 3 |
| Ip20 | 005 | R10 | 0 | 0 | 2 | 0 |
| Ip8.8 | 004 | R5 | 0 | 0 | 2 | 0 |
| Ip8.8 | 005 | R5 | 3 | 0 | 2 | 2 |
| Is14 | 004 | R5 | 5 | 0 | 4 | 4 |
| Is14 | 005 | R5 | 0 | 0 | 2 | 0 |

Totals: **10/10 videos executed; 5 videos have ≥1 VALIDATED camera; 13 HERO surfaces; 22 unsupported MVS cases; version 1: 0/10 videos pass**.

## 2. Which videos maintain metric depth?

13 generated surfaces have Ring HERO/CAD ratio medians **0.9977–1.0192**, ratio MAE **0.0169–0.0368**, residual MAE **0.648–1.836 mm**. Surface nearest-neighbor medians are **0.193–0.529 mm** where multiple surfaces exist.

This supports approximately correct **Ring-region metric depth** for the generated surfaces. It does **not** establish polyp-body accuracy. Seven videos produced no surface because all their cameras were `MODEL_PREDICTED` and support selection correctly failed; no threshold was lowered.

R5 is operational but not uniformly successful: Is14/004 gives 5 validated and 4 surfaces; Ip8.8/005 gives 3 and 2; Ip8.8/004 and Is14/005 give 0.

## 3. V6 vs M2F6

M2F6's current read-only baseline (`formal_002`) has 15–16 HERO per group and coverage medians 0.763–0.946. The V6-GENERALIZED run has only **13 HERO surfaces total** under the preserved V6 validation. These are **not paired** Target/Support comparisons; M2F6 numbers are group-level reference only. V6 is not shown superior by this comparison.

## 4. Camera / Support / HERO adapter attribution

**Not established.** The shared RAW input was not frozen by instruction. Therefore:

- no A/B/C/D controlled input exchange;
- no camera-only or support-only causal result;
- no HERO adapter equivalence result.

`HERO_ADAPTER_EQUIVALENCE.csv`, `CAMERA_SUPPORT_ABLATION.csv`, and `METRIC_DEPTH_ATTRIBUTION.md` are intentionally status tables, not fabricated comparisons.

## 5. Long-run evidence

The V6-GENERALIZED runs have real stage logs and output tables but **do not yet emit the M2F7 `RUN_STATE.json`/`RUN_TRACE` contract**. This is a remaining engineering gap; the previous raw M2F7 trace was not overwritten or backfilled. Future runs must use `RUN_RESUME_CONTRACT.md` and a unique run id.

## Conclusion

V6 can be parameterized and executed across R10/R5 with one adapter, but its strict camera validation is not a general success mechanism: five of ten videos produce zero validated cameras, and only 13 surfaces survive. The generated surfaces retain good Ring-region metric-depth consistency. No historical module should enter the formal mainline from this result alone; B causal work remains unstarted.

## Adapter detail

For each video, the current M2F6-selected middle/last frames are used as the V6 reference/heldout. Their actual raw identities are recorded in each run's `inputs/REFERENCE_RECEIPT.json`; the unmodified V6 scripts still query protocol IDs 459/516, so only those two protocol fields are aliased, not the image path or camera. This is an ADAPT boundary, not a second support algorithm.
