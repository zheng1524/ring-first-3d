# M2F5 Implementation Plan (executed)

1. Patch `run_w0_camera.stage_tracks` to always call current `track005`; remove frozen_011 copy.
2. Add raw sampling in `tools/m2f5_unified.py`: 12 uniform + 4 largest-gap real frames, no frozen39 list.
3. Prepare fresh frames with `prepare_view`; apply DXY `ring_holes.run` to every frame; store clean sidecars.
4. Run fresh W0 with clean sidecars; one per raw video.
5. Build one tolerant local pool from current W0 (S2-style local candidate semantics); no S0/S1/S2 formal outputs.
6. Use W0 scene-point mean and angular centrality for anchor; no historical INITIAL.
7. Call T10 then T13 on the same pool; no T11; retain real T13 four-camera geometry check.
8. Run official HERO on 174 ready tuples; preserve Raw Mesh.
9. Evaluate all supports with standard A→B using B camera; generate six views.
10. Run all 13 groups from raw videos; keep failures and no post-result filtering.
11. Add behavior tests for raw sampling, current tracks, mask clean, HERO identity, A→B, six-view.
12. Freeze outputs, registry evidence, reports, and commit.
