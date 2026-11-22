# LEAKAGE_AUDIT

证据：`results/T6_provenance_leakage.json`、`core/run_corrective.py` 的 split 代码。

## 现行划分

```python
vbs = sorted({m['b'] for m in ms})        # 只对 video-b（005）的 view 排序
fit = set(vbs[::2]); ho = set(vbs) - fit  # 005 偶数=fit，奇数=holdout
pairs_fit = [... if m['b'] in fit]        # 004 相机完全按配对进入
```

## 结论

| 项 | 实测 |
|---|---|
| 005 侧 | 8 FIT / 8 HOLDOUT 视角，**隔离成立** |
| **004 侧** | **从未留出**：6 个 004 视角全部同时出现在 FIT 与 HOLDOUT 配对里 |
| `views_004_used_in_both` | `G03_key02_raw00327, G03_v004_raw00202/00242/00263/00283/00304`（6/6） |
| 泄漏机制 | 004 的相机 `C4` 直接进入 H 的估计（`H @ C4` 与 005 观测做对极），同一 `C4` 又用于 HOLDOUT 残差；004 的特征身份被两侧共享 |

因此 `HOLDOUT 4.538 px` **只能说明"未见过的 005 视角"上的泛化**，**不能**说明 004 侧泛化。
021 报告把它写成"留出验证通过"是**过度表述**。

## 023 需要的划分（可实施）

1. **双侧视角留出**：004 按 raw_frame 排序取偶数训练/奇数留出；005 同样，形成 4 个象限（FIT-004/FIT-005 估计，其余三种组合评价）。
2. **地标级留出**：同一 3D 身份的所有观测必须整体进同一侧（现在没有 3D 身份，等 F7 完成后再执行）。
3. **时间簇留出**：按 raw_frame 聚类（相邻 <10 帧为一簇），整簇进同一侧，避免同簇近邻帧泄漏。
4. 划分在建匹配/估计 yaw **之前**冻结，写入 `config/FIT_HOLDOUT_SPLIT.json` 并计算 SHA。
