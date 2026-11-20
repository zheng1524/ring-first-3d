# G01_REFERENCE_PIPELINE

**Task:** TASK-E4-G01-PIPELINE-AUDIT-003
**Status:** `AWAITING_RA_REVIEW`
**审计方式：** 只读源码追溯 + 冻结产物统计。未运行任何求解器、未重训、未修改 DXY。
**快照：** `/home/liu/ring_first_3d_workspace` @ `ff24295`；历史源 `/home/liu/polyp_research/ring_anchor_3d/experiments/`

---

## 0. 核心结论（先读这一节）

**项目里不存在"一条 G01 成熟流程"。存在两条互不相同的上游，G01 的 004 与 005 分别来自不同的一条。**

| | **A 线（004 线，E4/native）** | **B 线（005 线，V6）** |
|---|---|---|
| 时间 | 2026-10 起，E4 系列逐步固化；2026-11-19 由 001 冻结 | 2026-10-19，`ring_first_v6_local_reconstruction` |
| Ring 观测 | `observe()` 直接取 labels 边界 | DXY 分割 + 补洞 + 连通域 + held 切分 |
| Ring 求解配置 | `seed_retain=2, max_nfev=35` | `seed_retain=4, max_nfev=100` |
| 求解内核 | `_kernels.decode/solve` | **同一份内核**（源 `ring_pose_contact_v1/scripts/recover.py`） |
| 最终相机 | 逐视角 `recover()`（PnP 种子 → 5DOF → yaw） | `local_ring_sfm.BA` 的全局输出 |
| 验证 | 3 px Ring 门限 | `validate_select` held 轨道验证 + 视角筛选 |
| 产出 | 004 相机、`reference_banks` | 005 相机、005 HERO、005 开放 Mesh |

`TASK-E4-UNIFIED-PIPELINE-COMPLETION-002`（下称 002）把 **B 线的参考库** 与 **A 线的最终相机** 组合在一起。这个组合在历史实验中从未出现过。

**因此对"G01 成熟实现"的任何引用，都必须先指明是 A 线还是 B 线。**

---

## 1. 权威 Ring 求解内核的共同祖先

`native/_kernels.py` 中的 `decode` / `image_seeds` / `solve` 三个函数，与 2026-10-15 首次出现的 `ring_pose_contact_v1/scripts/recover.py` **逐字节相同**（AST 抽取后字符串比较）。

| 函数 | `native/_kernels.py` | 源 `ring_pose_contact_v1/scripts/recover.py` | 判定 |
|---|---|---|---|
| `decode(a, ref)` | :21-22 | 同名 | `IDENTICAL` |
| `image_seeds(ob)` | :24-30 | 同名 | `IDENTICAL` |
| `solve(obs, ref, seeds)` | :32-41 | 同名 | `IDENTICAL` |
| `torus_residual` | :43-48 | 不同文件（`torus_residual` 由 `native/camera.residual` 绑定） | 见下 |

**五参数的物理含义（源码直接可读）：**

```
a = [a0, a1, a2, a3, a4]
center = ref_t + ref_R @ [a0·z, a1·z, z],  z = exp(a2)
Q      = ref_R @ Rotvec([a3, a4, 0])
```

即：2 个像平面位置（按深度缩放）+ 1 个对数深度 + 2 个环法向倾角分量。**绕环轴的 yaw 不在这 5 个参数内**，它是第 6 个自由度，由 RGB 单独消歧（见 §2.2）。

求解器：`least_squares(..., loss='soft_l1', f_scale=huber_px, max_nfev=cfg['max_nfev'], bounds=([-3,-3,log5,-1.55,-1.55],[3,3,log500,1.55,1.55]))`，按初始种子 loss 排序后取前 `cfg['seed_retain']` 个分别优化，最后按 loss 排序返回。

**关键：内核相同，但"喂多少算力"由调用方决定。** 这是 A/B 两线出现的第一处分叉。

---

