# TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE — TECHNICAL_REPORT

```
UNIFIED_PIPELINE:      PARTIAL
G01 GEOMETRY:          GEOMETRY_INSUFFICIENT_EVIDENCE（2D 验证后 0 个身份）
G03 GEOMETRY:          GEOMETRY_PARTIAL（10 个身份 + H 候选完成；Joint BA/评价未完成）
G06 GEOMETRY:          GEOMETRY_PARTIAL（6 个身份 + H 候选完成；Joint BA/评价未完成）
NEW_METHOD_VALIDATION: INSUFFICIENT_EVIDENCE
```

## 1. 本轮真正完成的重建（代码层，全部在一个入口 `core/u028c.py`）

| 项 | 实现 |
|---|---|
| 运行上下文 | `Ctx(group, max_views)`：每组独立 `input_manifest/w0/view_selection/ring/rgb_features/identities/h_initialization/triangulation/ba/evaluation/figures` |
| W0 自动补算 | `w0_ensure()`：优先 `camera_mainline`；否则**调用正式** `tools/run_w0_camera.py --output runs/<G>/w0/video<v>`（不覆盖主线） |
| 真实哈希 | 每视角记录 `RGB` 内容 SHA256（`hashlib.sha256(rgb.tobytes())`）与 cache 文件 SHA256，写入 `input_manifest/` |
| 统一视角选择 | `select_views()`：Ring-valid **或** RGB 可用（SIFT≥120）+ 贪心角度覆盖（相机中心最小间距 + Ring 加分），**不再按帧号取前 N** |
| Ring（两个视频） | 历史 DXY `recover()` → `ring/<view>.npz|json`；`ring020_026.RingRenderer` 逐视角 M/I/C/O → `ring/RING_SCORES.csv` |
| 跨视频身份（2D 验证） | `features019.matches`（ratio .72 + mutual + MAGSAC）→ 用 `<label>_OBSERVATIONS.json` 把 (view, feature_id) 映射到地标 → 按 view-pair 投票 → `MULTIVIEW_IDENTITY_SUPPORTED / TWO_VIEW_GEOMETRY_SUPPORTED / GEOMETRIC_CONFLICT` + 一对一 |
| FIT/HOLDOUT | 身份级 70/30，`rng(2028)`，存 `SPLIT.json`（真实身份索引） |
| H 候选（新） | Ring **残差向量** 6-DoF 精化（yaw 网格 30°）+ 极线评分 → `H_CANDIDATES.csv` |
| 旧/新流程 | 旧：H=I → M2(H-only)；新：H2 → M3b(H+X)，同一 BA（`ba_core_r4`） |
| 三角化 | 身份级：两侧全部真实二维观测 + 固定相机（H 只应用一次）→ 历史 019 逐轨迹代码 |

## 2. 实际执行结果（真实数据）

| 组 | 参考/另一 | 选中视角 | 地标 | **2D 验证身份** | 状态 |
|---|---|---|---:|---:|---|
| **G01** | 005 / 004 | 4 + 4 | 10 / 26 | **0** | `GEOMETRY_INSUFFICIENT_EVIDENCE` |
| **G03** | 005 / 004 | 4 + 4 | — | **10**（fit 7 / hold 3） | `GEOMETRY_PARTIAL`（H 候选已完成，BA 未完成） |
| **G06** | 004 / 005 | 4 + 4 | — | **6**（fit 4 / hold 2） | `GEOMETRY_PARTIAL`（同上） |

- G03 身份示例：`005:168-004:92`，6 个 view-pair 支持，状态 `MULTIVIEW_IDENTITY_SUPPORTED`；
- G01 在 4+4 视角下 2D 验证后仍为 0，与 028 的 0 一致 → 该组当前视角/纹理下确实无法建立跨视频身份（诊断：10/26 个地标，Ring MIO 0.409）。

## 3. 未完成（如实）

1. **G03/G06 的 M2/M3b、评价与新旧对比未完成**：进程在 H 候选之后被会话预算终止（无 `SUMMARY.json`、无 `ba/*.npz`）。
2. **8 类真实图全部 `NOT_EXECUTED`**（无图，未用示意图代替）。
3. **H 候选的极线评分为空**：`epipolar_score()` 的 `fit_ids` 传入的是 ids_rows 行号，而函数按 `r.ref_index` 过滤 → 全部被过滤掉，`epi=None`、score=1e6+ring。**这是本轮发现的真实缺陷（D7）**，导致 H 排序实际上只按 Ring。
4. W0 自动补算在 G06 上本轮**未触发**（G06 W0 已由 028 写入 `runs/.../w0`，本轮直接复用）；代码路径存在但**未被端到端验证**（D8）。

## 4. 缺陷登记（EXECUTION_DEFECT_REGISTER 摘要）

| # | 缺陷 | 影响 | 状态 |
|---|---|---|---|
| D1 | `RingRenderer` 模块级 `R`/`VIEWS` 被多次覆盖 | 早期 KeyError | 已修（每组建一次 renderer，VIEWS 一次写全） |
| D2 | ring 证据目录与 `R` 不一致 | FileNotFoundError | 已修（symlink `rep/ring` → `ring/`） |
| D3 | 相机集未限制到选中视角 | KeyError（未载入视角） | 已修 |
| D4 | BA geometry 分支误用 `role[ref]` | KeyError | 已修 |
| D5 | `FTT` 导入位置 | NameError | 已修 |
| **D7** | **极线评分 fit 索引错配** | **H 候选排序只按 Ring（epi 恒空）** | **未修** |
| **D8** | W0 自动补算未端到端演练 | 该门控缺证据 | **未验证** |

## 5. 结论

- 统一工程骨架（上下文、真实哈希、W0 自动入口、统一视角选择、2D 验证身份、FIT/HOLDOUT、H 候选、单 BA）**已实现并可运行到身份/H 候选阶段**；
- 但本轮**没有完成**要求的 G01/G03/G06 端到端（H 初始化 → 共同三角化 → Joint BA → FIT/HOLDOUT → 8 图），
  因此 `UNIFIED_PIPELINE = PARTIAL`，`NEW_METHOD_VALIDATION = INSUFFICIENT_EVIDENCE`；
- 最关键的下一轮修复：D7（极线评分索引）、D8（W0 自动补算演练），随后重跑 G03/G06 的 BA 与评价并出图。
