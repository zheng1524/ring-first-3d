# BODY_READINESS_CARD — G06/004

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G06/004
总候选视角：8
成功恢复相机：8
Ring 门禁通过：7
RGB 几何验证通过：0

CORE：0
SUPPORT：6
QUARANTINE：2

可靠方向覆盖：14.4 deg
Ring 中位：0.80 px
RGB held 中位：4.61 px
RGB held p95：13.90 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G06_v004_raw00874 | 15.5 | 3.83 | A_RING_OBSERVATION | ring gate failed (3.83 px) |
| G06_004_new_r00 | 10.9 | 0.74 | D_BA_CONFLICT | held=10.9 with covis=7 |
| G06_004_growth_r03 | 7.1 | 0.57 | OK |  |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: G06_v004_raw00151, G06_v004_raw00195, G06_004_growth_r01, G06_v004_raw00326, G06_004_growth_r03, G06_004_ref04
- QUARANTINE: G06_004_new_r00, G06_v004_raw00874

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。