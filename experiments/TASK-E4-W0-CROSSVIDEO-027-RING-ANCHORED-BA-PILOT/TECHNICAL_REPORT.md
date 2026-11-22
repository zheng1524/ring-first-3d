# TASK-E4-W0-CROSSVIDEO-027 — TECHNICAL_REPORT

```
Gate 0 工程基础（026 入口修复 + 配对敏感性）:   PASS
Gate 1 观测正确（106 观测 / 12 身份 / FIT 隔离）: PASS
Gate 2 数学正确（residual-at-truth / 固定轨迹等价）: PASS（Ring 边缘冻结为近似）
Gate 3 受控 BA:                                PARTIAL（良态 ≤0.03°；粗差 14.9°）
Gate 4 共享 H 对照:                            FAIL（Ring 004 0.229 → 53.2）
Gate 5 真实 G03 BA:                            EXECUTED 但 REJECTED（Ring 004 54.2）
BA_ACCEPTED:                                   NO
CROSS_VIDEO_GEOMETRY_ACCEPT:                   NO
BODY_CROSS_VIDEO_ADMISSION:                    NO
G01/G05:                                       BLOCKED_BY_W0_ADMISSION
```

## 1. 本轮真正建立的东西

- **可运行的 Ring-anchored BA 适配层**（`core/ba_core.py`）：
  变量 H(6) + 每相机 δξ(6) + 12 个共享地标；残差 = 真实 RGB 重投影 + 历史 Ring 逐点距离 +
  W0 位姿先验 + 弱地标先验；求解器为 `scipy.optimize.least_squares`（TRF + Huber + 数值 Jacobian）。
- **固定轨迹适配器**（`core/fixed_track_tri.py`）与历史 019 输出**逐点相同**（max diff 0.0，317/806 条），
  因此 P0.2 的"固定轨迹"实验是真正的纯几何实验。
- **配对敏感性**（同相机矩阵同时算 Ring 与 3D）：004 在 0.5° 级相对误差下 Ring 几乎不变（0.229–0.259），
  三维位移中位 **1.85–4.32 mm**；005 为 0.92–1.47 mm。
- **受控真值 BA**：良态场景相机恢复 **0.03°/0.07 mm**、H 0.029°、地标 0.055 mm；
  Ring-only（87°）与单侧观测（8.4°）被 rank 诊断正确识别为不可辨识（42/48）。

## 2. 关键科学结果：Ring 与 12 个真实身份不可同时满足

| 配置 | RGB 中位 | Ring 004 |
|---|---:|---:|
| A W0（各视频自身地标） | 0.446 px | **0.229** |
| B1 H + 地标（相机固定） | 3.804 px | **53.162** |
| C BA（释放 004，λ_R=10） | 0.594 px | **54.156** |

把 004 相机移动到"能解释 005 侧真实身份"的位置，Ring 误差恶化约 **230×**。
这不是权重问题：提高 λ_R 只会让 RGB 失效、H 回到 Ring-compatible，而背景残差仍有毫米级。
即 **在现有 12 个三维身份 + W0 位姿下，Ring 与跨视频背景几何存在毫米级不相容**，
与 026 的 66 对距离差中位 3.90 mm、027 配对敏感性 1.85–4.32 mm 相互印证。

## 3. 失败归因（按优先级）

1. **可辨识性/不相容（主因）**：Ring 对 yaw 完全不可见；12 个身份的三维位置与 Ring 锚定相机冲突。
2. **数值优化（次因）**：粗差场景未收敛到真值（14.9°，max_nfev=60）；多相机扰动 0.88°。
3. **观测**：12 个身份只有 106 条 FIT 观测（每身份 3–8 视角），信息量有限。
4. **初始化**：H 从 identity 起步，yaw 冷启动在良态场景被 RGB 拉回，但粗差下失败。

## 4. 九个问题

1. **Ring 能可靠约束哪些自由度？** 倾斜/平移（世界轴向），**不能**约束绕法向 yaw；
   局部旋转在 5° 量级可见，但 0.5–1° 与三维形变脱耦。
2. **仅优化共享 H 能到什么程度？** 若允许重构地标，RGB 3.8 px、Ring 004 53.2 → **不可接受**；
   若固定地标（仅 H），退化更严重。共享 H 无法弥合 Ring 与背景的冲突。
3. **受控 BA 能否恢复真值？** 良态（含 25° yaw 冷启动、低视差、不同 K、局部扰动）**能**（≤0.03°）；
   粗差场景**不能**。
4. **真实 G03 能否在 Ring 保持下改善 RGB？** **否**：C 的 RGB 0.59 是相对 B1 的改善，
   但 Ring 被破坏到 54.2；相对 A 的 0.446 也没有改善。
5. **改善是否出现在 HOLDOUT？** **NOT_EVALUABLE**（模型已被 Ring 门拒绝，不做事后挑选）。
6. **每台相机修正多少？** 见 `PER_CAMERA_UPDATES.csv`；004 三台为 0.5° 量级/亚毫米，
   005 全部 0（锚点/未释放）。
7. **修正是否合理？** 数值量级合理，但方向**不可接受**（Ring 54×）。
8. **12 个身份一致性是否改善？** 在 C 中 RGB 中位 0.59（FIT），但代价是 Ring 破坏；
   这不是"改善"，是"用 Ring 换 RGB"。
9. **不可辨识的自由度？** 绕 Ring 法向的 yaw（S8）、单侧观测下的整体位姿（S9）。
10. **若失败，主因？** 可辨识性/观测不相容（主）+ 粗差鲁棒性（次），不是求解器 bug
    （residual-at-truth RGB = 0，固定轨迹等价 max diff = 0）。
11. **是否有可用相机结果？** **没有**。本轮未产生可进入三维重建的相机。
12. **是否引入重复流程/泄漏？** 无第二套主线（单入口 + 适配层）；HOLDOUT 未参与任何优化；
    但 Ring 边缘在优化内**冻结**属于已记录近似。

## 5. 下一轮建议（不擅自执行）

1. **先做单视频 Ring BA**（不引入跨视频身份）：验证 004/005 各自相机在 Ring + 自身多视角轨迹下能否稳定收紧；
2. 用 **026-CORRECTIVE 的配对敏感性**反推合理先验：0.5° 相对误差已对应 2–4 mm，说明要么相机精度需提升，
   要么跨视频配准目标必须放宽到 mm 级而非亚毫米；
3. 复核 12 个身分的**二维观测来源**（track 成员是否混入错误特征）——虽然人确认了对应，但每条观测的二维位置精度未单独验证；
4. 若要继续 BA：把 Ring 作为**硬约束/罚函数**而非均值残差，并加入粗差检测（而非仅 Huber）。

## 6. 复现

```bash
B=experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$B/core:$B/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $B/run_cross_video_registration.py --group G03 --stage full-027
```
耗时：p0 约 90 s；p3 约 60 s；p4 约 256 s；p6 约 20 s。
