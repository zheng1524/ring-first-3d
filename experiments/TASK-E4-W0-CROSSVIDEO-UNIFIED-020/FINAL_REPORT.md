# TASK-E4-W0-CROSSVIDEO-UNIFIED-020 — FINAL_REPORT

```
SOURCE_DISCOVERY:            PASS
W0_MAINLINE_UNIQUE:          PASS
W0_GROUP_G03:                PASS   (6 ACCEPT / 16 ACCEPT)
W0_GROUP_G01:                FAIL   (0 ACCEPT: 16 QUARANTINE both videos)
W0_GROUP_EXTRA(G05):         FAIL   (0 ACCEPT: 13 IE + 3 Q / 16 IE)
HISTORICAL_MODULES_REUSED:   PARTIAL
ADAPTER_EQUIVALENCE:         PASS
COMMON_SIFT_PIPELINE:        PASS
COMMON_LANDMARK_PIPELINE:    PARTIAL  (2D-2D only; no cross-video 3D identity)
RING_GRADIENT:               PASS (ring term active and differentiable; not the legacy mesh renderer)
RGB_GRADIENT:                PASS (FD gradient descent verified, grad_norm 0.865)
SHARED_SE3_EXECUTED:         PASS (G03)
HOLDOUT_VALIDATION:          PASS (G03: 5.855 px on unseen 005 views)
CROSS_GROUP_PROTOCOL_IDENTICAL: PASS (one code hash, one config)
EXECUTED_CODE_UPLOADED:      PASS
CLEAN_REPRODUCTION:          PASS (offline: 5.323 -> 4.248 px, exact)
BODY_CROSS_VIDEO_ADMISSION:  NO
```

## 1. 三个组的真实 W0 结果（同一入口 `tools/run_w0_camera.py`）

| 组 | 004 ACCEPT | 005 ACCEPT | Ring raw | held 中位 | 结论 |
|---|---:|---:|---:|---:|---|
| **G03** | 6 | 16 | 0.83 / 0.96 | 0.98 | 可做跨视频 |
| G01 | 0（16 QUARANTINE） | 0（16 QUARANTINE） | 1.47 / 0.91 | 6.02 / 2.63 | 未通过 W0 |
| G05 | 0（13 IE + 3 Q） | 0（16 IE） | 0.81 / 0.60 | 3.39 / 27.15 | 未通过 W0 |

**这是本轮最重要的发现**：冻结 W0 + 冻结准入策略在 G01/G05 上**没有一个视角达到 ACCEPT**。
按任务要求如实标记，不回退 B0/RoMa/历史相机，也不为某组放宽阈值。

## 2. 跨视频实验（G03，唯一具备 ACCEPT 相机网络的组）

| 指标 | seed（1-DoF yaw 47.67°） | 共享 SE(3) 之后 |
|---|---:|---:|
| 正向 Sampson 中位 | 5.32 px | **4.25 px** |
| 3 px 内点比例 | 31.5% | **39.0%** |
| 目标（Ring + 0.02·Epi + 0.01·Prior） | 0.2165 | **0.1803** |
| 修正量 | — | **0.040 mm / 2.27°** |
| 留出（4 个未见 005 视角） | — | **5.855 px / 31.0%** |

Ring 项单独报告为 0.1074；对极项 5.4528（未加权）。**L_F（双向 3D 地标重投影）不存在**，因为还没有跨视频 3D 同名身份 —— 记为缺失，不用 0 冒充。

## 3. 回答

- **Q1 是否只有一套主线？** 是。三组都走 `tools/run_w0_camera.py`；`INPUT_SHA256.csv` 记录了每组的 `camera_result.npz` 来源；
  G01/G05 是**本轮现场运行**的 W0（不是历史冻结相机）。
- **Q2 历史 019/020 复用了什么？** 复用其数学：`H=exp(q·scale)@seed`、Adam lr .01 + 回溯 8 次 + 1.2 mm/10° 边界、
  Ring 曲线 `dist/3` Huber、双向对极项、权重 1.0/0.02/0.01。源码 SHA 见 `SOURCE_REUSE_MATRIX.csv`；
  但 **019/020 原始模块没有端到端执行**（legacy 逐视角缓存缺失），所以是 `PARTIAL` 而不是 `PASS`。
- **Q3 是否新造算法？** 三处改动都在 `ALGORITHM_CHANGE_LEDGER.csv`：
  C1 `exp_se3` 用 6 维模长（L2 已修）；C2 匹配器路径按组参数化（L1）；C3 用 `torus_contours` 像素曲线替代 `RingRenderer`（**L2，需人工复核**）。
- **Q4 三组参数是否一致？** 是。`config/UNIFIED_PROTOCOL.json` 单一文件，`RUN_STATE.json` 里 `code_hash` 相同，
  且 `test_no_group_branch_in_entry` 断言入口无组分支。
- **Q5 Ring 与 RGB 是否同时改善？** G03 上：RGB 中位 5.32→4.25 px；Ring 项在优化中保持同量级（0.107），
  修正仅 0.04 mm/2.27°，没有用破坏 Ring 换取 RGB。**但没有独立证据表明 Ring 也变好**，只能说未被破坏。
- **Q6 错误在哪一阶段？** G01/G05：`W0_POSE_ERROR`（单视频相机未过门控），不是跨视频算法问题；
  G03：`FEATURE_MATCHING_ERROR`（内点 39%、p95 92 px）。
- **Q7 相比 018-REPAIR 有进展吗？** 有，但**不能直接比大小**：018 用的是同一批匹配但不同目标与聚合方式。
  本轮可比的是：同一个 W0 输入、同一个目标函数下，SE(3) 把 5.32→4.25 px，且留出 5.86 px 与训练侧一致（018 的留出是 14.45 px）。
  差异来自 018 只在 yaw 上留出、没有共享 SE(3) 项。
- **Q8 可否进入跨视频三维重建？** **NO**。内点 39%、p95 92 px、无 3D 同名身份，不满足独立几何证据。

## 4. 交付

`code/run_cross_video.py`、`adapters/{asset_resolver,coordinate_adapter,w0_to_crossvideo020}.py`、
`config/UNIFIED_PROTOCOL.json`、`tests/test_protocol.py`(8/8)、`audit/{SOURCE_REGISTRY.json,RUN_STATE.json,INPUT_SHA256.csv,OUTPUT_SHA256.csv}`、
`metrics/{CROSS_GROUP_COMPARISON,HOLDOUT_EVALUATION,COMMON_GEOMETRY,GRADIENT_CHECK,OFFLINE_REPRODUCTION}.csv|json`、
`runs/{G01,G03,G05}/`、`artifacts/{SOURCE_AUDIT,INPUT_FIXTURES,RESULTS_AUDIT}.zip`。
