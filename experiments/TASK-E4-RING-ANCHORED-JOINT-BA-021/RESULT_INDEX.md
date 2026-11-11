# 021 结果索引

| item | path |
| --- | --- |
| 完整报告/方法/失败 | TECHNICAL_REPORT_SUMMARY.md / TECHNICAL_REPORT.md / METHOD_AND_INPUT_AUDIT.md / FAILURE_LEDGER.md |
| 四份独立定量报告 | G01_GEOMETRY_AUDIT.md / G03_GEOMETRY_AUDIT.md / G05_GEOMETRY_AUDIT.md / G06_GEOMETRY_AUDIT.md |
| 统一量化与决策 | FOUR_GROUP_GEOMETRY_SCORECARD.csv / FOUR_GROUP_RESEARCH_DECISION.md |
| 18真实身份/553像素/描述子 | observations/CROSS_COMMON_TRACKS.json / CROSS_PIXEL_DESCRIPTOR_INDEX.csv / CROSS_DESCRIPTORS.npz |
| 输入来源与SHA | config/FOUR_GROUP_INPUTS.json / provenance/UPSTREAM_READONLY.json / ADDITIONAL_CAMERA_SOURCE_AUDIT.json |
| 全部矩阵与优化X | results/*.json / optimization/*/FINAL.json / HISTORY.json / ITER_*.pt |
| B1/B2/B3全部68派生相机 | derived/ALL68_CAMERAS_B*.json / T004_from005_B*.json |
| 全部005逐帧/双向SIFT | metrics/ALL005_FRAME_METRICS.csv / SIFT_READABLE_SUMMARY.csv / SIFT_ALL68_PER_VIEW.csv / UNUSED_SIFT_TRACK_EVALUATION.json |
| Schur信息/点漂移/初值/影子 | metrics/BA_IDENTIFIABILITY.json / COMMON_POINT_MOVEMENT.csv / INITIALIZATION_SENSITIVITY.json / ENDPOINT_SHADOW_PROPOSALS.csv |
| 同视频负对照 | metrics/NEGATIVE_CONTROL.json / NEGATIVE_PER_VIEW.csv |
| 21源跨视频HERO固定分母与严格共同集合 | metrics/HERO_INDEPENDENT_PER_PAIR.csv / HERO_EXACT_CROSS_METHOD_COMMON.csv / HERO_EXACT_COMMON_GAINED_LOST.csv / HERO_MULTILAYER_NATIVE_RAY_PROXY.csv |
| 四组完整逐源/逐面/原生Pixel ID | metrics/groups/ / evaluation/groups/*/*SOURCE_EVIDENCE.npz / *_RING_MATERIAL.npz / *_BODY_FACE_MM_ERROR.npz |
| 其他视频轻量清点 | metrics/OTHER_VIDEO_ASSET_INVENTORY.json/csv |
| 大文件路径/SHA | assets_index/LOCAL_RESULTS.json |

## 八张核心图

[全部18条实际RGB身份审计](figures/All18_Actual_RGB_Track_Identity_Audit.png)。

- [Fig1_020_Named_Track_Problem](figures/Fig1_020_Named_Track_Problem.png)
- [Fig2_Common_BA_Actual_Mechanism](figures/Fig2_Common_BA_Actual_Mechanism.png)
- [Fig3_B0_B3_Pose_And_Residuals](figures/Fig3_B0_B3_Pose_And_Residuals.png)
- [Fig4_Crossvideo_Actual_Reprojection](figures/Fig4_Crossvideo_Actual_Reprojection.png)
- [Fig5_G01_Crossvideo_Actual_Geometry](figures/Fig5_G01_Crossvideo_Actual_Geometry.png)
- [Fig6_G03_Stalk_And_Source_Geometry](figures/Fig6_G03_Stalk_And_Source_Geometry.png)
- [Fig7_G05_Body_Base_And_HERO](figures/Fig7_G05_Body_Base_And_HERO.png)
- [Fig8_G06_Local_Deformation_And_Ring](figures/Fig8_G06_Local_Deformation_And_Ring.png)

## 四组完整图集与本地GLB

- [G01定量审计](G01_GEOMETRY_AUDIT.md) · [六视角](figures/groups/G01/Six_View_HERO_Body_Evidence.png) · [主体毫米误差](figures/groups/G01/Body_Surface_Native_Depth_Error_mm.png) · GLB：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/derived/G01/G01_INDEPENDENT_LAYERS_NOT_FUSION.glb`；独立图层与全部源SHA见`derived/G01/SOURCE_LAYER_INDEX.json`。
- [G03定量审计](G03_GEOMETRY_AUDIT.md) · [六视角](figures/groups/G03/Six_View_HERO_Body_Evidence.png) · [主体毫米误差](figures/groups/G03/Body_Surface_Native_Depth_Error_mm.png) · GLB：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/derived/G03/G03_INDEPENDENT_LAYERS_NOT_FUSION.glb`；独立图层与全部源SHA见`derived/G03/SOURCE_LAYER_INDEX.json`。
- [G05定量审计](G05_GEOMETRY_AUDIT.md) · [六视角](figures/groups/G05/Six_View_HERO_Body_Evidence.png) · [主体毫米误差](figures/groups/G05/Body_Surface_Native_Depth_Error_mm.png) · GLB：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/derived/G05/G05_INDEPENDENT_LAYERS_NOT_FUSION.glb`；独立图层与全部源SHA见`derived/G05/SOURCE_LAYER_INDEX.json`。
- [G06定量审计](G06_GEOMETRY_AUDIT.md) · [六视角](figures/groups/G06/Six_View_HERO_Body_Evidence.png) · [主体毫米误差](figures/groups/G06/Body_Surface_Native_Depth_Error_mm.png) · GLB：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/derived/G06/G06_INDEPENDENT_LAYERS_NOT_FUSION.glb`；独立图层与全部源SHA见`derived/G06/SOURCE_LAYER_INDEX.json`。

G01同尺度阶段对照：[RoMa→020R3→021B3](figures/groups/G01/Before020_After020_After021.png)。G03额外[新增首层错误诊断](figures/groups/G03/New_First_Hits_Are_Not_Correct_Surface.png)，逐射线原生ID见G03_NEW_HIT_FAILURE_LOCATIONS.csv。全部图层保持原面；不是融合Mesh。GLB/大数组未强制上传，完整本地路径和SHA均在索引。
