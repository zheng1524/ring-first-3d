# Reproduce A2

基准：父提交4b60db5d9402c2bb87692ba3b2b7819f3c7c1423；六源顺序固定。必须拥有DERIVED_INPUT_LINEAGE列出的原文件和旧Gate A本地派生缓存，按config/PROTECTED_START.json核对SHA；不下载模型、不从Raw面或其他预测补深度。固定Python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python，复用历史Open3D vendor。主环境不改。

从新任务repo根目录执行；output必须是尚不存在的本任务runtime子目录：

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001/code/replay.py --output /home/liu/ring_first_3d_e3n0_a2/experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001/runtime/replay_new
```

入口原样复制已冻结协议；仅依次执行discover、cleanup、validate_inputs，拒绝覆盖已有输出。不重新执行旧Gate A或模型加载。复现本轮2,810候选、223新排除、9保留、105875输入、27.959mm域及诊断。7份CSV和正式结果逐字节SHA对照。已实测runtime/replay_verification/REPLAY_VERIFY.json全部一致。

原始执行次序为preregister.py → discover.py → cleanup.py → validate_inputs.py → figures.py → audit.py；preregister只在父HEAD且无协议时运行一次，禁止在最终HEAD重写历史冻结记录。审计/报告入口不会启动推理，但无需为复现数值而再次运行。r14诊断从旧HUMAN_REVIEW_CONTEXT读取真实(99,144)，不依赖旧叙述笔误。

LOCAL_ONLY：原始/基线/本轮派生深度、全部原ID世界坐标、crop NPZ、重放缓存。LOCAL_RESULTS_INDEX记录路径/bytes/SHA。上传只有任务代码、配置、CSV/JSON、报告和四PNG。没有神经网络前向、GPU、GT、相机拟合或新TSDF。所有失败是预期保留结果，复现成功不意味着Gate A通过。
