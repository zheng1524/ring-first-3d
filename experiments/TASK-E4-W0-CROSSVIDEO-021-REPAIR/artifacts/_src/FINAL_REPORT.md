# TASK-E4-W0-CROSSVIDEO-021-REPAIR — FINAL_REPORT

```
SE3_SIX_DOF_VALID:            PASS
SAMPSON_STANDARD_VALID:       PASS
OPTIMIZER_STATE_VALID:        PASS
OPTIMIZER_CUMULATIVE_BOUND:   PASS
W0_INPUT_SINGLE_SOURCE:       PASS
W0_ADMISSION_FAIL_CLOSED:     PASS
HISTORICAL_MODULE_REUSE:      PARTIAL
RING_OBJECTIVE_EQUIVALENCE:   NOT_VERIFIED
SIFT_PIPELINE_CONFIG_MATCH:   PASS
G03_CROSSVIDEO:               PARTIAL
G01_W0:                       BLOCKED
G05_W0:                       BLOCKED
HOLDOUT_INDEPENDENT:          PASS
CROSS_GROUP_PROTOCOL_IDENTICAL: PASS
EXECUTED_SOURCE_COMPLETE:     PASS
CLEAN_REPRODUCTION:           PASS
BODY_CROSS_VIDEO_ADMISSION:   NO
```

## 1. 三个真实数学/流程错误（均已修复并测试）

| # | 错误 | 证据 | 修复 |
|---|---|---|---|
| C1 | `exp_se3` 用 `q[:3]` 同时当平移和旋转，**只有 3 个自由度生效** | 020 版 `det(R)=1` 测试仍能通过 | 新 `camera_mainline/code/se3.py`，精确 6-DoF exp map，与 `scipy.linalg.expm` <1e-12、与 `pytorch3d.se3_exp_map`（顺序 `(v,ω)` + 转置）~1e-17 |
| C2 | Sampson 分母是 `|Fx1|+|Fᵀx2|`，**不是标准定义** | 同一批匹配两种公式差 30% | `sqrt((Fx1)₁²+(Fx1)₂²+(Fᵀx2)₁²+(Fᵀx2)₂²)`，与点到极线距离单元测试一致 |
| C3/C4 | 边界施加在**单步**上；拒绝后 Adam 动量未回滚 | 代码审查 | 累计约束 `H_cand·H_seed⁻¹ ≤ 1.2 mm / 10°`；拒绝时位姿+Adam 状态完全回滚 |
| C5 | 协议写 6000/.01，代码实际 4000 | 配置 vs 执行 | 对齐为 `nfeatures=6000, contrastThreshold=0.01` |
| C6 | `adm.get(i,'ACCEPT')` 缺字段默认通过 | 代码审查 | `w0_adapter.py` fail-closed：缺 admission → 阻断；未知状态 → 排除 |

## 2. G03 重跑（FIT/HOLDOUT 在优化前冻结）

| 模型 | θ | FIT 中位（标准 Sampson） | HOLDOUT 中位 | FIT 内点3 | HOLDOUT 内点3 |
|---|---:|---:|---:|---:|---:|
| A yaw-only | 45.45° | 9.67 px | 7.48 px | — | — |
| **B SE(3) 6-DoF** | 45.45° | **4.64 px** | **4.54 px** | 27.7% | 29.4% |

- 累计修正 **0.163 mm / 3.55°**，80/80 步接受，全部在 1.2 mm / 10° 内。
- yaw 求解器状态是 **`AMBIGUOUS_MULTIMODAL`**（不再被强行标成 "可辨识"）。
- 旧非标准公式在同一 H 上给出 3.28 px —— **与 4.64 px 不是同一个量，不能与 020 的 4.248 比较**。

## 3. G01/G05：`BLOCKED_BY_W0_ADMISSION`（如实保留，未放宽阈值）

| 组 | 004 | 005 | 主导失败类别 |
|---|---|---|---|
| G01 | 0 ACCEPT（14 POSE_UNCERTAIN + 2 RING_ERROR） | 0 ACCEPT（15 POSE_UNCERTAIN + 1 EVAL） | **POSE_UNCERTAIN**（held p95 > 8 px） |
| G05 | 0 ACCEPT（13 OBSERVATION_INSUFFICIENT + 3 POSE_UNCERTAIN） | 0 ACCEPT（16 OBSERVATION_INSUFFICIENT） | **OBSERVATION_INSUFFICIENT**（有效轨迹 <20），≠ 相机错误 |

## 4. 如实标注的未完成项

- `RING_OBJECTIVE_EQUIVALENCE = NOT_VERIFIED`：`torus_contours` 版 Ring 项与 020 `RingRenderer` 未做数值对照（legacy 逐视角缓存缺失）。
- `HISTORICAL_MODULE_REUSE = PARTIAL`：复用的是数学与调度（已与 PyTorch3D 交叉验证），019/020 模块本体未端到端执行。
- `L_F`（双向 3D 地标重投影）仍不存在：没有跨视频 3D 同名身份；**没有用 0 冒充**。
- 019 的多视角轨迹/三角化流程尚未接入（SIFT 只到成对匹配）。

## 5. 交付

`code/run_cross_video.py`（单一入口，按 stage 写 `audit/<G>/RUN_STATE.json`，原子写入）、
`camera_mainline/code/{se3,shared_se3,yaw_1dof,cross_video_matches,w0_adapter}.py`、
`tests/{test_se3_math,test_optimizer,test_data_contract}.py`（**23/23 通过**）、
`metrics/*`（SE3/SAMPSON/OPTIMIZER 验证、G03 结果、W0 准入审计、组间对比、离线复现）、
`baseline_020/`（无效实现冻结 + SHA）、三份审计包。
