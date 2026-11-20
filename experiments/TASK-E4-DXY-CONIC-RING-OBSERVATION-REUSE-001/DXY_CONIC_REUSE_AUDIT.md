# DXY_CONIC_REUSE_AUDIT

**Task:** TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001
**目的：** 在实现前回答"历史 Conics/CAD 轮廓代码是否还在、能否复用、旧方法为何没有稳定收益"。
**范围：** 本地历史工作区、当前仓库 lineage、外部开源实现。**只读审计。**

---

## 1. 本地历史检索结果

### 1.1 命令与范围

```bash
grep -rln "conic|Conic|quadric|Quadric" --include=*.py <旧工作区>/ring_anchor_3d/experiments
grep -rln "mature_geometric|conic" --include=*.py <ws>/src
find /home/liu -maxdepth 4 -type d -name "*mature_geometric*"
```

### 1.2 找到的历史实现（真实存在，非报告转述）

| 路径 | 作用 | 是否可复用 |
|---|---|---|
| `src/ring_first_3d/mainline/lineage/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/mature_geometric_pose_refinement/code/conics_init.py` | 由二维椭圆生成三维位姿候选；`ellipse_matrix()` 构造齐次 Conic；调用 vendor `estimate_pose(Q, r, 0.)`；枚举法向符号并贴合 gauge | **部分可复用**：`ellipse_matrix` 公式与本次实现一致；`estimate_pose` 不用于最终解 |
| `.../mature_geometric_pose_refinement/code/cad_render.py` | "M3T-inspired render-boundary + CAD association"（文件头自述） | 依赖 `ring020` 与 `open3d`，**当前环境不可直接 import** |
| `.../code/refine.py` | 冻结材质点局部求解 + CAD 目标接受 | 同上，依赖 `base_geometric`/`cad_render` |
| `.../code/stage1.py` | 组合 `conics_init` + `refine` 的分阶段入口 | 同上 |
| `/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/mature_geometric_pose_refinement/vendor/conics/conics/_conic.py` | 第三方 conic→pose 实现，含 `estimate_pose` | 已定位、可按 AST 抽取；**本次未采用**（见 §4） |
| `.../TASK-E4-A1-ELLIPSE-VS-FULLMASK-001` | 椭圆 vs 完整 Mask 的早期对照 | 只读参考 |

**结论：** 历史 Conics + CAD 轮廓代码**没有丢失**，`mature_geometric_pose_refinement` 目录完整保留在 lineage 中。但它是"候选初始化 + 局部求解"的组合，并非"轮廓级残差"模块。

### 1.3 旧方法的失败证据（源码内可读）

`conics_init.py` 自身写明：

```python
Ring_yaw_from='gauge only; RGB still required'
```

即：单视图 Conic 只能给出**中心与法向**，绕环轴的 yaw 无法由椭圆确定，必须依赖 RGB/gauge。这与本轮 005 基线在 G03/005 上遇到的"Ring 通过但 RGB 不一致"是同一类问题的两个侧面。

历史结论（V6/021 冻结产物）：005 与 004 的跨视频对齐 `accepted=false`（held MAE 9.17 / 41.9 px），说明"Conics + 对齐"路线没有得到稳定收益；V6 之后改用 Ring-First + RGB PnP + 局部 SfM/BA。

**因此本轮不重复"用 Conic 直接解位姿"的路线，只把它当作二维观测来源与残差项。**

---

## 2. DXY 侧可复用性（本轮核心）

用 `/usr/bin/python3`（唯一同时具备 `skimage`/`cv2` 的解释器）实测：

```python
from dxy_mid._engine import ring_component as RC
base, payload = RC.recover(labels, bgr_image, 10.0)
```

- 80/80 冻结 FIT 视角**全部返回 `valid=True`**，`branch` 均为 `visible_inner_arc_RANSAC`（直接可见内弧，非对称推断）。
- 返回 `inner / outer / centerline` 三组 `{cx, cy, major_radius, minor_radius, angle_deg}`，坐标即 360×640 原生像素（与 005 缓存同坐标系，**无需缩放重采样**）。
- 同时返回 `diagnostics`：`center_gap_norm`、`wire_major_mm`、`wire_minor_mm`、`outer_inner_major_ratio`、`angle_gap_deg`、`centerline_frontality`、`mask_band_recall/precision`、`inner_arc_coverage`、`inner_normalized_residual`、`inner_sector_instability`。

