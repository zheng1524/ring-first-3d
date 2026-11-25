# M2F10 V6 Multiview HERO Expansion Implementation Plan

> Execute inline with `executing-plans`; verify with `verification-before-completion`. The user explicitly authorized implementation without another approval gate.

**Goal:** Run one V6 route from RAW on ten videos, use every current camera with a legal V6 Support tuple, attempt one bounded real-frame recovery, and preserve native predictions separately from accepted surfaces.

**Architecture:** Extend `tools/m2f8_v6_general.py`, the existing route entrypoint. Keep the frozen V5/V6 Ring, track, BA, validation, HERO, CAD and depth code unchanged. Adapt only the source selection loop and the packager's fixed two-case tail; reuse `m2f6_observations.choose_real_supplements` for one new RAW preparation and full rerun. Every execution version has its own run directory and live trace.

**Tech stack:** Python 3.12, NumPy, OpenCV, PyTorch, Open3D, pytest.

## Source contract and baseline

- [ ] Confirm M2F9 commit `b791c9af`, its 10-video audit, and source SHA for V6 `select_supported_views.py`, `run_mvs005_supported.py`, `package_surfaces.py`.
- [ ] Record the precise V6 admission condition: Support camera `VALIDATED`, shared RGB track overlap at least 15, exactly three source cameras. Note that `package_surfaces.py` itself has no further per-surface quality gate; its final two-case comparison is a batch assumption.
- [ ] Run baseline focused tests: `PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -m pytest -q tests/test_m2f9_v6_general.py tests/test_m2f6_pipeline.py tests/test_ring_cad_r10_r5.py`.

## A/B: Expanded reference and bounded Support schedule

- [ ] Add behavioral tests in `tests/test_m2f10_v6_general.py`: all eligible target indices appear once, target order favors angular separation, each tuple uses only original V6 legal Support cameras, at most three distinct tuples per target, and a successful first inference skips later tuples.
- [ ] Add a narrow AST adapter in `tools/m2f8_v6_general.py` that changes only the V6 supported selection loop's two-reference iterable. Retain its original overlap and angle ranking body and save the original and expanded case receipts with source hashes.
- [ ] Schedule at most three original-rank Support combinations per target. Invoke the original supported HERO body once per needed combination and stop for that target after its first successful inference. Preserve all failed attempts and every native depth.

## D: Independent surface packaging

- [ ] Add behavioral tests proving one failed Target cannot prevent an unrelated legal Target's mesh, preview RAW_HERO is never counted as accepted, and no case may be packaged without the original V6 supported-view admission.
- [ ] Adapt the original `package_surfaces.py::main` AST only at input case selection and its two-case comparison tail. Execute its unchanged per-case metric backprojection, mesh, topology and receipt body for each successful supported case. Keep rejected native depth in `raw/` and record explicit failure states.

## C: One real observation supplement

- [ ] Add tests that recovery uses at most four real frame numbers, starts a distinct attempt directory, recomputes all chosen frames from RAW, and redoes Ring, tracks, BA, validation, selection and HERO. Reject reuse of first-attempt cameras or meshes.
- [ ] Add an optional supplemental frame-number input to `m2f5_unified.prepare_one_m2f6`; recompute its current candidate sweep and the selected frames from RAW, then include only the selected real supplements. The normal no-supplement path must remain bytewise behavior-equivalent.
- [ ] Reuse `choose_real_supplements` with current candidate features and RGB matches; run exactly one second attempt when accepted independent surfaces are below six. If no legal supplement is found, retain a `NO_REAL_SUPPLEMENT` result.

## Evidence, experiment and delivery

- [ ] Smoke test one baseline good and one failure video; verify source hashes, tuple receipts, `RUN_STATE` and the accepted/diagnostic boundary. Commit the stable code before formal runs.
- [ ] Run the same entrypoint on all ten RAW videos under one new run ID. Audit every native prediction and every accepted surface by Target, video and group; include full camera status/reasons and recovery attempt IDs.
- [ ] Reuse existing six-view, trajectory, multivideo and surface-distance tools for selected images. Do not alter points, scale or view bounds to conceal failures.
- [ ] Register `rf-m2f10-v6-multiview@1` in `docs/registry/routes.yaml`, write `M2F10_FINAL_REPORT.md`, run focused and regression tests plus hash/resume verification, explicitly add selected small artifacts, commit, push, and verify the remote SHA.

**Stop rule:** A required change to frozen BA, validation thresholds, official HERO, CAD, DXY or metric conversion requires a separate user decision.
