# V6 Frontend Recovery and Photo Pilot Implementation Plan

> Execute the explicitly approved attachment task in this isolated worktree; use executing-plans and boundary tests. Full rerun requires the researcher's later pilot approval.

**Goal:** Repair actual V6 frontend semantics and scheduling, test the fixed six-group cohort, and prepare a single full-run entry.

**Architecture:** Reuse route.py and full_run.py. Process-local adapters modify the frozen external functions through checked AST transformations; external files remain read-only. Camera outputs freeze both candidates; schedule outputs separately freeze the selected candidate and its complete plan. R1/R2 differ only by eligible photo input configuration.

**Tech Stack:** Existing Python venv, NumPy/OpenCV/SciPy, existing V6/HERO/native cleaning and renderer.

## Approved composition (attachment is the authorization)

| Capability | Source/entry | Input → output | Treatment | Validation |
|---|---|---|---|---|
| Registry/preprocess | full_run inventory; route.prepare; existing PREPARED | RAW identity → same 16+up-to-6 RGB/Mask | REUSE, verify hashes/contract | cohort 12, R0 7 empty+5 output=105 |
| Ring observations | native.camera.observe(all); M2F10 build_ring → V5 ring_observations adapter | real labels → q/p/b | ADAPT boundary semantics in actual namespace | contact Ring retained; real image clipping; train/held disjoint |
| Tracks/graph | V6 track005.main/pair_data | original RGB/Mask → cached tracks and accepted edges | REUSE | unchanged match thresholds; original track IDs retained |
| Component | original reference receipt; graph accepted edges | complete view pool → anchor component | ADAPT before V6 solve | 21+1; B outside; duplicate physical views; ≥4 excluding B |
| Initialization/BA | V6 local_ring_sfm.initialize/triangulate_training/BA | component, original temporal edges → two candidate camera sets | ADAPT only temporal indices/short-track guard/empty-region weight | no across-gap or photo temporal edges; nonempty weight unchanged |
| Validation/plan | V6 validate_select/select_supported_views; route.schedule | candidate camera sets → exact Q0/Q1 tuples | ADAPT safe None and complete-plan fallback | keep original with legal tuple; 3 cameras not sufficient; version consistency |
| Photo | existing INIT + geometry remap; calibration record | independent photo → own K/mapping/Mask/view ID | ADAPT only when calibration evidence supports it | no inferred K from resize; no copied video pose; explicit not-evaluable otherwise |
| HERO/Mesh | route.hero; original run_mvs/package | frozen tuple → native depth/original mesh | REUSE | model/native/mesh definition hashes |
| Trusted | surface_clean.mapped_input_for_source; cleaning.classify_native; trusted_subset | original V/F/mapping → four-state and F[state==0] | REUSE | protocol 99c00f… unchanged; Raw and Trusted separately counted |
| Report | nearviews.make/visualize.draw | original meshes → common-axis metric figures | REUSE/ADAPT labels | R0/R1/R2 video target regression, photo targets separate |

Registry exists; docs/architecture.md absent at pin. Registry's historical candidate statuses are superseded only within this task's explicitly approved bounded pilot, not promoted to full mainline.

## Steps

- [x] Freeze baseline audit tables, six-group manifest, all79/120 manifests, photo metadata/calibration evidence, disk estimate and actual imported source hashes.
- [x] Add failing boundary tests in tests/test_v6_frontend_recovery.py: adjacency retention, safe empty metrics, region evidence, anchor component, train/held identity, temporal gaps, B exclusion, duplicate physical IDs, zero-plan-only fallback, candidate binding.
- [x] Add frontend_policy.py (pure identity/component/temporal decisions), frontend_kernels.py (checked process-local frozen kernel adapters), frontend.py (route integration and full-plan selection). Modify route.py/full_run.py only at explicit opt-in hooks and cache/signature boundaries.
- [x] Add photo admission/geometry metadata contract. Researcher confirmed same optics/zoom/crop/distortion; use video processing with explicit uncalibrated shared-K assumption.
- [x] Run tests with PYTHONPATH=src and the shared venv; record red/green evidence. Audit actual imports and replay 79 saved Mask point counts without HERO.
- [x] Freeze source commit and independent run root/config. Execute original full_run runner with reuse_old_results=false for the 12-video R1 cohort, shared GPU lock, source snapshots and per-tuple budget freeze.
- [x] Execute R2 only with eligible independently identified photos under the researcher-confirmed shared imaging assumption; all input starts from the original video pool before component selection. If calibration cannot be established, expose explicit R2 blocking evidence and do not masquerade R1 reuse as a photo trial.
- [x] Apply unchanged TRUSTED-only to actual new Raw, create nearviews and 3–4 single-source figures, compare all105 original successful targets; retain losses/failures.
- [x] Register candidate composition; commit/push report, hashes, tests, figures and commands. Prepare full79/120 config/space/launch/recovery plan without starting it. Obtain human confirmation of pilot before full rerun.

## Scope safeguards

No H004, no new optimizer, no GT tuning, no borrowed poses, no camera interpolation, no tolerance/BA-success gate changes, no best-looking HERO selection. All discarded original views remain in denominator and provenance. Only immutable baseline preprocessing may be reused, never R0 cameras under a new protocol. Source-level patches are local, hashed, and included in camera/schedule/hero signatures. Existing shared GPU queues/assets are protected.

Completed bounded pilot only. Full run has not started: R2 lost 21 original video Targets; R1 consistency trade-offs require researcher review. Full-run confirmation remains outstanding, as required by the attachment.
