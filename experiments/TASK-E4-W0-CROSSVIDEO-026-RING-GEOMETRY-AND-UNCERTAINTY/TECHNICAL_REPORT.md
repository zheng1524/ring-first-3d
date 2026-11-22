# TASK-E4-W0-CROSSVIDEO-026 — TECHNICAL_REPORT

```
RING_GEOMETRY_VALIDATED:            PASS（历史 020 RingRenderer 实跑，22 视角）
RING_POSE_IDENTIFIABILITY:          PASS（yaw 盲区已量化）
TRIANGULATION_UNCERTAINTY_CHARACTERIZED: PASS
JOINT_OPTIMIZATION_EXECUTED:        NO（Gate C = NO_RING_COMPATIBLE_RIGID_ALIGNMENT）
CROSS_VIDEO_GEOMETRY_ACCEPT:        NO
BODY_CROSS_VIDEO_ADMISSION:         NO
G01/G05:                            BLOCKED_BY_W0_ADMISSION（未改门限）
```

## 1. 历史 Inner/Outer 真的被复用并跑通

固定提交 `5636aae` 的 020 **确实运行过**（gate.log 有 `RING020_GATE ... {'I':..,'O':..,'C':..}` 与 `metrics/RING_*` 产物）。
本轮把 `ring020.py` 复制为 `ring020_026.py`，**只改两行路径**（CAD、NORMALIZATION → 环境变量），
在 22 个当前 G03 ACCEPT 视角上端到端运行：

| E_M | E_I | E_C | E_O | E_Ring |
|---:|---:|---:|---:|---:|
| 0.093 | **0.099** | 1.834 | **0.257** | **0.242** |

CAD 使用 G03 专用 `RING.npz`（R=5.6,r=0.6），NORMALIZATION 使用真实 G03 文件（非悬空链接），
I/O 观测由 011 `DXY_OBSERVATIONS` 适配，可见弧由历史 `segments()` 的 CAD 自遮挡决定。

## 2. Ring 可辨识性

| 扰动 | E_Ring |
|---|---:|
| 0° yaw | 0.260 |
| 1° yaw | 0.560 |
| 5° yaw | 3.711 |
| 15° yaw | 9.231 |
| 45° yaw | 54.205 |

→ **yaw 在 1° 内几乎不可辨识**；Ring 不能确定绕法向的绝对 yaw；
对 0.5° 级相对相机误差亦不敏感。H025 被 Ring 严格拒绝（**178.7**）。

## 3. 三角化敏感性（本轮核心）

| 扰动类型 | 3D 位移 p50 | 点间距离变化 |
|---|---:|---:|
| 共同刚体旋转 1°（负对照） | 0.35 mm | **7e-7 mm** |
| 共同平移 0.5 mm | 0.46 mm | 4.5e-7 mm |
| **单个/独立相机 0.5°** | **13.8 / 28.3 mm** | **3.4 / 19.3 mm** |
| 独立相机 1° | 14.2 / 37.2 mm | 4.1 mm |

观测到的跨视频距离差：中位 **3.90 mm**、p90 6.69、max 9.79 —— **完全落在相对相机误差可解释的范围内**。

## 4. 联合优化

**未执行。** 025 的 H 被完整 Ring 判为 178.7（灾难性），且 4/12 内点、seed 间差 15.8 mm/31°。
状态：`NO_RING_COMPATIBLE_RIGID_ALIGNMENT`。未放宽门限、未改 CAD、未删身份。

## 5. HOLDOUT 全量（修正 025 的"6.08 px"）

132 次机会：52 匹配（28 <10 px、24 ≥10 px）、80 无匹配。
**全部匹配** 中位 **7.91**、p90 **83.74**、p95 85.53、max 89.70 px；
004→005 中位 32.67、005→004 中位 6.96。025 的 6.08 px 只是低误差子集。

## 6. 十个科学问题

**Q1** 历史 I/O 运行过（gate.log 有 I/O/C 数值）；本轮复用 `RingRenderer`（仅两行路径改动），**未新建算法**。
**Q2** 增强：对倾斜/平移（5° → 3.7；亚毫米 → 见 CSV）更敏感；**未增强**：<1° yaw 与 0.5° 级相对相机误差。
**Q3** **是**：1° yaw 时 Ring 0.26→0.56（很小），而三角化位移 0.35 mm（共同）/10–14 mm（相对）。
**Q4** 004 与 005 都敏感；005 的相对扰动更剧烈（28 mm vs 14 mm），但 004 只有 3 个 FIT 视角，几何更弱。
**Q5** 3.90 mm 中位差 **全部可被** 0.5° 级相对相机误差解释（3.4–19 mm）；无超出证据。
**Q6** 完整 I/O 让候选 H 的判定从"1.04→6.84 px"变为 **0.242→178.7**，判别力显著增强。
**Q7** **否**：不存在同时符合 Ring 与背景观测的稳定 H（025 假设被否决）。
**Q8** 联合优化未执行，因此**没有**改善或恶化 HOLDOUT 的证据。
**Q9** **是**：证据指向单视频内部相机相对位姿是主要误差源，下一步应做单视频 BA，而非继续调 H。
**Q10** **是**：单一入口（025 的 `run_cross_video_registration.py` 结构），G01/G05 同一路由返回 `BLOCKED_BY_W0_ADMISSION`。

## 7. 复现

```bash
N=experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$N/core:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $N/core/p1_ring_io.py
PYTHONPATH=$N/core:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $N/core/p2_sensitivity.py
PYTHONPATH=$N/core:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $N/core/p2_relative.py
PYTHONPATH=$N/core:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $N/core/p4_figures.py
```
