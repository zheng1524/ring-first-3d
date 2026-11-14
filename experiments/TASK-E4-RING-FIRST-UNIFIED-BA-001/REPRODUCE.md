# 复现

本地目录 `/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001`。沿用Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；使用本目录runtime/packages的PyCeres2.6，Ceres2.2.0。系统python3.8不适用于本轮Python3.12语法。无GPU训练/推理。

既有原始数据、021特征地图和HERO必须位于索引登记路径；源文件SHA见INPUTS_FROZEN与资产索引，不把未上传本地缓存说成仓库内容。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
U=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001
# 已有FINAL时只验证，不重新优化或覆盖。
$PY -B "$U/code/replay.py"
# 只重建独立诊断/图像，候选保持冻结：
$PY -B "$U/code/joint_information.py" G01
$PY -B "$U/code/joint_information.py" G03
$PY -B "$U/code/joint_information.py" G05
$PY -B "$U/code/joint_information.py" G06
$PY -B "$U/code/evaluate.py"
$PY -B "$U/code/cross_held_audit.py"
$PY -B "$U/code/stage_decision.py"
$PY -B "$U/code/additional_audit.py"
$PY -B "$U/code/hero_evaluate.py"
$PY -B "$U/code/source_coverage.py"
$PY -B "$U/code/finalize_tables.py"
$PY -B "$U/code/scope_audit.py"
$PY -B "$U/code/export_layers.py"
$PY -B "$U/code/visualize.py"
$PY -B "$U/code/report.py"
$PY -B "$U/code/verify.py"
# 查看本地GLB/HTML（HTTP，首次需联网获取固定three0.169模块）：
$PY -m http.server 8765 --directory "$U/local_results/interactive"
# 浏览器 http://localhost:8765/G01_VIEWER.html，其余G03/G05/G06同名。
```

从干净的独立实验副本重跑：prepare → visible_arcs → stage_a → joint_ba(G01/G03/G05/G06) → sensitivity → information → evaluate → stage_decision → HERO/GLB/figures。使用同一protocol，不按HOLDOUT改参数。原生崩溃最小复现 binding_repro 的旧backend快照/日志保留；当前solver显式预求Jacobian，不能通过关闭自定义Torus残差“修复”。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；98 canonical视角=81FIT+17HOLDOUT。G01含004/005；其他三组只有004 |
| 本算法独立成功 | B1实际76个独立局部求解，另5个参考相机受保护；B2仅G01一个共享SE(3)求解；B3四个真实联合问题，76个五维局部相机块+一个六维H+1377个XYZ，数值输出不是绝对精度认证 |
| 本算法失败 | 无用旧位姿填充的失败预测；B4四组NOT_RUN，照片12/12 NOT_RUN；初次PyCeres冷调用崩溃保留，显式Jacobian预求值后实际组级运行完成；独立RGB科学可信性尚未建立（不是当前严重数值阈值FAIL） |
| 历史测量值回退 | 0；B0/参考相机/HOLDOUT是预登记对照或规范，不冒充新恢复结果。B2不适用的三组保持NaN/N/A，不复制B0 |
| 失败组及具体原因 | G01初版005地图评价坐标错误已纠正；当前未超过冻结严重退化阈值，但四组独立RGB仍有权衡；B3四组留出极线代理均增大；G01/G06旧深度相容性下降。见FAILURE_LEDGER、逐视角/逐来源CSV和Figure4–8 |
| 最终统计样本 | 全部4组完整保留；按每指标真实视角、轨迹或source-target像素分母统计；不把重复源观测当独立物理样本。真实GT测量MAE/MedARE/尺寸p95为NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；协议/输入/源码在运行前冻结，候选在HERO之前冻结；HOLDOUT不进目标，不按HERO选路线，保留预登记主初值而非较低损失的敏感性候选 |
