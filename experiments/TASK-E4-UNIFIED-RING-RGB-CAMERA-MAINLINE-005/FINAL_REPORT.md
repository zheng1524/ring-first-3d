# TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005 — FINAL_REPORT

**STATUS: `AWAITING_RA_REVIEW`** · 统一相机主线已建立并跑通全部 10 段视频；最终相机已独立冻结，**未进入 HERO/Body**。

---

## 0. 一句话结论

**统一性是成立的：10/10 视频走同一文件、同一 `config.json`、同一 Ring 门限（3.0 px）、同一版本评分权重；源码静态测试禁止 `if group ==`。**
**但统一不等于全线达标：74/80 FIT 视角通过 Ring 门限，只有 8 个达到独立 RGB 验证，66 个为 `USABLE_WITH_CAUTION`，5 个 `INVALID`，1 个 `INSUFFICIENT_EVIDENCE`。**

与历史相比最重要的两处变化：

1. **最终相机不再是逐视角 `recover()` 覆盖 BA 的结果**，而是多视角 BA 解本身经 3 px Ring 门限后冻结 → 消除了 004 审计发现的"覆盖导致 G03 final 159 px"的结构性缺陷。
2. **G03/005 从"0 个可下游视角"变为 8/8 通过门禁、2 个 VALIDATED**；**G05/005 从"NOT_RUN"变为 7/8**。

代价也要写清楚：统一 BA 方案的 **RGB 多视角一致性总体只到中位 8.7 px**，远未达到"全部可验证"的水平。

---

## 1. 统一架构（已实现）

见 [UNIFIED_CAMERA_ARCHITECTURE.md](UNIFIED_CAMERA_ARCHITECTURE.md)。实现为单一入口 `code/unified_camera.py`：

```
8 个 FIT 视角（RGB/Mask/K）
  → Ring 观测（native.observe，原始 Mask 不改）
  → Ring 5DOF 候选（native.camera.recover，无 RGB）
  → RGB 跟踪（冻结 V6 track005；held = 每 5 取 1）
  → 多视角初始化（冻结 V6 initialize，2 个版本）
  → 联合 BA（冻结 V6 BA：特征重投影 + Ring 残差 + 时间先验 + 正性）
  → 训练侧版本评分（Ring + 训练特征 + BA 目标 + 收敛标志；held 不参与）
  → 逐视角 3 px Ring 门禁
  → held 独立评价（只决定状态，不反选）
```

**最终相机 = 选中版本的 BA 相机**。`recover()` 只提供候选分支，不再逐视角覆盖。

**唯一配置**：`code/` 下的 `metrics/RUN_CONFIG.json` 记录冻结 `config.json` 的 SHA256、评分权重、门限与全部来源哈希。

---

## 2. 全量结果（10 段视频 × 8 FIT 视角 = 80）

| 实例 | Ring MAE 均值 | 门禁通过 | VALIDATED | USABLE_WITH_CAUTION | INVALID | 选中版本 |
|---|---:|---:|---:|---:|---:|---:|
| G01/004 | 1.28 | 8/8 | 0 | 8 | 0 | v0 |
| G01/005 | 0.97 | 8/8 | 0 | 8 | 0 | v0 |
| G02/004 | 2.48 | 6/8 | 0 | 6 | 2 | v1 |
| G02/005 | 2.01 | 8/8 | 0 | 8 | 0 | v1 |
| G03/004 | 0.88 | 8/8 | 0 | 8 | 0 | v0（ambiguous） |
| **G03/005** | **0.75** | **8/8** | **2** | 6 | 0 | v0 |
| G05/004 | 1.90 | 6/8 | 0 | 6 | 1(+1 INSUFF) | v0 |
| **G05/005** | **1.95** | **7/8** | **1** | 6 | 1 | v0 |
| G06/004 | 1.20 | 7/8 | 0 | 7 | 1 | v0 |
| **G06/005** | **0.67** | **8/8** | **5** | 3 | 0 | v0（ambiguous） |

- Ring MAE 全样本：中位 **0.976** px、p95 **3.258** px、最大 **9.943** px。
- 独立 held 重投影（逐视角）：中位 **8.73** px；按实例中位从 **2.47**（G06/005）到 **28.10**（G02/005）。
- 状态合计：VALIDATED **8** / USABLE_WITH_CAUTION **66** / INVALID **5** / INSUFFICIENT_EVIDENCE **1**。

