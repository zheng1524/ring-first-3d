# H_ONLY_VARIABLE_AUDIT

## 实现方式

`core/r3_run.py::solve(mode='h_only')` 的参数向量**只有 6 个**：`theta = dxi_H`，`H = Exp(dxi_H) @ H0`。
地标 `X_fixed` 与所有相机 `dxi ≡ 0` 以**闭包常量**传入残差函数，不在参数向量中。

## 证据

| 项 | 值 |
|---|---|
| `n_params` | **6**（每次 H-only 运行的 `METRICS.json`） |
| Jacobian 形状 | 4417 × **6** |
| 秩 | **6 / 6** |
| 条件数 | 46.8（0°）/ 44.4（3°）/ 47.4（12°） |
| 地标来源 | **仅 005 三个 FIT 相机的二维观测**（`r2_synth.triangulate`，历史 019 逐轨迹代码） |
| 地标在优化中 | **严格不变**（不在残差参数中，`RESULT.npz` 的 `X` 与 `X_init` 逐位相同） |
| GT 地标 | 未使用（仅用于最终评分） |
| GT H | 未使用（仅用于生成观测与评分） |

`runs/controlled/Honly_yaw*/RESULT.npz` 保存 `H_init/H/X_init/X`，`METRICS.json` 保存完整求解器状态。
