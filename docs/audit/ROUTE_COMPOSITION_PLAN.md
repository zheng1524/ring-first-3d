# ROUTE_COMPOSITION_PLAN — 第一轮收紧组合表（待人工批准）

**状态：`PENDING_HUMAN_APPROVAL`**
**Scope:** Ring-First 3D 现有实现 → 统一主线的第一轮组合方案。
**Workspace HEAD:** `8b0c166ef5a2310bcdacbc4eae68198ad6530edc`
**Code changes:** 无。本表批准前不写生产代码。

---

## 0. 门禁结论（必须先读）

按 `docs/registry/MODULE_PROMOTION_POLICY.md` 与 `registry/routes.yaml` 的规则，正式流程只能组合 `confirmed` 或 `frozen` 路线。

当前：

- `confirmed = 0`
- `frozen = 0`
- `candidate = 12`
- `exploring = 9`

因此**现在不能声明任何“正式 pipeline 已组合完成”**。本表的作用是：

1. 明确每个阶段应使用哪条现有路线；
2. 明确哪些阶段只是 glue/ADAPT；
3. 明确哪些阶段是 GAP，本轮不得开发；
4. 批准后，先把 **M1（单视频相机）** 收紧并冻结，再把 M2-M4 作为研究候选继续推进。

> 批准本表 ≠ 冻结任何模块。冻结需要单独的验收证据与人工批准。

---

## 1. 组合表

图例：**REUSE** = 直接调用现有入口；**ADAPT** = 保留算法主体，仅加边界适配；**GAP** = 现有实现不满足能力，暂停生产开发。

