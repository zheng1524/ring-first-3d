# PIPELINE_DIFFERENCE_MATRIX

**Task:** TASK-E4-G01-PIPELINE-AUDIT-003
**Status:** `AWAITING_RA_REVIEW`
**审计基线（只读）：** `/home/liu/ring_first_3d_workspace` @ `ff24295`（分支 `exp/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002`）
**被审对象：** `experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002`（下称 **002**）
**对照对象：** `ring_first_v6_local_reconstruction`（下称 **V6**，2026-10-19）、`TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001`（下称 **001**，2026-11-19）
**方法：** 逐函数源码对照 + 数值复算 + 冻结产物统计。**未修改任何源码，未重跑任何实验，未写入 DXY。**

图例：`IDENTICAL` / `ADAPTER_ONLY` / `ALGORITHM_CHANGED` / `STAGE_MISSING` / `UNVERIFIED` / `QUALITY_REGRESSION`

---

## 0. 一句话结论

002 的**数值内核**（Ring 五自由度 `decode/image_seeds/solve`、RGB yaw、PnP、BA、Body 优化器、3 px 门限）与历史实现**逐字节同源**。真正的差异不在"算法被改了"，而在**上游接线**：

0. **"G01 成熟实现"不是一条链，而是两条**（详见 §2.6）：004 走 E4/native 线（`observe` + `recover`，2 种子/35 迭代，无 DXY 预处理），005 走 V6 线（DXY 分割/补洞/连通域 + 4 种子/100 迭代 + BA 出相机）。002 把两条线拼成"V6 的库 + native 的相机"，这个组合历史上从未被验证过。

在此之上还有三个具体缺陷：

1. 每帧独立验证（`validate_select`）整段缺失 —— 而它正是 G01/V6 用来发现相机不可靠的机制；
2. 参考库构建出现**三条互不相同的数据来源**，不同实例的相机不再可比；
3. 初始化版本仍按 `min(available)` 选取，但 002 删掉了 V6 中唯一能看出"版本间发生翻转"的**旋转离散度**诊断，只留下与之正交的 `center_spread_mm`。

后果在 G03/005 上可定量复现：被选中的标定版本在 Ring 门限内（0.6–1.1 px），但 Body 投影平均 IoU 仅 **0.31**，而未被选中的另一版本为 **0.84**。

---

## 1. 模块逐项矩阵

