# TASK-E4-HISTORICAL-CROSSVIDEO-REPRODUCTION-019 — FINAL_REPORT

```
HISTORICAL_019_REPLAY:        PARTIAL
HISTORICAL_020_REPLAY:        PARTIAL
HISTORICAL_CODE_AUDIT:        COMPLETE
W0_ADAPTER:                   VALID
G03_3D_LANDMARK_IDENTITY:     INSUFFICIENT
G03_CROSS_VIDEO_YAW:          IDENTIFIABLE (low precision)
G03_CROSS_VIDEO_SHARED_SE3:   PARTIAL
G03_CAMERA_NETWORK:           BLOCKED
CODE_AUDIT_PACKAGE:           COMPLETE
BODY_CROSS_VIDEO_ADMISSION:   NO
```

## 0. 本轮最重要的事实

1. **历史 019/020 源码存在、可读、已审计**（不在 `5636aae` 这个 commit —— 该 ref 在本仓库不存在，38 个提交里都没有；源码在
   `/home/liu/polyp_research/ring-first-3d/experiments/` 与 `assets/retained_sources/`）。
2. **`020/landmarks/CROSS_004.npz` 是悬空软链接**，指向已删除的
   `/home/liu/ring_first_3d_e4_sdf_localization/...`。这是历史资产不可复现的直接原因。
3. 用 019 的同名文件替代后，**18 对共同地标的 3D 一致性重放得到 2/18 在 0.75 mm 内（中位 3.01 mm），
   而历史报告是 5/18** → 数值不一致，标 `MISMATCH`。

## 1. Stage H：历史源码审计（`HISTORICAL_SOURCE_AUDIT.md`）

- `019` 24 个模块、`020` 22 个模块，全部存在（含 `REPRODUCE.md`、`FAILURE_LEDGER.md`、metrics/results）。
- **`features019.py` 在 019 / 020 / 021 三处 SHA256 完全相同**（`50cd25fd8df87364…`）——
  任务书担心的"同名不同内容"没有发生。
- 参数与任务书描述一致（源码核对）：
  SIFT `nfeatures=6000, contrastThreshold=.01`；ratio 0.72；USAC_MAGSAC 1.5 / 0.999 / 10000；
  三视角轨迹 + `least_squares(soft_l1, f_scale=1.5)`；质量门 `positive depth, max reproj<2px, parallax>0.5°`；
  Ring 曲线用 `dist/3` 的 Huber；Mid 权重 1.0/0.25/0 由覆盖类别决定；
  `H = exp_se3(q*scale) @ seed`；Adam `lr=.01`、80 次、`LOCAL_SE3_BOUND` 1.2 mm / 10°。

## 2. Stage H：历史复现（`HISTORICAL_REPRODUCTION_REPORT.md`）

| 项 | 结果 |
|---|---|
| R0/R3 的 `T` 矩阵 | 存在、`det=1`、正交误差 0 |
| 方向检验 | 对 X004 施加 **H** → 中位 **45.42 mm**；施加 **H⁻¹** → **3.01 mm** ⇒ **H = H_004←005 得到数值确认** |
| 18 对 3D 一致性 | **2/18 < 0.75 mm，3/18 < 1 mm，中位 3.01 mm**（历史：5/18）→ `MISMATCH` |
| R0 vs R3 | 2.92 mm vs 3.01 mm（R3 略差 0.09 mm），与历史"边际改善"一致 |
| HERO / HOLDOUT IoU / Ring MAE | **NOT_REPRODUCED**：需要 020 的 HERO+Body 评价链，本轮未执行 |

**`HISTORICAL_020_REPLAY = PARTIAL`**：3D 一致性可重放但不等于历史数字；HERO 指标未复现。

## 3. Stage A：W0 适配器（`W0_ADAPTER_REPORT.md`）

`adapters/w0_to_legacy020.py` 只做一件事：把 `camera_mainline/G03/video00{4,5}/camera_result.npz`
的 `c2w/K/ids/raw_frames` 与 `admission.csv` 按 **view id** 关联（不靠数组顺序），产出 019/020 需要的
`id/K/T/cache/role`。`adapters/coordinate_adapter.py` 显式给出 `H_005←004 = H_004←005⁻¹`，
并写 `COORDINATE_CONVENTION_AUDIT.json`。
7 个坐标测试全部通过（SE3 逆、c2w 复合、点变换、距离保持、Ring 轴半径保持、法向 parity、非法矩阵拒绝）。

## 4. Stage G：G03 迁移（`G03_CROSSVIDEO_REPORT.md`）

