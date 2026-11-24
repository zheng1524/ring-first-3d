# HISTORICAL MVS REPRODUCTION REPORT

**Task:** TASK-M2D-HISTORICAL-MVS-REPRODUCTION-AND-VISUAL-CORRECTION-001  
**Branch:** `exp/TASK-M2D-HISTORICAL-MVS-REPRODUCTION-AND-VISUAL-CORRECTION-001`  
**Output:** `runs/m2d_mvs_reproduction/`

## 0. Status

```text
HISTORICAL_HERO_REPRODUCED       = true  (4/4 bitwise)
INPUT_IDENTITY_VERIFIED          = true  (4/4 source hashes)
PIXEL_ROUNDTRIP_PASS             = true  (max 3.5e-13 px)
HERO_RAW_SHAPE_VERIFIED          = true  (depth, V, F exact)
HISTORICAL_CLEANING_REUSED       = true  (same protocol; one R1 run)
STANDARD_A_TO_B_REPRODUCED       = true  (bitwise prediction; five-panel generated)
SOURCE_MESH_IDENTITY_PASS        = true  (tuple target mesh, not first PASS mesh)
INDEPENDENT_VIEW_IDENTITY_PASS   = false (not executed)
SIX_VIEW_RENDERER_REUSED         = false (only standard five-panel)
ALL_GROUP_PIPELINE_ADAPTED       = false
REPRESENTATIVE_GALLERY_COMPLETE  = false
HUMAN_REVIEW_PENDING             = true
```

This is a controlled historical reproduction, not a new 39-group MVS claim.

## 1. R0/R1: historical HERO reproduction

Four historical targets with original input caches and cameras:

| Target | Group | R1 depth MAE | Median | P95 | Faces equal | V max |
|---|---|---:|---:|---:|---|---:|
| G01_004_ref03 | G01 | 0.0 | 0.0 | 0.0 | true | 0.0 |
| G03_key00_raw00100 | G03 | 0.0 | 0.0 | 0.0 | true | 0.0 |
| G05_key00_raw00097 | G05 | 0.0 | 0.0 | 0.0 | true | 0.0 |
| G06_004_ref04 | G06 | 0.0 | 0.0 | 0.0 | true | 0.0 |

All 225,280 native pixels are finite and equal. `HERO_native.npz`, `RAW_NATIVE_MESH.npz`, face ordering and vertex coordinates reproduce exactly. This establishes that the current `hero.py::infer()` and model weights are not the source of the observed historical shape change.

Inputs were loaded directly from the historical `SOURCE.json` `input_caches`/`camera_results`; hashes matched (`INPUT_IDENTITY_VALIDATION.csv`). No directory-order fallback was used.

## 2. Pixel geometry

`geometry.resize_index_intrinsics`, `native_rgb_labels`, `unproject`, `project` were used. Native output is 352×640; work RGB/Mask is 360×640.

Pixel roundtrip over all 225,280 native pixels:

| Target | median error | P95 | max | work-label agreement |
|---|---:|---:|---:|---:|
| G01 | 4.3e-14 | 1.2e-13 | 3.4e-13 | 0.9975 |
| G03 | 3.2e-14 | 1.1e-13 | 2.5e-13 | 0.9986 |
| G05 | 5.7e-14 | 1.2e-13 | 2.5e-13 | 0.9978 |
| G06 | 5.9e-14 | 1.3e-13 | 3.5e-13 | 0.9982 |

Point projection is effectively exact. Label agreement is 99.75–99.86%, not 100%; the residual is nearest-pixel/mask-boundary discretization, not evidence that the historical standard is exact for every boundary pixel. The earlier manual `359/351` resize was not used.

A-to-A evidence: `visualization/pixel_roundtrip/*_A_to_A.png`.

## 3. Standard A-to-B

Historical `reprojection.py::render/evaluate/make_figure` was used, not a hand-written 2-D projection.

Historical sample:

```text
G01_004_ref03 → 004_07
```

Replay result:

```text
prediction bitwise equal to historical npz: true
target Polyp pixels: 13,769
prediction valid pixels: 12,997
common pixels: 12,654
uncovered target: 1,115
predicted outside: 343
target_coverage: 0.9190
RGB MAE: 22.47 / 255
RGB median: 18.0
RGB P95: 57.33
RGB RMSE: 29.14
independent geometric distance: NOT_EVALUABLE (no independent target depth)
```

The historical standard five-panel was generated with the original `make_figure()`:

`visualization/standard_a_to_b/G01_004_ref03__to__004_07.png`

## 4. Cleaning

`cleaning.py::classify_native` was executed on R1 G01 with the frozen cleaning protocol SHA `99c00fe5...`. It retained Raw and wrote Trusted/Conservative/Uncertain/Rejected/Unknown meshes without vertex change. Counts:

```text
TRUSTED=41,597; UNCERTAIN=1,152; REJECTED=0; UNKNOWN=3,175
```

The historical `CLEANING.json` sample at `/home/liu/ring-first-hero-core/outputs/hero` is **not the same target** (different native/labels hash), so its counts (38,815/879/0/4,052) are not used as an identity comparison. The cleaning code/protocol is reused; exact historical count comparison for the same target is not available in the retained task directories.

## 5. What is not established

- R2 camera-only: not executed; no exact current-W0 frame mapping for the historical identifiers.
- R3 support-only: not executed.
- R4 current 39-group chain: not executed in this branch.
- Independent-view/B→A historical identity: not executed.
- Six-view renderer and full Raw/Cleaned gallery: not generated.

The automatic 112 MVS outputs from M2D must not be treated as historical reproductions; they remain a separate result.

## 6. Answers

1. **Can current implementation reproduce historical MVS?** For the controlled R1 set, yes: depth, V, F and standard A→B prediction are bitwise equal. This is not proof for all groups.
2. **Where did shape degradation first appear?** Not in HERO R1. Because R2/R3 are not completed, the first divergence between historical and current cannot be assigned to camera, support or cleaning. It is not model nondeterminism.
3. **Do current cameras significantly affect HERO depth?** Not measured; R2 not executable with exact frame mapping.
4. **Does support selection reduce surface quality?** Not measured; R3 not executed.
5. **What caused mask offset?** The old M2D path used a manual 359/351 mapping and first-PASS mesh binding. The standard geometry path gives 99.75–99.86% label agreement and effectively exact point roundtrip; exact mesh identity now uses tuple ID. This corrects the demonstrated offset, but does not prove all masks perfect.
6. **Did corrected A-to-B restore historical definition?** Yes for the standard sample: historical `render/evaluate/make_figure`, target coverage definition and five panels; prediction bitwise equal.
7. **Worth starting body?** Not yet. We have a correct historical HERO/A→B anchor, but no R2/R3, no independent-view identity, no 39-group adaptation and no six-view gallery.

## 7. Source reuse

See `SOURCE_REUSE_MAP.csv`; direct reuse:

```text
hero.py::infer
geometry.py::resize_index_intrinsics/native_rgb_labels/unproject/project
cleaning.py::classify_native
reprojection.py::render/evaluate/make_figure
replays.py::a_to_b
real_p0_renderer.py (five panel / 5d)
```

No new simple projection or plotting implementation was used for the standard A→B.