| # | 模块 | G01 成熟实现（V6/001） | 002 当前实现 | 判定 | 源码证据 | 实验后果 | 严重度 | 建议修复级别 |
|---|---|---|---|---|---|---|---|---|
| M1 | Ring 观测（边界采样/遮挡未知） | **两条**：V6 用 DXY 预处理后的 `ob`（含 `q_held`）；E4/001 用 `observe()` 直接取边界 | 采用 E4/001 的 `observe()` | `ALGORITHM_CHANGED`（相对 V6） | `native/camera.py:39-49` vs `ring_first_v6.../scripts/prepare_ring.py:23-29` | 无连通域/补洞，孤立 Ring 块直接进入门限（§2.4） | 高 | A |
| M2 | Ring 五自由度求解（内核） | `ring_pose_contact_v1/scripts/recover.py` 的 `decode/image_seeds/solve` | **逐字节相同**（AST 抽取比对） | `IDENTICAL` | `native/_kernels.py:21-41` ≡ `recover.py` | 无 | — | — |
| M2b | Ring 求解**配置** | V6 prepare_ring：`seed_retain=4, max_nfev=100` | `RF_CONFIG: seed_retain=2, max_nfev=35` | `ALGORITHM_CHANGED`（配置） | V6 `prepare_ring.py:23`；002 `camera.py:16` | 搜索预算减半以下，分支命中率可能不同 | 中 | A/B |
| M3 | RGB yaw / 法向翻转消歧 | `recover()` 72 角度栅格 + 有界细化 | 同一实现 | `IDENTICAL` | `camera.py:84-99`（`for f in [False,True]` + `np.linspace(-pi,pi,72)`） | 无 | — | — |
| M4 | RGB 参考地图 PnP | `native/rgb.py: pnp()` SIFT+RANSAC+LM | 同一实现 | `IDENTICAL` | `rgb.py:20-32` | 无 | — | — |
| M5 | **参考库构建** | V6：单一链路（Ring candidates → SIFT 跟踪 → 局部 SfM → BA → features019 三角化） | 002：**三条链路并存**（见 §2.2） | `ALGORITHM_CHANGED`（按实例而异） | `banks.py:20-57`；`bootstrap_references.py:47-96`；`complete_reference_inputs.py:11-55` | 不同实例相机不可比；003 报告仍以"同一成熟链"叙述 | **高** | A/B |
| M6 | RGB SIFT 跟踪 | `track005.py`（held 轨道每 5 取 1） | 逐字节副本，仅当走 MATURE 链路时调用 | `IDENTICAL`（代码）/ 使用面收窄 | `code/frozen_calibration/track005.py:34,44` | G01/005、G02/004 未走此链路 | 中 | A |
| M7 | 局部 SfM 初始化/三角化 | `local_ring_sfm.initialize/triangulate_training` | 逐字节副本 | `IDENTICAL` | `frozen_calibration/local_ring_sfm.py`（AST 抽取 6 个函数） | 无 | — | — |
| M8 | BA | `local_ring_sfm.BA`，`least_squares(soft_l1, max_nfev=60)` | 同源同参 | `IDENTICAL` | `local_ring_sfm.py:63-89`；`config.json: BA_max_nfev=60` | 无 | — | — |
| M9 | **BA 收敛是否准入** | 不检测：`rec.update(success=True)`（仅异常才算失败） | 同样不检测：`status='PASS'` 只要不抛异常 | `IDENTICAL`（**继承缺陷，非 002 新引入**） | V6 `track005.py:94-98`；002 `bootstrap_references.py:78-83`；`local_ring_sfm.py:89`（`success=fit.success` 只记录） | G03/005 选中 `success=False` 版本 | **高** | A |
| M10 | **初始化版本选择** | `primary=min(available)`，并显式记录"fixed version order not holdout" | `primary=min(poses)`，语义等价 | `IDENTICAL`（同样继承） | V6 `validate_select.py:5`；002 `bootstrap_references.py:85,90` | G03/005 选中较差版本 | **高** | A/B |
| M11 | **每帧标定验证** | `validate_select.py`：held 轨道重投影、Ring 自轮廓、正深度比、中心离散、旋转离散 → `VALIDATED / MODEL_PREDICTED` | **整段缺失** | `STAGE_MISSING` | V6 `validate_select.py:5-18`；002 无对应文件 | 坏相机无任何拦截 | **极高** | A |
| M12 | **支持视角筛选** | `select_supported_views.py`：仅取 `VALIDATED` 视角进入 MVS | **缺失**（8 个 FIT 全部进入 HERO/Body） | `STAGE_MISSING` | V6 `select_supported_views.py:2`；002 `standard.py:44-50` 只查相机 ADMISSION | G03/005 坏相机进入 HERO | **极高** | A |
| M13 | 验证诊断字段 | `held_reprojection`、`initialization_rotation_spread_deg`、`ring_open_hole_ratio`、`held_positive_fraction` 等 | 仅保留 `Ring_MAE_px / Ring_P95_px / center_spread_mm` | `STAGE_MISSING`（诊断被裁剪） | V6 `validate_select.py:15`；002 `bootstrap_references.py:88-90` | **保留的诊断与主要失效模式正交**（见 §2.3） | **高** | A |
| M14 | 跨视频对齐（004↔005） | `align_local_scenes_disjoint.py`，结果 **`accepted=False`**（见 §3） | TASK.yaml 显式禁止 `cross_video_BA` | `STAGE_MISSING`（**有意，且历史上本就不成立**） | `alignment005_to004_disjoint.json: accepted=false, alpha=-88.9°` | 004/005 从未共享坐标 | 中（须在报告中显式声明） | 文档级 |
| M15 | HERO | `run_mvs005.py` → 官方 MVSAnywhere | `hero_stage` 适配（4 帧循环支持，偏移 2/4/6） | `ADAPTER_ONLY` | `adapters.py:16-27`；`standard.py:44-58` | 无算法变化 | — | — |
| M16 | **HERO 深度尺度一致性检查** | 无 | 无 | `IDENTICAL`（**从未有过**） | — | 2/40 视角深度差 6–25× 仍 PASS（§2.5） | **高** | B/C |
| M17 | Body 初始化 | EXACT013 `V/F/F_solid/cap` | 同一资产，逐字节 | `IDENTICAL` | `pipeline.py` 冻结资产；001/002 同源 | 无 | — | — |
| M18 | Body 优化器 | Graph 32 节点 + Smooth ARAP + Sweep，36 外循环 | 同源，仅实例路由补丁 | `ADAPTER_ONLY` | `adapters.py:13-16`（`video='004'→VIDEO`）；002 `UPDATES.json.configuration` | 无算法变化 | — | — |
| M19 | Ring/几何门控 | 3 px Ring 门限、透视/自交/基底 | 未改动 | `IDENTICAL` | `pipeline.py: camera_gate`；`RESULT_CARD` 声明未放宽 | 无 | — | — |
| M20 | 评价与 GT 隔离 | 冻结后独立评价，尺度固定 SE(3) | 同源 | `ADAPTER_ONLY` | `adapters.py:28-36` | 无 | — | — |
| M21 | **Body 更新有效性判定** | 无（只看门控） | 无（只看门控） | `IDENTICAL` | `UPDATES.json`；实测位移见 §2.4 | G02/005、G06/005 位移 1.6e-5/2.6e-5 mm 仍记 PASS | 中 | B/C |

