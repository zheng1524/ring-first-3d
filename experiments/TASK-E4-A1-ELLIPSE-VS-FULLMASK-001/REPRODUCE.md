# 复现

分支exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001；Ring源码父提交1d5e36a，预注册10f70a1，数值修正冻结64bc0b0。原始数据保持原绝对路径和SHA，不复制视频/权重。

```bash
cd /home/liu/ring_first_3d_e4_e1e2
TASK_ROOT=experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
DXY_PY=/home/liu/new-polyp-dxy/.venv/bin/python
"$DXY_PY" -B "$TASK_ROOT/code/generate_dxy.py"
"$PY" -B "$TASK_ROOT/code/replay_inputs.py"
"$PY" -B "$TASK_ROOT/code/synthetic.py"
"$PY" -B "$TASK_ROOT/code/run.py"
"$PY" -B "$TASK_ROOT/code/analyze.py"
"$PY" -B "$TASK_ROOT/code/visualize.py"
"$PY" -B "$TASK_ROOT/code/validate.py"
"$PY" -B "$TASK_ROOT/code/write_report.py"
"$PY" -B "$TASK_ROOT/code/finalize.py"
```

输入缓存缺失的全新复现工作树先执行replay_inputs.py --rebuild，它复用冻结prepare科学语句，只将首次注册断言/写协议改为严格内容比较；现有结果目录只校验，不能覆盖历史结果。DXY和run.py逐源/求解恢复并跳过已有项。要独立重算DXY而非复用已生成像素几何，应在独立复现目录保留原JSON副本后从空DXY_GENERATED开始；用同一源SHA和content-seeded ID，不使用冻结毫米结果表。不要在现有人工结果目录删除文件强制重跑。

本地PLY、B首层/Mask NPZ、六视角、GLB和HTML在local_results，上传小型参数JSON、指标和4核心图即可。GLB各图层统一转为米，PLY和分析保持毫米。原始首轮在local_results/pre_ring_pool_fix和metrics/PRE_RING_POOL_FIX_*完整保留，不纳入正式比较。输入路径和哈希在provenance，环境在ENVIRONMENT.json。

generate_dxy用官方Python3.10（numpy1.26.4/scipy1.15.3/cv2 4.10.0/skimage .25.2），几何实验用原Ring Python3.12。两者只通过像素几何JSON交换，无网络/权重/GT。脚本只写新任务目录。正式源数据/科学代码由v0.2冻结校验，后续报告脚本单独索引。
