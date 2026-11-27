# 复现与查阅

所有命令均使用实际共享环境；外部V5/V6不写入。科学执行身份 `dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e`，后处理工具身份由本交付Git提交确定。原输入/输出与模型SHA见SOURCE_MANIFEST、VIEW_MANIFEST、RUN_IDENTITIES及ACTUAL_KERNELS。

## 已完成小试的运行/断点恢复

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
OUT=/home/liu/ring_first_3d_workspace/runs/v6_frontend_photo_pilot_001
SNAP="$OUT/snapshots/dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e"
# R1；R2用相同命令，只将配置名改为R2.json。已DONE会跳过，不删除状态重跑。
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SNAP/src" V6_EXECUTION_COMMIT=dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 "$PY" -m ring_first_3d.v6_raw.full_run run --config "$OUT/config/R1.json"
```

实际runtime配置在OUT/config，指向冻结快照；仓库config是可审阅的预检模板。工程尝试与中断相机不属于正式结果，分别保存在engineering_attempts及R*/interrupted，位置映射见ARCHIVE_RELOCATION。两轮runner日志均有QUEUE_EXIT COMPLETE；测试日志内人为故障测试的COMPLETE_WITH_FAILURES不代表科研队列失败。

## 检查与后处理

```bash
cd /home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-FRONTEND-PILOT-001
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PY" -m unittest discover -s tests -p 'test_v6*.py'
"$PY" tools/v6_frontend_pilot_evidence.py
"$PY" tools/v6_frontend_pilot_audit.py
# 以下是已执行的后处理入口，复现时每轮分别调用；不更改科学计划/准入。
"$PY" tools/v6_frontend_pilot_report.py clean --variant R1
"$PY" tools/v6_frontend_pilot_report.py clean --variant R2
"$PY" tools/v6_frontend_pilot_report.py metrics --variant R0
"$PY" tools/v6_frontend_pilot_report.py metrics --variant R1
"$PY" tools/v6_frontend_pilot_report.py metrics --variant R2
"$PY" tools/v6_frontend_pilot_report.py views
"$PY" tools/v6_frontend_pilot_report.py graphs
"$PY" tools/v6_frontend_pilot_report.py photos
"$PY" tools/v6_frontend_pilot_report.py single
"$PY" tools/v6_frontend_pilot_report.py summary
"$PY" tools/v6_frontend_diagnose_zero.py
```

指标缓存受后处理源码SHA保护；输入不变也不能把旧实现缓存冒作新实现。最终index另加入人工交接结论与技术报告链接，重新summary会覆盖这些文字，但不改变图表或数据。

## 本地可视化

当前地址：<http://127.0.0.1:8960/index.html>。服务根为OUT，index跳转report/index.html；report是本任务报告目录的符号链接，R0指向冻结旧结果，不复制大资产。浏览器在本机访问；远程机器访问需要SSH端口转发，不开放公网服务。

若服务已停止：

```bash
python3 -m http.server 8960 --bind 127.0.0.1 --directory /home/liu/ring_first_3d_workspace/runs/v6_frontend_photo_pilot_001
```

全量另见FULL_RUN_PLAN。R2当前存在严重覆盖退化，不能只解除approval_required就发布全量；本轮没有执行全量命令。
