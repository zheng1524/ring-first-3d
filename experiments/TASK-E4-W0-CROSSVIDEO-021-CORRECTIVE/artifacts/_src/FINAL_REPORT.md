# TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE — FINAL_REPORT

```
SE3_6DOF_CORRECT:                 PASS
SAMPSON_STANDARD_CORRECT:         PASS
OPTIMIZER_BOUNDS_CORRECT:         PASS
ADAM_STATE_CORRECT:               PASS
GRADIENT_VALID:                   PASS (EPI+Prior: autograd vs FD; Ring: FD only)
W0_PROVENANCE_VALID:              PASS
W0_ADAPTER_VALID:                 PASS
HISTORICAL_SIFT_EXECUTED:         BLOCKED
MULTIVIEW_LANDMARKS_EXECUTED:     BLOCKED
HISTORICAL_RING_OBJECTIVE_EXECUTED: PARTIAL (native Ring term; 020 RingRenderer not run)
FULL_R3_OBJECTIVE_EXECUTED:       BLOCKED (L_F has no 3D identity)
TRAIN_HOLDOUT_ISOLATED:           PASS
G03_EXPERIMENT:                   PARTIAL
G01_W0_DIAGNOSTIC:                PASS
G05_W0_DIAGNOSTIC:                PASS
ONE_MAINLINE_ONLY:                PASS
CROSS_GROUP_PROTOCOL_IDENTICAL:   PASS
EXECUTED_CODE_UPLOADED:           PASS
CLEAN_REPRODUCTION:               PASS
BODY_CROSS_VIDEO_ADMISSION:       NO
```

## 1. 修复的数学（每项都有测试）

| 项 | 020 基线（无效） | 现在 | 证据 |
|---|---|---|---|
| SE(3) | `exp(q[:3])`，平移另取 `q[:3]` → 3 DoF | `exp(hat(q·scale))`，`q=(v,ω)` 六分量 | Jacobian 秩 = 6；纯平移不产生旋转；纯旋转不产生平移；与 `scipy.expm` <1e-12；与 `pytorch3d.se3_exp_map`（顺序 `(v,ω)`+转置）<1e-9 |
| Sampson | `|Fx₁|+|Fᵀx₂|` | `sqrt(四项平方和)` | 与点到极线距离一致；同 H 下旧 3.28 px / 新 4.64 px（不同量，不可比） |
| 边界 | 单步 `H_cand·H_cur⁻¹` | 累计 `H_cand·H_seed⁻¹ ≤ 1.2 mm / 10°` | `test_cumulative_*`；实测累计 0.163 mm / 3.546° |
| Adam | 拒绝后保留动量 | 拒绝回滚位姿 + m/v | `test_adam_rejection_restores_state` |
| 数据入口 | `adm.get(i,'ACCEPT')` | fail-closed：缺 admission 阻断、未知状态排除 | `test_w0_provenance` 等 4 项 |
| SIFT | 代码 4000 vs 协议 6000/.01 | 统一 6000/.01 | 本轮 G03 匹配 2003（FIT）/1746（HOLDOUT） |

## 2. 受控实验（`metrics/GEOMETRY_CORRECTNESS.csv`）

| 用例 | 真值 | 估计 | 误差 | 状态 |
|---|---:|---:|---:|---|
| A1 纯 yaw | −30° | −30.012° | **0.012°** | UNIQUE_MINIMUM |
| A4 +30% 错配 | −30° | −30.066° | **0.066°** | FLAT_OBJECTIVE |
| A7 同视频 Identity | 0° | −0.016° | **0.016°** | UNIQUE_MINIMUM |
| A2 纯平移（仅 Ring，单视角） | 0.30 mm | 0.308 mm | 0.008 mm | 切向仍不可辨识（记录） |
| A3 混合 6DoF（Ring+EPI） | 6° | — | **5.98°** | 未恢复（记录，非通过） |
| A6 Ring 对 yaw 的对称性 | 不变 | loss 变动 0.0 | **PASS** | Ring 不提供 yaw |

**A3 的失败是真实结论**：Ring 单独对 yaw 无信息（A6），而 EPI 只有尺度不变的方向信息，
所以 Ring+EPI 在合成场景里无法唯一确定旋转——这正好解释了为什么在真实数据上必须谨慎。

