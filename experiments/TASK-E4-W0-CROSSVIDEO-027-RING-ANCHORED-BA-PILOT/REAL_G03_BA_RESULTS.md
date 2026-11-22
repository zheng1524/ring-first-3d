# REAL_G03_BA_RESULTS

`FROZEN_BA_OBSERVATIONS.csv`：106 观测 / 12 身份 / 11 台 FIT 相机；锚点 = 最后一台 005 FIT；
λ_R = 10、σ_rot 0.5°、σ_trans 0.25 mm（运行前写入 `config/BA_PROTOCOL.json`）。

| 配置 | RGB 中位 | p90 | p95 | max | Ring MIO | Ring 004 | Ring 005 | nfev |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A W0 per-video | 0.446 | 0.910 | 1.305 | 1.825 | 0.160 | 0.229 | 0.148 | — |
| B1 H+地标 | 3.804 | 13.014 | 14.960 | 45.692 | 0.160 | **53.162** | 0.148 | 20 |
| C BA（释放 004） | 0.594 | 3.572 | 9.012 | 41.184 | 0.971 | **54.156** | 0.631 | 20 |

## 每台相机修正（C）

见 `PER_CAMERA_UPDATES.csv`。005 全部为 0（锚点+未释放）；004 三台被释放，
旋转/平移修正量级与 `RING_3D_PAIRED_SENSITIVITY.csv` 中 0.5° 级扰动一致。

## 判定

- **C 被 Ring 门拒绝**：004 Ring 从 0.229 恶化到 54.2，而 RGB 中位仅从 3.80 改善到 0.59（相对 B1）。
- 优化器在 λ_R=10 下仍让 RGB 主导（Ring 残差为均值归一，量级 ~0.16 vs RGB 106 个 px 级残差）。
- 提高 λ_R 会让 RGB 失效、H 回到 Ring-compatible 但背景残差 ~mm 级 —— 这正是"无解"的表现，
  而不是权重没调好。

**状态：`REAL_BA_EXECUTED = YES`，`BA_ACCEPTED = NO`。**
