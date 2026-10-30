# 当前用户授权与执行边界

2026-10-30（Asia/Shanghai），用户直接下达 TASK-NEURAL-E0-COMPARE-001，正式授权有限 P0/P1 和 P1 成功后的 G01 初步对照。附件的旧 P0_AUDIT_ONLY、NOT_APPROVED、只上传文档和需再次批准 P1 等描述，均为较早草案，已由本次直接授权覆盖。研究冻结、GT隔离、独立路线和资源门禁继续适用。原附件研究文档保留历史状态，不作为当前权限判断。

实际执行：独立工作树 `/home/liu/ring_first_3d_neural_e0`，分支 `exp/TASK-NEURAL-E0-COMPARE-001`，精确基点 `fa50f68f27fd1679276e3ac549322cda05fc4191`。未修改 root README、AGENTS、主线或历史实验。附件根 README 另存 `research/phase_e_neural/ATTACHMENT_ROOT_README.md`。

P1 有权执行，但启动前必须满足数据、GPU、依赖、许可证及磁盘门禁。本轮发生 ENOSPC；官方 MapAnything 权重单文件 4,914,062,480 bytes，超过初始可用约3.3 GiB及后续约0.3 GiB。只缩减本任务工作树重复签出的历史文件，未删除任何旧资产。SDF所需依赖/编译闭包亦不具备。依用户终止条件，停止模型分支；继续完成只读审计、证据图、增量版本和报告。不将 NOT_RUN 写作算法失败或科学胜负。

只读 CUDA 小张量通过；没有安装、驱动调整、模型权重下载、HERO重推、SDF优化、Map前向或CPU模型回退。
