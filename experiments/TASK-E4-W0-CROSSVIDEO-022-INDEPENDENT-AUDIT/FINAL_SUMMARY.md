# FINAL_SUMMARY — 022 独立审计

## 1. 一句话总结

021 可信到："六个自由度、标准 Sampson、累计边界、数据 fail-closed 是真的；但梯度验证、断点恢复、Ring 对称性、A2/A6 受控实验、双侧留出都不是真的"，因此它是 **Ring+EPI+Prior 的诊断程序**，不是 020 R3，跨视频几何**不予接受**。

## 2. 已验证的成果（独立复算支撑）

1. `core/se3.py` 的 6-DoF 指数映射：雅可比秩 6、纯平移不改 R、纯旋转 t=0、与 scipy/pytorch3d 数值一致。
2. 标准 Sampson：`sqrt((Fx1)1²+(Fx1)2²+(Fᵀx2)1²+(Fᵀx2)2²)`，与点到极线距离一致。
3. 累计边界：`H·H_seed⁻¹`，实测 0.163 mm / 3.546°。
4. 数据入口 fail-closed：缺 admission 抛错，UNKNOWN 不进入 FIT。
5. G03 真实数值（按现行定义）：FIT 9.669→4.637 px，HOLDOUT 7.476→4.538 px；内点约 28%；p95 156 px。

## 3. 阻断列表（按严重性）

| ID | 问题 | 证据 |
|---|---|---|
| P0-A | `torch_objective` ≠ 正式 objective（无 Ring、EPI 权重 1.0 vs 0.02）；"梯度已验证"不成立 | `results/T1_objective_mismatch.json` |
| P0-B | A2 数据中没有 `H_true`（L(identity)=0）；A3 无断言；A6 同时转相机与观测 | `results/T5_controlled_validity.json` |
| P0-C | 优化器无 checkpoint；`resume` 测试是同一调用跑两次；回滚断言条件性 | `results/T3_optimizer_state.json` |
| P0-D | 未调用 019/020；无多视角 3D 地标；`L_F` 缺失 | `ACTUAL_CALL_GRAPH.md` |
| P0-E | Ring 用 `torus_contours` 顶替 `RingRenderer`，未做等价性对照 | `shared_se3.py:55` |
| P0-F | 硬编码 K（`:13/:93`）、`source_sha` 是路径、`n_raw` 逻辑与 | `results/T4_input_provenance.json` |
| P0-G | G03 与 G01/G05 `code_sha` 不同；`config_sha` 为 null（配置晚于运行 2.5 h） | `BASELINE_LOCK.md` |
| P1-H | 004 侧 6/6 泄漏；HOLDOUT 只隔离 005 | `LEAKAGE_AUDIT.md` |
| P1-I | 离线复现仍依赖 `/home/liu/...` 的 W0 相机 | `core/reproduce_offline.py` |
| P1-J | `INIT=AMBIGUOUS_MULTIMODAL` 却输出 `OPTIMIZE=PASS` 的呈现方式易误读 | `runs/G03/RESULTS.json` |

## 4. 原代码复用清单（023 必接）

必须重新接入：`019/features019.py`（SIFT/轨迹/三角化）、`020/features020.py`（跨视频身份）、
`020/ring020.py`（M/I/C/O 与可见弧）、`020/objective020.py`（双向 `L_F`）、`020/optimize020.py`（Adam+deepcopy 回滚）。
可不动：W0 入口、DXY、Ring CAD、HERO、Body。
可选：`020/gate020.py`、`feature_gate020.py`（梯度/纯 yaw 检查）。

## 5. 现有真实结果的正确解释

- G03：`9.669/7.476 → 4.637/4.538 px` 是**同一目标下**的改善，但该目标是 Ring+EPI+Prior，**不是**完整配准；
  `HOLDOUT` 仅 005 侧独立；p95 156 px、内点 28% → **不能**用于三维融合。
- G01：`HELD_P95` 尾部失败（14+15 视角），`held_n` 37–43 并不缺观测。
- G05：`INSUFFICIENT_TRACKS`（13+16，held_n 13–16 < 20）→ 证据不足，**不等于**相机错误。
- `BODY_CROSS_VIDEO_ADMISSION = NO`。

## 6. 下一轮最小修复（023）

见 `MINIMAL_FIX_PLAN.md`：F1 目标一致化 → F2/F3 checkpoint 与回滚可观测 → F4/F5 K/SHA/统计 → F6 双侧留出 →
F7 多视角地标与 `L_F` → F8 Ring M/I/C/O → F9 受控 GT → F10 配置哈希前置。
停止条件：任一 P0 失败即停，不调阈值、不换算法。

## 7. 审计产物索引

| 项 | 位置 |
|---|---|
| 审计分支/commit | `audit/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT` @ 本提交 |
| 源码收集 | `provenance/pinned_sources/`（29/29 pinned 校验通过） |
| 测试脚本 | `audit_tests/t1..t6` |
| 数值结果 | `results/T1..T6_*.json`、`results/W0_admission_*.csv`、`results/POSITIVE_DEPTH_AUDIT.csv` |
| 输入/输出 SHA | `provenance/MANIFEST.json` |
| 运行命令 | `provenance/COMMANDS.md` |
| 证据副本 | `evidence/`（021 的 RESULTS/SE3_HISTORY/RUN_STATE/SPLIT） |
| 未获得数据 | 020 legacy 逐视角缓存（目录已删）、G01/G05 跨视频实验（无 ACCEPT） |
| 复现 | `python audit_tests/t1..t6`（只读，PYTHONPATH 指向 021 core） |
