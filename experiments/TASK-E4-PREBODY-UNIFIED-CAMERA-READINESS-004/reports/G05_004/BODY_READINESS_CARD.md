# BODY_READINESS_CARD — G05/004

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G05/004
总候选视角：8
成功恢复相机：8
Ring 门禁通过：6
RGB 几何验证通过：0

CORE：0
SUPPORT：4
QUARANTINE：4

可靠方向覆盖：23.7 deg
Ring 中位：1.58 px
RGB held 中位：9.67 px
RGB held p95：34.17 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G05_v004_raw00676 | 39.6 | 3.62 | A_RING_OBSERVATION | ring gate failed (3.62 px) |
| G05_key04_raw00542 | 24.2 | 3.25 | A_RING_OBSERVATION | ring gate failed (3.25 px) |
| G05_v004_raw00357 | 12.7 | 2.47 | D_BA_CONFLICT | held=12.7 with covis=7 |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: G05_key00_raw00097, G05_v004_raw00117, G05_v004_raw00197, G05_v004_raw00217
- QUARANTINE: G05_key02_raw00320, G05_v004_raw00357, G05_key04_raw00542, G05_v004_raw00676

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。