# FIT_HOLDOUT_AUDIT

| 项 | 值 |
|---|---|
| SPLIT 来源 | 025 `runs/G03/SPLIT.json`（SHA `b67e29e7bf5c39082a4b…`，与 026 相同） |
| 004 FIT / HOLDOUT | 3 / 3 |
| 005 FIT / HOLDOUT | 8 / 8 |
| Ring 评价视角 | 22 个 ACCEPT 全部（FIT 11 + HOLDOUT 11） |
| H025 评价 | 全部 22 视角，004 侧用 H，005 侧用 H⁻¹ |
| HOLDOUT 是否参与选择 | **否**（H025 来自 025 冻结结果，本轮未搜索/优化） |
| 三角化偏好 | 未使用 HOLDOUT 轨迹 |

本轮未重新做 HOLDOUT 双向投影：该数据属于 025/026 的评测结果（全量已记录：
52 匹配 / 24 个 >10 px / 80 无匹配；中位 7.91、p90 83.74 px）。本轮修复不改变这些观测，
只改变 Ring 与三角化的解释，故未重复计算。