---

## 2. 五个疑点的逐条核实

### 2.1 疑点一：BA 收敛未进入准入 —— **成立，但属继承缺陷**

`BA()` 从不抛异常表达"未收敛"，只把 `fit.success` 记进返回字典：

```python
# code/frozen_calibration/local_ring_sfm.py:89
return cur, P, dict(success=fit.success, nfev=fit.nfev, ...)
```

调用方仅捕获异常即视为成功：

```python
# code/bootstrap_references.py:79-83
ini,info=ns['initialize'](...); X,tids,support=ns['triangulate_training'](ini,tr); cur,P,ba=ns['BA'](...)
np.savez_compressed(...); poses[version]=cur
results.append(dict(version=version,status='PASS',initialization=info,local_BA=ba,...))
except Exception: results.append(dict(version=version,status='FAIL',...))
```

**实测：** G03/005 版本 0 记录为 `status=PASS`，但其 `local_BA.success=False`、`nfev=60`（打满预算）、目标 0.2134；版本 1 `success=True`、`nfev=46`、目标 0.1469。

**关键判断：** V6 的 `track005.py:94-98` 是同一写法（`rec.update(success=True, ...)`），`validate_select.py:5` 也只按 `x['success']` 过滤。**因此这是 V6 就存在的缺陷，002 忠实继承，不是本轮新引入的退化。** 在修复方案中不能把它描述成"恢复被新流程遗漏的成熟检查"，而应描述为"成熟链本身缺少收敛准入"。

### 2.2 疑点二：`primary = min(poses)` —— **成立，且与 V6 完全一致；但 002 丢了配套诊断**

V6：

```python
# scripts/validate_select.py:5
available=[x['version'] for x in runs if x['success']]; assert available; primary=min(available)
```

002：

```python
# code/bootstrap_references.py:85,90
primary=min(poses); cur=poses[primary]
... selection='original lowest successful initialization version; no GT/HOLDOUT feedback'
```

选择规则一致。但在 V6 里，选完之后还有一整套**独立验证**（M11/M13）；002 只保留了三个标量诊断。差异不在"选取规则"，而在"选取之后没有验证"。

### 2.3 疑点三：G03/005 Ring 通过但 Body IoU 极低 —— **已定位到具体机制：被选中的标定版本落在错误分支**

证据链（全部可复算）：

