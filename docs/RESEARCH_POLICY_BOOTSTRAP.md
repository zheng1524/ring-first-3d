# TASK.yaml 与科研执行入口

这是既有 Harness 的增量控制入口。最短交接提示词：

> 按 TASK.yaml 检查并执行已授权阶段，用同一 run-dir 恢复；失败停止。完成 accept，返回结果卡、可视化路径和提交 SHA，然后停止。

在仓库根目录执行：

```bash
bash tools/research/run.sh tools/research/policy.py init --task-id TASK-YOUR-TASK-001 --output experiments/TASK-YOUR-TASK-001/TASK.yaml
# 核对目标、人工授权阶段和预算；init 本身不运行任务或取得科学批准。
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-YOUR-TASK-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-YOUR-TASK-001/TASK.yaml --run-dir /absolute/repo/experiments/TASK-YOUR-TASK-001/runs/001 --stage all
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-YOUR-TASK-001/TASK.yaml --run-dir /absolute/repo/experiments/TASK-YOUR-TASK-001/runs/001
```

`run --stage preflight|contracts|smoke|artifacts` 指定阶段；`status` 查看进度；`failures` 查询失败记忆。命令返回 0 表示该命令完成，2 表示拒绝/失败；run 完成后还须 accept。没有忽略失败、force 或跳过前置门禁的选项。

[模板](../templates/TASK.yaml) 包含目标、模块 ID、冻结变量、输入/源码/reference/evidence SHA、FIT/HOLDOUT、授权阶段、验收、预算和停止条件。相机角色复用冻结 CASE.json 的 SHA，不手抄 108 个 ID。模板授权为 pending，init 绑定本机已登记的真实回归输入。后续不必阅读整个项目，只需任务契约、check 拒绝信息与本次 RESULT_CARD。

严格校验拒绝未知字段、重复 YAML key、任意 YAML 对象/别名、未知模块、错误单位/坐标、FIT/HOLDOUT 重叠、GT 输入、错误 SHA 和受保护输出。模块 ID 映射到现有 SHA 锁定源码与数学契约，不另写算法。

首版只执行已有工程验证 API：Preflight→11 项 Contracts→真实 Smoke→Artifacts。已有 Preflight/Smoke 是完整集成包，运行时须显式声明全部十个模块；模块子集可执行 check 来源核查，未声明完整范围时拒绝启动集成包。本轮不为细粒度调度拆改科学算法。新的科研 handler 需另经授权与注册；TASK.yaml 不能执行任意 shell/Python、主体重建或 GT 评价。

每个 run 冻结 TASK、233 个真实资产身份、源码/测试/Failure Registry 哈希、Python/依赖版本、编译 Renderer SHA 和相关环境，阶段前后复核。参数/来源/版本变化时旧 run 拒绝恢复，须用新 run-dir。强制停止由 TASK 契约与注册代码断言执行。

结果采用独立 attempt 和不可变 snapshot；JSON fsync 后原子发布、完成目录 rename，最后只原子切换 current 指针。失败、超时、stdout/stderr/原始 payload 与旧快照保留。同一 run 的并发写由 flock 拒绝。恢复会跳过已验证阶段；中断半成品记为 INTERRUPTED，不能接受半写 PASS。Linux worker 的 parent-death 信号及超时进程组终止防止遗留本任务 GPU worker。中断保守扣除预留 timeout，预算限制新阶段、重试与 worker 输出，失败诊断仍保留。

每个已开始尝试的有效任务，包括失败任务，生成：

```text
run-dir/
  visualization/index.html
  RESULT_CARD.md
  RUN_MANIFEST.json
  TECHNICAL_REPORT.md
  metrics.json
  failures.json
  FREEZE.json
  attempts/
  snapshots/
```

验收验证全部实际路径、SHA/大小、HTML 所有本地 href/src、失败证据与各授权阶段的实际 PASS。缺可视化不自动补造。页面展示本次阶段状态/耗时和明确标注的既有真实回归图；历史图不能当成本轮新重建。check 是只读检查，非法 YAML/不可信输出在建立 run 前拒绝，不向猜测路径写产物。科学验收始终 NOT_APPLICABLE。

[Failure Registry](registry/FAILURE_REGISTRY.json) 区分代码/环境/身份错误、科学负结果和未完成评价；记录已证实原因或仅观察到的现象、修复、回归测试和固定证据。导入项均为 candidate；没有 reviewer、approval 和证据不得晋升 reviewed_permanent，记忆不驱动自动算法切换或修复。

worker 为可信既有 API 加 Python I/O 门禁，拒绝 GT 路径和 attempt 外文件写入，临时目录定位到本次 attempt；外部命令仅允许原 Git 只读查询及 CPU 元数据。它不是恶意原生代码的 OS 沙箱，约束依赖固定源码、无任意 handler、冻结数据与已审计 API。受保护目录保持只读。

复测：

```bash
bash tools/research/run.sh -m unittest discover -s tests -v
bash tools/research/run.sh tools/research/test_policy_integration.py --task experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/TASK.yaml --label new-unique-label --output /tmp/policy-cli-results.json
```

集成测试实际调用既有 GPU/DXY API，并终止自己创建的一次 smoke runner 验证恢复，不修改冻结输入。使用新 label，不覆盖历史。尝试目录保持 LOCAL_ONLY，Git 只保存必要源码、模板、报告和实测摘要。
