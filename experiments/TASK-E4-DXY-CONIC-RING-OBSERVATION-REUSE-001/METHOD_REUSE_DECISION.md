# METHOD_REUSE_DECISION

**原则：** 能复用就不重写；不能复用必须说明原因。本轮只改 Ring 几何观测与其位姿优化接口。

---

## 1. 决策表

| # | 组件 | 来源 | 决策 | 理由 |
|---|---|---|---|---|
| R1 | 二维 Ring 内外椭圆与质量诊断 | DXY V9.1 `ring_component.recover` | **复用（只读调用）** | 任务要求以 DXY 为二维几何权威；实测 80/80 有效，坐标与 005 缓存同为 360×640 |
| R2 | Ring 小孔/连通域等预处理 | DXY `ring_holes` 等（内部） | **不单独调用** | 由 R1 内部完成；重复调用会造成二次处理 |
| R3 | 三维 Ring 透视轮廓 | `src/ring_first_3d/mainline/native/camera.torus_contours` | **复用** | 解析 Torus 视轮廓，避免用平面圆近似 |
| R4 | 椭圆→齐次 Conic | 历史 `conics_init.ellipse_matrix` 公式 | **复用（等价实现）** | 公式一致；不引入历史模块的 gauge/依赖 |
| R5 | Conic→位姿求解 | 历史 vendor `conics/_conic.estimate_pose` | **不复用** | 解的是圆锥/椭球位姿族；yaw 不可观测，历史文件自述需 RGB 补充 |
| R6 | CAD 轮廓渲染与关联 | 历史 `cad_render.py`（M3T-inspired） | **不复用** | 依赖 `ring020` + `open3d`，当前环境不可用；且本轮已有解析轮廓 |
| R7 | Sampson 轮廓残差 | 自行实现 `code/conic.py` | **新实现（~40 行）** | 现有代码中没有"CAD 解析轮廓 × DXY 内外 Conic"的残差模块 |
| R8 | RGB/SIFT、轨迹、BA、版本评分、门限 | 005 冻结实现 | **完全复用，未改动** | 任务硬约束 |

---

## 2. 为什么不用 LfD / QuadricSLAM / M3T

| 框架 | 为什么不能直接替换本任务的求解器 |
|---|---|
| [LfD](https://github.com/IIT-PAVIS/LfD) | 其未知量是三维**二次曲面（ellipsoid）**；本任务 CAD 已知且是**管状环**，未知量只有 6DoF 位姿。把 Ring 当 quadric 会丢失已知尺寸约束 |
| [QuadricSLAM](https://open.qcr.ai/code/quadricslam/) | 面向 SLAM 的因子图后端，引入它等于替换整个相机系统，超出"只改 Ring 观测"的边界 |
| [M3T/SRT3D](https://github.com/DLR-RM/3DObjectTracking) | 需要 CAD 渲染与区域对应；本轮已有解析轮廓，引入渲染器只会增加变量 |

三者共同的可借鉴点是**"用二维轮廓而不是离散点做对应"**，这一点已在本轮残差中体现。

---

## 3. 本轮新增代码的边界

`code/conic.py` 只做四件事：
1. `conic_from_ellipse`：DXY 椭圆 → 3×3 齐次 Conic（含尺度归一化）。
2. `sampson`：点到 Conic 的一阶几何距离（px）。
3. `split_curves`：把 `torus_contours` 的两条曲线按**面积**分为内/外，不假设输出顺序。
4. `quality_weight`：把 DXY 的 coverage/residual/stability/branch 映射为**连续权重**，不做硬拒绝。

`code/arm_runner.py` 只做装配：复用 005 的轨迹、候选、BA、评分、门限与评价，仅替换 `ring_residual`。

---

## 4. 不可复用却仍然保留的东西

- 历史 `mature_geometric_pose_refinement/` 全部源码**原样保留**，未删除、未修改，作为后续"轮廓关联"研究的一手材料。
- 历史 vendor conics 保留在原处，未复制进本任务。
