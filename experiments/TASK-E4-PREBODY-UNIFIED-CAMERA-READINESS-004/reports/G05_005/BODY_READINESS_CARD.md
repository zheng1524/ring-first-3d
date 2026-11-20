# BODY_READINESS_CARD — G05/005

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G05/005
总候选视角：8
成功恢复相机：8
Ring 门禁通过：7
RGB 几何验证通过：2

CORE：1
SUPPORT：4
QUARANTINE：3

可靠方向覆盖：33.8 deg
Ring 中位：0.80 px
RGB held 中位：4.11 px
RGB held p95：16.56 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G05_v005_raw00082 | 18.1 | 0.81 | D_BA_CONFLICT | held=18.1 with covis=7 |
| G05_v005_raw00251 | 13.7 | 0.78 | D_BA_CONFLICT | held=13.7 with covis=7 |
| G05_v005_raw00404 | 7.2 | 9.94 | A_RING_OBSERVATION | ring gate failed (9.94 px) |

## 建议用于 Body 初始化的相机

- CORE: G05_v005_raw00150
- SUPPORT: G05_v005_raw00167, G05_v005_raw00285, G05_v005_raw00353, G05_v005_raw00437
- QUARANTINE: G05_v005_raw00082, G05_v005_raw00251, G05_v005_raw00404

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。