# Method and reuse audit

This is a Body-anchored ray-depth alternating pilot, not per-source ICP, SRAR official output, fusion, or an absolute-accuracy measurement.

| Intended mechanism | Actual implementation |
|---|---|
| 018 shared Body | Unchanged `p3d.Case`, `FreeVertices`, original world-mm INITIAL, observed and solid faces kept separately. Original FIT/HOLDOUT silhouette split and Ring A/B/C/D maps retained. |
| Official differentiable rendering | `p3d.py`: official PyTorch3D rasterizer, detached CAD depth ordering from VISIBILITY_ORDER_REPAIR; `NativeDepth` reuses original barycentric world-point interpolation and fixed miss cost on **all native trusted observations**. |
| Full observation supervision | All 75 FIT HERO sources contribute to one sum, not sequential Body overwrites. Original 018 FIT cameras provide the unchanged silhouette objective. New sources additionally contribute their native foreground/ray-qualified geometric evidence, not new silhouette-camera optimization. This is a deliberate minimal adaptation, not a claim of 75 full-image silhouette terms. |
| Original cleaning | 017/018/MAX FACE_EVIDENCE and TRUSTED subsets referenced read-only; UNCERTAIN/REJECTED/UNKNOWN never become strong geometry. Tiny components audited but no new component deletion. Original face/pixel IDs retained. |
| Three source coefficients | `native_multi.corrected`, `Source.points`, analytic inverse-transpose normal transform; native observation and archived mesh each retain their own original pixel rays and grid. Coefficients mm, no rotation/translation/scale degrees of freedom. |
| Robust bounded estimation | `bias_proposal`: SciPy TRF soft-L1, analytic fixed-correspondence point-plane Jacobian; data-only rank/SVD check before regularization; fixed source sample up to1024; global coefficient and actual axial correction bounds. Reassociation error/coverage and native CAD order checked after solve. |
| Strong correspondence | `correspond`: signed normal agreement, metric distance, same-source first layer, projected foreground, CAD front order, local reprojection. Full native counts for acceptance/evaluation. |
| Distinct geometry | Behind another source surface remains occlusion/unexplained. CONFLICT requires two qualified, independent direction/parent groups supporting a free-space proxy. Labels are not physical truth. |
| No-hit gradient fix | `weak_anchors` searches only same-camera-visible foreground-connected near-ray triangles, excludes caps via observed F. Official PyTorch3D point-face operator applied as one point/one admitted triangle per batch; no global nearest-surface loss. Sparse unmatched regions lacking an admissible face retain UNEXPLAINED and fixed miss cost. |
| Relative shape prior | Exact 018 Edge/Laplacian/Normal/unsupported priors. No implemented ARAP term is claimed. Ring/base are hard guard constraints, not fictional differentiable losses. |
| Safety | `safe_geometry.GeometryGuard` reused; contact-coherent proposal from016; all parameters, Adam state and guard state restored at rejection. Cumulative native corrections and Body world-mm displacement bounded. Dense64 final Ring audit, inherited tiny penetration explicitly remains a defect. |
| Acceptance | Full fixed-correspondence objective with bias prior, fixed-native first-hit and matched coverage, independently recomputed fixed-N geometry score, and guard all required. Strict zero net coverage drop is a conservative pilot rule; failure of this rule does not prove the route impossible. |
| Fixed association vs dynamic source points | Corrected code keeps face/pixel IDs fixed while rebuilding source target XYZ from current theta. Earlier snapshot-based outer check archived, not hidden. B0/B2 exactly unchanged at theta0; only B1/B3 rerun. |
| Holdout / GT | HOLDOUT and independent HERO evaluated only after all formal predictions freeze. No GT files, ICP, HERO re-inference or camera recovery. Historical ancestors may have seen current heldout views: current split is update-stage, not fully independent end-to-end. |

Implementation paths: `code/native_multi.py`, `body_multi.py`, `run_multi.py`, `evaluate_multi.py`, `synthetic_tests.py`, `preflight_multi.py`, `check_real_gradients.py`, `finish_checks.py`. Reused source SHA receipts: `provenance/REUSED018_CODE.json`. Actual original code vs modifications and freeze records are retained separately.

The pilot uses five outer rounds maximum and up to two accepted Body updates per round, not a claim of full convergence or topological reconstruction. A deterministic exact outer rollback is a stopping fixed point. A retained zero-update state is a reported failure to improve, not hidden replacement by another reconstruction route.

Mature references inspected:

- [SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html): bounded TRF/robust least squares; installed version recorded separately.
- [Open3D distance queries](https://www.open3d.org/docs/release/tutorial/geometry/distance_queries.html): actual RaycastingScene mesh distances and first-layer visibility.
- [PyTorch3D point-face autograd](https://pytorch3d.readthedocs.io/en/latest/_modules/pytorch3d/loss/point_mesh_distance.html): reused C++/CUDA distance derivative.
- [SRAR reference implementation](https://github.com/huangqx/MultiScanRegistration) and [primary SRAR discussion](https://www.cs.utexas.edu/~huangqx/sig_20_uq.pdf): shared latent surface / alternating registration workflow inspiration only. This task replaces scan SE(3) with three ray-depth coefficients and keeps a PyTorch3D Body. No official SRAR solver is claimed.
- [Open3D ARAP](https://www.open3d.org/docs/release/tutorial/geometry/mesh_deformation.html): enhancement reference, not executed or included as a new ablation.

Contract repair R3: the inherited native first-layer depth term is now gated by the same full-native MATCHED mask as strong correspondence supervision. Conflicts, unexplained and unknown rays retain fixed diagnostic miss penalties but have no strong depth gradient. Eligible unexplained no-hit points only use the restricted weak point-face term. The earlier ungated results and reports were excluded and archived. Strong-gate gradient tests and modules-off baseline tests were rerun before formal R3. This fixes an implementation deviation from the user task, without changing weights, thresholds, cases or using HOLDOUT/GT ranking.
