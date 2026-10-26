# 全部结果索引

任务状态：工程完成；最终9视频均保留Raw；自动清理和跨视频认证未成功。GT=NONE。

[技术报告](TECHNICAL_REPORT.md) · [视频决策](metrics/P1_video_decisions.csv) · [005验收](metrics/P1_005_acceptance.csv) · [P2指标](metrics/P2_results.csv) · [P3指标](metrics/P3_results.csv)

## 公开核心图片（4+3+3）

- [FigP1_004_spatial_trials](figures/FigP1_004_spatial_trials.png)
- [FigP1_005_spatial_trials](figures/FigP1_005_spatial_trials.png)
- [FigP1_crossgroup_counterexamples](figures/FigP1_crossgroup_counterexamples.png)
- [FigP1_damage_and_failure](figures/FigP1_damage_and_failure.png)
- [FigP2_004_crossframe](figures/FigP2_004_crossframe.png)
- [FigP2_005_crossframe](figures/FigP2_005_crossframe.png)
- [FigP2_support_and_failure](figures/FigP2_support_and_failure.png)
- [FigP3_004_crossframe](figures/FigP3_004_crossframe.png)
- [FigP3_005_crossframe](figures/FigP3_005_crossframe.png)
- [FigP3_support_and_failure](figures/FigP3_support_and_failure.png)

## 本地完整输出

完整目录：`/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/local_results`。以下文件未公开，具体文件及SHA见[LOCAL_ASSET_INDEX.csv](metrics/LOCAL_ASSET_INDEX.csv)。

| 参考 | 原点N | L1–L5 / 六方向 / 三状态本地目录 |
| --- | --- | --- |
| G01_004_ref03 | 24343 | `local_results/visuals/G01_004_ref03/` |
| G01_004_ref08 | 14029 | `local_results/visuals/G01_004_ref08/` |
| G01_004_ref13 | 13010 | `local_results/visuals/G01_004_ref13/` |
| G01_005_raw00057 | 19813 | `local_results/visuals/G01_005_raw00057/` |
| G01_005_raw00459 | 12775 | `local_results/visuals/G01_005_raw00459/` |
| G01_005_raw00745 | 14873 | `local_results/visuals/G01_005_raw00745/` |
| G02_004_ref04 | 3885 | `local_results/visuals/G02_004_ref04/` |
| G03_004_ref04 | 26966 | `local_results/visuals/G03_004_ref04/` |
| G04_004_ref04 | 3663 | `local_results/visuals/G04_004_ref04/` |
| G05_004_ref04 | 31600 | `local_results/visuals/G05_004_ref04/` |
| G06_004_ref04 | 9282 | `local_results/visuals/G06_004_ref04/` |
| G07_004_ref04 | 19784 | `local_results/visuals/G07_004_ref04/` |
| G08_005_ref04 | 19631 | `local_results/visuals/G08_005_ref04/` |

每参考`local_results/<id>/`保存Raw精确NPZ/PLY、T1/T2/T3（仅门控通过者）、GLOBAL50原索引/原面Mesh以及Final_Cleaned_exact.npz。P2/P3各A/candidate子目录保存透明预测/真实B/叠加/差异/侧视及逐像素源原点ID。没有原视频、权重或完整缓存上传。
