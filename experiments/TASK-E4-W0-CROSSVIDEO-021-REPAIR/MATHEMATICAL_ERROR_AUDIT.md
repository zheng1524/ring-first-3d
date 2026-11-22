# MATHEMATICAL_ERROR_AUDIT

| 项 | 020（无效） | 021（修复） | 验证 |
|---|---|---|---|
| SE(3) 参数 | `exp(q[:3])`，平移另取 `q[:3]` → 3 DoF | `exp(hat(q·scale))`，`q=(v,ω)` 6 个独立分量 | 6 参数逐一扰动均改变位姿；与 scipy `expm` <1e-12；与 pytorch3d `se3_exp_map`（`(v,ω)`+转置）~1e-17 |
| Sampson | `|Fx1|+|Fᵀx2|` | `sqrt((Fx1)₁²+(Fx1)₂²+(Fᵀx2)₁²+(Fᵀx2)₂²)` | 与点到极线距离一致；同 H 下旧 3.28 vs 新 4.64 px |
| 累计约束 | 单步 `H_cand·H_cur⁻¹` | `H_cand·H_seed⁻¹` | `test_cumulative_bound`：0.163 mm / 3.55° < 1.2/10 |
| Adam | 拒绝后保留动量 | 拒绝回滚位姿与 m/v | `test_rejected_step_rolls_back_state` |
| 相机/投影 | — | `q=Rᵀ(X−C)`，正深度、K 显式 | `test_camera_projection_and_depth` |

**只检查 det(R)=1 不足以发现 3-DoF 退化** —— 旧的 det 测试确实通过，这就是漏检原因。