**版本评分实例**：G03/005 v0=1.409 vs v1=6.469（选 v0，正确）；G06/005 v0=0.970 vs v1=0.976（差 <5%，标 `AMBIGUOUS_VERSION`，取 v0）；G03/004 同样 ambiguous。

---

## 3. 七个问题的回答

### Q1. 是否建立了真正统一的 Ring+RGB 相机恢复流程？

**是。** 一个入口、一份配置、一条调用链；`tests/test_unified.py` 用静态检查断言源码中不存在 `if group ==` 分支，且不包含 `import dxy` / `'body'` / `'hero'` / `'gt'` 路径。10 段视频全部实际执行同一代码路径（日志 `metrics/FULL_RUN.log`）。

### Q2. G01 的成熟相机结果能否复现？

**Ring 约束可以复现，RGB 多视角一致性只能部分复现。**
G01/004 Ring MAE 均值 1.28 px、G01/005 0.97 px，8/8 通过门禁，与历史（001 的 45/56、Ring MAE 0.45–1.58 px）同量级。但我们的独立 held 中位 8.53/9.56 px，**高于 V6 当年 v0 的通过水平（15/22 VALIDATED）**，因此不能宣称"完全复现成熟结果"。
差异来源明确：本轮统一使用 **8 个 FIT 视角**做标定（V6 用 22 帧），轨迹数与基线都更少。

### Q3. G03 的 RGB 多视角一致性是否改善？

**显著改善。** 002 的最终相机在 G03/005 上的 held MAE 为 **159.2 px**（004 审计复算），本轮统一 BA 为 **6.13 px 中位**，且 8/8 通过 Ring 门禁、2 个视角达到独立验证。这与"取消逐视角覆盖"直接相关：版本 v0 的 Ring 均值 0.75 px，v1 被训练侧评分正确排除（6.469 vs 1.409）。

### Q4. G05 的 Ring Mask 异常是否得到合理处理？

**合理，但方式是"不删除、只记录"。** 本轮统一采用 **M0 原始观测**（不启用最大连通域），因为 004 审计已证明 M1 在 2/4 多分量视角上反而变差。G05/005 仍得到 **7/8** 通过门禁的相机（002 为 6/8 且下游未运行），其中 1 个 VALIDATED。
孤立分量所在的 `G05_v005_raw00404` 仍然 **INVALID**（Ring MAE **9.94 px**），与本轮未启用最大连通域一致；其余 7 个视角照常输出。本轮**没有**为它做任何特殊处理，也没有为 G05 增加任何规则，符合"不按病例写规则"的要求。

**全部 5 个 INVALID 视角**：G02/004 raw00816（3.06 px）、G02/004 raw00837（3.38）、G05/004 key04_raw00542（3.25）、G05/005 raw00404（9.94）、G06/004 raw00874（3.83）；另有 G05/004 raw00676 为 `INSUFFICIENT_EVIDENCE`。其中 4 个只是略超 3 px，**不构成"相机完全错误"**，只是未通过正式门限。

### Q5. 十段视频分别保留了多少可靠视角？

见 §2 表：门禁通过 **6–8/8** 每实例；其中 VALIDATED（同时满足 Ring 与独立 RGB）为 0–5 个。**"通过门禁"与"几何验证"必须分开读**：66 个视角属于"可用但需谨慎"。

### Q6. 哪些问题无法通过现有 Ring+RGB 信息解决？

1. **RGB 一致性整体偏弱**：即使 Ring 很好，held 中位仍 8.7 px。原因是 8 视角、短基线、部分视频特征稀少（G06/005 仅 87 条轨迹 / 18 条 held）。
2. **G03/004 的 held 27.5 px**：该视频的 Ring 门禁 8/8 通过，但 RGB 关系不自洽；现有信息不足以判定是相机还是匹配问题。
3. **全局规范差异**：与 002/001 的对照旋转差在 G01/004 113°、G02/004 177°、G06/004 179°，属**参考帧与规范定义的差异**，不是错误；但这也说明"跨任务直接比绝对位姿"没有意义。
4. **HOLDOUT 相机本轮未求解**（统一流程只恢复 8 个 FIT）；HOLDOUT 完整性标注为 `NOT_SOLVED_THIS_ROUND`。

### Q7. 哪些相机已经足够可靠，可以冻结并进入下一阶段？

**建议冻结全部 74 个门禁通过视角，并按下表分级使用：**

