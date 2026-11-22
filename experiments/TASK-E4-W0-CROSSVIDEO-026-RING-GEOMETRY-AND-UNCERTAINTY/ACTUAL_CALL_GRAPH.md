# ACTUAL_CALL_GRAPH

```
core/p1_ring_io.py
 └─ replay_020/code/ring020_026.py::RingRenderer(22 ACCEPT views).losses(H=I)
      ├─ CADCurves.segments()   [历史，未改]
      ├─ point_to_segments()    [历史，未改]
      ├─ evidence()             [历史，未改；输入为 011 DXY 适配的 I/O 观测]
      └─ pytorch3d rasterizer   [runtime/p3d]
core/p2_sensitivity.py
 ├─ RingRenderer.losses(H025·C4 / H025⁻¹·C5)
 ├─ RingRenderer.losses(单自由度扰动)
 └─ features019.landmarks()   [历史 019，未改]  共同模式扰动
core/p2_relative.py
 └─ features019.landmarks()   [历史 019，未改]  单相机/独立扰动
core/p4_figures.py → 10 张真实数据图
```

适配（仅数据/路径）：`RING_CAD`、`RING_NORM`、`config/VIEWS.json`、`inputs/G03/<view>.npz`（含 T）、`ring/<view>.npz|json`。