## 2. A 线：004 的成熟实现（E4/native → 001）

### 2.1 阶段表

| # | 阶段 | 真实函数（file:line） | 输入 | 关键参数 | 输出 | 证据类型 |
|---|---|---|---|---|---|---|
| A1 | 冻结输入与视角选择 | 001 `audit/SELECTED_VIEWS.json`；`pipeline.py: audit()` | RGB/Mask/cache/K/Ring/初始 Mesh | 8 FIT / HOLDOUT 分离 | 视图清单 | **重算（冻结）** |
| A2 | Ring 观测 | `native/camera.py:39-49 observe(labels)` | 360×640 labels(0/1/2) | 5×5 膨胀判遮挡；`q_train` 采样 128；`p/b_train` 192 | `mask/q_train/unknown_boundary/p_train/b_train` | 重算 |
| A3 | 参考库 | 001 `audit/reference_banks/<G>_<v>.npz` | 历史同视频 FIT | `BANK_ADMISSION.json` 记录 ancestry | 3D 地标 `X` + 观测清单 | **继承（构建过程未留日志 → UNVERIFIED）** |
| A4 | RGB PnP | `native/rgb.py:20-32 pnp()` | RGB + bank | SIFT 6000、ratio .72、RANSAC 3px/1000 | `C`、inliers | 重算 |
| A5 | Ring 5DOF | `native/camera.py:61-103 recover()` + `_kernels.solve` | labels + PnP 种子 | `RF_CONFIG` 2 种子/35 迭代 | 全部候选 `candidates` | 重算 |
| A6 | RGB yaw | `recover()` :84-94 | 每个候选 × 法向翻转 | 72 点栅格 + 有界细化（±5°） | `source='originalRF5DoF_RGB_yaw'` | 重算 |
| A7 | 来源过滤 | 001 `rf_only.py:43-50` | 候选集合 | 仅取 `originalRF5DoF_RGB_yaw`；`min(FIT_objective)` | 每视角最终 `CAMERA_RESULT.json` | 重算 |
| A8 | 3 px 门限 | `pipeline.py: camera_gate` | 相机 + Ring MAE + bank 状态 | `Ring_boundary_MAE_limit_px = 3.0` | `ADMISSION.json` | 重算 |
| A9 | HERO | 001 `hero_stage.py` | 4 帧（偏移 2/4/6）FIT + 相机 | 官方 MVSAnywhere，352×640，axial-Z mm | `HERO_native.npz` / `Raw_open_mesh.ply` | 重算 |
| A10 | Body 初始化 | `EXACT_013_INPUT_MESH_V_F_SOLID_CAP` | 每病例固定资产 | 642 V / 1280 F（G01） | `INITIAL.npz` | 继承（冻结资产） |
| A11 | Body 优化 | 001 `body_stage.py`（Graph 32 节点 + Smooth ARAP + Sweep） | INITIAL + HERO + 2D 对应 | 36 外循环、`depth_lambda .01`、`sigma .5mm`、`huber 1.0` | `FINAL.npz`、`UPDATES.json`、`STEP_*.json` | 重算 |
| A12 | 几何门控 | 同 A8 + 碰撞/自交/基底 | 候选 Mesh | 未放宽 | accept/reject | 重算 |
| A13 | 独立评价 | `evaluate_stage.py` | 冻结预测 + GT | 尺度固定 SE(3)，96 起点 | `BODY_METRICS` | 重算（GT 后置） |

### 2.2 yaw 为什么必须由 RGB 解

Ring 是旋转对称体（R=5.6 mm，r=0.6 mm）。绕环平面法向旋转任意角度，环的**自身轮廓投影几乎不变**。因此：

- 5 DOF 只能定出环的位置、深度与法向；
- 第 6 个自由度（绕法向的 yaw）必须靠**环外**的信息——即 RGB 背景特征与参考库地标；
- A 线的做法：对每个 5DOF 候选 × 法向翻转，在 ±180° 上做 72 点栅格搜索 + 有界细化，用 `score()` 选优；`score = Ring Huber + 0.2·PnP 重投影 Huber + 100·max(0.1−z)`。

