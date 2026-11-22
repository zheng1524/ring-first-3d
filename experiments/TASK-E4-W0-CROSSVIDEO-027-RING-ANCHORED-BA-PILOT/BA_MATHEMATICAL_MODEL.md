# BA_MATHEMATICAL_MODEL

## 变量与参数化

```
H    = Exp(dxi_H) @ H0                       (H = H_005<-004)
T005 = Exp(dxi_005,i) @ T005,i^W0            (c2w, 005 frame = Ring world)
T004 = Exp(dxi_004,i) @ T004,i^W0            (在 004 帧内)，世界坐标用 C = H @ T004
X_j  ∈ R^3                                   (共同世界坐标 = 005/Ring 世界)
```
`T⁻¹X` 用列向量约定：`Xc = (X - C[:,3]) @ C[:3,:3]ᵀ`（与历史 019 `project` 完全一致）。

## 目标

```
E = Σ_obs ρ(‖π(K,T⁻¹X) - u‖)                      [RGB, ρ = Huber(f_scale=3)]
  + λ_R Σ_ring ρ(d_i/3)/N                          [Ring, 历史 M/I/O 逐点距离]
  + Σ_cams ‖dxi‖²_Σ                                [位姿先验 σ_rot=0.5°, σ_trans=0.25 mm]
  + Σ_lm  ‖X_j - X_j^019‖² / σ_geo²                [弱几何先验 σ_geo=50 mm]
```

**Ring 语义**：历史 `RingRenderer.losses` 返回加权**均值** `mean(huber(d/3))`。
为放进最小二乘，每个残差取 `d_i/3/√N`，使 `Σ r²` 在二次区等于该均值（一次项/Huber 折点处为近似，
已在 `RESIDUAL_AND_JACOBIAN_VALIDATION.md` 记录差异）。**没有**对总损失开平方。

## Gauge

- 005 的 Ring 世界固定；
- 固定最后一台 005 FIT 相机（anchor）；
- H 承担 004 视频级的整体放置，004 相机只做小修正；
- Ring 绕对称轴的 yaw 不可由 Ring 确定（受控 S8 显示 rank 42/48，误差 87°）。

## 求解

`scipy.optimize.least_squares(method='trf', loss='huber', f_scale=3, x_scale='jac', max_nfev=20)`。
Jacobian 为数值差分（TRF 内部 2-point），未提供解析雅可比。
Ring 可见边缘在一次优化内**冻结**（初始位姿计算），评估时重新计算 —— 已在报告中标注为近似。