| 级别 | 数量 | 建议用途 |
|---|---:|---|
| VALIDATED | 8 | 可直接用于下一轮 Body 重拟合的主证据 |
| USABLE_WITH_CAUTION | 66 | 可用于 Body，但必须在报告中标注"未通过独立 RGB 验证" |
| INVALID | 5 | 不得进入下游 |
| INSUFFICIENT_EVIDENCE | 1 | 不得判为失败；标为证据不足 |

**不建议**在 RA 批准前进入 HERO/Body；也不建议把本轮相机称为"世界坐标真值"。

---

## 4. 与历史相机的对照

`FINAL_VS_HISTORY_CAMERAS.csv`（78 个可对照视角）：

| 实例 | 旋转差均值 | 中心差最大 |
|---|---:|---:|
| G01/004 | 113.3° | 48.8 mm |
| G01/005 | 22.6° | 9.5 mm |
| G02/004 | 176.6° | 34.1 mm |
| G02/005 | 15.3° | 5.2 mm |
| G03/004 | 16.8°（max 122.4°） | 84.2 mm |
| G03/005 | 166.4° | 71.3 mm |
| G05/004 | 18.0° | 9.4 mm |
| G05/005 | 157.2° | 46.4 mm |
| G06/004 | 178.6° | 4.6 mm |
| G06/005 | 14.0° | 6.1 mm |

**读法**：179°/177°/113° 这类差异是**全局规范**（参考帧不同、法向分支不同），不是相机错误；15°–23° 的差异才是同规范下的真实修正量。**不得据此断言哪一方更准确**——两者都没有位姿 GT。

---

## 5. 交付物

| 文件 | 内容 |
|---|---|
| `UNIFIED_CAMERA_ARCHITECTURE.md` | 唯一架构、规范定义、状态语义、禁止项 |
| `CAMERA_PROVENANCE.csv` | 80 视角的来源（Ring/RGB 哈希、参考帧、BA 版本、gauge） |
| `CAMERA_QUALITY_MATRIX.csv` | 80 视角的四层状态与全部指标 |
| `VIEW_COVERAGE_MATRIX.csv` | 10 实例覆盖（含 HOLDOUT 说明） |
| `FAILURE_REGISTRY.csv` | 失败实例/阶段 |
| `INPUT_MANIFEST.csv` | 80 输入的路径与 SHA256 |
| `FINAL_VS_HISTORY_CAMERAS.csv` | 与 002/001 相机的旋转/中心差 |
| `metrics/RUN_CONFIG.json` | 唯一配置、权重、环境、源码 SHA |
| `runs/<G>/<V>/` | Ring 候选、tracks、BA_0/1、VERSION_SCORES、CAMERA_RESULT、VALIDATION、CAMERA_FREEZE |
| `visualization/figures/*.png` | 6 张静态图（无 HTML） |
| `code/unified_camera.py` | 唯一入口 |
| `code/tests/test_unified.py` | 8 项回归（静态契约 + 三角化自检 + 观测契约） |

**复现：**

```bash
cd <ws>/experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code
export PYTHONPATH=<ws>/src:.
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY unified_camera.py                        # 全部 10 段
$PY unified_camera.py --group G03 --video 005
$PY -m unittest discover -s tests -v         # 8/8 pass
$PY make_figures.py
```

---

## 6. 科学边界（已遵守）

- 未使用 Body、GT、HERO 恢复相机；源码静态测试断言不含相关路径。
- 未运行 HERO/Body；未修改 DXY（未 import）。
- 未覆盖 001/002 的冻结相机与预测；本任务只写自己的 `runs/`。
- 未按病例选择算法/参数/门限；未使用 HOLDOUT 选择版本。
- 3 px Ring 门限保持不变。

---

## 7. 已知局限（必须与结论同时阅读）

1. **held 评价使用的是训练时的同一批轨迹来源**（held 轨道从未进入初始化/BA，但来自同一段视频的同一跟踪过程）。它是"独立于求解"的，但不是"独立于数据源"。
2. **标定视角从 V6 的 22 帧缩减为 8 帧**（统一规则），这是本轮 RGB 一致性总体弱于 V6 的主要原因，属**设计取舍而非缺陷**；若要提高，需要在不违反"同一规则"的前提下扩大标定视角集——这是下一轮的候选议题。
3. **版本评分权重是本轮预先声明的**（1.0/0.1/0.02/0.5），未做敏感性分析；只有 G03/005 与 G06/005 两例能区分版本。
4. **全局规范差异无法用绝对位姿验证**；本轮只能保证"同一段视频内部一致"。
5. 80 个视角中 6 个未通过门禁，其中 G05/004、G06/004 的失败原因未逐视角归因。