**这解释了为什么 Ring 门限（3 px）在原理上无法发现 yaw 错误**：yaw 错误对 Ring 残差几乎零贡献。

**一个必须写明的口径问题（001 的实测）：** 001 首次混合策略在 105 个视角上的赢家分布为 `REAL_RGB_PNP_LM:54 / RING_ONLY_YAW_UNRESOLVED:49 / originalRF5DoF_RGB_yaw:2`，全部 `admitted_frames=0`。原因是 `score()` 里含 `0.2×PnP 内点重投影`项（`camera.py:56-58`），而 PnP 候选正是对这同一批内点拟合出来的——**目标函数天然偏向 PnP**。因此：

- "PnP 胜出 54 次"说明的是**目标函数结构**，不是"Ring-First 精度更差"；
- `RF_ONLY` 的合规性来自**先按 `candidate_source` 过滤、再在同一目标函数下比较**（`rf_only.py:43,48`），不是来自更优拟合；
- 读 001/002 的任何 Ring-First 结论时，都必须先确认"赢家是谁"以及"过滤发生在比较之前还是之后"。

### 2.3 A 线中"成熟"与"未验证"的分界

| 项目 | 状态 | 依据 |
|---|---|---|
| Ring 5DOF 内核与 yaw 消歧 | **成熟** | 自 2026-10-15 起未变，多任务复用；本轮 AST 比对确认 |
| RGB PnP（SIFT+RANSAC+LM） | **成熟** | 同上 |
| 3 px 门限 | **成熟（但只约束 Ring）** | 001/002 一致 |
| 004 参考库的**构建过程** | **UNVERIFIED** | 只有 `BANK_ADMISSION.json` 的 ancestry 记录（8 视角），无构建脚本与中间产物 |
| 004 相机的**绝对正确性** | **UNVERIFIED** | 从未有独立位姿 GT；`calibrated_pose_truth=false` 写死在 `recover()` 返回里 |
| Body 优化器 | **成熟** | Graph/SARAP/Sweep 在 002 中被 §2 的 G01 结果验证过（B2 使 FIT IoU 0.833→0.887） |

---

## 3. B 线：005 的成熟实现（V6）

### 3.1 阶段表

