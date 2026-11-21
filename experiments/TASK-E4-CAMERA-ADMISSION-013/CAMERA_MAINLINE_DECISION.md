# CAMERA_MAINLINE_DECISION

```
CAMERA_MAINLINE = W0
CAMERA_ADMISSION_GATE = READY
SINGLE_VIDEO_CAMERA_RESEARCH = CLOSED
```

## 依据

用统一准入策略（基线 ≥2 mm 过滤后）对 G03/005 的 16 个视角重新评价：

| 臂 | ACCEPT | QUARANTINE | REJECT | Ring raw MAE | held 中位 | held p95 |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 16 | 0 | 0 | 0.844 | 1.113 | 3.354 |
| **W0** | **16** | 0 | 0 | **0.829** | **0.990** | **3.319** |

W0 在两个口径上都略优，且此前"raw00229 = 10.72 px"的异常已被证明是退化三角化，**不存在相机失稳证据**。
因此按任务书 §7.1，**允许 W0 作为 G03/005 的优选相机结果**，并已冻结到 `camera_mainline/`。

## 冻结资产

`camera_mainline/G03/video005/`
- `accepted_cameras.npz`：16 个 ACCEPT 相机（c2w、K、points、track_ids、reference、Ring CAD 尺寸、来源臂）
- `admission_report.csv`、`rejected_views.csv`（本轮为空）、`input_manifest.json`

## 关闭声明

**单视频（G03/005）相机算法竞争到此结束。**
- B0 保留为算法基线；W0 为冻结资产。
- J2/J3 不进入主线；010 双轮廓几何作为独立技术资产保留。
- 不再进行权重实验。

## 其他组的适用方式

同一 `camera_admission.py` + 同一 `CAMERA_ADMISSION_POLICY.yaml`，不设按组差异。
若某视角被拒，按 §P3 从同视频其他候选帧补位，使用相同恢复算法与相同门限；
若某方向无合格相机，明确报告缺失，不强制补齐。
