# TASK-M2F6 — Unified Observation & Metric Geometry Refinement

## Scope and route

The formal route starts from each raw video, builds 2D candidates and cleaned masks, chooses a variable number of connected observations, runs frozen tracks and Ring-First B0/W0, selects T10 targets and T13 supports from the current W0, then calls official HERO and evaluates the retained raw meshes. The same entrypoint and parameters apply to all ten videos. The route register is `docs/registry/routes.yaml` (`rf-m2f6-unified-observation@1`). Original M2F5 outputs remain intact.

Frozen components reused: M2A C2/B1R matching and real-frame recovery, `features019.matches`, `tracks005`, `local_ring_sfm.initialize` versions 0/1, `unified_camera.version_score`, `pipeline_adapter.admission_tiers`, historical T10 Quality-Diversity and T13 Support Selection, official HERO, native metric backprojection, A→B rendering, and the existing triangle renderer. No HERO depth, Ring CAD, camera intrinsics, DXY model, or frozen geometry mathematics were changed.

The R5/R10 CAD files are the existing assets (SHA-256 `dee04ef5…` / `56bac879…`); W0 identity checks require Ring centerline/cross-section radii of 3.1/0.6 mm and 5.6/0.6 mm respectively.

## Controlled changes and evidence

| Step | Change | Controlled evidence |
| --- | --- | --- |
| E0 | Render each existing M2F5 mesh with its own R5/R10 CAD, three actual cameras plus World X/Y/Z, a 5 mm scale, and independent target colors. | `runs/m2f6_unified/baseline/visualization/multisurface/`; image identities in `baseline/BASELINE_RENDER_INDEX.json`. This is display correction only. |
| E1 | Choose reference from current Ring and RGB graph; score historical initialization versions 0/1 with existing training-side score. | `e1/E1_COMPARISON.csv`; G03/005 remains 13 ACCEPT, G01/005 remains 0 ACCEPT. |
| E2 | Select variable observation count from real 2D quality, Ring evidence and RGB connection graph. | `e2/E2_COMPARISON.csv`; G03/005 37 candidates → 30 selected and 26 ACCEPT; G01/005 40 → 26 and 0 ACCEPT. |
| E3 | Bounded two-round, four-frame-per-round real supplement; rerun features, W0 and T10/T13 after addition. | `e3/E3_COMPARISON.csv`; G06/004 0 → 3 ACCEPT after four real frames, held reprojection p95 30.14 → 12.93 px; median remains about 3.8 px. |
| E4 | Use one Ring-centered direction definition and current RGB/Clean Mask/K/c2w for Anchor/T10/T13; retain one local camera pool. | `e4/E4_CENTER_DIAGNOSTIC.csv`; prior scene proxy offsets 3.4–34.1 mm, direction changes 4.5–12.7° median. |
| E2 correction | Replace a 48-frame rounding threshold for temporal bridges with actual RGB match-edge verification. A prior 49-frame gap with a strong direct SIFT edge had caused redundant insertion. Keep existing S2 admission for 0 ACCEPT cameras; only connection, Ring observation, initialization, or T13 support deficits trigger recovery. | [Controlled comparison](e2_correction/BRIDGE_W0_CONTROLLED_COMPARISON.csv) and selected receipts: retained `formal_001` diagnostic G03/004 38 frames, held p95 22.22 px; fresh raw `e2b` 14 frames, held p95 7.09 px and 8/8 ready. Fresh raw `e2c` G01/005 initial 16 frames, 7/8 ready; bounded supplement to 24 frames still 7/8. |

E1–E4 are diagnostic comparisons, not final scientific acceptance. G01/005 did not recover during these comparisons. Current REJECT cameras stay excluded by the existing admission route; historical REJECT labels are not imported.

## M2F5 baseline for the ten-video cohort

`nn` is the median symmetric nearest-neighbor distance between independent surfaces and is a diagnostic, not GT accuracy. `CAD MAE` is Ring-label depth agreement; it alone cannot establish body pose.

