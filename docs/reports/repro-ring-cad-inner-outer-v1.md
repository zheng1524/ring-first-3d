# 复现报告 — ring-cad-inner-outer v1

**状态：PENDING_INDEPENDENT_REPRODUCTION（本执行智能体自测 PASS，不构成独立复现）**

- 入口：`runs/ring-cad-inner-outer-v1/reproduce.sh`
- Fixture：G03/005 的 raw00070 / raw00142 / raw00215
- 实测（B0 相机，inner/outer MAE，px）：

| view | inner | outer | expected | pass |
|---|---:|---:|---|:--:|
| raw00070 | 1.50 | 2.05 | 1.50 / 2.05 | ✅ |
| raw00142 | 1.15 | 1.73 | 1.15 / 1.73 | ✅ |
| raw00215 | 0.64 | 1.46 | 0.64 / 1.46 | ✅ |

容差 0.25 px；`REPRO: PASS`。

**限制**：仅 3 视角几何检查，不是多视角 BA 验收。
