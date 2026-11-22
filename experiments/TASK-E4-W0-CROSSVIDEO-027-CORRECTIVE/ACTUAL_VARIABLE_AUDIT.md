# ACTUAL_VARIABLE_AUDIT

`runs/G03/ACTUAL_OPTIMIZATION_VARIABLES.json` 由 `core/p8_audit.py` 从**参数索引**生成，不是文字声明。

| 集合 | 相机 | 参数 |
|---|---|---|
| H | — | θ[0:6] |
| ANCHOR (frozen) | `G03_v004_raw00202` | 无索引 |
| RELEASED | `G03_v004_raw00242`, `G03_v004_raw00263` | θ[6:12], θ[12:18] |
| FROZEN (all 005 FIT) | 8 台 `G03_v005_raw*` | 无索引 |
| Landmarks | 12 | θ[18:54] |

`dim = 6 + 2*6 + 12*3 = 54`。断言：`anchor ∈ frozen`、`released ∩ frozen = ∅`、锚点无索引。

测试 `tests/test_corrective.py` **7/7 通过**（含"旧锚点一个相机都没冻结"的复现）。
