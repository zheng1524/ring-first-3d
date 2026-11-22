# ACTUAL_CALL_GRAPH

```
experiments/.../023/core/p3_landmarks.py
  └─ replay_019_020/code/features019.py::features(v)      [历史源码，未改]
       └─ PREPARED cache npz (RGB, labels)                 [真实 W0 输入]
  └─ features019.py::landmarks(ids,label)                  [历史源码，未改]
       ├─ matches() → match_desc() (ratio .72 + mutual)
       ├─ fundamental() → sampson() (<4 px 过滤)
       ├─ cv2.triangulatePoints + least_squares(soft_l1, f_scale=1.5)
       └─ 质量门: 正深度 ∧ reproj<2px ∧ parallax>0.5° ∧ |X|<300
     → replay_019_020/runs/p3/landmarks/G03_{004,005}.npz (+ _OBSERVATIONS.json)

experiments/.../023/core/p3_objective.py
  ├─ 读取 W0 camera_result.npz (004/005 ACCEPT) 与 021 MATCHES.npz（只读）
  ├─ features019.match_desc(des4, des5) → 24 个跨视频身份
  ├─ losses(): L_Ring(torus_contours) + 0.2L_SIFT3D(双向) + 0.02L_EPI + 0.01L_Prior
  ├─ optimize(): Adam + 累计边界 + 每 10 步 checkpoint
  └─ 输出 runs/G03/P3_RESULT.json, P3_ckpt.npz

experiments/.../023/tools/forensic_epipolar_fixed.py   [P0 修复]
experiments/.../023/tools/p1_independent_holdout.py    [P1 独立 F 对照]
```

历史模块调用身份：`features019` = **实际调用**；`features020` = 仅复用 `match_desc`（部分）；
`ring020`/`objective020`/`optimize020` = **未调用**，数学被重述。
