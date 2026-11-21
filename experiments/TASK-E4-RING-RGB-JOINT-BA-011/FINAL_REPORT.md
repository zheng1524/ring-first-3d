# TASK-E4-RING-RGB-JOINT-BA-011 — FINAL_REPORT

**STATUS: `PARTIAL`（B0 与 J2 均已真实运行；J2 崩溃已定位到版本选择偏差；强制同版本复核未完成）**

## 0. 真实结果（G03/005，16 冻结视角）

| 指标 | B0（冻结原始边界） | J2（Inner+Outer 联合） |
|---|---:|---:|
| Inner MAE (px) | **1.02** | 1.97 |
| Outer MAE (px) | **1.66** | 2.70 |
| Ring 原始边界 MAE (px) | **0.98** | 2.36 |
| RGB Held 中位 (px) | **2.38** | **52.19** |
| RGB Held p95 (px) | **4.39** | 193.50 |
| 正深度比例 | 0.99 | 1.00 |
| **选中的初始化版本** | **0** | **1** |

## 1. 崩溃原因（已定位，非"算法精度不够"）

**两臂选到了不同的 Ring-First 初始化版本**（B0→v0，J2→v1）。

原因在 `version_score()`：它用 `mean(|ring_residual|)` 作为版本评分的一项，而 J2 的 ring 残差是**按弧长归一化后的新块**，尺度与 B0 不同 → 评分不可比 → 选到另一条分支。

这正是本任务书 §7.1/§8.2 事先警告的"不同方法用不同尺度训练损失选版本"问题。

**因此 52.19 px 至少部分是选择偏差，不能据此判定 Inner+Outer 几何无效。**

## 2. 已实现并验证的工程项

| 项 | 状态 |
|---|---|
| 弧长权重 `sqrt(w·Δs/L_ref)`，128/256/512 不变 | ✅ |
| 有符号残差 `(p_DXY−p_CAD)·n_outward` | ✅ |
| `UNOBSERVED` 零贡献 + 状态 | ✅ |
| 抵消冻结 `sqrt(counts/rglen)` 的适配层 | ✅（J2 内 `sqrt(n_r/c)`） |
| 路线登记 / 组件表 / 技术地图 / 异常审计 | ✅ `registry_check` exit 0 |
| 第一份复现包 `ring-cad-inner-outer v1` | ✅ `REPRO: PASS`（3 视角，容差 0.25 px） |
| 强制同版本 J2 复核 | ⏳ 已启动，未取到结果 |

## 3. 未完成

- 强制 v0 的 J2 数值（已启动）；
- 图 A/B/C/D；
- G05/005；
- 共同训练侧评分器（`COMMON_TRAIN_SELECTION_SCORE`）——这是修复版本选择问题的正解，本轮未实现。

## 4. 路线状态

| route | status | 依据 |
|---|---|---|
| `ring-cad-inner-outer` v1 | `candidate` | 复现包 PASS，独立复现 PENDING |
| `cam-ring-rgb-joint` v1 | `exploring` | J2 结果被版本偏差污染，不能升级 |

## 5. 下一步（唯一正确方向）

1. 实现与臂无关的公共训练侧评分器（Ring 原始边界 + Inner + Outer + 材料 + RGB train + 正深度 + 收敛），
2. 两臂都用它选版本；
3. 再比较 B0 vs J2；
4. 若仍退化，才进入几何归因（010 已给出 outer ~1.3 px 系统偏移的证据）。
