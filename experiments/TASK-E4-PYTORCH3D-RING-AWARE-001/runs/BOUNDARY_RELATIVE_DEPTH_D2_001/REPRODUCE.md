# 复现与本地恢复

分支：`exp/TASK-E4-PYTORCH3D-RING-AWARE-001`。预注册commit：`0d14669`。本轮根目录：
`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BOUNDARY_RELATIVE_DEPTH_D2_001`。

Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`。复用父实验`runtime/pytorch3d`与`runtime/packages`、Open3D/FCL本地包；没有安装新框架。Blender：`/home/liu/blender/blender-5.0.1-linux-x64/blender`。PyTorch3D官方源码commit见父版本回执，`p3d.py`与上一轮修复版逐字节相同。

执行顺序（源码中的R由文件实际路径决定；不得在本次冻结输出上重复运行）：

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
RUN=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BOUNDARY_RELATIVE_DEPTH_D2_001
# 新空的隔离副本中准备，历史源只读：
$PY -B "$RUN/code/prepare.py"
/home/liu/blender/blender-5.0.1-linux-x64/blender --factory-startup --background --threads 2 --python-exit-code 2 --python "$RUN/code/blender_virtual.py" -- virtual_Ip
/home/liu/blender/blender-5.0.1-linux-x64/blender --factory-startup --background --threads 2 --python-exit-code 2 --python "$RUN/code/blender_virtual.py" -- virtual_Is
$PY -B "$RUN/code/prepare_observations.py"
$PY -B "$RUN/code/projection_gate.py"
$PY -B "$RUN/code/preflight.py"
$PY -B "$RUN/code/freeze.py" before
$PY -B "$RUN/code/run_serial.py"
$PY -B "$RUN/code/freeze.py" after
# 以下全在所有预测冻结之后；不能提前读取GT三维评估调参：
$PY -B "$RUN/code/evaluate_d2.py"
/home/liu/blender/blender-5.0.1-linux-x64/blender --factory-startup --background --threads 2 --python-exit-code 2 --python "$RUN/code/blender_checks.py" -- "$RUN"
$PY -B "$RUN/code/audit_native_solids.py"
$PY -B "$RUN/code/extra_evaluate.py"
$PY -B "$RUN/code/section_audit.py"
$PY -B "$RUN/code/readonly_multiview.py"
$PY -B "$RUN/code/figures_d2.py"
$PY -B "$RUN/code/boundary_diagnostics.py"
$PY -B "$RUN/code/native_contract.py"
$PY -B "$RUN/code/validate.py"
$PY -B "$RUN/code/write_report.py"
```

检查点位于`local_results/{case}/{B,E1,E2,E3}/STEP_XXXX.pt`，含实际步数、SGD动量、offset、完整配置及NumPy/Torch/CUDA随机状态。网格及毫米V/F为同名NPZ/PLY，最终为`FINAL.npz`和`FINAL_mm.ply`，全部原始面保留。固定B复用目录以符号链接指向上一轮真实输出；迁移时需按`assets_index/LOCAL_RESULTS.json`及B回执复制实际目标，不能只复制链接。

恢复：重建同一Case/P0，`offset=state['offset']`，创建同配置SGD并`load_state_dict(state['optimizer'])`，恢复三种RNG；从`state['step']`后继续。当前train.py是固定300步一次性实验入口，并故意拒绝覆盖FINAL；扩展训练不在本轮授权中，未提供自动延长或参数搜索。所有checkpoint可完整读取和迁移，不含新调度器（本轮SGD无scheduler）。

本地大型输入、GT、完整检查点和Mesh不上传GitHub；路径、SHA、源码、表格及精选核心PNG上传。`assets_index/PREDICTIONS_FROZEN.json`证明独立GT评价之前固定预测；`HISTORY_PROTECTION.json`证明上一轮未修改；`SOURCE_MANIFEST.json`记录新源文件。复现需先核对SHA及已有依赖，不能用其他路线预测或旧测量值补齐缺失输入。
