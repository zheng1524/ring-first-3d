# TASK-AB-FULL-SCENE-VIS-002 结果索引

本地绝对目录：`/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002`

[直接打开HTML图库](/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002/visualizations/index.html) · [完整案例文件夹](/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002/figures/cases/) · [本地报告](/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002/TECHNICAL_REPORT.md) · [复现](REPRODUCE.md)。图库按G01/G06/G08/G07和角度排序，包含11张五面板、11张高分辨率Real_B_vs_Full_AtoB_Scene.png、11张侧/斜视和A/B相机关系图；所有大图LOCAL_ONLY。

公开核心图：

1. [双向跨视频22.60°/23.25°完整场景](figures/Fig1_G01_crossvideo_full_scenes.png)
2. [photo003 39.29°候选与失败](figures/Fig2_photo003_large_angle_candidate.png)
3. [G06/G08/G07三组统一诊断](figures/Fig3_multigroup_full_scene_diagnostics.png)
4. [同配对旧/新版完整对照](figures/Fig4_old_new_same_pair.png)

[旧Polyp-only指标](metrics/legacy_polyp_metrics.csv) · [新点云场景独立指标](metrics/scene_point_metrics.csv) · [逐项结果及大图路径](metrics/results.json) · [大角度限制](metrics/large_angle_summary.csv) · [实际源帧/坐标](metrics/source_coordinate_inventory.csv) · [冻结选帧](metrics/pair_selection.csv) · [渲染器版本SHA](provenance/RENDERER_VERSIONS.json) · [本地资产SHA](metrics/LOCAL_ASSET_INDEX.csv)。

公开目录：https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-AB-FULL-SCENE-VIS-002/experiments/TASK-AB-FULL-SCENE-VIS-002 。背景是冻结预测XYZ、DISPLAY_ONLY，跨源关系仍CANDIDATE；不是融合或重建性能改善。
