# M2F1 STRICT FINAL REPORT

**Task:** TASK-M2F1-STRICT-PIPELINE-RESTORATION-002  
**Branch:** `exp/TASK-M2F1-STRICT-PIPELINE-RESTORATION-002`  
**Output:** `runs/m2f1_strict_restoration/`

## 0. Final engineering status

```text
ACTUAL_SUBAGENTS_LAUNCHED           = true
AUDITOR_A_PASS                      = false
AUDITOR_B_PASS                      = false
AUDITOR_C_PASS                      = false
AUDITOR_D_PASS                      = false
FINAL_ACCEPTANCE                    = false
W0_BRANCH_REPAIR_ACTUALLY_EXECUTED  = false
W0_INPUT_IDENTITY_VERIFIED          = false
W0_TRACK_IDENTITY_VERIFIED          = false
HISTORICAL_T10_RESTORED             = false
HISTORICAL_T11_RESTORED             = false
S0_POLICY_ENFORCED                  = false
S1_TRAJECTORY_POLICY_ENFORCED       = false
S2_LOCAL_GEOMETRY_POLICY_ENFORCED   = false
HERO_TUPLE_GEOMETRY_VERIFIED        = false
ALL_39_GROUPS_ATTEMPTED             = false
```

This task is **not accepted**. Four real subagents ran and all returned FAIL. The strict three-group run produced real new HERO, but the P0 admission/T10/T11/geometry/W0 conditions are not met, so the 39-group stage was not started.

## 1. What was actually executed

- Three representative groups; 4 videos.
- Strict T10 route: **50 new HERO**.
- Separate T11 route: **10 new HERO** (17 targets, 10 ready).
- Total: **60 new HERO**; 180 corrected B-camera A→B pairs; coverage median **0.947**, RGB MAE median **13.20**.
- No old HERO surface was reused.
- `rank > 4` truncation was removed in the strict run.
- S2 was restricted after audit to `s0 or s1` non-branch; the audited 75-row version included rejected cameras and is not the final strict result.

## 2. Independent audit results

### Auditor A — W0

FAIL. The prior “Track mismatch” narrative was partly wrong: the W0 points match the frozen BRIDGE tracks; the validation used the wrong `work_A1` path. The actual defects are missing bridge registry rows, directory-order prepared lookup, no pre-HERO freeze, and no valid A2 branch repair. The only A2 pilot used R=5.0 instead of frozen 5.6.

### Auditor B — admission/selection

FAIL. Historical T10/T11 direction centre/anchor/partition semantics were not restored; the S2 tier was not the policy tier in the audited version; frozen thresholds were not enforced; the final gate was membership/count only; T10/T11 tables were not honestly split.

### Auditor C — HERO input/geometry

FAIL. 60 HERO rows are not 60 unique ordered tuples; receipts lack per-tuple RGB/Mask/K/c2w hashes; false-identity/bridge/branch inputs entered; A2B used raw B mask for some clean-mask inputs; G01 has no explicit alias mapping. Camera K, mesh binding, B-camera A2B and units passed.

### Auditor D — regression/scope

FAIL. No frozen 002 commit at audit time; S2 admitted rejected cameras; T11 label inversion; tests were count/status only; 75 rows were presented as admitted while only 42 were admission-clean and identity-verified. HERO/geometry/cleaning core untouched; historical 4/4 preserved.

## 3. Scientific observations (not acceptance)

- G01 still shows severe CAD-HERO outliers (minimum about −15.9 mm) under the strict run; no G01-specific fix was made.
- Is9.79 and Is14 new surfaces exist, but Is9.79 W0 identity remains contaminated by the wrong track path and no valid A2 repair.
- Standard A→B with B camera is actual and reproducible; this does not prove MVS geometry correctness.

## 4. Required corrections before re-review

1. Build 766/766 registry with the correct BRIDGE tracks and camera/track hashes.
2. Freeze W0 before HERO and enforce identity/false-branch checks in the pre-inference tuple gate.
3. Restore historical T10/T11 model-centre directions, anchors and direction partitions; split genuine T10/T11 tables.
4. Enforce frozen S0/S1/S2 policy; define S2 local tier before seeing results; no REJECTED/branch inputs.
5. Add real target/support geometry checks and per-tuple receipts.
6. Fix A2B clean/raw mask identity and deduplicate unique tuples/pairs.
7. Add genuine behavioral tests and re-run all four auditors on a committed frozen tree.
8. Only then run all 39 groups.

## 5. Artifacts

`w0/`, `admission/`, `selection/`, `hero/`, `evaluation/`, `visualization/`, `evidence/`, `independent_audit/`, `VALIDATION_39.json`, `VISUALIZATION_INDEX.html`.
