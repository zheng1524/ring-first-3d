# FIT_HOLDOUT_COMPARISON

| 项 | FIT | HOLDOUT |
|---|---|---|
| 相机 | 11（3×004 + 8×005） | 11（3+8），未参与优化 |
| 冻结观测 | 106 | 0（本轮未重建 HOLDOUT 2D 匹配） |
| A W0 RGB | 0.446 px 中位 | 025 全量：52 匹配，中位 7.91、p90 83.74 px |
| B1 RGB | 3.804 | NOT_EVALUABLE |
| C RGB | 0.594 | **NOT_EVALUABLE** |
| Ring FIT | A 0.160 / C 0.971 | 未单独报告 |

**HOLDOUT 判 NOT_EVALUABLE 的理由**：C 配置已被 Ring 门拒绝（004 Ring 54.2），
对已被拒绝的模型再报告 HOLDOUT 数字属于事后挑选。故不声称"BA 在 HOLDOUT 上改善"。
未把未评价项记为零。
