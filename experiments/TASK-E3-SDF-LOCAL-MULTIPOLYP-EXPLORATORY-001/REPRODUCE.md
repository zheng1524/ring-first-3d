# 本地执行与完整恢复

工作树 `/home/liu/ring_first_3d_e3_sdf_multi`，分支 `exp/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001`。

```bash
cd /home/liu/ring_first_3d_e3_sdf_multi
TASK=experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
```

准备顺序已完成，当前不得重新初始化：prepare_assets.py（当前Gate复核/固定名单/只读复用/新G08同规则清理）→ build_ports.py（受控复制/差异）→各场景 prepare.py（官方Git blob与神经输入）→ performance.py（每源一次不更新GPU全梯度）→audit_handoff.py→freeze_exploration.py。各脚本包含禁止覆写守卫；需复现时在新的隔离目录按原资产SHA重建。

首次串行运行：

```bash
"$PY" -B "$TASK/code/run_all.py"
```

G01_004→G06_004→G08_005，各自同一个共享三参考M1，连续累计10000步；只一个GPU训练进程。不会启动200k旧计划。完成后CPU绘图/技术报告，并按明确授权提交本独立分支的小结果，字段/检查点留本地。

检查实时状态与完整日志：`groups/场景/metrics/single_M1_STATUS.json`、`runtime/TRAIN_场景.log`。每100步日志；0/200/500/1000/2000/5000/10000永久检查点/原场/Mesh，另每1000步最新完整状态。初始模型是官方真实网络初始化，后续都是实际Adam更新结果，不是解析球替代。

若真正工程故障中断，先记录/修复原因，保持冻结代码/输入与模型目标后恢复（不要与已有进程同时运行）：

```bash
MONOSDF_SCENE=G01_004 "$PY" -B "$TASK/code/train_full.py" M1 --resume
```

对应检查点：`groups/场景/checkpoints/single_M1/latest.pt`，LATEST.json提供SHA。含model、Adam、scheduler、全protocol/execution、当前累计step/loss step、CPU/CUDA/Python/NumPy RNG、采样seed/下一步/来源循环、输入/源码SHA和累计耗时。严格恢复要求场景/源码/配置一致，不能借其他物理组的场。1000→2000→5000→10000不重置优化器。

CPU重新汇总图与报告（不增加参数更新）：

```bash
"$PY" -B "$TASK/code/deliver.py"
```

本地所有原场/输出在 `groups/场景/local_results/single_M1_stepXXXXXX/`：`raw_mm.ply`为毫米，`sdf_*_model.npy`为XYZ轴序原SDF（乘本组s转mm），`evaluation.npz`保存原生ID/首交点/MISS/面标签。空零面有原场和明确计数，不生成假Mesh。不做几何平滑、删面或补洞。LOCAL_CHECKPOINT_INDEX.json为最终检查点路径/哈希索引。

云端继续训练时，先复刻provenance/ENVIRONMENT.json的软件版本，复制独立检查点及已冻结输入/所选原始资产，按清单重映射本地绝对路径并验证所有数据SHA。不可直接复制本机虚拟环境或重新预测HERO。不同GPU的FP32运算可有微小差异，需先比较固定批次前向、Loss/梯度和一次恢复状态，再延长；不承诺跨硬件bitwise一致。云端另行确定延长目标，当前脚本仍严格停在10000。
