# 本机复现与长程运行

独立工作树 `/home/liu/ring_first_3d_e3_sdf_full`；Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`，PyTorch2.7.1+cu128，官方 MonoSDF commit12513009。不需要下载模型权重，网络按种子初始化。原生输入/历史依赖绝对路径和SHA见 provenance；仓库不复制原视频/大缓存/其他路线预测。

```bash
cd /home/liu/ring_first_3d_e3_sdf_full
TASK=experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
```

`prepare.py` 已执行并冻结，不应在当前目录重新初始化；其已有冻结守卫会拒绝。它说明在一个新隔离目录内如何从已登记原始 Git blob/源文件生成输入。私有 frozen_inputs 和 runtime 不进 Git，异机需先按 provenance恢复这些只读资产，不能通过下载其他来源补齐。

检查输入和坐标（CPU；不更新参数）：

```bash
"$PY" -B "$TASK/code/validate_preflight.py"
```

资源 benchmark 每臂只运行一次，已有结果会拒绝重跑，不能用它代替正式训练。`preflight_delivery.py` 是资源暂停时点快照生成器，正式运行后不要重跑覆盖该快照。

本次研究者授权先完整 ref08 的 M0/M1；正式冻结已经在首次更新前保存。初次串行启动（已有日志/检查点会拒绝覆盖）：

```bash
"$PY" -B "$TASK/code/run_authorized_stage.py"
```

顺序 M0 200000步 → M1 200000步；三 CORE 不启动。主循环来自官方 MonoSDFTrainRunner.run，变更 diff 随交付保存。每100步输出状态/日志，每1000步保存 latest，关键步保存不可覆盖检查点和真实 SDF/Mesh。`metrics/single_M0_STATUS.json` 与 `single_M1_STATUS.json` 为实时状态，`runtime/FORMAL_single_*.log` 为本地完整日志。

硬件或数值中断先阅读 `*_INTERRUPTION.json` 并解决具体原因；禁止因几何差而重启搜参。保持冻结源码/输入后从完整 latest 恢复对应臂（不会重建网络状态替代已训练状态）：

```bash
"$PY" -B "$TASK/code/train_full.py" M0 --resume
```

恢复的是 last完整检查点，不保证等于硬件中断前最后一次更新；中间未保存更新如实计为丢失，M0最后计数仍须实际达到200k。latest 包含参数、Adam、调度器、loss step、CPU/CUDA/Python/NumPy RNG。不得与正在运行的进程同时恢复。

读取已保存结果生成真实进度图（CPU，不增加训练更新）：

```bash
"$PY" -B "$TASK/code/render_progress.py"
```

`local_results/single_M*_step*/raw_mm.ply` 为毫米原始零面，`sdf_*_model.npy` 为网络单位原始 SDF（XYZ轴序；毫米值乘10.053），没有删除组件/平滑/补洞。`evaluation.npz` 按原始 Pixel ID保存逐观测首交点和面标签。checkpoint 索引在 `metrics/*_CHECKPOINT_INDEX.json`；大文件仅本地。

图中统一显示域与模型域相同；原始 HERO 全范围文件保持不变。原面清理比较仅按现有Mask有效性引用原面，不移动顶点，不参与神经预测。所有三 CORE 摄像资格仍 INSUFFICIENT_EVIDENCE。

完成单参考后必须报告并等待三 CORE资源安排审阅；不自动扩大视角/组别、重跑 HERO、读取GT或修改DXY。完整任务结束后还需研究者和PM验收，不能自行升级主线。
