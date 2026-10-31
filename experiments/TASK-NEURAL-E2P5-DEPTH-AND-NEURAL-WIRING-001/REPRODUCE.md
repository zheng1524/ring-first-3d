# E2.5仅复现本轮P1/P2（不重跑旧审计）

父提交c530fcb，官方MonoSDF12513009。Python3.12、torch2.7.1+cu128但实际CPU；pyhocon/skimage复用E0已存在runtime/python，不安装/下载权重。原始资产LOCAL_ONLY，缺文件或SHA不同应停止，不换图/补旧结果。

```bash
set -euo pipefail
cd /home/liu/ring_first_3d_neural_e2p5/experiments/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
e25_python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
mkdir -p runtime
"$e25_python" code/preregister.py
"$e25_python" code/depth_consistency.py >runtime/REPRO_P1_DEPTH.log 2>&1
"$e25_python" code/ring_depth_audit.py >runtime/REPRO_P1_RING.log 2>&1
"$e25_python" code/bias_diagnostics.py >runtime/REPRO_P1_BIAS.log 2>&1
"$e25_python" code/official_sdf_cpu_adapter.py >runtime/REPRO_P2.log 2>&1
"$e25_python" code/neural_numerics_audit.py
"$e25_python" code/figures.py
"$e25_python" code/report.py
"$e25_python" code/validate_delivery.py
```

正常干净复现只构造4个唯一场景/候选网络。原交付另有2个相同参数的诊断bug复核，历史记录保留，不必重复该失败。test_miss_degeneracy.py的单独main用于按原SHA复核B，不是正式训练。

P1先完成才允许P2。P2真实参数SHA前后相同，GPU调用被拒绝，官方构造两处CUDA张量仅局部转CPU。固定16源射线/128单元，不执行官方自适应sampler、Map推理、优化器、训练或参数更新。研究门槛失败是有效输出；脚本完成不能解释成三参考/重建PASS。

当前单次网络RSS约1.2–2.4GiB，只有二维诊断/少量射线trace；不复制原视频或大权重，不删除旧实验。local_results/runtime不进Git。报告/manifest时间戳会变化，复现前保留当前Git提交。