| # | 阶段 | 真实函数（file:line） | 输入 | 关键参数 | 输出 |
|---|---|---|---|---|---|
| B1 | 输入台账 | `scripts/prepare_ring.py:14` 读 `inputs/ledger005_preseg.json` | 22 关键帧（16 历史 + 6 新增） | `config.json: reference_raw=459, held=516, max_new_frames=6` | 台账 |
| B2 | 分割（新帧） | `prepare_ring.py:17-19` `INITSegmentation.predict()` | 新帧 RGB | DXY 冻结模型 | 新 Mask |
| B3 | Ring 观测/补洞/连通域 | `prepare_ring.py:2-9` 导入 `dxy_mid._engine.ring_holes.run as holes`、`components.FrameInput`、`v81_components.existing_ring_check`、`selection.evaluate as quality` | RGB + Mask | DXY 参数 | `ring_train/ring_heldout/visible_region/background_region/ring_mask` |
| B4 | Ring 候选 | `prepare_ring.py:23-33`：`image_seeds` + 中心线几何追加种子 + `branch_seed_policy.diverse_four` | 观测 | **`seed_retain=4, max_nfev=100`** | `ring_candidates005.json`，含每候选 `heldout=stats(ring_residual(po,ob,'held'))` |
| **B4b** | **yaw / spin 消歧（B 线的机制与 A 线不同）** | `local_ring_sfm.py:20-50 initialize()`：不靠 PnP，而是从已解帧出发，用**背景 SIFT 极线误差**（`background_registration.epi`）在 72 网格 + ±π/36 精修选 spin，并对每候选做三角化正性检查；最后 `least_squares` 全局 alpha 精修（`global_alpha_nfev=80`） | 已初始化的相机 + 背景轨道 | `yaw_grid=72`、`temporal_rotation_prior_deg=30`、正性惩罚 `+5·max(0,.95−pos)` | 初始相机 |
| B5 | RGB 跟踪 | `scripts/track005.py:4-44` | 22 帧 RGB | SIFT 6000、ratio .72、`pair_offsets [1,2,4]`、`hold=idx%5` | `tracks005.npz`（含 `held`）、`pairs005.npz` |
| B6 | 局部 SfM | `local_ring_sfm.py:20-38 initialize()`、`triangulate_training()` | ring candidates + tracks | `pose_initializations=2`、`yaw_grid=72` | 初始相机 |
| B7 | BA | `local_ring_sfm.py:63-89 BA()` | 初始相机 + 训练轨道 + Ring 观测 | `BA_max_nfev=60`、soft_l1、huber 1.0、时间先验 30°/10mm | `local005_camera_{v}.npz` |
| B8 | **每帧验证** | `validate_select.py:5-18` | 相机 + `tr['held']` | `validation_min_test=8, MAE≤3, p95≤6, positive≥.95, spread≤2` | 每帧 `VALIDATED/MODEL_PREDICTED`、**旋转/中心离散** |
| B9 | **支持视角筛选** | `select_supported_views.py:2` | 验证结果 | 仅 `VALIDATED` | 送入 MVS 的视角子集 |
| B10 | MVS/HERO | `run_mvs005.py` / `run_mvs005_supported.py` | 支持视角 + 相机 | 官方权重 | 005 深度/点云 |
| B11 | 封装 | `package_surfaces.py` | MVS 结果 | — | 开放 Polyp/Ring/Background PLY |
| B12 | 跨视频对齐 | `align_local_scenes_disjoint.py` | 004/005 轨迹 | Ring 轴离散搜索，无 ICP/尺度 | **`accepted=false`**（§4） |

### 3.2 B 线明确留下的负结论（必须继承进任何引用）

来自 `ring_first_v6_local_reconstruction/README.md` 与 `DECISION.md`：

- 005 相机 **22/22 数值候选，15/22 通过相对几何筛查**；正式 `local005_VALIDATED_only.npz` 含 7 个 NaN；
- **跨 004 对齐失败**（`cross_video_VALIDATED_transform.npz` 全 NaN），未做正式融合；
- 连续表面只有 1 个 Polyp 稀疏支持点，两参考约 0.65 mm 深度差，存在环遮挡排序矛盾；
- 真实 GT 精度未知。

---

## 4. 004 与 005 的真实关系

| 问 | 结论 | 证据 |
|---|---|---|
| 是否共享同一世界坐标系？ | **否，且是设计上不共享** | `v6/scripts/export_and_reproject.py:16` 直接写入元数据 `coordinates='local005 Ring frame, unknown rotation relative to004'`；005 世界由 `local_ring_sfm.py:92`（`pp[ref]=canonical_reference(c2r)`）+ `v6_common.py:27-31`（`positive_gauge` + 绕 z 旋到参考相机 xy 方位 0）定义；004 世界来自 `previous.prev.cam('real','0')`（`surface_fusion_v2` → `inputs/real_camera_0.npz`） |
| "都在原点"意味着什么 | **只是规范选择，不是测量结论** | 两条链各自把自己的环放到原点；环心/环轴重合是**假设** |
| 是否真正做过跨视频配准？ | 做过，**未通过**，且**代码结构上无法表达通过** | `metrics/alignment005_to004_disjoint.json`：`accepted=false`、`method="whole-scene Ring-axis rotation plus normal-sign branch, no ICP or scale correction"`、`alpha_deg=-88.90`、held 005→004 MAE **9.165 px**、held 004→005（仅 5 观测 / 3 独立点）MAE **41.912 px**；`export_and_reproject.py:37` 甚至有 `assert not align['accepted']` |
| 哪些阶段独立？ | 全部独立 | 002 `TASK.yaml: forbidden: [cross_video_BA]`；001 `hero_stage.py:21-26` 只取同视频 4 帧 |
| 是否共享同一个 Body？ | **只共享冻结初值资产与 GT，不共享优化结果** | 每 (case,video) 独立 `body/B1,B2/FINAL.npz`；001 `body_stage.py:17` 只跑 `video='004'`；002 `TASK.yaml: cross_video_body_training=false` |
| HERO 是否跨视频融合？ | **否** | 001 `HERO_TARGETS_FROZEN.json` 32 个目标全部 `video='004'`；002 支持帧全部同视频 |
| 是否退化为两个单视频优化？ | **是，且这是当前唯一有证据支持的形态** | 上述全部 |

