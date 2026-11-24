# TASK-M2F2 技术报告：统一主线修复与真实实验

**分支**：`exp/TASK-M2F2-ROOT-CAUSE-CORRECTIVE-003`  
**RUN_ID**：`M2F2-20261124-FINAL-005`  
**代码版本**：`tools/m2f2_unified.py` SHA256 `525bfe5221b72869ff0dca82ec6b0271c3fbf9c7befa97b704fe8101ee8a1b5b`；RUN_ID 收据另记源提交 `6d92aed6cf4a62fe4c97493ea2a5a8c45f6033c8`。  
**实验目录**：`runs/m2f2_root_cause_corrective/`。  
**最终判定**：**三组验收失败；39 组未执行。** G03 在严格门控下完成了条件性的 HERO/几何实验；G01、G06 没有合法的 T13 四相机 tuple，不能报出新的 HERO 或 A→B 指标。历史精确锚点亦未恢复。所有 NaN 均代表 NOT_EVALUABLE，不以零代替。

## 1. 历史实现复用与统一入口

单一入口为 [`tools/m2f2_unified.py`](../../tools/m2f2_unified.py)，依次调用现有 `tools/run_w0_camera.py`（含现有 BA）、冻结的 [`views/selection.py`](../../src/ring_first_3d/views/selection.py) 中 T10/T11/T13 AST 代码、`mainline/native/hero.py` 的官方 HERO 推理、`mainline/native/cleaning.py` 和已有 B 相机重投影。新增 [`views/pipeline_adapter.py`](../../src/ring_first_3d/views/pipeline_adapter.py) 只负责历史输入适配、严格 S0/S1/S2 准入和 T13 证据门；[`mainline/input_identity.py`](../../src/ring_first_3d/mainline/input_identity.py) 负责身份及几何收据。未修改 DXY、HERO、geometry 或 cleaning 的核心算法，未针对任何组调整门限。

G01/G03/G06 分别固定映射至 `GP_Ip_12.0mm_closed_R10_single_refY`、`GP_Ip_20.0mm_closed_R10_single_refY`、`GP_IIa_14.0mm_closed_R10_single_refY`。M2F1 报告中的另外两组为 `GP_Is_9.79...` 和 `GP_Is_14.0...`，因此旧三组指标**不能**作为本轮 G03/G06 的逐组改善比较。

全局身份表核验 73 个已存 W0 包和本轮六个新 W0 包；实际新跑的相机实验仅为上述三组各两个视频。其余 73 包只作身份闭包检查，未伪称本轮重新执行或完成 39 组 HERO。

## 2. 已知问题逐项处置

| M2F1 问题 | 本轮证据与状态 |
| --- | --- |
| `work_A1` 路径误判轨迹身份 | 从各 W0 `manifest.json` 读取真实轨迹文件、PREPARED、源视频和 W0 的路径与 SHA256；验证 track ID 范围、视角顺序、K、c2w。旧 79 包均可按真实路径验证，先前“轨迹不匹配”误报已消除。 |
| 缺 5 条 BRIDGE、PREPARED 依赖目录顺序 | [`FRAME_REGISTRY.csv`](../../runs/m2f2_root_cause_corrective/w0/FRAME_REGISTRY.csv) 为 79/79 视频、766/766 视角，身份失败 0；每行绑定源视频/PREPARED/cache/track/pairs/W0 哈希。按 manifest 显式映射，不按目录排序猜输入。 |
| A2/BA、Ring CAD | 六个本轮视频由原 W0 入口与现有 BA 重跑，R10 中心线半径 5.6 mm、管半径 0.6 mm，验证器同时检查 R5 为 3.1/0.6 mm。六视频属于 T1 sampling gap，未满足现有 T2/T3 A2 分支条件；旧 A2 pilot 的 R=5.0 错误结果未复用，也未新造 A2。 |
| `if False`、T11 标作 T10 | 同一候选池分别实际调用原 T10 `quality_diversity` 与原 T11 `direction_quota`；独立写入 T10/T11 行，行为测试检查两个方法均被调用且标签正确。 |
| 历史方向中心、锚点和分区 | 复用历史 014 complete-link 方向分区（距离阈值 0.26），方向为相机中心减模型中心；当前稀疏 W0 缺历史 INITIAL mesh，模型中心只能显式使用 W0 场景点均值代理。历史锚点按原始帧最近映射，但 0 个精确匹配，记录 `PROXY_NOT_HISTORICAL`。**此项未完全解决，不能声称历史 T10/T11 精确复现。** |
| S0/S1/S2 与 REJECTED | 按 M2C 严格阈值及 T0/T1 轨迹类别逐相机评定，S2 另需至少两个有 ≥12 几何匹配的邻接支持。REJECTED、T2/T3 和身份失败均不能进入 S2。准入政策与 T10/T11 目标选择、T13 支持选择分别存表。 |
| T13 几何门 | 原 T13 候选计算后检查至少 12 几何内点、方向角、极线误差、视差、非零目标基线及三支持方向分离；失败 tuple 记录原因，不调用 HERO。G01 的 4 个 S1 相机仍未形成满足 T13 的三支持集合；G06 最多 2 个。 |
| HERO 身份、重复与 A→B mask | HERO 前重查 W0、pairs、RGB、clean Mask、K、c2w、目标/支持几何和冻结的 tuple 哈希；`input_identity_verified=False` 会抛错。75 个选择 tuple 行仅 14 个唯一合法有序 tuple 真正推理，各 tuple 只计算一次；A→B 均使用 B 相机和 CLEAN B mask，42 对有独立源 mesh/相机/mask 哈希。收据含 RUN_ID、代码 SHA 与输入哈希。 |
| G01 约 −15.9 mm 深度异常 | 只读检查旧 7 条 G01 记录：3 条小于 −10 mm（其中有重复目标），目标与支持 W0 位姿绑定精确、原生 K 精确、深度为 mm 轴向 Z；7 条中无一条四相机都符合本轮 S1。全局 K/位姿绑定或单位错误未能解释旧异常，但因没有合法新 tuple，目标/支持贡献的因果诊断仍 **NOT_EVALUABLE**。未改 HERO 深度。见 [`G01_DEPTH_CONCLUSION.json`](../../runs/m2f2_root_cause_corrective/evaluation/G01_DEPTH_CONCLUSION.json)。 |

