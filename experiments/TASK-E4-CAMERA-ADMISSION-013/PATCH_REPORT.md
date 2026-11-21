# PATCH_REPORT — TASK-E4-CAMERA-ADMISSION-013-PATCH

```
CAMERA_MAINLINE:              W0
CAMERA_ADMISSION_GATE:        READY
CROSS_VIDEO_014_ADMISSION:    YES
SINGLE_VIDEO_CAMERA_ALGORITHM_RESEARCH: CLOSED
```

## Q1：179°–180° 究竟来自哪里

旧代码：

```python
Rm = np.median(np.array([c[:3,:3] for c in cams]), axis=0)
Q  = np.linalg.qr(Rm)[0]              # <- 不是一个有物理意义的参考旋转
ang_i = angle(c[:3,:3] @ Q.T)
```

环视相机的旋转是**绕环轴均匀分布**的。对旋转矩阵逐元素取中位数**不是旋转**（不正交），
再投影到 SO(3) 得到的 `Q` 与所有相机都相差约 180°。

实测：旧指标 **179.0–180.0°，中位 179.8°**（B0/W0 相同）。**纯计算错误，不是物理跳变。**

## Q2：正确的 SO(3) 相邻旋转

以真实帧号排序，用 `θ = arccos((tr(RaᵀRb)−1)/2)`：

| 指标 | 值 |
|---|---:|
| 相邻视角旋转 中位 | **0.14°** |
| 相邻视角旋转 最大 | **0.79°** |
| 相邻中心跳变 最大 | **2.53 mm** |
| 相对参考相机旋转 中位 | 0.78–0.85°（记录用，不作门控） |

视角运动是连续的，**不存在姿态跳变**。

## Q3：三条轨迹的分类（不再统称"近零基线"）

| track | 基线 | 夹角 | 源深度 | 目标深度 | 分类 |
|---|---:|---:|---:|---:|---|
| 1225 | 0.44 mm | 2.1° | −4.5 | −4.5 | **DEGENERATE_TRIANGULATION** |
| 1065 | 0.41 mm | 0.4° | −11.4 | −10.2 | **DEGENERATE_TRIANGULATION** |
| 245 | 9.6–10.0 mm | 13.8–14.6° | **−41.6** | −40.8 | **CHEIRALITY_FAILURE_SOURCE**（不是小基线问题） |

245 的基线充足，但两条源视线的交点在相机后方 → 对应关系本身错误。

## Q4：B0/W0 的真实 RGB 指标（同一评价器，三套口径）

| 臂 | 原始 held_n | 几何有效 held_n | 有效 held 中位 | 有效 p95 | 退化三角化 | 目标深度失败 |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 全量 | — | 1.11 | 3.30 | 385 | 0 |
| W0 | 全量 | — | **0.98** | **3.21** | 408 | 0 |

（有效轨迹要求：基线 ≥2 mm、夹角 ≥2°、两源正深度、源重投影 ≤3 px；筛选依据**只来自源视角几何**，
不使用目标视角误差，避免事后筛选偏差。目标视角负深度单独计数，不静默删除。）

## Q5：诊断是否会绕过其他失败项

**不会。** `diagnose_once` 已删除，改为 `apply_diagnostic`：只替换与三角化直接相关的 p95/median 字段，
然后**完整重跑 `classify`**。新增负例测试：

| 测试 | 结果 |
|---|---|
| 退化轨迹 + Ring 不合格 | **QUARANTINE（不 ACCEPT）** |
| 退化轨迹 + 179° 旋转异常 | **不 ACCEPT** |
| 退化轨迹 + 中心跳变 50 mm | **不 ACCEPT** |
| 缺 `pose_valid` 字段 | **不 ACCEPT** |
| 缺 held 统计 | **INSUFFICIENT_EVIDENCE** |
| 仅 p95 超标、其余正常 | 诊断后可 ACCEPT |

测试总数 **14/14 通过**（含旋转几何 6 项：同一旋转、1°/5°/179°、q≡−q、w2c→c2w、非法矩阵）。

## Q6：修复后实际 ACCEPT 数量

**B0 16/16、W0 16/16**（Ring 0.84/0.83 px；held 1.11/0.98 px，p95 3.30/3.21）。
数量不是目标，是结果——这次每条指标都有几何依据。

## Q7：相机资产是否可读可追溯

`camera_mainline/G03/video005/`
- `accepted_cameras.npz`：16 个 ACCEPT 相机（c2w、K、ids、raw_frames、reference、Ring CAD、来源臂、状态、points、track_ids、`pose_convention='c2w'`）
- `all_camera_admissions.csv`、`rejected_views.csv`（空）、`quality_summary.json`
- `input_manifest.json`：policy/gate/rotation/held-evaluator/相机资产/轨迹 的 SHA256

**已实际提交到 Git**（`git add -f`，`.npz` 被 gitignore）。Policy 中 `frozen_at_commit` 已由 `TBD` 更新。

## Q8：能否启动 014

**YES。** 阻止性问题已全部修复：旋转口径、Gate 放行逻辑、三角化几何有效性、资产缺失、字段缺失检查。
可在 014 中继续验证的遗留项（不阻塞）：
- 视角几何有效轨迹数在部分视角偏少（≥20 门限已满足但余量不大）；
- 尚未审计其余九段视频的 Ring-First 候选分支稳定性。

## 修改清单

`code/camera_admission.py`（重写 v2）、`code/camera_rotation_metrics.py`（新）、
`code/evaluate_held_geometry.py`（新）、`tests/test_camera_admission.py`（14 项）、
`policy/CAMERA_ADMISSION_POLICY.yaml`（frozen 标记）、
`metrics/{ADMISSION_RESULTS, TRACK_AUDIT_1225_1065_245}.csv`、`camera_mainline/G03/video005/*`。
