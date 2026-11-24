# M2F1 FINAL REPORT — W0 admission and view-selection restoration

**Task:** TASK-M2F1-W0-ADMISSION-AND-VIEW-SELECTION-RESTORATION-001  
**Branch:** `exp/TASK-M2F1-W0-ADMISSION-AND-VIEW-SELECTION-RESTORATION-001`  
**Output:** `runs/m2f1_w0_admission_restoration/`

## 0. Status

```text
W0_INPUT_IDENTITY_VERIFIED              = false
W0_TRACK_IDENTITY_VERIFIED              = false
W0_BRANCH_REPAIR_ACTUALLY_ATTEMPTED     = false
S0_ACTUALLY_ENFORCED                    = true
S1_ACTUALLY_ENFORCED                    = true
S2_ACTUALLY_ENFORCED                    = true
T10_ACTUAL_TARGETS_USED                 = true
T11_ACTUAL_TARGETS_USED                 = true
T13_ACTUAL_SUPPORTS_USED                = true
HERO_PRE_INFERENCE_GATE_VERIFIED        = true
NEW_HERO_INFERENCE_EXECUTED             = true
THREE_REPRESENTATIVE_GROUPS_EXECUTED    = true
ALL_39_GROUPS_ATTEMPTED                 = false
STANDARD_A_TO_B_VERIFIED                = true
MULTISURFACE_VIDEO_IDENTITY_VERIFIED    = true
HUMAN_REVIEW_PENDING                    = true
```

This is not a completed 39-group run: **294 new gated HERO tuples cover 33/39 groups and 44/79 videos**; six groups have no gate-ready tuple. W0 track identity remains unresolved for two videos.

## 1. Actual new control flow

The new entry `tools/m2f1_pipeline.py` does:

```text
FRAME / W0 views
→ arm-specific admitted pool
→ T10 (S0/S1) or T11 (S2)
→ T13 support selection from that same pool
→ target/support/relative/3-support gate
→ new HERO
→ historical cleaning
→ corrected B-camera A→B
```

No M2E/M2F HERO result was reused. All 294 outputs are new.

| Arm | Target records | Ready tuples | New HERO |
|---|---:|---:|---:|
| S0 | 10 | 4 | 16 |
| S1 | 30 | 14 | 151 |
| S2 | 17 | 9 | 127 |
| total | 57 | 27 (3-group partial table) / 294 all | **294** |

The 3 representative groups produced 27 new HERO before the all-group extension.

## 2. W0 identity

- `FRAME_REGISTRY`: 761 actual views with source video path/hash, RGB hash, raw/clean Mask hash, K/c2w.
- Track audit over 79 videos: **2 mismatches**:
  - `GP_Is_9.79mm_closed_R10_single_refY/004`: W0 max track ID 161, track count 126.
  - `GP_Is_10.5mm_closed_R5_single_refY/005`: mismatch too.
- The first was recomputed; `run_w0_camera.py` stopped with `RING_POSE_GRAPH_DISCONNECTED`. It was **not** repaired by truncation/wrapping.
- Therefore Is9.79 new HERO is `input_identity_verified=false` and conditional.
- G01 and Is14 old W0 track identities are consistent.

## 3. Actual A→B

The new 294 HERO targets were evaluated against all three selected supports using historical `reprojection.render/evaluate` and the **target B K/pose**:

| Metric | New M2F1 |
|---|---:|
| A→B pairs | **882** |
| Targets | 205 unique target IDs |
| Coverage median | **0.9156** |
| Coverage mean | 0.857 |
| RGB MAE median | **14.94** |
| RGB MAE mean | 17.64 |
| Predicted outside median | 191 px |

Old M2F corrected 651-pair set remains separate. No paired quality claim is made between M2E/M2F/M2F1 because target/support sets differ.

## 4. G01 / Is9.79 / Is14 outcomes

New G01 S1 targets include serious outliers: CAD-HERO signed median **−15.89 mm** and **−13.76 mm**; other new G01 targets near 0 (+0.35, +2.19). Thus the severe G01 suspension is **not fixed** by merely enforcing admission/T13. G01 had no S0 target.

Is9.79 produced 6 new conditional surfaces; new CAD-HERO signed medians near 0 (group median ~0.02 mm), but W0 track identity remains unverified, so this cannot be called fully verified.

Is14 produced new surfaces and retains near-Ring behavior; detailed new CAD-HERO rows are in `evaluation/CAD_HERO_NEW.csv`.

## 5. Answers

1. **What W0 problems were fixed?** Source-video hashes and raw/clean mask identities were bound in FRAME_REGISTRY; track audit identified 2 actual mismatches. The Is9.79 recompute failed with a real pose-graph disconnection; it was not hidden or truncated. Branch repair was not executed.
2. **How did admission change pools?** It changed actual target/support pools: 16 S0, 151 S1, 127 S2 new HERO. The pre-inference gate rejected 503−294=209 candidate tuples.
3. **Which targets did T10/T11 choose?** T10 for S0/S1, T11 for S2; both produced actual new HERO. Counts are in `selection/T10_TARGET_SELECTION.csv`, `T11_TARGET_SELECTION.csv`, `FINAL_HERO_TUPLES.csv`.
4. **Did T13 select only from legal pools?** Yes for the new pipeline: every support came from the same arm pool; final tuples have 3 distinct supports, target not in supports, and no duplicate IDs.
5. **Does G01 severe suspension remain?** Yes. New gated G01 targets still include −15.89 and −13.76 mm CAD-HERO outliers. Admission/T13 alone did not fix it.
6. **Is Is9.79 valid reconstruction preserved?** Six new surfaces are near Ring, but its W0 track mismatch remains; the result is conditional and cannot be declared fully verified.
7. **Does the new line improve quality/coverage?** It expands new gated HERO to 33/39 groups and 882 pairs, with coverage median 0.916, but there is no controlled paired comparison to M2E/M2F; no superiority claim.
8. **Is there a reusable W0→MVS entry?** Yes: `tools/m2f1_pipeline.py` is parameterized by group/video and uses the same code; however, 6 groups have no gate-ready tuple and W0 track identity is not fully closed.

## 6. Visuals

- `visualization/representative_three_groups/` — four representative video sheets
- `visualization/multisurface_by_video/` — same-video overlays only; no cross-video mixing
- `visualization/figures/A_to_B/` — one new corrected five-panel
- `VISUALIZATION_INDEX.html`

No independent B, no A2 camera ablation, no support-combination ablation, and no numerical multisurface consistency were executed.

## 7. Files

`w0/`, `admission/`, `selection/`, `hero/`, `evaluation/`, `visualization/`, `evidence/`, `VALIDATION_39.json`, `VISUALIZATION_INDEX.html`.
