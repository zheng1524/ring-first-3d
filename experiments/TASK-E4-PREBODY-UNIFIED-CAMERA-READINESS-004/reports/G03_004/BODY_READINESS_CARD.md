# BODY_READINESS_CARD — G03/004

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G03/004
总候选视角：8
成功恢复相机：8
Ring 门禁通过：8
RGB 几何验证通过：0

CORE：0
SUPPORT：0
QUARANTINE：8

可靠方向覆盖：169.0 deg
Ring 中位：0.67 px
RGB held 中位：27.50 px
RGB held p95：483.87 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G03_key00_raw00100 | 721.5 | 0.58 | D_BA_CONFLICT | held=721.5 with covis=7 |
| G03_key07_raw00896 | 42.6 | 1.45 | D_BA_CONFLICT | held=42.6 with covis=7 |
| G03_key04_raw00554 | 35.8 | 0.96 | C_INIT_OR_GAUGE | held=35.8 axis_off=18.8 |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: (none)
- QUARANTINE: G03_key00_raw00100, G03_key02_raw00327, G03_v004_raw00426, G03_v004_raw00467, G03_v004_raw00487, G03_key04_raw00554, G03_v004_raw00569, G03_key07_raw00896

## 准入结论：**CAMERA_REPAIR_REQUIRED**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。