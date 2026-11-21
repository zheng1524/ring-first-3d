# 019 复现

工作树：`/home/liu/ring_first_3d_e4_sdf_localization`；分支`exp/TASK-E4-RING-POLYP-REGISTRATION-019`。

解释器：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`；实际Python3.12、PyTorch2.7.1cu128；官方PyTorch3D本地commit `e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31`。同一已安装OpenCV/Open3D/SciPy环境，通过`common.py`设置原本地依赖路径。不下载新模型/框架。硬件RTX3060Laptop6GiB，单GPU串行。

所有命令从工作树根目录执行，以下`$PY`仅为任务变量，`$TASK019`为本任务目录。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK019=experiments/TASK-E4-RING-POLYP-REGISTRATION-019
```

完整来源、精确输入SHA和原路径：`INPUT_MANIFEST_COMPLETE.json/csv`。RGB/Mask/视频/原生HERO/018主体/原始相机需在对应本地存储存在；Git仓库不含大文件。请在独立实验副本运行准备和训练阶段，勿在已冻结目录覆盖结果。

```bash
$PY -B $TASK019/code/prepare019.py
$PY -B $TASK019/code/frame019.py
$PY -B $TASK019/code/ring019.py
$PY -B $TASK019/code/clean_sources019.py
$PY -B $TASK019/code/features019.py
```

**预注册冻结注意**：`prepare019.py`是初始准备器，随后本轮在搜索前冻结了精确004前4→后4负对照与原生方向4分区。其最终`config/VIEWS.json`、`config/NEGATIVE_SPLIT.json`、`01_PROTOCOL.md`和`provenance/BEFORE_SEARCH_FREEZE.json`是权威输入。独立重跑在prepare后、features之前，从已交付原目录执行`restore_frozen_config019.py --destination /绝对路径/独立副本`恢复最终配置；它只重定位任务内缓存路径，保持原相机/方向/分割/划分完全不变，并拒绝写入原冻结目录或已有冻结预测的副本。不要把prepare的初始默认negative排序当最终协议。`frame019.py`只核查并产出证据，不修改原相机。SIFT数值退化帧对保持无F。

```bash
$PY -B $TASK019/code/gate019.py
$PY -B $TASK019/code/geometry019.py
$PY -B $TASK019/code/search019.py
$PY -B $TASK019/code/performance_gate019.py
$PY -B $TASK019/code/refine019.py
```

`refine019.py`已有FINAL则跳过，已有ITER.pt则恢复q+Adam。严格重跑请使用独立副本、独立输出，不能把恢复段秒数作为全训练耗时。最终选模必须在任何HOLDOUT提取前冻结，禁止后续GT或HOLDOUT回流。

下列为**纯冻结后评价/可视化**（不更新模型），也是此次续执行实际完成的后处理链：

```bash
$PY -B $TASK019/code/evaluate019.py
$PY -B $TASK019/code/ring_depth019.py
$PY -B $TASK019/code/hero_diagnosis019.py
$PY -B $TASK019/code/feature_evaluate019.py
$PY -B $TASK019/code/stability019.py
$PY -B $TASK019/code/deliver019.py
$PY -B $TASK019/code/audit_delivery019.py
$PY -B $TASK019/code/reports019.py
$PY -B $TASK019/code/verify_delivery019.py
```

已有全部缓存时可只重跑`deliver019.py`与`reports019.py`恢复核心图和文字；`audit_delivery019.py`核对原资产和冻结结果SHA，未通过应停止交付。`stability019.py`只复用搜索缓存做预定FIT子集yaw敏感性，不做留出驱动新优化。

尺寸定义：计算与NPZ/相机均为毫米，GLB仅按规范导出米(.001)，不是重新估计尺度。SIFT像素对应原640×360；HERO原生352×640。派生HERO只变换坐标，不插值或补面，不构成融合。
