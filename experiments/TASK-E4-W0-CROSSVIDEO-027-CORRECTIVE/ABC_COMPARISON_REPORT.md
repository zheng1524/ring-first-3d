# ABC_COMPARISON_REPORT

| 配置 | 是否存在 | 原因 |
|---|---|---|
| A0 W0 单视频 | **有**（027 数值仍有效） | RGB 中位 0.446 px、p90 0.910；Ring MIO 0.160 |
| B0 共享 H（固定地标） | **BLOCKED** | Gate 1/2/3 未全部通过 |
| B1 共享 H + 共享地标 | **BLOCKED** | 同上 |
| C Ring 锚定 BA | **BLOCKED** | 同上 |

## 027 的 B/C 为何不能沿用

1. **变量集合错**（D1）：005 相机被实际优化；
2. **Ring 评价错**（D2）：`Ring004 53.162 / 54.156` 由 `inv(T0)@C` 产生 → 标 `INVALIDATED_PENDING_CORRECT_EVALUATION`；
3. **未收敛**（D6）：`success=False`。

因此本轮**没有**可报告的 B0/B1/C 真实结果。A0 仍是唯一有效基线。
