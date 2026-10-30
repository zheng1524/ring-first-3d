# 本轮结果入口

[中文技术报告](TECHNICAL_REPORT.md) · [复现和只读核验](REPRODUCE.md) · [失败台账](FAILURE_LEDGER.md) · [本地HTML图库](visualizations/index.html)。科学状态：无有效双臂对照，不选赢家。

|核心图|内容|
|---|---|
|[Fig1](figures/Fig1_four_group_inputs_cameras.png)|四物理组、五视频真实输入/Mask/Ring/冻结相机|
|[Fig2](figures/Fig2_G01_six_views_and_method_status.png)|G01两单视频历史基线、Map M3、SDF先验失败的统一mm六视角；004新模型NOT_RUN；跨视频NOT FUSED|
|[Fig3](figures/Fig3_G01_real_A_to_B.png)|真实目标00860、Map M3源几何投影、叠加/差异/未知/CAD遮挡；SDF失败明确标注|
|[Fig4](figures/Fig4_support_CAD_failure_evidence.png)|SDF观测支持0、实际loss、CAD与全范围几何失败；各面板mm轴/全局窗口明确|

完整本地图库23张PNG，含所有已有有效方法的六视角以及G01全部3目标A→B（005两目标不择优）。[图库与历史GLB来源索引](provenance/GALLERY_AND_GLB_INDEX.csv)、[5个新GLB的路径/SHA](provenance/NEW_GLB_INDEX.csv)。GLB/完整NPZ/权重/单独原图为LOCAL_ONLY；GitHub链接不能打开未上传的大缓存。本机根 `/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001/`。

|可复算表/证据|用途|
|---|---|
|[四组最终状态](metrics/FOUR_GROUP_FINAL_STATUS.csv)|4组审计与只运行G01_005的预算边界|
|[两臂最终状态](metrics/ARM_FINAL_STATUS.csv)|4配置数值成功与SDF适配失败、成本|
|[完整目标分母](metrics/G01_REAL_TARGET_COMPARISON.csv)|覆盖、IoU、boundary F1、RGB、失败/未知|
|[双方同像素](metrics/G01_IDENTICAL_COMMON_PIXELS.csv)|避免不同支持范围MAE选赢家|
|[Ring尺度定位](metrics/MAP_RING_SCALE_ALIGNMENT.csv)|M0–M3逐源已知CAD偏差，非Polyp GT|
|[全部CAD](metrics/ALL_METHOD_CAD_AUDIT.csv)|内点数、最大深度、全点分母|
|[重叠层与pose](metrics/MAP_OVERLAP_AND_POSE_DIAGNOSTIC.csv)|共同射线和冲突分母|
|[源SHA](provenance/SOURCE_SHA_LEDGER.csv)|344冻结输入文件|
|[留出资格](provenance/SOURCE_LEAKAGE_LEDGER.csv)|9目标全保留，G06/G07旧源污染|
|[不可变模型冻结](provenance/ALL_MODEL_OUTPUTS_FROZEN_BEFORE_EVALUATION.json)|先模型输出、后B评价|
|[SDF域失败](provenance/SDF_POST_RUN_DOMAIN_AUDIT.json)|为何0观察支持，不能当科学通过|
|[清理授权与58文件SHA](provenance/USER_AUTHORIZED_CLEANUP.json)|仅清理明确失效旧下载产物|
|[原始运行日志](provenance/run_logs/)|当前工程失败不省略；旧CUDA失败另存|
|[最终核验](metrics/FINAL_VALIDATION.json)|只读哈希/契约/保护/交付核验|
|[最终manifest](provenance/FINAL_MANIFEST.json)|源码、配置、表、核心图、文档与本地来源|

`ARM_RUN_STATUS.csv`和`FOUR_GROUP_READINESS.csv`是第一阶段资源门禁快照；最终请使用带FINAL的表。附件中的PM_READY/PROPOSED文档是历史草案，当前授权和事实以本轮用户指令与本报告为准。
