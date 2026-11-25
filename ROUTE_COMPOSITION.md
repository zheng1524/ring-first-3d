# M2F7 — HIST-V6 / CURRENT-M2F6 Route Composition (STOP GATE)

**Status: EXECUTED diagnostic reproduction. HIST-V6 is a partial reproduction; CURRENT-M2F6 independently rerun; B/C NOT_COMPARABLE.**
**Branch:** `exp/TASK-M2F7-HIST-G01-CAUSAL-001`  
**Base:** `exp/TASK-M2F6-UNIFIED-OBSERVATION-GEOMETRY-001` @ `1a06461a91790ac1a115444434e176b6dabffb7c`  
**Serena:** project activated; source symbols and call paths inspected.

## 1. Composition table

| Stage | route_id@version | Historical V6 entrypoint | Current M2F6 entrypoint | Inputs → outputs | REUSE/ADAPT/GAP | Smoke test |
|---|---|---|---|---|---|---|
| G01-005 raw video | raw identity, no route | `ring_first_v6.../scripts/setup_audit.py` | `tools/m2f5_unified.py --m2f6` (`video_paths`) | 861-frame MP4 → frame identities | REUSE raw | SHA-256 `1d56e789...c86d` |
| Historical keyframes (22) | `v6-view-selection` (unregistered) | `setup_audit.py` + `metrics/view_selection.json` + `inputs/original16.json` | M2F6 `candidate_frames` / `select_observations` | original16 + 6 appearance/novelty frames → 22 fixed raw indices | ADAPT for identity; RGB/Mask must be **re-decoded raw** | 22 ledger indices; no V4 pixels |
| INIT + DXY 2D clean | `v6-init-dxy` (unregistered) | `prepare_ring.py` new-frame branch; DXY `INITSegmentation` + `ring_holes` | `prepare_one_m2f6` + DXY `ring_holes.run` | raw RGB → labels/clean masks | **GAP for V6 original16**: V6 copies V5 Ring observations; new6 branch is REUSE | compare re-decoded RGB/Mask SHA |
| Ring observations / candidates | `v5-ring-diverse` (unregistered) | `prepare_ring.py`; V5 `ring_observations.py`, `ring_candidates_diverse.py`, V4 `adapter.py` | `prepare_one_m2f6` DXY adapter + current Ring candidates | clean labels → Ring candidates | **GAP** for exact V6 original16; V5 intermediates are historical; new6 branch REUSE | source hashes frozen; no raw-only original16 path |
| `branch_seed_policy.diverse_four` | `v5-diverse-four` (frozen source, unregistered) | V5 `branch_seed_policy.py::diverse_four` | current frozen seed policy (same source family) | seeds → four branch seeds | REUSE | source hash `6ed402...2700`; 4-quadrant test |
| `track005` | `rf-frozen-tracks005@1` (frozen) | `v6/scripts/track005.py` | `tools/run_w0_camera.py` current track005 | 22 frames RGB/Mask → tracks005/pairs005 | ADAPT path re-decode; core REUSE | compare tracks under re-decoded input |
| `local_ring_sfm.initialize` | `rf-frozen-ba-local-ring-sfm@1` (frozen source, V6 parameters) | `v6/scripts/local_ring_sfm.py::initialize` | current W0 initialization (`run_w0_camera.py` / local_ring_sfm) | Ring candidates + pairs → initial c2w | REUSE | source hash `673b57...`; version 0/1 |
| `local_ring_sfm.BA` | `rf-frozen-ba-local-ring-sfm@1` (frozen source, V6 parameters) | `local_ring_sfm.py::BA` | current W0 BA | initial c2w + tracks → BA cameras | REUSE | `config.json` hash `d2f61b...`; 22 cameras |
| `validate_select` | `v6-validate-select` (unregistered) | `validate_select.py` | M2F6 admission/kept current route | BA cameras + held tracks → VALIDATED/MODEL_PREDICTED | REUSE source; **not registered** | recompute 15/22 as diagnostic, no hardcode |
| `select_supported_views` | `v6-supported-views` (unregistered) | `select_supported_views.py` | M2F6 T10/T13 | validated cameras + held tracks → supports | REUSE source; **not registered** | supports subset of VALIDATED; no MVS error |
| Official MVSAnywhere HERO | `surface_fusion_v1/run_mvs_adapter3` (frozen asset source, unregistered) | `run_mvs005.py` / `run_mvs005_supported.py` → `run_mvs_adapter3.py` | `native/hero.py::infer` | 4 real frames + cameras → native depth | REUSE V6 adapter for HIST; current native HERO for CURRENT; **diagnostic only** | checkpoint hash; native shape 352×640 |
| Raw metric mesh | `v6-depth-mesh` (unregistered) | `v6_common.depth_mesh` / `package_surfaces.py` | native metric mesh | depth+K+c2w → mm mesh | REUSE | no ICP/scale correction |
| Current M2F6 full route | `rf-m2f6-unified-observation@1` | — | `tools/m2f5_unified.py --m2f6`; `m2f5_hero_eval.py --m2f6` | raw → observations → W0 → T10/T13 → HERO | REUSE, **status `executed_scientific_incomplete`, `formal_usable:false`** | M2F6 G01-005 existing trace |
| CONTROL A | HIST-V6 cameras + HIST targets/supports | — | — | complete historical baseline | **GAP**: HIST raw-only route blocked | blocked |
| CONTROL B | M2F6 cameras + HIST targets/supports | — | — | same images, swap camera source | **NOT_COMPARABLE** | empty common selected frame set |
| CONTROL C | HIST cameras + M2F6 targets/supports | — | — | same cameras, swap view choice | **NOT_COMPARABLE** | empty common selected frame set |
| CONTROL D | M2F6 cameras + M2F6 targets/supports | — | — | current complete baseline | REUSE (independent only) | M2F6 G01 trace |

