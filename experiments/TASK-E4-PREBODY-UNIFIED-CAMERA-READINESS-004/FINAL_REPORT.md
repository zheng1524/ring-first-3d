# FINAL_REPORT — PRE-BODY UNIFIED CAMERA READINESS

**STATUS: `PARTIAL_EXECUTION` / `AWAITING_RA_REVIEW`**

## 0. 先说清楚做了什么、没做什么

| 步骤 | 状态 |
|---|---|
| Step 1 原始视频审计 | **完成**：结论是原始视频不可得、INIT 权重受限制（见 RAW_VIDEO_PROVENANCE.md） |
| Step 2 统一视频准备（raw→INIT Mask） | **BLOCKED_RESTRICTED_WEIGHTS**，未执行 |
| Step 3 8/16/22 全量密度 | **未执行**（前端阻塞；003 已证仅 2 段可跑） |
| Step 4 相机恢复与审计 | **执行**：复用 005 冻结相机，10 段全量 |
| Step 5 异常诊断（R0–R3、时间正则） | **未执行**（需重跑 BA，预算不足） |
| Step 6 可视化 | **部分**：6 张真实数据图（Ring 投影 3、相机网络 2、密度对照 1）；六方向相机网络未做 |
| Step 7 Body 准入 | **执行**：10 张 BODY_READINESS_CARD |

**任何"已改善"的结论都不会在本报告出现**，因为稳健 BA 与密度均未在本轮执行。

## 1. 总表（十段视频）

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

## 2. Q1–Q7

**Q1 是否实现了 raw→camera 的统一流程？**
**没有。** 统一程序已写好（单入口、单配置、无按病例分支，测试断言），但**前端（raw→INIT Mask）被权重限制阻塞**，本轮只能用 005 冻结 Mask。这是已声明偏差，不是静默替代。

**Q2 增加视角带来什么？**
本轮未执行密度全量。可引用 003 的**外部证据**（仅 G02/005、G05/005 可跑）：G02/005 held 28.10→8.24（N=16），G05/005 VALIDATED 1→9（N=22）。三维上，新增相机主要补充了**不同方位**的相机，网络连通性上升，但 G02/005 的 p95 仍 61 px，说明仍有少数拖尾视角。

**Q3 最大误差来源？**
按分类：`D_BA_CONFLICT` 28/80 最多，`C_INIT_OR_GAUGE` 10，`A_RING` 6，`E` 1，`OK` 35。**主要矛盾是多视角几何冲突，而不是单视角 Mask 错误。**

**Q4 是否值得排除极端视角？**
**值得，但本轮未做**。需要 R0–R3 实验证明"剔除后其余相机更好"。判据已预先写在 EXPERIMENT_PROTOCOL.md（其余相机 held 中位降 ≥20% 且 CORE 不减少）。

**Q5 稳健 BA / 时间正则能否改善？**
**未知（未执行）**。不得在未做实验时声称改善。

**Q6 是否已有足够相机支持 Body？**
- **READY_WITH_CAUTION（7 段）**：G01/004、G01/005、G03/005、G05/004、G05/005、G06/004、G06/005。
- **CAMERA_REPAIR_REQUIRED（3 段）**：G02/004、G02/005、G03/004。
- **READY_FOR_BODY_INIT：0 段**（严格判据下 CORE≥5 且覆盖≥60° 无人达到）。
- 推荐优先进入受控 Body 初始化：**G06/005（5 CORE，held 2.47 px）**、**G03/005（2 CORE + 5 SUPPORT，held 6.13 px）**。

**Q7 继续降误差 vs 直接开始 Body，哪个收益更大？**
**对 7 段 CAUTION 视频，直接开始受控 Body 初始化的收益更大**：其 held 中位 4.1–9.7 px，相机网络已连通，继续压误差的边际收益低于获得三维主体先验的收益。
**对 3 段 REPAIR 视频（G02/004、G02/005、G03/004），继续修相机收益更大**，尤其 G02/005——003 已证明密度是有效手段。

## 3. 科学边界

- 未使用 Body/GT 参与任何相机计算；`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`。
- 未修改 005、DXY、001/002/003；只读消费其冻结产物。
- 未删除任何困难视角；QUARANTINE 保留原始观测与相机。
- 未用 held 选择分类阈值或准入规则（阈值来自配置，先于运行固定）。

## 4. 主要风险

1. **前端阻塞**使"统一流程"目前只统一了后半段；要真正端到端，必须先解除权重/视频限制。
2. **分类阈值未经验证**（15°/20 mm/10 px 为工程初值），尚未做敏感性分析。
3. **可视化不完整**：缺六方向相机网络、RGB 重投影差异图、posthoc Body 诊断。
4. 013/004 等实例的 `raw_frame` 未做像素级复核（因无法从原视频重生成）。
