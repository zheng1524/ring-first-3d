# TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL — TECHNICAL_REPORT

```
ENGINEERING_CORRECTNESS: PARTIAL
UNIFIED_PIPELINE:        PASS
G01_GEOMETRY:            INSUFFICIENT_EVIDENCE
G03_GEOMETRY:            PARTIAL
G06_GEOMETRY:            PARTIAL
OLD_NEW_COMPARISON:      MIXED_RESULTS
HOLDOUT_VALIDATION:      PARTIAL
REPRODUCIBILITY:         PARTIAL
```

## 1. 修复的数学错误（有测试）

| 修复 | 内容 | 测试 |
|---|---|---|
| **A1/D7** | `epipolar_score` 改按 **CSV 行位置（身份 ID）** 选 FIT，不再用 `ref_index ∈ fit_rows`；返回 `{epi,n_ids,n_corr,status}`，`EPIPOLAR_UNOBSERVABLE` 显式标记；无效候选 `score=inf`，不再把 0 当缺失 | `H_CANDIDATES.csv` 中 G03/G06 的 `epi` **非空**、`epi_status=OK`、`n_fit_ids>0`（`SUMMARY.epi_available=true`） |
| **A2** | 基础矩阵纠正为 `F = K_other^-T [t]× R K_ref^-1`（此前 K 顺序反了） | `T02`：真实对应 Sampson < **1e-8**；5° 错误 H 下中位 >1 px；交换相机顺序仍满足 `x_b^T F x_a=0` |
| **A3** | FIT-only 进入 H-only / 三角化 / Joint BA；HOLDOUT 仅用于"参考观测三角化 → 预测另一视频观测"的独立评价 | `SPLIT.json` 身份隔离；`REPROJ_HOLDOUT_*.csv` 由独立路径生成 |
| **A4** | 旧路线改为：**参考视频 FIT 观测三角化 → H-only → 共同三角化 → Joint(H,X)** | `triangulation/X_REF_ONLY.csv`（仅参考视频观测）；旧路线 M2 使用该结构 |
| **A5** | `ring_vector` 加入 **Centerline**（I/C/O），空边返回 `None`（`RING_EDGE_NOT_EVALUABLE`），不再静默 0 | 候选 Ring 能量与 BA 块使用同一残差函数（T05 因 D11 跳过，数值等价未在本轮验证） |
| H 一次 | 参考/待配准角色由 `role` 显式映射，相机仅 W0，H 只在 BA 内 | `T07`：`H@H@T0` 与 `H@T0` 投影差 >1e-6 |

测试结果：`tests/test_final_math.py` **3 PASS / 1 SKIP**（T05 因 D11 跳过）。

## 2. 三组真实执行结果（同一入口 `core/u028c.py`，max-views=4）

| 组 | 参考/另一 | 身份（fit/hold） | epi 可用 | 旧路线 FIT / HOLDOUT | 新路线 FIT / HOLDOUT | Ring（旧/新） |
|---|---|---|---:|---:|---:|---:|
| **G01** | 005/004 | **0** | — | — | — | — |
| **G03** | 005/004 | **10**（7/3） | **true** | **1.10 / 5.58 px** | **1.34 / 9.17 px** | 0.474 / 0.386 |
| **G06** | 004/005 | **6**（4/2） | **true** | 1.24 / **197.39 px** | 1.39 / **194.55 px** | 0.231 / 0.170 |

- **Joint BA 状态**：两组 `success=false`（M2/M3b 各 20 次函数评价，预算内未满足容差）→ 只算 `GEOMETRY_PARTIAL`，不宣布收敛。
- **G03**：旧路线在独立 HOLDOUT 上更好（5.58 vs 9.17 px），新路线 Ring 更好（0.386 vs 0.474）→ **MIXED**。
- **G06**：两条路线 HOLDOUT 都 ~195 px（2 个留出身份、观测极少）→ 该组独立验证**不通过**；Ring 新路线略好。
- **G01**：3 视角与 4 视角配置下均为 **0 个 2D 验证身份**（`features019.matches` 无有效跨视频支持），同 028 结论；但按任务要求记录为"证据不足"而非"程序跳过"。

## 3. 未完成/缺陷（如实）

