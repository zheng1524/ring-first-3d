# REAL_GROUP_COMPARISON

| 组 | 身份(fit/hold) | 旧 FIT | 旧 HOLDOUT | 新 FIT | 新 HOLDOUT | Ring 旧/新 | BA success |
|---|---|---:|---:|---:|---:|---|---|
| G01 | 0 | — | — | — | — | — | — |
| G03 | 10 (7/3) | 1.10 | 5.58 | 1.34 | 9.17 | 0.474/0.386 | false |
| G06 | 6 (4/2) | 1.24 | 197.39 | 1.39 | 194.55 | 0.231/0.170 | false |

- G03：旧路线 HOLDOUT 更好（5.58 vs 9.17），新路线 Ring 更好 → **MIXED_RESULTS**；
- G06：两条路线 HOLDOUT 均失效（~195 px，2 个身份）→ 该组**不能**用于方法比较；
- G01：0 身份 → `INSUFFICIENT_EVIDENCE`；
- 结论：`OLD_NEW_COMPARISON = MIXED_RESULTS`，`HOLDOUT_VALIDATION = PARTIAL`。
