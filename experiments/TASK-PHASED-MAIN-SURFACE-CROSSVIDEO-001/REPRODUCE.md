# 复现与输入边界

使用 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（Python 3.12），实际依赖见 [RUNTIME.json](provenance/RUNTIME.json)。Open3D 0.19 直接只读调用历史 `surface_fusion_v3/vendor`；不安装或迁移整个旧项目，不下载权重。原始冻结资产未公开，外部机器仅凭 public 仓库不能独立重建这些科研结果。

在本机核验当前交付（已实际运行；16 项解析/来源测试与 286 项结果级检查通过）：

```bash
cd /home/liu/ring_first_3d_phase_d
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/code/reproduce.py verify
```

查看顺序、资产与阶段计划，不运行研究计算：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/code/reproduce.py plan
```

需要重新执行时，必须指定全新目录，既有目录一律拒绝覆盖。脚本复制本任务小型代码/配置，建立只读绘图模块链接，按冻结输入依次运行 D0、五初值有界 GICP、有限 yaw 诊断、一种缓存匹配 PnP 备用、评价、D3、GLB 和绘图；不会重新运行 HERO、Ring-First、密度清理或 Dxy。

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/code/reproduce.py replay --destination /home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/runtime/replay_run_01/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001
```

本轮所有实际阶段已逐段执行；新目录一键 `replay` 的完整第二遍未额外执行。随机种子均冻结；Open3D 线程/线性代数平台可能产生浮点差异，应比较数值容差与决策状态，不能承诺跨机器 GLB/PNG 字节一致。

已有结果的图片重画入口为 `code/figures.py` 和 `code/diagnostic_views.py`；它们只读取现有实际 XYZ/RGB 和派生 H，不做配准或融合优化。L1–L4 使用固定 `visualization/real_p0_renderer.py` 的原始点绘制接口，诊断点大小 0.08、alpha=1、CAD alpha=0.15；L5 用原冻结 K/c2w，点大小 0.8、黑色不透明 CAD。无点抽样、补洞、平滑或新增表面。

来源与版本：

- [INPUTS](provenance/INPUTS.json)：六参考的 XYZ/RGB/Mask/深度、相机、原 Mesh、B/C 和固定绘图接口 SHA。
- [TARGETS_FROZEN](provenance/TARGETS_FROZEN.json)：D0 选择帧与 D1 留出帧在计算图像误差前分离。
- [SOURCE_RULES_FROZEN](provenance/SOURCE_RULES_FROZEN.json)、[PROTOCOL](PROTOCOL.md)、[config](config.json)：D0/主路线的事前冻结。
- [D1_BACKUP_BEFORE_COMPUTE](provenance/D1_BACKUP_BEFORE_COMPUTE.json)：唯一备用方法的输入、三个固定子样本和冻结 seed0。
- [SOURCE_VERSION_HISTORY](provenance/SOURCE_VERSION_HISTORY.json)：实际运行源码的精确归档；后续修正仅涉及状态归属及 POINTS 元数据导出，数值配准不变。
- [GLB_METADATA_REPAIR](provenance/GLB_METADATA_REPAIR.json)：三份 GLB 增补来源元数据前后，几何与 RGB 二进制缓冲区 SHA 完全一致。
- [HEIGHT_SENSITIVITY_CORRECTION](provenance/HEIGHT_SENSITIVITY_CORRECTION.json)：最初法向扰动的旋转锚点不在拟合平面上；已用独立后分析投影锚点修正。原基底拟合与高度值未变，旧法向扰动数值不用于结论。
- [FINAL_SOURCE_MANIFEST](provenance/FINAL_SOURCE_MANIFEST.json)：最终源码 SHA，包括精确执行版本归档。所有不可评价数值以 JSON `null`、CSV 空值保存，相当于 NaN，不以历史值回退。

通用 `stats()` 的 `MAE` 字段表示所传入值的平均绝对值；用于 RGB/残差时有误差含义，用于高度分布时不是 GT 测量误差。报告只将后者解释为原型分布。GT/Oracle 文件受运行时 I/O 守卫阻止；所有本任务写入限于本任务目录。启动与终止的五个受保护工作区已核对 HEAD、index、完整状态及既存未提交科研文件 SHA。