1. G03/005 两次初始化版本的相机相对旋转差为 **174.1°–179.4°**（逐视角），即两版本互为"绕视线轴的翻转分支"；像素 Ring 残差对翻转不敏感，所以两者都能通过 3 px 门限。
   - 复算：`NATIVE_CALIBRATION_0.npz` vs `NATIVE_CALIBRATION_1.npz`，8 个 FIT 视角旋转夹角 174.10–179.42°。
2. 版本 0（被选中）的 BA 未收敛（`success=False`），版本 1 收敛。
3. **Body 投影复算**（同一 EXACT013 的 B1 `FINAL.npz`，仅替换相机版本，其余不变）：

   | 视角 | IoU@v0 | IoU@v1 | | 视角 | IoU@v0 | IoU@v1 |
   |---|---:|---:|---|---|---:|---:|
   | raw00070 | 0.1313 | 0.8335 | | raw00474 | 0.1507 | 0.8499 |
   | raw00589 | 0.1633 | 0.8493 | | raw00099 | 0.1337 | 0.8267 |
   | raw00402 | 0.7864 | 0.8361 | | raw00546 | 0.1641 | 0.8440 |
   | raw00373 | 0.7675 | 0.8269 | | **均值** | **0.3077** | **0.8395** |

   与流水线自报的 FIT IoU 0.2376/0.2432/0.2387 同量级（我的复算是粗略光栅化，不做遮挡/深度测试，故略高）。
4. 因此：**Ring 正确 ≠ 相机正确**。Ring 是旋转对称体，绕环轴约 180° 的翻转不改变 Ring 投影残差，却把 Body 放到错误一侧。3 px 门限在原理上无法发现该失效。

**结论：** G03/005 的失败不是"Ring-First 算法错"，也不是"Body 形态错"（其条件占据 IoU 0.767，与 GT 形状并不差），而是**标定版本选择 + 缺少旋转分支验证**共同造成的相机-主体相对定向错误。旧 004 相机、旧缺柄问题都没有被本轮修复，报告这一点的表述是诚实的。

**两条必须同时写明的补充证据（来自对 v6 冻结产物的复核）：**

1. **v6 自己就记录过这个翻转，而且数值一致。** `ring_first_v6.../metrics/camera005_status.csv` 的 `rotation_spread_deg` = **177.2–178.1°**；`validate_select.py:15` 还把它写进逐帧记录 `initialization_rotation_spread_deg`。002 把这两个字段一起删掉了，只留 `center_spread_mm`。**这不是"成熟链没有该诊断"，而是"002 删掉了成熟链已有的诊断"。**
2. **`min(available)` 并非总是选错——它是运气。** 在 v6 自己的 005 上：v0（`BA.success=False`，nfev 打满 60）反而是**更好**的版本（22 帧中 15 帧 VALIDATED）；v1（`BA.success=True`，nfev 仅 12）为 **0/22**。也就是说：
   - "BA 未收敛"与"该版本更差"**不是等价的**；
   - 不能把修复简化为"过滤 `success=False`"；
   - 真正需要的判据是**验证通过数 / 旋转离散 / Body 投影一致性**，而不是 `success` 位或版本序号。

   这一点同时否定了两种过度简化的修复方案（"只看 BA success"和"改成按目标函数取最优"），必须在 RA 裁决时明确。

### 2.4 疑点四：G05/005 `G05_v005_raw00404` 的 Mask 质量 —— **成立，且已量化到单个连通域**

`metrics/RING_COMPONENT_DIAGNOSTICS.csv`（已是 002 自己产出的证据）：

| 分量 | 面积 px | 观测边界点 | 该分量 Ring MAE | 对总 MAE 贡献 |
|---|---:|---:|---:|---:|
| 1（主环） | 9,901 | 113/128 | 0.724 px | 0.639 px |
| 2（孤立块） | **63** | 15/128 | **75.19 px** | **8.812 px** |

总 MAE 9.451 px > 3 px 门限，**完全由 63 像素的孤立区域造成**。若只对主环求值，该视角 MAE 为 0.724 px，可通过门限。

同一实例另有两个视角是 RGB 内点为 0（`raw00251`: 7 匹配/0 内点；`raw00285`: 9 匹配/0 内点），属参考库覆盖不足，与掩膜无关。因此 G05/005 的 PARTIAL 是**两类独立原因**叠加，不能合并叙述。

