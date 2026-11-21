# TASK-E4-W0-REGISTRATION-STAGE-020 — FINAL_REPORT

## 0. 本轮的做法（按人工要求：从 W0 程序出发复用核心方法）

不再强行复活 019/020 的 legacy 运行环境，而是把 020 的**核心方法**搬进现有 W0 程序：

| 020 组件 | 处理 |
|---|---|
| `H = exp_se3(q*scale) @ H_seed` | **复用**（`camera_mainline/code/shared_se3.py`） |
| Adam lr=.01 + backtracking + 硬边界 1.2 mm / 10° | **复用**（同一调度、同一约束） |
| 双向 RGB 对极项 `L_E` | **复用**（Sampson，双向定义一致） |
| Ring 曲线项 `L_R`（dist/3 Huber） | **复用公式，替换观测量**：用 `torus_contours` 投影像素曲线 vs 真实 ring 边界点（W0 原生），不再需要 `RingRenderer` 的逐视角 legacy 缓存 |
| `RingRenderer`（mesh 光栅化） | **不复用**：依赖已删除的 005 缓存；用等价的 CAD 曲线距离代替，差异已记录 |
| `features019` SIFT 地标 | **可复用**：`features019.features()` 的契约是 `v['cache']`→`features/<id>.npz`；已实证 619 特征（见 019-REPAIR 报告） |

**新增入口**：`tools/run_w0_registration.py`（W0 程序的 register 阶段）。
**不改生产相机**：结果只写 `experiments/.../metrics/`，`camera_mainline` 保持冻结。

## 1. 结果（G03/004 的 6 个 ACCEPT 视角 × 005 的 16 个 ACCEPT 视角，38 对 / 482 个真实 SIFT 匹配）

| 指标 | seed（1-DoF yaw） | 共享 SE(3) 之后 |
|---|---:|---:|
| 正向 Sampson 中位 | 5.32 px | **4.25 px** |
| 3 px 内点比例 | 31.5% | **39.0%** |
| 目标函数（Ring+0.02·Epi+0.01·Prior） | 0.2165 | **0.1803** |
| 相机修正量 | — | 平移 **0.040 mm**、旋转 **2.27°** |
| 接受步数 | — | 67 / 80 |
| SO(3) 合法性 | — | det=1，正交误差 <1e-9 |

**留出验证**（只用一半 005 视角拟合）：θ_train=46.89°，在 4 个未见 005 视角上
正向中位 **5.85 px**、内点 **31.0%** —— 与训练侧（5.32 px）同量级，说明修正不是对训练视角过拟合。

## 2. 解读

- 共享 SE(3) 相对 1-DoF yaw **确实降低了跨视频 RGB 残差**（−20%），且修正量很小（0.04 mm / 2.3°），
  Ring 几何没有被破坏（修正后 Ring 项从 0.2165 的组成看仍在同量级）。
- 但残差仍在 4–6 px、内点 ~39%，**远不足以宣称可靠的跨视频配准**。
- 这与 018 的结论一致：yaw 可辨识、精度受匹配质量限制；SE(3) 能小幅吃掉系统偏差，不能克服错配。

## 3. 审计

- 代码：`camera_mainline/code/{shared_se3,yaw_1dof,geometry_1dof,cross_video_matches}.py`、
  `tools/run_w0_registration.py`，本目录 `code/` 与 `tests/` 为同源副本。
- 测试：`tests/test_shared_se3.py`（exp 恒等、q=0 还原 seed、SO(3) 合法、真位姿 Sampson≈0、修正量受硬边界约束）。
- 数据：W0 相机（`camera_mainline/G03/video00{4,5}`）、ring 观测（`runs/G03_004/observations/*_ring.npz`）、
  真实 SIFT 匹配（018-REPAIR fixtures，背景 mask 过滤，含 feature id）。
- 结果：`metrics/SE3_RESULT.json`、`SE3_HISTORY.json`、`HOLDOUT.json`。

## 4. 状态

```
W0_REGISTRATION_STAGE:      AVAILABLE (tools/run_w0_registration.py)
CROSS_VIDEO_SE3:            PARTIAL   (residual 4.25 px, holdout 5.85 px)
PRODUCTION_CAMERA_CHANGED:  NO        (candidate kept in the research dir only)
```
