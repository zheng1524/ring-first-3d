# DXY_READONLY_METHOD_REVIEW

**Task:** TASK-E4-G01-PIPELINE-AUDIT-003
**Status:** `AWAITING_RA_REVIEW`
**对象：** `/home/liu/new-polyp-dxy`（V9.1 Geometry + Mid-Major Scale），**严格只读**
**方式：** 静态调用图 + 源码逐行阅读；**未运行** `measure_frame`/测试/脚本；**未写入、未修改 DXY 任何文件**。
**独立复核：** 本文最关键的 6 条断言已由审计主线**独立重验**（见 §0.2），其余为静态推断，已在 §9 标注 UNVERIFIED。

---

## 0. 结论摘要

### 0.1 一句话

DXY 的 V9.1 是一条**没有相机模型**的二维测量链：它先做**只增不减的小孔填充**，再用**最大连通域 + 5×5 闭开 + RANSAC 椭圆**恢复环几何，最后在**弱透视同深度**假设下把像素长度换算成毫米。它的三项能力对三维前端有直接价值——**小孔填充规则、连通域选择、椭圆拟合质量三件套**；但它的**尺度模型与中心线平均**在几何上不可移植。

### 0.2 本次独立重验的 6 条关键断言

| # | 断言 | 复核结果 |
|---|---|---|
| 1 | `ring_holes` 不做闭运算 | ✅ `ring_holes.py:6` `RULE['closing_used']=False`，全文无 `morphologyEx` |
| 2 | 闭+开 5×5 只发生在拟合副本 | ✅ `polypseg_ring_fitting.py:15-20` `MORPH_CLOSE`→`MORPH_OPEN`，作用于入参副本 |
| 3 | V9.1 实际用 `legacy` 门限 | ✅ `exact_v2.py:26`、`run_competition.py:9` 显式传 `'legacy'` |
| 4 | `native_P` 被 `observable_P` 覆盖 | ✅ `observable_boundary.py:11-12` 临时替换 `prior.native_P`，`finally` 复原 |
| 5 | 链序：先补洞，再建 FrameInput，再 Ring | ✅ `pipeline.py:67-69` `holes → FrameInput(effective) → engine.ring` |
| 6 | DXY 无相机内参/位姿 | ✅ `components.py:8-16` 的 `FrameInput` 无 K；全仓 grep `solvePnP\|camera_matrix\|intrinsic\|focal` **零命中** |

### 0.3 与三维重建最相关的三个事实

1. **小孔填充是"只加环像素"的单侧操作**，`assert` 保证息肉标签与未填充处逐位不变（`ring_holes.py:33-36`）。这使它可以安全地作为三维前端的预处理。
2. **孤立环斑块不会被删除**。拟合只取最大连通域（`polypseg_ring_fitting.py:29-35`），但该斑块仍是 `labels==2` 的像素，仍会参与 `band` 抑制与 P 的 3×3 邻接判定。**因此"DXY 能自动处理孤立误分割"是错误理解**——它只让拟合不受影响，不让观测/门限不受影响。
3. **二维椭圆不能直接当三维位姿**，原因是数据契约与几何两方面的双重缺失（§8）。这不是"精度不够"，而是"信息不存在"。

---

## 1. V9.1 实际调用链

入口 `pipeline.measure_frame` → `_measure`，全部算法调用集中在 `_measure` 内（`pipeline.py:65-130`）：

| # | 阶段 | 调用 | 位置 | 在正式链 |
|---|---|---|---|---|
| ① | Ring 小孔填充 | `engine.holes` → `ring_holes.run` | `pipeline.py:67` | **YES** |
| ② | 建帧对象 | `engine.FrameInput(image,effective,…)` | `pipeline.py:68` | **YES** |
| ③ | Ring 几何恢复 | `engine.ring` → `v81_components.existing_ring_check` | `pipeline.py:69` | **YES** |
| ④ | 边界（P/Q/X） | `engine.boundary` → `observable_boundary.boundary_native` | `pipeline.py:83` | **YES** |
| ⑤ | 交叉环重验 | `engine.cross_ring` | `pipeline.py:84` | **YES** |
| ⑥⑦ | 短 Q 弧过滤 | `q_arc_filter.analyze/apply` | `pipeline.py:86-87` | **YES** |
| ⑧ | V2 基线 | `run_competition.current_baseline` | `pipeline.py:89` | **YES** |
| ⑨ | 5 变体×A/B | `v84_pilot.configs84` | `pipeline.py:92` | **YES** |
| ⑩⑪ | 选择与审计 | `q_distance_selection` | `pipeline.py:94-95` | **YES** |
| ⑫ | 尺度 | `scale.run('mid_major')` | `pipeline.py:101` | **YES** |
| ⑬ | 轴长 | `contracts.ellipse_axes` | `pipeline.py:118` | **YES** |

