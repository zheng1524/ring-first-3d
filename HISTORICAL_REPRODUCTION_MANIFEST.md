# M2F7 Historical G01-005 Reproduction Manifest (executed diagnostic)

## Source identity

- Historical source root (read-only): `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/`
- Raw video: `/home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Ip_12.0mm_closed_R10_single_refY_005.mp4`
- Raw SHA-256: `1d56e7890cf46364d0138007e559d5d77bb2919510b73a5b62e68ce964a9c86d`
- Frame count: 861
- V6 config SHA-256: `d2f61b29b454a7f7e48b5d5f1254cd806ff9348335f220fb1e5f11ddedc61ddc`

## Frame ledger classification

| Item | Classification | Evidence |
|---|---|---|
| 22-frame list | `PLANNED_RECOMPUTED_FROM_RAW` for RGB/Mask; `HISTORICAL_REFERENCE_ONLY` for identity protocol | `setup_audit.py`; `metrics/view_selection.json`; `inputs/original16.json` |
| original16 identities | `HISTORICAL_REFERENCE_ONLY` | V4 ledger; frame indices 0,57,...,860 |
| extra6 identities | `PLANNED_RECOMPUTED_FROM_RAW` | raw novelty/clarity selection; 326,427,611,655,785,834 |
| V6 `inputs/*.png` and V4 PNGs | historical pixels; **not allowed as solving input** | must be re-decoded from raw and hash-checked |
| V6 `prepare_ring.py` original16 Ring observations/candidates | `UNVERIFIED_PROVENANCE` / **GAP** | copies V5 `observations/*.npz` and `ring_candidates_diverse.json` |
| V6 `predictions/*`, `metrics/local_validation.json`, HERO/Mesh | historical reference only | never load as run input |

## Frozen source lineage (verified in place; no changes)

| Module | Path | SHA-256 |
|---|---|---|
| V6 common | `scripts/v6_common.py` | `59404f5c2a35913c253f802f5bb4ff21461861958a881f86973de15710693fe1` |
| V6 prepare Ring | `scripts/prepare_ring.py` | `4225f0fe7ea713ac109b26a4151be0ef5b4b23b17a62732f36146c6fc1b0f271` |
| V6 track005 | `scripts/track005.py` | `c912da0713a329a3c954fc7b1dfbdcf43459493432ccbc782d7742cd26e514ac` |
| V6 local Ring SfM | `scripts/local_ring_sfm.py` | `673b57af12fcda5dad082eb7397574d46f0bdce2c097956c0682d8dac2cd8541` |
| V6 validate/select | `scripts/validate_select.py` | `bdfb607de4c3d967b2c84ce866a24f5fd5bd046744ce6dd62d4e545fd07b58db` |
| V6 supported views | `scripts/select_supported_views.py` | `f8439f53565baff7f1afcedc652109b47333fe80d364d1bab88e5a7515640128` |
| V6 HERO | `scripts/run_mvs005.py` | `6aabb25d6f6e39328206ff09aff74fea531746d5b38e2b3925698fb02e55992b` |
| V6 HERO supported | `scripts/run_mvs005_supported.py` | `353dc7f3ed2baf7383f45f141d51ad074e14fdc723efc4cc4b3a7b59d02ab46f` |
| V5 diverse-four | `ring_first_v5_geometry_crossvideo/scripts/branch_seed_policy.py` | `6ed402479a22804a4a41c23b68c99d0db6ed9bd91975597cb43d8a7471812700` |
| V5 Ring candidates | `ring_first_v5_geometry_crossvideo/scripts/ring_candidates_diverse.py` | `ddf49cb39144252b6b111f58f8f9449dc5d94023607d075d59e700cea5c8157f` |
| V4 adapter | `ring_first_v4_synthetic_audit/scripts/adapter.py` | `144dcbdc64520697b71621bd7fc476db5200b28eaf646333482be9aaf713af19` |
| V6 HERO adapter | `surface_fusion_v1/scripts/run_mvs_adapter3.py` | `14315d808e71a136dad71877c52336473fb2431428451e0a3b3de6f894e7d481` |

## Freeze verification

All V6 freeze manifests were re-hashed against the actual files in place:

```text
inputs                         28/28 OK
ring_protocol                   7/7 OK
tracking_protocol               3/3 OK
local_solver_protocol           5/5 OK
validation_protocol             3/3 OK
supported_view_selection_protocol 2/2 OK
MVS_protocol                    5/5 OK
local_cameras                   5/5 OK
ring_inputs                    47/47 OK
```

## Historical comparison only (not reproduced)

V6 records 15/22 VALIDATED and 7/22 MODEL_PREDICTED for version 0, and 0/22 for version 1; four HERO forward runs and two supported-view cases. These numbers are **reference values to compare against after a true raw reproduction**, not inputs or assertions.

## Current M2F6 identity

- Route: `rf-m2f6-unified-observation@1`
- Status: `executed_scientific_incomplete`, `formal_usable: false`
- Existing run: `runs/m2f6_unified/formal_002`
- Existing G01/005 selected raw frames: `[41,62,125,188,230,251,314,377,398,440,503,566,629,692,755,818]`
- Existing G01/005 ready targets: 7 (raw 230, 692, 503, 818, 566, 755, 398)

## Comparability statement

V6 22 raw frames and M2F6 selected 16 raw frames have **zero intersection**. Therefore A/B/C/D paired exchange cannot be performed with the original M2F6 view selection. B and C are `NOT_COMPARABLE`. Any future exchange would require a new approved experiment, not a silent re-sampling of M2F6.

## Executed raw reproduction (2026-11-25)

- Run root: `runs/m2f7_hist_g01/hist_v6/`
- 22/22 re-decoded RGB and Mask hashes match the historical V6 ledger; **no historical PNG/Mask was used**.
- V5 source recomputed Ring observations and candidates from the 22 raw frames into a run-local V5 runtime; V6 `prepare_ring` then consumed those raw-recomputed original16 files. No historical V5 observation/candidate file was loaded as a solver input.
- V6 `track005`, `local_ring_sfm` version 0/1, `validate_select`, `select_supported_views`, four official MVSAnywhere runs and `package_surfaces` completed.
- Actual result: **8/22 VALIDATED for version 0**, **0/22 for version 1** (historical reference: 15/22 and 0/22).
- Diagnostic comparison: the 22 RGB/Mask hashes and Ring candidate c2r values match the historical V6 records exactly; track005 finite values/NaN patterns match; version 0/1 initial cameras match within 3e-8/2.5e-8. The BA output and validation center spread still differ, so this is a **partial algorithmic reproduction**, not an exact 15/22 reproduction.
- Four official HERO cases completed: `005_ref00459`, `005_ref00000`, `005_supported_ref00459`, `005_supported_ref00688`. The supported cases differ from the historical supported set because the newly recomputed camera validation selected a different reference.
- M2F6 independently rerun at `runs/m2f7_hist_g01/current_m2f6/`: 8 HERO, 21 A→B; no V6 camera/view input.
- B/C: `NOT_COMPARABLE`; V6 22-frame and M2F6 selected 16-frame intersection is empty.
