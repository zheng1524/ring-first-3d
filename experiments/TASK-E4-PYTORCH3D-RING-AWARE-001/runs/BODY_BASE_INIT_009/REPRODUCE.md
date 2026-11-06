# 复现与恢复

本地唯一结果根目录：
`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_INIT_009`

预注册提交 e1daf3e。代码、配置、输入及预测SHA分别见PREOPT_FREEZE、SOURCE_MANIFEST、PREDICTIONS_FROZEN与LOCAL_RESULTS_INDEX。提交的小文件不包含原始视频/HERO权重/大输入；复现需本地原资产路径，不能只凭Git仓库完整运行。DXY与旧polyp_research只读。

环境沿用父实验已安装PyTorch3D、Open3D、SciPy、FCL；Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；Blender5.0.1：`/home/liu/blender/blender-5.0.1-linux-x64/blender`。依赖版本见DELIVERY_VALIDATION。无需部署新框架。

以下命令中的工作目录为上述结果根目录，使用 -B 避免写旧资产pycache：

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY -B code/delivery_validate.py
```

**已有结果只读复核/可视化**（会重写本轮派生指标/图，不会改预测；默认不需要再跑）：

```bash
$PY -B code/fixed_depth_scores.py
$PY -B code/additional_metrics.py
$PY -B code/visualize_body.py
$PY -B code/candidate_gallery.py
```

原正式顺序为 prepare_new_case.py（仅首次缺失源）、lock_and_prepare.py、base_observations.py、preflight.py、projection_gate.py、freeze.py、run_serial.py；之后冻结所有local_results再评价。**不要在交付目录重复运行准备/优化/冻结命令**，会覆盖本轮文件。若必须完整重做，先复制本轮代码与配置到独立重跑根目录，将common.py的R/输入路径适配到新根目录，保留原CASE_LOCK及所有固定规则；输入文件从本地索引按SHA复制，完成新预注册后再执行：

```bash
$PY -B code/run_serial.py
```

该程序按PROTOCOL.json串行执行九例三个固定初值，不需要训练检查点；所有低维候选由JSON参数与NPZ顶点/面保存。不要用它启动后续自由形变。独立评价命令见code/evaluate_body.py、quality_audit.py；Blender入口blender_checks.py需要任务根目录参数，参阅其文件末尾。冻结后才计算评价，不读取GT。

原生输入恢复：inputs/Gxx、depth_observations；第九例新源new_input_pipeline/groups/G09；排除的重复源单独保存new_input_pipeline_DUPLICATE_G08_EXCLUDED。修正过的路径映射在DUPLICATE_PATH_RELOCATION.json，禁止把重复源作为G09读取。所有原相机、HERO、Mask文件保持不变。

每个模型的NPZ包含V、F、F_solid与inferred_base_faces；参数JSON包含p、meta及实际阶段记录。毫米PLY可直接查看；冠面推断闭合底面仅用于记账，非观测表面。没有模型权重/optimizer checkpoint，因为本轮是低维SciPy拟合。