**链外/死代码（必须知道，否则会误引）：**

| 对象 | 状态 | 证据 |
|---|---|---|
| `native_boundary.native_P`（含图像对比度判据） | **不执行**（被覆盖） | `observable_boundary.py:11-12` |
| `gate.run(...,'u2_strict')` 的一整套严格阈值 | **不执行** | `exact_v2.py:26` 固定 `'legacy'` |
| `split_mask_if_needed` 的 watershed 分支 | 调用但早退 | `polypseg_ring_fitting.py:69-70`（`expected_rings=1`） |
| `fit_single_component` 的 `mid_ellipse`/`quality` | 计算但不被主线读取 | `ring_component.py:66` 只读 `outer_ellipse` |
| `v83_boundary.extract` | 执行**两次** | `native_boundary.py:39`、`cross_ring_boundary.py:20` |
| `engine.fusion` | 每帧链 **NO**（批处理用） | `batch.py:71-73` |

---

## 2. Ring Mask 清理（逐项）

### 2.1 小孔填充：**YES**（`ring_holes.py`）

| 问题 | 答案 | 证据 |
|---|---|---|
| 是否做小孔填充 | **是** | `pipeline.py:67` → `ring_holes.py:8-37` |
| 形态学闭运算 | **否** | `ring_holes.py:6` `closing_used=False`；全文无 `morphologyEx` |
| 形态学开运算 | **否** | 同上 |
| 连通域筛选 | 对"环内背景洞"做 8 连通枚举；**不删除环连通域** | `ring_holes.py:18-21` |
| 只改 Ring 还是也改 Polyp | **只改 Ring**（`result[fill]=2`），并有 `assert` 保证息肉逐位不变 | `ring_holes.py:32-36` |
| 保留原始 Mask | **是**（`labels.copy()`，不原地修改；只把 SHA256 写入 audit） | `ring_holes.py:9`；`pipeline.py:80-81` |
| 是否移动真实边界 | **是**，但只移动"被环完全包围的小背景洞"的边界 | `ring_holes.py:22-31` |

**5 条接受/拒绝规则（`ring_holes.py:22-31`）：**

1. 洞内含非背景 → 保留（`contains_polyp_or_nonbackground_preserve`）；
2. 面积 > `min(.025·ring_area, .5·w²)` → 保留（`area_above_small_hole_limit…`）；
3. 长边 > `1.5·w` → 保留（`elongated_or_large_span_preserve`）；
4. 距环质心 < `.35·sqrt(area/π)` → 保留（中心保护）；
5. 洞的 8 邻边界必须**全是**环材料，否则保留。

其中 `w = 2·q90(distanceTransform(ring))`（`:12-13`），即"局部环带宽的参考分位"。

### 2.2 `ring_component` + `polypseg_ring_fitting` 的形态学：**YES，但只作用于拟合副本**

| 项 | 答案 |
|---|---|
| 闭运算 | `MORPH_CLOSE` 5×5 椭圆核（`polypseg_ring_fitting.py:17`） |
| 开运算 | 对闭结果再做 `MORPH_OPEN` 5×5（`:19`） |
| 作用域 | 只作用于裁剪框内的副本（`ring_component.py:64` 传入 `region[y0:y1,x0:x1]`） |
| 是否写回标签 | **否** |
| 调用点 | `ring_component.py:64`（主）；`v81_components.py:16`（兜底再调一次） |

### 2.3 两者不是同一步骤（这是本轮必须纠正的混淆）

| 维度 | `ring_holes` 小孔填充 | `preprocess_ring_mask` 闭开 |
|---|---|---|
| 目的 | 修**掩膜内容** | 修**拟合数值输入** |
| 方法 | 连通域 + 5 条几何/拓扑规则 | 5×5 闭 → 5×5 开 |
| 作用域 | 全图 `labels==2` | 裁剪副本 |
| 写回标签 | **是** | **否** |
| 顺序 | 先（`pipeline.py:67`） | 后（`pipeline.py:69` 内部） |
| 在 V9.1 链 | YES | YES |

