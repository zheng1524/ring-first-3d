# RING_RESIDUAL_EQUIVALENCE

- 正式 Ring 残差：`r = sqrt(2·w·ρ(d/3)/N)`，`w = {I:0.35, C:0.05, O:0.35}`（与 `ba_core_r4` 完全同一函数 `ring_energy.ring_residuals`）。
- 候选精化与 BA 现在使用**同一个** `ring_vector_for_H` 构造。
- 数值：向量能量 `0.5‖r‖²` 与 BA 块能量相对差 **<1e-12**（`test_vector_matches_energy_and_length`）。
- 残差长度 = 004 相机实际参与损失的 I/C/O 观测点数和（少于等于观测总数，因逐点距离需要有效边）。
- 缺失某类观测时返回空向量，不计入能量；**不会**静默补零（空数组长度 0）。

## 能量路径对照

| 路径 | 定义 | 一致性 |
|---|---|---|
| `ring_vector_for_H` | I+C+O 残差向量 | 基准 |
| `BAProblemR4.blocks(..., H)` | 同一残差函数 | 与上一致（004 块） |
| 独立 `RE.rho` 求和 | `w·mean(ρ(d/3))` | 与 `0.5‖r‖²` 在二次/Huber 区完全一致 |
