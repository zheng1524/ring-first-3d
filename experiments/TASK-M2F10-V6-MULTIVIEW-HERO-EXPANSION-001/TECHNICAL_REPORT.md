# TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001 — Technical report

## Route composition

| Stage | route_id@version | Entry | Current input → output | Decision | Smoke evidence |
| --- | --- | --- | --- | --- | --- |
| RAW frame preparation | `rf-m2f6-unified-observation@1` | `tools/m2f5_unified.py::prepare_one_m2f6` | RAW MP4 → current RGB, clean Mask, K, selected frame receipts | ADAPT: optional four real supplements; recompute from RAW | Ip12/005 and Is14/005 current candidate manifests |
| Ring, tracks, BA, validation | `rf-m2f9-v6-generalized@1` | `tools/m2f8_v6_general.py` calling frozen V5/V6 scripts | current observations → Ring poses, tracks, two BA versions, primary V6 statuses | REUSE | Ip12/005 and Is14/005 `RUN_STATE.json` |
| Target/Support | `rf-m2f10-v6-multiview@1` | existing `tools/m2f8_v6_general.py::adapt_all_supported_targets` | all current cameras → original V6 legal three-source tuples | ADAPT: target scheduling and at most three source combinations; original ranking and admission unchanged | Ip12/005 37 legal tuples; Is14/005 zero after recovery |
| HERO and metric mesh | `rf-m2f10-v6-multiview@1` | frozen `run_mvs005_supported.py`, frozen `package_surfaces.py` via narrow AST boundary | verified tuple → native depth → independently packaged supported mesh | ADAPT: remove old two-case packaging tail; retain frozen inference and per-case geometry | Ip12/005 15 independent supported meshes; Is14/005 zero |
| Native and A→B audit | `rf-m2f10-v6-multiview@1` | `tools/m2f8_v6_general.py` | final attempt native/accepted outputs → target, video, group tables | REUSE existing CAD ray and reprojection metrics | Ip12/005 17 native depths and 45 accepted A→B pairs |
| Visualization | `rf-m2f10-v6-multiview@1` | `tools/m2f8_render_v6.py` | original meshes/native depth and current cameras → six-view, sampled observations, status path | REUSE existing renderer and M2F6 montage | Ip12/005 multi-surface; Is14/005 rejected previews |

The frozen V6 Support conditions remain: Support cameras have `VALIDATED` status; each shares at least 15 RGB tracks with the target; each tuple contains three distinct real sources. The frozen packager's geometry body has no extra per-mesh quality threshold. Its final comparison assumed exactly two cases. Removing that assumption permits individual supported meshes; it does not promote preview HERO depths to accepted surfaces.

## Source identity and experimental boundary

- Inherited M2F9 report commit: `b791c9affa74e848f04792cb600f8b95040bba3a`.
- Frozen V6 selector SHA-256: `f8439f53565baff7f1afcedc652109b47333fe80d364d1bab88e5a7515640128`.
- Frozen supported HERO runner SHA-256: `353dc7f3ed2baf7383f45f141d51ad074e14fdc723efc4cc4b3a7b59d02ab46f`.
- Frozen packager SHA-256: `5c8d01c0fb3cb9d1169dfdb489636357e2ad744bfe09ca0d0cec12647ab05f15`.
- The formal runner commit is `a38d4c82`; the formal run ID is `M2F10-FORMAL-20261125-02`.
- `M2F10-FORMAL-20261125-01` was stopped before completion when an intervening visualization commit changed HEAD during execution. That directory remains an aborted diagnostic and is excluded from all final statistics.

No frozen Ring, track, BA, validation, HERO, CAD, intrinsics, DXY, depth conversion or Support scoring source was edited. No mesh registration, depth scaling, GT-based selection or new acceptance threshold was used.

## Smoke findings

The Ip12/005 smoke produced 15 independent supported meshes, 17 native HERO depths and 45/45 A→B metric evaluations. The unfiltered Ring ratio median was 1.0090, with native Ring MAE median 0.959 mm. Its multi-surface six-view shows visible side-view layering despite the increased surface count. Ring depth agreement and output quantity do not establish scientific multiview consistency.

The Is14/005 smoke used exactly one recovery with four real raw frames (574, 204, 38, 315), recomputed the full current observation and V6 route, and still had 0 `VALIDATED` cameras and 0 legal supported tuples. Its two preview native depths remain in the diagnostic directory; no accepted mesh was created.

The full ten-video results, failures, input hashes, visual index and final acceptance decision are in [M2F10_FINAL_REPORT.md](../../M2F10_FINAL_REPORT.md).