### 2.4 遮挡是否补全

| 层 | 是否补全 | 说明 |
|---|---|---|
| Mask 层 | **否** | 未闭合缺口是 external → 保留；含息肉的洞保留 |
| Ring 参数化层 | **是（仅 Ring）** | 可见弧 RANSAC 椭圆天然外推；内弧失败时用中轴 `2mid−outer` 合成 |
| Polyp 层 | **否** | 只用 Q 软区间约束圆/椭圆，不做像素补全 |

---

## 3. 连通域（逐项）

| 层 | 规则 | 是否在正式链 | 证据 |
|---|---|---|---|
| Ring 清理 | 只枚举"环内背景洞"，不删环组件 | YES | `ring_holes.py:18-31` |
| Ring 拟合 | `select_components`：`min_area=300`，按面积降序取第 1 个 | YES | `polypseg_ring_fitting.py:23-35` |
| Ring 证据带 | `band` 用**全部**环像素膨胀 → 产生候选抑制区 | YES | `v2_candidates.py:34-35` |
| P 的 3×3 邻接 | 3×3 内有环像素即判 X | YES | `observable_boundary.py:47-49` |
| Polyp 组件 | 面积 < `max(12,.003rr²)` 丢弃；可见点 <12 丢弃；`broad_descriptor` 判宽 | YES | `v2.py:102,115` |
| Polyp 主体 A | `outside & broad & visible≥12` 并集 | YES | `v2_candidates.py:39-43` |
| Polyp 主体 B | 全部 substantial 并集 + 开运算 | YES | `v2_candidates.py:44-47` |
| 内部息肉孔 | 永远判 X | YES | `observable_boundary.py:44` |

**关键结论（须写入三维侧的设计讨论）：**

> DXY 对孤立环斑块只是"拟合时忽略"，**并不从掩膜移除**。因此"借用 DXY 的连通域选择"**不能**直接解决 G05/005 的 63 px 孤立块问题；要解决三维侧的问题，必须把"连通域选择"作用到**观测层**（`observe()` 的边界采样），而不是只作用到拟合层。

---

## 4. Ring 椭圆拟合（逐项）

| 问题 | 答案 | 证据 |
|---|---|---|
| 外环提取 | 最大外轮廓（RETR_CCOMP）→ RANSAC 外椭圆；再用可见弧点重拟合 | `polypseg_ring_fitting.py:49-54`；`ring_component.py:66-76` |
| 内环提取 | 可见内弧点 → RANSAC → `validate`；失败走中轴兜底 | `ring_component.py:77-94` |
| 中心线 | **内/外椭圆参数逐项算术平均**（cx,cy,a,b），角度用 `2θ` 圆平均 | `ring_component.py:100` |
| RANSAC | **是**：200 次、20 点子集、`cv2.fitEllipseDirect`、阈值 `max(2.5, .015·2·max(a,b))`、`rng=42`、内点重拟合 | `polypseg_ring_fitting.py:132-181` |
| 异常点过滤 | 灰度阶跃 ≥5、`alignment≥.60`、`rho` 带、RANSAC 内点、四象限稳定性 | `ring_component.py:19,28-29,110-120` |
| 用灰度梯度还是 RGB | **只用灰度**（`BGR2GRAY`），且**不是图像梯度**，是沿椭圆法向的两采样点符号差，`hop=max(3,max(shape)/256)` | `ring_component.py:20,24,27-29` |
| 残差评估 | 归一化残差 ≤0.08；`coverage` 36 bin 占用；`stability` 四扇区重拟合 | `ring_component.py:51-53,106-120` |
| 遮挡恢复 | ①可见弧椭圆外推；②中轴 `2mid−outer`；③拓扑闭合内环兜底 | `ring_component.py:70-94`；`v81_components.py:16-29` |
| 不可靠时返回 | `valid=False` + 明确 `reason`；`pipeline.py:82` 立即返回 `D=NaN`、`quality_class='ring_failure'` | `ring_component.py:61-95` |

**符号约定（重要限制）：** 代码要求"环材料比洞内与环外都暗 ≥5 灰度级"（`ring_component.py:28-29`）。公开样例是黑色环带，与此一致。**换亮环会两侧失败**，只能走中轴兜底。这是材质相关假设，不是通用算法。