| 阶段 | 现有 route_id@version | 入口 | 输入输出 | REUSE/ADAPT/GAP | smoke test |
|---|---|---|---|---|---|
| **0. Provenance（横切）** | `rf-provenance@1` | `tools/check_module_provenance.py`, `tools/registry_check.py` | 源码/产物路径 → SHA256 + 状态诊断 | **REUSE + ADAPT**（需覆盖 docs registry 与输入闭包） | `python tools/registry_check.py` exit 0；028 RUN_MANIFEST 309/309 匹配（已实测） |
| **1. Input** | `rf-input-prepared@1` | `experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/code/prepare.py` | 原始视频 + 分组 → `PREPARED.json` + per-view cache | **REUSE**（读取已生成的 prepared 产物） | 对 G01/G03/G05/G06 各读一个 `PREPARED.json`，views>0、cache 存在、K 有限 |
| **2. Video Preparation** | `rf-input-prepared@1` | `prepare.py` / `prepare_views.py` | 原始帧 → RGB/labels/K 缓存 | **ADAPT**：补一个正式 prepare 入口并把 prepared 哈希写入 W0 manifest | 同一输入重复 prepare，RGB/labels/K 哈希一致 |
| **3. Ring Geometry** | `rf-native-ring-cad@1`（正式候选）；`rf-ring020-mesh-cad@1`（028 实际使用） | `src/.../native/camera.py::torus_contours`；`ring020_026.py::RingRenderer` | c2w + K + CAD → I/O/C 像素曲线 | **ADAPT**：先用等价性测试决定唯一 Ring 定义；不得两套并行进入正式线 | 同一 pose/K/CAD 下两套曲线最大像素差 < 约定阈值；3-view `ring-cad-inner-outer` fixture PASS |
| **4. Single-Video Camera** | `rf-w0-camera@1` + `rf-frozen-tracks005@1` + `rf-frozen-ba-local-ring-sfm@1` | `tools/run_w0_camera.py --stage all` | prepared + tracks → B0/W0 c2w + admission | **REUSE**（M1 唯一正式入口） | G03/005：16/16 ACCEPT，ring 0.828765，held 0.980167，p95 3.209369（已实测） |
| **5. Camera Quality** | `rf-camera-admission@1` | `camera_mainline/code/camera_admission.py::decide` + frozen policy | per-view metrics → 4 状态 | **REUSE**；下游几何必须只消费 `accepted_cameras.npz` | 合成阈值上下界测试；G03/005 16 ACCEPT；G06/005 0 ACCEPT（已实测） |
| **6. Cross-Video Matching** | `rf-features019-crossvideo@1` | `features019.matches`（pin lineage/固定副本） | two views → index pairs + MAGSAC + F | **REUSE（pinned copy）** | 两个 G03 视角匹配：index 在界内、RANSAC 有 inlier；RGB_SHA256 一致 |
| **7. View Selection** | `rf-view-selection-028@1` | `u028c.select_views` | W0 cameras + SIFT + Ring → 每视频 N 视角 | **ADAPT**：强制 ACCEPT 过滤；跨视频联合重叠选择是 **GAP**（下一阶段） | 选中视角 ⊆ ACCEPT；G01/G05/G06 因 0 ACCEPT 直接 BLOCKED（当前 G03/G06 不满足） |
| **8. Identity Construction** | `rf-identity-028@1` | `u028c.build_identities` | matches + landmark maps → IDENTITIES/SPLIT | **ADAPT**：增加失败/冲突诊断、identity-keyed X、最小多视角支持 | G03 至少 1 个多视角身份；注入冲突匹配 → `GEOMETRIC_CONFLICT`；无 NaN |
| **9. H Initialization** | `rf-h-init-ring-epi-028@1`（028）；`rf-h-init-020-yaw-se3@1`（020） | `u028c.ring_candidates`；`tools/run_w0_registration.py` | W0 cameras + Ring + FIT corr. → H（other→ref） | **ADAPT（边界） + GAP（方法）**：028 的 yaw 量化/对称分支是方法问题，不能在收紧阶段改目标函数；020 仅 G03 fixture，不能直接当正式路线 | T02 Sampson 真值 <1e-8、5° 错 H >1px；T07 H 只应用一次；H_init 不能恰好等于 yaw 网格点（当前不满足） |
| **10. Joint BA (H+X)** | `rf-joint-ba-hx-028@1` | `ba_core_r4.BAProblemR4` + `solve_pipeline` M3b | FIT obs + Ring + X0 + H → H,X | **GAP**（frozen `local_ring_sfm.BA` 无 H/X 联合变量）；028 是未批准的 candidate | 合成 6+3N 已知 H/X 恢复，`success=True`；当前 20 nfev/27 参数 `success=False`，不满足 |
| **11. Evaluation** | `rf-eval-fit-holdout-028@1` | `u028c.reproj_stats` / `holdout_stats` | H,X + FIT/HOLDOUT split → median/p90/neg | **ADAPT**：状态机、非有限值、负深度、identity 对齐 | HOLDOUT 不进入优化；非有限观测被计数；G06 194.5px 必须报失败而非 GEOMETRY_OK |
| **12. Visualization** | `rf-figs-028@1` | `core/figs_final.py` | summaries + CSVs → 8-panel PNG | **ADAPT** | 所有声明图存在、PNG、非零；图不作为精度/覆盖验收替代 |
| **13. Local Camera Correction (M5)** | 无 | — | 局部相机修正 + Joint BA | **GAP** | 受控扰动恢复测试（当前 `camvar.released=[]`，未执行） |

---

## 2. 组合后的目标顺序（本轮只到 M1）

```text
Input / PREPARED
  ↓  REUSE (rf-input-prepared)
Single-Video Camera W0
  ↓  REUSE (rf-w0-camera + frozen track005 + frozen local_ring_sfm)
Camera Quality Gate
  ↓  REUSE (rf-camera-admission)  ← 下游必须只读 accepted_cameras.npz
  ├─ 0 ACCEPT → BLOCKED_BY_W0_ADMISSION（G01/G05/G06 本轮预期）
  └─ both sides ACCEPT → 继续（G03）
Cross-Video Matching
  ↓  REUSE pinned features019
View Selection
  ↓  ADAPT (admission filter; joint selection = GAP)
Identity Construction
  ↓  ADAPT
H Initialization
  ↓  ADAPT boundary + GAP method (no algorithm change this round)
Joint BA (H+X)
  ↓  GAP candidate (not frozen; rerun only after convergence fix)
Evaluation
  ↓  ADAPT
Visualization
```

