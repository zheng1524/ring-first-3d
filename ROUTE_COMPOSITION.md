# M2F5 — Unified Route Composition (executed)

**Status: EXECUTED 13-group pipeline.** Human approval `M2F5` accepted the specified existing modules and allowed the two former GAPs to be adapted within the approved scope.

## Composition

| Stage | Route | Entrypoint | I/O | Decision | Evidence |
|---|---|---|---|---|---|
| Raw input / sampling | `rf-m2f5-input-fresh@1` + `rf-m2f5-dense-sampling@1` | `tools/m2f5_unified.py::prepare_one/sample_frames` | raw video → 12 uniform + 4 largest-gap real frames → fresh PREPARED | ADAPT (new glue) | `RUN_TRACE/*`, `prepared/*/PREPARED.json` |
| INIT + DXY 2D clean | `rf-m1-input-39@1`, `rf-m2f5-mask-clean-2d@1` | `prepare_view` + `m2c_prepare_clean.py`/DXY `ring_holes.run` | raw RGB/INIT → RGB/labels/K + clean sidecar | REUSE/ADAPT | 432 clean frames, `MASK_CLEAN_*.csv` |
| Ring CAD | `rf-native-ring-cad@2` | `native/camera.py::torus_contours` | R5 3.1/0.6; R10 5.6/0.6 | REUSE | all 13 groups |
| Track + BA + W0 | `rf-frozen-tracks005@1`, `rf-frozen-ba-local-ring-sfm@1`, `rf-w0-camera-current-tracks@3` | `tools/run_w0_camera.py` (patched: always current-run track005) | fresh PREPARED/clean → W0 | REUSE/ADAPT | 26 W0 outputs; all `tracks_source=generated_by_pipeline_current_frames`; no frozen_011 copy |
| One local admission pool | `rf-m2f5-local-admission@1` | `pipeline_adapter.admission_tiers` | W0 metrics/graph → one tolerant local pool | ADAPT | 208 target rows / 174 ready |
| Data anchor | `rf-m2f5-current-anchor@1` | `m2f5_unified.build_views` | W0 scene points mean + angular centrality | ADAPT (no historical INITIAL) | 27 current-run traces |
| T10 target | `rf-m2f5-t10@1` | `selection.select_views(quality_diversity)` | local pool → all selected targets, no top-4 truncation | REUSE of approved algorithm | 208 target rows |
| T11 | **removed from formal route** | — | control only | removed | no T11 output |
| T13 support | `rf-m2f5-t13@1` | `coverage.support_pairs` via `select_views(hero_support)`; `validate_t13` | target+pool → 3 supports + geometry gate | REUSE/ADAPT | 174 ready, 522 A2B |
| HERO | `rf-m2f5-hero-native@1` | `native/hero.py::infer` | 3 supports → native depth/Raw Mesh | REUSE | 174/174 PASS |
| Standard A→B | `rf-m2f5-a-to-b@1` | `reprojection.render/evaluate` | source Raw Mesh + **B** K/pose | REUSE | 522 pairs |
| Six-view | `rf-m2f5-six-view@1` | `_mesh_renderer.actual_mesh_image` | Raw Mesh + Ring CAD | REUSE | 174 target sheets + 25 same-video multisurface |

## Execution result

| Item | Actual |
|---|---:|
| Groups | **13/13** |
| Raw videos prepared | 27 |
| W0 selected videos | 26 |
| W0 hard failures | 1 (`GP_Is_10.5.../005`) |
| Unique HERO | **174/174 PASS** |
| A→B pairs | **522** |
| CAD-HERO rows | 174 |
| Mask-clean frames | 432 |
| Same-video multisurface pairs | 544 |

No historical PREPARED, frozen frame list, historical W0, historical Anchor/INITIAL, or historical HERO/Mesh was used. `run_w0_camera.stage_tracks` no longer copies `frozen_011`; all traces show current-run track generation. S0/S1/S2 formal parallel products and T11 formal route are removed; one tolerant local pool is used.

## Remaining real limitations

- `GP_Is_10.5mm_closed_R10_single_refY/005` has no W0 result; the group still has 8 HERO from video 004.
- CAD-HERO medians are not uniformly near zero; several groups show large offsets (e.g. `GP_Ip_12.0mm...` −13.4 mm, `GP_IIa_22.0mm...` −14.0 mm). This is reported, not hidden.
- Raw metric meshes are used directly; no 3D cleaning/fusion is applied.
