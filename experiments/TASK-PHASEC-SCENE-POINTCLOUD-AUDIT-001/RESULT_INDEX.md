# 全部场景结果索引

本轮仅展示与几何现象审计，GT=NONE，准确性=NOT_EVALUABLE。5视频、5参考、4独立物理组；G01两视频不是两个物理样本。全部20张PNG均为实际输出。完整XYZ/RGB点层仅保存在本地。

| 场景 / 原始参考 | 五层（RGB/深度） | 近相机三视角 | Ring XYZ三视角 | 同相机真实帧比较 |
|---|---|---|---|---|
| G01_004 004_03 raw303 / NORMAL_CONDITIONAL | [L1–L5](figures/G01_004/Layers_L1-L5.png) | [RGB/深度](figures/G01_004/Camera_3Views.png) | [RGB/深度](figures/G01_004/XYZ_3Views.png) | [L5](figures/G01_004/Real_vs_3D.png) |
| G01_005 v005_00057 raw57 / NORMAL_CONDITIONAL | [L1–L5](figures/G01_005/Layers_L1-L5.png) | [RGB/深度](figures/G01_005/Camera_3Views.png) | [RGB/深度](figures/G01_005/XYZ_3Views.png) | [L5](figures/G01_005/Real_vs_3D.png) |
| G04_004 key04_raw00437 raw437 / UNQUALIFIED_STRESS | [L1–L5](figures/G04_004/Layers_L1-L5.png) | [RGB/深度](figures/G04_004/Camera_3Views.png) | [RGB/深度](figures/G04_004/XYZ_3Views.png) | [L5](figures/G04_004/Real_vs_3D.png) |
| G06_004 key04_raw00596 raw596 / NORMAL_CONDITIONAL | [L1–L5](figures/G06_004/Layers_L1-L5.png) | [RGB/深度](figures/G06_004/Camera_3Views.png) | [RGB/深度](figures/G06_004/XYZ_3Views.png) | [L5](figures/G06_004/Real_vs_3D.png) |
| G07_004 key04_raw00369 raw369 / UNQUALIFIED_STRESS | [L1–L5](figures/G07_004/Layers_L1-L5.png) | [RGB/深度](figures/G07_004/Camera_3Views.png) | [RGB/深度](figures/G07_004/XYZ_3Views.png) | [L5](figures/G07_004/Real_vs_3D.png) |

[技术报告](TECHNICAL_REPORT.md) · [点数与来源](metrics/stage_counts.csv) · [场景指标](metrics/scene_summary.csv) · [背景范围](metrics/background_ranges.csv) · [实际验证](metrics/VALIDATION.json) · [图片哈希](provenance/FIGURE_MANIFEST.json)

本地点层：`/home/liu/ring_first_3d_scene_vis/experiments/TASK-PHASEC-SCENE-POINTCLOUD-AUDIT-001/local_layers/<scene>/Layers_L1-L4_XYZ_RGB.npz`；完整反投影背景为同目录 `Raw_Background_FULL.npz`。未公开上传全量点层、源图像、视频或模型。
