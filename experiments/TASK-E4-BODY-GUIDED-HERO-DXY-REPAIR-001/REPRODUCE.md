# 复现

环境：Body/评价使用 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；DXY使用 `/home/liu/new-polyp-dxy/.venv/bin/python`；版本见provenance/ENVIRONMENT.json。所有实验资产绝对路径和SHA见provenance/INPUT_SHA.json与config/SOURCE_BINDING.json。原始75缓存不上传Git；无原始资产时只能审阅已交付冻结结果，不能声称完整重跑。

本任务的已冻结目录不能覆盖运行。要完全重跑，先在另一个独立工作树/目录保留相同repo历史路径结构并复制本任务代码，删除新副本中的预测/冻结产物（只针对新副本），然后按以下顺序运行；不得删除本任务当前冻结结果。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK=experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001
$PY "$TASK/code/prepare_inputs.py"
$PY "$TASK/code/run_dxy.py"
$PY "$TASK/code/qualify_views.py"
$PY "$TASK/code/contracts.py"
$PY "$TASK/code/run_fits.py"
$PY "$TASK/code/evaluate.py"
$PY "$TASK/code/legacy_compare.py"
$PY "$TASK/code/visualize.py"
$PY "$TASK/code/validate.py"
$PY "$TASK/code/report.py"
```

无需新训练或下载权重。冻结求解脚本固定三初值×60nfev，仅2D损失，无HERO/GT。DXY逐源记录及全部优化TRACE JSON/NPZ保留；worker日志在runtime。可在当前目录安全重跑validate.py进行只读输入/冻结/公平性验证；其输出只更新验证回执，不优化。Git交付仅精选全视角图集与六方向图、报告、小表、冻结JSON和主体小NPZ/PLY；全部逐帧独立PNG、每像素投影/Jacobian/NPZ轨迹留在本地并列SHA索引。
