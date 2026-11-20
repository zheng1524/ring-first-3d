# BODY_READINESS_CARD — G02/005

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G02/005
总候选视角：8
成功恢复相机：8
Ring 门禁通过：8
RGB 几何验证通过：0

CORE：0
SUPPORT：0
QUARANTINE：8

可靠方向覆盖：88.4 deg
Ring 中位：1.94 px
RGB held 中位：28.10 px
RGB held p95：61.16 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G02_v005_raw00661 | 66.8 | 1.81 | D_BA_CONFLICT | held=66.8 with covis=7 |
| G02_v005_raw00511 | 50.8 | 1.81 | D_BA_CONFLICT | held=50.8 with covis=7 |
| G02_v005_raw00703 | 41.2 | 2.00 | D_BA_CONFLICT | held=41.2 with covis=7 |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: (none)
- QUARANTINE: G02_v005_raw00104, G02_v005_raw00211, G02_v005_raw00318, G02_v005_raw00511, G02_v005_raw00575, G02_v005_raw00661, G02_v005_raw00703, G02_v005_raw00875

## 准入结论：**CAMERA_REPAIR_REQUIRED**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。