# ACTUAL_CALL_GRAPH（静态 import + 实际运行证据）

## 正式链路（命令 `python core/run_corrective.py --group G03`）

```
core/run_corrective.py
  ├─ adapters? 否：直接 import core/w0_adapter.py            [实际调用]
  │    └─ camera_mainline/G03/video00{4,5}/{camera_result.npz, admission.csv, manifest.json}
  │       + PREPARED.json caches                              [实际读取]
  ├─ core/cross_video_matches.collect()                       [实际调用]
  │    └─ cv2.SIFT_create(6000, 0.01) → ratio 0.75 → labels==0 背景过滤
  │       （无 mutual、无 RGB-RANSAC、无多视角轨迹、无三角化）
  ├─ core/yaw_1dof.solve()                                    [实际调用]
  ├─ core/shared_se3.objective()/optimize()                   [实际调用]
  │    ├─ se3.exp_se3（新实现）
  │    └─ ring_term → torus_contours()（W0 原生，非 RingRenderer）
  └─ camera_metrics.check_so3 / delta_size                    [实际调用]
```

## 历史模块的调用身份

| 模块 | 身份 | 证据 |
|---|---|---|
| `019/code/features019.py` | **仅被 import 的历史资产？否——完全未被 import** | `grep features019 core/*.py` 无 import；只有注释 |
| `020/code/features020.py` | **未调用** | 同上 |
| `020/code/ring020.py`（RingRenderer/CADCurves） | **未调用** | `shared_se3.py:55` 注释明说用 `torus_contours` 代替 |
| `020/code/objective020.py` | **未调用**（数学被手写重述） | 无 import；`shared_se3.py` 仅注释引用 |
| `020/code/optimize020.py` | **未调用**（Adam 调度被重写） | `shared_se3.optimize` 为 numpy 手写实现 |
| `020/code/gate020.py` / `feature_gate020.py` | **未调用** | 无 import |
| `tools/run_w0_camera.py` | 间接：W0 产物由它生成，但 021 不调用它 | 读取其输出文件 |

**结论：021 的正式目标 = Ring(`torus_contours`) + EPI + Prior，不是 020 R3。**
`L_F`（双向 3D 地标）不存在；`core/run_corrective.py` 里 `L_F` 字段直接写
`'BLOCKED: no cross-video 3D landmark identity'`，没有参与 `objective()`。

## 状态语义（防止把 Adam 步数当准入）

| 指标 | 021 实际值 | 含义 |
|---|---|---|
| `OPTIMIZER_ACCEPTED_STEP` | 80/80 | Adam 接受更新步，**不是**相机准入 |
| `W0_VIEW_ACCEPT` | G03 6+16；G01 0+0；G05 0+0 | 冻结准入策略的视角状态 |
| `DIAGNOSTIC_OPT_COMPLETED` | G03 yes；G01/G05 no | 是否跑完 80 次迭代 |
| `CROSS_VIDEO_GEOMETRY_ACCEPT` | **NO** | 内点 27.7%、p95 156 px、无 3D 同名身份 |
| `BODY_CROSS_VIDEO_ADMISSION` | **NO** | 同上 |

## 动态完整性说明

G03 的三次运行日志见 `provenance/`（`RUN_STATE.json`、`SE3_HISTORY.json`）；
G01/G05 只有 `LOAD_W0` 与 `W0_ADMISSION` 两阶段即 `BLOCKED`，与代码分支一致（`if not acc_a or not acc_b: return`）。