**本轮正式冻结目标只有 M1。** M2-M4 在本轮只允许做“正确性收紧 + 受控重跑”，不允许加入新几何/新目标函数。

---

## 3. GAP 清单（暂停生产开发，等待批准）

| GAP | 缺失能力 | 为什么现有模块不够 | 需要的输入/输出 | 验收测试 | 本轮处理 |
|---|---|---|---|---|---|
| **G1** | 跨视频联合选帧 | `select_views` 只是每视频独立贪心角度覆盖，无跨视频重叠/身份支持目标；T12/T13 是单视频覆盖 | W0 cameras + 跨视频 match graph → 每视频 view set | 选出的视角使跨视频匹配数/身份数最大化；G03 可复现 | 登记，下一阶段 |
| **G2** | 稳健 2D 身份 + 多视角轨迹 | `build_identities` 贪心一对一，5/10 G03 身份只有 1 个 view pair；021 identity 是 G01 背景专用 | matches + landmark graph → identity + support + conflict | 冲突注入测试；多视角支持率报告；无一对一漏配 | 登记，下一阶段 |
| **G3** | 可辨识的 Ring+RGB H 初始化 | 028 目标函数只有 Ring（yaw 不变），epi 只做排序；020 是 G03 fixture | W0 cams + Ring + RGB corr. → H + identifiability status | 合成真值 H 恢复；180° 对称分支被拒绝；G03/G06 状态明确 | 登记，下一阶段（需新版本） |
| **G4** | 收敛的 H+X Joint BA | `local_ring_sfm.BA` 无 H；028 M3b 20 nfev 不收敛，且 Ring 边分配固定在 H_init | FIT obs + Ring + X0 → H,X + convergence | 合成 6+3N 恢复 success=True；真实 G03 至少 60-100 nfev 并检查 rank/条件数 | 登记，下一阶段 |
| **G5** | 局部相机修正（M5） | `camvar` 支持 released，但 028 一直传 `[]`；无修正后验证 | W0 cams + H + X → 局部修正 cams | 受控 0.25/0.5° 扰动恢复；不得吸收 H | 登记，下一阶段 |
| **G6** | 正式 prepare 入口 | `prepare.py` 是实验脚本，W0 只读缓存；manifest.prepared=null | raw video → PREPARED + hashes | 干净目录重放，哈希一致 | 本轮可做（M1 closure） |
| **G7** | Manifest/export 闭包 | W0 manifest 的 tracks_sha256 指向导出目录外，observations 不导出 | output dir → 自包含 manifest | 断网/移走 TASK-015 后仍可复现 | 本轮可做（M1 closure） |
| **G8** | Registry 迁移 | 两处 registry；`registry_check.py` 只读 root | docs registry → validator | validator 对 docs/registry/routes.yaml 通过 | 本轮可做（docs） |

---

## 4. 允许的 glue（批准后）

只允许以下边界工作，不得复制算法：

