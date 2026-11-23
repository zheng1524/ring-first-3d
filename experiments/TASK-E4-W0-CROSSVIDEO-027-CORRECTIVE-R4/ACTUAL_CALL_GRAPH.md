# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G03 --stage controlled-error-ablation
 ├─ core/r4_run.py
 │    ├─ make_fixed()            GT 场景 + 冻结观测（实验 I）
 │    ├─ baseline_X()           005-only 三角化（历史 019）
 │    ├─ perturb_cams()/perturb_X()/E1,E2 retriangulate
 │    ├─ solve(M1|M2|M3)       同一 ba_core_r4.residual_vector(rgb_mode)
 │    └─ run_group()            每组独立目录 + CONFIG/METRICS/RESULT
 ├─ core/ba_core_r4.py         单一残差入口 + 能量分解（E_terms == 0.5‖r‖²）
 └─ core/figs_r4.py            6 张图（读 METRICS.json / RESULT.npz）
tests/test_r4_contracts.py     4/4（损失切换、能量恒等、相机扰动、E 组重三角化）
```
