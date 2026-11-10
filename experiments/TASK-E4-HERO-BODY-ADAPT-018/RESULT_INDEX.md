# 018 结果索引

本地根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018`。

- [简洁技术报告](TECHNICAL_REPORT_SUMMARY.md)
- [完整技术报告](TECHNICAL_REPORT.md)
- [原始任务书](TASK.md)
- [算法/输入逐项审计](METHOD_AND_INPUT_AUDIT.md)
- [失败台账](FAILURE_LEDGER.md)
- [43视角清单](VIEW_HERO_COMPLETENESS_MANIFEST.csv)
- [全部来源面积/类别/连通性](metrics/ALL_SOURCE_AREAS_LABELS_AND_CONTINUITY.csv)
- [全部方法四组比较](evaluation/metrics/COMPARISON.csv)
- [逐参考指标](evaluation/metrics/PER_VIEW.csv)
- [逐组池化原生残差分位数](evaluation/metrics/POOLED_NATIVE_DEPTH_RESIDUALS.csv)
- [严格原生ID共同/新增/丢失命中](evaluation/metrics/EXACT_PAIRED_NATIVE_CORRESPONDENCES.csv)
- [原生HERO逐来源冲突](evaluation/metrics/SOURCE_CONFLICT_DIAGNOSTIC.csv)
- [未命中全局最近点风险诊断](evaluation/metrics/NO_HIT_POINT_MESH_FEASIBILITY.csv)
- [逐分量实际梯度](metrics/PER_VIEW_ACTUAL_GRADIENTS.csv)
- [运行/拒绝及损失汇总](metrics/OPTIMIZATION_PROCESS_SUMMARY.csv)
- [全输入/真实Face子集测试](metrics/INPUT_AND_NATIVE_SUBSET_TESTS.json)
- [官方P3D投影与完整参数梯度门禁](metrics/P3D_HERO_PROJECTION_GRADIENT_GATE.json)
- [原Raw离散化与原生深度差诊断](metrics/RAW_DISCRETIZATION_VS_NATIVE_DIAGNOSTIC.csv)
- [完整本地模型/输入/checkpoint路径及SHA](RESULT_INDEX.json)
- [复现与严格恢复](REPRODUCE.md)

各组核心共享主体：

|组|本地相对路径|实际迭代/接受|
|---|---|---:|
|G06|`arms/B2_TRUSTED_COH16/local_results/G06/FINAL_mm.ply`|43/40|
|G05|`arms/B2_TRUSTED_COH16/local_results/G05/FINAL_mm.ply`|40/40|
|G01|`arms/B2_TRUSTED_COH16/local_results/G01/FINAL_mm.ply`|40/40|
|G03|`arms/B2_TRUSTED_COH16/local_results/G03/FINAL_mm.ply`|40/40|

同一目录下的FINAL.npz有V/F/F_solid、推断底盖、边界顶点、参数与实际接受步数；FINAL.pt有Adam、随机状态及配置。INITIAL、ACCEPTED_0001/0010/0020/0040和ATTEMPT检查点完整保留。G06 B1因规则停止于39次，没有虚构第40个接受模型。

原生来源与Face标签：`hero_fit/<view_id>/`、`holdout/hero/<view_id>/`，各有SOURCE.json、HERO_native.npz、Raw_open_mesh.ply、FACE_EVIDENCE.npz、TRUSTED_HERO.npz/ply、OBS_FULL.npz、OBS_TRUSTED.npz、ORIGINAL_FACE_NORMALS.npz。TRUSTED不是仅改变颜色，而是原Face ID真子集。

完整图：`figures/full/G06/`、`G05/`、`G01/`、`G03/`。核心图位于`figures/Fig1...Fig5...png`；所有原始三维坐标保留，无ICP、尺度调整或几何后处理。
