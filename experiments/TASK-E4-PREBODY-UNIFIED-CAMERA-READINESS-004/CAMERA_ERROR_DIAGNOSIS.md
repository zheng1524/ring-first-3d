# CAMERA_ERROR_DIAGNOSIS

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

## 1. 分类分布（80 个 FIT 视角）

| 类别 | 数量 |
|---|---:|
| OK | 35 |
| D_BA_CONFLICT | 28 |
| C_INIT_OR_GAUGE | 10 |
| A_RING_OBSERVATION | 6 |
| E_INSUFFICIENT_OBSERVATION | 1 |

**判据（全局，不按视频变化）：**

```
A_RING_OBSERVATION : Ring 门禁未过（>3 px）
E_INSUFFICIENT     : held_N < 8 或 visible_tracks < 40
B_RGB_MATCHING     : held > 10 px 且共视不足（<2 个共视视角）
C_INIT_OR_GAUGE    : 光轴与"指向环心"夹角 > 15°，或环距偏离实例中位 > 20 mm
D_BA_CONFLICT      : held > 10 px、共视充分、位姿不离群
OK                 : 其余
```

**重要修正记录：** 初版曾用"与其余相机旋转中位数之差"判离群，导致 73/80 被误判为 `C`——环视相机本就朝向各异，该判据无意义。已改为物理量（光轴 vs 指向环心夹角、环距偏离度）。

## 2. 三个重点病例

### G02/005（held 中位 28.10 px，8/8 QUARANTINE）
- Ring 中位 2.01 px，门禁基本全过；RGB 一致性极差 → 不是 Mask 问题。
- 003 密度实验：16 视角后 held 降至 8.24 px（−71%），22 视角 9.61 px。
- 判定：**基线不足 + 轨迹稀少**，不是个别错配。

### G03/004（held 中位 27.50 px，Ring 中位 0.88 px）
- Ring 全过门禁但 RGB 不成立——Ring 旋转对称性使 3 px 门限对此类错误失明（与 004 审计一致）。

### G06/005（held 中位 2.47 px，5 CORE）
- 当前最健康实例；但方向覆盖 <60°，故准入仍为 READY_WITH_CAUTION。

## 3. 结论

1. Ring 门禁不是相机质量的充分条件（G02/005、G03/004 为反例）。
2. held 大 ≠ 相机错：需结合共视数、可见轨迹数与位姿离群度区分 B/C/D。
3. 本数据中 `D_BA_CONFLICT` 最多（28/80），说明主要矛盾是**多视角几何冲突**而非单视角 Mask 错误。