本轮 W0 与旧 W0 使用相同 PREPARED 和 track 哈希；六视频中 G01/G06 的 c2w 完全相同，G03/004 平移最大差约 0.703 mm、G03/005 约 0.0043 mm。差异没有被静默称作位级复现，详见 [`W0_OLD_NEW_COMPARISON.csv`](../../runs/m2f2_root_cause_corrective/w0/W0_OLD_NEW_COMPARISON.csv)。两组旧/新数值差的根因尚未完全定位。

## 3. 实际三组结果

以下 S0/S1/S2 为两个视频相机数之和；T10/T11 为目标选择行数，**不是**独立重建数。A→B 覆盖率的分母为各 B 视角 clean Polyp mask 像素；RGB MAE 单位为 0–255。CAD–HERO 是同一相机下 Ring CAD 光线深度与 HERO 深度的差，**不是**未知部署位姿下的 GT 形状精度。

| 组 | W0 | S0/S1/S2 | T10/T11 目标 | 唯一 HERO | A→B 对 | 覆盖率中位 | RGB MAE 中位 | CAD–HERO signed/MAE 中位 mm | 状态 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| G01 | 2/2 | 0/4/4 | 8/6 | 0 | 0 | NaN | NaN | NaN | NOT_EVALUABLE_NO_VALID_T13_TUPLE |
| G03 | 2/2 | 6/16/16 | 34/19 | 14 | 42 | 0.9344 | 12.4493 | −0.1453 / 1.7709 | CONDITIONAL_HERO_EXECUTED |
| G06 | 2/2 | 0/2/2 | 4/4 | 0 | 0 | NaN | NaN | NaN | NOT_EVALUABLE_NO_VALID_T13_TUPLE |

G03 的 14/14 HERO、42/42 A→B 和 14/14 CAD–HERO 行完成，评价阶段失败 0。G03 同视频不同目标曲面的 43 个两两比较中，世界坐标质心距离中位 1.341 mm，双向最近邻距离中位 0.298 mm、pair p95 中位 0.854 mm，最大 pair p95 2.076 mm。这是同一 W0 坐标系的**一致性诊断**，并非独立 GT 精度、覆盖率或完整曲面证明。数据见 [`GROUP_STATUS.csv`](../../runs/m2f2_root_cause_corrective/evaluation/GROUP_STATUS.csv)、[`A_TO_B_METRICS.csv`](../../runs/m2f2_root_cause_corrective/evaluation/A_TO_B_METRICS.csv)、[`CAD_HERO_GEOMETRY.csv`](../../runs/m2f2_root_cause_corrective/evaluation/CAD_HERO_GEOMETRY.csv)、[`MULTISURFACE_CONSISTENCY.csv`](../../runs/m2f2_root_cause_corrective/evaluation/MULTISURFACE_CONSISTENCY.csv)。

## 4. 六视角人工检查材料

