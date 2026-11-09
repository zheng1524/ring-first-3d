# REPRODUCE

在当前仓库实验分支运行；不写历史实验、不写DXY。环境沿用现有安装，不重新下载框架。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
R=experiments/TASK-E4-MULTIVIEW-INIT-STALK-015
$PY -B "$R/code/prepare.py"
$PY -B "$R/code/preflight.py"
$PY -B "$R/code/geometry_preflight.py"
$PY -B "$R/code/phase_a.py"
$PY -B "$R/code/select_phase_a.py"
$PY -B "$R/code/phase_b.py"
$PY -B "$R/code/postprocess_all.py"
```

以上是严格顺序，不可并行GPU。已完成的FINAL会跳过；未完成的训练从最新实际attempt的pt恢复优化器、参数、随机状态和拒绝计数。已存在ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT后，训练脚本主动拒绝更新。重新跑训练必须使用另一个派生运行目录，不能破坏本轮冻结证据。

长时作业使用start_new_session脱离终端，PID及状态在runtime/SERVICE_PID.json、CONTINUATION_PID.json、STATUS.json；观察phase_a.log、continue_serial.log及postprocess_all.py日志。上游根inputs和depth_observations是只读链接；不复制大型原始视频/权重。

Phase A/B相同继承目标、密集物理保护、80候选/40接受/连续30拒绝终止；最后接受状态是FINAL。完整.pt保留本地，不仅是权重；对应NPZ、PLY、参数、几何检查、源哈希见metrics/RESULT_INDEX.json和provenance。GT评价必须最后运行。每个预测刚性对齐只改变评价副本，未对齐源Mesh不改动，尺度始终固定1。

## 已完成运行的只读检查与产物复核

不要对当前已冻结目录重新执行优化；上面的完整顺序用于具有相同输入索引的新隔离副本。现有结果检查：

```bash
$PY -B "$R/code/final_delivery_audit.py"
```

报告生成器 `summarize_results.py`、`b0_evidence.py` 之后需依次运行 `finalize_review.py` 与 `final_delivery_audit.py`，保留本轮综合判断。`stalk_gt_review.py` 仅使用已经保存的刚性变换生成五例 Ip 对比，不再配准或选模。后处理重入保留最初的 `GT_FIRST_ACCESS.json`，不重写首次读取时间。

依赖与来源遵循已有环境及 provenance；原始 RGB/HERO/Blender、完整 .pt 和评价中间副本不随 Git 上传。Git 内 `review_meshes` 是精确的 V/F 几何副本，足以审阅全部路线，不能替代完整优化器恢复状态。
