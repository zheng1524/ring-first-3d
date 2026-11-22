# CROSS_VIDEO_GEOMETRY_EVALUATION

## 是否执行了正式共享 SE(3) 优化

**没有。** 一致性模块给出的候选 H 与 Ring 几何冲突（Ring MAE 1.04 → 7.70 px），
按 P6 状态机不得用这些身份强行优化。`OPTIMIZATION/` 目录为空并写入 `BLOCKED.json`。

## 现有可用指标（全量候选，不做筛选）

| 指标 | 值 |
|---|---|
| 候选身份 | 15 |
| 三维残差 中位 / p90 | **6.37 mm** / 24.6 mm（全量）；内点 4 个 ≤1 mm |
| 正向重投影（004→005，FIT 观测） 中位 | **23.90 px** |
| 反向重投影（005→004，FIT 观测） 中位 | **6.09 px** |
| HOLDOUT 独立 2D 评价 | **NOT_EVALUABLE（n=0）** |
| Ring MAE（W0 / RANSAC H） | 1.043 / 7.704 px |

## 判定

```
LANDMARKS_VALIDATED:   PASS（317/806）
IDENTITIES_VALIDATED:  FAIL（15 候选中仅 4 个三维一致，且全部 Ring 冲突）
CONSISTENCY_VALIDATED: FAIL（GEOMETRY_CONFLICT）
OPTIMIZATION:          BLOCKED
CROSS_VIDEO_GEOMETRY_ACCEPT: NO
BODY_CROSS_VIDEO_ADMISSION:  NO
```

## 失败原因（区分）

1. **身份不足**：FIT-only 后 15 个候选，其中 11 个三维残差 >1 mm（描述子匹配不到位）。
2. **Ring 冲突**：4 个内点给出的刚体变换与公制 Ring 不一致 → 这些身份不可能同时正确。
3. **HOLDOUT 无证据**：FIT 地标在 HOLDOUT 视角没有可信描述子对应 → 独立验证缺失。
4. 不是"优化器不收敛"：本轮未优化。
