# BA_SOURCE_REUSE_AUDIT

## 搜索范围与结果

| 来源 | 内容 | 本轮用途 |
|---|---|---|
| 历史 019 `features019.py` | `project`、`least_squares(soft_l1, f_scale=1.5)` 三角化 | **直接复用**（三角化、以及固定轨迹实验） |
| 历史 020 `ring020.py` | `CADCurves.segments/project/point_to_segments`、`RingRenderer` | **直接复用** Ring 几何与可见边缘 |
| 020 `objective020.py` / `optimize020.py` | `SymmetricFeatures` 目标 + Adam + LOCAL_SE3_BOUND | **仅参考**（Adam 不是 BA 求解器；其目标为 mean-loss，无向量残差接口） |
| 021 `core/se3.py`、`torch_objective.py` | SE(3) exp、SampledObjective | **se3 复用**；torch 目标未用（022 已证与正式目标不同） |
| 022 `MINIMAL_FIX_PLAN` F7/F10 | checkpoint/梯度要求 | 参考 |
| 026-CORRECTIVE `p2_se3_ring.py` | 增量语义、MIO 定义、H 方向 | **直接复用**约定 |
| 025 `p2_validate` | HOLDOUT 批量描述子 | 参考（本轮 HOLDOUT 判 NOT_EVALUABLE，见报告） |

## 结论

项目内**没有**可直接调用的向量残差 BA 求解器。历史 020 的 `optimize020` 是 Adam + 局部信赖域，
其目标以 **mean-loss** 形式实现（无 per-observation 残差向量），无法直接喂给稀疏最小二乘。

因此本轮采用：
- **求解器**：`scipy.optimize.least_squares`（TRF + huber + 数值 Jacobian）—— 成熟框架，未自研；
- **新增代码**：仅 `core/ba_core.py` 的**残差适配层**（H/相机/地标参数化 + Ring 逐点距离抽取），
  以及对历史 019 三角化的固定轨迹调用封装 `core/fixed_track_tri.py`（与历史输出逐位一致，max diff 0.0）。

未重新实现：SE(3)、投影、Ring CAD、SIFT、三角化、鲁棒损失定义。
