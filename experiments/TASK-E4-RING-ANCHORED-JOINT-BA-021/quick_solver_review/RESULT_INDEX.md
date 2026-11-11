# 快速复核结果索引

[摘要](TECHNICAL_REPORT_SUMMARY.md) · [完整求解器报告](SOLVER_REVIEW_REPORT.md) · [方法审计](METHOD_AND_LOSS_AUDIT.md) · [失败台账](FAILURE_LEDGER.md)

- [Figure_A_Mature_Solver_Review](figures/Figure_A_Mature_Solver_Review.png)
- [Figure_B_Independent_Photo_Ring_And_CAD](figures/Figure_B_Independent_Photo_Ring_And_CAD.png)
- [Figure_C_Photo_Video_Camera_Geometry](figures/Figure_C_Photo_Video_Camera_Geometry.png)
- [Figure_D_Photo_Geometry_Readiness](figures/Figure_D_Photo_Geometry_Readiness.png)
- [Photo_Heldout_RGB_Reprojection_Evidence](figures/Photo_Heldout_RGB_Reprojection_Evidence.png)

[12张照片资产与SHA](INDEPENDENT_PHOTO_ASSET_MANIFEST.csv) · [G01相机审计](G01_PHOTO_POSE_AUDIT.md) · [HERO准备](G01_PHOTO_HERO_AUDIT.md) · [71候选视角表](ALL_VIEW_BODY_ADAPT_READINESS.csv) · [未来单主体方案](ALL_VIEW_BODY_ADAPT_PLAN.md)

数值位姿与候选链：results/photos/G01_photo00*/，原RGB对应与特征ID：photo_features/、ALL_RGB_LANDMARK_MATCHES.json、RGB2D_PER_VIEW_AUDIT；BA目标调用与实际迭代：optimization/；独立原生共同集合：metrics/HERO_EXACT_COMMON_GAINED_LOST.csv。

当前完整本地二进制/失败隔离索引见assets_index/LOCAL_ARTIFACTS.json；原始JPG/视频/权重未复制上传。照片HERO原生文件不存在，不列作成功产物。
