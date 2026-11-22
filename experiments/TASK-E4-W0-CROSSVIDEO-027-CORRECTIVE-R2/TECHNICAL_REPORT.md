# TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2 — TECHNICAL_REPORT

```
STATUS: CONTROLLED_BA_PARTIAL
L0 residual-at-GT:      PASS   (RGB 0, I/C/O <=1.2e-13)
L1 correct init:        PASS   (2.7e-6 deg / 6.5e-15 mm, success=True)
L2 H-only (3 deg):      PARTIAL(H 0.022 deg, success=False)
L2 H-only (12 deg):     FAIL   (7.06 deg — Huber saturation / basin)
L3/L4/L5:               NOT_EXECUTED (time budget)
REAL G03 BA:            NOT RUN (not authorised)
READY_FOR_REAL_G03_BA:  NO
```

## 1. 关键突破：受控场景第一次真正一致

027-CORRECTIVE 的受控实验把**合成 RGB** 与**真实 G03 Ring** 混在一起，GT 本身无法同时解释两者，
所以那批"3–10° 失败"无法归因。本轮从**同一 GT 相机**生成 RGB 与 Ring（I/O/C）观测：

| Level 0（GT 代入） | 能量 |
|---|---:|
| RGB | **0.0** |
| Inner / Centerline / Outer | **1.2e-13 / 1.7e-14 / 1.2e-13** |

⇒ 同一场景严格自洽；BA 数学与历史 Ring 几何在 GT 处一致。

## 2. 三角化特征身份修复

`feature_id ≡ landmark_id`（不再从轨迹顺序重推）。6 台 GT 相机 / 12 地标：
三角化误差 **< 1e-6 mm**、66 对距离一致、打乱顺序与缺失观测均不串号（T1–T5，4/4 PASS）。

## 3. 分级结果

| Level | 结果 | 判定 |
|---|---|---|
| L0 | 见上 | PASS |
| L1 GT 相机 + 三角化地标 | 相机 **2.7e-6°**、H **1.2e-6°**、地标 **6.5e-15 mm**、`success=True`、nfev 10 | **PASS** |
| L2a H-only，GT yaw 12° | H **7.06°**、0.53 mm、`success=False` | FAIL |
| L2b H-only，GT yaw 3° | H **0.022°**、0.0025 mm、`success=False`（40 次上限） | 误差 PASS / 状态 NOT_CONVERGED |
| L3 单相机 | — | NOT_EXECUTED |
| L4 多相机（≥4） | — | NOT_EXECUTED |
| L5 噪声/粗差/不同 K | — | NOT_EXECUTED |

## 4. 十个问题

**Q1 三角化是否重复读错特征？** 是（旧代码按轨迹顺序重推），已修；T1–T5 证明不串号，误差 <1e-6 mm。
**Q2 同一 GT 场景能否同时解释 RGB 与 Ring？** **能**（L0 全部 ~1e-13）。
**Q3 Centerline 是否进入 BA？** **是**（独立通道，L0 `C=1.7e-14`，L2 中 C 非零）。BA 目标 = ICO，不是 MICO。
**Q4 是否仍用 GT H 选边缘？** **否**，边缘只从初始相机算；GT 仅用于生成观测与评价。
**Q5 无噪声正确初始化能否恢复地标并保持几何？** **能**（L1：6.5e-15 mm，`success=True`）。
**Q6 只优化 H 能否恢复已知变换？** **在收敛域内能**（3° → 0.022°）；12° 初值失败。
**Q7 L3/L4 是否进一步恢复？** 未执行（时间预算），因此不能回答。
**Q8 S5/S10 是否做了名称对应的实验？** 本轮未执行 L5；027 的命名问题已记录，未再冒充。
**Q9 若失败，哪个级别/原因？** L2a：初始化偏差 12° 使 004 侧 RGB 全部落入 Huber 线性区，梯度被压制 → 收敛域问题，不是模型错误（3° 可恢复）。
**Q10 是否具备真实 G03 BA 条件？** **否**：L2 的 12° 级失败、L3–L5 未做、`success=False`。

## 5. 明确未完成

- L3/L4/L5 与多相机扰动未执行（时间预算）→ `NOT_EXECUTED`；
- 两次 L2 均 `success=False`（`max_nfev`）→ 标 `NOT_CONVERGED`；
- 可见边缘随相机变化的敏感性统计 `NOT_DONE`；
- 解析 Jacobian 对比 `NOT_DONE`。

## 6. 建议（不执行）

1. 加**粗到细的鲁棒尺度**（初始 f_scale 大，逐步收紧）或用 Ring-compatible yaw 搜索给出初值，解决 12° 收敛域问题；
2. 补 L3/L4（≥4 台释放相机）与 L5（噪声/粗差/不同 K）；
3. 全部通过后再申请真实 G03 B0/B1/C。

## 7. 复现

```bash
R=experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$R/core:$R/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY -m unittest discover -s $R/tests -v
PYTHONPATH=$R/core:$R/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R/core/levels.py --levels 0,1
PYTHONPATH=$R/core:$R/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R/core/levels.py --levels 2 --yaw 3
PYTHONPATH=$R/core:$R/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $R/core/figs_r2.py
```
