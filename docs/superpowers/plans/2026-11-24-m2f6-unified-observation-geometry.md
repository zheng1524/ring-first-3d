# M2F6 Unified Observation and Metric Geometry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore a single raw-video route whose observations connect, whose Ring-first W0 is data-driven, and whose raw HERO surfaces are evaluated in their actual metric positions across the ten specified videos.

**Architecture:** Continue `tools/m2f5_unified.py` as the one formal orchestrator. Reuse frozen INIT/DXY, track005, Ring candidates, `local_ring_sfm.initialize`/BA, historical `version_score`, T10/T13, HERO, mesh renderer and B-camera reprojection. Add only candidate-selection, reference-selection, recovery and provenance glue at existing boundaries. Keep M2F5 outputs immutable; write M2F6 results to `runs/m2f6_unified/`.

**Tech Stack:** Python 3.12, NumPy, OpenCV/SIFT, Pandas, SciPy, frozen Ring-first and HERO adapters, pytest.

---

## File map and invariants

- `tools/m2f5_unified.py`: parameterize output root/RUN_ID, current-data candidate sampling, one W0→T10/T13 route, bounded recovery loop and runtime trace. Preserve existing CLI semantics where possible.
- `tools/run_w0_camera.py`: select reference from current Ring/SIFT evidence and compare frozen initialization versions with `unified_camera.version_score`; retain an explicit legacy policy for regression. Produce one selected B0/W0, not two official W0s.
- `tools/m2f5_hero_eval.py`: bind actual tuple inputs before inference, use per-group CAD inside the group loop, and render existing or new raw meshes with six directions and 5 mm scale.
- `src/ring_first_3d/views/pipeline_adapter.py`: use the existing single local admission pool and T13 validation; any adapter added here must preserve core T10/T13.
- `docs/registry/routes.yaml`: reconcile pending versus executed route versions, then register only the demonstrated M2F6 composition with source hashes and smoke evidence.
- `tests/test_m2f6_pipeline.py`: behavior tests for the boundaries above; no tests that merely count rows.
- `experiments/TASK-M2F6-UNIFIED-OBSERVATION-GEOMETRY-001/TECHNICAL_REPORT.md`: one concise scientific and engineering report.

Never edit official HERO, metric unprojection, Ring CAD, K or DXY source. No Body, GT or HERO depth enters camera recovery. No output-based deletion of failed curves or surfaces.

## E0 — Render the retained M2F5 baseline correctly

- [x] Add a failing renderer test with R5 and R10 fixture CAD meshes; assert the selected CAD is loaded per group, six labels are target/support/support/X/Y/Z, and a 5 mm bar is drawn from `actual_mesh_image` pixels/mm.
- [x] Run `PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -m pytest tests/test_m2f6_pipeline.py -q`; record the expected failure.
- [x] Extract the existing M2F5 render loop into a callable that accepts `input_root`, `output_root`, group and video, preserving every raw mesh and coloring each target. Move CAD loading into the group loop; invoke the callable without HERO for the baseline render.
- [x] Re-render the existing ten M2F5 mesh sets into `runs/m2f6_unified/baseline/visualization/multisurface/`. Record source mesh hashes, Ring kind and GT pose unknown. Compare these figures to retained M2F5 originals before any new W0 run.
- [x] Re-run the renderer test and commit the E0 glue, test and selected baseline images; push the branch.

## E1 — Current-data reference and historical branch scoring

- [x] Write failing tests for a connected synthetic Ring/SIFT graph: a high-connectivity, Ring-supported frame wins over one nearest raw frame 459; disconnected candidates fail explicitly; only training evidence enters the reference score.
- [x] Add one reference-choice adapter to `run_w0_camera.py` after `pair_data`. Consume current `q_train`/Ring candidate evidence and edge inlier counts; store the per-reference evidence and chosen index. Keep `--reference-policy legacy459` for replay; the M2F6 route uses the current-data policy.
- [x] Run the existing `local_ring_sfm.initialize(..., version=0/1)` and frozen BA for both candidates where available. Call existing `unified_camera.version_score` on each training-side solution, select the lower score and write one official B0/W0. Preserve both trial receipts as diagnostics only.
- [x] Smoke G03/005 and G01/005 with identical prepared inputs and a new output root. Compare reference, branch, connectivity and Ring/held errors; CAD-HERO is reserved for newly recomputed HERO.
- [x] Run E1 tests and existing W0 tests, then commit and push E1 changes and small score tables.

