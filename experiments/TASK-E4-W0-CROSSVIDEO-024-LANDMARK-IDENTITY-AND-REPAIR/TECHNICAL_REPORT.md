# TASK-E4-W0-CROSSVIDEO-024 — 技术报告

```
MATH_VALIDATED:            PASS
SPLIT_VALIDATED:           PASS
LANDMARKS_VALIDATED:       PASS (317 / 806, FIT-only)
IDENTITIES_VALIDATED:      FAIL (15 候选 / 4 三维内点 / Ring 冲突)
CONSISTENCY_VALIDATED:     FAIL (GEOMETRY_CONFLICT)
OPTIMIZER_VALIDATED:       PASS (resume / rollback / gradient)
CROSS_VIDEO_GEOMETRY:      BLOCKED（未进入优化）
CROSS_VIDEO_GEOMETRY_ACCEPT: NO
BODY_CROSS_VIDEO_ADMISSION:  NO
G01/G05:                   BLOCKED_BY_W0_ADMISSION（0 ACCEPT，未改门限）
```

## 1. 本轮真正修好的（有测试）

1. **受控 GT 重写**：观测由 `H_true` 生成。A2 误差 **0.0054 mm / 0.016°**，A3 **0.0010 mm / 0.014°**（此前 A2/A6 无效）。
2. **Ring 歧义**：固定观测只变候选 yaw，Ring 曲线在 ±60° 内仅变 **0.47 px**（离散化伪信号），
   加入背景 3D 后同一扫描变化 **124.4 px** 且唯一极小在真值 → 证明 yaw 只能由 RGB 3D 提供。
3. **正式目标梯度**：FD 梯度由两套独立实现交叉验证，差 **<1e-9**（不再用不同函数自证）。
4. **真 checkpoint/resume**：40 步连续 vs 20+重载+20，`q` 逐位相同。
5. **强制拒绝回滚**：q/m/v/best 不变。
6. **不同 K 的极线测试**：`l5=F x4`、`l4=Fᵀ x5`，删除了 023 的无效断言。
7. **数据隔离顺序**：先冻结 SPLIT，再只用 FIT 视角建地标/身份（317/806，15 候选）。

## 2. 身份一致性（新增模块）

`core/landmark_consistency.py`（Open3D RANSAC，无尺度）：15 候选中 **4 个**在 1.0 mm 内支持同一刚体变换，
但该变换使 004 FIT 视角的 **Ring MAE 从 1.04 px 恶化到 7.70 px** → **GEOMETRY_CONFLICT**。
其余 11 个三维残差中位 8.9 mm（最大 42.7 mm）。

## 3. 可视化（六类，真实数据）

`runs/G03/VISUALIZATIONS/`
`01_identity_contact_sheet.png`（15 个候选真实 RGB 裁剪）、
`02_3d_identity_correspondences.png`（X004 / H·X004 / X005，三轴同尺度）、
`03_ransac_before_after.png`（拒绝者仍显示）、
`04_bidirectional_reprojection.png`（低/中/高误差 + 真实观测 vs 预测 + 箭头）、
`05_identity_residual_distribution.png`（3D mm / 正向 px / 反向 px 分列全量）、
`06_identity_support_matrix.png`（每个身份被哪些真实视角观测，FIT/HOLDOUT 区分）。

## 4. 回答

**Q1 023 的数学/梯度/Resume 是否修复？** 数学与 Resume：**是**（A2/A3/A6/A7 + resume + rollback + 双实现梯度，全部本轮实测）。
梯度：本次验证的是**双向 3D 重投影 + 前向/反向投影**这一正式项；Ring 的最邻域/Huber 折点未声称可导（已标注）。

**Q2 FIT/HOLDOUT 是否特征/地标/身份级隔离？** **是**：先冻结划分，地标与身份只用 FIT 建；HOLDOUT 只做评价。
**但** HOLDOUT 2D 评价 **n=0（NOT_EVALUABLE）**，没有用 0 冒充。

**Q3 历史 020 多视角身份是否恢复？** `features019`（SIFT/轨迹/三角化/match_desc）**真实运行**；
`features020.make` 的 PnP/投票/一对一**未接入**（依赖其 scope 运行包）→ **部分**。

**Q4 24 个候选中有多少支持同一刚体变换？** 023 的 24 个是全视角地标；本轮 FIT-only 后为 **15 个**，
其中 **4 个**在 1 mm 内支持同一刚体变换，但**全部与 Ring 冲突** → 0 个被接受。

**Q5 RANSAC 是否在受控实验中恢复真值？** **是**：0/20/50% 错误身份下误差 0；80% 时 0.42 mm/2.47°（边界）；100% 正确拒绝。

**Q6 真实 G03 三维一致性是否与 Ring、双向投影一致？** **否**：4 个内点的 H 与 Ring 冲突，
正向重投影中位 23.9 px、反向 6.1 px。

**Q7 新模块是否消除了错误身份的异常优化趋势？** **是**：本轮**没有**用错误身份做优化（023 的 5.24→4.04 是错误身份驱动），
而是阻断并给出证据。

**Q8 是否建立统一程序？** **是**：`run_cross_video_registration.py --group G`，三组同一入口；
G01/G05 正确返回 `BLOCKED_BY_W0_ADMISSION`。

**Q9 是否接受跨视频几何？** **NO**。剩余阻断：
① 身份数量与质量（15→4，且 Ring 冲突）；
② `features020.make` 的多视角投票/PnP/一对一未接入；
③ HOLDOUT 2D 证据为 0；
④ 时间簇切分未做；
⑤ Ring 仍是 `torus_contours` 近似，非 M/I/C/O。

## 5. 复现

```bash
M=experiments/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$M/core:src $PY $M/core/controlled_gt.py
PYTHONPATH=$M/core:src $PY -m unittest discover -s $M/tests -v
PYTHONPATH=$M/core:src $PY $M/run_cross_video_registration.py --group G03
PYTHONPATH=$M/core:src $PY $M/core/p4_visuals.py
```
