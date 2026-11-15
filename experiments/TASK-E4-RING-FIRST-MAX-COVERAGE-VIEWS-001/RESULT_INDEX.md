# 结果索引

- 总结：`TECHNICAL_REPORT_SUMMARY.md`；完整方法/结论：`TECHNICAL_REPORT.md`。
- 来源、相机、照片、覆盖：对应根目录的`*_AUDIT.md`、`*_REPORT.md`、`VIEW_COVERAGE_METHOD.md`。
- 全部884候选：`ALL_CAMERA_CANDIDATES.csv`；条件与失败：`CAMERA_QUALITY_AND_UNCERTAINTY.csv`及`metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv`。
- 全部最终位姿：`results/ALL_FINAL_METRIC_CAMERA_POSES.json`；实际Ceres参数、共同XYZ：`results/ACTUAL_CERES_FINAL_STATES.json`；历史命名候选：`results/HISTORICAL_SE3_CANDIDATES.json`。
- 目标与数量：`MAX_COVERAGE_VIEW_SELECTION.csv`、`VIEW_COUNT_ABLATION.csv`、`selection_verified/`；`selection/`仅初轮失败诊断。
- 三支持图：`HERO_SUPPORT_FRAME_SELECTION.csv`；47次原生来源：`NEW_HERO_SOURCE_MANIFEST.csv`。
- 几何分母/深度：`HERO_COVERAGE_AND_CONFLICT_SCORECARD.csv`、`metrics/HERO_PER_NATIVE_PAIR.csv`；实际覆盖及E5：`metrics/HERO_COUNT_ACTUAL_COVERAGE.csv`、`metrics/HERO_SOURCE_ACTUAL_CONTRIBUTIONS.csv`。
- E4：`metrics/E4_FIXED_COMMON_NATIVE_PIXEL_COMPARISON.json`；来源相关性：`metrics/HERO_RGB_SOURCE_DAG.csv`、`metrics/HERO_PAIR_UPSTREAM_CORRELATION.csv`。
- Ring/RGB竞争、可辨识性与规范：`metrics/RING_RGB_GRADIENT_COMPETITION.csv`、`metrics/CONDITIONAL_RGB_SCHUR_INFORMATION.json`、`metrics/EXACT_SOURCE_GAUGE_CANONICALIZATION.json`。
- 配准前后真实相机位移补图：`figures/Fig7b_Actual_Camera_Registration_Changes.png`；实际毫米向量：`metrics/ACTUAL_CAMERA_BEFORE_AFTER_VECTORS.json`（仅显示补充，未改预测）。
- 关键图：`figures/Fig1`至`Fig8`文件；四组`*_Six_View_Atlas.png`；`G03_Ring_Near_Local_Detail.png`。
- 交互图集：根目录`G01/G03/G05/G06_MAX_COVERAGE_VIEW_ATLAS.html`，配合`local_results/interactive`中的独立图层GLB；浏览器检查见`metrics/BROWSER_ATLAS_TESTS.json`。
- 新原始深度/Raw/四状态Mesh/Face与Pixel ID：`hero_fit/<SOURCE>/`；大文件不在Git，按`assets_index/SCIENTIFIC_OUTPUT_BUNDLE.json`及REPRODUCE.md取回。
- 全部失败与限制：`FAILURE_LEDGER.md`；下一阶段建议：`FOUR_GROUP_FINAL_RESEARCH_DECISION.md`。本轮不自动进入Body更新。
