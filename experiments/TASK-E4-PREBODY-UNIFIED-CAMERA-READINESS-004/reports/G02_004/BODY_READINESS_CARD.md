# BODY_READINESS_CARD — G02/004

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G02/004
总候选视角：8
成功恢复相机：8
Ring 门禁通过：6
RGB 几何验证通过：0

CORE：0
SUPPORT：2
QUARANTINE：6

可靠方向覆盖：205.8 deg
Ring 中位：2.26 px
RGB held 中位：15.32 px
RGB held p95：67.48 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G02_v004_raw00900 | 84.8 | 2.28 | D_BA_CONFLICT | held=84.8 with covis=7 |
| G02_key04_raw00570 | 35.3 | 1.95 | D_BA_CONFLICT | held=35.3 with covis=7 |
| G02_key01_raw00219 | 19.6 | 2.24 | D_BA_CONFLICT | held=19.6 with covis=7 |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: G02_v004_raw00333, G02_key02_raw00336
- QUARANTINE: G02_key01_raw00219, G02_key04_raw00570, G02_v004_raw00753, G02_v004_raw00816, G02_v004_raw00837, G02_v004_raw00900

## 准入结论：**CAMERA_REPAIR_REQUIRED**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。