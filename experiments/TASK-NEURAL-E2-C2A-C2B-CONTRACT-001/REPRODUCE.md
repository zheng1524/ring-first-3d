# E2 CPU复现说明

代码基于E1 af71a6f，仅使用其已冻结证据；不要运行E1审计、reset或重新初始化。下面命令仅CPU合同；不会进行官方模型forward、训练或权重更新。需要原机LOCAL_ONLY资产；Git仓库不是原始数据备份，缺资产必须报错，禁止下载替代图或补齐历史测量。

在独立E2工作树运行：

```bash
set -euo pipefail
cd /home/liu/ring_first_3d_neural_e2/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
e2_python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
for e2_script in test_c2a scene_geometry multiview map_inputs comparison initialization_contract figures replay_negative_case validate; do
  "$e2_python" "code/${e2_script}.py" >"runtime/reproduce_${e2_script}.log" 2>&1
done
"$e2_python" code/deliver.py report
"$e2_python" code/deliver.py manifest
```

顺序强制C2a先通过再进C2b；`test_c2a`会将C2b门槛重置到真实链接待核验，`scene_geometry`通过后才允许C2b。不要并行这些有依赖的步骤。实际最终检查见metrics/FINAL_VALIDATION.json（275项阶段检查+257项独立完整性核验，不是科学样本数）。复现会更新本任务时间戳/冻结manifest，请先保留当前Git提交快照。

Python必须为3.12；系统3.8不适用。环境/官方代码版本见provenance/CPU_ENVIRONMENT.json，Open3D来自冻结vendor。context中的审计钩子禁止网络、GT、权重与任务外科研写入。CPU有解析几何autograd，但无优化器、无参数更新。这里不包含任何正式神经模型运行命令。

local_results存放六源射线包、六源batch/reliability、30派生Map深度及M3混合深度；原生相机/深度未改写。runtime保留日志/图缓存，均Git忽略且存于持久目录。源路径和SHA见E2_READONLY_INPUTS_AND_SHAS；缺失/变更资产需停止，不能自动换源。

首次失败原始日志为runtime/C2A_attempt001.log；原分组表达式未归档，因此replay_negative_case仅演示错误长度分组的反例，不能声称逐字复现原失败源码。实际几何验收始终使用真实triangle primitive身份与原0.002mm容差。