**这是本轮唯一权威的二维 Ring 几何来源。** 我们没有另写椭圆拟合器。

> 说明：DXY 需要 `skimage`，主工作虚拟环境没有该依赖。为避免安装新包，DXY 侧以独立解释器运行并把结果导出为 JSON（`code/dxy_export.py`），三维侧只读 JSON。DXY 源码未做任何修改。

---

## 3. 外部成熟实现评价

| 项目 | 方法 | 是否采用 | 理由 |
|---|---|---|---|
| [IIT-PAVIS/LfD](https://github.com/IIT-PAVIS/LfD) | 多视角二维椭圆 → 三维二次曲面（ellipsoid） | **未采用** | 其未知量是**椭球**，与"已知尺寸管状 Ring CAD 的位姿"不是同一问题；且它要求多视角椭圆属于同一 quadric |
| [QuadricSLAM](https://open.qcr.ai/code/quadricslam/) | GTSAM 因子图中的 quadric landmark | **未采用** | 引入完整 SLAM 后端，超出"只改 Ring 观测接口"的边界 |
| [M3T / SRT3D (DLR-RM)](https://github.com/DLR-RM/3DObjectTracking) | 基于 CAD 的 region-based 位姿跟踪 | **仅借鉴概念** | 需要 CAD 渲染器与区域对应；本轮已通过 `torus_contours` 得到解析透视轮廓，无需引入渲染管线 |
| 历史 vendor `conics/_conic.py` | 单 conic → 位姿假设 | **未采用（仅复用公式）** | 它解的是圆锥/椭球位姿族，且 yaw 不可观测（见 §1.3）；本轮位姿由 Ring-First + BA 提供，Conic 只作为残差 |

---

## 4. 数学适用性判断

1. **Conic 表示可复用**：椭圆 `(c,a,b,θ)` → 齐次二次型 `C` 是标准构造，历史 `ellipse_matrix()` 与本轮 `conic_from_ellipse()` 公式一致（同等价）。
2. **Conic→pose 不可直接复用**：单视图圆环的 pose 存在法向二重解与半径-深度耦合；必须由多视角 + RGB 消歧，这正是 005 的 BA 在做的事。
3. **管状 Ring 的投影轮廓不是椭圆**：`torus_contours` 给出的是真实管状体的解析视轮廓（两条闭合曲线），与平面圆环的椭圆投影有系统性差异。**DXY 的内外椭圆是"该轮廓的二次拟合"，不是轮廓本身**——这是本轮的核心建模假设，必须被显式检验（见 `FINAL_REPORT.md` Q3）。
4. **内外椭圆不是独立三次观测**：Mid 是内外的平均，不能与内外等权相加。

---

## 5. 复用决策摘要

| 组件 | 决策 |
|---|---|
| DXY `ring_component.recover`（只读调用） | **复用**，作为唯一二维 Ring 观测源 |
| DXY 质量诊断字段 | **复用**，映射为连续置信度权重（非硬门控） |
| 历史 `ellipse_matrix` 公式 | **复用**（等价实现，注明来源） |
| 历史 vendor `estimate_pose` | **不复用**（只作审计证据） |
| 历史 `cad_render/refine`（M3T-inspired） | **不复用**（依赖不可得；概念已借鉴） |
| `native.torus_contours` | **复用**，作为三维 CAD 透视轮廓 |
| Sampson 轮廓残差 | **自行实现**（~40 行；无现成模块同时接受"CAD 解析轮廓 × DXY 内外椭圆"） |

---

## 6. 未确认项

1. 历史 `cad_render.py` 的 `ring020.CADCurves` 在当前环境缺失，无法验证其轮廓关联精度；本轮未尝试恢复该依赖。
2. 历史 Conics 实验的中间指标未在 lineage 中保留到足以复算的程度（只有报告与代码，无 per-view 数值）。
3. 外部框架未做实际编译/运行验证，仅做方法学评估。
