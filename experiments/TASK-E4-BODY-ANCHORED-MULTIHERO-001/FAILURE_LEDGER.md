# Failure ledger — all groups retained

- G01 B1 round5: ['COMPLETE_FIXED_CORRESPONDENCE_OBJECTIVE', 'FIXED_DENOMINATOR_GEOMETRY_SCORE']; candidate hit delta 0, matched delta 3; full rollback. [metrics/G01_B1_ROUNDS.json](metrics/G01_B1_ROUNDS.json).
- G03 B1 round1: ['FIXED_NATIVE_MATCHED_COVERAGE_DROP']; candidate hit delta 0, matched delta -577; full rollback. [metrics/G03_B1_ROUNDS.json](metrics/G03_B1_ROUNDS.json).
- G03 B2 round2: ['FIXED_DENOMINATOR_GEOMETRY_SCORE']; candidate hit delta 286, matched delta 775; full rollback. [metrics/G03_B2_ROUNDS.json](metrics/G03_B2_ROUNDS.json).
- G03 B3 round3: ['FIXED_DENOMINATOR_GEOMETRY_SCORE']; candidate hit delta 208, matched delta 1518; full rollback. [metrics/G03_B3_ROUNDS.json](metrics/G03_B3_ROUNDS.json).
- G05 B2 round2: ['FIXED_NATIVE_HIT_COVERAGE_DROP']; candidate hit delta -15, matched delta 252; full rollback. [metrics/G05_B2_ROUNDS.json](metrics/G05_B2_ROUNDS.json).
- G05 B3 round3: ['FIXED_NATIVE_HIT_COVERAGE_DROP']; candidate hit delta -14, matched delta 8380; full rollback. [metrics/G05_B3_ROUNDS.json](metrics/G05_B3_ROUNDS.json).
- G06 B1 round4: ['FIXED_NATIVE_MATCHED_COVERAGE_DROP']; candidate hit delta 0, matched delta -5; full rollback. [metrics/G06_B1_ROUNDS.json](metrics/G06_B1_ROUNDS.json).
- G06 B3 round4: ['FIXED_NATIVE_MATCHED_COVERAGE_DROP']; candidate hit delta 0, matched delta -5; full rollback. [metrics/G06_B3_ROUNDS.json](metrics/G06_B3_ROUNDS.json).

## Per-case unsolved issues

- G01: committed Body updates 10; nonzero corrected sources 16; Ring64 minimum 0.0000038 mm; raw native MAE delta -0.020830 mm. Reason logs {}. See fixed three-direction atlas and all source states.
- G03: committed Body updates 4; nonzero corrected sources 6; Ring64 minimum -0.0061616 mm; raw native MAE delta -0.008796 mm. Reason logs {'FIXED_DENOMINATOR_GEOMETRY_SCORE': 1}. See fixed three-direction atlas and all source states.
- G05: committed Body updates 4; nonzero corrected sources 14; Ring64 minimum -0.0083696 mm; raw native MAE delta 0.000182 mm. Reason logs {'FIXED_NATIVE_HIT_COVERAGE_DROP': 1}. See fixed three-direction atlas and all source states.
- G06: committed Body updates 0; nonzero corrected sources 11; Ring64 minimum -0.0010851 mm; raw native MAE delta 0.000000 mm. Reason logs {'FIXED_NATIVE_MATCHED_COVERAGE_DROP': 1}. See fixed three-direction atlas and all source states.

G03 petals/unique branches remain ambiguous where no reliable same-layer overlap exists. Ray-only b/a/c cannot provide arbitrary 6DoF correction; no-overlap sources remain native. Weak anchors help only admitted same-camera foreground-connected geometry; other misses retain no strong gradient. No new topology was attempted.

Inherited Ring penetration, weak actual background bases, correlated sources and unknown backside/caps prevent unconditional physical/measurement claims. No GT accuracy metrics fabricated. A successful source correction can fit an incorrect Body; raw/HOLDOUT measures must remain separate.

Engineering archives: runtime/ENGINEERING_PILOT_BEFORE_UNIT_FIX, ANCHOR_SNAPSHOT_FIX_R1, STRONG_SUPERVISION_GATE_FIX_R2. These are excluded formal results; none deleted. Final R3 first-layer gradients obey MATCHED-only eligibility. Video-label parser correction did not alter a prediction. Initial detail-figure selector expected HOLDOUT instead of UPDATE_HOLDOUT; original plotting exception retained. No hyperparameter search or holdout-based winner selection.
