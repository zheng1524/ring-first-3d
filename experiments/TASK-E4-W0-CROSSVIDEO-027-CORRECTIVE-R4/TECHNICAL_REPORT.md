# TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4 — TECHNICAL_REPORT

```
Gate A 执行错误修复:   PASS（D1–D5 修复，4/4 测试；D6=M4 未执行）
Gate B 受控输入正确:   PASS（同一场景/观测；E1/E2 真重三角化；身份映射）
Gate C 数学正确:       PASS（能量恒等 <1e-9；Ring I/C/O 计数>0；GT 隔离）
Gate D 受控优化:       PARTIAL（M0–M3 完成；M4 NOT_EXECUTED）
Gate E 结果审计:       PARTIAL（单个种子；幅度网格未补全）
STATUS: CONTROLLED_BA_PARTIAL
```

## 1. 修好了什么（有先失败后通过的测试）

| 缺陷 | 证据 |
|---|---|
| D1 联合优化忽略 `rgb_mode` | 大残差 Huber≠平方（>1e-3），小残差相对差 <1e-6 |
| D2 只取第一个 RGB 残差 | `E_terms == 0.5‖r‖²` 全部 21 个 run 误差 **0.0** |
| D3 Ring 计数错 | I/C/O 计数与实际残差数组一致且 >0 |
| D4 扫描改的是 GT 而非初始化 | R4 固定 GT（12.03°），只改 `H_init`/相机/地标 |
| D5 预算不可比 | M2=200、M1/M3=60，逐 run 记录 `nfev` |
| D6 M4 索引 bug | 已修，但 **M4 未重跑 → NOT_EXECUTED**（如实记录） |

## 2. 核心结果（固定场景 H 真值 12.03°，预算见上）

| 组 | 初始扰动 | H 终值 | 地标终值 | Ring(I+C+O) | success |
|---|---|---:|---:|---:|---|
| A 基线 | 无 | **0.0004–0.0006°** | 0.0000–0.0001 mm | 0.0019 | M2=True |
| A（M1 仅地标） | 无 | 12.03°（不动） | 1.67 mm | 0.269 | False |
| **B 相机 0.25°** | 2 台 004 | **1.02°**（M2）/0.94°（M3） | 0.00 / 0.21 | 1.95 | M2=True |
| **B 相机 0.50°** | 2 台 004 | **1.00°**（M2）/0.53°（M3） | 0.00 / 0.09 | 1.95 | M2=True |
| **C 地标 3 mm** | 仅结构 | **7.90°**（M3） | 2.07 | 3.51 | False |
| **D 两者** | 相机 0.5°+3 mm | **6.88°**（M3） | 1.82 | 3.12 | False |
| **E1 仅 005 重三角化** | 005 相机 0.5° | **0.0007°**（M3） | 0.00 | 0.0019 | False |
| **E2 两段重三角化** | 全相机 0.5° | **11.81°**（M3） | 1.58 | 0.920 | False |

## 3. 十个问题

**Q1 相机正确时 1–3 mm 地标初值是否易纠正？** 3 mm 时 M3 只降到 **2.07 mm**，且把 H 带偏到 7.9° → **不易纠正**。
**Q2 0.5° 相机相对误差影响多大？** 冻结相机时 H 只能到 **0.5–1.0°**（残余 1–2 倍于扰动），RGB 中位 0.85→0.45 px。
**Q3 同时扰动是否更难？** 是：D 6.88°、E2 11.81°，均未恢复。
**Q4 重三角化误差 vs 直接扰动结构？** E1 的误差是**坐标系整体漂移**（相对 005 内部距离不变，0.0 mm），
C 的 3 mm 是**结构形变**；E2 是两者混合（1.80 mm）。E1 的"H 完美"是吸收伪影。
**Q5 仅优化地标能否补偿相机误差？** 不能：M1 下 H 仍 12.03°，地标反被拉坏 1.4–1.7 mm。
**Q6 何时需要释放 H？** 只要 004/005 之间存在相对位姿偏差（B/D/E2），必须优化 H。
**Q7 何时必须释放单相机？** 当相机相对误差存在且 H 无法吸收时（B 组 H 卡在 ~1°）→ 必须 M4；本轮 M4 NOT_EXECUTED。
**Q8 005 误差如何影响 005-only 三角化与 H？** 005 相机 0.5° → 结构整体漂移（相对 005 距离不变），
H 吸收后 7e-4° 但**几何错误**；005 与 004 同时偏（E2）则 H 几乎不恢复。
**Q9 渐进 vs 直接联合在公平预算下？** **无法判定**：本轮 M3 的 H 阶段只有 30 次，M2 有 200 次，预算不同；
未宣称渐进更优。
**Q10 Ring+RGB 是否足以区分相机误差与地标误差？** 部分：Ring 在 B 组从 0.269 升到 1.95、C 组到 3.5，
说明 Ring 能感知"结构/位姿不一致"，但**无法单独归因**到相机或地标（两者都会抬高 Ring）。

**最终判断：`CONDITION_DEPENDENT`** —— 相机相对误差不能被 H/地标吸收（B：H 卡在 ~1°，E2：11.8°）；
地标误差在 H 阶段被冻结时会污染 H（C：7.9°）；两者叠加最差（D：6.9°）；
E1 说明"低 H 误差 ≠ 正确几何"。

## 4. 可视化（6 张，全部由实际数据生成）

`01_initial_geometry_A_to_E.png`、`02_triangulation_error_vectors.png`、
`03_camera_vs_landmark_sensitivity.png`、`04_M0_to_M4_comparison.png`、
`05_ring_rgb_geometry_conflict.png`、`06_error_source_summary.png`。

## 5. 明确未完成

- **M4**（释放 2 台 004 相机）NOT_EXECUTED（索引 bug 修复后未重跑）；
- 单个种子（未跑 5 seeds）；幅度网格未补全（C 只有 3 mm、D 只有 0.5°+3 mm）；
- 方向保持残差 `dir2d` 未用于结论；
- 视差角/质量门存活率未逐地标输出。

## 6. 复现

```bash
R4=experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$R4/core:$R4/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY -m unittest discover -s $R4/tests -v
PYTHONPATH=$R4/core:$R4/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R4/core/r4_run.py --what baseline
PYTHONPATH=$R4/core:$R4/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R4/core/r4_run.py --what leftover
PYTHONPATH=$R4/core:$R4/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R4/core/figs_r4.py
```
