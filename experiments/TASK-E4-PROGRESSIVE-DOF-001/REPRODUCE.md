# 一次渐进运行复现

当前记录已完成，不能删完成标记重启。新复现应复制代码到另一个隔离目录，并生成真实路径/SHA回执；不得覆盖本轮或Gate A。

本轮复用 `../TASK-E4-2D3D-OBSERVABILITY-001/inputs` 下BASE_FIELD、BASE_SOURCE_MESH、RING_CAD、CAMERAS及五份TARGET PNG的原字节，config/SOURCE_GATE_A_PROTOCOL来自其原协议；**不复制GT底场、不重新导出或渲染实验数据**。GT仅后验读取原 `audit_only/NATIVE_CAD_GT.npz`，它不是预测底场。模型初值取完全相同的Ring规则P0，local参数均0。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
EXP=experiments/TASK-E4-PROGRESSIVE-DOF-001
```

新目录复制上述冻结输入、代码和SOURCE_GATE_A_PROTOCOL后：

```bash
"$PY" -B "$EXP/code/prepare.py"
"$PY" -B "$EXP/code/checks.py" P0
```

prepare只生成独立空间评价查询点/本轮配置，不生成Mask或GT。P0的V/F必须与原文件完全相同，六方向预期仿射误差<1e−6mm，防火墙拒读GT/副本外几何；若合同失败不得运行优化。

运行前提交代码/协议（本记录668dbe1），生成assets_index/PREOPT_FREEZE.json。格式为`{"commit":实际commit,"files":[{"path":真实绝对路径,"sha256":实际SHA,"bytes":大小}]}`，枚举本轮code、config、inputs及01_PROTOCOL，不含GT。不能照抄本记录路径冒充新冻结。

```bash
"$PY" -B "$EXP/code/fit.py" S1
"$PY" -B "$EXP/code/select_kernels.py"
# 仅KERNEL_SELECTION.eligible为True时：
"$PY" -B "$EXP/code/checks.py" LOCAL
```

S1最后迭代、核中心JSON、选择CSV/JSON、LOCAL_ZERO_CONTRACT均在S2前绑定SHA，结构见assets_index/S2_DYNAMIC_FREEZE.json。S2的START继承S1 FINAL，不按GT/留出选择。

```bash
"$PY" -B "$EXP/code/fit.py" S2
# 仅CENTER_RELEASE_GATE.released为True时运行以下两条；本记录为False，未运行。
"$PY" -B "$EXP/code/checks.py" CENTERS
"$PY" -B "$EXP/code/fit.py" S3
```

两核幅值各有符号约束，中心只能由拟合残差medoid选取，半径1.8mm固定。S2维度8；若信号门槛满足，仅释放有贡献核的中心，可能11/14维，不释放零幅值无贡献核。阈值/预算预先冻结，不为通过而改参数。

```bash
"$PY" -B "$EXP/code/freeze_outputs.py"
"$PY" -B "$EXP/code/final_probe.py"
"$PY" -B "$EXP/code/evaluate.py"
"$PY" -B "$EXP/code/diagnose.py"
"$PY" -B "$EXP/code/figures.py"
"$PY" -B "$EXP/code/report.py"
"$PY" -B "$EXP/code/validate_delivery.py"
```

全部优化结果冻结之后才能打开GT。final_probe只做已登记数值探针，无新优化/选模。evaluate中的全局/扩张/收缩分量是固定最终参数的代数诊断，不替代正式输出、不变成额外训练臂。

本地真实零面Mesh：`local_results/P0/BODY_mm.ply`、`local_results/S1/FINAL/BODY_mm.ply`、`local_results/S2/FINAL/BODY_mm.ply`；同目录MODEL.npz保存q、V/F。每轮也保留。模型由原参考SDF及q/核中心重算，单位mm；各向异性组合字段不伪称严格单位梯度SDF。没有平滑、补洞、删面等几何后处理。

绝对路径/SHA和固定采样/J矩阵/分量数据见assets_index/LOCAL_RESULTS.json；小型stdout回执在run_receipts。完整轨迹、每源loss、几何和GT指标在metrics。不上传大输入/GT/Mesh原始数据。

Python3.12、NumPy1.26.4、SciPy1.15.3、Torch2.7.1、Open3D0.19、trimesh5.1.1、FCL0.7、Blender5.0.1复用旧环境，无新框架/权重下载。官方Kaolin原样DMTet及许可保留。CPU运行、-B防止在历史只读路径写缓存。Gate B/C/D、其他病例、GPU或训练均未执行。
