# RESIDUAL_AND_JACOBIAN_VALIDATION

| 检查 | 结果 |
|---|---|
| RGB 残差在真值处 | **rms = 0.0**（合成数据，精确投影） |
| Ring 残差在真值处 | rms 0.646（真实 Ring 观测本身有 ~1.9 px 残差，非零是正确行为） |
| 固定轨迹三角化 vs 历史 019 | **max diff 4 = 0.0，5 = 0.0**（317 / 806 条，逐点相同） |
| Ring 均值语义 | 逐点 `d/3/√N`，Σr² 在二次区 = 历史均值；Huber 折点附近为近似（记录） |
| SE(3) 增量语义 | 继承 026-CORRECTIVE：矩阵差 7.1e-15，端到端损失等价 ≤1.2e-5 |
| 数值 Jacobian | TRF 2-point；未提供解析 Jacobian（已知限制） |
| 条件数 | 受控良态场景 rank=48/48；S8/S9 rank=42/48（可辨识性下降） |

**未做**：解析 Jacobian 与数值 Jacobian 的逐列比对（`NOT_DONE`）。
