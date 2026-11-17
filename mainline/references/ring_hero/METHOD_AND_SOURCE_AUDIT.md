# Actual implementation and frozen-source audit

This is an engineering extraction from `ring-first-3d@5636aaebd61a3d53b69f528692c4c7095df46508`, not a new registration/reconstruction experiment.

## Design → implementation

| Required method | Actual module | Fidelity / boundary |
| --- | --- | --- |
| Original Ring-first five-parameter centre/normal solve | `camera.py`, exact `decode/image_seeds/solve` in `_kernels.py` | Same seeds, retained seeds2, max_nfev35, bounds, soft-L1 and numerical tolerances |
| Actual torus rather than an image ellipse proxy | `torus_contours` / original V5 `torus_residual` | Exact perspective tangent locus; R=5.6, r=0.6mm; original region and boundary residual |
| RGB full-pose information | `rgb.py` and yaw/normal selection in `camera.py` | SIFT6000 / contrast.01; mutual ratio.72; descriptor-track mod5 holdout; same EPNP/RANSAC and LM; same yaw72-grid and branch choices |
| Formal support cameras affected by RGB/Ceres | Frozen example c2w, per-frame scope in VERSION_LOCK | Target RF solve is rerun; Ceres-refined support camera is kept. Full video Ceres solver/map build is not falsely claimed as part of this target CLI |
| Official HERO | `hero.py`, external official `DepthModel` and official inference wrapper | All535 learned tensors loaded, three fixed coordinate buffers regenerated; FP16 CUDA; same target/source/image/preprocess/refinement settings |
| Metric native geometry | `geometry.py`, exact `unproject/depth_mesh` | Axial Z, camera translations /1000 for model; depth *1000 for project; no depth resize; same0.75mm jump rule and native Pixel IDs |
| Optional original cleaning | `_clean_kernels.py`, `cleaning.py` | Original017 feature/classifier/gap functions and parameter values. Same MAX gap combination, no group-specific rules, no retained vertex motion |
| Actual-Mesh visualization | `_mesh_renderer.py`, `visualization.py` | Existing Open3D triangle ray renderer and same MAX optional face-colour adapter. Caller supplies Raw/Ring bounds, not Body or GT |

The necessary changes are module boundaries, explicit dependency paths, standard CLI/IO, unit checks, packaged configuration and version validation. Function text is checked against `provenance/MODULE_MIGRATION.csv`. There is no loss reweighting, threshold search, model replacement or newly fitted camera correction.

## ring_first_v1 and V5 are different dependencies

The historical MAX adapter obtains **unprojection and native-grid meshing** from `ring_first_v1/scripts/common.py`; it does not make that file the final camera solver. The current Ring solve combines the actual `ring_pose_contact_v1/recover.py` five-dimensional parameterization with the **V5 real-mask torus residual**. The shared torus projection is the original `scripts/geometry.py` tangent-locus function. These dependencies are separately named and hashed rather than calling everything “v1” or “v5”.

Some legacy transitive code was outside the Git tree. Its exact whole-file SHA was already recorded in the snapshot's `CAMERA_CODE_G*.json`, `HERO_CODE_AND_INTERFACE.json` or original017 `PREANALYSIS_FREEZE*.json`. The migration table points to those frozen receipts. Where a complete source blob is present in the snapshot, its direct path is recorded instead. The extracted necessary functions are now included, removing that old runtime dependency.

## Expected versions checked individually

1. Project `cameras.py`: requested SHA equals frozen snapshot bytes.
2. Project `torus.py`: requested SHA equals frozen snapshot bytes.
3. Project `infer.py`: requested SHA equals frozen snapshot bytes.
4. HERO checkpoint: full2420601860-byte file SHA equals the requested value; all learned tensors loaded.
5. **Claimed MVSAnywhere commit does not pass identity verification.** Calling Git in the old vendor directory returned the parent research repository. Its `4483e25…` commit was “Package reproducible polyp result pipeline”, not an upstream MVSAnywhere commit; official API returned422. The actual105 used Python/config files exactly match upstream5bd49bba. This provenance correction changes neither source code nor predictions.
6. DINOv2: all156 local Python files match upstream7764ea0f; verified before the final CLI run.

`docs/registry/REUSABLE_MODULES.md` was not found in the required snapshot or inspected worktree. No T14–T20 catalogue labels are invented. This remains a documentation gap; it did not justify guessing another algorithm.

## Camera/Ceres scope

The target frame has a directly reproduced RF/RGB initial camera. Support `G01_v004_raw00326` has a frozen final-vs-initial maximum matrix-element difference of0.14393199341606078; its historical selected Ceres mode and actual camera are recorded in `validation/DEMO_CAMERA_SCOPE.json`. Other selected frames keep their own original ancestry and conditional status.

Historical refinement used PyCeres2.6/Ceres2.2, released full6DoF only with enough real RGB observations (minimum10 inliers), and operated on a fixed selected subset rather than certifying every numerical pose. Its original code SHA and conditions are in VERSION_LOCK. This release does not silently replace the formal source camera with a new Ring-only result or rerun experimental019–021 BA.

## Prediction/evaluation separation

Fresh target recovery uses RGB, labels and the declared real reference map. Fresh HERO uses the four fixed cameras and actual images. Neither prediction reads historical depth values, Body, Blender GT, Dxy measurements or other-route predictions. Native Raw output is written before historical numerical comparison. Cleaning reads the new Raw/native data and known CAD, not old class labels.

The exact match of new vs old classifications is an independent post-output comparison. It is not label replay disguised as new cleaning. The fixed G01 case contains no Rejected face under these unchanged rules; Uncertain and Unknown still remain.

## Geometry fidelity

Authoritative float64 vertices, face ordering, native Pixel IDs and depth arrays are equal to the frozen result in this case. PLY is the original float32 encoding. GLB uses a documented fixed /1000 conversion into glTF metres; loading it back and multiplying by1000 is checked to within float32 precision. No fitted scale, ICP, surface deformation or hole filling occurs.

Original artefacts remain visible and quantified, including signed CAD penetration and open boundaries. The release demonstrates reproducibility, not absolute geometric correctness.
