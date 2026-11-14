# 结果索引

[技术摘要](TECHNICAL_REPORT_SUMMARY.md) · [完整报告](TECHNICAL_REPORT.md) · [相机总表](FOUR_GROUP_POSE_SCORECARD.csv) · [HERO总表](HERO_SURFACE_ALIGNMENT_SCORECARD.csv)

- [Figure1_Actual_Unified_BA](figures/Figure1_Actual_Unified_BA.png)
- [Figure2_Four_Group_Ring_Projection](figures/Figure2_Four_Group_Ring_Projection.png)
- [Figure3_Four_Group_Actual_Cameras](figures/Figure3_Four_Group_Actual_Cameras.png)
- [Figure4_G01_Real_HERO_Before_Shared_Joint](figures/Figure4_G01_Real_HERO_Before_Shared_Joint.png)
- [Figure5_Actual_HERO_Layer_Zoom](figures/Figure5_Actual_HERO_Layer_Zoom.png)
- [Figure6_Native_HERO_Evidence_Heatmap](figures/Figure6_Native_HERO_Evidence_Heatmap.png)
- [Figure7_Four_Group_All_Native_HERO](figures/Figure7_Four_Group_All_Native_HERO.png)
- [Figure8_Frozen_Independent_Geometry_Metrics](figures/Figure8_Frozen_Independent_Geometry_Metrics.png)
- [G01_SIX_VIEW_ATLAS](figures/G01_SIX_VIEW_ATLAS.png)
- [G03_SIX_VIEW_ATLAS](figures/G03_SIX_VIEW_ATLAS.png)
- [G05_SIX_VIEW_ATLAS](figures/G05_SIX_VIEW_ATLAS.png)
- [G06_SIX_VIEW_ATLAS](figures/G06_SIX_VIEW_ATLAS.png)

## 本地大型资产（未上传Git）

- G01：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001/local_results/interactive/G01_CAMERA_HERO_COMPARISON.glb`，18547860 bytes，SHA256 `cd2f2b6c41042b5e6e7db3e4fad8cff649bab0c17a1e51f157a8cd073e6879d2`；同目录 `G01_VIEWER.html`。
- G03：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001/local_results/interactive/G03_CAMERA_HERO_COMPARISON.glb`，13551392 bytes，SHA256 `c7dc90fdd168a065e0004bd295fddec8acfb1606adf8faed45a1d105a52fe219`；同目录 `G03_VIEWER.html`。
- G05：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001/local_results/interactive/G05_CAMERA_HERO_COMPARISON.glb`，17993248 bytes，SHA256 `74600f3e014792f98086ce5bed648578d87d6788d41f3ba0205908e2abf414af`；同目录 `G05_VIEWER.html`。
- G06：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001/local_results/interactive/G06_CAMERA_HERO_COMPARISON.glb`，5926356 bytes，SHA256 `aec03f8970f278f3f6d3514ce5a6e0a8b7d9008d6fd1d037ae9b5b9f6bbf6b91`；同目录 `G06_VIEWER.html`。

冻结相机：results/{group}/{B0,B1,B2,B3}/FINAL.json；B4原PENDING/初版NOT_RUN文件保留，当前结论读NOT_RUN_CORRECTED_EVALUATION_REASON和STAGE_DECISION。共同XYZ在B3 FINAL中；原始RGB轨迹及像素在config/TRACKS.json，描述子/图像原文件在输入SHA索引。外层拒绝原因、各次Ceres完整FullReport与真实日志在optimization。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；98 canonical视角=81FIT+17HOLDOUT。G01含004/005；其他三组只有004 |
| 本算法独立成功 | B1实际76个独立局部求解，另5个参考相机受保护；B2仅G01一个共享SE(3)求解；B3四个真实联合问题，76个五维局部相机块+一个六维H+1377个XYZ，数值输出不是绝对精度认证 |
| 本算法失败 | 无用旧位姿填充的失败预测；B4四组NOT_RUN，照片12/12 NOT_RUN；初次PyCeres冷调用崩溃保留，显式Jacobian预求值后实际组级运行完成；独立RGB科学可信性尚未建立（不是当前严重数值阈值FAIL） |
| 历史测量值回退 | 0；B0/参考相机/HOLDOUT是预登记对照或规范，不冒充新恢复结果。B2不适用的三组保持NaN/N/A，不复制B0 |
| 失败组及具体原因 | G01初版005地图评价坐标错误已纠正；当前未超过冻结严重退化阈值，但四组独立RGB仍有权衡；B3四组留出极线代理均增大；G01/G06旧深度相容性下降。见FAILURE_LEDGER、逐视角/逐来源CSV和Figure4–8 |
| 最终统计样本 | 全部4组完整保留；按每指标真实视角、轨迹或source-target像素分母统计；不把重复源观测当独立物理样本。真实GT测量MAE/MedARE/尺寸p95为NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；协议/输入/源码在运行前冻结，候选在HERO之前冻结；HOLDOUT不进目标，不按HERO选路线，保留预登记主初值而非较低损失的敏感性候选 |
