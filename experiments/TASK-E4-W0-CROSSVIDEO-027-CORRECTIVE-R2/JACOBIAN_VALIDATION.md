# JACOBIAN_VALIDATION

| 项 | 结果 |
|---|---|
| 残差向量维度（L0） | 10 970 |
| GT 处残差 | 最大 8.9e-09；RGB 0.0；I/C/O ≤1.2e-13 |
| 数值 Jacobian 秩（L1） | 记录于 `LEVEL_RESULTS.csv`（`rank`/`n_params`） |
| 参数维度 | 6 + 6×n_released + 3×n_lm（L1 = 6+12+36 = 54） |
| 冻结变量 | `camvar` 断言 + 测试：锚点/005 无参数索引 |

未做解析 Jacobian 与数值 Jacobian 逐列比对（`NOT_DONE`），SciPy 使用 2-point 差分。
