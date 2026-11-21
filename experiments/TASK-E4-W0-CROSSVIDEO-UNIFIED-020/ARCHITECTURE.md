# ARCHITECTURE — one W0 mainline + one cross-video algorithm

```
PREPARED (frozen INIT)  ->  tools/run_w0_camera.py  ->  camera_mainline/<G>/video<v>/
                                   |                        (camera_result.npz, admission.csv, manifest.json)
                                   v
                     experiments/TASK-E4-W0-CROSSVIDEO-UNIFIED-020/code/run_cross_video.py
                                   |
      LOAD_W0 -> ADAPTER_CACHE -> SIFT -> INIT(1-DoF) -> SE3 -> EVALUATE -> EXPORT
```

- `asset_resolver.py` is the only place that maps `(group, video)` to files.
- `camera_mainline/code/{shared_se3,yaw_1dof,geometry_1dof,cross_video_matches}.py` are shared by **all** groups.
- `run_cross_video.py` contains **no** `if group == ...` branch (tested by `test_no_group_branch_in_entry`).
- Every stage writes `audit/RUN_STATE.json` with code hash + stage status; `RUNNING` is never treated as `PASS`.
