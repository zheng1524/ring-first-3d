# E4 Body-E DXY repair: Phase-0 frozen protocol

## Scope and freeze

This is `TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`, created from commit `492725ffd8e2fac86fe18099a87f7ef6d6d93b3b` of the read-only predecessor `TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001`.  Phase 0 audits inputs only.  It does not run DXY, optimize an ellipsoid, read GT, read Body-U parameters, update a camera, update HERO, or invoke A2/resection.

The 75-source denominator is fixed: G03=18, G05=16, G01=26, G06=15. `VIEW_INVENTORY.csv` and `provenance/PHASE0_SOURCE_BINDING.json` are the frozen input binding. The audit program is `code/phase0_audit.py` (SHA256 `d08758c69c4645e67fc1c8c9882c57fb8873519abfbd62cfa7bb834beb7fdd2f`).

## Frozen input and DXY rule

- Official DXY checkout: `/home/liu/new-polyp-dxy`, exact commit `75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`, `VERSION=DXY-MID-1.0.0rc1`; intended entry point `dxy_mid.pipeline.measure_files`.
- Every source has a direct original RGB and original uint8 label mask binding; 75/75 masks decode as one-channel labels containing exactly the permitted classes 0, 1, and 2.
- All four cases are `R10`. The sole DXY scale argument will be the **10.0 mm inner diameter**. The recorded midline radius (5.6 mm) and wire diameter (0.6 mm) are explicitly not DXY inputs.
- Phase 1 will retain only official DXY native-pixel `candidate.center_native` and `candidate.basis_native` for E1. It must never consume a DXY millimetre result, historical DXY prediction, DT core, or OpenCV replacement ellipse. Missing official geometry becomes `NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY`.

## Binding version discrepancy

The task statement names `TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/config/FINAL_CAMERA_POOL.json`. That file is absent at this commit. The present, hash-audited replacement is `config/RAW_CAMERA_CANDIDATES.json`; this is recorded as a substitution rather than silently renamed. Binding follows the predecessor's rule: source `view_id`/aliases first, then metadata RGB SHA where available. 46 sources have both checks; 29 archived OLD018 sources have no `target_SHA` field but have exactly one view-ID candidate.

## Coordinate and view eligibility freeze

The inventory is not a declaration that all images can be jointly fitted.

| pool | sources | Phase-0 status |
| --- | ---: | --- |
| video004 | 58 | Same-video candidate pool; 33 have a frozen metric pose and 25 do not. |
| video005 | 15 | Separate pending cross-video audit; 10 have a frozen metric pose and 5 do not. |
| independent photos | 2 | Separate; both lack a frozen metric pose. |

`TASK-E4-RING-ANCHORED-JOINT-BA-021` provides cross-video RGB/Ring evidence for G01 only. It does not establish G03, G05, or G06 video004/video005 compatibility. Phase 2 must therefore treat videos as separate coordinate pools by default; it may certify a joint G01 pool only after an explicit audit. Photos remain separate unless a metric pose and coordinate relationship are independently verified. No missing pose is inferred, synthesized, or replaced with Body-U.

## Planned methods (not yet executed)

E1 will use official DXY geometry converted exactly by `q=(p-c)B^{-T}` and `||q||²<=1`; E2 will use every original Polyp-mask pixel. Both will use the same nine-parameter ellipsoid, Ring CAD, camera set, three fixed starts, bounds, SciPy TRF budget, and 2D loss. The historical A1 `depth_parts` / HERO XYZ term is prohibited for this initialization. Candidate selection must consider only finite, geometrically valid, normal optimizer-success results; all starts, including failures, must be retained.

## Phase gates

1. Phase 1: official DXY regeneration for all 75 bindings, with DXY provenance and source hashes.
2. Phase 2: view qualification and a frozen FIT/HOLDOUT list. Missing-pose sources are not FIT eligible. No cross-video combination is presumed.
3. Phases 3–4: only after Phase-2 freeze, fit and evaluate E1/E2 fairly. GT remains unavailable to fitting, view selection, and model selection.

No Phase 1–4 action has occurred at this Phase-0 freeze.