> 注：**不得**通过删除分量来通过门限。可选方案是"连通域选择 + 记录被排除分量"，并在报告中同时给出含/不含两种 MAE。见 DXY 审阅与 PROPOSED_MINIMAL_REPAIR_PLAN。

### 2.5 疑点五：G03/005 HERO 深度残差达数百毫米 —— **异常确认；主因指向相机，非模型，但仍属 UNVERIFIED**

**实测（40 个已求解视角全量扫描）**：以 `中位深度 / 相机到环心距离` 为尺度一致性指标，中位数 1.03、p90 1.61，但有两个极端值：

| 视角 | HERO 深度中位 | 相机 \|t\| | 比值 |
|---|---:|---:|---:|
| G03_v005_raw00373 | **1060.8 mm** | 41.7 mm | **25.4×** |
| G03_v005_raw00402 | **246.6 mm** | 40.3 mm | **6.1×** |

场景尺度约 40 mm、环 R=5.6 mm，1 m 深度在物理上不可能。二者均被记为 HERO `PASS` 并进入 Body。

**与相机的关系（可复算）**：这两个视角正是版本 0 与版本 1 差异最大的两个（`center_spread_mm` 64.7 / 60.3 mm，其余 6 个视角 1.3–2.3 mm）。在版本 0 下，目标相机与三个支持相机的间距为 60–61 mm；在版本 1 下为 2.8–13.5 mm。即版本 0 把目标相机放到了离支持帧约 6 cm 的位置，HERO 拿到的四视图几何自相矛盾。

**判定：** 相关性**强**，但因果**未证**——因为不允许重跑 HERO。若后续要做判别性诊断（只读、不重训），应比较同一视角在 v0/v1 两套相机下的官方推理输出；那属于下一次任务，不在本轮范围。

**无论成因如何，可确证的是：现有 HERO 门禁只检查 `valid_pixels/polyp_vertices/faces`（`hero/*/ADMISSION.json`），从不检查深度与相机的公制一致性。** 这是一个独立于成因的流程缺陷。

---

## 2.6 本轮最重要的结构性发现：**"G01 成熟实现"其实是两条上游，不是一条**

任务书要求"找到 G01 真正成熟的实现"，不能假定最近一次统一流程就是标准。逐源码核对后必须报告：**项目里存在两条互不相同的 Ring 上游，G01 的 004 与 005 分别来自不同的一条，002 把它们拼在了一起。**

| 维度 | **A 线：E4/native（004 线）** | **B 线：V6 prepare_ring（005 线）** |
|---|---|---|
| Ring 观测来源 | `native/camera.py: observe()`：直接对 labels 取边界，5×5 膨胀判遮挡未知 | DXY `INITSegmentation` 产 mask + DXY 适配器 `adapt()` 产 `ring_train/heldout/visible_region/background_region`，并做 5 取 1 的 held 切分 |
| Ring 预处理 | **无**（无补洞、无连通域、无既有环检查） | `dxy_mid._engine.ring_holes.run`（补洞）、`components.FrameInput`、`v81_components.existing_ring_check` |
| 候选播种 | `image_seeds()`：按深度/倾角/方位离散播种 | `image_seeds()` + 几何中心线追加种子 + `branch_seed_policy.diverse_four` 去冗余 |
| 求解预算 | `seed_retain=2, max_nfev=35` | `seed_retain=4, max_nfev=100` |
| 求解内核 | `_kernels.decode/solve` | **同一份内核**（AST 比对逐字节相同，源 `ring_pose_contact_v1/scripts/recover.py`） |
| 参考库 | 004 冻结库（001 的 `BANK_ADMISSION.json`） | 局部 SfM + BA（`local_ring_sfm`） |
| **最终相机如何得到** | 逐视角 `recover()`：PnP 种子 → 5DOF → RGB yaw 网格 | **BA 输出**（`local005_camera_{version}.npz`），无逐视角重解 |
| 验证 | 仅 3 px Ring 门限 | `validate_select` held 验证 + `select_supported_views` 筛选 |
| 跨视频 | 不涉及 | 尝试 004↔005 对齐，**accepted=false** |