| Video | HERO | A→B | Coverage median | CAD MAE mm | nn mm |
| --- | ---: | ---: | ---: | ---: | ---: |
| G01/004 | 7 | 21 | 0.758 | 17.67 | 5.61 |
| G01/005 | 7 | 21 | 0.898 | 2.98 | 9.89 |
| G03/004 | 8 | 24 | 0.940 | 2.83 | 0.48 |
| G03/005 | 8 | 24 | 0.937 | 1.14 | 0.29 |
| G06/004 | 7 | 21 | 0.820 | 7.75 | 2.43 |
| G06/005 | 6 | 18 | 0.805 | 4.55 | 7.48 |
| Ip 8.8 R5/004 | 8 | 24 | 0.925 | 0.75 | 0.28 |
| Ip 8.8 R5/005 | 7 | 21 | 0.913 | 0.96 | 0.54 |
| Is 14 R5/004 | 8 | 24 | 0.956 | 0.72 | 0.39 |
| Is 14 R5/005 | 8 | 24 | 0.854 | 13.18 | 1.11 |

Source: retained `runs/m2f5_unified` evaluation CSVs. GT deployment pose is unknown. Values are from prior results and are **not** M2F6 improvements.

## Formal execution and scientific verdict

Formal result root: `runs/m2f6_unified/formal_002`. The earlier `formal_001` directory is retained only as a diagnostic of the temporal-bridge error. The actual run creates per-video append-only `RUN_TRACE`, recovery receipts, current W0 packets, selection receipts, pre-HERO tuple receipts, raw meshes, six-view images, and metric CSVs. Failed videos and targets remain `NOT_EVALUABLE` with NaN metrics.

The formal run completed 10 videos, 80 selection targets, 78 native HERO calls, 234 A→B pairs and 10 six-view comparisons. G01/005 and G06/005 each retain one `NOT_EVALUABLE` target after two bounded supplement rounds. [W0 and selection summary](final/W0_SELECTION_SUMMARY.csv), [HERO execution](final/hero/HERO_EXECUTION_RESULTS.csv), [A→B](final/evaluation/A_TO_B_METRICS.csv), [per-target CAD-HERO](final/evaluation/CAD_HERO_GEOMETRY.csv), [all surface pairs](final/evaluation/MULTISURFACE_CONSISTENCY.csv), [video comparison](final/FINAL_VIDEO_COMPARISON.csv) and [runtime traces](final/RUN_TRACE/) are the audit tables.

The table reports M2F5 → M2F6. `NN` is the median pairwise symmetric nearest-neighbor distance in mm; the p90 column shows why a low median can hide an outlier. Ring CAD depth MAE and A→B coverage do not alone prove body pose. All original target meshes contribute to the displayed metrics.

| Video | W0 ACCEPT / ready | A→B coverage | CAD MAE mm | NN median mm | NN p90 after mm | Six-view judgement |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [G01/004](final/visualization/comparison/GP_Ip_12.0mm_closed_R10_single_refY_004.png) | 0 / 8 | .758 → .747 | 17.67 → 18.01 | 5.61 → 2.21 | 16.75 | Separated layers remain; fail |
| [G01/005](final/visualization/comparison/GP_Ip_12.0mm_closed_R10_single_refY_005.png) | 0 / 7 | .898 → .918 | 2.98 → 1.00 | 9.89 → .59 | 10.16 | Six surfaces converge; one ~10 mm outlier and one unready target; fail |
| [G03/004](final/visualization/comparison/GP_Ip_20.0mm_closed_R10_single_refY_004.png) | 0 / 8 | .940 → .945 | 2.83 → 3.90 | .48 → .47 | .95 | Compact surfaces retained; Ring depth slightly worse |
| [G03/005](final/visualization/comparison/GP_Ip_20.0mm_closed_R10_single_refY_005.png) | 11 / 8 | .937 → .935 | 1.14 → 1.01 | .29 → .33 | .42 | Compact surfaces retained |
| [G06/004](final/visualization/comparison/GP_IIa_14.0mm_closed_R10_single_refY_004.png) | 1 / 8 | .820 → .732 | 7.75 → 12.54 | 2.43 → 3.77 | 7.25 | Stacked layers and wrong Ring relation; fail |
| [G06/005](final/visualization/comparison/GP_IIa_14.0mm_closed_R10_single_refY_005.png) | 0 / 7 | .805 → .767 | 4.55 → 9.41 | 7.48 → 2.31 | 5.14 | Some surface convergence, metric depth worse; fail |
| [Ip 8.8 R5/004](final/visualization/comparison/GP_Ip_8.8mm_closed_R5_single_refY_004.png) | 12 / 8 | .925 → .920 | .75 → .78 | .28 → .22 | .41 | Compact surfaces and Ring relation retained |
| [Ip 8.8 R5/005](final/visualization/comparison/GP_Ip_8.8mm_closed_R5_single_refY_005.png) | 12 / 8 | .913 → .908 | .96 → .77 | .54 → .18 | .34 | Compact surfaces and Ring relation retained |
| [Is 14 R5/004](final/visualization/comparison/GP_Is_14.0mm_closed_R5_single_refY_004.png) | 7 / 8 | .956 → .954 | .72 → .73 | .39 → .34 | .82 | Compact surfaces and Ring relation retained |
| [Is 14 R5/005](final/visualization/comparison/GP_Is_14.0mm_closed_R5_single_refY_005.png) | 0 / 8 | .854 → .893 | 13.18 → 7.41 | 1.11 → 8.02 | 11.16 | Two separated depth clusters; fail |

