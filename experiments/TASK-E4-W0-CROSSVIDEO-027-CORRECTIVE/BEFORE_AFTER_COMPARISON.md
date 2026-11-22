# BEFORE_AFTER_COMPARISON

| 项 | 027 | 027-CORRECTIVE |
|---|---|---|
| 005 相机是否被优化 | **是**（报告称否）→ D1 | **否**（`frozen` 9 台，无参数索引） |
| 004 锚点 | 无（元组无效） | `G03_v004_raw00202` 显式 frozen |
| 参数维度 | 未核对 | **54**（6 + 2×6 + 12×3），断言通过 |
| Ring 评价变换 | `inv(T0)@C`（错） | `C@inv(T0)`（`canonical` 一致 1e-12） |
| BA Ring 目标 | 仅 I/O，λ 平方成 100 | I/C/O 精确能量映射，λ 为能量权重（4× 验证） |
| 受控初值 | GT 三维点（泄漏） | 历史 019 三角化（X_init 与 GT 差 0.81–6.47 mm） |
| 受控恢复 | 0.030°（泄漏） | **3.0–10.6°，全部 success=False** |
| 真实 B/C | 报告 Ring 53/54 | **INVALIDATED**，未重跑（Gate 3 FAIL） |
| HOLDOUT | NOT_EVALUABLE | NOT_EVALUABLE（无模型） |
| 收敛状态 | success=false 未报 | 明确记录并阻断 |
