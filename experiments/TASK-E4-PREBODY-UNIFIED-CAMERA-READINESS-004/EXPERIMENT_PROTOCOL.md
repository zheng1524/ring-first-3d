# EXPERIMENT_PROTOCOL

## 1. 本轮实际执行的实验

| 编号 | 实验 | 状态 |
|---|---|---|
| E0 | 统一程序在十段视频上产出同结构诊断与准入 | **已执行** |
| E1 | 异常视角 A–E 分类 | **已执行** |
| E2 | CORE/SUPPORT/QUARANTINE + Body 准入 | **已执行** |
| E3 | 密度 8/16/22 全量 | **未执行**（前端阻塞 + 003 已证只有 2 段可跑） |
| E4 | R0–R3 稳健 BA（降权/剔除/增量） | **未执行**（需要重跑 BA；本轮预算不足） |
| E5 | 时间正则 BA | **未执行** |
| E6 | POSTHOC_BODY_CAMERA_DIAGNOSTIC | **未执行**（Body 资产未在本轮载入） |

## 2. 未执行项的诚实标注

E3–E6 均标记 `NOT_EXECUTED`，不得在任何图表或结论中暗示已获得对应证据。
E4/E5 的判据已在 `UNIFIED_PIPELINE_SPEC.md` 预先声明，下一轮应按同一判据执行，
不得在看到 held 之后再调整阈值。

## 3. 若执行 E4，预先声明的判据

| 结论 | 条件 |
|---|---|
| 采纳剔除 | 剔除后其余相机 held 中位下降 ≥20%，且 CORE 数不减少 |
| 采纳降权 | 同上，且不删除任何视角 |
| 放弃 | 其余相机 held 上升或 CORE 减少 |

## 4. 可复现

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=<ws>/src:. $PY code/unified_prebody.py --all
PYTHONPATH=<ws>/src:. $PY code/make_figures.py
$PY -m unittest discover -s tests -v
```