**004 参考库的真实血统（与 005 不同源）：** 001 的 `audit/reference_banks/G01_004.npz`（153 个地标）来自 **019/021** 链路的 `features019.landmarks`（≥3 视图轨迹、SIFT 互检 ratio .72、MAGSAC F 1.5px、soft_l1 三角化），经 MAX-COVERAGE 归档打包、由 001 `ARCHIVE_EXTRACTION.json` 解包。**与 v5/v6 无关。**

**005 被 001 拒绝的直接代码位置：** `021/geometric_pose_optimization/code/prepare.py:36-37` 对 `video=='005'` 施加 `lm['X'] = lm['X'] @ H.R.T + H.t`（`H` 来自 `results/B3.json['T']`），即"继承的跨视频变换"；001 `rf_only.py:30` 因此硬编码追加 `INHERITED_CROSS_VIDEO_MAP_GAUGE_UNCERTIFIED` 并 FAIL。002 的 `banks.py:39-45` 用**逆 H 回到原生 005 坐标**（`cross_video_coupling_removed:true`，980/980 点保留，往返 2.84e-14 mm）——这是对 001 拒绝理由的正确修复方向。

**004/005 的关系在 V6 时代就已经被判失败**；001 在 `rf_only.py:30` 又把 G01/005 的历史库显式标为 `INHERITED_CROSS_VIDEO_MAP_GAUGE_UNCERTIFIED` 并 FAIL。002 改用同视频重建，方向正确，但**不能因此宣称"多视频共享主体"**。

**三个必须分开陈述的验收目标：**

| 目标 | 现状 |
|---|---|
| 单视频优化成功 | 9/10 实例有 B1/B2 输出 |
| 跨视频几何一致 | **从未成立**（v6 拒绝，002 禁止） |
| 多视频共享主体更新 | **未实现**，也没有被证据支持 |

---

## 5. Ring-First 版本谱系

| 版本 | 日期 | 职责（据 README/HUMAN_SUMMARY） | 与 G01 的关系 |
|---|---|---|---|
| `ring_pose_contact_v1` | 2026-10-15 | **Ring 五自由度内核首次出现**（`decode/image_seeds/solve`） | 所有后续的祖先 |
| `ring_first_v1` | 2026-10-15 | 早期 ring 重建/浮点 K 实验 | 未进入 G01 |
| `v2_real_ba` / `v3_static_ba` | 2026-10-15 | 真实/静态 BA 试验 | BA 概念来源 |
| `v4_synthetic_audit` | 2026-10-16 | 合成审计 | 未进入 G01 |
| `v5_geometry_crossvideo` | 2026-10-19 | 跨视频几何；`ring_candidates_diverse`、`branch_seed_policy` | **B 线播种策略来源** |
| `v5_real_validation` | 2026-10-16 | 真实验证 | B 线前身 |
| **`v6_local_reconstruction`** | **2026-10-19** | **005 相机/深度/开放 Mesh；`prepare_ring` + `track005` + `local_ring_sfm` + `validate_select` + `select_supported_views` + MVS** | **B 线主体** |
| `v7_multisource_gasf` | 2026-10-19 | 多源 GASF | 未进入 G01 |
| `v8_registration_narrow_baseline` | 2026-10-20 | MASt3R 窄基线注册 | 未进入 G01 |
| `v9_ring_guided_recovery` | 2026-10-20 | Ring 引导恢复 | 未进入 G01 |
| `v10_matching_observability` | 2026-10-20 | 匹配可观测性 48 组 | 诊断来源 |
| `v11a_native_pointmaps` | 2026-10-20 | 原生点图 | 未进入 G01 |
| `v12_pose_matching_audit` | 2026-10-20 | 相机/对应独立审计 | 诊断来源 |
| `v13_multisource` | 2026-10-21 | 多源共同坐标验收 | `LOCAL_SUPPORT_ONLY / G3_FAILED` |
| `v14a_forensic_audit` | 2026-10-21 | 取证审计（阶段 A） | 诊断来源 |
| `v15_rc_lba` | 2026-10-21 | 受限局部 BA 与跨视频验证 | 未进入当前链 |

