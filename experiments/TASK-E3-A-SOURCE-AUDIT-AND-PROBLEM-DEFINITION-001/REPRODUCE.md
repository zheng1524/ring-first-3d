# E3-A 复现与只读边界

本分支保留小型代码/表格/报告/PNG，不复制全量视频、PLY/NPZ或权重。完整路径与SHA见 `provenance/INPUT_HASHES.json`、benchmark和代码复用表。离开当前机器缺少这些输入必须明确报缺失，不得换用旧预测、生成假资产或下载新推理补齐。

已执行环境：Linux CPU，`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（Python3.12/NumPy1.26），Open3D为既有 `surface_fusion_v3/vendor`，CUDA_VISIBLE_DEVICES空；没有导入模型或checkpoint。`common.py`复用E1审计钩子：封禁GT/Oracle/Dxy、网络、任务目录外写入，并额外封禁神经运行时/checkpoint导入。

源码入口位于 `code/minimal_readonly_audit_tools/`。原执行顺序如下（将`TASK_ROOT`设为本任务绝对路径；不要使用旧模块main）：

```bash
TASK_ROOT=/home/liu/ring_first_3d_e3a/experiments/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001
E3_PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/inventory.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/geometry_audit.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/casebook.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/historical_coverage.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/figures.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/freeze_benchmark.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/report.py"
"$E3_PYTHON" "$TASK_ROOT/code/minimal_readonly_audit_tools/validate_delivery.py"
```

`inventory.preregister`检查原父提交 `fcdcefb...`，且既存历史保护快照必须相同；这是**首次采集重放保护**，在已提交分支上直接重跑inventory会有意停止，不能临时删掉检查制造PASS。正常交付复核只运行最后的 `validate_delivery.py`；完整重建应建立新的独立任务目录/父提交checkout，使用相同固定协议并另存快照，不能覆盖本次冻结证据。RA_READING_RECEIPTS是实际人工阅读收据，不能靠脚本生成来代替阅读；不改变收据冒充新阅读。

本轮实际的失败尝试、最终运行与布局修订见 `provenance/EXECUTION_LOG_INDEX.json`；runtime原日志和中间NPZ留在本地、Git忽略。它们不属于未来方法输出。`local_results/own`为已有原面的射线查询缓存；`face_facts`为原面代理/索引，`historical_F3`为现存输出的查询缓存；没有新增Mesh、LocalField或全局标量模型。

关键复核：36份原面身份/坐标往返、全部输入SHA、17/8两层相机资格、252对同视频检查、288条定位、108点查询、108历史覆盖记录、固定9目标和65视图依赖、4张真实PNG、无GT/模型/优化调用、旧worktree快照不变。所有科学未知项独立列于失败记录，不能把交付完整性检查当算法成功率。

如缺少本地源或哈希不符，停止该项复现并报告缺口。最后的新任务输出SHA清单用于复核当前交付；会变动的验证日志及清单本身不进入自身哈希，以避免循环。
