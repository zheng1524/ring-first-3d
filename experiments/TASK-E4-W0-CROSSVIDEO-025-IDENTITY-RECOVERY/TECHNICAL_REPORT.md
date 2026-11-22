# TASK-E4-W0-CROSSVIDEO-025 — TECHNICAL_REPORT

```
SOURCE_REUSE_GATE:        PASS（features020.make 真实调用）
CONTROLLED_GATE:          PASS（8/8 测试，含 024 的 A2/A3/A6/A7）
SPLIT_GATE:               PASS（HOLDOUT 未进入身份链）
IDENTITY_BUILD:           PASS（12 selected / 12 rejected，逐级数量可查）
CONSISTENCY:              PARTIAL（4 内点，但 Ring 冲突 + 种子不稳定）
HOLDOUT:                  PASS（28 个有效，中位 6.08 px）——024 的 0 是程序缺陷，已修
RING:                     HYPOTHESIS_STATUS = RING_CONFLICT（不是身份判决）
IDENTITY_VALIDATION:      BLOCKED
CROSS_VIDEO_GEOMETRY_ACCEPT: NO
BODY_CROSS_VIDEO_ADMISSION:  NO
G01/G05:                  BLOCKED_BY_W0_ADMISSION（同一入口，未改门限）
```

## 1. 历史 020 真的跑起来了

按源码核对后的顺序执行（`core/p1_020_chain.py`，35 s）：

```
features019.landmarks(fit4,'CROSS_004')            -> 317
features019.cross(fit4,fit5,lm4,'CROSS')           -> 21 对 / 220 观测；PnP 1/8
features019.landmarks(fit5,'INDEPENDENT_005')      -> 806
features020.make('CROSS',fit5,fit4,'REVERSE','INDEPENDENT_005')
     内部再跑 cross(fit5,fit4,lm5,'REVERSE')        -> PnP 3/3
     -> 24 个投票候选 -> 12 选中（≥2 视角/侧 + 一对一）/ 12 拒绝
```

只用 FIT 视角；`common.py` 唯一改动是 `REPO` 路径。

## 2. 12 个 020 身份 + 三维一致性

| 分类 | 数量 | 特征 |
|---|---:|---|
| `RIGID_CONSENSUS_SUPPORTED` | **4** | 3D 残差 0.41–0.97 mm；HOLDOUT 中位 3.4–6.1 px |
| `RIGID_CONSENSUS_CONFLICT` | 8 | 3D 残差 2.4–15.1 mm；HOLDOUT 50–85 px（无有效观测者除外） |
| 全部候选 `HYPOTHESIS_STATUS` | `RING_CONFLICT` | Ring MAE 1.04 px → 6.84/5.77 px |

**多假设诊断**：seed 0 与 seed 1 的 H 相差 **15.8 mm / 31°**；seed 2–4 相互一致但与 seed 0 差 3.4 mm / 8.3°。
4 个内点不足以稳定确定刚体变换 → 候选 H 只能作为诊断假设。

## 3. HOLDOUT 修复

024 的 `n=0` 是**程序缺陷**：单描述子查询无法通过 `match_desc` 的 mutual（反向 knn 只有 1 个候选），
且反向分支传了 `None`。025 改为**批量描述子**匹配并按 `H` / `H⁻¹` 双向投影：

| 类别 | 004→005 | 005→004 |
|---|---:|---:|
| MATCHED_VALID | 12 | 16 |
| MATCHED_HIGH_ERROR | 0 | 4 |
| NO_DESCRIPTOR_MATCH | 64 | 16 |

有效 **28**，中位 **6.08 px**，p90 **7.63 px**。未匹配不记 0、不判错。

## 4. 回答

**Q1 历史 020 是否真正恢复？** **是**（`features020.make` 实际调用，含其内部反向 `cross`、投票与一对一；
输出 `CROSS_NAMED_3D_TRACK_PAIRS.json` 原始文件已保存）。

**Q2 020 多视角投票在当前 W0 找到多少身份？** 24 个投票候选 → **12 个选中**（≥2 视角/侧、一对一），12 个因视角支持不足被拒。每侧证据来自 3 个 004 FIT 视角、3–12 次 vote。

**Q3 相比 024 的 15 个描述子候选，020 是否减少明显错误？** 是：020 的候选 3D 残差中位 4.39 mm（024 为 6.37 mm），
且每个候选都有可审计的多视角证据；但两者 RANSAC 内点都是 4 个，**不能**说 020 已被证明更正确。

**Q4 哪些身份有真实多视角支持？** 全部 12 个都有（每侧 ≥3 个 FIT 视角、vote 3–12）；
但只有 4 个同时满足 1 mm 刚体一致（#1,#3,#7,#9，残差 0.41–0.97 mm）。

**Q5 哪些只是与某个 H 不一致、不能确定错误？** 另外 8 个（#0,#2,#4,#5,#6,#8,#10,#11）——
它们有多视角支持但与当前 4 内点的 H 冲突；由于 H 本身不稳定且与 Ring 冲突，**不能**判为错误匹配。

**Q6 HOLDOUT 是否恢复正常？** **是**（28 个有效观测；024 的 0 是缺陷）。

**Q7 Ring 与三维冲突是否解释清楚？** 部分：Ring 冲突是**候选 H 的属性**（`HYPOTHESIS_STATUS=RING_CONFLICT`），
已与身份状态解耦；但 020 的 M/I/C/O Ring 目标仍未接入，`torus_contours` 只是近似。

**Q8 是否只有一条正式主线？** **是**：`run_cross_video_registration.py --group G --stage identity-validation`，
G01/G05 正确返回 `BLOCKED_BY_W0_ADMISSION`；无组专用路径，配置由入口解析并下发。

**Q9 是否有充分证据建议下一轮启动 H 优化？** **NO**。阻断：① 4 个内点 + 种子不稳定；② 候选 H 与 Ring 冲突；
③ 8 个身份处于"多视角支持但与 H 冲突"的未定状态；④ Ring 目标仍是近似；⑤ 时间簇未切分。

## 5. 六类可视化（真实数据，PNG 已入库）

`runs/G03/VISUALIZATIONS/`：`01_identity_method_comparison.png`、`02_multiview_identity_evidence.png`
（每个身份 2 个真实 004 + 2 个真实 005 视角裁剪，+ 标出精确 SIFT 点）、`03_3d_track_correspondences.png`、
`04_ring_hypothesis_comparison.png`（真实 005 Ring 观测 vs W0/H/H⁻¹ 预测轮廓）、
`05_holdout_bidirectional_reprojection.png`、`06_identity_audit_summary.png` + 同名 CSV。

## 6. 复现

```bash
N=experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$N/core:src $PY $N/run_cross_video_registration.py --group G03 --stage identity-and-visuals
PYTHONPATH=$N/core:src $PY -m unittest discover -s $N/tests -v
```
