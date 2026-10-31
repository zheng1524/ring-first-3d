# E2.6 CPU复现

原始E1/E2/E2.5不重跑，只读复用。任务目录`/home/liu/ring_first_3d_neural_e2p6/experiments/TASK-NEURAL-E2P6-INITIALIZATION-AND-STABLE-LOSS-001`；Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（Python 3.12.13）。已有E0官方代码/缓存依赖、源参考与固定NPZ必须存在；不下载权重，不运行Map/GPU。

所有命令在任务目录下运行；已有冻结结果应先保留，逐阶段执行并保留失败日志。校准只有1条规则；如失败，**停止初始化搜索**，后续命令仅复核同一模型/病理控制的损失诊断，不改参重搜。

```bash
export PYTHONDONTWRITEBYTECODE=1
PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PYTHON" code/preregister.py
"$PYTHON" code/calibrate.py
"$PYTHON" code/stable_test.py
"$PYTHON" code/weak_anchor_test.py
"$PYTHON" code/neural_gate.py
"$PYTHON" code/coverage.py
"$PYTHON" code/zero_level_controls.py
"$PYTHON" code/figures.py
"$PYTHON" code/report.py
"$PYTHON" code/validate.py
```

`weak_anchor_test.py`以稳定Mask全负失败为条件；只是候选，不执行参数步。`zero_level_controls.py`不是新增校准，按同参数SHA核对opacity与真实前交叉。原E2.6结果发生一次start_sdf trace修正，不变的科学判定由独立assert记录。

仅最终完整性复核可单独运行`code/validate.py`；不会构造神经网络。它检查冻结SHA、固定像素、原工作树、真实CPU输出记录和报告链接。预期完整性PASS_WITH_RESEARCH_GATES_FAILED，**研究门槛预期FAIL**，不得为得到PASS改阈值。

本地`local_results/`和`runtime/`不入Git；输入来源/最终NPZ与日志SHA在交付manifest中。PNG是未训练官方raw SDF或明确标注控制实验，不是训练后三维重建。环境和旧代码依赖见`provenance/ENVIRONMENT.json`及`CODE_REUSE_E2P6.csv`。
