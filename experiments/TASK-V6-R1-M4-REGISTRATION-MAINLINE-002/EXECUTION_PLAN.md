# M4 全量主线实施计划与复用表

基础提交：f7a3ff8581a80b44adc9eb8415d11748f086a6ee。用户已批准附件范围并要求连续执行。
采用 executing-plans 顺序执行；FIT 诊断结束后冻结全量规则，不继续方法搜索。

|阶段|现有入口|处理|验证|
|---|---|---|---|
|依赖|002 common2/solver2、001 V6_KERNELS、R1 源码|按 Git SHA 解析到本任务缓存；不要求旧工作树|模块文件 SHA、原六组 T 回放|
|输入|R1 audit/preflight.freeze_group|取消六组和双视频截断，所有 manifest 视频列状态|终态39组79视频1153合法源逐阶段身份|
|匹配/三角化|real2.make_tracks/triangulate/ring_prior|复用内核；组内所有视频一次匹配、共享held轨迹身份|旧六组缓存身份、多个视频切片不重分held|
|求解|solver2.solve_methods M4|FIT高影响诊断后决定保留或小修正，单一配置|同域旧六组、T变化、Ring与held完整分母|
|Clean|clean_after.one +017/018|按冻结M4，所有源一次登记，缓存键含T/CAD/分类器|原面ID/state、同步相机、共同面零额外位移|
|评价/图|metrics2/evaluate_real2、R1 visualize|M4统一，三状态、原面固定采样|完整失效计数、同观测辅助对照、接口读取|

- [ ] code/context.py 与入口：固定提交解析依赖；CPU单线程、逐组续跑；保留5GiB磁盘余量，任务上限1GiB。
- [ ] code/audit.py：核验终态清单、摄像机/Ring/HERO链；所有视频含无输出；来源键case+tag；统一按case排序参考（不读held/效果）。
- [ ] code/diagnose.py：旧六组冻结FIT，最高残差5%/重复空间桶影响诊断；只验证一个通用可靠性限权候选；无工程收益则保留原M4。冻结 config/DECISION.json。
- [ ] code/run.py：复用旧六组相同输入的tracks/DLT；新增组一次全视频匹配后共享FIT/held切片。先直接参考边、必要时已连接视频中转；未连接不伪造T。
- [ ] code/outputs.py：所有已连接来源配准后Clean、相机/地标与GROUP.json接口；未连接保留本地来源和明确状态。
- [ ] code/review.py：旧六组旧新同域比较，全量表；三状态中文HTML、真实截面、RGB/Ring/相机；下游读取契约测试。
- [ ] 全量实际运行：局部失败记录并继续，恢复错误阶段；最终核验输入哈希、每源唯一、所有39组状态及续跑入口。
- [ ] TECHNICAL_REPORT.md/REPRODUCE.md、注册表、精选证据提交增量push，核实远端SHA。

不重跑上游，不更改旧结果，不将数值收敛/跨视频一致性称绝对精度，不启动主体优化。