**失败原因枚举（可直接借用为三维侧审计字段）：**
`ring_mask_insufficient` / `ring_component_missing` / `outer_fit_missing` / `observable_outer_edge_insufficient` / `outer_edge_fit_unstable` / `ring_recovery_unreliable`（`ring_component.py:61-95`）。

---

## 5. Polyp Mask 与 P/Q/X

| 项 | 事实 | 在正式链 | 证据 |
|---|---|---|---|
| P（可观察边界） | 由 `observable_P` 判定：原始息肉轮廓点上，排除内部孔、画幅边界、3×3 内有环、3×3 内无背景 | YES | `observable_boundary.py:35-53` |
| **P 是否用图像强度** | **否**。对比度判据在 `native_P` 里，但被覆盖 | — | `observable_boundary.py:11-12`；`native_boundary.py:25-29` |
| Q（遮挡弱约束） | 原始息肉轮廓像素 + 外法向 + 软区间 `[−min(1,.05w), {.1,.2,.35}w]`；**从不定位遮挡边界** | YES | `boundary_v7.py:89-91`；`cross_ring_boundary.py:59` |
| X（不可用） | 其余全部；reason 枚举 15+ 种 | YES | `boundary_v7.py:64-87`；`q_arc_filter.py:14` |
| 主体圆/椭圆候选 | V2 种子 + Q 相干初始化（5 个位移分数）+ 最小 RANSAC（64 次）+ 5 种子 LM 精化（`max_nfev=70`） | YES | `geometry_competition.py:52-67,154-210` |
| 异常轮廓排除 | 短 Q 弧整段删、Q 端点裁 20%、重复 Q 去重、环内息肉不算外约束、小封闭背景洞不算外部 | YES | `q_arc_filter.py:40`；`v84_boundary.py:99-112`；`v83_boundary.py:71,42-43` |
| A/B 双主体 | 两候选的 `trusted` 被**同一 P** 覆盖，差异只剩 mask 派生的 center/extent | YES | `observable_boundary.py:23-24`；`geometry_competition.py:21` |

---

## 6. 质量诊断

### 6.1 实际执行的 `legacy` 门限（`gate.py:29-30`）

| 指标 | 阈值 |
|---|---|
| `center_distance_norm` | ≤ 1.25 |
| `fit_minor_radius` | ≥ `max(.15rr, .08extent)` |
| `fit_major_radius` | ≤ `max(3rr, 1.6extent)` |
| `arc_coverage` | ≥ 0.20 |
| `norm_residual` | ≤ 0.08 |
| `axis_ratio`（椭圆） | ≤ 3.5 |

### 6.2 **未执行**的 `u2_strict` 阈值（`gate.py:34-38`）

`n_points=25`、`visible_fraction=.20`、`arc_coverage=.40`、`norm_residual_all=.10`、`inlier_ratio=.60`、`C=.50`、`P=.50`、`sector_instability=.25` 等。**V9.1 不调用**（`exact_v2.py:26` 固定 `'legacy'`）。

### 6.3 V9.1 把 4 条判据降级为诊断（`q_evidence_policy.py:6,22-26`）

`P_inlier_fraction_below_0.60`、`legacy_arc_coverage_below_0.20`、`weak_evidence_direction_coverage_below_0.50`、`Q_interval_support_below_0.80` → **不再否决**，只写诊断。

**实际否决只剩 4 条**：`legacy_normalized_residual_above_0.08`、`V2_center_radius_or_axis_bounds`、`P_p90_residual_too_large`、`P_dominant_serious_Q_conflict`。

### 6.4 稳定性与可辨识性

| 指标 | 阈值 | 证据 |
|---|---|---|
| 三容差都必须接受 | `accept_count==3` | `v8_context.py:35` |
| 跨种子直径 UD | >0.20 → 不可辨识 | `:38` |
| 近优解数 | <3 → 搜索未证唯一 | `:39` |
| Q 饱和 | >0.30 警告 | `:41` |
| A/B 分歧 | >0.20 | `:42` |
| 近优集 | `score ≤ best×1.10 + 0.0004` | `geometry_competition.py:140` |

### 6.5 Q 冲突恢复（降级测量）

A/B 都无接受候选时，`recover_conflicted_candidates` 会**清空所有候选 reasons**、绕过 gate，按"弧加权平均 Q 距离"选一个，并标 `quality_class='Q_conflict_recovery'`、`stability_review_pass=False`（`q_distance_selection.py:26-56`；`pipeline.py:99,116`）。

