# RESULT_INDEX

- TECHNICAL_REPORT_SUMMARY.md：结论、审计表、局限和下一步资格。
- TECHNICAL_REPORT.md：全源分母和科学失败解释。
- METHOD_AND_INPUT_AUDIT.md：公式、历史复用及实际实现差异。
- metrics/FINAL_SOURCE_SUMMARIES.csv、GROUP_SUMMARY.csv：逐源/逐组原面数、面积、连通与覆盖。
- metrics/RULE_BLOCKING_ATTRIBUTION.csv、PATCH_FAILURE_ATTRIBUTION.csv：为何异常没有删除。
- metrics/TWO_SIDED_GAP/：每条测试边的来源、原生像素ID、端点、外推误差与原因。
- face_decisions/*.csv.gz：全部原面最终分类、理由文字、原点和native Pixel ID、邻面状态；REASON_CODEBOOK.json是位码合同。
- final_results/<source>/ARCHIVE_RAW/FACE_EVIDENCE.npz：原始V/F、所有逐面异常指标、状态、原Face/Pixel身份。
- final_results/<source>/ARCHIVE_RAW/CLEANED_SUBSET.npz / CLEANED.ply：真正清理输出，原面子集、坐标精确不变；本轮0删，故等于原面集合。
- final_results/*/NATIVE_GRID：仅原深度网格证据诊断，不作为主体适配输入或新的重建结果。
- local_results：初始PCA诊断负结果及其完整逐面指标/CSV，不覆盖。
- figures/Fig1–Fig4：四类原始Raw Mesh主图；figures/full：18来源各两图；figures/local_archive：原Raw Face ID局部证据。
- figures/diagnostic_native_grid：原深度格完整范围诊断图；编号和面积不能与Raw原面混淆。
- RESULT_INDEX.json：逐文件本地绝对路径、SHA与原source几何索引。

精确完整几何/证据NPZ保留本地；Git提交代码、配置、核心/逐源图、小表和完整压缩逐面决策。未上传大原始模型、视频或环境。未修改DXY/016/015及原始相机/HERO/Mask/CAD。
