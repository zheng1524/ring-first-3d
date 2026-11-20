# CAMERA_READINESS_SUMMARY

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

## 总表（十段视频）

| Group/Video | Views | Ring Median | RGB Held Median | RGB p95 | CORE | SUPPORT | QUARANTINE | Coverage(deg) | Body Ready |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| G01/4 | 8 | 1.13 | 8.53 | 23.82 | 0 | 4 | 4 | 35.4 | READY_WITH_CAUTION |
| G01/5 | 8 | 1.00 | 9.56 | 38.01 | 0 | 4 | 4 | 93.6 | READY_WITH_CAUTION |
| G02/4 | 8 | 2.26 | 15.32 | 67.48 | 0 | 2 | 6 | 205.8 | CAMERA_REPAIR_REQUIRED |
| G02/5 | 8 | 1.94 | 28.10 | 61.16 | 0 | 0 | 8 | 88.4 | CAMERA_REPAIR_REQUIRED |
| G03/4 | 8 | 0.67 | 27.50 | 483.87 | 0 | 0 | 8 | 169.0 | CAMERA_REPAIR_REQUIRED |
| G03/5 | 8 | 0.77 | 6.13 | 14.99 | 2 | 5 | 1 | 22.6 | READY_WITH_CAUTION |
| G05/4 | 8 | 1.58 | 9.67 | 34.17 | 0 | 4 | 4 | 23.7 | READY_WITH_CAUTION |
| G05/5 | 8 | 0.80 | 4.11 | 16.56 | 1 | 4 | 3 | 33.8 | READY_WITH_CAUTION |
| G06/4 | 8 | 0.80 | 4.61 | 13.90 | 0 | 6 | 2 | 14.4 | READY_WITH_CAUTION |
| G06/5 | 8 | 0.66 | 2.47 | 4.26 | 5 | 3 | 0 | 27.9 | READY_WITH_CAUTION |

## 异常分类分布（80 FIT 视角）

| 类别 | 数量 |
|---|---:|
| C_INIT_OR_GAUGE | 73 |
| A_RING_OBSERVATION | 6 |
| E_INSUFFICIENT_OBSERVATION | 1 |

## 读法

- **CORE 只占少数**：80 视角中 CORE 合计 8，说明当前多数相机"Ring 可用但 RGB 未完全验证"。
- **QUARANTINE 集中在 G02/004、G02/005、G03/004**：三者的 held 中位 15–28 px。
- **G06/005 最健康**（5 CORE、held 2.47 px），但方向覆盖不足 60°，故判 READY_WITH_CAUTION。
- 没有实例达到 READY_FOR_BODY_INIT；这只说明"严格判据下如此"，不代表不能做受控实验。
