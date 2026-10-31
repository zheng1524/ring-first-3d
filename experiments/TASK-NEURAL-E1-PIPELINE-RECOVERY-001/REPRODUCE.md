# CPU复现

本地完整目录：`/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001`。HTML绝对路径：`/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/visualizations/index.html`。

只有本机仍有旧数据与原环境时可完整重放；GitHub不含原视频/权重/全量NPZ/GLB和隔离依赖。缺失资产按MISSING/BLOCKED记录，不能从报告造数据。下面只运行本任务CPU脚本，不运行E0模型、CUDA探针或清理入口。

```bash
cd /home/liu/ring_first_3d_neural_e1
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1
TASK_E1_PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK_E1_DIR=experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001
"$TASK_E1_PY" "$TASK_E1_DIR/code/source_audit.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/sdf_contract.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/map_contract.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/figures.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/failure_evidence.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/validate.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/report.py"
```

重放会更新本E1派生指标、图和时间戳；如需保留本次完整原件，先复制新任务目录并重新建立新分支，保持旧工作树只读。原有源码/物理相机、数据和E0结果由保护哈希验证。

只读核验可仅运行`validate.py`；它读取既有产物，重做小型CPU断言并写本任务验证文件。每次源码变化后重建对应BEFORE_TEST冻结；不得改变CPU_CONTRACT容差去换PASS。SDF组件状态是BLOCKED_STATIC_ANALYSIS_ONLY，数学等价几何不能当官方神经执行。

数据转换：原始几何mm，官方条件m；原源相机保持相同。source-index与原UV、三角面ID、重心、未知/遮挡标签保存在`local_results/depth_conditions/*.npz`，仅本地。首次SDF CPU兼容错误见`runtime/SDF_attempt001.log`和`provenance/SDF_ATTEMPT001_FREEZE.json`。
