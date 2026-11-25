# M2F9 FINAL REPORT — V6 Generalized Pipeline Correction

**Branch:** `exp/TASK-M2F9-V6-GENERALIZED-PIPELINE-CORRECTION-001`  
**Code commit:** `91b97905`  
**Final run:** `runs/m2f9_v6_general/M2F9-FINAL-20261125-02/`  
**Final audit:** `runs/m2f9_v6_general/M2F9-AUDIT-FINAL-20261125-02/`  
**Worktree:** `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F9`

## Completion status

The previously unfinished 10-video experiment was completed with the existing corrected M2F9 runner. No runner/solver/code was modified in this completion pass.

- 10/10 videos executed from RAW-derived M2F6 input.
- `--verify-resume`: **10/10 `RUN_STATE_OK`**.
- M2F9 behavioral tests: **17 passed**.
- Final native depth targets: **34**.
- Native HERO outputs: **26**.
- Packaged meshes: **8**.
- Targets from VALIDATED cameras: **2**.
- NOT_EVALUABLE: **7**.

The previously interrupted `is14_005` reached `hero_raw`; it has 2 RAW_HERO outputs but no legal support, hence no supported HERO/mesh. This is a valid strict-validation outcome, not a missing execution stage.

## What was corrected in M2F9

1. RAW M2F6 preparation is isolated from historical V5 imports.
2. Clean-mask identity is checked against the selected candidate manifest; stale clean masks are rejected.
3. Reference/heldout are selected from current data and the V6 source lookups are AST-adapted without changing actual frame identities.
4. Each video has a unique run_id and `RUN_STATE.json` with stage input/output SHA-256.
5. Native HERO adapter equivalence was tested on the identical G01-005 four-view tuple: **225,280 pixels**, depth max difference **0.0 mm**, exact fraction **1.0**.
6. Native V6 depth is audited without filtering `MODEL_PREDICTED` cameras; raw and packaged denominators are reported separately.

## Final per-video results

| Video | Targets | Native HERO | Packaged | Validated target | Unfiltered ratio median | Unfiltered MAE mm |
|---|---:|---:|---:|---:|---:|---:|
| IIa14/004 | 4 | 2 | 0 | 0 | 1.0116 | 0.715 |
| IIa14/005 | 2 | 2 | 0 | 0 | 1.0172 | 0.579 |
| Ip12/004 | 4 | 2 | 0 | 0 | 1.0070 | 1.435 |
| Ip12/005 | 4 | 4 | 4 | 1 | 1.0088 | 1.024 |
| Ip20/004 | 2 | 2 | 0 | 0 | 1.0793 | 10.042 |
| Ip20/005 | 4 | 2 | 0 | 0 | 1.0078 | 1.184 |
| Ip8.8/004 | 4 | 3 | 0 | 0 | 1.0041 | 0.747 |
| Ip8.8/005 | 4 | 4 | 4 | 1 | 1.0050 | 0.789 |
| Is14/004 | 4 | 3 | 0 | 0 | 1.0253 | 0.800 |
| Is14/005 | 2 | 2 | 0 | 0 | 0.9306 | 4.027 |

## Interpretation

- The M2F9 correction produces **26 native HERO outputs across all 10 videos**, but strict V6 validation only admits **2 targets** as VALIDATED.
- Only **Ip12/005** and **Ip8.8/005** reached packaged meshes.
- Ring depth ratios are near 1 for most unfiltered targets; `Ip20/004` and `Is14/005` remain outlier cases. These are not averaged away.
- The adapter layer is equivalent on the tested G01 tuple, so the remaining discrepancy is not an adapter input-normalization difference for that tuple.
- No A/B/C/D Support/camera causal experiment is claimed here; M2F9 provided the pipeline correction, run contracts, native audit and adapter equivalence, not a new causal conclusion.

## Artifacts

- `evidence/final_audit/VIDEO_METRICS.csv`
- `evidence/final_audit/GROUP_METRICS.csv`
- `evidence/final_audit/TARGET_METRICS.csv`
- `evidence/final_audit/verify_resume.log`
- `evidence/adapter_g01/ADAPTER_EQUIVALENCE.json`
- M2F9 test result: **17 passed**
