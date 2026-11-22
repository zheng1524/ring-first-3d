# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G
  └─ core/p1_pipeline.py
       ├─ W0 camera_result.npz + admission.csv + PREPARED.json   [真实输入，SHA 记录]
       ├─ SPLIT（读特征之前冻结：even=FIT / odd=HOLDOUT）
       ├─ replay_019_020/code/features019.py::features()         [历史源码]
       ├─ features019.py::landmarks(FIT only)                    [历史源码；FIT 视角三角化]
       ├─ features019.py::match_desc(des4, des5)                 [历史源码；跨视频候选]
       ├─ core/landmark_consistency.py::check()                  [本轮新增小模块；Open3D RANSAC]
       ├─ Ring 检查：torus_contours(H·C4) vs W0 q_train           [独立几何冲突检查]
       └─ HOLDOUT：把 004 地标投到 005 HOLDOUT 视角，与描述子匹配到的真实像素比较
core/p4_visuals.py → 六类可视化 + forward/reverse 重投影 + 状态落盘
```

调用身份：`features019` = **实际调用**；`features020`/`ring020` = **未调用**；`landmark_consistency` = **新增授权模块**。
