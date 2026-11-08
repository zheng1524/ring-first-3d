# 完整结果索引

大模型、原始RGB/Mask/HERO/视频/GT均不提交GitHub；以下本地路径与SHA索引供恢复。

运行根：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013`

关键图：figures/Fig1–Fig4；逐例详图：figures/full/；全部方法配置：config/PROTOCOL.json；最终选择：config/SELECTED_FINAL.json。

预测：local_results/G*/FINAL.npz（真实毫米顶点、原始面身份与底盖标签）、FINAL.pt（参数、优化器、随机状态和配置）；各接受里程碑同目录。

全部试跑：arms/PILOT_A*/、PILOT_O*/、COMBINED_VERIFY/；完整012重现：arms/REPLAY_012_FULL/；正式统一：arms/FINAL_UNIFORM/。

公制预测：local_results/metric/G*/FINAL011/012/013.npz；纯主体刚性对齐：local_results/aligned/G*/FINAL*.npz；T/最优与次优：metrics/BLENDER_RIGID_ALIGNMENT.json及metrics/alignment/；GT独立来源：evaluation_only/GT_SOURCE_LOCK.json。

新输入：new_input_pipeline/G10/groups/G10、G11/groups/G11；来源、帧和相机SHA：assets_index/与inputs/G*/CASE.json。

指标：metrics/NATIVE_SUMMARY.csv、PER_VIEW_METRICS.csv、BLENDER_GEOMETRIC_METRICS.csv、PAIRED_012_013.csv。历史冻结：assets_index/HISTORY_012_PROTECTION.json。

独立密集几何复核：metrics/DENSE_RING_AUDIT.csv、GEOMETRY_ACCEPTANCE.csv；完整性：metrics/DELIVERY_VALIDATION.json。小型可审阅模型：review_models/G*/，NPZ/PLY为mm、GLB为m；本地大检查点完整SHA索引：assets_index/LOCAL_RESULT_INDEX.json。每组最高点/最低点/跨度和完整方向误差均用同一最佳T。G03首个保存的远漏覆盖改善状态为accepted25（实际candidate25）；accepted10尚未达到，不能将该离散记录冒称精确生理柄部生成时刻。

GPU队列已完成；正式统一11例实际接受/候选次数分别保存在metrics/G*_RUN.json，全部合计2240/2650。正式FINAL模型SHA验证后未再更新。主结果7fa1766之后补充均为独立评价、图像、报告和失败记录。