## E2 — Current-data 2D candidate and observation selection

- [x] Write failing tests that candidate selection never reads c2w/3D direction, does not read frozen frame lists, chooses variable observation counts, favors nonduplicate 2D Ring appearances and preserves an inlier-connected frame graph.
- [x] Use `prepare_view` and DXY `ring_holes.run` for a bounded, temporally distributed raw-video candidate pool. Reuse T10's locked pixel expressions for sharpness/contour/Ring visibility before its direction statement. Use Ring ellipse appearance only as a **2D** diversity proxy.
- [x] Reuse M2A `features019.matches`/match graph evidence for connection, with train-side SIFT inliers; select one connected observation set by image quality, 2D diversity and overlap. The formal frame count follows the observed graph, not a fixed 16.
- [x] Keep candidate and selected PREPARED manifests separate. Hash every candidate cache, RGB, raw/clean Mask and K. Re-run E2 tests; compare G03/005 and G01/005 against E1 with all downstream settings held fixed.
- [x] Commit and push E2 code, tests and small observation tables.

## E3 — Bounded real-frame recovery and complete re-execution

- [ ] Write failing tests for RGB graph disconnection, insufficient Ring `q_train`, and T13 with fewer than three supports; each must request real candidate frames and then rerun tracks, Ring, B0/W0 and selection. A two-round, four-frame-per-round budget must end in an explicit failure.
- [ ] Reuse the M2A C2/B1R components: select bridge candidates by RGB inliers to disconnected components or Ring visibility to Ring-poor frames. All added frames use the same `prepare_view` and DXY-clean path as initial observations.
- [ ] Within `m2f5_unified.py`, rebuild the current PREPARED manifest after supplementation and call the same W0 and T10/T13 functions again. Preserve the earlier attempt as evidence; do not lower geometric requirements or reuse prior W0 poses.
- [ ] Smoke G06/004 and a stable G03 video, then run tests and commit/push the bounded recovery implementation.

## E4 — Centre, Anchor and current T10/T13 inputs

- [ ] On the E3 outputs, calculate both W0 scene-point mean and known Ring/world origin direction blocks for all ten videos; log angular changes, selected anchors and T13 tuple changes without evaluating GT or changing thresholds.
- [ ] Choose one shared centre definition based on current camera/Ring geometry and the successful controls, then pass it to `direction_blocks` and the existing T10 quality adapter. Keep `selection.select_views` and `validate_t13` unchanged.
- [ ] Write a test proving T13 receives the same current RGB, clean Mask, K and c2w as the tuple receipt. Recheck that historical REJECT labels do not indirectly veto the approved single local pool.
- [ ] Run E4 tests, commit and push the input adapter and centre diagnostic table.

## FINAL — Ten-video formal replay, evaluation and registration

- [ ] Remove any use of `tools/m2f5_trace.py` from the formal path. Emit append-only RUN_TRACE records at every actual stage call; record failure and hashes then, never after the fact. Call existing `tuple_receipt()` immediately before each HERO invocation and verify it against the actual arrays.
- [ ] Run the sole M2F6 entry on G01, G03, G06, Ip 8.8 R5 and Is 14 R5 (004/005 each), from the original videos into a fresh independent output root. Preserve every failed video, Target and surface in the denominator.
- [ ] Generate the ten-video before/after six-view panels, candidate RGB/Mask contact sheets, camera tracks, Target/Support and inlier tables, per-target CAD-HERO depth ratio, multisurface distances, and B-camera A→B. Do not use the metrics to drop a surface.
- [ ] Update `docs/registry/routes.yaml`: reconcile inline confirmed versions with old pending records; register the exact M2F6 composition and source SHA only after its smoke and real-run evidence exists.
- [ ] Run focused regressions plus the M2F5 inherited suite; inspect real images and source hashes; write the task report with success preservation, failure improvement or non-improvement, and remaining metric/GT limitations.
- [ ] Explicitly stage only code, registry, logs, small metric tables, receipts and selected PNGs. Commit and push; confirm remote SHA with `git ls-remote` before claiming synchronization.

## Plan review

The E0–E4 order matches the approved PM decision. Camera recovery uses only Ring/RGB training evidence, the same local admission/T10/T13/HERO route serves all videos, and no frozen mathematical core changes. A missing reusable method or need for a new geometry algorithm stops implementation for human decision.
