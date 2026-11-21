# 变更诊断

## 009 inner-only 崩溃（负结果登记）

- 现象：held 2.38 → 51.45 px。
- 010 定位：**单一 CAD 位姿无法同时拟合 DXY inner 与 outer**；inner-only 为把 inner 从 1 px 压到 0.06 px，需要 1.4 mm / 3.5° 的相机位移，被 RGB 拒绝。
- outer 有符号残差全域 −0.9…−1.6 px（CAD outer 系统性内缩）。
- 状态：`implementation/geometry conflict`，**不是** "inner 方法被否定"。

## 011 修复项

1. 弧长权重改为 `sqrt(w·Δs/L_ref)`，消除采样密度依赖。
2. 有符号残差改为 `(p_DXY − p_CAD)·n_outward`，并用解析测试校验符号。
3. `UNOBSERVED` 零贡献 + 状态记录（不再用常数残差）。
4. J2 适配层用 `sqrt(rglen/counts)` 抵消冻结 BA 的 `sqrt(counts/rglen)`，使各块权重与设计一致。
