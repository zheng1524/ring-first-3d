# 复现与恢复

本地根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018`。

Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`。环境及PyTorch3D commit见 `provenance/ENVIRONMENT.json`；完整HERO权重仅复用本地2.42GB checkpoint，SHA见 `provenance/HERO_MODEL.json`。不下载新模型，不修改旧数据。

## 已执行的数据恢复顺序

在仓库根目录，依次使用同一Python执行：

```bash
$PY experiments/TASK-E4-HERO-BODY-ADAPT-018/code/prepare018.py
$PY experiments/TASK-E4-HERO-BODY-ADAPT-018/code/infer018.py
$PY experiments/TASK-E4-HERO-BODY-ADAPT-018/code/clean018.py
$PY experiments/TASK-E4-HERO-BODY-ADAPT-018/code/frame_audit018.py
$PY experiments/TASK-E4-HERO-BODY-ADAPT-018/code/jpeg_binding018.py
$PY experiments/TASK-E4-HERO-BODY-ADAPT-018/code/setup_arms018.py
```

以上是历史恢复顺序，不应在冻结的最终目录重跑setup，它会重建初始R1计划。正式R2使用已保存的 `config/ARM_PLAN.json`；R1保存在 `config/ARM_PLAN_R1_RETAINED.json`。`repair_full018.py`记录FULL native像素包含口径的修复并保留R1观测。当前clean018已经包含最终FULL逻辑；从头复现可直接产生最终观测，无需人为先制造R1缺陷。

## 实际正式训练与断点恢复命令

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/check_inputs018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/serial018.py
```

serial018按冻结计划依次执行G06→G05→G01→G03，共14路线。每病例/路线配置另存 `arms/<arm>/config/<group>_ARM.json`；运行时 `ARM.json`是串行当前指针，不是替代逐病例配置。优化器、学习率、动量、随机状态和实际接受次数均在`.pt`保存；如果存在FINAL则跳过，只有未完成臂才从最大attempt检查点严格恢复。**不得删除FINAL来重跑或挑选更好中间状态**。

例如单臂未完成恢复：

```bash
E4_RUN_DIR=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/arms/B2_TRUSTED_COH16 \
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/train018.py G06 --resume
```

如果要独立从头复现，应建立新的018副本：复制小型code/config与清单、对冻结RGB/Mask/pose/HERO建立只读路径或链接，保留018源码相对根目录结构，清空**新副本**的arms/local_results/evaluation。不得清理或覆盖本次冻结结果及015/016/017。原生HERO和017资产均可按SHA复用；新的推理只在缺失时发生。

## 冻结后评价与可视化

以下只在14条FINAL全部完成后执行：

```bash
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/freeze018.py
E4_RUN_DIR=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/evaluation \
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/evaluate018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/conflicts018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/figures018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/summarize018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/paired018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/aggregate_residuals018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/export_sources018.py
$PY -B experiments/TASK-E4-HERO-BODY-ADAPT-018/code/final_validation018.py
```

HOLDOUT读取只有评价阶段被允许。跨来源HERO差异仅为只读几何代理，绝不用于反向传播、调权或挑checkpoint。没有真实GT评价、Blender对齐或Dxy改动。

## 产物

- `hero_fit/<id>` / `holdout/hero/<id>`：每个原生来源及标签、TRUSTED真实面片子集、原生像素映射。
- `arms/<arm>/local_results/<group>/FINAL.npz` / `FINAL_mm.ply`：真实共享主体，毫米坐标，无后处理。
- `arms/<arm>/local_results/<group>/*.pt`：完整优化器恢复状态。
- `arms/<arm>/metrics`：损失、逐分量梯度、接受/拒绝、候选、运行状态。
- `evaluation/metrics`：固定分母逐视角指标、独立64阶Ring检查、B0配对比较。
- `figures`：精选核心图与各组完整图。
- `RESULT_INDEX.json`：所有本地Mesh/数据/检查点的绝对路径、大小、SHA256。

未上传Git的原生数据和检查点保存在本机持久磁盘；不能将只有本地路径的索引冒称为已完成异地备份。

实际训练Torch/NumPy种子为继承代码中的20261108（已在14个INITIAL.pt核验），PROTOCOL.seed=20261110的元数据偏差公开保留，见ACTUAL_RUNTIME_CONTRACT.json；旧深度采样器使用单独固定的20261110。不应把改变种子的再运行称为本次原样复现。
