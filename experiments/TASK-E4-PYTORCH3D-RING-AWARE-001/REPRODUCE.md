# 复现与本地结果索引

本实验分支 `exp/TASK-E4-PYTORCH3D-RING-AWARE-001`。先阅读01_PROTOCOL、TECHNICAL_REPORT及FAILURE_LEDGER。最终预测固定第300步，不按GT挑选，不替换旧实验。

**当前有效工程实现是 `runs/VISIBILITY_ORDER_REPAIR_001`，不是根目录的软zbuf失败初版。** 根目录原训练/预测/指标全部保留作为失败记录；当前四张审阅图来自修复版。`metrics/FINAL_PAIRED_METRICS.csv`、`metrics/FINAL_RESULT.json`和`assets_index/CURRENT_RESULT_INDEX.json`是主索引。不能单独引用旧GRADIENT_GATE.json的有限/非零true作为稳定性验收。

## 已有环境与来源

- Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`，准确包/GPU版本见assets_index/ENVIRONMENT.json。
- 官方源码位于本目录runtime/pytorch3d，提交锁在config/FROZEN.json；无源码修改。上游教程、许可证和相机转换源码小副本在upstream/。
- 独立辅助包位于runtime/packages。只安装fvcore、iopath、yacs、termcolor、portalocker、ninja；不重新安装torch，不下载模型权重/视频/BundleSDF。
- 官方cow.obj仅约322KiB，下载地址：https://dl.fbaipublicfiles.com/pytorch3d/data/cow_mesh/cow.obj 。本轮不需要纹理。
- 虚拟/真实输入为已有资产的受控复制，见assets_index/INPUT_MANIFEST.json；原Mask和K/c2w保持原生640×360身份。不重新渲染目标数据。
- 大文件与环境不上传GitHub。本地绝对路径、字节数和SHA见assets_index/LOCAL_RESULTS.json。迁机须先恢复这些合法原始输入，不可用其他算法结果补齐缺失文件。

## 官方扩展构建

在独立runtime/pytorch3d目录、安装本轮辅助包后，用现有torch对应CUDA编译：

```bash
CUDA_HOME=/usr/local/cuda-12.8 \
CUB_HOME=/usr/local/cuda-12.8/include \
TORCH_CUDA_ARCH_LIST=8.6 MAX_JOBS=2 \
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python setup.py build_ext --inplace
```

完整编译日志runtime/pytorch3d_build.log。首次构建时ninja尚未安装，因此setuptools串行构建；没有跳过CUDA扩展或替换成其他渲染器。

## 顺序执行

以下命令从实验目录运行。已冻结结果存在时脚本会阻止覆盖；完整重跑需创建独立副本，不删除当前FINAL或历史结果。

下面这一组复现根目录的**失败初版**，用于审计；不代表当前推荐实现。最终配对复现见其后的“隔离修复版”一节。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python

# 新副本第一次准备已有输入和截面证据。prepare只复制/适配，不重生成目标场景。
$PY -B code/prepare.py
$PY -B code/ring_sides.py

# 官方2000步复现、导出审计、相机门禁、遮挡图、梯度门禁；任何失败停止。
$PY -B code/pipeline.py

# 人工/执行者检查两个Occlusion_Audit图片后冻结输入与代码。
$PY -B code/freeze.py pre

# 只串行使用GPU；两条件同起点/视角序列/预算。
$PY -B code/train.py virtual Baseline
$PY -B code/train.py virtual RingAware
$PY -B code/train.py real Baseline
$PY -B code/train.py real RingAware

# 必须先冻结所有预测，之后才读取native GT做三维评价。
$PY -B code/freeze.py predictions
$PY -B code/evaluate.py

/home/liu/blender/blender-5.0.1-linux-x64/blender -b \
  --python code/blender_geometry_check.py -- "$PWD"

$PY -B code/figures.py
$PY -B code/report.py
$PY -B code/validate_delivery.py
```

## 隔离修复版：当前结果

只改Ring可见性：每次前向重新按CAD/主体深度确定离散前后次序，禁止对不稳定的zbuf次序反传；仍对官方软轮廓进行真实顶点反向传播。无zbuf平滑深度梯度，不用梯度裁剪、不变SGD/loss正则/300步预算。完整旧失败保持原位。

现有冻结目录只读查看；若复跑，先建立独立副本，保留其code/config和不变输入的受控引用。当前本机修复版inputs是原输入的只读使用链接，runtime/packages与pytorch3d引用同一已验证官方环境。**不要在该链接上运行prepare或ring_sides重新写入冻结输入。** 每个新副本使用独立local_results、metrics和assets_index。

