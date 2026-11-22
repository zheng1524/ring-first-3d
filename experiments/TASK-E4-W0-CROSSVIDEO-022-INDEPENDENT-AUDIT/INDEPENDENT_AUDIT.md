# INDEPENDENT_AUDIT — TASK-E4-W0-CROSSVIDEO-021

**审计对象**：`bfd9c622bb2660b4a2e4c2ffdbadbb72b19971fd`（`exp/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE`）
**审计者**：独立审计智能体（未参与 021 开发）
**结论**：`AUDIT_PASS`（审计完成且有证据）；**021 的跨视频几何 `NOT ACCEPTED`**。

---

## 1. 一句话

021 修复了 **SE(3) 参数化、Sampson 定义、累计边界** 三个真实数学错误（可复现验证），
但它的"梯度已由 autograd 验证""resume 可复现""Ring 对称性已验证""A2/A6 受控实验通过"**不成立**；
`HOLDOUT` 只隔离了 005 侧，004 侧 6/6 泄漏；
且正式目标只是 **Ring(torus_contours)+EPI+Prior**，**没有调用任何 019/020 历史模块，没有 `L_F`**。

## 2. 已验证为真的修复（可独立复算）

| 项 | 证据 | 结果 |
|---|---|---|
| SE(3) 六自由度 | 差分雅可比秩=6；纯平移不改 R；纯旋转 t=0；与 `scipy.linalg.expm` 1e-12、与 `pytorch3d.se3_exp_map` 1e-9 | **真实** |
| 标准 Sampson | 分母 `sqrt(四项平方和)`；与点到极线距离一致 | **真实** |
| 累计边界 | `H_cand·H_seed⁻¹`，实测 0.163 mm / 3.546° < 1.2/10 | **真实** |
| 数据 fail-closed | 缺 admission 抛错、UNKNOWN 排除 | **真实**（但对 UNKNOWN 输入无单测） |
| REJECT 分支 | `if not ok: q=old_q; m,v=old_m,old_v` | 代码存在，**外部不可观测** |

## 3. 被夸大的声明（P0）

| ID | 声明 | 实测 | 证据文件 |
|---|---|---|---|
| P0-A | "autograd 与有限差分一致，梯度已验证" | `torch_objective.py` 与 `shared_se3.objective` **不是同一个函数**：无 Ring 项、EPI 权重 1.0（正式 0.02）。同数据同 q：**0.00211 vs 0.16752** | `results/T1_objective_mismatch.json` |
| P0-C | "resume 等于不中断" | `optimize(seed, ring, pairs, K, iters, verbose)` **没有 checkpoint 参数/返回值**；该测试是"同一调用跑两次" | `results/T3_optimizer_state.json` |
| P0-C | "Adam 拒绝后回滚已验证" | 断言只在 `accepted_steps==0` 时执行；`m/v` 是局部变量，外部无法验证 | 同上 |
| P0-F | "per-view K" | `core/run_corrective.py:13/93` 用模块级硬编码 K；`w0_adapter.py:55` 的 `source_sha` 是**路径字符串**；`cross_video_matches.py:33` 的 `n_raw=len(ka) and len(kb)` 是 int 而非乘积 | `results/T4_input_provenance.json` |
| P0-G | "三组同一代码" | G03 `code_sha=54455c57…`，G01/G05 `070710d5…`；`config_sha` 全为 `null`（`config/UNIFIED_PROTOCOL.json` 的 mtime 18:20 晚于 G03 15:46 约 2.5 h） | `BASELINE_LOCK.md` mtime 表 |

## 4. 受控实验的有效性（P0-B）

| 用例 | 问题 | 证据 |
|---|---|---|
| A2 纯平移 | 观测在 **identity** 姿态生成，数据里没有 `H_true`；`L(identity)=0`，报告值 0.008 mm 只是 `‖H_true‖` 残差 | `results/T5_controlled_validity.json` |
| A3 混合 6DoF | 只"记录" 5.98° 误差，**没有断言**；构造端的符号约定还要修正 | `core/controlled.py` |
| A6 Ring 对称 | **同时**旋转相机与观测（`Cc=yy@C4` 且 `pts=torus_contours(Cc)`），不变性是恒等的，不是可辨识性证明 | 同上 |

## 5. 真实数据协议（P1）

- **匹配阶段**：`cross_video_matches.collect` 只做 SIFT→ratio 0.75→背景 mask；**无 mutual、无 RGB-RANSAC、无多视角轨迹、无三角化**。
  96 对 / 3749 匹配；FIT 48 对、HOLDOUT 48 对。
- **残差**：最终 H 上中位 4.59 px、**p95 156.1 px**、>50 px 占 **16.6%**（`results/T6_provenance_leakage.json`）。
- **泄漏**：004 的 6 个视角**全部**同时出现在 FIT 与 HOLDOUT（只有 005 分了奇偶）。
  故 `HOLDOUT 4.538 px` 只证明"未见 005 视角"的泛化，**不证明 004 侧**。
- **G01/G05**：见 `W0_GROUP_DIAGNOSTICS.md`；G01 是 `HELD_P95` 尾部（14+15），G05 是 `INSUFFICIENT_TRACKS`（13+16，held_n 中位 13–16 < 20）。
  `positive_depth` 语义问题经复核**在本数据上数值恰好一致（均 1.0）**，不影响准入结论。

## 6. 历史源码复用（P0-D/P0-E）

`grep` 全部 `core/*.py`：**没有** import `features019/features020/ring020/objective020/optimize020/gate020/feature_gate020`。
`shared_se3.py:55` 注释明说用 `torus_contours` 代替 `RingRenderer`。
因此 021 = **Ring(native)+EPI+Prior 诊断**，不是 020 R3；`L_F` 在 `RESULTS.json` 里是字符串 `"BLOCKED: ..."`，没有进入目标。

## 7. 结论

| 判定 | 值 |
|---|---|
| AUDIT | `AUDIT_PASS` |
| 021 数学修复（SE3/Sampson/边界/fail-closed） | `VERIFIED` |
| 021 "梯度/resume/Ring 对称/受控 A2/A6" 声明 | `NOT VERIFIED / OVERSTATED` |
| 021 是否完整 020 R3 | `NO` |
| 021 HOLDOUT 是否双侧独立 | `NO`（004 泄漏） |
| CROSS_VIDEO_GEOMETRY_ACCEPT | `NO` |
| BODY_CROSS_VIDEO_ADMISSION | `NO` |
