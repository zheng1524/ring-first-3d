# R1统一入口与全量B实施计划

依据用户直接批准的任务附件执行；R1路线、全量启动及A/B交接已授权，不重复申请批准。仅调整接口/缓存/调度，科学方法冻结于dfc13。

## 实际组合表（先于代码）

| 阶段 | 现有函数/版本 | 本轮处理 | 输入→输出/验证 |
|---|---|---|---|
| RAW选帧/INIT | route.prepare/historical_extra/frame_indices；dfc13 | ADAPT：提取现有冷builder，规范缓存调用同一函数 | MP4→原16+最多6 RGB/Mask/K；冷热逐值比较 |
| Ring | M2F10.build_ring＋frontend_kernels | REUSE | 原像素观测→q/p/b；实际源码锁不变 |
| 匹配 | V6 track005.main/v6_common | ADAPT：完整帧池缓存包裹，原实现只调用一次 | RGB/Mask→完整track/pair；值/NaN/类别/held核验 |
| 分量 | frontend.component | REUSE；R1移除不必要的旧输出读取 | 原锚/B→同分量、原时间边 |
| 相机 | 原两初始化/BA/validate_select | REUSE | Ring+RGB→原Q0/Q1；两例对照数值及计划 |
| 组合 | frontend.select_complete_plan、route._schedule | REUSE | 默认有合法元组即保留，零计划才回退 |
| HERO | route.hero＋官方内核 | REUSE | 冻结1+3元组→native/原V/F；正式队列前部验收 |
| clean | pilot_report.clean→classify_native/trusted_subset | ADAPT：提取共用逐源clean，接入runner | 原V/F→017四态+gap/F[state==0]；原实现参数不变 |
| 展示/统计 | full_run.summarize_video/refresh、nearviews.make | ADAPT：自动clean计数/三基线比较/终态报告 | 单套Raw近景图、固定79/39/1653分母 |

无缺失科学阶段。预处理与匹配两类规范缓存使用阶段内容身份、文件SHA和完成回执；提交/路径仅溯源。缓存缺失生成、过期拒用、损坏隔离；固定RAW/内核漂移报错。空目录和未完成临时目录不命中。既有回执不改写。

## 实施与验收顺序

1. 已发布B001精确生成交付重复包清单，由A持maintenance.lock核验执行；保护现有所有有效输入。
2. 为缓存缺失、损坏、内容等价及热路径写边界测试；提取已有builder，解除prepare和preserve_video_tracks两处强依赖。
3. 提取既有clean公共逐源函数并接入prepare→camera→schedule→hero→clean→render；结构化结果区分零计划/数据/工程/资源/低盘。
4. 两例独立空缓存且禁读旧目录跑至相机/计划，热路径验证不再解码/INIT/SIFT；与R1同输入同track/元组比较。其余pilot对照在正式队列中自动完成。
5. 必要迁移完成并验证消费者后才发布额外释放批次；读取A回执、测空间、按1653上限加新缓存和阶段峰值预算。
6. 登记唯一R1配置和默认入口；提交科学快照，持维护锁核验清理闭合并启动授权全量。首次新native/非空Raw→clean→图表完成且队列再推进后交接RUNNING。
7. 上传独立报告提交，提供PID、SHA、当前计数、本地URL、恢复命令。空间确实不足则据实交接缺口，不删受保护内容、不虚称启动。
