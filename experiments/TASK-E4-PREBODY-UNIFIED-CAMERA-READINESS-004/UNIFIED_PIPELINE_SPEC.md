# UNIFIED_PIPELINE_SPEC

**唯一入口：** `code/unified_prebody.py`
**唯一配置：** `configs/unified_config.json`
**调用：** `python unified_prebody.py --group G01 --video 004`（或 `--all`）

## 1. 规定流程与实际执行状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| 1 | RAW VIDEO → 解码 → 候选帧 → INIT 分割 → 质量 → FIT/HOLDOUT | **BLOCKED_RESTRICTED_WEIGHTS**（见 RAW_VIDEO_PROVENANCE.md） |
| 2 | Ring Mask 与 DXY 几何诊断 | 执行（DXY 只读） |
| 3 | Ring-First 候选 / SIFT / 初始化 / BA / 版本选择 / held 评价 | 复用 005 冻结产物（不重解） |
| 4 | 逐视角异常分类 A–E | 执行 |
| 5 | 相机网络指标（共视、方向覆盖、离群度） | 执行 |
| 6 | CORE / SUPPORT / QUARANTINE + Body 准入 | 执行 |

## 2. 统一性证明

- 代码中不存在 `if group ==` / `if video ==` 分支（`tests/test_unified.py` 断言）。
- 组/视频只用于**选择输入路径**；Ring 尺寸、内参、门限、分类规则全部来自同一配置。
- 同一程序在十段视频上产出同结构输出。

## 3. 关键规则（全部全局）

```
A_RING_OBSERVATION  : Ring 门禁未过
E_INSUFFICIENT      : held_N < 8 或 visible_tracks < 40
B_RGB_MATCHING      : held > 10 px 且共视不足
C_INIT_OR_GAUGE     : 旋转离群 > 25° 或中心离群 > 12 mm
D_BA_CONFLICT       : held > 10 px 且共视充分且位姿不离群

CORE       : 门禁过 + held<=3 + held_p95<=6 + held_N>=8
SUPPORT    : 门禁过 + held<=10（非 CORE）
QUARANTINE : 其余

READY_FOR_BODY_INIT   : CORE>=5 且 方向覆盖>=60°
READY_WITH_CAUTION    : CORE+SUPPORT>=3
CAMERA_REPAIR_REQUIRED: 其余
```

## 4. 坐标与规范

- 世界系 = Ring 系（环心原点，单位 mm）。参考帧由 005 的 `positive_gauge + xy 方位归零` 定义。
- 比较不同实验时先做**全局规范对齐**（只允许刚体变换），不得把 180° 规范差异当成相机错误。