> 这套"降级但显式标注"的做法，与三维侧需要的"`RING_AXIS_GAUGE_SUSPECT` 但继续产出并标注"是同一种设计哲学，可直接借鉴其字段命名与审计结构。

---

## 7. 每项"是否属于 V9.1 正式链"汇总

| 项 | 在链 | 证据 |
|---|---|---|
| 小孔填充 `ring_holes.run` | **YES** | `pipeline.py:67` |
| 小孔填充闭运算 | **NO** | `ring_holes.py:6` |
| 闭+开 5×5 拟合预处理 | **YES** | `ring_component.py:64` |
| 最大连通域 `min_area=300` | **YES** | `polypseg_ring_fitting.py:23-35` |
| watershed 拆分 | 调用 YES / 生效 **NO** | `polypseg_ring_fitting.py:69-70` |
| RANSAC 椭圆（200 次 / rng 42） | **YES** | `polypseg_ring_fitting.py:132-181` |
| 灰度阶跃（±5，暗环） | **YES** | `ring_component.py:20,27-29` |
| RGB / Sobel / Canny | **NO** | 仅灰度；无梯度算子 |
| `2mid−outer` 中心线兜底 | **YES（条件）** | `ring_component.py:82-94` |
| 内/外平均中心线 | **YES** | `ring_component.py:100` |
| `native_P`（含对比度） | **NO**（被覆盖） | `observable_boundary.py:11-12` |
| `observable_P`（3×3 邻接） | **YES** | `observable_boundary.py:35-53` |
| `u2_strict` 严格阈值 | **NO** | `exact_v2.py:26` |
| 4 条判据降级 | **YES** | `q_evidence_policy.py:6,22-26` |
| Q 软区间 | **YES** | `boundary_v7.py:89-91` |
| 短 Q 弧过滤 | **YES** | `q_arc_filter.py:40` |
| Q 冲突恢复 | **YES** | `q_distance_selection.py:26-56` |
| 尺度 `(D+1.2)/(2a_mid)`，`M=I` | **YES** | `scale.py:17-19`；`pipeline.py:102-103` |
| 相机内参 / 3D 位姿 | **不存在** | `components.py:8-16` |

---

## 8. 为什么二维椭圆不能直接当 Ring-First 三维位姿

**（一）数据契约层面：没有相机模型。**
`FrameInput` 只有 `image / labels / inner_diameter_mm / source_id / image_sha256 / mask_sha256`（`components.py:8-16`）。全仓无 `camera_matrix`/`intrinsic`/`distort`/`focal`/`solvePnP`。**没有 K 与畸变，PnP 无法定义。**

**（二）自由度层面：5 参数 vs 6+1。**
椭圆 `(cx,cy,a,b,θ)` 是 5 个量；平面圆刚体位姿是 6 个，半径未知再 +1。像面上 `a ∝ R/d`，**R 与 d 不可分离**。DXY 的处理是把 `R=(D+1.2)/2` 当已知标定，于是 `a` 只用于求尺度 `s=(D+1.2)/(2a_mid)`（`scale.py:19`），**从不求 t**。所以它输出的是尺度，不是位姿。

**（三）几何层面：单视图圆环存在法向二重解。**
椭圆反投影是以相机中心为顶点的锥，锥与平面相交得圆；即使有 K，平面法向仍有翻转二重解。DXY 把内外环**平均成一个椭圆**（`ring_component.py:100`），恰好丢掉了唯一化所需的内外双约束。

**（四）模型层面：中心线平均只在弱透视同轴相似下成立。**
透视下，同平面圆环的内外边界**不是**同心相似椭圆。`validate` 用 `gap/amid≤0.12`、角度差≤18°、线宽 0.6–1.8/0.42–1.98 mm 来**排除偏离情形**（`ring_component.py:42-44`），即用"拒测"代替"求解"。

**（五）尺度模型层面：`M=I` 与任何三维整流冲突。**
`mid_major` 断言 `matrix==I`、`coordinate_system=='native_image_px'`（`pipeline.py:102-103`），并用标量 `pxmm=2·a_mid/(D+1.2)` 同时除 major/minor 两方向（`ring_component.py:38-39`）——这假设两方向放大率相同，倾角信息被抹掉。

**（六）对象层面：息肉不在环平面内，环本身也不在平面上。**
`scale.py:12` 的 `mid_affine` 注明 "polyp and ring share plane and depth"；公开样例中环贴在息肉球冠上。**球冠上的环不是平面圆**，把它当平面圆已是一阶近似，再升级为 3D 位姿会把近似误差当真值。

