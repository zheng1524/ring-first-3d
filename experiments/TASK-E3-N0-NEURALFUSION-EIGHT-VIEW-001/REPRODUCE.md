# Reproduce

首次算法/输入冻结提交：`b9711c8`。原始私有RGB/HERO/相机/CAD和官方权重不复制进Git，实际路径/SHA在provenance及config/EXPERIMENT_FROZEN.json；全部本地中间状态在LOCAL_RESULTS_INDEX.json。PLY数值单位mm，GLB为SI米。

环境：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`，Python3.12、numpy1.26.4、scipy1.15.3、torch2.7.1+cu128、Open3D0.19（原vendor）、scikit-image0.23.2（上一轮task隔离runtime/python），RTX3060 6GiB。没有修改共享环境；官方NF commit/权重在TECHNICAL_VERSION_LOCK.md。

## 执行顺序及保护

本轮已完成，**不要在正式结果目录重复infer/prepare清理**。infer阻止覆盖任何已完成前缀；Gate及prepare也有一次运行/冻结保护。preflight/version_lock是首次建立工具，冻结后禁止覆盖。新增规则改动必须新记录，不能篡改当前实验。

原始执行：用户确认首版文档不存在→version_lock.py建立v1→camera_gate.py统一27来源→prepare.py冻结选择、单轮清理、裁剪、公制域→两组各forward完整再reverse完整→evaluate.py→diagnose.py→visibility_diagnostics.py→historical_compare.py→expansion_plan.py→figures.py→finalize.py→verify_delivery.py。所有步骤从当前任务code执行。GPU只有infer.py，其他为CPU统计/显示。

## 只读复核已有结果

在仓库根执行（不启动GPU）：

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/verify_delivery.py
```

它复核26次调用、输入/源码/权重SHA、状态计数单调、固定分母、Mesh身份、照片/相机绑定、评价计数和交付文件，不进行训练或新推理。CPU重放MC的既有证据在metrics/MESH_EXTRACTION_AND_SHADING_AUDIT.csv。

## 准备隔离的相同输入复跑（不自动运行）

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/prepare_replay.py
```

该工具只在本task/runtime/replays下复制代码、冻结配置及4145点累计屏蔽ID表，从原始HERO和这些ID重新生成全部13来源/26份派生输入与crop，逐SHA精确复原；建立只读可视化/历史metadata链接，并CPU验证身份；打印独立任务根路径。不依赖隐藏的旧V6缓存副本，不创建新仓库，不启动GPU。需要现有私有原始资产和已审计Gate A runtime仍在。实测恢复结果见provenance/RESTORE_INPUTS_CHECK.json。

如未来单独授权相同预训练复跑，在打印的新任务根中使用：

```text
python -B <new-task-root>/code/infer.py G01_004 forward
python -B <new-task-root>/code/infer.py G01_004 reverse
python -B <new-task-root>/code/infer.py G06_004 forward
python -B <new-task-root>/code/infer.py G06_004 reverse
```

严格8/8/5/5，26次，prefix共享状态，逆序空场。低几何指标不是提前停机条件；输入/尺度/程序无效才停止。PyTorch/CUDA sparse聚合浮点顺序可能引入小数值差异，不能保证跨硬件bitwise几何相同；单次所用权重及输入必须bitwise不变。

评价/显示可在隔离目录按上述CPU步骤生成；每次保存原始field/known及MC哨兵副本，禁止用几何平滑改输出。支持类别是可见性约束的未校准代理；所有Raw分母、MISS、CAD遮挡、未入源和清理移除均保留。三种PLY显示几何须完全一致。

历史Open3D只评价读取D0 G1，未生成本轮预测；无G06历史对照就返回NOT_AVAILABLE。本轮不创建新TSDF，不从其他路线生成预测，不读GT/Oracle/旧测量值。