**002 的实际做法：**

- 004 的四个实例 → 直接继承 **A 线**结果（`FROZEN_REFERENCE`）；
- 005 的参考库 → 用 **B 线**代码构建（`bootstrap_references.py`，`MATURE_..._REV1`）；
- 005 的最终相机 → 又回到 **A 线**的 `recover()`（`cameras.py:24`）。

也就是说：**"B 线的库 + A 线的相机"这一组合在历史上从未被验证过**。V6 的 005 相机来自 BA，而不是 per-view `recover()`；001 的 004 相机才是 per-view `recover()`。002 把两者接在一起，却没有 B 线配套的 held 验证（M11）来兜底。

这解释了两件事：

1. 为什么报告里"复用 G01/004 RF_ONLY_V1 的 native camera.recover"（`report/FINAL_REPORT.md:13`）与"四段 005 已实际调用成熟 G01 上游模块"（同文件 `:23`）同时成立却不矛盾——它们说的是两条不同的线；
2. 为什么 G03/005 会选到翻转分支：**A 线的 per-view `recover()` 没有 B 线的 held 验证**，而 B 线的库又给了它一个可能已经偏转的 gauge。

> **给 RA 的判据建议：** 在批准任何修复前，必须先回答"哪条线是 G01 的权威线"。若权威线是 A 线，则 005 应当要么完全用 A 线重建库，要么明确标注为实验性；若权威线是 B 线，则 002 的最终相机阶段（`cameras.py`）就是 `ALGORITHM_CHANGED`，而不是 `ADAPTER_ONLY`。

---

| 问题 | 证据 | 结论 |
|---|---|---|
| 两视频是否共享同一参考坐标系？ | V6 `metrics/alignment005_to004_disjoint.json`：`accepted=false`、`status=MODEL_PREDICTED_ALIGNMENT_ONLY`、`alpha_deg=-88.90`、`normal_flip=false`、held 005→004 MAE 9.17 mm、held 004→005 MAE 41.9 mm | **否。** 尝试过环轴旋转 + 法向翻转的离散对齐，被明确拒绝 |
| 是否真正做过跨视频配准？ | 同上；方法注明 "no ICP or scale correction" | 做过，**未通过** |
| 哪些阶段独立处理两个视频？ | 002 `TASK.yaml: forbidden: [cross_video_BA]`；`pipeline.inherited()` 只把 004 的 G01/G03/G05/G06 作为冻结引用 | 全部独立 |
| 是否共享同一个 Body？ | 002 每个 (case,video) 独立 `body/B1,B2/FINAL.npz`；同一 `EXACT013` 资产作为初值 | **共享初值资产，不共享优化结果** |
| HERO 是否跨视频融合？ | 002 的 HERO 支持帧取同视频 FIT（偏移 2/4/6，`standard.py:44-50`） | **否** |
| 新流程是否退化为两个独立单视频优化？ | 是 | **是，且这是当前唯一被证据支持的形态** |

另外，001 在 `rf_only.py:30` 曾显式把 G01/005 的历史库判为 `INHERITED_CROSS_VIDEO_MAP_GAUGE_UNCERTIFIED` 而 FAIL。002 用"同视频重建"替换了它，方向正确；但这恰恰说明 **004 与 005 之间没有共享坐标**。

**报告口径要求：** 任何"多视频共享主体"的表述在 004/005 之间都不成立。只能表述为"同一冻结初值资产下的两个独立单视频实例"。

---

## 4. 参考库来源的三种形态（跨实例可比性风险）

按 `bank/ADMISSION.json` 的 `execution` 字段实扫：

| 实例 | execution | 来源 | 地标数 |
|---|---|---|---:|
| G01/004, G03/004, G05/004, G06/004 | `FROZEN_REFERENCE` | 001 的 `BANK_ADMISSION.json` 冻结引用 | 8 / 6 / 8 / 7 |
| G01/005 | `NEW_BUILD_OR_RECOVERY` | 历史原生地图 + 记录 H 逆变换恢复 | 980 |
| G02/004 | `NEW_BUILD_OR_RECOVERY` | `features019.landmarks` 同视频 7 张历史 FIT | 125 |
| G02/005, G03/005, G05/005, G06/005 | `MATURE_G01_NATIVE_REFERENCE_BUILD_REV1` | V6 Ring+RGB 局部 SfM + BA + features019 | 230 / 145 / 107 / 52 |