| 候选 | θ | 正向中位 | 反向中位 | 内点3 |
|---|---:|---:|---:|---:|
| B0（Ring-only，θ=0） | 0° | **57.6 px** | 55.1 px | 7.5% |
| B1（018 候选） | 47.24° | **11.7 px** | 11.0 px | 12.4% |
| B2（本轮搜索） | 47.67° | 11.2 px | 10.2 px | 12.9% |

- **Ring 单独不能定 yaw**（θ=0 比 θ=47° 差 5 倍），RGB 对应才能定 —— 与 Ring 的旋转对称性一致。
- **留出验证**：只用一半 005 视角估计 → θ̂=**46.89°**；在未见过的 005 视角上正向中位 **14.45 px**、反向 **13.43 px**。
  yaw 泛化了（差 0.35°），但精度只有 ~14 px。
- **A 组（004 QUARANTINE）**：θ=0→120 px、47°→96 px、搜索 32°→73 px，内点 4–7% ⇒ **不是 yaw 分支问题**。
- 负对照：打乱对应 → `DEGENERATE`；半数据 → `DEGENERATE`。

**`G03_CROSS_VIDEO_SHARED_SE3 = PARTIAL`**：只做了 1-DoF yaw（且有留出验证）。
6-DoF SE(3) **未执行**——因为没有 Type III（跨视频 3D 同名身份），
在 2D 对极残差 11–14 px 的条件下放开 6 自由度只会过拟合，故拒绝执行并记录原因。

## 5. 回答

- **Q1** 历史能否复现？**部分**。失败原因具体是：① `020/landmarks/CROSS_004.npz` 悬空软链接（缺失输入）；
  ② HERO/Body 评价链未在本轮执行（环境依赖）；③ 3D 一致性数字 2/18 ≠ 5/18（数据替代导致）。
- **Q2 哪些模块有效？** Ring CAD 曲线与可见弧：有效但**对 yaw 无信息**；SIFT 地标：可建立；
  跨视频身份：**不足**（无 Type III）；双向投影：可用但精度 11–14 px；2D-only 对极：可用；
  共享 SE(3)：**未证实**。
- **Q3 哪些执行错误值得修复？** E1 悬空软链接（必须修数据迁移）；E2 方向约定（必须显式取逆）。
  其余见 `EXECUTION_ERROR_LEDGER.csv`。
- **Q4 G03 能否用历史多视角地标算法？** 数量上**不能完成**：本轮只有 Type I（2D–2D，B 组 38 对 / A 组 50 对），
  Type II/III 为 0（005 侧同一特征没有跨视图描述子身份）。→ `G03_3D_LANDMARK_IDENTITY = INSUFFICIENT`。
- **Q5 G03 是否有可靠 yaw？** **有条件的可辨识**：47.2°（留出 46.89°，差 0.35°），但精度 11–14 px。
- **Q6 共享 SE(3) 能否改善跨视频 RGB？** 1-DoF yaw 把 57.6 → 11.7 px；6-DoF 未执行（无 3D 身份）。
- **Q7 是否引入 Ring 冲突？** 纯 yaw 绕 z 轴，Ring 圆心保持不动、法向不变（`test_ring_axis_rotation_preserves_radius`、`test_normal_parity`）。
- **Q8 3D 背景点是否更一致？** 历史数据重放：R0 2.92 mm / R3 3.01 mm，**没有变好**。
- **Q9 大残差来源**：`FEATURE_IDENTITY_ERROR`（无跨视频 3D 身份）+ `MATCHING_ERROR`（重复纹理，11–14 px）
  + `SINGLE_VIDEO_POSE_ERROR`（004 A 段）+ `INSUFFICIENT_EVIDENCE`；`IMPLEMENTATION_ERROR` 已由受控测试排除。
- **Q10 是否形成可用共同相机网络？** **NO**（仅 1-DoF 候选 + 留出残差 14 px，未达独立几何证据要求）。

## 6. 交付

`adapters/{w0_to_legacy020,coordinate_adapter}.py`、`code/{replay_historical,run_g03_registration,reproduce_offline,geometry_019,yaw_solver_019}.py`、
`tests/test_coordinate_conventions.py`（7/7）、`metrics/*.csv|json`、`SOURCE_REUSE_MATRIX.csv`、`EXECUTION_ERROR_LEDGER.csv`、
`artifacts/TASK-E4-HISTORICAL-CROSSVIDEO-REPRODUCTION-019_CODE_AUDIT.zip`。
