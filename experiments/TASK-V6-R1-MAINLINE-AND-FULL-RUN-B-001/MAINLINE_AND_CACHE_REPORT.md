# R1主线与缓存整理

执行授权：TASK-V6-R1-MAINLINE-AND-FULL-RUN-B-001。R1科学基线dfc13a01，交付53909889；本轮只重构入口、阶段缓存、恢复与统计，未改科学门槛。最终执行快照/PID见FULL_RUN_HANDOFF。

## 唯一当前入口

`python tools/v6_raw_to_hero.py run`，委托原`ring_first_3d.v6_raw.full_run`，默认`config/FULL_RUN.json`。模块CLI不传config也使用同一配置。实际活跃`docs/registry/routes.yaml::current_mainline`已登记。历史R0/R2配置保留；新配置include_photos=false、reuse_old_results=false、approval_required=false。39物理组/79注册视频、1653非诊断Target；120照片保护且不处理，30未注册视频不进入分母。

## 实际模块组合

|阶段|实际函数/版本|输入→输出与处理|
|---|---|---|
|RAW/原16+补帧|route.build_raw_preprocessing / historical_extra / frame_indices|原MP4→RGB、Mask、真实帧号/时间/K；从dfc13原prepare冷分支逐AST提取|
|INIT|原DXY INIT与setup_audit选择块|原冻结模型及变换；权重与源码仍由原signature核验|
|预处理缓存|stage_cache.ensure_prepared|同一builder；缓存缺失生成，完整回执与每文件内容核验后复用|
|Ring|M2F10.build_ring / frontend_kernels.install|R5/R10真实物理参数；真实全边界观测；无病例分支|
|完整匹配|stage_cache.ensure_matching→原track005.main|完整原视图池、原SIFT/RANSAC/train-held；分量裁剪前保存完整track/pair|
|分量|frontend.component / preserve_video_tracks|保留原锚/B与时间边；当前完整轨迹作为本次基准，不定位旧输出|
|相机|route.cameras→原两初始化/local_ring_sfm/validate_select|原Ring+RGB BA；未改目标函数、收敛与相机准入|
|Target/Support|frontend.select_complete_plan / route.schedule|默认计划非空即保留，只有零合法才检查另一原初始化；冻结1+3|
|HERO/建面|route.hero→冻结M2F10→官方HERO / 原package_surfaces|每新合法元组新推理；同输入恢复成功native，资源失败最多一次重试；重试后按原计划排序ledger|
|clean|clean_stage.clean_source→原classify_native / trusted_subset|抽取小试逐源处理；冻结017+gap与F[state==0]，原V/F/FaceID/四态保留|
|展示/统计|full_run.summarize_video / refresh→nearviews.make|现有Raw近景逐源六视图、裁切计数、Trusted计数、失败/零计划分离；自动终态报告|

精确本地源码SHA见`evidence/SOURCE_HASHES.json`；外部内核仍由原KERNEL_LOCK与protocol_signature核验，实际执行提交由V6_EXECUTION_COMMIT记录。官方HERO SHA仍为00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d。

## 缓存边界与独立性

唯一规范位置`/home/liu/ring_first_3d_workspace/cache/v6_r1/{prepared,matching}/<真实视频名>`。本轮正式配置关闭可选legacy导入，已有规范缓存核验复用，其余RAW冷生成。因此旧R0预处理/轨迹不再是新R1必需输入；仍有其他保留消费者的旧副本未擅自释放。

科学身份覆盖RAW、K、实际选择/INIT/builder、规范RGB/Mask/顺序、匹配内核/适配AST/config及完整数组。NPZ容器字节用于损坏检测，数组名称/shape/dtype/值/NaN用于内容等价；运行提交、时间、缓存目录留在溯源。COMPLETE最后原子写入；未完成不命中，STALE/CORRUPT隔离重建并保留原因。JSON物化为独立副本，二进制不可变文件可硬链接，不制造全套重复资产。

prepare不再强制旧INPUT_IDENTITY，preserve_video_tracks不再沿preprocessing_reuse.source查旧轨迹。旧输出禁读通过Python审计钩子记录；合法外部科学源码、模型、CAD继续只读。

## 最小冷/热验证

两例均从空规范缓存开始，禁止旧R0/RAW-to-HERO/pilot运行根读取，至相机/计划，不执行HERO。工程验证执行756f2870161c1ca8fae623cfd81b8394d725f9d8；运行在独立engineering_validation，未计正式全量。

|视频|合法Target|选择初始化|输入/轨迹/分量/时间边|两版相机c2w|元组哈希|
|---|---:|---:|---|---|---|
|IIa4.5/R10/005|13|0|逐项完全一致|逐位一致，最大差0|全部一致|
|Ip8.8/R5/005|21|1（默认零计划后回退）|逐项完全一致|逐位一致，最大差0|全部一致|

热路径同入口重入，无解码/INIT/SIFT重算；两层缓存均明确HIT，禁读旧输出尝试为0。完整证据与日志见`evidence/VALIDATION_*`。验证后修改仅涉及full_run/clean/展示与HERO失败恢复调度；相机、匹配、选择函数未改变。

## 失败与恢复

新队列自动prepare→camera→schedule→hero→clean→render。科学零计划与数据、工程、资源、低盘单列；原锚分量不足也保留真实零输出原因。HERO内部吞掉的异常由ledger识别，资源失败同元组最多重试一次；重试事务保存PENDING及原ledger/完成回执，先失效COMPLETE再裁剪失败条目，重入恢复未完成事务。成功native不重推。未解决HERO异常即使有部分曲面也保留HERO_FAILED，成功源仍clean/展示，不报正常完成。终态强制ledger tag集合与PLAN一致。

恢复核验RUN_IDENTITY（配置/manifest/执行快照）；DONE还核验RAW、CAD、相机/HERO父子/产物、clean父输入及产物SHA，拒绝漂移。clean回执绑定真实CAD、RGB/Mask、适配代码、原native/VF/相机/输入。已冻结分类内核未改。

相关测试初次50项通过；审查修复后54项通过，另新增中断重试事务测试通过。失败的红测与一次报告代码括号错误记录均保留；最终验证见evidence。独立审查指出3项Important，修复记录见REVIEW_RESOLUTION.md。

## 空间与共同样本

`evidence/SPACE_BUDGET.json`按1653全部产出估算约13.16GB，含新缓存、相机、400MB阶段峰值和1GiB保底；不假设困难视频会失败。实际启动df/清理回执另记STARTUP_CHECK。至少1GiB+当前阶段峰值不足时暂停。

`config/BASELINE_RECORDS.json`归档105、205、795三个重叠集合的真实Target、Support、元组/mesh哈希、初始化和原单面诊断指标；不相加。运行自动逐Target对照保留/丢失/失败/待运行及Support/init/指标变化，不把不同条件下的均值称路线精度提升。Raw/Trusted非空只是输出覆盖。

## 清理后导入依赖补充修复

原两例验证后，A清理暴露共享模块顶层对退役示例相机的隐藏读取。首启无HERO即暂停并归档。29874fe6只解除两项模块初始化读旧相机，保留全部原函数AST；两例再次重解/比较全部逐位一致（13/21元组），最终56项测试通过。细节见IMPORT_DEPENDENCY_REPAIR.md及BOOTSTRAP_VALIDATION证据。
