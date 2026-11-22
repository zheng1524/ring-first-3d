# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G --stage controlled-r2
 ├─ core/r2_synth.py
 │    ├─ build_scene()            GT H / GT cameras / GT landmarks      [GT 只用于观测与评价]
 │    ├─ ring_observations()     同一 GT 相机投影固定 CAD -> I/O/C 观测
 │    ├─ rgb_observations()      同一 GT 场景 -> 2D 观测 (feature_id = landmark_id)
 │    └─ triangulate()           历史 019 逐轨迹代码 (fixed_track_tri)，稳定键
 ├─ core/camvar.py               FROZEN / ANCHOR / RELEASED + 参数索引
 ├─ core/ba_core_r2.py           I/C/O 精确能量映射；边缘仅来自初始相机
 └─ core/levels.py               L0..L5 分级实验
      └─ core/figs_r2.py          6 张图
tests/test_triangulation_identity.py   T1-T5 (4/4)
```
无第二套 BA；求解器仍为 `scipy.optimize.least_squares`。