按修复版目录的配置、来源和相机门禁回执，执行：

```bash
# 在修复版的独立复跑副本中；此前官方复现/原生相机门禁回执来自根目录。
$PY -B code/gradients.py
$PY -B code/occlusion_audit.py
$PY -B code/freeze.py pre
$PY -B code/train.py virtual Baseline
$PY -B code/train.py virtual RingAware
$PY -B code/train.py real Baseline
$PY -B code/train.py real RingAware
$PY -B code/freeze.py predictions
$PY -B code/evaluate.py
/home/liu/blender/blender-5.0.1-linux-x64/blender -b \
  --python code/blender_geometry_check.py -- "$PWD"
$PY -B code/figures.py
$PY -B code/validate_delivery.py
```

官方cow的RENDER_COMPARISON和复现回执只用于统一Fig1，应按资产索引从根目录恢复；不是项目模型预测回退。分类截面metrics/sides必须同原输入复制。原始预优化分类/CAD图在第一次运行前已检查；修复版实际像素权重图因缺少只读元数据副本而在运行后补生成，时序在REPAIR_AUDIT_PROVENANCE中明确记录。后续复跑应先生成图再启动，不复用这个接线遗漏。

根目录的后验汇总命令为：

```bash
$PY -B code/paired_diagnostics.py
$PY -B code/finalize_delivery.py
$PY -B code/validate_delivery.py
```

`code/report.py`为保留的首轮报告代码，不用于覆盖当前最终报告。最终报告由finalize_delivery汇总两个运行，同时保留初版数值失败。不要按GT从两个运行中挑更好结果；修复选择依据是自动微分与有限差分严重矛盾。

原生GT路径为上一轮Gate A的audit_only/NATIVE_CAD_GT.npz，仅独立投影门禁与预测冻结后的评价读取。训练使用三FIT Mask，不读该文件、不按留出/GT选模型。真实GT始终NOT_EVALUABLE。

## 工程失败保留

官方首次9位OBJ检查及完整2000步结果保留在local_results/official_attempt01_decimal9；同配置复放只修复序列化/审计，不改网络、优化器、预算或按结果选优。正式16位OBJ与原float32源数据位级一致。默认CUDA coarse-bin同Mesh重复渲染也有像素波动，官方bin_size=0仅用于独立导出审计，原始失败未覆盖。

P0初次投影容量溢出失败在metrics/PROJECTION_GATE_FAILED_BIN_CAPACITY.json。修复为每bin容量至少单Mesh全部面数；两条件一致、原IoU阈值不变，原始相机和几何不改动。详见metrics/ENGINEERING_REPAIRS.json。

## 实际输出与恢复

- 官方：local_results/official/FINAL.obj、FINAL_SOURCE_FLOAT32.npz、RENDER_COMPARISON.npz，完整训练曲线metrics/OFFICIAL_TRAINING.csv。
- 项目：local_results/{virtual,real}/{Baseline,RingAware}/STEP_0000/0100/0200/0300 对应NPZ、毫米PLY和PT；FINAL.npz、FINAL_mm.ply、FINAL_normalized.obj为最终实际网格。
- 上述根目录路径属于初版保留结果；当前有效配对在runs/VISIBILITY_ORDER_REPAIR_001/local_results的同名结构。该运行的LOCAL_RESULTS、PREDICTIONS_FROZEN_BEFORE_GT和DELIVERY_VALIDATION分别提供全路径/SHA/核验回执。
- PT包含offset、optimizer状态、步数、随机状态、归一化与完整配置；当前运行完成即停止，不自动续训。未来恢复时以同一BASE V/F加载offset和optimizer，并恢复numpy/torch/cuda随机状态；本轮没有调度器或其他网络。
- 归一化OBJ坐标必须用对应NPZ的scale和center恢复毫米；直接查看毫米PLY可避免误用归一化尺寸。
- 所有方法逐视角统一Open3D评价数据：local_results/eval；当前表面“有Mask可见支持/推断或未验证”分类为证据，不是三维真值。
- 四张核心图在figures/Fig1–4；完整原相机投影在figures/full；优化前全部分区/深度/最终权重审计图及数组保留本地。

恢复或复现不能关闭GT隔离、改变camera资格、混入video005，也不能按GT回退到表现更好的历史中间Mesh。