三件事必须写进报告：
1. 004 的四个引用来自 001 的冻结库，**不是本轮重算**；
2. G01/005、G02/004 走的是"历史归档/三角化"路径，**不是 V6 的局部 SfM+BA 路径**；
3. 因此"全流程统一"只对 4 个 MATURE 实例成立，其余 6 个是混合来源。报告 §"全部使用共享成熟构库" 的措辞偏强。

---

## 5. Body 更新的"PASS 但不动"

用 `INITIAL.npz` 与 `FINAL.npz` 的顶点欧氏距离复算：

| 实例 | B1 最大位移 mm | B2 最大位移 mm | 已接受步数(B1) | 结论 |
|---|---:|---:|---:|---|
| G01/005 | 0.633 | 0.566 | 20/36 | 有效更新 |
| G02/004 | 0.092 | 0.144 | 13/36 | 弱更新 |
| **G02/005** | **0.000016** | **0.000018** | 9/36 | **数值停滞** |
| G03/005 | 0.462 | 0.088 | 11/36 | 有更新但相机错 |
| **G06/005** | **0.000026** | **0.000027** | 9/36 | **数值停滞** |

`UPDATES.json` 中 G02/005、G06/005 的 `graph_translation_mm` 在迭代 0 即为全零矩阵，说明图节点从未移动，但门控仍逐帧记为 accepted。B0/B1/B2 三臂指标完全相同（如 G02/005 全部 0.5532024156）也正是这个原因。

**这是"执行成功"冒充"优化有效"的典型案例**，与 Q7 要求区分的层次直接相关。

---

## 6. 分层判定汇总

| 判定层 | 结论 | 依据 |
|---|---|---|
| 算法执行成功 | 9/10 实例产生 B1/B2；8/10 全视角 RF | `report/PIPELINE_COMPLETENESS.csv` |
| 参考库可靠 | **仅 4/10 走 V6 同源；6/10 为混合来源** | §4 |
| 相机恢复可靠 | **否**：G03/005 两版本互差 ~177°，选中者 BA 未收敛 | §2.3 |
| 多视角几何一致 | **否**：无 held-track 验证；无支持视角筛选 | §2.1、M11/M12 |
| 主体优化有效 | **部分**：2/5 新实例数值停滞 | §5 |
| 最终形态准确 | **未评价**：真实 HERO 绝对 3D 仍 `NOT_EVALUABLE` | `RESULT_CARD`、`BODY_METRICS` 列 `world_accuracy_claim=False` |

---

## 7. 必须与报告同时呈现的负面证据

1. G03/004 的 HOLDOUT 重放仍为 3.065 px > 3 px（报告已承认）。
2. G03/005 的 FIT IoU 0.24 是**相机分支错误**的直接后果，不是新发现的主体形态缺陷。
3. G05/005 的 PARTIAL 由"孤立 Ring 分量"与"RGB 零内点"两类原因构成。
4. 2/40 视角 HERO 深度尺度异常且被 PASS 接受。
5. G02/005、G06/005 的 Body 更新为零位移。

---

## 8. 本矩阵未覆盖的部分（UNVERIFIED）

| 项 | 原因 |
|---|---|
| HERO 深度异常的**唯一成因** | 需重跑官方推理（本轮禁止）；只能确认相关性与门禁缺失 |
| G02/005 停滞的数值原因 | 需检查逐视角对应质量与正则强度；本轮只做了位移统计 |
| G01/005 的 980 地标恢复精度 | 依赖历史记录的 H；未独立复算 H 的来源可靠性 |
| 004 冻结库的原始生成过程 | 001 只记录了 ancestry 8 视角，未保留当时中间产物（已确认 `reference_banks/G01_004.npz` 存在但无构建日志） |
