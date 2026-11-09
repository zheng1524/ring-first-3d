# RESULT_INDEX

- [技术报告摘要](TECHNICAL_REPORT_SUMMARY.md)、[失败记录](FAILURE_LEDGER.md)、[B0 判断](B0_REVIEW.md)。
- [初始化全组图](figures/Fig1_All11_Initializers_And_Updates.png)、[五例 Ip 图](figures/Fig2_All5_Ip_Stalk_Comparison.png)、[真实机制图](figures/Fig3_Current_Coverage_Gradient_And_Motion.png)、[全组刚性评价图](figures/Fig4_All11_Rigid_Aligned_GT_Comparison.png)。
- `figures/phase_A/`：11例真实输入/三种初始化/更新/留出投影；`figures/phase_B/`：5例 Ip 三路线；`figures/details/`：六视图及真实执行位移箭头。
- `review_meshes/Gxx/`：全部 81 个原始毫米 Mesh 的精确 NPZ 几何副本；另有 11 个 `BODY_FINAL_mm.ply` FIT-only 候选，不据 GT 改选。原始几何身份核对见 [复制索引](metrics/REVIEW_MESH_COPY_INDEX.json)。
- [完整本地 Mesh、优化器检查点绝对路径](metrics/RESULT_INDEX.json)；每个 `arms/路线/local_results/Gxx/FINAL.pt` 保留优化器、参数和随机/采样状态；同目录 STEP/MECHANISM 保存中间状态。严格冻结后不在此目录恢复更新，迁移需派生新目录并校验哈希。
- [逐预测评价](metrics/BLENDER_GEOMETRIC_METRICS.csv)、[SE3 变换](metrics/BLENDER_RIGID_ALIGNMENT.csv)、[路线统计](metrics/GT_ROUTE_SUMMARIES.csv)、[配对比较](metrics/COMMON_SUCCESS_PAIRED_COMPARISONS.csv)、[原坐标观测指标](metrics/ALL_NATIVE_FLAT.csv)。
- 本地评价副本 `local_results/aligned/Gxx/`；源预测不改动。GT 原始资产和大型检查点不上传 GitHub，来源及 SHA 在 provenance/evaluation_only 索引中，复现见 REPRODUCE.md。
