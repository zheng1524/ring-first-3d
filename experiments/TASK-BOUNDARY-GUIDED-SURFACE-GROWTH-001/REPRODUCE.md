# 缓存复现及版本

本轮最终预测已经停止。以下默认只读已有预测，不恢复HERO、配准或生长。公开仓库不含输入、权重及完整几何缓存；需要本机已有冻结路径。

```bash
cd /home/liu/ring_first_3d_boundary_growth
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
TASK_DIR=experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001
PYTHON_BIN=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PYTHON_BIN" "$TASK_DIR/code/reproduce.py" verify
"$PYTHON_BIN" "$TASK_DIR/code/reproduce.py" index
# 重绘原有图（CPU；保留参数及来源，覆盖同名派生图，请先复制需要保留的版本）
"$PYTHON_BIN" "$TASK_DIR/code/reproduce.py" figures
# 可选重新核算冻结预测的评价；不产生新预测，但会新增评价冻结manifest
"$PYTHON_BIN" "$TASK_DIR/code/reproduce.py" evaluate
```

Python 3.12环境；依赖numpy、scipy、Pillow、opencv、matplotlib、trimesh、Open3D，精确版本见`provenance/ENVIRONMENT.json`。不要用系统Python 3.8替代。

读取路径由`code/common.py`声明；14份历史参考来自上一轮注册表，22份本轮成功参考见`provenance/NEW_CASES.json`。Raw XYZ/source_uv/open mesh/完整原面、native深度、显示分辨率pack、Cleaned掩码、背景点云和所有快照均保存在`local_results/`，从原始point/face ID和每块H可复现派生几何。

实际运行顺序：`assets.py`（初始审计/选主体/恢复种子）→`run_growth.py G06_004 G07_004 G08_005`→各场景缓存续跑→G01两视频；`evaluate.py`及独立审计→`visualize.py positive/final`→`cross_sources.py`有限跨视频候选/照片图→最终核验。上述为执行记录，不是推荐重新推理的命令；CUDA已不可用，禁止把失败后再次推理当本轮完成前提。

生长前配置/实现：`GROWTH_IMPLEMENTATION_FROZEN.json`；只修复源ID调用和快照恢复的实施变更见`GROWTH_IMPLEMENTATION_REVISION_001/002.json`。参数未因评价结果更改。最终源码和受控历史依赖SHA见`FINAL_CODE_AND_SOURCE_MANIFEST.json`、`CODE_REUSE.json`。两阶段预测评价冻结分别见`PREDICTIONS_EVAL_FREEZE_001/002.json`，首阶段评价实现存档在`provenance/source_versions/`。后续增加同数据F1对照及诊断，未改预测。

实际渲染继续调用仓库`visualization/real_p0_renderer.py`、`SameCameraScene`、历史五面板及点云绘图函数。源码SHA、每图相机/边界/点大小、同视角和六方向参数见manifest与`SCENE_DISPLAY_*`、`G01_SIX_VIEW_PARAMETERS.json`。不使用平面贴图或新补面；Ring为固定CAD，背景实际XYZ仅DISPLAY_ONLY。

恢复点：`local_results/scenes/*_Final.json`及逐轮`*_Snnn.json`；005两个失败输入没有深度/XYZ。原错误停止元数据留在`local_results/recovery_audit/`，审计修正仅改停止身份，未改已接纳几何。最终审计时不再运行任何新预测。

本地图库：`visualizations/index.html`，完整几何/源索引/GLB入口见`RESULT_INDEX.md`、`metrics/OUTPUT_ASSET_INDEX.csv`。GitHub公开精选图片和小表，未上传完整缓存或GLB。
