# M2F8 — V6 Generalization & Metric Depth Attribution (Phase 1 / STOP)

**Status: STOPPED AT COMPOSE-ROUTE GATE. No new V6-GENERALIZED execution, no HERO, no B/C/D run.**
**Branch:** `exp/TASK-M2F8-V6-GENERALIZATION-001`  
**Base:** `exp/TASK-M2F7-HIST-G01-CAUSAL-001` @ `5c061e0b0d511f07215cf0c4b128fc3385be5906`  
**Serena:** project activated; source and call paths inspected.

## 1. Route composition table

| Stage | route_id@version | Historical V6 entrypoint | CURRENT-M2F6 entrypoint | Inputs → outputs | REUSE/ADAPT/GAP | Smoke test |
|---|---|---|---|---|---|---|
| Raw video + common sampling | M2F6 `rf-m2f6-2d-observation@1` (approved glue) | V6 fixed 22 ledger (M2F7 adapter) | `tools/m2f5_unified.py --m2f6::prepare_one_m2f6` | raw → candidate RGB/Mask/K | **ADAPT**: remove G01/22-frame/path constants; use one common input set | same raw frames; RGB/Mask hashes |
| INIT + DXY clean | M2F6 `rf-m2f6-2d-observation@1` | V6 `prepare_ring.py` new-frame branch | `m2f5_unified.py::prepare_one_m2f6` | raw RGB → labels/clean | REUSE DXY; ADAPT path | 22/22 hash check on G01; group-agnostic |
| Ring observations / candidates R10 | V5 `ring_observations.py`, `ring_candidates_diverse.py`; V6 `prepare_ring.py` | V6 `prepare_ring.py` | M2F6 current Ring/CAD | clean labels → candidates | **ADAPT** for arbitrary frames | candidate count/held stats |
| Ring candidates R5 | **none in V6** | V6/V5 hardcoded `R=5.6` | M2F6 `rf-native-ring-cad@2` (R5) | R5 labels → candidates | **GAP** | cannot compose without changing V6 Ring core |
| `branch_seed_policy.diverse_four` | V5 `branch_seed_policy.py` (frozen source) | V5 source | current frozen seed policy | seeds → 4 branches | REUSE | four-quadrant test |
| `track005` | `rf-frozen-tracks005@1` | V6 `track005.py` | `run_w0_camera.py` current tracks | current frames → tracks/pairs | REUSE core; ADAPT path | finite/NaN identity |
| `local_ring_sfm.initialize/BA` | `rf-frozen-ba-local-ring-sfm@1` | V6 `local_ring_sfm.py` | M2F6 W0 BA | Ring+tracks → c2w | REUSE core; ADAPT reference selection | version 0/1 receipts |
| `validate_select` | V6 `validate_select.py` (unregistered) | V6 source | M2F6 admission | BA+held → VALIDATED | REUSE; ADAPT fixed 459/516 | counts/status receipts |
| `select_supported_views` | V6 `select_supported_views.py` (unregistered) | V6 source | M2F6 T10/T13 | validated cameras → supports | REUSE; **ADAPT fixed 459/516** | supports subset of validated |
| V6 official HERO | `surface_fusion_v1/run_mvs_adapter3.py` | `run_mvs005.py`/`run_mvs005_supported.py` | `native/hero.py::infer` | four frames+cameras → mm depth | **ADAPT/UNVERIFIED**: adapter equivalence test required | identical four-frame output comparison |
| CURRENT-M2F6 | `rf-m2f6-unified-observation@1` | — | existing `--m2f6` | raw → current pipeline | REUSE READ-ONLY | existing M2F6 tests |
| `SHARED-RAW-DIAGNOSTIC` | proposed diagnostic only | — | — | same raw frames → A/B/C/D | **BLOCKED** until R5 decision and common inputs | identity receipts before HERO |

## 2. Fixed dependencies that must be removed for the generalized route

- `m2f7_hist_v6.py`: hardcoded G01-005 source path, run root and G01 geometry; must become an adapter driven by a run manifest.
- V6 `config.json`: `reference_raw=459`, `ring_R_mm=5.6`, `MVS_target=[352,640]`, `R=5.6` assumptions.
- V6 `select_supported_views.py`: `held=516`, `ref=459` hardcoded.
- V6 `validate_select.py`: `ref=459`, `heldout=516` hardcoded.
- V6 `local_ring_sfm.py`: reference lookup by raw 459.
- V6 `prepare_ring.py`: candidate depth `z=5.6*K/major_radius`; V5 `ring_candidates_diverse.py` `rad=5.6`; V6 `v6_common.py` `contour_project` fixed `R=5.6,r=.6`.
- V6 `run_mvs005.py` / `run_mvs005_supported.py`: fixed local paths/tags; only path/config adaptation allowed.

These fixed IDs are removable as **ADAPT** for R10. They are not the GAP.

## 3. Hard GAP: R5 is not implemented in the V6/V5 Ring core

The requested 5-group cohort includes:

```text
G01 R10, G03 R10, G06 R10, Ip8.8 R5, Is14 R5
```

`Ip8.8` and `Is14` raw videos are R5. V6/V5 Ring source has no R5 parameterization:

- `prepare_ring.py`: `z=5.6*K[0,0]/e['major_radius']`
- V5 `ring_candidates_diverse.py`: `rad=5.6, tube=.6`
- V6 `v6_common.py`: `contour_project(... R=5.6,r=.6)` and `torus_residual` fixed R10
- V6 `config.json`: `ring_R_mm: 5.6`; V6 does not consume a per-group R5 value in these functions.

M2F6 already has a correct R5 route (`rf-native-ring-cad@2`), but inserting it into V6 would replace V6's Ring candidate/BA core, not merely adapt the boundary. That is a **new core composition**, forbidden without approval.

**Requested decision:** approve a single authoritative **R5 V6 Ring adapter** built by parameterizing the existing V6 formula with the existing R5 physical CAD (3.1/0.6), or stop the R5 half of the study. Until then, V6-GENERALIZED cannot be registered or executed for all 5 groups/10 videos.

## 4. Other issues to resolve after R5 decision

1. **Reference/held selection**: remove fixed 459/516. The R10 generalization must choose a reference from current data using the V6 reference rule; this is an adapter, but must be fixed before any HERO inspection.
2. **HERO adapter equivalence**: `surface_fusion_v1/run_mvs_adapter3.py` vs `native/hero.py::infer` must be compared on the same four frames; source inspection shows possible K-edge/offset and depth-unit differences. Not yet executed; it is a required B1 gate.
3. **M2F6 status**: `rf-m2f6-unified-observation@1` is `executed_scientific_incomplete`, `formal_usable:false`; it is read-only for this study, not promoted.
4. **Historical V6 status**: `rf-m2f7-hist-v6@1` is candidate/diagnostic only; M2F7's 8/22 vs 15/22 mismatch remains known.

## 5. Planned five videos before any 10-video expansion

1. G01-005 (R10 historical reference)
2. G03-005 (R10 stable current reference)
3. G06-004 (R10 current failure case)
4. Is14-005 (R5 blocked by GAP)
5. Ip8.8-005 (R5 blocked by GAP)

No substitution of R5 frames with R10 CAD is allowed.

## 6. Stop condition

No `V6_GENERALIZATION_REPORT.md`, no 10-video comparison, and no shared-input HERO are produced in this phase. A human decision on the R5 V6 Ring adapter is required before implementation. No route is registered or promoted.
