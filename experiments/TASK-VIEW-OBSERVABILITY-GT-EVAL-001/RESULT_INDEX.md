# 结果入口

任务：TASK-VIEW-OBSERVABILITY-GT-EVAL-001，四物理组、五已有局部场景；22完整重投影（14同视频、2跨视频候选、6照片目标候选），另88个来源方向因缺失/未注册不执行。没有新重建/融合/训练。

本地根目录：`/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001`  
[完整技术报告](/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/TECHNICAL_REPORT.md) · [直接打开HTML图库](/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/visualizations/index.html) · [本地图像目录](/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/figures/) · [本地所有A→B](/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/figures/A_to_B/)

GitHub实验：[目录](https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001)。完整XYZ/GT/射线缓存及其余图像为LOCAL_ONLY，不能称已公开同步。

公开核心图：

1. [五来源相机/轨迹/方向/连接图](figures/G01_camera_view_coverage.png)
2. [四组来源支持与冲突](figures/G01_source_surface_support.png)
3. [标准五面板：好/有限/压力案例](figures/A_to_B_core_review.png)
4. [高度与Dxy形状GT条件评价](figures/GT_metric_summary.png)

[GT身份与配对](metrics/gt_asset_manifest.csv) · [高度27条件](metrics/gt_height_evaluation.csv) · [Dxy81条件](metrics/gt_dxy_evaluation.csv) · [独立组固定条件统计](metrics/gt_group_prespecified.csv) · [全部21来源](metrics/source_view_inventory.csv) · [62相机帧](metrics/camera_frame_inventory.csv) · [480对视角/来源](metrics/view_pairwise_metrics.csv) · [来源支持](metrics/source_surface_support.csv) · [110条A→B候选/缺失清单](metrics/a_to_b_pair_inventory.csv) · [22实测结果](metrics/a_to_b_results.csv) · [12同视频有向深度冲突](metrics/within_video_depth_conflicts.csv) · [本地资产SHA](metrics/local_asset_index.csv)。

[高度分报告](reports/GT_HEIGHT_EVALUATION.md) · [Dxy分报告](reports/GT_DXY_EVALUATION.md) · [GT审计](reports/GT_EVALUATION_REPORT.md) · [融合失败定义](reports/FUSION_ACCEPTANCE_DEFINITION.md) · [顶层设计者交接](research/TOP_LEVEL_RESEARCH_HANDOFF.md) · [复现](REPRODUCE.md)。

完整每张A→B图文件名、NPZ、输入SHA、数值均见`metrics/a_to_b_results.csv`；本地HTML直接展示全部22图。上轮10个GLB保持原路径不改：[上轮索引](/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/RESULT_INDEX.md)。本轮不生成新的融合GLB。