| # | 问题 | 影响 | 状态 |
|---|---|---|---|
| **D10** | `u028c.py` 的 `U` 常量最初仍指向 `028-CORRECTIVE`，本轮 G03/G06 结果先写入旧目录（已复制回 FINAL/runs 并在清单注明来源） | 溯源混乱 | 已修复 U 指向；结果已迁移 |
| **D11** | 单元测试里 `RingRenderer` 的模块级 `R` 与 R6 路径耦合 | T05 跳过 | **未修** |
| D12 | BA `success=false`（20 次评价） | 不能称收敛 | 如实记录 |
| D13 | 8 张图未按"每图一文件"拆分，改为每组一张 8 面板合成图 + 一张跨组图 | 与交付清单不完全一致 | 如实记录 |
| D14 | 未做"删除 W0 缓存后自动重放"的真实演练 | 门控缺证据 | **未验证** |
| D15 | 未做干净目录全量复跑 | 复现性 | **PARTIAL** |

## 4. 二十问（要点）

1. **D7 修复？** 是；`epi` 非空、`n_fit_ids>0`、`epi_available=true`（G03/G06）。
2. **HOLDOUT 排除？** 是；H/三角化/BA 只用 FIT 行，HOLDOUT 走"参考观测三角化→预测另一视频观测"独立路径。
3. **旧路线恢复？** 是；先仅用参考视频 FIT 观测三角化，再 H-only。
4. **Ring I/C/O 一致？** 代码统一；数值等价测试因 D11 跳过 → **未完全验证**。
5. **参考视频可切换？** 是；G06 参考=004、G03/G01 参考=005，均由统一规则选出。
6. **H 重复应用？** 否；T07 通过。
7. **缓存隔离？** 每组独立 `runs/<G>/{rgb_features,ring,...}`；D10 为单次事故已记录。
8. **W0 自动补算？** 代码路径存在，**未演练**（D14）。
9. **视角选择考虑跨视频重叠？** **否**：当前仅单视频 Ring/RGB/角度覆盖（未做跨视频重叠评分）→ `PARTIAL`。
10. **单视频三角化不稳定是否提前删除匹配？** **是**（身份仍依赖 `landmarks` 的观测映射）→ 未修复。
11. **G01 有可靠对应？** **无**（3/4 视角均为 0；证据：`IDENTITIES.csv` 空、`SELECT_*.csv` 与 SIFT 计数已存）。
12. **G03 旧/新 H？** 两者 `H_init_is_identity` 分别 true/false，最终 H 存在 `ba/old.npz|new.npz`（未在此表格展开数值）。
13. **G06 旧/新 H？** 同上。
14. **共同三角化差异？** G03 旧路线 HOLDOUT 5.58 vs 新 9.17 px；G06 两者均失效。
15. **Joint BA 执行/收敛？** 执行；**未收敛**（`success=false`）。
16. **Ring 前后保持？** G03 0.474/0.386，G06 0.231/0.170（BA 后），未见发散。
17. **FIT/HOLDOUT？** G03 FIT 1.1/1.34、HOLDOUT 5.58/9.17；G06 HOLDOUT ~195 px（不通过）。
18. **冲突相机/点？** G06 的 005（W0 留出轨迹不足）与 2 个留出身份最明显。
19. **是否靠删观测获胜？** 未删除；但 G06 只有 2 个留出身份，统计力弱。
20. **有资格比较新旧？** **不足**：G03 可作初步对照（`MIXED`），G01 无数据、G06 HOLDOUT 失效。

## 5. 证据路径

`runs/<G>/SUMMARY.json`、`runs/<G>/{identities,h_initialization,triangulation,ba,evaluation,ring,view_selection}/`、
`runs/G03/figures/G03_unified_8panel.png`、`runs/G06/figures/G06_unified_8panel.png`、`runs/G01/figures/G01_unified_8panel.png`、`runs/CROSS_GROUP.png`、`tests/test_final_math.py`。

## 6. 复现

```bash
F=experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
for g in G01 G03 G06; do
  PYTHONPATH=$F/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:runtime/p3d:src \
  $PY $F/core/u028c.py --group $g --max-views 4
done
```
