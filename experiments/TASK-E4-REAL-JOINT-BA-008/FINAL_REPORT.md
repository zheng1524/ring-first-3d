# TASK-E4-REAL-JOINT-BA-008 — FINAL_REPORT

**STATUS: `PARTIAL`（G03/005 A0/A1 完成；A2 与 G05/005 未完成）**

## 0. 结论

修复 007 的工程缺陷后，**G03/005 上 A1 不再像 007 那样退化**：

| 指标 | A0（修复后） | A1（修复后） | 007 中的 A1 |
|---|---:|---:|---:|
| inner→DXY (px) | **0.97** | 1.26 | 1.76 |
| outer→DXY (px) | **1.68** | 2.14 | 2.55 |
| RGB held 中位 | 2.38 | **2.33** | 3.87 |

**Q1（007 退化有多少来自工程错误）：大部分。** 修复后 held 从 3.87 回到 2.33（与 A0 的 2.38 持平略优），说明 007 的退化主要不是"DXY 轮廓本身有害"，而是缓存/模式/权重装配问题。

## 1. 已修复（P0）

| 缺陷 | 修复 | 证据 |
|---|---|---|
| `_TREE` 全局 id() 缓存（id 复用→脏曲线） | **删除**，改为无缓存的精确点到线段距离 | `test_no_cache_pollution`：50 次对象churn 后距离逐位不变 |
| A1/A2 模式判断失效（`mode=='A1'` 但传 `dxy_contour`） | 改为显式臂名 `A0/A1/A2` | `joint_residual_blocks.ring_residual(arm,...)` |
| `K0=None` 传入 `torus_contours` | 统一 `K = K0 if K0 is not None else K_default` | 007 已修，008 复核 |
| 采样长度不足/重复点 | 弧长重采样，**恒返回 m 点**，接缝处理 | `test_fixed_length`、`test_arc_length_uniform`（间距 CV<2%） |
| 退化时返回零残差（伪装完美拟合） | 显式惩罚块（值 10） | `test_degenerate_not_zero` |
| 距离依赖 1px 离散化 | 精确点到线段距离 | 单测 5/5 通过 |

## 2. BA 缩放审计（`BA_LOSS_SCALE_AUDIT.md`）

冻结 BA：`ring_residual(cur[i], ob[i]) * sqrt(max(1,counts[i]) / max(1,rglen[i]))`。

**关键结论：** 由于乘了 `sqrt(counts/rglen)`，**每个视角的 Ring 总贡献 ≈ counts[i] × mean(r²)**，与 `rglen`（采样数）几乎无关。
因此把边界项从 128 点换成 512 点**不会**自动让 Ring 强 4 倍——007 担心的"采样数改变权重"在总权重意义上是自洽的。
但这同时意味着：**Ring 权重被 RGB 轨迹数 counts[i] 调制**，这是一个不合理耦合（视角特征多→Ring 更硬）。A2 若要真正独立加权，必须绕过该耦合，本轮未完成。

## 3. 未完成

- **A2**（柔性 τ=1 + λ_C 扫描）：仅实现未运行。
- **G05/005** 三臂：未运行。
- 图 B/C/D/F、`LOSS_AND_GRADIENT_DIAGNOSTICS.csv`：未生成。
- DXY `inner_points/outer_points` 未导出；可见弧仍用"椭圆采样点到真实边界点 ≤2px"，已记录为偏差。

## 4. 已完成可视化

- `visualization/A_ring_projection/G03_005_A.png`：3 个真实视角 ×（Ring-First 初值 / A0 / A1），DXY 青/紫红，CAD 黄/橙，同一画面同一坐标。
- `visualization/E_camera_network/G03_005_E.png`：A0/A1 相机中心（`c2w[:3,3]`）与光轴（`R@[0,0,1]`）+ Ring CAD。

## 5. 回答

- **Q1** 修复后 held 3.87→2.33，**007 的退化主要是工程性的**（缓存/模式/装配），不是 DXY 轮廓的原罪。
- **Q2** A1 是否意外削弱 Ring？在总权重意义下没有（见 §2）；但 per-view 权重被 counts 调制的问题仍在。
- **Q3** 正确实现后 DXY 连续轮廓是否更稳？**G03/005 上 A1 的 held 与 A0 持平略优（2.33 vs 2.38），但 inner/outer 距 DXY 变差**（1.26/2.14 vs 0.97/1.68）——即相机更服从 RGB，而非更贴合 DXY。
- **Q4** A2 能否更进一步？**未运行，不能回答。**
- **Q5** 冲突细节：未做逐区域归因（需图 B/C）。
- **Q6** 现在更适合做主线的是 **A0**；A1 可作为"RGB 略优"的备选，但需 A2 与 G05 验证后再定。
