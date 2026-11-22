# TASK-E4-W0-CROSSVIDEO-023 — 技术报告

```
P0_EPIPOLAR_DRAWING_FIXED:      PASS
P1_INDEPENDENT_F_VALIDATION:    PASS (结论与 022R 相反)
P2_MATH_ENGINEERING_FIXES:      PARTIAL (checkpoint 已实现；resume/gradient 测试未执行)
P3_HISTORICAL_LANDMARKS_RUN:    PASS (738 + 1213 个真实地标)
P3_CROSS_VIDEO_IDENTITY:        LANDMARK_BLOCKED (24 个身份、残差 ~58 px)
P4_TWO_SIDED_HOLDOUT:           PARTIAL (按视角切分，但地标三角化用了全部视角)
P5_CROSS_GROUP:                 G01/G05 BLOCKED (0 ACCEPT，未绕门限)
CROSS_VIDEO_GEOMETRY_ACCEPT:    NO
```

## 1. P0：022R 极线画反了（已证实并修复）

`forensic_extra.py` 中：

```python
for col, (im, pts, Fl, color) in enumerate(((im4, uu, Fpose, ...), (im5, vv, Fpose.T, ...))):
    l = Fl @ np.r_[uu[j] if col == 0 else vv[j], 1.0]
```

- 004 面板：`Fpose @ x_004` 是**005 图上的极线**，却画在 004 图上；
- 005 面板：`Fpose.T @ x_005` 是**004 图上的极线**，却画在 005 图上。

正确关系：`l_005 = F x_004`，`l_004 = Fᵀ x_005`。
修正后脚本：`tools/forensic_epipolar_fixed.py`（原脚本保留为 `tools/forensic_epipolar_ORIGINAL_buggy.py`），
输出 `runs/G03/05_Fpose_vs_Fimg_epipolar_FIXED.png`、`epipolar_lines_FIXED.csv`、4 张真实局部裁剪 `crop_*.png`。
数值测试 `tests/test_epipolar_drawing.py`：纯平移场景下极线水平（方向约定）、
真实 G03 匹配上单侧点线距离与 Sampson 一致（Sampson ≤ 两侧距离）、裁剪端点在图内。**3/3 PASS**。
**021 的 H 与误差数据未改动。**

## 2. P1：F_img 的"0.82 px"是样本内过拟合（关键纠正）

| 对照 | F_pose 中位 | F_img 中位 | F_img 更好的对数 |
|---|---:|---:|---:|
| 022R 样本内（同一批点拟合+评价） | 4.664 px | **0.818 px** | 96/96 |
| **随机半划分（保留空间覆盖）** | 4.790 px | **2.885 px** | 60/87 |
| **空间左/右划分（外推）** | 4.172 px | **17.764 px** | 23/87 |
| 单应矩阵（退化探针，随机半划分） | — | 45.78 px | — |

- 样本内的 5.7× 优势在**样本外缩到 1.7×**，在**空间外推时反转**（F_img 反而差 4.3×）。
- 单应矩阵在留出点上比两者都差一个量级 → **不是平面/低视差退化**。
- 结论：022R 的"长尾主因是相机几何而非匹配"**不能**由 0.82 vs 4.66 支持；
  正确表述是：匹配有真实信号（自由 F 能到 ~2.9 px），但 022R 的数字被样本内拟合放大。
- 文件：`P1_F_holdout_comparison.csv`、`P1_random_split_control.csv`、`P1_epipoles.csv`、`06_P1_F_holdout.png`。

## 3. P2：数学与工程

| 项 | 状态 | 说明 |
|---|---|---|
| 6-DoF SE(3)、标准 Sampson、累计边界 | 继承并复核 | 023 的 `core/se3.py` 即 021 已验证实现；本轮未改公式 |
| checkpoint | **已实现** | `core/p3_objective.py::optimize` 每 10 步 `np.savez(ckpt, q,m,v,it,best)` |
| resume 等价测试 | **未执行** | 时间预算内未做"重载 vs 不中断"逐位比较 → `PARTIAL` |
| 正式目标的梯度测试 | **未执行** | 仍是审计发现 P0-A 的同一缺陷；023 未补 |
| per-view K | 改进 | 023 的损失全部用 W0 `camera_result.npz` 的 `K`，不再有模块级硬编码 |
| 匹配计数 | 修复 | 023 不再使用 `len(ka) and len(kb)` |

