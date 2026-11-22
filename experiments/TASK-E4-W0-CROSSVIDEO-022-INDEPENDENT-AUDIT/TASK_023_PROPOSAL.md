# TASK_023_PROPOSAL

## 目标（语义）

`L = L_Ring(M,I,C,O) + 0.2·L_SIFT3D + 0.02·L_EPI + 0.01·L_Prior`，
`H = exp(hat(q*s)) @ H_seed`（`q=(v,ω)`），固定 005 世界，方向 `H_(005<-004)`。

## 阶段

| 阶段 | 内容 | 通过条件 | 停止条件 |
|---|---|---|---|
| P0 | 合入 F1–F5、F10（数学/工程） | 全部测试逐位可复现 | 任一 FAIL |
| P1 | 干净环境 Level-1：用归档相机/匹配/观测重算 G03，不依赖 `/home/liu` | 与 021 数值一致（同定义） | 不一致 |
| P2 | 019 特征/轨迹/三角化接入（005 → 004） | 产出真实 2D-3D/3D-3D，`L_F` 非零 | 无 3D 身份 → BLOCKED |
| P3 | Ring M/I/C/O 接入或等价性证明 | 四项分别可算、梯度有限 | 观测缺失 → 标 RING_OBSERVATION_INCOMPLETE |
| P4 | 双侧留出 + 受控 GT（F6/F9） | 004 不泄漏；已知 GT 恢复 | 泄漏/不恢复 |
| P5 | G03 正式实验 | FIT/HOLDOUT 分别报告；3D 中位误差有界 | 不达 → 报失败 |
| P6 | G01/G05 同协议回归 | 仅诊断，保持 BLOCKED | — |

## 验收状态机

`AUDIT_PASS`（022，已完成）→ `MATH_PASS`（P0/P1）→ `LANDMARK_PASS`（P2）→ `CROSS_VIDEO_GEOMETRY_ACCEPT`（P5，独立三维证据）→ 才允许 `BODY_CROSS_VIDEO_ADMISSION=YES`。

当前：`MATH_PASS` 未达成（见 `MATHEMATICAL_DEFECTS.csv`），`BODY=NO`。
