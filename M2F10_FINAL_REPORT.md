# M2F10 FINAL REPORT — V6 Multiview HERO Expansion

**Status:** `COMPLETE_WITH_SCIENTIFIC_LIMITATIONS`  
**Branch:** `exp/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001`  
**Code commit:** `a38d4c82`  
**Formal run:** `runs/m2f10_v6_multiview/M2F10-FORMAL-20261125-02/`  
**Native audit:** `runs/m2f10_v6_multiview/M2F10-AUDIT-FINAL-20261125-01/`  
**A→B audit:** `runs/m2f10_v6_multiview/M2F10-A2B-FINAL-20261125-01/`  
**Final visuals:** `runs/m2f10_v6_multiview/M2F10-FINAL-VISUAL-20261125-01/`

## Completion

- 10/10 videos executed under one M2F10 route.
- `--verify-resume`: 15 attempt run-states (`attempt0` 10 + `attempt1` 5) all `RUN_STATE_OK`.
- M2F10 tests: **16 passed**.
- Native audit: **160 targets**, **86 native HERO depths**.
- Accepted independent packaged surfaces: **66**, all from five videos.
- A→B: **198/198 PASS** pairs; 10 videos, 5 groups.
- Final six-view renders: **5** videos with accepted surfaces.
- Five videos correctly have zero accepted surfaces; no threshold was lowered.

## Per-group result

| Group | Accepted surfaces | A→B pairs | A→B pass | Coverage median | RGB MAE median | Packaged Ring ratio median | Packaged Ring MAE median |
|---|---:|---:|---:|---:|---:|---:|---:|
| IIa14 | 17 | 51 | 51 | 0.928 | 22.19 | 1.0088 | 0.440 |
| Ip12 | 15 | 45 | 45 | 0.912 | 14.64 | 1.0090 | 0.959 |
| Ip20 | 0 | 0 | 0 | — | — | — | — |
| Ip8.8 | 25 | 75 | 75 | 0.856 | 34.79 | 1.0077 | 0.728 |
| Is14 | 9 | 27 | 27 | 0.942 | 23.67 | 1.0294 | 1.016 |

Accepted surfaces by video:

```text
IIa14/004 17    IIa14/005 0
Ip12/004  0     Ip12/005 15
Ip20/004  0     Ip20/005 0
Ip8.8/004 12    Ip8.8/005 13
Is14/004  9     Is14/005 0
```

## Accepted vs diagnostic

- All **160** target records are retained in the native audit, including `MODEL_PREDICTED` and `NOT_EVALUABLE`.
- The **66** accepted surfaces are the independently packaged targets with the frozen V6 Support evidence.
- Rejected/native-only HERO depths remain in `visualization/diagnostic_native`; no rejected depth was promoted to a mesh.
- `M2F10-FORMAL-20261125-01` remains an aborted diagnostic and is excluded from final statistics.

## Recovery

A bounded real-frame recovery was attempted only where needed, using the existing M2F10 supplement mechanism. It did not relax V6 validation. `IIa14/004` reached 17 accepted surfaces after recovery; several other videos still have zero accepted surfaces. `Is14/005` remains at zero accepted surfaces after its recovery attempt.

## Scientific limitations

- The increased number of surfaces is not evidence of better multiview consistency; the six-view outputs still show layered surfaces.
- A→B pass fraction is high, but RGB MAE/coverage are target-camera dependent and do not establish absolute GT accuracy.
- The A→B audit uses the same accepted target/support set; it is not a new camera selection or a GT-shaped mesh.
- No cross-video registration, depth correction, ICP, scaling or point deletion was used.

## Artifacts

- `experiments/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001/evidence/final/GROUP_METRICS.csv`
- `VIDEO_METRICS.csv`, `TARGET_METRICS.csv`
- `A_TO_B_GROUPS.csv`, `A_TO_B_VIDEOS.csv`, `A_TO_B_PAIRS.csv`
- `VERIFY_RESUME.log`
- `TECHNICAL_REPORT.md`
