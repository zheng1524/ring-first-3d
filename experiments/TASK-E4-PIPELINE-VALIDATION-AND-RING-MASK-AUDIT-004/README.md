# TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004

**STATUS: `AWAITING_RA_REVIEW`** — 只读审计，未修改任何正式流程、预测或 DXY。

## 一页摘要（中文）

本轮把上一轮 9 条历史证据全部用冻结产物重新复算，并新增四项独立审计。**复算实现对表成功**：用 V6 自己的冻结相机与轨迹重放 held-out 验证，得到 `15/22` 与 `0/22`，与 V6 记录的 `VALIDATED` 计数逐项一致，因此后续对 002 的复算可信。

**三个最重要的发现：**

1. **最终送入 HERO 的相机不是 BA 解，而且更差。** held-out 留一视角复算：G03/005 BA v1 = **5.50 px**、v0 = 77.7 px、实际 `CAMERA_RESULT` = **159.2 px**；G05/005 为 11.6 / 39.5 / 34.8；G02/005 为 11.9 / 12.3 / 21.1。只有 G06/005 保持 ~3 px。流程中没有任何环节检查这件事。
2. **G03/005 的分支错误可以用与相机无关的 `EXACT013 INITIAL` Body 判定**：IoU 在 v0 = **0.304**、v1 = **0.842**、final = **0.229**。与上一轮用 FINAL Body 的 0.308/0.840 一致，排除循环论证。
3. **最大连通域观测不是普适修复。** 78 个有相机视角中仅 4 个多分量；M1 在 2 个改善（G05/005 9.451→0.748），在 2 个变差（G02/004 1.915→1.936；G02/005 1.589→1.766）。被弃分量最大仅占 0.63%。

**三个不成立的简单化：** ①"Ring MAE 大就是孤立分量" → 只在 G05 成立，Ring MAE 中位仅 0.663 px；②"Body 不更新就是失败" → 4/10 停滞，但其余 6 个有 0.088–0.633 mm 真实更新；③"HERO 深度异常是模型坏了" → 仅 2/40 比值 >3×，成因未证。

## 交付物

| 文件 | 内容 |
|---|---|
| [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) | 总报告 + Q1–Q3 回答 + 未确定项 |
| [RING_MASK_METHOD_COMPARISON.md](RING_MASK_METHOD_COMPARISON.md) | DXY 四类处理逐项、M0–M3 全量对照、反例、迁移建议 |
| [GATE_NECESSITY_AUDIT.md](GATE_NECESSITY_AUDIT.md) | 每项门控的来源/证据/误拒/终止必要性 + 敏感性 |
| [CAMERA_VALIDATION_REPLAY.md](CAMERA_VALIDATION_REPLAY.md) | 两类相机区分、对表验证、逐实例复算、门限审计 |
| [PIPELINE_REPAIR_PROPOSAL.md](PIPELINE_REPAIR_PROPOSAL.md) | R1–R8 候选与三处优先修改（含回退） |
| `RING_COMPONENT_COMPARISON.csv` | 78 视角 × M0/M1/M2/M3 + 全边界分解 |
| `CAMERA_VALIDATION_REPLAY.csv` | 3 种相机集合 × 4 实例的 held 复算 |
| `CAMERA_BRANCH_DIAGNOSTICS.csv` | v0/v1/final 旋转与中心差、Ring MAE、BA 状态 |
| `CAMERA_BODY_GAUGE_DIAGNOSTICS.csv` | INITIAL Body 在 3 种相机下的 IoU |
| `GATE_SENSITIVITY.csv` | 78 视角 × 3/5/10 px 通过状态 + 内点数 |
| `VIEW_COVERAGE_MATRIX.csv` | 10 实例 FIT/HOLDOUT/HERO/Body 覆盖 |
| `HERO_HEALTH.csv` | 40 视角深度统计与尺度比值 |
| `BODY_UPDATE_HEALTH.csv` | 10 arm 位移/步数/指标 |
| `metrics/INPUT_SHA256.json` | 12 个输入文件的身份哈希 |
| `visualization/figures/*.png` | 6 张静态图（无 HTML） |
| `visualization/README.md` | 每张图展示什么、怎么读 |
| `code/*.py` | 全部复算脚本（只读输入，可重跑） |

## 复现

```bash
cd /home/liu/ring_first_3d_workspace/experiments/TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004/code
export PYTHONPATH=/home/liu/ring_first_3d_workspace/src:.
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY run_camera_validation.py     # CAMERA_VALIDATION_REPLAY.csv, CAMERA_BRANCH_DIAGNOSTICS.csv
$PY run_ring_mask.py             # RING_COMPONENT_COMPARISON.csv
$PY run_gates_health.py          # GATE_SENSITIVITY / VIEW_COVERAGE / BODY_GAUGE / HERO / BODY health
$PY make_figures.py              # visualization/figures/*.png
```

## 边界

- 未修改 002 的 `code/`、预测、`ADMISSION`；未重跑 SfM/BA/HERO/Body。
- DXY **未被 import 或运行**；小孔规则按 `ring_holes.py` 的 `RULE` 文本独立重实现（含断言）。
- 未修改任何正式门限；未用 GT/HOLDOUT 做选择。
- 未删除或覆盖任何原始数据、ZIP、Mask、相机、HERO、Body 资产。

## 待 RA 裁决

1. R2 是"只告警"还是"可阻断下游"？若阻断需同时批准实例级覆盖阈值。
2. R1 的 held 下限如何处理（G06/005 全实例仅 18 条 held）？
3. R3 是否允许在新任务版本中启用 M1 并重算相机？
