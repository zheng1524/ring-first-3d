# Method and input audit — Phase 0

## Result

The input denominator and original file bindings are now auditable, but the Body-E route is **not yet eligible for optimization**. The predecessor's `prepare.py` used `ellipse_descriptor(labels==1)` (DT 25% core plus AMS) and restricted Body FIT selection to `video=='004'`. Its `fit_body.py` also selected lowest cost without excluding failed optimizations. None of those outputs, parameters, or candidate choices are reused here.

## Audited source inventory

| group | sources | video004 | video005 | photo | frozen metric pose | no metric pose |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| G03 | 18 | 12 | 6 | 0 | 10 | 8 |
| G05 | 16 | 14 | 1 | 1 | 9 | 7 |
| G01 | 26 | 17 | 8 | 1 | 15 | 11 |
| G06 | 15 | 15 | 0 | 0 | 9 | 6 |
| **all** | **75** | **58** | **15** | **2** | **43** | **32** |

`VIEW_INVENTORY.csv` records per source: RGB/mask/cache SHA256, file path, class encoding, Ring ID, DXY inner diameter, K, frozen pose or its absence, source/observation/mesh SHA256, sharpness/glare, capture type, and coordinate-pool status. Disk file SHA verification passed for all 75 RGB/Mask/cache/source/observation/mesh bindings. No GT path was opened.

## Binding and input integrity

The full source list comes from the predecessor `config/SOURCES.json` (SHA256 captured in `provenance/PHASE0_INPUT_FILES.json`). The code binds a source to a raw camera candidate through the exact predecessor logic: matching `view_id` or an alias, preferring a matching metadata `target_SHA`.

| binding outcome | sources |
| --- | ---: |
| view ID + metadata RGB SHA256 | 46 |
| unique archived view ID; source metadata has no target SHA | 29 |
| ambiguous, missing, or substituted image | 0 |

All groups are locked to R10 by the original CASE files. The DXY inner diameter is thus 10 mm; `R_mid_mm=5.6` and `wire_mm=0.6` have been retained only for audit and are prohibited from scale conversion.

## Cross-video conclusion at Phase 0

The 021 study documents a G01-only 004/005 RGB correspondence and Ring-aware shared-SE3 analysis. Its own protocol explicitly limits cross-video work to G01. There is no corresponding proof for G03, G05, or G06, and no photo coordinate assignment. Consequently this experiment has not merged any video coordinate system. Phase 2 must issue `CROSS_VIDEO_FRAME_AUDIT.csv` before it can freeze joint FIT views; until then every video and photo pool is separate.

## Official DXY availability

`/home/liu/new-polyp-dxy` is present, clean, and at required commit `75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`; `src/dxy_mid/pipeline.py` declares `VERSION=DXY-MID-1.0.0rc1` and has SHA256 `2671739527cf8433b58dd480a6f40302c13fe0ab2ab3474d09ad318d6a45146a`. No DXY call has been made yet and no DXY output, historical prediction, or millimetre result has been read.

## Phase-0 failure / hold ledger

| condition | affected | disposition |
| --- | --- | --- |
| `FINAL_CAMERA_POOL.json` absent in this revision | all 75 bindings | Explicitly substituted the existing raw candidate pool; no claim of file identity. |
| no frozen metric pose | 32 sources | Not eligible for FIT unless Phase 2 finds independent, hash-traceable pose evidence; never guessed. |
| G03/G05/G06 cross-video alignment unproven | all their video005 sources | Separate coordinate pools; no joint fit. |
| independent photo alignment unproven | 2 photos | Separate and not FIT eligible at present. |

## Fixed audit table

| 审计项目 | Phase-0 status |
| --- | --- |
| 目标组数 | 4 groups; 75 source denominator |
| 本算法独立成功 | Not applicable: no prediction route has run |
| 本算法失败 | No numerical prediction attempted; 32 sources held for missing metric pose |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | Per-source pose state in `VIEW_INVENTORY.csv`; hold reasons above |
| 最终统计样本 | None in Phase 0; denominator remains 75 |
| 是否使用 GT 选择算法 | No; GT not read |
