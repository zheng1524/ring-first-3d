# 复现与结果恢复

运行根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_012`。

环境继续使用`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`、父实验的runtime/packages与runtime/pytorch3d（官方源码e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31）、Blender5.0.1。无下载新网络或框架。九例初值、相机/Mask/原生深度、权重与点对按PREOPT_FREEZE恢复；011历史文件受HISTORY_011_PROTECTION保护。

不要在已有交付目录直接重跑训练或冻结命令。完整重现实验必须建立独立副本，按输入SHA恢复同一数据，保持父级环境/渲染源码布局。Git不包含大型原始数据、全部Mesh与checkpoint，单独clone无法重建未上传资产。所有本地文件路径/SHA见LOCAL_RESULTS_INDEX。

在原实验父目录下用`code/prepare_replay.py --output /绝对路径/同一runs目录/REPLAY_012`可建立空白独立副本；入口拒绝覆盖任何已有目录，仅复制011冻结输入和初始化支持缓存，不复制012预测/检查点/GT。随后在新副本执行以下命令，不能在交付根目录重复执行。

独立副本中的原执行入口：

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY -B code/preflight.py
$PY -B code/freeze.py
$PY -B code/run_serial.py
$PY -B code/freeze_and_scale.py
$PY -B code/evaluate_native.py
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --factory-startup --python code/blender_geometry_checks.py -- /绝对路径/独立副本
```

每例停止于300接受、800提案、连续80拒绝或数值故障的最先条件。真正达到的接受里程碑才保存ACCEPTED_N；未达到的不能生成伪造中间Mesh。FINAL始终是最后接受状态，不按GT或HOLDOUT选最好轮次。NPZ中V为原世界毫米坐标，F为观测可参与面，F_solid含推断闭合面，inferred_base_faces必须随网格保留；PLY单独打开不能辨认其观测身份。

PT保存完整位移参数、Adam矩/时钟、实际接受数/提案数、NumPy/Torch/CUDA状态和配置。恢复还必须保持同一初值、基底约束、冻结支持缓存及渲染/深度实现，不能只读顶点声称无缝续训。本轮完成后不自行继续。

只有PREDICTIONS_FROZEN_BEFORE_GT和SCALE_LOCK_BEFORE_GT形成后，才建立GT_SOURCE_LOCK。身份、单位与作者基底证据按实际来源审计，不凭预测形状猜测。允许对应GT缺失，必须保留九例NaN与原因。

```bash
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --factory-startup --python code/export_blender_gt.py -- /绝对路径/独立副本
$PY -B code/validate_gt.py
$PY -B code/rigid_metrics.py
$PY -B code/figures_native.py
$PY -B code/figures_gt.py
```

ICP严格with_scaling=False，Ring尺度只在此前核验一次，转换另存aligned目录，不覆盖原世界预测或相机。三维指标均标注After Ring-based Metric Recovery and 6-DoF Rigid Alignment；2D维持原始相机关系，不将刚性对齐的模型单独投回未变相机。

Dxy为同一作者基底方向的凸包最大投影Feret；高度缺少可信基准时NOT_EVALUABLE。H95采用相同面积采样定义。表面距离分别说明观测支持代理、未观测背面与推断盖；完整GT到预测的距离并不只代表可见面误差。体积IoU是固定Sobol占据采样估计，不能称精确布尔体积；推断/不可靠底盖仅报告占据代理，非闭合或自交实体严格IoU不可评价。无GT回填、无DXY主线修改。
