# GT_LEAKAGE_AUDIT

| 环节 | GT 是否进入 | 证据 |
|---|---|---|
| 生成 RGB/Ring 观测 | 是（允许） | `r2_synth.build_scene` / `ring_observations` |
| 基线地标 X0 | **否**（005 二维观测 + 005 GT 相机三角化；相机是 GT 但这是"参考相机"定义） | `baseline_X` |
| C/D 组地标扰动 | 以 X0 为基准加噪，**不使用 GT X** | `perturb_X(X0, ...)` |
| H 初值 | 恒为 I（不使用 GT H） | `run_group` |
| 可见边缘 | 由初始相机（含扰动）计算，**不使用 GT H** | `geom_from(cams_world)` |
| 权重/门限调整 | 未使用 GT | 配置冻结 |
| 最终评价 | 使用 GT（允许） | `se3_err` / `lm_err` |

**实验干预说明**：B/C/D 的扰动幅度用 GT 定义（"给 3 mm 误差"），这属于受控干预定义，不是优化输入。
