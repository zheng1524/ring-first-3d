# ACTUAL_CALL_GRAPH

```
core/r6_experiments.py
 ├─ r6_core.build_fixed()            固定 GT 场景 + 冻结观测 + X0(005-only)
 ├─ r6_core.ring_candidates()        Ring 残差向量 6-DoF 精化 + 每身份 Sampson 评分
 ├─ r6_core.triangulate_under_H()    固定相机（H 只应用一次）共同三角化（历史 019 代码）
 ├─ r6_core.solve(M1/M2/M3b/M4)      单一 BAProblem（ba_core_r4）
 ├─ HOLDOUT: FIT/HOLDOUT 身份划分（rng 2026）
 └─ E1: 005 相机扰动 -> 005-only 重三角化 -> H2 -> 共同三角化
core/figs_r6.py                      7 张图（全部读 CSV/NPZ）
tests/test_r6_p0.py                  7/7
```
