# M2F3 FINAL REPORT — W0 与准入主线收敛

**Branch:** `exp/TASK-M2F3-W0-AND-ADMISSION-CONVERGENCE-001`  
**Output:** `runs/m2f3_admission_convergence/`

## 0. 结果概览

| 组 | S0/S1/S2 cam | T10/T11 targets | 唯一 HERO | A→B pairs | 覆盖中位 | RGB MAE 中位 | CAD-HERO signed/MAE 中位 |
|---|---:|---:|---:|---:|---:|---:|---:|
| G01 | 0/5/20 | 21/12 | **16** | 48 | 0.898 | 13.23 | −0.275 / 4.443 mm |
| G03 | 6/18/20 | 38/22 | **20** | 60 | 0.938 | 9.91 | −0.944 / 3.092 mm |
| G06 | 8/15/24 | 35/23 | **26** | 78 | 0.940 | 9.88 | +0.263 / 0.948 mm |

共 **62 个唯一新 HERO**、**186 个标准 B 相机 A→B 对**。G03 的 14 个旧曲面已保留其良好一致性；G01/G06 由本轮统一流程自然产生新结果，未针对组名调整。

## 1. 六项工程修改

### P0-1 W0 恢复
- G01/004 与 G06/004 实际执行 `m2b_global_branch` 候选搜索（正确 R10=5.6/0.6），再用 `run_w0_camera --init-poses` 执行 BA。
- 两次真实结果均为 `COMPLETED_LIMITED / NO_ACCEPT_CAMERAS`（G01 0 accept，G06 0 accept），证据在 `logs/a2_*.log`、`logs/w0_a2_*.log`。未把未采用的姿态写入正式选择。
- G06/004 另外执行真实候选补帧：从原始视频生成 4 个中间帧，使用 raw-label recovery sidecar（明确标记，不冒充 DXY clean），14-view W0 达到 **COMPLETED_VALID，8 ACCEPT**。该恢复包接入正式选择。

### P0-2 S0/S1/S2
- S0 恢复冻结 YAML 的 positive_depth **0.95**（移除旧 0.99），并保留 2 mm triangulation baseline 字段检查（缺失时明确记录，不伪造）。
- S1 不再只是 S0 放宽：加入 graph/local frame evidence；S2 独立于 S1，使用 frame-valid 非 branch 的局部候选，最终由 T13 四相机几何检查决定。
- 行为测试 `tests/test_m2f3_convergence.py` + 旧回归共 **26 passed**。

### P0-3 候选不足恢复
- G06/004 原 S2 10 个候选仍无合法 T13 tuple；实际补 4 个原始视频中间帧并重跑 W0，得到 14-view、8 ACCEPT，再执行同一 T10/T11/T13 → HERO 路径。没有降低三支持要求或使用插值相机。

### P1-1 anchor
- 移除固定 `VIEW_SELECTION_016` anchor 的依赖；本轮 anchor 由当前合法池的方向中心性生成（`CURRENT_DATA_ANGULAR_ANCHOR`）。
- 模型中心优先使用历史 INITIAL mesh 中心（G01/G03/G06 可用时），不可用才用 W0 场景代理。历史精确 anchor 仍为 **false**，没有把当前 anchor 冒充历史 anchor。

### P1-2 T13
- 保留历史 SIFT/mutual/极线/视差/内点评分。
- 明确撤销此前误把“相机中心 2 mm”当门控的实现：2 mm 是三角化基线字段，不是相机中心距离；改用 T13 的真实极线、视差、内点和三支持方向检查。

### P1-3 通用入口
- `groups_from_arg` 改为接受当前 PREPARED Manifest 的真实 group_id，并动态发现视频；不再要求 G01/G03/G06 固定名单或 004/005 固定列表。

## 2. 结果解释

- **G01**：从 0 个合法 tuple 提升到 16 个（S2 16），覆盖中位 0.898；但 16 个 CAD-HERO 中最小仍为 **−17.28 mm**，严重悬空没有消失。不能因为获得 HERO 就宣称几何修复。
- **G03**：20 个新 HERO、60 对，覆盖中位 0.938，保持条件性良好；旧 M2F2 的 14 个曲面未被覆盖。
- **G06**：补帧恢复后 26 个 HERO、78 对，覆盖中位 0.940，CAD-HERO 中位 +0.263 / MAE 0.948；这是恢复路径有效性的实际证据，但仍不是 GT 精度证明。
- 同视频多曲面一致性 371 个 pair 已计算；跨视频不混合。

## 3. 未闭合

- W0 A2 候选/BA 在 G01/004、G06/004 实际执行但均 0 accept；正式选择仍使用原 W0 或 G06 补帧 W0。A2 的“有效修复”未成功。
- 4 个 G06 recovery 帧不在 M2F2 的 766 行 `FRAME_REGISTRY` 中；`W0_INPUT_IDENTITY_VERIFIED` 仍不能整体标 true。
- 历史精确 anchor/INITIAL 中心未完全恢复（anchor_exact=false）。
- 未运行 39 组，未做主体重建、融合或跨视频研究。
