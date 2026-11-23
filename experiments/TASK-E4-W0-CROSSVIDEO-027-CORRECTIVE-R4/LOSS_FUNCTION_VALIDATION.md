# LOSS_FUNCTION_VALIDATION

单一残差构造：`ba_core_r4.rgb_residual(e, mode)`
- `huber`：`r=sqrt(2*rho(|e|/3))`
- `squared`：`r=e/3`（二维）
- `dir2d`：方向保持（已实现，**未用于结论**）

| 检查 | 结果 |
|---|---|
| 大残差 Huber vs 平方 能量差 | >1e-3（确实不同） |
| 小残差（1e-4 扰动）相对差 | <1e-6（符合二次区一致性） |
| 联合路径是否使用同一 `rgb_mode` | 是（`residual_vector` 唯一入口） |
| `0.5‖r‖²` vs 分块能量和 | **<1e-9**（21 个 run 全部 `energy_consistency=0.0`） |
| Ring I/C/O 计数 | 每 run >0，来自实际残差数组 |
| 负深度 | 本受控数据 0 例 |
