# PROGRESSIVE_BA_COMPARISON

## 旧流程 vs 新流程（端到端）

| 流程 | 状态 |
|---|---|
| 旧：005-only 三角化 → H-only（H=I 起）→ M3b | **NOT_EXECUTED**（`PIPELINES.csv` 脚本 bug：M2/M3 列都写最终指标、M3b 的 X 未更新） |
| 新：Ring+RGB H → 共同三角化 → M3b | **NOT_EXECUTED**（同上） |

**不报告这两行数字**。可替代证据是**初始化 → 三角化**环节（同一批观测、固定相机）：

| H | H 误差 | 三角化误差 |
|---|---:|---:|
| I（旧路线起点） | 12.027° | 1.800 mm |
| Ring+RGB（新路线起点） | **0.512°** | **0.156 mm** |

## M1/M2/M3b/M4 四模式

- M1（仅 X）：C 组 7 个 run 已执行（见 `CORRECT_H_LANDMARK_RECOVERY.md`）；
- M2（仅 H）：B 组与 T 组已执行；
- **M3b（H+联合）**：参数 6+36=42，已通过 `test_M3b_joint_has_H_and_X`；B 组执行 2 例；
- **M4（+2 台 004）**：参数 54，已通过 `test_M4_parameter_layout`；B 组执行 1 例。

## 公平性

- 预算：M1=80、M2=60–100、M3b=60（30+30）、M4=80；**不完全相同**，已逐行记录 `nfev`；
- 不宣称"渐进优于直接联合"，因为端到端对照未有效执行。
