# 复现

基线：`release/research-harness-001@e24fbd0069d31636424af188b863169633ca47ae`。本任务目录 `/home/liu/ring_first_3d_policy_bootstrap`，复用原环境与冻结资产，不安装包或修改受保护目录。

在项目根目录：

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/TASK.yaml --run-dir /home/liu/ring_first_3d_policy_bootstrap/experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/runs/verified-001
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/TASK.yaml --run-dir /home/liu/ring_first_3d_policy_bootstrap/experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/runs/verified-001
```

同一源码/环境/输入时，run --stage all 对该已完成 run 只核验并跳过成功阶段。新运行换新 run-dir 名，历史不覆盖。已冻结 TASK 不允许改参数后恢复；变更须用独立新 run。

回归：

```bash
bash tools/research/run.sh -m unittest discover -s tests -v
bash tools/research/run.sh tools/research/test_policy_integration.py --task experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/TASK.yaml --label new-label --output /tmp/policy-integration-new.json
```

预期 35 项测试通过；第二条为 18 次实际 CLI 检查，包含自己启动的 Smoke Runner 的 SIGKILL 和恢复。使用新 label，已存在目录拒绝覆盖。正常结果路径和恢复结果路径由输出 JSON 给出，每个 run 都有本地 index.html、结果卡及 RUN_MANIFEST。

源码指纹包含 policy、原 Harness 与测试文件、Failure Registry、相关环境和已编译 Renderer SHA；新增/修改这些源文件会使旧 run 拒绝恢复，应创建新 run。测试摘要、Markdown 报告及 Git commit 本身不改变执行字节指纹。其他机器需用 init 重新绑定同 SHA 的登记资产和环境；没有真实资产/GPU时不能模拟通过。
