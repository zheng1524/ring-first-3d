# UNIFIED_CAMERA_ARCHITECTURE

**Task:** TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005
**Status:** 设计冻结（实施前）· 全部 10 段视频共用同一算法、同一参数、同一门限、同一选择规则。

---

## 0. 要解决的既有缺陷（来自 003/004 审计）

| 缺陷 | 证据 | 本架构如何消除 |
|---|---|---|
| 存在两套相机 | V6 BA 相机 vs 002 逐视角 `recover()` | **最终相机 = 多视角解**，逐视角 Ring-First 只作为**候选种子**，不再覆盖 |
| 版本选择无质量比较 | `primary=min(available)`；G03 选到 77.7 px 的版本，v1 只有 5.5 px | **训练侧统一评分**选版本（§6），不用户序号 |
| 最终相机无验证 | 最终相机 held 重投影 G03 达 159 px，无任何告警 | 逐视角 held + Ring + 正深度**评价**；评价结果只决定状态，不反选 |
| Ring 观测无统一规则 | 孤立分量污染 G05；最大连通域又伤 G02 | 统一分量规则（§4），10 段共用 |
| 状态语义混用 | 文件存在 / 门禁通过 / 几何有效混为一谈 | 四层状态严格分离（§8） |

---

## 1. 总体数据流（唯一路径）

```
冻结输入（每实例 8 个 FIT 视角：RGB / Mask / K / 视角身份）
        │
        ├─[A] Ring 观测统一化  (§4)  ──►  q_train / p_train / b_train / 分量诊断
        │
        ├─[B] Ring 5DOF 候选（逐视角，无 RGB）  ── native camera.recover(rgb_geometry=None)
        │       └─ 输出 ring_alternatives（多法向分支）
        │
        ├─[C] RGB 多视角跟踪  ── V6 track005（SIFT 6000 / ratio .72 / mutual / 同类约束）
        │       └─ 输出 tracks(xy, category, held=每5取1)、pairs
        │
        ├─[D] 多视角初始化  ── V6 local_ring_sfm.initialize(version=0,1)
        │       └─ 背景极线 + Ring 残差 + 正性惩罚；两版本仅初始分支不同
        │
        ├─[E] 联合 BA  ── V6 local_ring_sfm.BA
        │       └─ 变量：非参考帧 6DoF + 3D 点；残差：特征重投影 + Ring 残差 + 时间先验 + 正性
        │       └─ Ring CAD 与 RGB 在一次优化里共同决定相机（不存在"先 RGB 后覆盖"）
        │
        ├─[F] 版本选择（训练侧评分，§6）  ──► 唯一正式版本
        │
        ├─[G] 逐视角 Ring 3 px 门禁  ──► CAMERA_ADMISSION_PASS / FAIL
        │
        └─[H] 独立评价（held 轨迹）  ──► CAMERA_GEOMETRY_VALIDATED（只评价，不反选）
```

**关键约束：** 图中不存在"逐视角 `recover()` 覆盖 BA 结果"的边。`recover()` 只在 [B] 提供 Ring 候选与 4 项法向分支，供 [D] 初始化使用。

---

## 2. 唯一求解器与唯一参数

| 模块 | 来源（复用，不重写） | 参数 |
|---|---|---|
| Ring 观测 | `ring_first_3d.mainline.native.camera.observe`（+ §4 的统一分量规则） | 128 点、5×5 息肉邻接剔除 |
| Ring 5DOF | `native/_kernels.decode/image_seeds/solve`（源 `ring_pose_contact_v1/scripts/recover.py`） | `RF_CONFIG`: seed_retain=2, max_nfev=35, huber=1.0, success_max=3px |
| RGB 跟踪 | V6 `track005.py` | SIFT 6000 / contrast .01 / ratio .72 / pair_offsets [1,2,4] / held = idx%5 |
| 初始化 | V6 `local_ring_sfm.initialize` | `pose_initializations=2`, `yaw_grid=72`, `global_alpha_nfev=80` |
| BA | V6 `local_ring_sfm.BA` | `BA_max_nfev=60`, soft_l1 f_scale=1, huber 1px, 训练点上限 500, 时间先验 30°/10mm |
| 参考地图 | V6/v5 `features019.landmarks` | 仅用于记录与下游 Body 阶段，本轮不参与最终相机 |
| 几何工具 | `native/geometry.project`, `native/camera.torus_contours` | 只读 |

**所有 10 段视频使用同一份 `config.json`**（`frozen_calibration/config.json`，与 V6 逐字节相同）。

---

## 3. 坐标规范（Gauge）的定义与记录

1. 参考帧 = **8 个 FIT 视角中 raw_frame 最接近 459 的那一帧**（V6 `reference_raw=459` 的统一推广；无 459 时取原始帧号中位数最近者）。规则对 10 段视频相同。
2. 规范：参考帧相机置于 `positive_gauge`（z>0）并把 xy 方位旋到 0（V6 `canonical_reference`）。**不得引入任何 Body 信息。**
3. 全局 180° 翻转是规范选择，不是错误：两个 BA 版本若只差全局刚体变换，则视为同一解的两种表示，只保留一个；若**部分视角**不一致，则为真正的相机错误（§7）。
4. 记录：`CAMERA_PROVENANCE.csv` 写入 `gauge_definition`、`reference_view`、`gauge_version`。

---

## 4. Ring 观测统一规则（10 段共用）

