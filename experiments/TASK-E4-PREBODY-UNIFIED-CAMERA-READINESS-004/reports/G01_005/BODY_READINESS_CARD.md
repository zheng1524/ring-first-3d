# BODY_READINESS_CARD — G01/005

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G01/005
总候选视角：8
成功恢复相机：8
Ring 门禁通过：8
RGB 几何验证通过：0

CORE：0
SUPPORT：4
QUARANTINE：4

可靠方向覆盖：93.6 deg
Ring 中位：1.00 px
RGB held 中位：9.56 px
RGB held p95：38.01 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G01_v005_raw00721 | 41.7 | 0.88 | C_INIT_OR_GAUGE | held=41.7 axis_off=17.5 |
| G01_v005_raw00192 | 31.1 | 1.02 | D_BA_CONFLICT | held=31.1 with covis=7 |
| G01_v005_raw00262 | 15.1 | 0.77 | D_BA_CONFLICT | held=15.1 with covis=7 |

## 建议用于 Body 初始化的相机

- CORE: (none)
- SUPPORT: G01_005_raw00057, G01_v005_raw00139, G01_video005_v005_00401, G01_video005_v005_00860
- QUARANTINE: G01_v005_raw00192, G01_v005_raw00262, G01_v005_raw00721, G01_video005_v005_00611

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。