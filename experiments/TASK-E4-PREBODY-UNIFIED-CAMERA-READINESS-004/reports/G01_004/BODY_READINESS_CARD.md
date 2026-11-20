# BODY_READINESS_CARD — G01/004

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G01/004
总候选视角：8
成功恢复相机：8
Ring 门禁通过：8
RGB 几何验证通过：0

CORE：0
SUPPORT：4
QUARANTINE：4

可靠方向覆盖：35.4 deg
Ring 中位：1.13 px
RGB held 中位：8.53 px
RGB held p95：23.82 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G01_004_ref03 | 29.1 | 1.15 | D_BA_CONFLICT | held=29.1 with covis=7 |
| G01_video004_004_05 | 14.1 | 1.88 | D_BA_CONFLICT | held=14.1 with covis=7 |
| G01_004_ref08 | 13.1 | 1.39 | D_BA_CONFLICT | held=13.1 with covis=7 |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: G01_004_ref13, G01_v004_raw01086, G01_v004_raw01112, G01_v004_raw01138
- QUARANTINE: G01_004_ref03, G01_004_ref08, G01_v004_raw00878, G01_video004_004_05

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。