## 4. P3：历史算法真的跑起来了

用**未修改的历史** `features019.features/landmarks`（`replay_019_020/code/`，仅把 `common.py` 的 REPO 指向本仓库）：

| 视频 | 视角 | 特征/视角 | ≥3 视角轨迹 | **合格三维地标** | 耗时 |
|---|---:|---:|---:|---:|---:|
| 004 | 6 | 1330–1516 | 911 | **738** | 23.7 s |
| 005 | 16 | 1058–1372 | 1644 | **1213** | 60.6 s |

跨视频身份用历史 `features019.match_desc`（ratio 0.72 + mutual）匹配两侧地标描述子：**24 个身份**。

## 5. P3/P4：完整目标 `L_Ring + 0.2·L_SIFT3D + 0.02·L_EPI + 0.01·L_Prior`

种子：1-DoF yaw 求解器给出 45.62°（`AMBIGUOUS_MULTIMODAL`），`H = exp(q·s) @ Rz(45.6°)`。

| 项 | FIT 初始 | FIT 最终 | HOLDOUT 最终 |
|---|---:|---:|---:|
| L_Ring | 0.092 | 0.094 | — |
| L_SIFT3D（前向/反向） | 31.58 / 17.85 | 25.34 / 12.18 | 26.33 / 13.42 |
| L_EPI（24 对） | 10.45 | 9.64 | — |
| L_Prior | 0 | 0.38 | 0.38 |
| **Total** | 5.244 | **4.042** | **3.978** |
| 观测数 | 121/50 | 121/50 | 113/55 |
| 修正量 | — | **0.589 mm / 5.73°** | — |

**关键判读**：Huber 值 18.8 对应平均残差 **≈56 px**（Huber 线性区 `hub(x)≈x−0.5`，`x=d/3`）。
即 **24 个跨视频身份绝大多数是错的**，`L_SIFT3D` 把优化拉向错误方向（EPI 从 4.6 px 中位恶化到 ~29 px 均值）。
因此：`L_SIFT3D` 有真实观测、但身份不可信 → **`LANDMARK_BLOCKED`**，不能用于几何验收。

## 6. P5：跨组

G01/G05 仍为 `0 ACCEPT`，保持 `BLOCKED_BY_W0_ADMISSION`；未使用历史相机、未改门限。

## 7. 回答

1. **是否真正恢复完整历史算法？** **部分**：`features019`（SIFT+轨迹+三角化）真实运行并产出 738/1213 地标；
   `features020` 的跨视频身份未端到端接入（用其同源的 `match_desc` 代替）；`ring020` 的 M/I/C/O 仍未接入（Ring 项仍是 `torus_contours`）；`objective020/optimize020` 的数学被重述而非调用。
2. **受控实验是否正确？** **未完成**：A2/A3/A6 的修复与正对照未执行（022 已证明其无效），本轮 `CONTROLLED_GT_RESULTS.md` 记录为 `NOT_DONE`。
3. **G03 三维几何是否改善？** **否**：跨视频身份残差 ~56 px，修正后 EPI 反而恶化；不得宣称改善。
4. **3–15 px 系统误差与 >50 px 长尾来自哪里？** 系统项：相机/H 与匹配噪声**共同**贡献（样本外 F_pose 4.17–4.79 px 优于自由 F 的空间外推 17.8 px，但随机划分下自由 F 更好 2.89 px）；
   长尾：匹配错误（22R 已证 mutual 仅 46–68%）与少量错误身份。**不能**再归因为单一"相机几何"。
5. **相机是否可进入 HERO/Body？** **否**（`CROSS_VIDEO_GEOMETRY_ACCEPT=NO`）。
6. **剩余阻断**：① 跨视频身份可靠性（需要 3D 一致性 RANSAC / 更严的多视角交叉验证）；② `features020`/`ring020` 未端到端接入；③ 受控 GT 与 resume/梯度测试未做；④ 地标三角化用了全部视角（部分泄漏）。

## 8. 复现

```bash
N=experiments/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY $N/tools/forensic_epipolar_fixed.py
$PY $N/tests/test_epipolar_drawing.py
$PY $N/tools/p1_independent_holdout.py
$PY $N/core/p3_landmarks.py --video 004
$PY $N/core/p3_landmarks.py --video 005
$PY $N/core/p3_objective.py
```
