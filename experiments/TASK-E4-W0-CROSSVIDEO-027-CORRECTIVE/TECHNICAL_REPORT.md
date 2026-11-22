# TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE — TECHNICAL_REPORT

```
Gate 1 变量管理:      PASS（7/7 测试；frozen=9, released=2, anchor=1, dim=54）
Gate 2 Ring 几何:     PARTIAL（D2/D3/D4 修复并数值验证；M 未进入 BA 数值残差，已记录）
Gate 3 受控真值:      FAIL（三角化初值下全部 success=False，3.0–10.6°）
Gate 4 真实 B0/B1/C:  BLOCKED（按门控规则不执行）
Gate 5 评价与复现:    PARTIAL（入口/哈希/审计通过；B/C 与 HOLDOUT 无模型）
BA_ACCEPTED / CROSS_VIDEO_GEOMETRY_ACCEPT: NO / NO
```

## 1. 修复的四个执行错误

| 缺陷 | 证据 | 状态 |
|---|---|---|
| **D1 锚点从未生效** | 旧代码 `anchor=('005',0)` 元组 vs 字符串 ID → 测试断言旧实现 `len(order)=11`（什么都没冻结） | 已修，`CameraVariables` + 索引审计 |
| **D2 Ring 评价矩阵方向** | 旧 `inv(T0)@C` 与真实相机差 >1e-3；新 `C@inv(T0)` 与 `canonical(C)` 差 **1e-12** | 已修，单一入口 `ring_adapter` |
| **D3/D4 Ring 目标与权重** | 旧 BA 只算 I/O 且 `λ` 平方成 100；新 `sqrt(2λρ/N)` 使 `0.5Σr²` **精确**等于历史加权均值，λ 1→4 严格 4× | 已修 |
| **D5 受控真值泄漏** | 旧初值 = GT+0.5 mm；新初值 = 历史 019 三角化（与 GT 差 0.81–6.47 mm） | 已修，GT 独立文件 |
| **D6 未收敛仍报告** | 旧 `success=false, nfev=20`；新记录 status/nfev/cost 并阻断 | 已记录 |

## 2. 关键数值

- 027 的 `Ring004 53.162 / 54.156`：**INVALIDATED**（D2）。
- W0 基线（有效）：RGB 中位 **0.446 px**、p90 0.910；Ring MIO **0.160**。
- 受控（三角化初值）：相机 **3.0–10.6°**、H 3.0–10.6°、地标 0.8–6.5 mm，**全部 `success=False`**；
  400 次迭代仍 3.04°；**λ_R=0（无 Ring）9.30°** → 失败不是 Ring 造成的。
- S9（单侧观测）在控制场景中**不可三角化** → `NOT_EVALUABLE`。

## 3. 十二问

1. **是否错误释放 005？** **是**（D1），旧报告"005 固定"为假；现在 8 台 005 全部 frozen、无参数索引。
2. **004 锚点是否有效？H 是否重复自由度？** 有效（`G03_v004_raw00202` frozen，H 承担视频级放置）；重复自由度已通过"只留 2 台 004 可动 + 1 台锚点"消除。
3. **修复后 B/C 的真实 Ring 误差？** **无**——B/C 未重跑（Gate 3 FAIL）；027 的 53/54 已作废。
4. **BA 内部 Ring 目标与历史是否一致？** I/C/O 的**能量等价精确到 1e-12**；**M 未进入 BA 数值残差**，故不宣称完整 MICO 等价。
5. **权重是否数学正确？** 是：λ 为能量权重，λ 1→4 得 4.000×，不是 16×。
6. **去掉 GT 初值后还能多准？** 三角化初值下 **3.0–10.6°**，全部未收敛；与 027 的 0.03° 形成对照，说明 027 的精度来自泄漏。
7. **S5/S7 失败来自哪里？** 首要不是粗差或不可辨识：**S1 无噪声也失败**，且 **λ_R=0 仍失败** → 是 RGB 目标 + 参数化在该配置下的可观测性/收敛问题（8 个自由三维点仅 3 台相机）。
8. **B0/B1/C 是否真正按不同变量集优化？** **未执行**；变量管理机制本身已通过测试。
9. **B/C 是否收敛？** 不适用；027 的 B/C `success=false`，本轮受控也 `success=false`。
10. **Ring 与 RGB 是否存在不可同时满足的冲突？** 现有证据**不足以**下此结论：027 的 53/54 是 D2 的产物，本轮未产生可信的真实 BA 结果。**待重跑**。
11. **HOLDOUT 是否证明泛化？** **否**，`NOT_EVALUABLE`。
12. **是否单一、可复现、无重复主线？** 是：单一入口 + 适配层；历史源码未改；旧结果未覆盖。

## 4. 下一轮建议（不擅自执行）

1. 先修**可观测性**：受控场景至少 4–6 台相机、跨视角轨迹，或固定部分地标；当前 3 相机/8 自由点太弱；
2. 用 **H 作为唯一视频级变量**、004 相机全部冻结做 B0，检验 H 单独是否可收敛（这是最简单的可辨识配置）；
3. 若继续 BA：给地标加强先验或用边缘化，避免 24 个自由参数吸收 H 的误差；
4. 真实 G03 只有在受控 ≥4 相机场景恢复到 ≤0.1°/0.2 mm 后才允许执行。

## 5. 复现

```bash
C=experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$C/core:$C/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY -m unittest discover -s $C/tests -v
PYTHONPATH=$C/core:$C/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $C/core/controlled2.py
PYTHONPATH=$C/core:$C/replay:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $C/core/p8_audit.py
```