## 2. What is actually shared

- **Raw identity:** both start from the same G01-005 MP4, SHA `1d56e7890cf46364d0138007e559d5d77bb2919510b73a5b62e68ce964a9c86d`.
- **Frame identity:** V6 22 = original16 `[0,57,115,172,229,287,344,401,459,516,573,631,688,745,803,860]` + extra6 `[326,427,611,655,785,834]`.
- **M2F6 selected:** `[41,62,125,188,230,251,314,377,398,440,503,566,629,692,755,818]`.
- **Intersection:** **empty**. Consequently no common Target/Support tuple exists; B and C are `NOT_COMPARABLE`, regardless of camera quality.

## 3. Historical V6 source truth

All V6 `freeze_*.json` source and input hashes re-verified in place: `inputs` 28/28, `ring_protocol` 7/7, `tracking_protocol` 3/3, `local_solver_protocol` 5/5, `validation_protocol` 3/3, `supported_view_selection_protocol` 2/2, `MVS_protocol` 5/5, `local_cameras` 5/5, `ring_inputs` 47/47. No source was modified.

V6 keyframe selection is a **pre-fixed protocol**: `setup_audit.py` selects six extra frames by appearance novelty/clarity before camera or MVS, and `metrics/view_selection.json` records `uses_GT_or_reconstruction_error: false`. The original16 identity is inherited from V4; this is acceptable only as a historical frame-identity protocol. Pixels and masks still must be **re-decoded from raw** and hash-checked.

## 4. Hard GAPs

### GAP-1 (resolved by approval) — raw-only V6 original16 Ring preparation

`prepare_ring.py` (SHA `4225f0...f271`) does:

```python
new = not a['original16']
if new:
    ... INIT + DXY + Ring fit ...
else:
    shutil.copyfile(V5/'observations'/f'{id}.npz', ...)
    rec = prior[id]       # V5 ring_candidates_diverse.json
```

Thus the “exact V6” original16 branch consumes historical V5 Ring observations and candidates, not raw-only recomputation. This directly violates the M2F7 RAW-only constraint. There is no registered raw-only V6 entrypoint; the historical source is read-only.

