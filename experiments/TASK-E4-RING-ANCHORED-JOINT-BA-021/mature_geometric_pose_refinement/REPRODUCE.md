# 复现与保全

目录 `/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/mature_geometric_pose_refinement`。Python3.12.13，SciPy1.15.3，Torch2.7.1+cu128，NumPy1.26.4。沿用已安装OpenCV/Open3D，无新大型框架/模型。Conics/M3T准确commit、完整源码SHA与许可证见vendor及MATURE_SOURCE_FETCH。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
N21=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/mature_geometric_pose_refinement
$PY -B "$N21/code/setup_inputs.py"
# 正式结果已冻结；run_videos/refine对已有FINAL只读复用，不重新初始化。
$PY -B "$N21/code/stage1.py"
$PY -B "$N21/code/run_videos.py" G01
$PY -B "$N21/code/run_videos.py" G03
$PY -B "$N21/code/run_videos.py" G05
$PY -B "$N21/code/run_videos.py" G06
$PY -B "$N21/code/evaluate_videos.py"
$PY -B "$N21/code/completeness_audit.py"
$PY -B "$N21/code/facts.py"
$PY -B "$N21/code/enrich_metrics.py"
$PY -B "$N21/code/mid_continuous.py"
$PY -B "$N21/code/figures.py"
$PY -B "$N21/code/report.py"
$PY -B "$N21/code/verify.py"
```

当前状态为PAUSED；不要依据evaluate_videos单独产生的初步门禁跳过completeness审计启动照片。完整性控制只作几何计算，不取消约束重新训练。严格回放应在独立目录，先恢复同SHA的旧geometric_pose输入链接和原021资产；不覆盖当前FINAL。

实际本轮四组CPU进程并行，GPU未用于训练或新HERO，8次Stage1正式同配置结果复用于Stage2。sum_process_seconds不是并行墙钟。大原件/特征/原生HERO留原路径，LOCAL_ARTIFACTS为路径SHA索引，不声称全部上传。
