# M2F5 FINAL REPORT — Unified 13-group reconstruction

**Branch:** `exp/TASK-M2F5-UNIFIED-ROUTE-EXECUTION-001`  
**Output:** `runs/m2f5_unified/`

## Executed

- 13 groups from **fresh raw-video sampling**; 27 raw videos prepared.
- 432 frames passed through INIT + DXY 2D Ring clean.
- Current `track005` generated in every W0 workdir; no `frozen_011` copy.
- 26 videos obtained W0; one hard failure: `GP_Is_10.5mm_closed_R10_single_refY/005`.
- One tolerant local admission pool; S0/S1/S2 formal parallel products removed.
- 208 T10 target rows; 174 unique valid tuples; no top-4 truncation.
- 174/174 HERO PASS; Raw metric Mesh retained; no 3D classify/fusion.
- 522 standard A→B pairs with B camera; 174 CAD-HERO rows; 544 same-video multisurface pairs.
- 5 M2F5 behavior tests + 22 inherited M2F2/W0 tests passed.

## Per-group results

| Group | HERO | A2B | Coverage median | RGB MAE median | CAD-HERO signed/MAE median |
|---|---:|---:|---:|---:|---:|
| GP_IIa_14.0mm_closed_R10_single_refY | 13 | 39 | 0.813 | 11.47 | −5.54 / 5.87 |
| GP_IIa_22.0mm_closed_R5_single_refY | 11 | 33 | 0.877 | 9.12 | −13.96 / 14.18 |
| GP_IIa_5.2mm_closed_R10_single_refY | 15 | 45 | 0.847 | 12.21 | −8.46 / 8.75 |
| GP_IIa_9.5mm_closed_R5_single_refY | 14 | 42 | 0.868 | 9.34 | −1.28 / 2.01 |
| GP_Ip_12.0mm_closed_R10_single_refY | 14 | 42 | 0.826 | 17.45 | −13.40 / 13.86 |
| GP_Ip_12.0mm_closed_R5_single_refY | 10 | 30 | 0.891 | 12.20 | +0.53 / 1.44 |
| GP_Ip_20.0mm_closed_R10_single_refY | 16 | 48 | 0.939 | 8.23 | −0.21 / 2.07 |
| GP_Ip_4.0mm_closed_R5_single_refY | 12 | 36 | 0.913 | 16.69 | −2.70 / 2.78 |
| GP_Ip_6.2mm_closed_R10_single_refY | 16 | 48 | 0.833 | 20.84 | −5.46 / 5.47 |
| GP_Ip_8.8mm_closed_R5_single_refY | 15 | 45 | 0.919 | 11.09 | +0.06 / 0.86 |
| GP_Is_10.5mm_closed_R10_single_refY | 8 | 24 | 0.800 | 22.46 | −11.85 / 11.85 |
| GP_Is_14.0mm_closed_R5_single_refY | 16 | 48 | 0.937 | 12.19 | −0.64 / 1.06 |
| GP_Is_18.0mm_closed_R5_single_refY | 14 | 42 | 0.875 | 13.68 | −13.37 / 13.66 |

## Engineering answer

`stage_tracks`, fresh sampling, DXY clean, W0, T10/T13, HERO, Raw Mesh, A→B and six-view all executed in one route. `RUN_TRACE` records actual stage inputs/outputs and hashes. No historical PREPARED/W0/Anchor/HERO was consumed as the formal run input.

## Scientific answer

The correct unified flow does not guarantee good geometry: large CAD-HERO offsets remain in several groups; one W0 video is non-computable. No result was removed or parameter-tuned after observing it. The next step is human review of the actual surfaces and the remaining CAD-HERO inconsistency.
