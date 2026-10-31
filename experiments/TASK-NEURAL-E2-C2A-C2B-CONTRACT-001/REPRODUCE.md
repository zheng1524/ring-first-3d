# 本轮E2继续执行：仅复现新增CPU工程

保留上一轮commit5d4bcbb；不重新初始化、重跑E1审计或重复上一轮275项阶段测试。上一轮完整复现说明仍在该提交。新工作树读取旧E2的冻结batch/射线/深度资格，只读SHA核验实际复用文件。

```bash
set -euo pipefail
cd /home/liu/ring_first_3d_neural_e2_cpu/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
e2_python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
mkdir -p runtime
"$e2_python" code/continuation_tests.py >runtime/CONTINUATION_WIRING_REPRODUCE.log 2>&1
"$e2_python" code/continuation_inputs.py >runtime/CONTINUATION_INPUT_REPRODUCE.log 2>&1
"$e2_python" code/continuation_deliver.py
"$e2_python" code/continuation_validate.py
```

仅解析Sphere/颜色函数与官方安全数学/输入工具执行。禁止调用官方神经网络、sampler或optimizer；官方模块注入会被拒绝。所有测试阈值和测试权重先冻结，无模型参数更新。实际GPU科学运行不在本复现命令中。

资产必须来自原E2工作树及已审计旧路径，缺文件或SHA变化会报错。local_results/continuation_cpu与runtime为本地持久数据，Git忽略。先保留当前提交，复现会更新本任务时间戳/报告/Manifest。
