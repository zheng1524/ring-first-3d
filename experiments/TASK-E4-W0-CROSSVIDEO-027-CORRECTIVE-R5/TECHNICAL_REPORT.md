# TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5 — TECHNICAL_REPORT

```
Gate A 工程修复:        PASS（5/5 测试：精确扰动幅度、锚点不动、M3b 42 参数、M4 54 参数、E 组真三角化）
Gate B 坐标与 H 初始化: PASS（Ring-only 候选 + 极线筛选，见下）
Gate C 正确 H 下 X-only: PASS（C0/C1/C3 全部恢复到 0.000 mm）
Gate D 新旧流程对照:    PARTIAL（H 初始化→三角化已比较；PIPELINES 运行脚本有 bug → INVALID/NOT_EXECUTED）
Gate E 相机扰动:        PARTIAL（B 组 M2/M3b/M4 部分完成，B_CAMERA.csv 未写出）
STATUS: H_INITIALIZATION_VALIDATED（初始化部分）
        PROGRESSIVE_BA: PARTIAL（流程对照未有效执行）
```

## 1. R4 缺陷修复（先失败→后通过）

| 缺陷 | 修复前 | 修复后测试 |
|---|---|---|
| 平移扰动被归一化成 1 mm | `w[:3] *= 1/‖w[:3]‖` | `test_magnitudes_exact`：0.25/0.5 mm 精确到 1e-6 |
| 旋转幅度随机 | 高斯三向量合成角未知 | 同上：0.25°/0.5° 精确到 1e-6（scipy rotvec 度量） |
| 锚点可能被扰动 | 无保护 | `test_anchor_and_005_untouched`：锚点与 005 恒不动 |
| E1/E2 未施加扰动 | `run_group` 未调用扰动 | `test_E_group_perturbation_changes_geometry`：重三角化与基线差 >1e-3 mm |
| M3 不是联合 | H-only → X-only | `test_M3b_joint_has_H_and_X`：参数 6+36=42，H 在第二阶段真实移动 |
| M4 参数偏移错 | `12+6nr` | `test_M4_parameter_layout`：54 参数、X 从索引 18 开始、末态 X 长度正确 |
| 可视化空图 | group 字段不匹配 | 本轮图表全部由 CSV 生成并检查行数 |

## 2. H 初始化（核心新证据）

Ring-only 候选（24 个 yaw，各做 6 自由度 Ring 局部精化）：

| 候选 | Ring 能量 | 中位 Sampson（FIT 8 身份） | H 旋转误差 |
|---|---:|---:|---:|
| **yaw=120°（最终选中）** | 0.0056 | **0.093 px** | **0.512°** |
| yaw=135° | 0.0031 | 0.871 px | 3.86° |
| yaw=30° | 0.0037 | 1.104 px | 4.77° |
| yaw=60° | 0.0171 | 1.658 px | 5.39° |
| … | … | 最高 7.3 px | 最高 29.7° |

- **Ring 能量在 yaw 上近似平坦**（0.003–0.03，无唯一极小）→ 复现 Ring 的旋转对称性；
- **极线误差对 yaw 敏感**（0.09–7.3 px）→ RGB 二维对应可选出正确 yaw。

## 3. H 初始化 → 共同三角化（同一批二维观测，相机全固定）

| H 初值 | H 旋转误差 | T1 三角化误差（中位） | T2 仅 X 精化 |
|---|---:|---:|---:|
| **H0 = I（旧路线）** | 12.03° | **1.800 mm** | 1.676 mm |
| **H1 Ring-only** | 3.86° | **0.928 mm** | 0.925 mm |
| **H2 Ring + RGB（新路线）** | **0.512°** | **0.156 mm** | 0.156 mm |
| H3 GT（仅正对照） | 0° | 0.000 mm | 0.000 mm |

⇒ **Ring+RGB 初始化把共同三角化误差从 1.80 mm 降到 0.156 mm（约 11.5×）**，H 误差从 12.03° 降到 0.51°。

## 4. 正确 H 下的三维点恢复（C 组，全部相机固定，仅优化 X）

