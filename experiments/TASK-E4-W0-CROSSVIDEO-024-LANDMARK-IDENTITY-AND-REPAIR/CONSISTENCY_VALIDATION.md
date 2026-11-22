# CONSISTENCY_VALIDATION

模块：`core/landmark_consistency.py`（新增、授权），Open3D `registration_ransac_based_on_correspondence`
+ `TransformationEstimationPointToPoint(with_scaling=False)`，无自由尺度。

## 受控验证（A7）

| 错误身份比例 | 状态 | 内点 | 恢复误差 |
|---:|---|---:|---|
| 0% | SUPPORTED | 30/30 | 0 mm |
| 20% | SUPPORTED | 24/30 | 0 mm |
| 50% | SUPPORTED | 15/30 | 0 mm |
| 80% | SUPPORTED | 7/30 | **0.42 mm / 2.47°**（边界，已记录） |
| 100% | INSUFFICIENT | 2/30 | — |
| 共线 | DEGENERATE | — | — |
| 3 点 | INSUFFICIENT | — | — |

## 真实 G03

| 项 | 值 |
|---|---|
| 候选 | 15 |
| 门限（**实验前锁定**） | **1.0 mm**；敏感性 0.5 / 1.0 / 2.0 mm |
| 内点 | **4**（fitness 0.267） |
| 0.5 mm | INSUFFICIENT（3） |
| 2.0 mm | INSUFFICIENT（3） |
| SO(3) | orthogonality 8.9e-16，det 1.0 → 合法 |
| 退化检查 | 非共线（奇异值比 0.53） |
| **Ring 兼容性** | **FAIL**：Ring MAE W0 **1.04 px** → RANSAC H **7.70 px** |
| 结论 | **`GEOMETRY_CONFLICT`** |

按任务要求：候选 H 与 Ring 冲突 → 保留结果、标记不一致、**不进入正式优化**。
