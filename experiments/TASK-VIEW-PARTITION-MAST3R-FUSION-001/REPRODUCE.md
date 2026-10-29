# 缓存复现与真实执行记录

工作树：`/home/liu/ring_first_3d_view_partition`，独立分支 `exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001`。仅此任务目录可写；旧任务、Dxy、P0、相机和模型均只读。真实推理已经完成，不需再运行上游模型来查看或重绘结果。

```bash
cd /home/liu/ring_first_3d_view_partition
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
task_python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
task_code=experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code
"$task_python" "$task_code/reproduce.py" verify
"$task_python" "$task_code/reproduce.py" render-D
"$task_python" "$task_code/reproduce.py" index
```

这些命令在本地依赖与缓存下核验或重绘本任务；没有训练、推理、PnP或新参数选择。`verify`写核验结果、来源身份附注和索引，不改预测数值/XYZ。完整图库：`experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/visualizations/index.html`。GitHub不包含完整输入和几何，因此不是无数据的独立公开重跑包；缺少外部只读缓存会明确报错，不伪造回退。

首次实际执行顺序及入口：

|批次|实际入口|状态|
|---|---|---|
|A|`batch_a.py` → `test_small.py` → `render.py` → `deliver.py A`|一次性冻结输入、参数、方向、Core/Transition/Holdout；存在冻结文件时拒绝重新初始化|
|B|`matching.py` → `cached_baselines.py` → `registration.py` → `render_b.py`|实际9 SIFT＋18 MASt3R新前向；2种子PnP/Ring；逐真实连通分量Open3D位姿图；旧LG/RoMa只读对照|
|C|`hero_new.py` → `hero_new.py --resume-postprocess` → `render_c.py`|实际5个新参考HERO前向；仅修复依赖后恢复已有深度后处理；原生深度SHA不变|
|D|`ownership.py` → `evaluate_d.py` → `attribution.py` → `render_d.py all` → `final_audit.py` → `report_d.py`|真实Raw/Cleaned F1/F2、隔离评价、完整场景、失败记录；这些预测产物已经冻结|

上述是实际实验调用记录；不要把重新执行B/C当作缓存重绘命令。完整参数是阶段A的`config/rules.json`与阶段D不覆盖旧键的`config/aggregation_rules.json`。阶段A–C Git提交提供逐阶段源码版本；当前HEAD包含最终包装与修复。每个阶段的冻结manifest记录当时的源码/输入SHA；`FINAL_CODE_AND_SOURCE_MANIFEST.json`绑定最终版本。旧函数AST原文复用关系见`CODE_REUSE_AUDIT.md`。

渲染调用最终仍为 `visualization/real_p0_renderer.py:draw_rgb_points` → 既有 `SameCameraScene` / `pointcloud_audit_renderer`。`render.py`逐字AST载入上轮 `camera_scene/depth_colors/scene_image/side`；`render_d.py`逐字载入既有 `five_panel`，只重新绑定本轮Cleaned source_data。Panel2粉色Polyp、蓝绿Background共享A相机轴向Z明暗，CAD黑色实体。所有B图像均只供比较，场景颜色来自A。L1–L5诊断使用原始主参考P0而非融合面，F1/F2另有P8/P9对照。

本地完整16个GLB与对应NPZ/PLY见`metrics/GLB_INDEX.csv`；各源块和删除标记见`local_results/pointcloud_blocks/`、`local_results/cleaned/`；大型资产均不上传。最终跨视频结果固定为 `G01_004_005_registration_candidate_not_fused.glb`。它是候选坐标中的独立点块，不是已通过融合验收的模型。
