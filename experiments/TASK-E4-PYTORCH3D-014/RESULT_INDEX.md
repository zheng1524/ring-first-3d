# 结果索引

- [Fig10_All_Groups_Best_Rigid_Alignment.png](figures/Fig10_All_Groups_Best_Rigid_Alignment.png)
- [Fig1_All_Groups_Camera_Partitions.png](figures/Fig1_All_Groups_Camera_Partitions.png)
- [Fig2_G01_Video_Pose_Correction.png](figures/Fig2_G01_Video_Pose_Correction.png)
- [Fig3_G01_Video_Stability.png](figures/Fig3_G01_Video_Stability.png)
- [Fig4_G02_Missing_Extra.png](figures/Fig4_G02_Missing_Extra.png)
- [Fig5_G03_Actual_Recovery_Process.png](figures/Fig5_G03_Actual_Recovery_Process.png)
- [Fig6_G03_Adaptive_Refinement.png](figures/Fig6_G03_Adaptive_Refinement.png)
- [Fig7_G07_G11_Detailed_Review.png](figures/Fig7_G07_G11_Detailed_Review.png)
- [Fig8_View_Count_2D_3D.png](figures/Fig8_View_Count_2D_3D.png)
- [Fig9_Contour_Loss_Ablation.png](figures/Fig9_Contour_Loss_Ablation.png)

最终原始模型：meshes/Gxx/FINAL014_mm.npz；可审阅模型：review_models/Gxx/FINAL014_mm.ply、FINAL014_scene_m.glb。NPZ/PLY为mm，GLB仅展示转换为m。

全部阶段：arms/<condition>/local_results/Gxx/；FINAL.pt包含参数、Adam、随机状态、迭代与配置。源文件哈希、绝对路径及字节数见provenance/LOCAL_CHECKPOINT_AND_MESH_INDEX.json；输入视频/HERO/权重不复制上传。

统一指标：VIEW_COUNT_ABLATION.csv / LOSS_ABLATION.csv / MESH_REFINEMENT_ABLATION.csv / PER_VIEW_METRICS.csv / BLENDER_ALIGNMENT_METRICS.csv。

## 详细图与诊断

- [Candidate_RGB_Mask_Atlas.png](figures/details/Candidate_RGB_Mask_Atlas.png)
- [G01_Pure_Body_Six_Views.png](figures/details/G01_Pure_Body_Six_Views.png)
- [G02_Pure_Body_Six_Views.png](figures/details/G02_Pure_Body_Six_Views.png)
- [G03_Pure_Body_Six_Views.png](figures/details/G03_Pure_Body_Six_Views.png)
- [G04_Pure_Body_Six_Views.png](figures/details/G04_Pure_Body_Six_Views.png)
- [G05_Pure_Body_Six_Views.png](figures/details/G05_Pure_Body_Six_Views.png)
- [G06_Pure_Body_Six_Views.png](figures/details/G06_Pure_Body_Six_Views.png)
- [G07_Pure_Body_Six_Views.png](figures/details/G07_Pure_Body_Six_Views.png)
- [G08_Pure_Body_Six_Views.png](figures/details/G08_Pure_Body_Six_Views.png)
- [G09_Pure_Body_Six_Views.png](figures/details/G09_Pure_Body_Six_Views.png)
- [G10_Pure_Body_Six_Views.png](figures/details/G10_Pure_Body_Six_Views.png)
- [G11_Pure_Body_Six_Views.png](figures/details/G11_Pure_Body_Six_Views.png)
- [Intermediate_G01_G03_Final_Predictions.png](figures/details/Intermediate_G01_G03_Final_Predictions.png)
- [Intermediate_G03_C_Actual_Controls.png](figures/details/Intermediate_G03_C_Actual_Controls.png)
- [Intermediate_G03_E_Actual_Controls.png](figures/details/Intermediate_G03_E_Actual_Controls.png)
- [Observed_vs_Unknown_Regions.png](figures/details/Observed_vs_Unknown_Regions.png)
- [Unit_Direction_Coverage.png](figures/details/Unit_Direction_Coverage.png)

逐病例：[PER_CASE_ANALYSIS.md](PER_CASE_ANALYSIS.md)；[G03机制诊断](G03_FAILURE_DIAGNOSIS.md)。数值底噪和原阈值失败：[GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv)。视频稳定性：[G01_VIDEO_STABILITY_AND_COVERAGE.csv](metrics/G01_VIDEO_STABILITY_AND_COVERAGE.csv)。

LOCAL_CHECKPOINT_AND_MESH_INDEX包含全部初始、接受检查点、FINAL、拒绝示例和机制数组的绝对路径、SHA及字节数。PREFLIGHT是资源/接口预检，不能计入134个正式条件/对照或11个物理组的分母。
