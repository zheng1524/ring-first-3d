# 复现

所有命令在仓库根目录执行；不在DXY或旧科研主线写入。

```bash
R=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
```

输入、官方PyTorch3D环境与已有权重引用见`assets_index`。原九例精确复制012的输入（即011FINAL）；新病例的名单在`config/NEW_CASES_LOCKED.json`，输入流为009成功脚本的任务内路径适配。为避免覆盖，已有完整运行不可直接重跑同一路径，应复制本运行目录至独立复现位置后设置`E4_RUN_DIR`，保留来源和SHA。

```bash
# 新输入构建，仅首次执行；大视频及模型只读引用
$PY -B "$R/code/prepare_new_case.py" G10
$PY -B "$R/code/prepare_new_case.py" G11
$PY -B "$R/code/build_new_inputs.py"
# 新病例低维初始化和011配方流程见initialization/code及runtime/NEW_*日志
# 完整正式学习：串行GPU，不使用GT/留出选模型
$PY -B "$R/code/gradient_preflight.py"
$PY -B "$R/code/pilot_driver.py"
# 只有上述所有正式预测完成，才能打开GT门禁
$PY -B "$R/code/freeze_scale013.py"
$PY -B "$R/code/evaluate_native.py"
```

`pilot_driver.py`独立保存A0–A3、O0–O4、一次组合核验、完整012复现和统一11例最终模型；已完成FINAL会跳过。预注册参数与最终选择不同文件保留。各臂`assets_index/PREOPT_FREEZE.json`锁定实际代码、输入、配置SHA，训练开头逐项核对。

完整checkpoint位于`arms/*/local_results/G*/`及最终`local_results/G*/FINAL.pt`，包含自由顶点参数、Adam、候选/接受计数、numpy/torch/CUDA随机状态与配置。它们是本轮恢复材料；恢复时还必须使用同一几何guard的初始和最后接受签名样本，以及同一固定损失调度计数。不可仅加载模型权重宣称无缝续跑。当前驱动刻意禁止覆盖既有FINAL，没有自动延长预算。

冻结预测及Ring尺度后，GT只读导出、有效性核验、统一最佳刚性评价和图片：

```bash
# GT_SOURCE_LOCK和新增来源核对必须先生成，不能反向参与优化
BLENDER=/home/liu/blender/blender-5.0.1-linux-x64/blender
$BLENDER -b --python "$R/code/export_blender_gt.py" -- "$R"
$PY -B "$R/code/validate_gt.py"
$BLENDER -b --python "$R/code/blender_geometry_checks.py" -- "$R"
$PY -B "$R/code/best_rigid.py"
$PY -B "$R/code/visual013.py"
$PY -B "$R/code/figures_body_alignment.py"
$PY -B "$R/code/report013.py"
```

详细路径和输出见`RESULT_INDEX.md`。NPZ/PLY的世界坐标单位mm；GLB如导出会换算为标准m并明确记录，不改变科学坐标。没有额外平滑、删除、补洞或GT驱动后处理。

追加预注册`02_OPTIMIZER_SCALE_AMENDMENT.md`之后，实际串行驱动改为：

```bash
$PY -B "$R/code/driver_amended.py"
$PY -B "$R/code/freeze_scale013.py"
```

旧驱动只在其已运行子任务保存FINAL后停止，记录`runtime/DRIVER_REPLACEMENT.json`，既有运行跳过，不覆盖重跑。O3N使用`train_normalized.py`，其他臂仍用冻结的原013训练脚本；原012完整重现仍使用`train012_exact.py`。最初协议/源码hash和追加修正的hash分别保留。
