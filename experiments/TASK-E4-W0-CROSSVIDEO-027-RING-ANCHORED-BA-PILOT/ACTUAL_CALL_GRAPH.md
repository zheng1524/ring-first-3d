# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G --stage full-027
 ├─ core/p0_paired.py
 │    ├─ core/fixed_track_tri.py (历史 019 逐轨迹代码, 固定轨迹封装)   [等价性 max diff 0.0]
 │    ├─ ring020_026.py::RingRenderer.losses(H_increment, cid)        [历史，2 行路径补丁]
 │    └─ 同一批相机 -> Ring MIO + ΔX + 66 对距离   -> RING_3D_PAIRED_SENSITIVITY.csv
 ├─ core/p3_controlled.py
 │    └─ ba_core.Problem (RGB + Ring + priors) -> scipy.optimize.least_squares(TRF, huber) -> 10 场景
 ├─ core/p4_real.py
 │    ├─ FROZEN_BA_OBSERVATIONS.csv (106 观测, SHA 记录)
 │    └─ A / B1 / C -> ABC_EVALUATION.csv, PER_CAMERA_UPDATES.csv, BA_RUN_STATE.json
 └─ core/p6_figures.py -> 9 张图（数据来源标注在标题/轴标签）
026-CORRECTIVE/core/p3_joint.py  (本轮补交，修复 026 入口缺失依赖)
```

求解器：`scipy.optimize.least_squares`（成熟框架）；新增代码仅 `ba_core.py` 残差适配层与
`fixed_track_tri.py` 固定轨迹封装；未重新实现 SE(3)/投影/Ring CAD/SIFT/三角化。
