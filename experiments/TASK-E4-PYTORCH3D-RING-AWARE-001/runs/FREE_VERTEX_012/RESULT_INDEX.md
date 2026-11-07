# 结果索引

核心图：

- [Figure1 九例三阶段](figures/Fig1_Nine_Free_Vertex_Overview.png)
- [Figure2 三例Ip柄部专题](figures/Fig2_Three_Ip_Stalk_Review.png)
- [Figure3 实际接受更新过程](figures/Fig3_Free_Vertex_Update_Process.png)
- [Figure4 Ring尺度与Blender刚性对齐](figures/Fig4_Ring_Scale_and_Blender_Alignment.png)
- [Figure5 定量结果](figures/Fig5_Quantitative_Results.png)

[输入回执](02_INPUT_RECEIPT.md) · [原始GT来源/单位/算子](03_GT_SOURCE_AND_METRICS.md) · [轻量模型下载](review_models/README.md)

[G01历史静态参考](figures/full/G01_Historical_Static_Reference.png)仅展示，没有参与优化或输出替换。

九例完整原图与三阶段Mesh：

- [G01](figures/full/G01_Three_Stage_Detail.png)
- [G02](figures/full/G02_Three_Stage_Detail.png)
- [G03](figures/full/G03_Three_Stage_Detail.png)
- [G07](figures/full/G07_Three_Stage_Detail.png)
- [G04](figures/full/G04_Three_Stage_Detail.png)
- [G05](figures/full/G05_Three_Stage_Detail.png)
- [G06](figures/full/G06_Three_Stage_Detail.png)
- [G08](figures/full/G08_Three_Stage_Detail.png)
- [G09](figures/full/G09_Three_Stage_Detail.png)

本地绝对根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_012`。

每例起点`inputs/Gxx/INITIAL.npz`为011 FINAL；`C_011.npz`为011 C。新结果`local_results/Gxx/FINAL.npz/.pt/FINAL_mm.ply`，实际达到的ACCEPTED_N与提案检查点同目录。V均为原生世界毫米，F_solid中的inferred_base_faces为单独推断底盖，不能当真实可见面。

`local_results/metric/Gxx`为CAD尺度锁定后几何，`local_results/aligned/Gxx`为仅评价用6DoF派生几何；不覆盖原预测或相机。GT主体和原始来源/单位记录在evaluation_only，不上传大型原始场景。

原始相机指标`NATIVE_WITH_GEOMETRY`/`PER_VIEW_METRICS`，配准矩阵`BLENDER_RIGID_ALIGNMENT`，Dxy/高度/IoU/表面距离`BLENDER_GEOMETRIC_METRICS`，原始GT有效性`GT_VALIDITY`，分母/误差统计`MEASUREMENT_SUMMARY`，共同九例配对`PAIRED_011_012`，原生/作者基底差异与含盖诊断`BASE_AND_SURFACE_DIAGNOSTICS`。

可直接下载[轻量审阅模型](review_models/README.md)：九例各含C011、FINAL011、FINAL012毫米PLY、黑色Ring CAD及012带Ring的交互GLB（标准米单位）。MODEL_SEMANTICS记录底盖面ID与原始NPZ来源。精确模型/checkpoint和完整候选日志仍在本地，路径/大小/SHA见assets_index/LOCAL_RESULTS_INDEX.json；大型原始模型/视频/环境不上传，完整重跑需要按索引恢复本地数据。
