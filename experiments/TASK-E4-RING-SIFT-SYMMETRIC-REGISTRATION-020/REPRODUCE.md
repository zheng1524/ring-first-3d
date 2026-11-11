# 020 复现

工作树`/home/liu/ring_first_3d_e4_sdf_localization`，分支`exp/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020`，任务目录`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020`。沿用019已安装Python3.12/PyTorch2.7.1cu128/P3D commit e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31；无新大型依赖。

源码复用、输入SHA和完整RoMa来自UPSTREAM_READONLY、INPUT_MANIFEST和config。inputs/G01、019原SIFT缓存与原Ring证据是只读链接；不重跑019或改写旧目录。复制本实验到独立回放目录时，需要将common.R指向独立输出，保持所有上游路径只读。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK020=experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020
$PY -B $TASK020/code/setup_inputs020.py
$PY -B $TASK020/code/prepare020.py
$PY -B $TASK020/code/features020.py
$PY -B $TASK020/code/named_candidate020.py
$PY -B $TASK020/code/gate020.py
$PY -B $TASK020/code/feature_gate020.py
$PY -B $TASK020/code/validate_landmarks020.py
$PY -B $TASK020/code/visibility_check020.py
$PY -B $TASK020/code/optimize020.py
$PY -B $TASK020/code/evaluate020.py
$PY -B $TASK020/code/layer_diagnostic020.py
$PY -B $TASK020/code/collision_check020.py
$PY -B $TASK020/code/audit020.py
$PY -B $TASK020/code/figures020.py
$PY -B $TASK020/code/reports020.py
$PY -B $TASK020/code/verify020.py
```

完整输入链接和21份HERO评价名单已经冻结，不需要重新推理深度。HERO文件缺失则必须按原索引恢复原源，不能替代；源SHA在config/HERO_EVALUATION_SOURCES.json。上述prepare仅重建协议，不应在交付冻结目录覆写；请用独立副本。audit可与优化同时等待，但HERO/Body/HOLDOUT评价只在全pose冻结后运行。独立图像可从已有evaluation与模型缓存重画，不需要再次优化。

优化保存q、Adam、迭代数与初始完整T；后续重启可加载ITER.pt，无FINAL的路线从对应状态继续。当前运行采用provenance/runtime_source_before_resume_support记录的原源码；新增恢复分支不更改本轮运行损失。日志seconds是该次进程运行时间，若恢复应单独累计。

I/O由实体CAD occluding edges+O3D自遮挡和语义分类产生，Torch投影距离求导；M用官方PyTorch3D；C用实际r5.6中心线。不用三平面圆近似管材边界，不用body遮挡主线。所有模型输出计算mm，GLB仅标准米(.001单位导出)，不是估计scale。
