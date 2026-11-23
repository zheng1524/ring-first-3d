# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G03 --stage h-init-and-triangulation
 ├─ core/r5_core.py
 │    ├─ build_fixed()            GT 场景 + 冻结观测 + 基线 X0（005-only）
 │    ├─ perturb_cams()           精确幅度扰动（锚点保护）
 │    ├─ ring_candidates()        yaw 网格 + Ring 6DoF 精化（边缘冻结于初始相机）
 │    ├─ epipolar_energy()        FIT 身份 Sampson 评分
 │    ├─ triangulate_under_H()    固定相机（004 经 H）联合三角化（历史 019 代码）
 │    └─ solve(M1/M2/M3a/M3b/M4)  单一 BAProblem（ba_core_r4）
 ├─ core/r5_experiments.py        H 对照 + C 组 + B 组
 └─ core/figs_r5.py               7 图（全部读 CSV）
tests/test_r5_p0.py              5/5（幅度、锚点、M3b、M4、E 组）
```
