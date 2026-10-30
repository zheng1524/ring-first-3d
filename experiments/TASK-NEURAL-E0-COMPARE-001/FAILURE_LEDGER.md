# Phase E Failure Ledger（初始审计状态）

状态 `PROPOSED`。既有历史失败不是 E0 模型失败；P0/P1 之后应按行追加原始证据，保留旧行。

|ID|来源|分类|证据|E0 处理|
|---|---|---|---|---|
|H-01|边界生长 G01_004|`ALGORITHM_NOT_PROVEN`（旧 F3）|S0→Joint 同像素 RGB MAE 22.813→24.155；CAD 旧点穿插额外19|保留为 SDF/Map 必须击败的反例；不提前宣布新方法能解决|
|H-02|边界生长 G01_005|`ALGORITHM_NOT_PROVEN`（旧 F3）|00860 同像素 19.634→22.809；00611 8.842→10.941；CAD 旧点穿插额外21|两个独立目标不能选择性只呈现一个|
|H-03|分区 MASt3R G01 跨视频|`REGISTRATION_UNVERIFIED`|双向轴向冲突 65.90%/70.40%；跨视频 GLB 仅候选|004/005 不联合、不将 H 作 GT|
|H-04|分区 MASt3R|`HOLDOUT_LEAKAGE_RISK`|004 两个旧HERO/P0源帧曾在HOLDOUT；G08无预冻结独立留出|P0 必须做 RGB/HERO 多图输入 SHA 级资格表|
|H-05|边界生长 video005|`RUNTIME_BLOCKED`|2/24 新 HERO 尝试失败；`cur_image.to(device)` unspecified launch failure；新进程 CUDA 检查失败|P0 只读硬件复查；不得算几何拒绝或用 CPU 极慢运行掩盖|
|H-06|G07 Is/R5|`DATA_INELIGIBLE_FOR_NORMAL_SUCCESS`|冻结相机 `UNQUALIFIED_CAMERA_STRESS`，旧 Ring 穿插 287 点|压力结论独立；不换组隐藏失败|
|H-07|G01 photo001–003|`DATA_INELIGIBLE_FOR_METRIC_RECON`|K490/pose 未认证，无可信照片 HERO 深度|只作图像候选，不补造公制 XYZ|
|H-08|四组形状 GT|`ABSOLUTE_3D_NOT_EVALUABLE`|部署世界变换/组织切面未独立认证|GT 密封，只后验非 Oracle 指标可用|
|E0-S|Arm S|`NOT_RUN`|仅官方可行性研究|静态可行并非 smoke 成功|
|E0-M|Arm M|`NOT_RUN`|仅官方接口研究|静态可行并非模型输出成功|

新增失败行最少包含 `time, task, group, video, source_shas, arm, config_sha, code_commit, attempted_stage, type, raw_error_or_metric, physical_denominator, disposition, next_approval_required`。严禁只留下成功样本。

## 本次实际执行追加（2026-10-30，Asia/Shanghai）

旧行保持为历史快照；当前状态以下表及 `ARM_FINAL_STATUS.csv` 为准。4物理组审计；新模型仅1组/1视频/2输入/2目标。配置哈希见各BEFORE_*冻结文件，代码commit见阶段提交及FINAL_MANIFEST；完整错误不省略于链接JSON。

|ID|步骤/组/帧或候选|实际失败/限制|证据与处置|
|---|---|---|---|
|E-01|P0 磁盘|ENOSPC，审计小目录无法创建；非算法失败|[原事件](provenance/RESOURCE_EVENTS.json)、[用户授权清理58项SHA](provenance/USER_AUTHORIZED_CLEANUP.json)；已恢复，未删除有效预测/权重|
|E-02|依赖/导入|缺hydra/uniception/pyhocon等；antlr缺失|[原导入错误](provenance/DEPENDENCY_IMPORT_INITIAL.json)、[隔离依赖](provenance/ISOLATED_DEPENDENCIES.json)；仅任务runtime安装，不改变原Torch/CUDA|
|E-03|M官方下载|600秒超时，余102.4MiB|[原超时](provenance/MAP_DOWNLOAD_RESULT.json)、[唯一终段恢复](provenance/MAP_DOWNLOAD_RECOVERY_RESULT.json)；同checkpoint，SHA通过|
|E-04|M模型加载|共享DPT参数的别名被初版守卫误拒绝|[加载失败](provenance/MAP_INITIAL_ALIAS_GATE_FAILURE.json)；改为按共享参数对象核查所有别名及实际加载值，发生在前向之前|
|E-05|M0接口，2次|Float/BFloat16边界冲突|[第一次](provenance/MAP_INITIAL_DTYPE_FAILURE.json)、[第二次](provenance/MAP_SECOND_DTYPE_FAILURE.json)；保持官方AMP-disabled模块FP32，两个边界只作dtype转换；非CUDA硬件故障|
|E-06|M3接口，1次|is_metric_scale Python bool被官方depth路径下标访问|[原M3错误及M0–M2输出](provenance/MAP_RUN_RESULT.json)、[M3唯一补充](provenance/MAP_M3_SUPPLEMENT_RESULT.json)；改为官方支持tensor([True])，未重跑已完成M0–M2|
|E-07|S G01_005两输入|一次400步优化完成，camera半径3.271/3.870大于吸收边界2.5；silhouette饱和；57176面中观测支持0|[域诊断](provenance/SDF_POST_RUN_DOMAIN_AUDIT.json)、[输出](provenance/SDF_RUN_RESULT.json)、[Fig4](figures/Fig4_support_CAD_failure_evidence.png)；适配失败，不加时/不第二次优化|
|E-08|M G01_005目标00860/00611|M0/M1两目标均0覆盖；M2为0%/12.97%；M3为3.67%/16.81%|[完整分母](metrics/G01_REAL_TARGET_COMPARISON.csv)、[相同像素](metrics/G01_IDENTICAL_COMMON_PIXELS.csv)、[Fig3](figures/Fig3_G01_real_A_to_B.png)；不以小支持集低MAE挑赢家|
|E-09|M已知Ring/公制定位|M3 Ring到固定CAD中位偏差约22mm；0穿插仍不能认证几何|[Ring公制诊断](metrics/MAP_RING_SCALE_ALIGNMENT.csv)、[冲突/相对pose](metrics/MAP_OVERLAP_AND_POSE_DIAGNOSTIC.csv)、[Fig2](figures/Fig2_G01_six_views_and_method_status.png)|
|E-10|G06 raw00351/G07 raw00293|从底层native源列表确认两帧曾作为旧HERO源输入|[SHA级泄漏表](provenance/SOURCE_LEAKAGE_LEDGER.csv)、[依赖边](provenance/HERO_DEPENDENCY_EDGES.csv)；两帧降为DIAGNOSTIC_ONLY，G07压力另列|
|E-11|G01_004/G06/G08/G07|新模型NOT_RUN，保留NaN；004原始顺序帧未认证、G08有限、G07不合格|[四组最终状态](metrics/FOUR_GROUP_FINAL_STATUS.csv)、[Fig1](figures/Fig1_four_group_inputs_cameras.png)；未执行不伪造几何，也不冒充模型算法失败|
|E-12|总体比较|0严格留出、SDF无有效支持面，未形成有效双臂科学对照|[最终状态](metrics/ARM_FINAL_STATUS.csv)；等待PM独立验收和RA技术审查，不自定胜者|
