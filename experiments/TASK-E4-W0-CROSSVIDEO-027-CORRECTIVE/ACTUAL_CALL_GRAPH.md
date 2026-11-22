# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G --stage {variables|ring|controlled|full-corrective}
 ├─ core/camvar.py::CameraVariables        (D1: FROZEN/ANCHOR/RELEASED + 索引 + 断言)
 ├─ core/ring_adapter.py                   (D2: 唯一 Ring 评价入口, C@inv(T0))
 ├─ core/ring_energy.py                    (D3/D4: sqrt(2λρ/N) 精确能量映射, λ 为能量权重)
 ├─ core/ba_core2.py::BAProblem            (RGB + I/C/O + prior + geo; loss='linear')
 ├─ core/controlled2.py                    (D5: 三角化初值 + GROUND_TRUTH.json 隔离)
 ├─ core/fixed_track_tri.py                (历史 019 逐轨迹代码, 固定轨迹封装)
 └─ core/p8_audit.py                       (ACTUAL_OPTIMIZATION_VARIABLES.json + 9 图)
tests/test_corrective.py                   (7/7: 旧错误可复现, 新实现通过)
```

真实 B0/B1/C：**未调用**（Gate 3 FAIL）。Ring 几何仍来自历史 `ring020_026.py`（2 行路径补丁）。
