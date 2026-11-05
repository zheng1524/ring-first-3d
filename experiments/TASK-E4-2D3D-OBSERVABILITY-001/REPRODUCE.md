# Gate A 复现与本地结果

这是原生CAD单场景短程审计，不是旧同核控制的续拟合。当前记录已完成，不能删除完成标记覆盖结果。复现请在新的隔离目录复制本轮代码/协议并重新生成路径和SHA回执。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
EXP=experiments/TASK-E4-2D3D-OBSERVABILITY-001
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
BLENDER=/home/liu/blender/blender-5.0.1-linux-x64/blender
```

原始`.blend`、Ring和相机路径/SHA见 `SOURCE_AND_FIREWALL_AUDIT.md`、`assets_index/INPUT_MANIFEST.json`；不复制整套原始数据。新目录只从旧实验复制原字节CAMERAS.json和RING_CAD.npz。**禁止复制旧BASE_FIELD、旧BASE_SOURCE_MESH或旧人工目标作为N0初始化/目标。**

新副本中依次执行（将`EXP`改为新隔离目录，并确认common.py的R解析到它）：

```bash
"$PY" -B "$EXP/code/prepare_p0.py"
"$BLENDER" --factory-startup --background --threads 2 --python-exit-code 2 --python "$EXP/code/export_native.py"
"$BLENDER" --factory-startup --background --threads 2 --python-exit-code 2 --python "$EXP/code/render_blender.py"
"$PY" -B "$EXP/code/projection_gate.py"
"$PY" -B "$EXP/code/firewall_probe.py"
"$PY" -B "$EXP/code/synthetic_bias.py"
"$PY" -B "$EXP/code/observability.py"
"$PY" -B "$EXP/code/audit_sources.py"
```

旧同核诊断只读旧两组完整本地资产；其旧GT/FINAL原损失必须与已冻结值一致到1e−12，防止目标身份混淆。它的GT参数不得写入N0配置。矩形半像素、J.T@residual梯度复核结果见NUMERICAL_CONTRACT_TESTS/JACOBIAN_GRADIENT_DIAGNOSTIC；它们不改训练目标。

正式拟合前提交协议/代码，并生成 `assets_index/PREOPT_FREEZE.json`：结构为`{"commit":实际commit,"files":[{"path":真实绝对路径,"sha256":实际文件哈希,"bytes":文件大小}]}`，枚举本轮code、inputs、config、01_PROTOCOL及MASK_ONLY_INITIALIZATION。不含audit_only GT；不能照抄其他路径回执。当前冻结提交为cb959b3，已完成两臂时未读原生GT三维评价。

```bash
"$PY" -B "$EXP/code/fit.py" ORIGINAL
# 只有SYNTHETIC_OBJECTIVE_AUDIT明确触发才执行这一臂；本记录触发为True。
"$PY" -B "$EXP/code/fit.py" SUBPIXEL_TARGET
"$PY" -B "$EXP/code/evaluate_native.py"
"$PY" -B "$EXP/code/self_audit.py"
"$PY" -B "$EXP/code/volume_validation.py"
"$PY" -B "$EXP/code/normal_ray_audit.py"
"$PY" -B "$EXP/code/figures.py"
"$PY" -B "$EXP/code/report.py"
"$PY" -B "$EXP/code/validate_delivery.py"
```

evaluate_native必须等两臂完成，先写ALL_PREDICTIONS_FREEZE再读原生GT。所有几何和原始粗节点体积评价保留；volume_validation只做一次固定2^18 Sobol积分精度核验，原因是原生平底的粗节点混叠，不更新模型、不选参数、不改原表。

实际Mesh/四参数：`local_results/ORIGINAL/FINAL/BODY_mm.ply`和`MODEL.npz`；配对结果为`local_results/SUBPIXEL_TARGET/FINAL/`。初始/每轮均保留。弱模式Mesh在`local_results/A2_weak_*/`等目录。全部公制mm，原始Mesh没有几何平滑/补洞/删面。数据、GT、固定J/查询点、Sobol点集和全部本地Mesh的绝对路径/SHA见 `assets_index/LOCAL_RESULTS.json`。

本机复用Python3.12、NumPy1.26.4、SciPy1.15.3、Torch2.7.1、Open3D0.19、trimesh5.1.1、FCL0.7.0.11、Blender5.0.1。common.py明确加入旧环境vendor和FCL路径，-B禁止在只读历史路径写缓存。没有安装skimage、PyTorch3D/新神经框架，没有GPU或训练权重更新。官方Kaolin原样torch-only DMTet源与Apache许可保留。

Gate B/C/D仅在config中登记，未执行。完成Gate A即停止，后续不得自动运行。
