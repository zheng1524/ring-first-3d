# UNIFIED_PIPELINE_ARCHITECTURE

```
                 UNIFIED ENTRY  core/u028.py --group <G>
                              │
        discover(G)  ← prepared/{G}_{video}, camera_mainline/G/video*, assets/.../G/RING.npz
                              │
        W0: read camera_mainline  else  tools/run_w0_camera.py --output runs/G/video*
                              │
        ring_evidence(): historical DXY recover(labels, RGB, 10.)  -> ring/<view>.npz|json
        RingRenderer: historical ring020_026 (only R repointed)   -> M/I/C/O per view
                              │
        features019.features / landmarks (same rule)  -> per-video 3D landmarks
        features019.match_desc(ref, other)             -> cross-video identities
        FIT/HOLDOUT: rng(2028) 70/30 identity split
                              │
        [H init old/new, joint triangulation, M3b BA]  ← NOT_EXECUTED this round
                              │
        FIT/HOLDOUT evaluation (same definition)       ← NOT_EXECUTED for H/BA
```

组名只出现在**数据路径**与**Ring CAD 路径**，不决定任何算法分支（`tests/test_u028_contracts.py::test_source_has_no_group_specific_algorithm`）。
