# LANDMARK_PERTURBATION_AUDIT

- 基线地标：**005-only 三角化**（三台 005 GT 相机 + 冻结二维观测，历史 019 逐轨迹代码），与 GT 差 0。
- C 组扰动：`X_init = X0 + ΔX`，`ΔX` 由种子 0 生成，方向归一化，幅度 1 mm / 3 mm。
- 扰动方向类型：`random`（三维随机单位方向）、`depth`（沿 +/−Z）、`perp`（垂直方向，本轮实现但主实验用 random）。
- 未通过改变二维观测模拟三维误差（观测始终冻结）。

| 组 | 幅度 | 初始地标误差（实测） |
|---|---:|---:|
| C1 | 1 mm | 1.0 mm（`C_landmark_only_1`） |
| C3 | 3 mm | **3.0 mm**（`C3_landmark_only`） |
- 所有地标 ID、支持相机、视差角保存在 `RESULT.npz` / `SUMMARY_ALL_RUNS.csv`。
