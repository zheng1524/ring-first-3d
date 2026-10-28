# 本地复现

已有冻结输入不在public仓库；完整路径与SHA在`provenance/INPUTS_FROZEN.json`。Python使用`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（3.12），Open3D 0.19.0只读vendor路径由`code/common.py`绑定；NumPy/SciPy/OpenCV/Trimesh/Matplotlib及Noto CJK字体沿用已验证环境。`real_p0_renderer.py`、`SameCameraScene`及原C0绘图函数SHA保留。

先进入本轮独立工作树：

```bash
cd /home/liu/ring_first_3d_grazing
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/reproduce.py --verify-only
```

仅重绘本轮已有真实A→B图（不运行清理/配准/评价）：

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/visualize.py --stage AB
```

完整算法顺序（仅在新的独立输出目录运行，不能在当前交付目录直接重跑）：`prepare.py → test_small.py → cleaning.py → aggregation.py primary → anchors.py → aggregation.py → evaluate.py → supplemental.py → visualize.py → validate.py → deliver.py`。`reproduce.py --fresh-replay`会将本任务小型代码/固定配置/任务文本复制到自己的`runtime/replay_<UTC>/`，使用同一批只读历史输入，禁止覆盖已有结果；不推送重放产物。完整重放约数分钟，生成较多本地点云/图像。

无需HERO、GT、Dxy或网络。所有点云采用毫米；GLB序列化米；NPZ保存精确XYZ与原索引。原始相机不变；跨视频H是派生候选，不更改正式pose文件。当前默认核验，不会自动重复科研实验。
