# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G03 --stage controlled-L2-diagnostics
 ├─ core/r3_run.py
 │    ├─ r2_synth.build_scene()             GT H/cameras/landmarks
 │    ├─ r2_synth.ring_observations()       同一 GT 相机的 I/O/C 观测
 │    ├─ r2_synth.triangulate()             005-only 二维观测 -> X_init（历史 019 逐轨迹）
 │    ├─ solve(mode='h_only')               theta = dH (6) ; X 与相机 dxi 冻结
 │    └─ solve(mode='joint') / progressive  theta = [dH, dxi_released, dX]
 ├─ core/ba_core_r2.py                      I/C/O 精确能量映射；边缘来自初始相机
 └─ core/visibility_jacobian.py             可见边关联审计 + H-only Jacobian
core/aggregate.py                          从全部独立 run 目录重建 SUMMARY_ALL_RUNS.csv
core/figs_r3.py                            6 张图（数值全部读自 METRICS.json）
```
每个 run 独立目录：`CONFIG.json / METRICS.json / RESULT.npz`；互不覆盖。
