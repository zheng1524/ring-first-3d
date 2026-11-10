# REPRODUCE

环境沿用现有 Python/PyTorch/PyTorch3D/Open3D/Blender，不下载模型。当前结果已冻结；新运行必须复制 code、config初始项和协议到另一个隔离目录，再执行以下顺序。不要对原016调用 prepare/freeze 或恢复优化。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
cd /home/liu/ring_first_3d_e4_sdf_localization/experiments/新的016复现副本
$PY -B code/prepare016.py
```

先依次设置 `E4_RUN_DIR` 为新副本下 `arms/DIAGNOSTIC`，运行 `diagnose016.py G03`、`diagnose016.py G01`、`diagnose016.py G02`。这些只前向、反向与影子候选，不提交优化。

取消该环境变量后执行 `freeze016.py`，然后 `run016.py`，串行完成13条新真实路线。S0和MECH_015_B始终只读引用015，不重新训练。配置、世界单位和输入ID均以冻结JSON为准。

数值诊断在 DIAGNOSTIC 环境下分别执行 `numeric016.py`、`discrete016.py`、`grouping016.py`、`raster_branch016.py`；最后 `CUBLAS_WORKSPACE_CONFIG=:4096:8 $PY -B code/binning016.py`。分箱/固定片元只用于诊断，不改变真实训练后端。已知粗分箱不确定性意味着固定随机种子不保证G02逐比特复现，原始输出与SHA已保留。

虚拟控制：

```bash
$PY -B code/virtual_prepare016.py
$PY -B code/virtual_gate016.py
```

第二条会重现旧分辨率Mask门禁失败；必须保留失败。按已登记网格修复，以原GT、CAD和相机直接生成320目标：

```bash
/home/liu/blender/blender-5.0.1-linux-x64/blender -b --factory-startup -t 2 --python-exit-code 1 --python code/render_virtual_grid016.py
$PY -B code/cache_virtual_grid016.py
$PY -B code/virtual_gate_grid016.py
```

修复后门禁通过才运行各虚拟arm：设置其 E4_RUN_DIR，依次 `virtual_probe_grid016.py`、`train_virtual_grid016.py virtual_Ip`。`resume_gpu016.py` 是本次工程恢复及实际历史快照追踪的串行驱动，当前原目录已经完成，不应重跑优化。真实步骤回放示例：

```bash
E4_RUN_DIR=/绝对路径/新副本/arms/DIAGNOSTIC $PY -B code/actual_trace016.py G03 /015/实际快照/MECHANISM_0001.npz OLD_B_FIRST
```

GPU完成后 `evaluate016.py` 要求 REAL_PREDICTIONS_FROZEN 和 VIRTUAL_PREDICTIONS_FROZEN，先核对全部预测和Ring尺度再读取真实GT。评价只使用冻结预测，不选模型或回改超参数。随后依次运行 `depth_audit016.py`、`ring_audit016.py`、`coupled_observability016.py`、`report016.py`、`append_interpretation016.py`、`figures016.py`、`delivery016.py`。

原始RGB/Mask/HERO/Blender资产和完整.pt不随Git上传，绝对路径与SHA在来源/运行清单。全部新.pt包含参数、Adam、随机状态、actual attempt、接受计数；未来恢复应使用新派生目录并保持源哈希，不覆盖本轮FINAL。
