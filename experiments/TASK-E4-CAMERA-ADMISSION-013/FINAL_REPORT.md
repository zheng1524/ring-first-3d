# TASK-E4-CAMERA-ADMISSION-013 — FINAL_REPORT

```
CAMERA_MAINLINE = W0
CAMERA_ADMISSION_GATE = READY
SINGLE_VIDEO_CAMERA_RESEARCH = CLOSED
```

## 1. 异常审查（各一轮，已定性）

| 视角 | 臂 | 原报 held | 定性 | 证据 |
|---|---|---:|---|---|
| raw00229 | W0 | 10.72 | **TRIANGULATION_ERROR** | 146 条轨迹中位 0.98、p95 2.88；max 1369.9 来自基线 0.44 mm 的退化三角化 |
| raw00186 | W3 | 6.75 | **TRIANGULATION_ERROR** | 主因 track 1065 基线 0.42 mm；次因 track 245 夹角 14.5° |

结论：**轨迹异常 ≠ 相机异常**。16 视角共 302 条轨迹因基线 <2 mm 被排除，该缺陷属评价器级，B0/W0 同样受影响。
因此旧 held 数值不可再用于比较，本轮全部重算。

## 2. 统一准入 Gate（长期成果）

- `code/camera_admission.py`：单实现，四状态 `ACCEPT / QUARANTINE / REJECT / INSUFFICIENT_EVIDENCE`，两级判断（硬性失败直接 REJECT；指标未达标先 QUARANTINE，允许一次定向诊断，仍不达标则 REJECT；证据不足标 INSUFFICIENT_EVIDENCE）。
- `policy/CAMERA_ADMISSION_POLICY.yaml`：阈值冻结，全组共享；含"孤立坏轨迹不得否定整个视角"的规则。
- 单元测试 **7/7 通过**（正常接受、非法位姿拒绝、证据不足、Ring 不合格、孤立坏轨迹、诊断后拒绝、无证据参考照片）。

## 3. 准入结果（G03/005）

| 臂 | ACCEPT | Ring raw | held 中位 | p95 |
|---|---:|---:|---:|---:|
| B0 | 16 | 0.844 | 1.113 | 3.354 |
| W0 | 16 | **0.829** | **0.990** | **3.319** |

## 4. 决策

- **CAMERA_MAINLINE = W0**（16/16 ACCEPT，两项指标均略优，异常已排除为三角化问题）。
- 冻结至 `camera_mainline/G03/video005/`，保留 B0/W0 原始结果，未覆盖任何历史文件。
- **单视频相机算法研究关闭**；J2/J3 不再实验。

## 5. 交付

`ANOMALY_DIAGNOSIS.md`、`CAMERA_MAINLINE_DECISION.md`、`FINAL_REPORT.md`、
`policy/CAMERA_ADMISSION_POLICY.yaml`、`code/{camera_admission,diagnose_anomaly,j2_obs_correct}.py`、
`tests/test_camera_admission.py`、`metrics/{ANOMALY_TRACK_ERRORS,ADMISSION_RESULTS,REJECTED_VIEW_LEDGER}.csv`、
`visualization/{anomaly_raw00229,anomaly_raw00186}.png`、`camera_mainline/G03/video005/*`。

## 6. 下一步

`TASK-E4-CROSS-VIDEO-CAMERA-014`：用同一 Gate 独立评价其余九段视频；
不满足的视角按 §P3 补位；缺失方向如实报告。