**A 线（native/E4）不在这张表里**——它来自 E4 系列的 `TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`、`TASK-E4-RING-ANCHORED-JOINT-BA-021` 等任务，参数与 V6 不同（2/35 vs 4/100 vs 4/45）。这条线在 2026-11-19 由 001 的 `native/` 模块固化。

---

## 6. 002 在两条线之间的实际接线

```
G01/004 ──► 001 冻结库（A 线，FROZEN_REFERENCE）──► cameras.py:recover()（A 线）──► HERO ──► Body
G01/005 ──► V6 代码建库（B 线，MATURE_REV1）──► cameras.py:recover()（A 线！）──► HERO ──► Body
G02/004 ──► features019 三角化（第三条路径）──► recover()（A 线）──► ...
```

`cameras.py:24` 对**所有**实例统一调用 `recover()`。也就是说：

- 004：A 线库 + A 线相机 —— **历史自洽**；
- 005：B 线库 + A 线相机 —— **混合，历史未验证**；
- G02/004：第三条库 + A 线相机 —— **混合，历史未验证**。

这是 002 相对于任何单一历史链最本质的偏离，也是 G03/005 出现问题（§2.3 of DIFFERENCE_MATRIX）的结构性背景。

---

## 7. 给 RA 的判据清单（回答 Q1 必须明确的点）

1. **哪条线是 G01 的权威线？** A 线（per-view recover）还是 B 线（BA 出相机）？这决定 `cameras.py` 是 `ADAPTER_ONLY` 还是 `ALGORITHM_CHANGED`。
2. **004 的参考库是怎么建的？** 001 只留下 `BANK_ADMISSION.json` 与 npz，没有构建脚本。若无法追溯，004 的"成熟"只能算"冻结可用"，不能算"可复现"。
3. **005 是否必须走 B 线全程？** 若必须，则 002 的最终相机阶段需要改回 BA 输出，并补上 `validate_select` 与支持视角筛选。
4. **是否接受"004/005 永久不共享坐标"？** 若不接受，需要新的跨源对应研究（V6 已失败一次，V15 也未成功）。

---

## 8. UNVERIFIED 清单

| 项 | 原因 |
|---|---|
| 004 参考库的构建脚本与中间产物 | 001 未保留；`audit/reference_banks/` 只有成品 |
| 004 相机的绝对几何正确性 | 无独立位姿 GT；V6 的跨视频对齐也未通过 |
| A 线 2/35 与 B 线 4/100 的实际差异幅度 | 需在相同输入上重解一次；本轮不运行求解器 |
| `torus_residual` 在 `native/camera.py` 的绑定与 V6 是否完全等价 | V6 由 `v6_common` 的 `ring_residual` 提供，绑定路径不同；函数体本轮未逐行比对 |
| V6 `prepare_ring` 的 DXY `holes/components` 实际生效程度 | 需 DXY 侧确认（见 `DXY_READONLY_METHOD_REVIEW.md`） |