## 3. G03（W0 冻结输入，FIT/HOLDOUT 优化前冻结）

| 模型 | θ | FIT 中位 | HOLDOUT 中位 | 内点（FIT/HO） |
|---|---:|---:|---:|---:|
| A yaw-only | 45.446°（`AMBIGUOUS_MULTIMODAL`） | 9.669 px | 7.476 px | 26.3% / 30.4% |
| **B SE(3) 6-DoF** | 同上 | **4.637 px** | **4.538 px** | 27.7% / 29.4% |

累计修正 0.163 mm / 3.546°，80/80 步接受，全部在边界内。`L_F` 记为
`BLOCKED: no cross-video 3D landmark identity`，没有用 0 冒充。

## 4. G01/G05（同一程序，未放宽门限）

| 组 | 004 ACCEPT | 005 ACCEPT | 主导失败 |
|---|---:|---:|---|
| G01 | 0（16 QUARANTINE） | 0（16 QUARANTINE） | `HELD_P95` 超标（POSE_UNCERTAIN），2 个 RING_ERROR |
| G05 | 0（13 IE + 3 Q） | 0（16 IE） | `HELD_TRACKS` < 20（OBSERVATION_INSUFFICIENT） |

两者均记为 `BLOCKED_BY_W0_ADMISSION`，未用历史相机替代。

## 5. 回答

- **Q1 为什么 020 错？** 六维参数被截断成 3 维（前三个同时当平移和旋转）；Sampson 分母非标准；
  边界按单步检查；拒绝后 Adam 动量未回滚；Ring 用 `torus_contours` 顶替 `RingRenderer` 且未做等价性验证；SIFT 参数与协议不一致。
- **Q2 如何修？** `core/se3.py`、`core/shared_se3.py`（Sampson/边界/回滚）、`core/w0_adapter.py`（fail-closed）、
  `core/cross_video_matches.py`（6000/.01）、`core/yaw_1dof.py`（状态拆分）。每项都有对应测试。
- **Q3 六自由度是否真的独立？** 是：Jacobian 秩 6，纯平移/纯旋转分离，与两个成熟实现数值一致。
- **Q4 Ring 与 SIFT 是否真正联合？** **没有完整联合**：Ring + EPI 在跑（权重 1.0 / 0.02），
  `L_F=0.2` 因缺少跨视频三维同名身份而 **BLOCKED**，不能称 R3。
- **Q5 G03 效果？** FIT 9.669→4.637、HOLDOUT 7.476→4.538 px；内点约 28%；Ring 项未被破坏（修正 0.163 mm / 3.5°）。
- **Q6 G01/G05 为什么过不了？** G01 是残差尾部（p95）过大；G05 是有效轨迹不足（不能读作相机错）。
  门控的 `positive_depth` 字段实现与语义不符（见 `W0_EVALUATOR_BUG_REPORT.md`），但在本数据上数值恰好一致，未影响结论。
- **Q7 是否共用一套程序？** 是：同一 `core/run_corrective.py`，`runs/<G>/RUN_STATE.json` 记录同一 `code_sha256`。
- **Q8 能否扩展到其他组？** 结构上可以（`asset_resolver` + `w0_adapter` 已按 `(group, video)` 参数化），
  但需要该组先通过 W0 准入；G01/G05 目前不满足。
- **Q9 能否进入跨视频三维重建？** **NO**：无 3D 同名身份、内点约 28%、p95 仍很大。

## 6. 交付

`core/`（se3、shared_se3、yaw_1dof、geometry_1dof、cross_video_matches、w0_adapter、camera_rotation_metrics、
torch_objective、controlled、run_corrective、reproduce_offline）、`tests/`（19/19）、`config/UNIFIED_PROTOCOL.json`、
`runs/{G03,G01,G05}/`、`metrics/*.csv|json`、`baseline_020/`（无效实现冻结 + SHA）、
`artifacts/{SOURCE_AUDIT,INPUT_FIXTURES,RESULTS_AUDIT}.zip`、`CLEAN_REPRODUCTION_REPORT.json`。