每张图为原始图像/重建表面的三个目标视角与世界 X/Y/Z 三个观察方向，图内比例尺约 5 mm；物理坐标单位 mm。Ring CAD 的物理半径已知，GT 病灶真实形状可信但**部署位姿未知**，图像及 CAD 比较均不得当作端到端 GT 结论。G03 多目标叠图可见大部分主体重叠、边缘和离群碎片存在；上表的两两距离量化了这种不一致。

- G03/004：[单目标六视角](../../runs/m2f2_root_cause_corrective/visualization/six_views/G03_004.png)、[多目标六视角](../../runs/m2f2_root_cause_corrective/visualization/six_views/G03_004_MULTISURFACE.png)。
- G03/005：[单目标六视角](../../runs/m2f2_root_cause_corrective/visualization/six_views/G03_005.png)、[多目标六视角](../../runs/m2f2_root_cause_corrective/visualization/six_views/G03_005_MULTISURFACE.png)。
- G03 原生开放网格样例：[004 PLY](../../runs/m2f2_root_cause_corrective/hero/GP_Ip_20.0mm_closed_R10_single_refY/004/1b3adcc753a07736/Raw_open_mesh.ply)、[005 PLY](../../runs/m2f2_root_cause_corrective/hero/GP_Ip_20.0mm_closed_R10_single_refY/005/f9309141a50dbe8e/Raw_open_mesh.ply)。全部 14 个 tuple 的 `RAW_NATIVE_MESH.npz`、`HERO_native.npz` 和输入收据均在同目录提交；PLY 只精选两个便于人工查看。
- G01：[004 无 HERO 的六方向 W0 图](../../runs/m2f2_root_cause_corrective/visualization/six_views/G01_004_NO_HERO.png)、[005 无 HERO 图](../../runs/m2f2_root_cause_corrective/visualization/six_views/G01_005_NO_HERO.png)；G06：[004 无 HERO 图](../../runs/m2f2_root_cause_corrective/visualization/six_views/G06_004_NO_HERO.png)、[005 无 HERO 图](../../runs/m2f2_root_cause_corrective/visualization/six_views/G06_005_NO_HERO.png)。这些图明确标示 **NO HERO**，不伪装重建。

## 5. 对 M2F1 的比较与 39 组决策

M2F1 报 60 行 HERO、180 个 A→B 对、覆盖率中位 0.947、RGB MAE 13.20，但其审计已指出 tuple 重复、准入及身份不合格。该数字不能与本轮 14 个唯一合法 tuple 作相同分母的性能排序。本轮解决了 registry 缺行、身份误报、T11 未执行/误标、S2 接纳 REJECTED、tuple 重复及 A→B mask 混用等工程缺陷；仍未恢复历史精确锚点/INITIAL mesh 中心，G01/G06 无合法 HERO，G01 深度异常的根因未被新数据证实。故三组验证失败，按任务要求 **39 组 0/39 执行**；没有静默扩展或更换算法。见 [`VALIDATION_39.json`](../../runs/m2f2_root_cause_corrective/VALIDATION_39.json)。

## 6. 复现与验证

在仓库根目录，使用本地已准备的 39 组 PREPARED、clean mask、源视频、冻结模型权重以及 `mainline/configs/SITE.local.json` 指定的 Python 环境。完整重跑单命令：

```bash
PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/m2f2_unified.py \
  --stage all --groups G01,G03,G06 --run-id M2F2-20261124-FINAL-005
```

本轮也分别运行 `--stage select`、`--stage hero`、`--stage evaluate` 做同 RUN_ID 的收据核对；最终产物由上方单命令重跑。测试：

```bash
PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -m pytest \
  tests/test_m2f2_entrypoint.py tests/test_m2f2_identity.py tests/test_m2f2_selection.py \
  tests/test_harness_contracts.py tests/test_w0_manifest_closure.py -q
```

结果 **22 passed**；测试覆盖 W0 失败即中止、错误 cache/track 身份、false identity 阻断、REJECTED/S2 阻断、阈值、方向中心、T13 几何、T10/T11 实际调用与标签。另对 13 张非空结果表的 RUN_ID/代码 SHA、14 个唯一 HERO 输入收据与实际 W0/mesh 文件、8 张六视角图作最终审计，见 [`FINAL_AUDIT.json`](../../runs/m2f2_root_cause_corrective/evaluation/FINAL_AUDIT.json)。W0、选择、HERO、评价日志分别在 `runs/m2f2_root_cause_corrective/logs/`。需保留本地输入视频与模型；提交只含精选小型证据，不上传全量视频、权重或虚拟环境。
