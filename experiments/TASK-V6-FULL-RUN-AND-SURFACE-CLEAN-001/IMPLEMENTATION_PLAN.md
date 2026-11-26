# V6 HIST 全量后台与三源 clean 执行清单

Goal：持久全量作业健康运行后交接；不等待全量结束。用户附件已明确批准工程适配和一个 clean 候选，本表落实该批准，不增加审批轮次。

| 阶段 | 已有入口 / 版本 | 输入→输出 | 处置与验证 |
|---|---|---|---|
| 全量清单 | frozen39/inputs.csv；本地真实 RAW | 物理组/文件→SHA、媒体探测、重复/例外 | ADAPT；逐文件核对，解释历史102差异 |
| RAW/INIT | v6_raw.route.prepare@115e41fe；原setup_audit | RAW→16+最多6帧/原Mask | REUSE；仅配置白名单与路径，真实帧/PTS检查 |
| Ring/SIFT/BA | route.cameras；精确M10 6ad695b0…与锁定V5/V6 | 当前观测→相机/门控 | REUSE；索引8/9及Q0/Q1完全保留 |
| Support | route.schedule/policy.choose_sources | 冻结相机→每Target一个3元组 | ADAPT实际分母；元组身份与动态预算测试 |
| HERO/Mesh | route.hero；原run_mvs005_supported/package_surfaces | 冻结计划→352深度/360原Mesh | ADAPT恢复日志；锁GPU，已成功元组不重跑 |
| 调度/汇总 | 新 full_run.py 工程编排 | 清单→逐视频状态/覆盖/持久进程 | 用户明确授权的新调度；有界队列1，原子标记、低空间保护 |
| 展示 | nearviews.make/原renderer | 全原面→近景逐源六视图 | ADAPT仅输入及类型开关；只生成这一类型 |
| 历史clean | native.cleaning.classify_native/_clean_kernels | 当前352/360映射→逐面证据 | ADAPT坐标/像素接口，不复用旧分类 |
| 单个clean候选 | 历史连续密度/原网格异常证据 | 预选3源→原面子集 | 用户明确授权；先冻结规则，保留未知和原始索引 |

- [ ] 清单、磁盘估算、配置；阶段/预算/恢复与固定分母测试先行。
- [ ] 实现最小配置接口、持久队列、只读复用与近景逐源；验证原内核哈希和旧策略测试。
- [ ] 固定执行源码快照，启动后台，观察新增视频真实HERO成功。
- [ ] 在clean之前冻结3来源与一个候选；历史基线、候选、原面映射核验；恰好3张中文单源三列图。
- [ ] 独立复核、提交上传、健康证据与RUN_HANDOFF、本地URL；退出而不等待全量。

架构：科学函数仍集中在既有route.py及锁定外部内核；full_run.py只调度，不复制求解器。每视频独立进程回收模块/GPU状态；同视频官方模型仅加载一次。队列宽度1为6GB共享GPU和当前磁盘的初始保守实测配置，避免并发相机进程干扰任务B。原产物引用不复制；新任务只删可再生点云导出和surface缓存时须先冻结可恢复清单，不删原生深度/相机/Mesh。清理候选不接入批量任务。
