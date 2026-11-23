# FIT_HOLDOUT_RESULTS

- 划分：`rng(2026)` 从 12 身份中抽 8 FIT / 4 HOLDOUT（`runs/SPLIT.json`），HOLDOUT 不参与候选评分（`test_holdout_does_not_change_selection`）。
- 评价：两条流程的最终模型投影到 FIT/HOLDOUT 的 004/005 观测。

| 流程 | 组 | n | RGB 中位 | p90 |
|---|---|---:|---:|---:|
| 旧 | FIT | 48 | 0.000 px | 0.000 |
| 旧 | HOLDOUT | 24 | 0.000 | 0.000 |
| 新 | FIT | 48 | 0.000 | 0.001 |
| 新 | HOLDOUT | 24 | 0.000 | 0.001 |

**如实说明**：两条流程在合成场景都收敛到机器精度，HOLDOUT **无法区分优劣**。
因此本轮不能声称"HOLDOUT 证明新路线更好"；只能说"没有观察到 HOLDOUT 退化"。
需要更难的场景（噪声、低视差、参考相机扰动）才能让 HOLDOUT 具有判别力。
