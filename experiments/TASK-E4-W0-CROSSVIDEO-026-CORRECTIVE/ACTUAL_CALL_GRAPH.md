# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G --stage full-corrective
 ├─ core/p1_centerline.py
 │    └─ dxy_mid._engine.ring_component.recover(labels, RGB, 10.)   [历史 019 同一例程]
 │         -> replay/ring_corrective/<view>.npz|json  (真实 inner/outer/centerline)
 ├─ core/p2_se3_ring.py
 │    ├─ replay/ring020_026.py::RingRenderer.losses(H_increment, cid)  [历史，2 行路径补丁]
 │    ├─ canonical_np vs 历史 canonical() 一致性检查
 │    ├─ SE3_COMPOSITION_TESTS (T1–T6，端到端损失等价)
 │    ├─ RING_IO_CORRECTIVE (22 视角，MIO + MICO)
 │    ├─ RING_POSE_SENSITIVITY_CORRECTED (世界轴 / 局部轴 / 平移)
 │    └─ H025_REEVALUATION (004: H, 005: H⁻¹)
 ├─ core/p4_tracks.py
 │    └─ 读取 026 已用未修改 features019 生成的地标 + OBSERVATIONS
 │         -> 稳定键交集 -> 位移 / 存活 / 12 身份可用性
 ├─ core/p6_figures.py  (10 图，标注数据来源与函数)
 └─ core/p3_joint.py    (门控：JOINT_OPTIMIZATION_EXECUTED=false)
```

每次运行都会打印 `PROTOCOL <algo> group <G> stage <S>` 并校验 config 中的 `algo` 字段。
