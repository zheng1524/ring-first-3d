# JOINT_BA_RESULT

| | B0-v0 | J2-v0 |
|---|---:|---:|
| inner MAE | 1.018 | 1.208 |
| outer MAE | 1.660 | 2.004 |
| raw (min over 2 CAD curves) | 0.977 | 1.631 |
| held median | 2.376 | 2.427 |
| held p95 | 4.387 | 4.325 |
| positive | 0.986 | 0.987 |
| valid views | 16 | 16 |
| camera Δ | — | 0.11 mm / 0.17° |

结论：**稳定、无漂移、但不优于基线。** 011 的 52.19 px 是执行偏差（v1 + CAD_INVALID 崩溃），不是方法本身的必然结果。
