# TASK-E4-W0-MAINLINE-CONSOLIDATION-015 — FINAL_REPORT

```
W0_MAINLINE:            READY
WORKSPACE_CLEANUP:      PARTIAL
G03_004_CAMERA:         PARTIAL   (6/16 ACCEPT, held 1.78 px)
G03_CROSS_VIDEO:        BLOCKED   (1/688 pairs >=20 inliers)
BODY_CROSS_VIDEO_ADMISSION: NO
```

## Q1 唯一流程

`tools/run_w0_camera.py` 是唯一入口（`--group --video --stage --dry-run --resume`）。
调用：Ring-First（`native.camera`）、冻结 `track005`、冻结 `local_ring_sfm.BA`、`camera_mainline/code/` 的评价与 Gate。
源码 SHA 记录在每次导出的 `manifest.json`。

## Q2 复现

- 冻结输入回归（005）：**16/16 ACCEPT，held 0.980 / p95 3.209，与 013 逐位一致**。
- Ring raw 0.964 vs 0.829：口径差异（顶点 KD-tree vs 线段距离），已记 OPEN。
- 004：从 Ring-First 端到端重跑（非冻结输入），16 视角，6 ACCEPT。

## Q3 清理

- 删：全仓 `__pycache__`（REGENERABLE），释放 1.54 MB。
- 保留：全部原始视频/ZIP、`assets/retained_sources`、DXY（未触碰）、所有实验报告与相机资产、Body/HERO 相关目录。
- `runs/` 目录与多份 gate 代码副本标 `PENDING_REVIEW`（历史脚本仍 import，未确认无依赖前不删）。
- **未执行任何 `rm -rf` 通配删除，未改写历史提交。**

## Q4 保留资产

原始 ZIP/视频、参考照片、Ring CAD、Ring-First 内核、010 双轮廓实验、011/012 的 J2/W0 证据、013/014 报告与相机资产——全部保留。

## Q5 八项工程问题

见 `ERROR_FIX_LEDGER.md`：6 项 FIXED、1 项 PARTIAL（K 默认值）、1 项 OPEN（Ring 距离口径）。

## Q6 004 指标

Ring raw 1.20、held 中位 1.78、p95 9.60、6/16 ACCEPT、10 QUARANTINE（拒绝原因：held p95 超标或有效轨迹 <20）。
资产：`camera_mainline/G03/video004/{camera_result.npz, accepted_cameras.npz, admission.csv, manifest.json}`。

## Q7 跨视频

**BLOCKED**：688 对中仅 1 对达 20 内点，无法建立跨视频轨迹或消除 yaw 歧义。

## Q8 主体重建

**跨视频：NO。** 单视频 005：可用（16/16 ACCEPT）；单视频 004：谨慎（6/16 ACCEPT）。

## 交付

`tools/run_w0_camera.py`、`camera_mainline/{README,CAMERA_PIPELINE,ACTIVE_CAMERA_MODULES}.md`、`camera_mainline/code/`、`camera_mainline/CAMERA_ADMISSION_POLICY.yaml`、
`camera_mainline/G03/video00{4,5}/`、本目录 4 份报告 + `cleanup/` 4 份 + `metrics/`、`visualization/camera_network/`。
