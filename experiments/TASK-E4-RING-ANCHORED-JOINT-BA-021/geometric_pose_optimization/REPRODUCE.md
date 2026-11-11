# 最小故障复现（不启动优化）

目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/geometric_pose_optimization`。原021/020/quick、原相机/HERO/CAD/DXY严格只读。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
GEO=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/geometric_pose_optimization
# 既有INPUTS_FROZEN时prepare直接退出。全新准备需原SHA资产与原021代码。
$PY -B "$GEO/code/prepare.py"
$PY -B "$GEO/code/validate.py"
# gate失败后仅诊断，不调用geometric.solve，不运行阶段B。
$PY -B "$GEO/code/diagnose.py"
$PY -B "$GEO/code/edge_diagnostic.py"
$PY -B "$GEO/code/baseline_audit.py"
$PY -B "$GEO/code/figures.py"
$PY -B "$GEO/code/report.py"
$PY -B "$GEO/code/verify.py"
```

最小数值反例：G05的G05_key04_raw00542、q=0、axis0、h=1e−4。诊断脚本分别打印/保存固定可见集合和完整重新可见性目标；`+Inf>=40−.002`为True的单独predicate也保存。不得把该比较直接改成finite判据后自动继续；真实切线miss应保留UNKNOWN，修复和重新放行须后续人工诊断。

环境：Python3.12.13，NumPy1.26.4，SciPy1.15.3，PyTorch2.7.1+cu128；pycolmap4.2.1存在但无自定义Problem接口，未新增依赖。CPU double几何诊断；没有模型训练/GPU推理。大数组/特征/原生HERO/原始视频留本地SHA索引，不上传复制数据集。
