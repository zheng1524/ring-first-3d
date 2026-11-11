# 021 复现

工作树`/home/liu/ring_first_3d_e4_sdf_localization`；分支`exp/TASK-E4-RING-ANCHORED-JOINT-BA-021`，根目录`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021`。复用既有Python3.12/PyTorch/PyTorch3D/OpenCV/SciPy/Open3D，无新模型下载。完整输入在config/FOUR_GROUP_INPUTS.json及020只读链接；原始大型数据不在Git，按绝对路径+SHA恢复，缺失不得替换。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
T21=experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021
# 创建新的空白回放目录，不复制历史预测，不覆盖交付目录。
REPLAY21=/home/liu/ring_first_3d_e4_sdf_localization/replays/021_fresh
$PY -B $T21/code/setup_replay021.py --output "$REPLAY21"
T21=$REPLAY21
$PY -B $T21/code/prepare021.py
$PY -B $T21/code/identity021.py
$PY -B $T21/code/track_contactsheet021.py
$PY -B $T21/code/weight_audit021.py
$PY -B $T21/code/assets021.py
$PY -B $T21/code/gate021.py
$PY -B $T21/code/tolerance_check021.py
$PY -B $T21/code/raster_pixel_audit021.py
$PY -B $T21/code/ba021.py
$PY -B $T21/code/eval021.py
$PY -B $T21/code/hero_common021.py
$PY -B $T21/code/rotation_audit021.py
$PY -B $T21/code/identifiability021.py
$PY -B $T21/code/shadow021.py
$PY -B $T21/code/per_view021.py
$PY -B $T21/code/group_audit021.py
$PY -B $T21/code/source_geometry021.py
$PY -B $T21/code/reverse_ring021.py
$PY -B $T21/code/covisible021.py
$PY -B $T21/code/body_error021.py
$PY -B $T21/code/coverage_figures021.py
$PY -B $T21/code/collision_figures021.py
$PY -B $T21/code/visualize021.py
$PY -B $T21/code/group_reports021.py
$PY -B $T21/code/g03_gain_diagnostic021.py
$PY -B $T21/code/report021.py
$PY -B $T21/code/verify021.py
```

顺序执行或仅将明确独立的等待脚本放后台。已有FINAL时不重新优化；缺FINAL而有ITER_*.pt则恢复q/X/Adam/迭代。初始矩阵与点、全部100候选、拒绝原因、每10步完整状态均保存。恢复旧段耗时另外列，不伪称无间断墙钟。

可只重画已冻结evaluation上的图，不需要再次BA/HERO。完整GLB只在本地索引，不能把未上传文件说成在Git。单位从头到尾mm，GLB标准m仅固定.001换算。
