# BODY_READINESS_CARD — G03/005

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G03/005
总候选视角：8
成功恢复相机：8
Ring 门禁通过：8
RGB 几何验证通过：2

CORE：2
SUPPORT：5
QUARANTINE：1

可靠方向覆盖：22.6 deg
Ring 中位：0.77 px
RGB held 中位：6.13 px
RGB held p95：14.99 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G03_v005_raw00474 | 18.6 | 0.67 | D_BA_CONFLICT | held=18.6 with covis=7 |
| G03_v005_raw00561 | 8.3 | 0.76 | OK |  |
| G03_v005_raw00546 | 8.2 | 0.74 | OK |  |

## 建议用于 Body 初始化的相机

- CORE: G03_v005_raw00373, G03_v005_raw00589
- SUPPORT: G03_v005_raw00070, G03_v005_raw00099, G03_v005_raw00402, G03_v005_raw00546, G03_v005_raw00561
- QUARANTINE: G03_v005_raw00474

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。