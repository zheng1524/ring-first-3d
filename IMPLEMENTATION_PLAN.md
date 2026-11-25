# M2F7 HIST-V6 / CURRENT-M2F6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `executing-plans` only after the human approves the route composition and resolves GAP-1. This plan is **not authorized to execute** at the current stop gate.

**Goal:** Faithfully reproduce HIST-V6 for G01-005 from raw video, independently reproduce CURRENT-M2F6, and perform only identity-valid camera/view exchanges.

**Architecture:** HIST-V6 must call the frozen V6 source modules in place through a thin run-root adapter; CURRENT-M2F6 must call the existing M2F6 entrypoint without sharing any V6 intermediate. The two complete runs are compared first; A/B/C/D follow only if the same four raw-frame identities exist.

**Tech Stack:** Python, OpenCV SIFT, V6/V5 Ring-First BA, official MVSAnywhere, numpy/pandas, existing `tools/m2f5_*` and registry tooling.

---

## Preconditions (not satisfied yet)

- [ ] Human approves the route composition table and the diagnostic status of unregistered V6 routes.
- [ ] Human resolves GAP-1: raw-only original16 Ring recomputation, without V5 historical Ring observations/candidates.
- [ ] Human confirms that B/C are `NOT_COMPARABLE` unless a new shared-frame experiment is separately authorized.
- [ ] No historical PREPARED, tracks, cameras, Ring candidates, HERO or Mesh may be loaded as solver input.

## Task 0: Freeze the audit identities

**Files:**
- Create: `experiments/TASK-M2F7-HIST-G01-CAUSAL-001/RUN_MANIFEST.json`
- Create: `experiments/TASK-M2F7-HIST-G01-CAUSAL-001/SOURCE_RECEIPTS.json`

- [ ] **Step 1:** Record the raw video path and SHA `1d56e789...c86d`, the V6 config SHA `d2f61b...ddc`, the V6 source hashes in `HISTORICAL_REPRODUCTION_MANIFEST.md`, and the M2F6 commit `1a06461a...bf7c`.
- [ ] **Step 2:** Re-decode the 22 fixed raw indices. Assert RGB/Mask hashes for the new6 frames and compare the original16 with the ledger; do not copy V4/V5 PNGs.
- [ ] **Step 3:** Write `RUN_MANIFEST.json` with `run_id=HIST-V6-G01-005-<timestamp>`, `source=RECOMPUTED_FROM_RAW`, and `historical_reference_only=true`.
- [ ] **Step 4:** Verify with `python - <<'PY' ... PY` (hash file + all 22 RGB/Mask); expected all 22 identity checks PASS.

## Task 1: Resolve GAP-1 — raw-only original16 Ring preparation

**Files:**
- Create: `tools/m2f7_hist_v6.py` (thin run adapter; imports frozen source only)
- Read-only sources: V6 `prepare_ring.py`, V5 `ring_observations.py`, V5 `ring_candidates_diverse.py`, V4 `adapter.py`
- Test: `tests/test_m2f7_hist_v6.py`

- [ ] **Step 1:** If the human approves V5-source recomputation, call the existing V5 `ring_observations.py` and `ring_candidates_diverse.py` entrypoints on freshly re-decoded original16 RGB/Mask/K; do not copy their algorithms.
- [ ] **Step 2:** If the human approves the explicit non-exact alternative, call V6’s new-frame Ring branch for all 22; label that run `HIST_V6_NEW_BRANCH_ALL22`, not `exact V6`.
- [ ] **Step 3:** Reject any attempt to call `shutil.copyfile(V5/observations/id_ring.npz)` or load `ring_candidates_diverse.json` in the formal run.
- [ ] **Step 4:** Run the raw-only Ring smoke test; expected 22 Ring candidates with source receipts and no historical observation payload.
- [ ] **Step 5:** Do not proceed if the route still cannot be expressed as an approved existing source path; mark `HIST_NOT_REPRODUCIBLE` and stop.

## Task 2: Thin V6 run adapter

**Files:**
- Create: `tools/m2f7_hist_v6.py`
- Create: `experiments/TASK-M2F7-HIST-G01-CAUSAL-001/v6/RUN_TRACE/`

