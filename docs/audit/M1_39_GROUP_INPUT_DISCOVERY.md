# M1_39_GROUP_INPUT_DISCOVERY

**Status:** read-only discovery before Round 2. No pipeline execution is claimed here.
**Base commit:** `98873442e01eb2f7b1b4b1d44a16e3709e856d61`

This document records the real 39-group input identity and the exact gaps that Round 2 must close. It is not the final `runs/validation_39/INPUT_COVERAGE.csv`; that file is generated only by the actual Round 2 run.

---

## 1. Sources of truth

| Source | Role |
|---|---|
| `/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv` | 790-frame identity registry: `group`, `video`, `frame_index`, `stem`, `ring_mm`, `image_sha256`, `mask_sha256` |
| `/home/liu/new-polyp-dxy/validation/frozen39/GT_mapping.csv` | 39-group GT identity; evaluation only, not used for M1 algorithm selection |
| `smart_endoscope_20260805 (1)/raw` | 229 raw files: 109 mp4 + 120 jpg |
| `smart_endoscope_20260805 (1)/work/group_predictions.csv` | 39-group nominal inventory; 39 rows |
| `/home/liu/new-polyp-dxy/validation/frozen39/videos.example.csv` | 79-video index; video bodies are local, not in Git |
| `.../dxy_remeasurement_20260917/02_segmentation/model/model.safetensors` | frozen INIT weights, sha256 `981aa596...` verified |

`frozen39/inputs.csv` is the **only** registry covering all 39 groups. `ALL_VIEWS.json` covers only G01-G11 and therefore cannot be used as the 39-group frame source.

---

## 2. Verified counts

| Metric | Value |
|---|---:|
| Groups | **39** |
| Videos | **79** |
| Registered frames | **790** |
| Reference photos | **120** |
| Groups with 2 videos | 38 |
| Groups with 3 videos | 1 (30 frames) |
| R10 groups / frames | **22 / 440** |
| R5 groups / frames | **17 / 350** |
| Raw videos present | **79 / 79** |
| Raw videos 1280×720 | **79 / 79** |
| Frame index within video length | **79 / 79** |
| Photos per group | 3 for 36 groups; 4 for 3 groups |
| Current prepared groups | **5** (G01, G02, G03, G05, G06) |
| Current prepared video dirs | **10** |
| Missing prepared groups | **34** |
| Missing prepared video dirs | **69** |

### 2.1 Legacy alias mapping (only these 5 groups)

| Legacy ID | Raw group_key | Ring |
|---|---|---|
| G01 | `GP_Ip_12.0mm_closed_R10_single_refY` | R10 |
| G02 | `GP_Ip_4.0mm_closed_R10_single_refY` | R10 |
| G03 | `GP_Ip_20.0mm_closed_R10_single_refY` | R10 |
| G05 | `GP_Is_18.0mm_closed_R10_single_refY` | R10 |
| G06 | `GP_IIa_14.0mm_closed_R10_single_refY` | R10 |

The remaining 34 groups have no legacy Gxx ID. Round 2 uses the raw `group_key` as the canonical `group_id`; the five legacy IDs remain aliases for historical regression. No arbitrary G07..G39 mapping is invented.

---

## 3. Ring geometry is not uniform

- R10: inner diameter 10 mm; CAD centerline 5.6 mm; wire 0.6 mm.
- R5: inner diameter 5 mm; CAD centerline 3.1 mm; wire 0.6 mm.

Verified from `assets/.../FREE_VERTEX_013/inputs/G07/RING.npz`: radial min 2.500, radial max 3.700, z ∈ [-0.600, 0.600]. The analytic torus kernel already accepts `R` and `r`.

Current blockers (all interface-level):

1. `native/camera.py::torus_contours` hardcodes `R=5.6, r=.6`.
2. `native/camera.py::residual` and `recover` hardcode `rad=5.6, tube=.6`.
3. `unified_camera.build_namespace` binds `ring_residual` to the R10 `residual`.
4. `camera_mainline/code/contour_metrics.py::ring_raw_mae` calls the R10 `torus_contours`.
5. `tools/run_w0_camera.py` writes `ring_cad_mm=[5.6,0.6]`.

No R5 mesh CAD is needed for M1: the canonical formal geometry is the analytic torus with data-derived R/r. The mesh CAD route (`ring020_026`) is not part of M1.

---

## 4. Camera intrinsics

- All 79 raw videos are 1280×720.
- The prepared work size is 640×360.
- Frozen 005 config: `K = [[490,0,319.5],[0,490,179.5],[0,0,1]]`.
- `unified_camera.build_namespace` already asserts `K == K_CFG`.
- No per-group K table exists in `frozen39`.

Round 2 records `K` per group and asserts every prepared cache equals the frozen K. A deviation becomes `INVALID_INPUT`, not a silent resize/coercion. If future data contains a different calibrated K, that is a new input-contract GAP.

---

## 5. Reference photos

- 120 jpg files, all 39 groups covered (3 or 4 each).
- M1 does not use reference photos for camera recovery.
- `INPUT_COVERAGE.csv` records `reference_photo_ids` and `reference_photos_used=false`.
- No claim is made that photos participated in M1 computation.

---

## 6. Prepared-input generation route

The existing generators are not directly usable for 39 groups:

| File | Problem |
|---|---|
| `005/code/prepare.py` `__main__` | `INIT_MODEL` is undefined (only `INIT_WEIGHTS` exists); writes `video`/`init_model` instead of the `PREPARED.json` contract |
| `005/code/prepare_views.py` | hardcoded to the 5-group `VIDEO_FRAME_MAP.csv` and `ALL_VIEWS.json` (11 groups) |
| `PREBODY/code/video_preparation/*` | earlier blocked experiment, not a 39-group entry |

The reusable part is `prepare.py::segment` + `prepare.py::prepare_view`, which implement the frozen INIT math (PIL bilinear 256/255, bilinear logits, argmax) and were already used to generate the 10 existing prepared dirs.

Round 2 adds a thin `tools/prepare_m1_inputs.py` that:

1. reads `frozen39/inputs.csv`;
2. resolves each `video` in the local raw directory;
3. calls `prepare_view(video, frame_index, cache)` — no model/training/threshold change;
4. writes `PREPARED.json` with the existing 005 contract (`group`, `video`, `video_path`, `video_sha256`, `init_weights`, `init_weight_sha256`, `math`, `ring_mm`, `views`);
5. writes `INPUT_COVERAGE.csv`.

It does **not** copy the segmentation code and does **not** use `frozen39` image/mask paths (which are absent, 790/790).

---

## 7. What would invalidate the 39-group input claim

- Any missing raw video/frame index out of range.
- Any prepared cache whose K differs from `K_CFG`.
- Any group whose ring_mm is neither 10 nor 5, or whose R/r cannot be derived.
- Any group whose videos are silently borrowed from another group.
- Any prepared cache generated from a different frame registry than `frozen39/inputs.csv`.

These become `INVALID_INPUT` with the specific file/frame, not `INSUFFICIENT_EVIDENCE`.

---

## 8. Current conclusion

**Input availability is sufficient to attempt 39-group M1 execution:**

- raw videos: 79/79 present;
- frames: 790/790 indexed;
- INIT weights: present and hash-verified;
- ring types: 22 R10 + 17 R5, both derivable from `ring_mm`;
- reference photos: 120/120 present, metadata-only for M1.

The only missing engineering pieces are the 39-group prepare runner, per-ring R/r parameter threading, W0 export/manifest/status closure, and the 39-group validator. None requires a new scientific algorithm.