### GAP-2 (registered diagnostic candidate) — V6 route

No V6 route exists in `docs/registry/routes.yaml`. The V6 source hashes are frozen, but status cannot be promoted to `confirmed/frozen` without human approval. Consequently HIST-V6 is not a legal formal composition yet.

### GAP-3 — No common Target/Support identity

V6 targets/supports are drawn from `{0,57,115,172,229,287,344,401,459,516,573,631,688,745,803,860}` and extra6; M2F6 selected 16 frames are entirely different. Therefore A/B/C cannot share four raw frame identities. Running B/C would require changing M2F6 sampling or fabricating overlaps, both forbidden.

## 5. Stop-gate decision requested

Before any code:

1. Approve or reject a **raw-only V6 original16 Ring recomputation adapter**:
   - prefer recomputing V5 Ring observations/candidates from raw with the existing V5 source (`ring_observations.py`, `ring_candidates_diverse.py`, V4 `adapter.py`) and re-decoding the original16 raw frames;
   - alternative: explicitly approve V6’s new-frame Ring branch on all 22 frames, which is **not exact V6**;
   - do not use V5 historical Ring observations/candidates.
2. Approve the thin **HIST-V6 run adapter** that imports the frozen V6 source in place (no source copying) and redirects its run root to a new run directory.
3. Confirm the diagnostic status of the unregistered V6 routes and the already `executed_scientific_incomplete` M2F6 route.
4. Confirm B/C are `NOT_COMPARABLE`; A/D may be compared only as independent baselines after V6 is raw-reproducible.

The approved raw V5 Ring preparation was executed: 22/22 RGB/Mask hashes match V6; V5 candidates and V6 tracks/initial cameras match; version-0 validation is 8/22, not historical 15/22. V6 is registered as candidate/diagnostic only; no formal promotion. B/C remain NOT_COMPARABLE.

## 5. Actual execution result (2026-11-25)

| Experiment | Cameras / validation | HERO | Outcome |
|---|---|---:|---|
| HIST-V6 | 22; version0 **8/22 VALIDATED**, version1 **0/22** | 4 | `PARTIAL_REPRODUCTION`; historical reference 15/22 not reproduced |
| CURRENT-M2F6 | independent fresh run; 16 prepared, 8 HERO | 8 | `INDEPENDENT_RERUN`; 21 A→B, coverage median 0.918 |
| CONTROL B | M2F6 cameras + V6 views | — | `NOT_COMPARABLE` (empty frame intersection) |
| CONTROL C | V6 cameras + M2F6 views | — | `NOT_COMPARABLE` (empty frame intersection) |

Reproduction checks: 22/22 raw RGB/Mask hashes match; V5 raw Ring candidates exact; V6 track005 finite values and NaN patterns exact; initial cameras exact within ~3e-8; BA/validation drift remains. No historical intermediate was used.

No historical module is promoted to the formal production route by this experiment. The registered HIST-V6 record is candidate/diagnostic only.

## 6. V6 HERO metric-depth audit (new raw predictions only)

| Target | Condition | Ring depth ratio median | Ratio MAE | Residual MAE | Historical area | Current area |
|---|---:|---:|---:|---:|---:|---:|
| 005_ref00000 | unfiltered | 0.9996 | 0.0301 | 0.909 mm | 132.559 | 132.484 |
| 005_ref00459 | unfiltered | 1.0074 | 0.0267 | 1.020 mm | 112.769 | 112.569 |
| 005_supported_ref00459 | supported | 1.0132 | 0.0280 | 1.064 mm | 112.638 | 115.724 |
| 005_supported_ref00688 | supported | 1.0139 | 0.0285 | 0.999 mm | NA | 130.394 |

All four raw V6 surfaces were retained. Surface pair nearest-neighbor medians are 0.145–0.684 mm (p95 0.485–1.794 mm); six-view images are in `runs/m2f7_hist_g01/visualization/v6_six_views/`.