The original sampling error was at the observation adapter: a 49-frame gap with a strong direct RGB edge was treated as longer than `2 × median step = 48`, causing G03/004 to select 38 nearly redundant frames. Using the existing match graph reduced it to 14; held p95 improved from 22.22 to 7.09 px before HERO. S2 is the only downstream camera pool; a zero ACCEPT count no longer creates an extra gate. Supplementation runs only when an actual RGB/Ring/initialization/Support deficit exists.

The remaining failures are **not solved**. Is 14/005 W0 jumps 114.7° and 64.8 mm between real frames 186 and 241 despite 168 RGB RANSAC inliers; G01/005 jumps 55.4° and 38.1 mm between frames 440 and 461 despite 231 inliers ([all camera steps](final/CAMERA_STEP_DIAGNOSTIC.csv)). The current W0 and official HERO then place those Targets in separate world-space clusters. G06/004 has no comparable trajectory jump, yet native HERO Ring depth is about 27.3 mm while the current camera rays meet the correct CAD at about 39.0 mm (median ratio .69; stable G03/005 ratio 1.00; [depth-source diagnostics](final/DEPTH_SOURCE_VIDEO_DIAGNOSTIC.csv)). These are observations, not proof that either camera metric scale or HERO native depth alone caused the G06 discrepancy. No depth, pose, mesh or CAD was directly altered to improve the numbers. [Representative sampled RGB, Clean Mask and W0 trajectories](final/visualization/observations/) show the actual inputs.

All ten videos use identical code, Ring-center definition, selection rules, recovery budget, HERO and evaluation; only their data and R5/R10 CAD differ. The successful reference videos remain visually compact, but G01/G06 and Is 14/005 do not meet the scientific goal of consistent surfaces and correct Ring-relative metric geometry. The registered route remains `formal_usable: false`; wider execution was not started. Further work on the unresolved camera and depth ambiguity requires a new approved method decision, not group-specific thresholds or direct depth correction.

## Verification and delivery

The focused behavior suite passed **24 tests**. A separate final audit verified 10 video receipts, 78 unique HERO tuples with pre-call input receipts, 234 A→B rows, 80 CAD rows including two `NOT_EVALUABLE`, and one geometry runtime trace per video. Formal W0/HERO ran at code commit `140dc5f8`; the final runtime geometry summary used `0e6d7372`. File SHA-256 values are recorded in `docs/registry/routes.yaml` and [artifact index](final/FINAL_ARTIFACT_INDEX.json). The audit copy contains 10 before/after six-view PNGs, selected observation contact sheets, small CSVs, logs, all tuple receipts and append-only traces; large videos, weights and raw Mesh files stay in the local result root.

## Reproduction

```bash
PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/m2f5_unified.py --m2f6 --stage all --groups GP_Ip_12.0mm_closed_R10_single_refY,GP_Ip_20.0mm_closed_R10_single_refY,GP_IIa_14.0mm_closed_R10_single_refY,GP_Ip_8.8mm_closed_R5_single_refY,GP_Is_14.0mm_closed_R5_single_refY --videos 004,005 --output-root runs/m2f6_unified/formal_002
PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/m2f5_hero_eval.py --m2f6 --groups GP_Ip_12.0mm_closed_R10_single_refY,GP_Ip_20.0mm_closed_R10_single_refY,GP_IIa_14.0mm_closed_R10_single_refY,GP_Ip_8.8mm_closed_R5_single_refY,GP_Is_14.0mm_closed_R5_single_refY --videos 004,005 --output-root runs/m2f6_unified/formal_002
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/m2f5_summary.py --output-root runs/m2f6_unified/formal_002
PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -m pytest -q tests/test_m2f6_pipeline.py tests/test_m2f5_pipeline.py tests/test_w0_manifest_closure.py
```

The exact formal directory is single use. A new run needs a new empty output directory to preserve runtime evidence.