- [ ] **Step 1:** Import V6 modules from `/home/liu/polyp_research/.../ring_first_v6_local_reconstruction/scripts` without copying core source; redirect only `R`/run-root/output paths.
- [ ] **Step 2:** Execute in order: `prepare_ring` → `track005` → `local_ring_sfm` → `validate_select` → `run_mvs005` → `select_supported_views` → `run_mvs005_supported` → `package_surfaces`.
- [ ] **Step 3:** For every stage write actual `RUN_TRACE` records with source hash, input SHA-256, output SHA-256, status, and failure text; never reconstruct traces afterward.
- [ ] **Step 4:** Verify expected historical camera checkpoints (15/22 version 0 and 0/22 version 1) only as comparison values; do not assert them if inputs differ.

## Task 3: Independent CURRENT-M2F6 rerun

**Files:**
- Run entrypoint: `tools/m2f5_unified.py --m2f6 --groups GP_Ip_12.0mm_closed_R10_single_refY --videos 005 --output-root ...`
- Hero entrypoint: `tools/m2f5_hero_eval.py --m2f6`
- Output: new `CURRENT-M2F6-G01-005-<timestamp>/`

- [ ] **Step 1:** Run from raw G01-005 with a new run root; do not read `runs/m2f6_unified/formal_002` intermediates.
- [ ] **Step 2:** Preserve M2F6 sampling, W0, camera pool, Anchor, T10/T13 and HERO.
- [ ] **Step 3:** Record all actual stage inputs/outputs and compare source/config hashes to the M2F6 route registry.
- [ ] **Step 4:** Do not import V6 cameras, targets or supports.

## Task 4: Identity pairing and controls

**Files:**
- Create: `REPRODUCTION_COMPARISON.csv`
- Create: `CAMERA_GEOMETRY_COMPARISON.csv`
- Create: `HERO_CONTROLLED_ABLATION.csv`

- [ ] **Step 1:** Build the intersection of V6 22 raw frames and M2F6 selected raw frames. Current evidence: intersection is empty; B/C => `NOT_COMPARABLE`.
- [ ] **Step 2:** If and only if a target plus three supports share raw frame IDs, run A/D and then B/C; every four-camera tuple must come from one complete recovery.
- [ ] **Step 3:** For B, use HIST-V6 cameras and HIST target/supports with exactly the same RGB/Mask/K; for C, use M2F6 cameras and M2F6 target/supports.
- [ ] **Step 4:** Do not substitute nearby frames, interpolate cameras, or reuse historical HERO to fill missing pairs.
- [ ] **Step 5:** Write `NOT_COMPARABLE` with the empty-intersection evidence; do not fabricate A/B/C.

## Task 5: Geometry and HERO evidence

**Files:**
- Create: `CAMERA_GEOMETRY_COMPARISON.csv`
- Create: `HERO_CONTROLLED_ABLATION.csv`
- Create: `VISUALIZATION_INDEX.html`

- [ ] **Step 1:** For identical raw frames compare relative rotation, camera-center mm distance, positive-depth fraction, held reprojection, Ring CAD reprojection, Ring branch spread and metric baseline.
- [ ] **Step 2:** For HERO compare native axial depth, Ring CAD ray depth ratio/residual, B-camera A→B, multisurface consistency and original-world six views.
- [ ] **Step 3:** Keep successful and failed cameras; do not select cameras by HERO error.
- [ ] **Step 4:** Classify conclusions as `CONFIRMED_BY_CONTROL`, `SUPPORTED_BUT_NOT_ISOLATED`, `UNRESOLVED`, or `NOT_COMPARABLE`.

## Task 6: Final report and stop

**Files:**
- Create: `FINAL_REPORT.md`
- Create: `RUN_TRACE/` summary
- Update: `ROUTE_COMPOSITION.md`

- [ ] **Step 1:** Answer the six mandated questions with actual evidence, including whether HIST-V6 reproduced and whether B/C were legally possible.
- [ ] **Step 2:** Report commit SHA, run roots, config/source hashes, exact failures and visual paths.
- [ ] **Step 3:** If any new core algorithm or unregistered route is required, stop and request human decision.

## Current stop

No task above is executed. The composition is blocked by GAP-1 (V6 original16 raw-only Ring preparation) and by the empty V6/M2F6 Target/Support intersection. Awaiting human approval.
