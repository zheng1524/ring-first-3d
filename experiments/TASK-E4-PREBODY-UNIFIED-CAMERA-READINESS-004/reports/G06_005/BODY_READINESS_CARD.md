# BODY_READINESS_CARD — G06/005

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

```text
实例：G06/005
总候选视角：8
成功恢复相机：8
Ring 门禁通过：8
RGB 几何验证通过：5

CORE：5
SUPPORT：3
QUARANTINE：0

可靠方向覆盖：27.9 deg
Ring 中位：0.66 px
RGB held 中位：2.47 px
RGB held p95：4.26 px
```

## 严重异常（按 held 排序）

| view | held | Ring | class | reason |
|---|---:|---:|---|---|
| G06_v005_raw00682 | 4.7 | 0.87 | OK |  |
| G06_v005_raw00311 | 3.5 | 0.62 | OK |  |
| G06_v005_raw00604 | 3.3 | 0.70 | OK |  |

## 建议用于 Body 初始化的相机

- CORE: G06_v005_raw00291, G06_v005_raw00487, G06_v005_raw00506, G06_v005_raw00643, G06_v005_raw00663
- SUPPORT: G06_v005_raw00311, G06_v005_raw00604, G06_v005_raw00682
- QUARANTINE: (none)

## 准入结论：**READY_WITH_CAUTION**

对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`

> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。