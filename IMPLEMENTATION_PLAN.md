# M2F8 V6 Generalization & Metric Depth Attribution Plan

> **For agentic workers:** Do not execute until the R5 GAP in `ROUTE_COMPOSITION.md` is resolved. The current phase has no run code.

**Goal:** Generalize one V6 Ring-First route across five groups (ten videos) and isolate the source of V6's metric-depth consistency with same-input controls.

**Architecture:** HIST-V6 remains read-only. V6-GENERALIZED is a thin adapter around the authoritative V6/V5 source modules, taking the M2F6 2D input set. CURRENT-M2F6 remains read-only. A separate SHARED-RAW-DIAGNOSTIC uses one fixed frame set and four independent camera/view combinations.

**Tech stack:** Python, V6/V5 Ring candidates and BA, OpenCV SIFT, official MVSAnywhere, existing M2F6/M1 evaluation, R10/R5 CAD.

---

## Preconditions (blocked)

- [ ] Human resolves R5 V6 Ring adapter: parameterize existing V6 formula with R5 3.1/0.6, or stop R5.
- [ ] Authorize one common RAW frame set for B/C; do not reuse historical intermediates.
- [ ] Confirm `run_id`, trace, and resume contract from M2F7 for every new run.

## Task 0: General input manifest

**Files:**
- Create: `experiments/TASK-M2F8-V6-GENERALIZATION-001/inputs/COMMON_INPUT.json`
- Test: `tests/test_m2f8_inputs.py`

- [ ] **Step 1:** Select the M2F6 2D input set from raw G01-005 and record raw frame IDs, RGB/Mask/K hashes, and candidate edges.
- [ ] **Step 2:** Re-decode every selected frame; assert no historical V4/V5 PNG path is a source.
- [ ] **Step 3:** Freeze the common frame set **before any camera/HERO output is read**.
- [ ] **Step 4:** Run `pytest tests/test_m2f8_inputs.py -q`; expected all identities PASS.

## Task 1: Generalized R10 V6 adapter

**Files:**
- Create: `tools/m2f8_v6_general.py`
- Reuse read-only: V6 `prepare_ring.py`, `track005.py`, `local_ring_sfm.py`, `validate_select.py`, `select_supported_views.py`; V5 `ring_observations.py`, `ring_candidates_diverse.py`, `branch_seed_policy.py`
- Test: `tests/test_m2f8_v6_general.py`

- [ ] **Step 1:** Build a run manifest with group/video/raw SHA/run_id; reject fixed G01/459/516.
- [ ] **Step 2:** Call V5 raw Ring observations/candidates for the common R10 frames; call V6 prepare/track/BA/validate/support without copying core code.
- [ ] **Step 3:** Choose reference/held from current R10 data using the same V6 angular/spread rule; freeze before HERO.
- [ ] **Step 4:** Run G01-005, G03-005 and G06-004 only; expected three separate run roots and actual validation/status tables.
- [ ] **Step 5:** Do not add an R5 path in this task; stop if R5 is required.

## Task 2: R5 decision

**Files:**
- Create: `docs/M2F8_R5_DECISION.md`

- [ ] **Step 1:** If approved, parameterize V6 Ring formulas with the existing R5 physical CAD (3.1/0.6) in one shared adapter; no second formula.
- [ ] **Step 2:** If not approved, mark R5 `GAP` and do not run Is14/Ip8.8; report the four-video incomplete cohort.
- [ ] **Step 3:** Verify R5 candidates against `rf-native-ring-cad@2` only as a geometry check, never as V6 camera output.

## Task 3: Shared RAW diagnostic for G01-005

**Files:**
- Create: `SHARED_INPUT_MANIFEST.md`
- Create: `HERO_ADAPTER_EQUIVALENCE.csv`
- Create: `CAMERA_SUPPORT_ABLATION.csv`
- Test: `tests/test_m2f8_adapter_equivalence.py`

- [ ] **Step 1:** Freeze one legal Target+3 Supports tuple with identical RGB/Mask/K.
- [ ] **Step 2:** Run the V6 adapter and native HERO adapter on exactly the same arrays; compare native depth elementwise and record units/K-edge/offsets.
- [ ] **Step 3:** Recover V6 and M2F6 cameras independently from the common images; never copy cameras between routes.
- [ ] **Step 4:** Fill A/B/C/D only where all four cameras and the same supports are legal; otherwise `NOT_COMPARABLE`.
- [ ] **Step 5:** Do not select a Target/Support based on HERO error; freeze before reading outputs.

## Task 4: Ten-video evaluation

**Files:**
- Create: `V6_GENERALIZATION_REPORT.md`
- Create: `V6_10_VIDEO_COMPARISON.csv`
- Create: `V6_VISUALIZATION_INDEX.html`
- Create: `METRIC_DEPTH_ATTRIBUTION.md`

- [ ] **Step 1:** Run the same V6-GENERALIZED adapter on all 10 videos if both R5 and R10 are approved.
- [ ] **Step 2:** Keep failed cameras and failed supports; no threshold lowering, no historical HERO/Mesh.
- [ ] **Step 3:** Compute Ring depth ratio/MAE, surface distances, A→B, and six views using the same R5/R10 CAD definitions.
- [ ] **Step 4:** Report coverage denominators and NOT_COMPARABLE reasons.
- [ ] **Step 5:** Stop before any new core algorithm; record GAP if one appears.

## Current status

Phase 2 (V6-GENERALIZED 10 videos) was executed after R5 approval. Five videos have validated cameras, 13 surfaces were produced, seven videos correctly failed support. Direction B is deferred because the common RAW input was not frozen. See V6_GENERALIZATION_REPORT.md.
