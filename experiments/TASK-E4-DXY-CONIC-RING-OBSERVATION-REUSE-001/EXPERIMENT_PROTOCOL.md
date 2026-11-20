# EXPERIMENT_PROTOCOL

**任务：** TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001
**基线：** `exp/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005` @ `ba6c4dc`（下文 005）
**分支：** `exp/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001`

---

## 1. 假设

> 用 DXY V9.1 的内外椭圆（轮廓级几何）替代 005 的原始边界点采样，可以在**不牺牲 RGB 多视角一致性**的前提下，得到更准确、更稳定的三维 Ring 位姿。

**可证伪点：** 若 Ring 拟合变好而 RGB held-out 变差，或困难病例改善但成熟病例退化，则假设不成立。

---

## 2. 实验臂（唯一变量 = Ring 几何观测项）

| 臂 | Ring 项 | 实现 |
|---|---|---|
| **A0** | 原始边界点（005 冻结结果） | 直接读取 005 的 `CAMERA_RESULT.json` 与 `CAMERA_QUALITY_MATRIX.csv`，**不重算** |
| **A1** | DXY 内/外 Conic 的 Sampson 轮廓残差 | `conic_residual(mode='A1')` |
| **A2** | A1 + 0.2 权重的原始边界轮廓残差 | `conic_residual(mode='A2', aux_weight=0.2)` |

**冻结不变（全部来自 005）：** SIFT 参数与轨迹构造、Ring 候选（`RING_CANDIDATES.json` 原样复制）、初始化框架（两个版本）、BA 优化器与预算（`max_nfev=60` 等）、版本评分权重、3 px Ring 门限、FIT/HOLDOUT 划分、视角集合（每实例 8 个 FIT）、相机内参、CAD 尺寸（R=5.6, r=0.6）。

**唯一改动：** 命名空间里的 `ring_residual` 函数。

---

## 3. 数据与坐标

- 输入：005 冻结的 80 个 FIT 视角缓存（RGB/labels/K，360×640）。
- DXY 观测：`metrics/DXY_OBSERVATIONS/<view>.json`，80/80 `valid=True`，均 `visible_inner_arc_RANSAC`。
- 无缩放重采样；Conic 按 Frobenius 归一化。

---

## 4. 运行方式

```bash
# 1) 导出 DXY 观测（需带 skimage 的解释器；DXY 只读）
PYTHONPATH=/home/liu/new-polyp-dxy/src /usr/bin/python3 code/dxy_export.py

# 2) 实验臂（主 venv）
export PYTHONPATH=<ws>/src:.
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY code/arm_runner.py --arm A1
$PY code/arm_runner.py --arm A2

# 3) 单元测试
$PY -m unittest discover -s tests -v
```

产物：`runs/<ARM>/<G>/<V>/{observations,predictions,camera,VALIDATION.json}`、`ARM_A1_VIEW_METRICS.csv`、`ARM_A2_VIEW_METRICS.csv`。

---

## 5. 指标（同时评价 Ring 与 RGB）

| 类别 | 指标 | 来源 |
|---|---|---|
| Ring | 每视角 `ring_MAE_px` / `p95`（对**原始边界**，用于与 A0 可比） | 与 005 完全相同的计算 |
| Ring | DXY 内外椭圆拟合残差（DXY 自身） | `diagnostics` |
| RGB | 训练特征重投影（版本评分内） | 005 `version_score` |
| RGB | **held-out 轨迹重投影 MAE/p95**（独立评价，不参与选择） | 005 `held_reprojection` |
| 相机 | 正深度比例、版本评分、选中版本 | `VALIDATION.json` |
| 覆盖 | 门禁通过数、VALIDATED/USABLE/INVALID 计数 | 逐视角状态 |

**注意：** `ring_MAE_px` 是对**原始边界点**计算的，因此 A1 在这一列上"看起来"可能更差——这是预期的：A1 优化的是 Conic 轮廓，不是边界点距离。**不能用这一列单独判断 A1 好坏**，必须同时看 DXY Conic 残差与 RGB held。

---

## 6. 判据

| 结论 | 条件 |
|---|---|
| 支持纳入主线 | 至少：Ring Conic 残差显著下降 **且** RGB held 不恶化 **且** VALIDATED/可用视角数不下降 |
| 部分支持 | Ring 改善但 RGB 持平；或个别病例改善、成熟病例不退化 |
| 不支持 | RGB held 恶化，或成熟病例（G01）门禁通过数下降，或可用视角数下降 |

**禁止**：用 held 反复挑选臂/参数；用 GT 选择；删除困难视角；调整门限。

---

## 7. 已知混杂

1. A1 的 Ring 项与 A0 的 Ring 项**量纲相同（px）但目标不同**（轮廓 vs 边界点），因此两者的 `ring_MAE_px` 不是同一目标函数下的可比损失，只是**对外报告的统一度量**。
2. 版本评分中的 `ring_MAE_mean_px` 在 A1/A2 下改为 conic 残差均值，可能改变版本选择；这一点在 `VALIDATION.json` 中逐实例记录。
3. DXY 主线本身假设环为平面圆环；管状 Ring 的透视轮廓与椭圆存在系统差异（见 `FINAL_REPORT.md` Q3）。
