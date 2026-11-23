# TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6 — TECHNICAL_REPORT

```
ENGINEERING_CORRECTNESS:        PASS（7/7 测试：Ring 向量、候选姿态、H 一次、阶段分离、参考相机、HOLDOUT 隔离、M4）
H_INITIALIZATION_VALIDITY:      PARTIAL（H2 = 2.985°，优于 H=I 的 12.03°，但 R5 的 0.51° 已撤回）
END_TO_END_COMPARISON:          PASS（两条流程均收敛；新路线 25 nfev vs 旧 75 nfev）
HOLDOUT_VALIDATION:             PARTIAL（无退化，但场景太易，无判别力）
CAMERA_PERTURBATION_ROBUSTNESS: PARTIAL（E1 完成；F1/F2/F3、E2 未执行）
REAL_G03_READINESS:             FAIL（未验证真实数据条件）
```

## 1. 修复的 R5 错误（有测试）

| 缺陷 | 修复 | 关键数字 |
|---|---|---|
| Ring 候选用**标量能量**优化 | 改用正式 I/C/O 残差向量 | 向量能量与 BA 块能量相对差 **<1e-12** |
| 候选"最终姿态"未记录 | 保存 `H_initial/H/refine_rot/refine_trans` | 精化转动 **6.7°–156°**；初始 yaw≠最终 yaw |
| **H 重复应用** | `make_problem` 只收 W0 相机，H 仅在 BA 内 | `C==H@T0`（<1e-12），`≠H@H@T0` |
| PIPELINES 记录错 | 分阶段保存 | 旧 75 nfev / 新 25 nfev，H/X 分别记录 |
| 极线读 GT 005 | 改用传入参考相机 | 扰动下能量差 >1e-6 |

## 2. H 初始化（修复后，与 R5 不同）

| 候选 | initial yaw | Ring | Sampson | H 误差 |
|---|---:|---:|---:|---:|
| 最优综合 | 165° | 0.00066 | **0.530 px** | **2.985°** |
| Ring 最优 | 15° | 0.00037 | 0.648 | 3.678° |
| 原 R5 的 120° | 120° | 0.00037 | 0.648 | 3.680° |

- Ring 能量在不同初始 yaw 下 0.00033–0.00066、**无唯一极小**；yaw 45/60/90° 精化到**同一个 H**（4.181°）→ yaw 等价类实测复现。
- **R5 的 H2=0.51° 无法复现**（其标量目标 + 重复 H 流程所致），已撤回；R6 的 H2 为 **2.985°**。

## 3. 共同三角化

| H | H 误差 | 三角化误差 |
|---|---:|---:|
| H0=I | 12.027° | **1.800 mm** |
| H1=Ring-only | 9.746° | 1.886 mm |
| **H2=Ring+RGB** | **2.985°** | **0.698 mm** |
| H3=GT | 0 | 0.000 mm |

## 4. 端到端新旧流程（同一场景/观测/残差）

| 流程 | 起点 | H 终值 | 地标终值 | nfev |
|---|---|---:|---:|---:|
| 旧：005-only → H-only → M3b | 12.03° | 0.00032° | **0.00013 mm** | 75 |
| 新：H2 → 共同三角化 → M3b | 2.985° | 0.00106° | 0.00051 mm | **25** |

**结论：精度无差异（都到机器精度），新路线省 2/3 局部迭代。** 在理想合成场景中不支持"更准"。

## 5. HOLDOUT 与参考相机

- HOLDOUT（4/12 身份，rng 2026）：两条流程 FIT/HOLDOUT RGB 均 ~0 px → **无判别力**，只能报告"无退化"。
- E1（005 相机扰动）：005-only X 误差 0.157/0.280/**4.303** mm（0.25°/0.5°/0.25 mm），
  H2 共同三角化 **0.81/0.78/0.90 mm**；H2 的 H 误差恒为 **3.68°**（落入 yaw 15° 的 basin，未恢复 GT 附近）。
  ⇒ 新路线在参考相机误差下**仍优于 005-only（0.25 mm 时 4.30→0.90 mm）**，但 H 精度下降、不再接近真值。

## 6. 十一个问题的答案

**Q1** 是，R5 的 Ring-only 6-DoF 用标量能量；修复后候选精化 6.7°–156°，H2 从 0.51° 变为 **2.985°**。
**Q2** 120° 起点的候选最终 H 误差 **3.680°**（精化转动 111.68°）；Ring 不能确定 yaw（45/60/90° 收敛到同一 H），只能弱约束倾斜/平移。
**Q3** 是，旧路线修复后 H 终值 **0.00032°**（12° 起点）。
**Q4** 精度上**否**；成本上**是**（75→25 nfev）。
**Q5** 优势仅限于"跳过一次从 I 出发的 H-only 阶段"，最终几何两者相同。
**Q6** HOLDOUT 无退化但也无优势（场景太易）。
**Q7** **不可靠**：0.25°/0.5°/0.25 mm 参考扰动下 H2 停在 3.68°，共同三角化 0.78–0.90 mm（理想时 0.70）。
**Q8** 仍优于 005-only（0.25 mm 平移：4.30→0.90 mm），但优势缩小。
**Q9** 共同变换可由 H 吸收；独立相机误差需要释放单相机（M4 工程已验证，科学对照未执行）。
**Q10** 合成遵循 c2w + Ring 公制；真实 W0 的同帧率、时间同步、Mask 质量、真实匹配率（HOLDOUT 52/132）**均未验证**。
**Q11** **不建议**进入真实 G03 共同三角化：需先在真实数据上验证 Ring 候选、极线筛选与参考相机误差。

## 7. 明确未执行/无效

- E2（004+005 同时扰动）、F1/F2/F3（局部释放）、E1 的 M4 修复：**NOT_EXECUTED**；
- R5 的 0.51°/0.156 mm **撤回**（错误标量目标 + 重复 H）；
- `HOLDOUT` 判别力不足，不能作为优势证据；
- 仍存在 **yaw 等价类**（45/60/90° 同解 + 12° vs 165° 起点差别大），需要专门研究。

## 8. 复现

```bash
R6=experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$R6/core:$R6/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY -m unittest discover -s $R6/tests -v
PYTHONPATH=$R6/core:$R6/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R6/core/r6_experiments.py
PYTHONPATH=$R6/core:$R6/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R6/core/figs_r6.py
```
