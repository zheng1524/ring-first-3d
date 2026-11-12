# 结果索引

[摘要](TECHNICAL_REPORT_SUMMARY.md) · [完整技术报告](TECHNICAL_REPORT.md) · [五方案表](FOUR_GROUP_POSE_COMPARISON.csv) · [共同成功集合](metrics/PAIRED_COMMON_VIEW_COMPARISONS.csv) · [失败70条](metrics/FAILED_CAMERA_ROUTES.csv) · [当前暂停原因](STAGE_GATE_DECISION.json)

- [Figure1_Actual_Validation_and_Runs](figures/Figure1_Actual_Validation_and_Runs.png)
- [Figure2_Four_Group_Real_RGB_P0_S0_A1_A2_A3](figures/Figure2_Four_Group_Real_RGB_P0_S0_A1_A2_A3.png)
- [Figure3_Four_Group_Metric_Cameras](figures/Figure3_Four_Group_Metric_Cameras.png)
- [Figure4_Real_CAD_Completeness_Failure](figures/Figure4_Real_CAD_Completeness_Failure.png)

各帧公制相机矩阵：results/{group}/{method}/{canonical_id}/FINAL.json；原始初始化分支initialization/{group}/{id}.json；实际TRF轨迹optimization同层级。原HERO反事实诊断、固定/共同/新增/丢失分母在FROZEN_DEPTH_COUNTERFACTUAL。HOLDOUT均未局部拟合。照片阶段未运行，无新照片相机/深度产物。
