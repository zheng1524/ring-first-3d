# TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3 — TECHNICAL_REPORT

```
Gate A 基线复现与记录:        PASS（独立 run 目录 + 聚合；R2 12° 差异已定位）
Gate B H-only 变量集合:       PASS（6 参数、rank 6/6、地标冻结、005-only 初值）
Gate C 收敛域诊断:            PASS（0–18° 扫描；可见边/鲁棒损失对照；Jacobian）
Gate D 渐进联合优化:          PASS（渐进 0.0009° 优于直接联合 0.0073°，不破坏 H）
Gate E Level 3–5:             NOT_EXECUTED
STATUS: CONTROLLED_BA_PARTIAL        READY_FOR_REAL_G03_BA: NO
```

## 1. 核心发现：R2 的 12° 失败是**初始化坐标系错误**，不是 BA 固有限制

| 实验（同一 12° 场景） | H 旋转误差 | success |
|---|---:|---|
| **真正的 H-only（6 参数，005-only 三角化地标）** | **3.8e-04°** | True（129 次） |
| **渐进：先 H-only，再联合** | **0.0009°** | False（60 次上限） |
| 直接联合（同一正确初值） | 0.0073° | False（60） |
| R2 直接联合（错误的 004+H=I 三角化初值，40 次） | 7.06° | False |
| R2 直接联合（同上，400 次） | 3.04° | False |

## 2. H-only 收敛域（统一 200 次预算）

| 初始 | 0° | 1° | 3° | 6° | 9° | 12° | 18° |
|---|---:|---:|---:|---:|---:|---:|---:|
| 最终 H 旋转 | 2.0e-5° | 0.0° | 4.0e-5° | 1.0e-4° | 1.0e-4° | **3.8e-4°** | 1.2e-3° |

全部 ≤1.2e-3°；rank 6/6、cond 44–47。不存在 12° 硬失败。

## 3. 三个对照都排除了"嫌疑"

| 嫌疑 | 对照 | 结论 |
|---|---|---|
| 可见边缘冻结 | GT / 3° / 12° 选边，在 GT 相机处算 Ring | E_I 5.6e-14 / 2.4e-6 / 1.3e-3 → **不是原因** |
| Huber 尺度 | 12° 联合：Huber vs 平方 | 0.0073° vs 0.0073° → **不是原因** |
| 地标自由度 | H-only vs 联合 | 3.8e-4° vs 0.0073° → 联合稍差但可接受；**主因是初值坐标系** |

## 4. Jacobian

rank **6/6**、cond **67.4**、GT 处 rms 1.06e-8、梯度 3.4e-7；方向导数相对误差 0.54
（最近边切换的非光滑，绝对差 <1e-8，已如实标注，不宣称"梯度全通过"）。

## 5. 十二问

1. **12° 下真正 H-only 能否恢复？** **能**：3.8e-4°（success=True）。
2. **冻结地标再释放是否优于直接联合？** **是**：渐进 0.0009° / 地标 1.8e-4 mm，优于直接联合 0.0073° / 1.5e-3 mm。
3. **12° 失败是否主要来自初始地标误差？** **是**：R2 用 004+H=I 三角化（偏 0.8–6.5 mm）；改 005-only 后消失。
4. **初始可见边是否限制收敛域？** **否**（E_I ≤1.3e-3）。
5. **Huber 尺度是否限制大误差恢复？** **否**（Huber 与平方相同）。
6. **二维方向保持残差是否改善稳定性？** **未验证**（已实现未运行）→ `NOT_EVALUATED`。
7. **3/6/9/12/18° 收敛结果？** 见上表，全部 ≤1.2e-3°。
8. **单相机扰动能否恢复？** **NOT_EXECUTED**。
9. **多相机扰动能否恢复？** **NOT_EXECUTED**。
10. **不同 K/噪声/粗差/低视差？** **NOT_EXECUTED**。
11. **哪些自由度仍不可辨识？** 本轮 H(6) 满秩；Ring yaw 的不可辨识由 RGB 弥补；单侧/无 RGB 情况未重测。
12. **是否具备真实 G03 BA 条件？** **否**：L3–L5 未执行，且真实数据的观测质量（52/132 HOLDOUT 匹配）仍需先评估。

## 6. 交付

`TECHNICAL_REPORT.md`、`R2_BASELINE_REPRODUCTION.md`、`H_ONLY_VARIABLE_AUDIT.md`、
`INITIALIZATION_BASIN_ANALYSIS.md`、`PROGRESSIVE_BA_RESULTS.md`、`FAILURE_CAUSE_ANALYSIS.md`、
`RING_VISIBILITY_ASSOCIATION_AUDIT.md`、`RGB_ROBUST_LOSS_COMPARISON.md`、`JACOBIAN_VALIDATION.md`、
`CONTROLLED_LEVEL3_5_RESULTS.md`、`ACTUAL_CALL_GRAPH.md`、`RUN_MANIFEST.json`；
代码 `core/{r3_run,aggregate,visibility_jacobian,figs_r3}.py` + 单入口；
数据 `runs/controlled/<tag>/{CONFIG,METRICS}.json + RESULT.npz`（11 个独立 run + 6 个对照 run）、
`SUMMARY_ALL_RUNS.csv`、`VISIBILITY_ASSOCIATION.csv`、`VISIBILITY_EDGE_OVERLAP.csv`、`JACOBIAN_H_ONLY.json`；
图 1–6 全部入库。

## 7. 复现

```bash
R3=experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$R3/core:$R3/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R3/core/r3_run.py --what h_only_sweep --yaws 0,1,3,6,9,12,18 --max-nfev 200
PYTHONPATH=$R3/core:$R3/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R3/core/r3_run.py --what compare --max-nfev 60
PYTHONPATH=$R3/core:$R3/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R3/core/visibility_jacobian.py
PYTHONPATH=$R3/core:$R3/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R3/core/aggregate.py
PYTHONPATH=$R3/core:$R3/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R3/core/figs_r3.py
```