1. 保留原始 Mask，**永不修改**；所有处理在副本上。
2. 识别全部 Ring 连通域；记录面积、质心、边界点数、与息肉膨胀区的关系。
3. 统一默认策略 = **M0**（原始观测），因为跨病例消融显示 M1 并非普遍改善（004 审计：2 改善 / 2 变差）。
4. 分量只做**诊断与降权建议**，不做删除；若某分量满足"面积占比 <1% 且不与息肉相邻 且 其边界到 CAD 投影的 MAE >5× 主分量"，则标 `SUSPECT_COMPONENT` 并记录，供人工决定。
5. 小孔填充（DXY 规则，独立实现）作为**可选**步骤，默认关闭；开启时必须断言息肉标签逐位不变。
6. 正式消融 M0/M1/M2 在同一代码路径下由参数开关控制，最终只能选定一个默认值。

---

## 5. 最终相机的定义

**最终相机 = 版本选择后的 BA 相机**，逐视角经 3 px Ring 门禁后写入 `CAMERA_RESULT`。

- 不再对每个视角单独调用 `recover()` 精修。
- 若某视角 Ring MAE >3 px，该视角 `ADMISSION=FAIL`，但**不终止整个实例**；其余视角继续输出。
- 逐视角 PnP 仅用于（a）为初始化提供种子、（b）诊断记录，**不得**作为最终相机。

---

## 6. 版本选择（训练侧统一评分）

对每个 BA 版本 `v` 计算（全部来自训练侧：FIT 视角 + 训练轨迹 + Ring 观测）：

```
score(v) = w1 * ring_MAE_train(v)                 # Ring 拟合
         + w2 * feat_reproj_MAE_train(v)          # RGB 训练轨迹重投影
         + w3 * (1 - positive_depth_fraction(v))  # 正深度
         + w4 * (0 if BA.success else penalty)     # 收敛（只作一项，不单独决定）
```

固定权重 `w = (1.0, 0.1, 10.0, 0.5)`，**不按病例调整**。

- `held` 轨迹**不参与** score（只用于 §8 的独立评价）。
- 若两版本分数差 <5%，判为 `AMBIGUOUS_VERSION`，按"参考帧 Ring MAE 更低者"决胜；仍相同则取 version 0 并记录。
- 目标函数形式、权重与决胜规则写入 `RUN_CONFIG.json`，10 段视频一致。

---

## 7. 对称性处理（全局规范 vs 真正不一致）

| 现象 | 判定 | 处理 |
|---|---|---|
| 两版本绝对旋转差 ≈180°，且**每个视角的相对旋转相同** | 全局规范差异（无害） | 取分数更高者；记录 `GAUGE_FLIP_GLOBAL` |
| 只有**部分视角**与其余视角不自洽（held 重投影高） | 真正不一致 | 该视角 `INVALID` 或 `USABLE_WITH_CAUTION`，实例不终止 |
| 两版本差异 <30° 且 held 误差接近 | 版本接近 | 取分数更高者 |

判定量：`per_view_held_MAE`（评价侧）、`relative_rotation_spread`（诊断）。**两者都不用于选择。**

---

## 8. 四层状态（严格分离，不得混用）

| 字段 | 含义 | 判据 |
|---|---|---|
| `CAMERA_FILE_EXISTS` | 有无相机文件 | 文件存在 |
| `CAMERA_ADMISSION_PASS` | Ring 3 px 门禁 | `ring_MAE <= 3.0` |
| `CAMERA_GEOMETRY_VALIDATED` | 独立评价通过 | `held_N >= 8` 且 `held_MAE <= 3` 且 `p95 <= 6` 且 `positive >= 0.95` |
| `CAMERA_USABLE_FOR_DOWNSTREAM` | 可进入下一阶段 | `ADMISSION_PASS` 且（`GEOMETRY_VALIDATED` 或 `USABLE_WITH_CAUTION`） |

视角级状态：`VALIDATED` / `USABLE_WITH_CAUTION` / `INSUFFICIENT_EVIDENCE` / `INVALID` / `NOT_RECOVERED`。

- `INSUFFICIENT_EVIDENCE`（held 不足）**不得**写成 `INVALID`。
- 实例级：不设未经验证的最小视角数；报告实际覆盖与缺失方向。

---

## 9. 禁止事项（写进运行时代码断言）

1. 不读取任何 `body/` 路径；不读取 GT；不读取 HOLDOUT 图像参与任何选择。
2. 不按 `group` 分支选择算法/参数/门限（代码中禁止 `if group ==`）。
3. 不覆盖 002/001 的冻结相机与结果；本任务只写自己的 `runs/`。
4. 不运行 HERO / Body。
5. 不 import DXY。

---

## 10. 产物与冻结

- `runs/<GROUP>/<VIDEO>/`：`ring_candidates.json`、`tracks005.npz`、`BA_{v}.npz`、`VERSION_SCORES.json`、`CAMERA_RESULT.json`（最终相机，冻结）、`VALIDATION.json`。
- `CAMERA_PROVENANCE.csv`：每视角的 Ring 来源、RGB 来源、初始化版本、BA 版本、门禁、评价。
- `CAMERA_QUALITY_MATRIX.csv`、`VIEW_COVERAGE_MATRIX.csv`、`FAILURE_REGISTRY.csv`。
- 最终相机冻结后打 `FINAL_CAMERAS_FROZEN.json`（含 SHA256），**只有人工批准后才进入 HERO/Body**。

---

## 11. 与历史实现的关系

- 本架构**不新增**科学算法：Ring 内核、跟踪、初始化、BA 全部复用既有冻结源码（逐字节复制到 `code/frozen/` 并 SHA 记录）。
- 新增的只是**装配层**：统一观察规则、统一版本评分、统一状态与验收。
- 与 002 的差异只有两处：(a) 最终相机取 BA 而非逐视角 `recover()`；(b) 版本选择由训练侧评分决定。两处都在本文件与 `RUN_CONFIG.json` 中预先声明。