**（七）代码自证：`bmid/amid < 0.35` 直接判 `ring_too_oblique`**（`ring_component.py:45`）。系统对"2D 近似失效"的帧选择**拒测**，而不是解 3D——这正是"2D 椭圆不足以表征 3D 姿态"的直接证据。

---

## 9. 对三维前端的可借鉴 / 不可移植

### 9.1 可借鉴（按价值排序）

| 优先级 | 方法 | 为什么可借鉴 | DXY 证据 | 三维侧对应缺口 |
|---|---|---|---|---|
| **高** | 小孔填充规则集（只加不减、5 条拒绝、不变式 assert） | 单侧、可审计、可回退；能消除"环内小洞造成的边界伪影" | `ring_holes.py:6,22-36` | 三维 `observe()` 直接用原始 labels，无任何环清理 |
| **高** | 椭圆拟合质量三件套（覆盖 / 稳定性 / 归一化残差） | 给"这个环能不能信"一个可量化判据，而不是只看 3 px | `ring_component.py:51-53,71-74,106-120` | 三维只有 Ring MAE/P95 |
| **中** | 显式失败原因枚举 | 便于跨任务统计与台账 | `ring_component.py:61-95` | 三维只有 `NO_RESOLVED_RING_FIRST_RGB_YAW` 一种原因 |
| **中** | "降级但标注"策略（Q 冲突恢复） | 与三维需要的 `SUSPECT` 语义一致 | `q_distance_selection.py:22`；`pipeline.py:99,116` | 三维目前 PASS/FAIL 二元 |
| **中** | 连通域选择（最大组件 + min_area） | 可移植到**观测层**，解决孤立环块 | `polypseg_ring_fitting.py:23-35` | 三维 `observe()` 无组件概念 |
| 低 | RANSAC 参数（200/20/rng42） | 可作为参考值，但三维拟的是 5DOF 位姿而非椭圆 | `polypseg_ring_fitting.py:132-181` | 不直接适用 |

### 9.2 明确不可移植

| 方法 | 原因 | 证据 |
|---|---|---|
| `centerline=(inner+outer)/2` | 透视下的近似，丢内外双约束 | `ring_component.py:100` |
| `scale=(D+1.2)/(2a_mid)`，`M=I` | 弱透视同深度假设；与 3D 整流冲突 | `scale.py:17-19` |
| 暗环专用 ±5 灰度阶跃 | 换环材质即失效 | `ring_component.py:28-29` |
| 2D 相似圆环阈值（gap/角度/线宽） | 三维应改用重投影/共面性残差 | `ring_component.py:42-44` |
| `observable_P` 的 3×3 邻接 | 纯 2D 拓扑；三维可见性应由深度/遮挡定义 | `observable_boundary.py:47-51` |
| A/B 主体（mask 形态学派生） | 2D 平面假设 | `v2_candidates.py:41-47` |

### 9.3 一条必须纠正的预期

**"用 DXY 的连通域处理就能修好 G05/005" —— 不成立。**
DXY 的 `select_components` 只影响**拟合选用哪个组件**；孤立斑块仍留在掩膜里，仍参与 `band` 与 P 的 3×3 邻接。要让三维侧的 Ring MAE 不受孤立块影响，必须在**观测层**做组件选择（等价于把 `observe()` 的边界采样限制在选定组件上），这是一个**新的观测语义**，需要 RA 批准，不能声称是"照搬 DXY"。

---

## 10. UNVERIFIED

1. 全部"是否在链上"结论来自**静态调用图与名字解析**，未实际运行 `measure_frame`。
2. 未统计真实数据上 `visible_inner_arc_RANSAC` 与 `centerline_symmetry` 各自占比。
3. 未验证"环比两侧暗 ≥5"在全部真实帧成立；只看了 1 张公开样例（黑环）。
4. 未验证 `v83_boundary.extract` 两次调用是否逐位一致（静态推断一致）。
5. 未验证小孔填充对 Q 判定的实际影响（静态推断：填洞边界全为环，不与息肉相邻，故不改 P 的 3×3 判定）。
6. 未验证 `v2_candidates` 中 B 主体开运算对 G05 一类低对比息肉的实际影响。
7. 本文引用的行号以 `src/dxy_mid/` 为根；子目录缩写见各处括注。
