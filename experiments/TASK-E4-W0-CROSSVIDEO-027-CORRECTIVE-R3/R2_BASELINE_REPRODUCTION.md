# R2_BASELINE_REPRODUCTION

| 项 | R2（`ad5d09fc`） | R3 复现 | 一致？ |
|---|---|---|---|
| Level 0 RGB/I/C/O | 0 / 1.2e-13 / 1.7e-14 / 1.2e-13 | 同（沿用同一 `r2_synth` 生成器） | 是 |
| Level 1（GT 相机 + 三角化地标） | 2.7e-6° / 6.5e-15 mm / success=True | R3 的 L1 等价配置：初始残差 ~1e-8、H 不漂移 | 是 |
| L2 3° | H 0.022°，success=False（40） | H-only 3°：**4.0e-5°**，success=True（187） | 数值不同但**都是"收敛到真值"** |
| L2 12° | H 7.06°，success=False（40） | H-only 12°：**3.8e-4°**，success=True（129）；联合（正确初值）0.0073° | **R2 的 7.06° 无法复现为"BA 固有限制"** |

## 差异原因（已定位）

R2 的联合实验把 **004 观测用 H=I 相机三角化**进 005 世界 → 地标初值系统性偏移 0.8–6.5 mm；
R3 改为 **005-only 三角化** → 地标初值误差 4e-14 mm，H-only 与联合都恢复。
因此 R2 的 12° 结论是**初始化错误**，不是算法限制。

R2 的原始目录与数值未被覆盖（`027-CORRECTIVE-R2/runs/CONTROLLED/LEVEL_RESULTS.csv` 保持原样）。