| 组 | 初始地标误差 | 终值 | success |
|---|---:|---:|---|
| C0 无扰动 | 0.0 | 0.000 | True |
| C1 1 mm 随机 | 1.0 | **0.000** | True |
| **C3 3 mm 随机** | 3.0 | **0.000** | **True** |
| C3-depth 3 mm 沿深度 | 3.0 | 0.077 | False |
| C3-perp 3 mm 垂直 | 3.0 | **0.000** | True |
| **C3-W 错误 H（I）+ 3 mm** | 3.0 | **1.679** | False |
| **C3-H2 用 H2 + 3 mm** | 3.0 | **0.146** | False |

⇒ **Q5：正确 H 下 3 mm 随机/垂直误差可完全恢复；深度方向 3 mm 最难（0.077，未收敛）。
Q6：R4 的 C 组"失败"主因是 H 初始化错误（C3-W 1.68 mm），不是三维点本身。**

## 5. 相机扰动（B 组，部分完成）

| 扰动 | M2（仅 H） | M3b（H+联合） | M4（+2 台 004） |
|---|---:|---:|---:|
| 0.25° | 0.113° | 0.146° | 0.262° |
| 0.50° | 0.227° | 0.323° | —（未跑完） |

注意：这些 H 误差较小，是因为 R5 的 X0 仍是**未扰动 005 相机的精确参考结构**（见 §7），
H 可以吸收大部分共同扰动。**不能据此说"相机误差可被完全修复"**；B_CAMERA.csv 未写出，M4 只完成 1 例。

## 6. 十个问题

1. **W0 是否已同坐标？H 是什么？** 合成场景中 005 相机定义世界；004 通过 `H` 放入该世界（`T004_world = H·T004_W0`）。H 是**两段视频之间的残余刚体变换**，不是 Ring 坐标的重复应用。真实 W0 的同一性仍需在真实数据上核对（本轮只在合成场景验证公式）。
2. **Ring-only 能否缩小 H 范围？** 能缩小到 3.86°，但 **yaw 不可辨识**（Ring 能量平坦），并给出多个等价候选。
3. **二维 RGB 能否改善 H？** 能：极线中位误差 0.09 px 的候选对应 H 0.51°，把 yaw 从 Ring 盲区中选出。
4. **是否降低共同三角化误差？** 是：1.80 → 0.156 mm。
5. **正确 H 下 3 mm 能否恢复？** 随机/垂直能（0.000），深度方向不能完全（0.077）。
6. **R4 的 C 组失败主因？** 错误 H（C3-W 1.68 mm vs C3 0.000）。
7. **新路线是否更优？** 在**初始化→三角化**环节明确更优（0.51°/0.156 mm vs 12°/1.80 mm）；端到端新旧流程对照 **未有效执行**（PIPELINES 脚本 bug），不能宣称完整流程更优。
8. **局部相机误差能否被 H+X 消除？** 只能部分：0.25–0.5° 的 2 台 004 独立扰动下 H 仍残 0.11–0.32°，M4 未完成足够对照。
9. **何时必须释放局部相机？** 当相机误差不是共同变换（独立扰动）时；共同变换可由 H 吸收。
10. **是否具备真实 G03 共同三角化条件？** **尚不具备**：需要真实数据上验证 Ring-only 候选与极线筛选；本轮仅在合成场景证明方法有效。

## 7. 明确未完成 / 无效

- **PIPELINES.csv INVALID**：运行脚本把 M2/M3 的 H 都写成了最终指标，且 M3b 的 X 未更新 → 新旧端到端流程对照 **NOT_EXECUTED**；
- B_CAMERA.csv 未写出（进程在 B0.5/M4 前结束）→ B 组 **PARTIAL**；
- E1/E2 组本轮未跑（时间预算）；
- HOLDOUT 身份级评价未做（只有 FIT 8 身份用于 H 候选筛选）；
- 地标先验：X0 为未扰动 005 三角化（近 GT）→ 这是**正对照先验**，已记录，不能代表真实数据条件。

## 8. 复现

```bash
R5=experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$R5/core:$R5/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY -m unittest discover -s $R5/tests -v
PYTHONPATH=$R5/core:$R5/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R5/core/r5_experiments.py
PYTHONPATH=$R5/core:$R5/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R5/core/figs_r5.py
```
