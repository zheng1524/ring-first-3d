# EXPERIMENT_PROTOCOL

- 输入：G05/005、G03/005，各 16 视角（006 prepared，官方 INIT Mask，DXY 重新导出 160/160 valid）。
- 轨迹/初始化/BA 预算/参考帧：三臂完全相同；Ring-First 初始位姿 **shared**。
- A0：冻结 `torus_residual + BA`。
- A1：替换 r_q 为 DXY 连续轮廓（τ=1.0 px）。
- A2：A1 + λ_R=1.0 显式归一化。
- 评价：原始边界 MAE、DXY inner/outer 距离、RGB held、正深度（统一程序）。
- held 仅评价，不参与臂/权重选择。

## 已知输入缺陷

16 视角取自**帧号前缀**（时间聚集），G05/005 held 47 px 由此而来；三臂同输入，相对比较有效，绝对值不可与 004 直接比。
