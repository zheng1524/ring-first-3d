# 结果索引：TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001

状态：D0 多来源开放场景；D1 派生刚体候选；D2 NOT_FUSED；D3 部分可评价。GT=NONE。

[完整报告](TECHNICAL_REPORT.md) · [可复现入口](REPRODUCE.md) · [实际指标](metrics/) · [全部本地结果 SHA 索引](provenance/LOCAL_RESULT_INDEX.csv)

公开四张核心图：

- [Fig1_three_complete_scenes.png](figures/Fig1_three_complete_scenes.png) — SHA256 `a65dacde092fc0fa70ea4029194b97c10ca9dee76259231956e909de3c3074b7`
- [Fig2_six_views_actual_XYZ.png](figures/Fig2_six_views_actual_XYZ.png) — SHA256 `1dcdc2ea9f6af9a6986433aedfb6f0e2cb775bbd7bff3f4785b817c18da15cce`
- [Fig3_real_crossframe_reprojection.png](figures/Fig3_real_crossframe_reprojection.png) — SHA256 `6d9a6b71e21346059c29ade1b9ad9753053e0224931cb0326f0a64d65ea3035a`
- [Fig4_BC_new_coverage_conflict_loss.png](figures/Fig4_BC_new_coverage_conflict_loss.png) — SHA256 `00ea67abdb097c98fc87c94ce5dd41cc3b2bfd02c3657cfce828c2b7a663171d`

完整几何仅保留本地；以下文件真实存在，并已独立重载核验。所有 GLB 用米序列化，原始数据用毫米。

| 本地 GLB | 字节 | SHA256 | 状态 |
| --- | ---: | --- | --- |
| `/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/local_results/GLB/video004_single_video_complete_visible.glb` | 8289252 | `e09c35a71a6d2d2403f152ec69a14fef5919cdd6b292ae5275231ab9012b2530` | SINGLE_VIDEO_COMPLETE_OPEN_MULTISOURCE_NOT_GEOMETRY_CERTIFIED |
| `/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/local_results/GLB/video005_single_video_complete_visible.glb` | 7344900 | `dc0b5c8d037e0ec6cf0e27586c988022146f981e0187c207e0883c4784709e69` | SINGLE_VIDEO_COMPLETE_OPEN_MULTISOURCE_NOT_GEOMETRY_CERTIFIED |
| `/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/local_results/GLB/video004_video005_registration_candidate.glb` | 15050900 | `5aa7fb747bec29c38903a3e94166530c50e5332a48a004a183b54fe9adf00d92` | CROSS_VIDEO_REGISTRATION_CANDIDATE_NOT_FUSED |

每场景本地图像、实际 XYZ/RGB、来源及诊断相机：

- `/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/local_results/visualizations/video004`：Layers_L1-L5、Camera_3Views、XYZ_3Views、Real_vs_3D、Local_3D_Scene、actual_XYZ_RGB.npz、diagnostic_cameras_exact.npz。
- `/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/local_results/visualizations/video005`：Layers_L1-L5、Camera_3Views、XYZ_3Views、Real_vs_3D、Local_3D_Scene、actual_XYZ_RGB.npz、diagnostic_cameras_exact.npz。
- `/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/local_results/visualizations/004_plus_005_candidate`：Layers_L1-L5、Camera_3Views、XYZ_3Views、Real_vs_3D、Local_3D_Scene、actual_XYZ_RGB.npz、diagnostic_cameras_exact.npz。

真实 A→B 的原图、两类预测、叠加、差异、XYZ 及逐像素来源：`local_results/D1_evaluation/`。历史 B/C 对照：`local_results/D0_evaluation/`。全部实际文件见 CSV 索引；完整图像、NPZ、GLB 均未批量上传。

已完成增量提交（本索引所在最终文档提交 SHA 由 Git 历史及最终交付回执提供，避免自引用）：

- `45d8cc5cf78d741eb22d98cd058252a8665308e9 Phase D: preserve multireference scenes, diagnose bounded registration, publish four real review figures`
- `fe9e045aadaac8de49d6d8ea0e897abb866bf4f9 Phase D: record explicit research authorization and freeze bounded source-aware protocol`