1. **Admission 边界**：从 `camera_result.npz` 读取 `admission_status`，只保留 ACCEPT；若任一视频 0 ACCEPT，写 `BLOCKED_BY_W0_ADMISSION` 并停止。
2. **路径 pinning**：把 `features019`、`fixed_track_tri`、`ring_energy` 的 import 指向唯一固定副本（优先 lineage / 新 pinned copy），删除对 `027-R6/replay` 的隐式依赖。
3. **Config 接线**：`budget_M2/M3b`、`yaw_step_deg`、`rgb_mode`、`holdout.seed`、`min_view_pairs_multiview` 从 `PIPELINE.json` 读取，并在 SUMMARY 中回显实际值。
4. **状态机**：增加 `BLOCKED_BY_W0_ADMISSION`、`OPTIMIZATION_NOT_CONVERGED`、`TRIANGULATION_FAILED`、`H_INIT_UNOBSERVABLE`；`GEOMETRY_OK` 只在“admission 通过 + BA success + 有限指标”时设置。
5. **Identity-keyed X**：`triangulate_*` 返回 `(identity_id, X)`，BA 用 identity_id 索引，禁止位置索引。
6. **Manifest 闭包**：W0 输出目录包含 tracks/observations 或记录其只读源哈希；028 每个 group（含 blocked）都写 `SUMMARY.json` + `MANIFEST.json`。
7. **测试**：每个边界一个最小测试；测试不得再注入生产入口缺失的 sys.path。

---

## 5. 明确禁止（本轮）

- 不修改 Ring 数学定义、不新增 Ring 损失、不替换 torus 投影器。
- 不修改 H 目标函数、不新增 epipolar 优化项（G3 是下一阶段）。
- 不调整任何组的阈值、视角预算、匹配策略。
- 不重写 `track005`、`local_ring_sfm`、`camera_admission`、`torus_contours`。
- 不创建第二套正式入口。
- 不把 028 的 candidate 结果写成 frozen 或 confirmed。
- 不删除任何历史实验目录/失败结果。

---

## 6. 已执行的验证证据（本表依据）

| 验证 | 结果 |
|---|---|
| 028 RUN_MANIFEST vs 工作树 | 309/309 匹配，0 mismatch，0 missing |
| 028 独立入口 | `ModuleNotFoundError: fixed_track_tri` |
| 028 测试（裸跑/全 PYTHONPATH） | 3 PASS / 1 SKIP（测试自行注入 R6/core） |
| G03/005 W0 回归 | 16/16 ACCEPT；0.828765 / 0.980167 / 3.209369 |
| G03/004 admission | 6 ACCEPT / 10 QUARANTINE |
| G06/005 admission | 0 ACCEPT / 16 INSUFFICIENT_EVIDENCE |
| 028 H init | 45.000°（G03）/ 180.000°（G06），均为 yaw 网格点 |
| 028 Joint BA | G03/G06 success=false，nfev=20，nparams=27/18 |
| 新 routes.yaml | 21 routes；candidate 12 / exploring 9 / confirmed 0 / frozen 0 |
| 隐藏写入 | `TASK-015/runs/G06_004/tracks_source.txt = generated_by_pipeline`（untracked） |

---

## 7. 需要人工确认的事项

- [ ] **A1. 批准本组合表**（阶段 → route → REUSE/ADAPT/GAP）。
- [ ] **A2. 批准本轮唯一冻结目标为 M1**，并批准 M1 的四个 closure 任务（prepare 哈希、tracks/observations 导出、干净 smoke、registry 迁移）。
- [ ] **A3. 批准 028 的有限正确性修复**：admission、config、convergence status、triangulation failure、identity-keyed X、Ring residual 去重；**不批准** H 目标函数修改。
- [ ] **A4. 确认 G01/G05/G06 本轮预期为 `BLOCKED_BY_W0_ADMISSION`**，不做组别特化、不放宽阈值。
- [ ] **A5. 确认 028 old/new 比较改记为 `OPTIMIZATION_NOT_CONVERGED`**，撤销 `MIXED` 科学比较结论。
- [ ] **A6. 批准 registry 迁移路径**：`docs/registry/routes.yaml` 成为权威清单，`registry/routes.yaml` 保留为 legacy（不删除、不静默覆盖）。
- [ ] **A7. 确认本轮不新增任何复杂几何/BA 算法**；G1-G5 只登记为下一阶段开发目标。

**在 A1-A7 得到确认之前，不执行 `executing-plans`，不修改生产代码。**
