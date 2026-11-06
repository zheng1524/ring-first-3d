# 一次性渐进形变/深度验证复现

分支仍为 `exp/TASK-E4-PYTORCH3D-RING-AWARE-001`。本运行不覆盖或替换上轮报告及模型。A直接引用`VISIBILITY_ORDER_REPAIR_001`，不引用早期软zbuf失稳结果。

本机目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/PROGRESSIVE_HERO_001`。

## 环境和数据

使用上轮同一Python、已编译PyTorch3D、CUDA12.8、本地RTX3060；runtime/packages和runtime/pytorch3d只引用既有安装，没有重装环境或下载模型。Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`。

inputs为原固定Mask/RGB/K/c2w/Ring/P0的受控复制。`assets_index/INPUTS.json`、`A_FROZEN.json`和`DEPTH_SOURCES.json`给出来源和SHA。HERO观测复用R1的固定512点/视角原生缓存，核对N0最新清理valid及原生HERO深度；全部原值、Pixel ID不变。352高深度K与360高RGB K通过同一相机射线对应，不能把native v直接当RGB v。

`depth_observations/*.npz`是固定射线观测，不是网络输出：真实FROZEN_NATIVE_HERO，虚拟IDEAL_GT_DEPTH_UPPER_BOUND。虚拟D理想GT深度由独立准备进程生成，三维GT Mesh不进入优化进程。真实HERO没有重新推理、参考校正或权重更新。

训练和评价必须使用原来角色：虚拟FIT obs01/03/05、HOLDOUT obs00/04；真实FIT ref08/ref13/ref03、UPDATE_HOLDOUT growth_r04/r06/r10。A历史只保存0/100/200/300，没有补造A的25/50等中间Mesh。

## 执行顺序

现有结果已冻结，禁止直接覆盖。复跑应复制本子目录代码/config到另一个独立运行副本，恢复输入引用及旧A索引，使用新的local_results/metrics。当前脚本会拒绝覆盖FINAL和freeze记录。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python

# 只在新的独立副本初次准备；同一代码及固定规则，不重新生成场景或Mask。
$PY -B code/prepare_run.py
$PY -B code/preflight.py
$PY -B code/freeze_run.py pre

# 串行执行，A不运行。
$PY -B code/train_progressive.py virtual B
$PY -B code/train_progressive.py virtual C
$PY -B code/train_progressive.py virtual D
$PY -B code/train_progressive.py real B
$PY -B code/train_progressive.py real C
$PY -B code/train_progressive.py real D

$PY -B code/freeze_run.py predictions
$PY -B code/evaluate_progressive.py
/home/liu/blender/blender-5.0.1-linux-x64/blender -b \
  --python code/blender_progressive_check.py -- "$PWD"
$PY -B code/post_diagnostics.py
$PY -B code/diagnose_geometry.py
$PY -B code/figures_progressive.py
$PY -B code/write_report.py
$PY -B code/validate_run.py
```

继承的`evaluate.py`数值函数保持原样；新驱动仅替换状态列表为P0/A/B/C/D及实际保存的checkpoint。6000+6000面积采样和2^18 Sobol域与上轮一致；自交体积代理不冒称严格实体Boolean体积。原`p3d.py`字节相同，Ring-Aware可见性和官方软轮廓/相机映射没有被替换。

## 检查点和恢复信息

每个`local_results/{virtual,real}/{B,C,D}/`保存：

- `STEP_0000/0025/0050/0075/0100/0150/0200/0250/0300.npz`及毫米PLY/PT；没有删除任何已保存状态。
- C/D另有`STAGE2_START`，与STEP_0100的实际V/F严格相同。
- `FINAL.npz`、`FINAL_mm.ply`、`FINAL_normalized.obj`为第300步真实原始Mesh，不做删面、平滑、补洞。
- PT含stage、global_q、origin、local、SGD状态、numpy/torch/cuda随机状态及完整config。可信自产PT可用`torch.load(...,map_location='cpu',weights_only=False)`读取。
- stage GLOBAL6使用六个参数；stage LOCAL使用origin+local。C/D切换阶段时SGD动量重置，这是冻结策略的一部分。后续恢复需保持阶段、归一化、F、参数顺序和优化器状态，不可仅加载Mesh后称无缝续训。本轮不自动续训。

大文件不提交GitHub；绝对路径/字节/SHA及完整恢复索引见`assets_index/LOCAL_RESULTS.json`。当前脚本只执行固定一次300步，没有自动续训或选最优模型入口。

## 留出、覆盖和工程记录

D构造缓存时加载了全部固定参考以便统一评价，但实际深度loss只调用FIT；`FAIRNESS.json`和DEPTH_TRACE逐次验证没有留出loss调用。B/C观测数据解码被hook禁止，完整性SHA读取不进入目标。未命中和病态射线不被移出分母；封顶惩罚与最大单项loss相同，不把命中数当可微目标。

FP32联合方向有限差分失败原记录保留，使用FP64顶点验证同一扰动/阈值后通过。零步SHA读取隔离接线失败的原源码、freeze和stdout位于`assets_index/pre_run_guard_failure`及`PREOPT_FREEZE_V1_GUARD_REJECT.json`；修正hook安装次序后才开始正式更新。算法和损失不因此改变。

后验公平性第一次错误地以原始FP64世界坐标做位级比较；改为与冻结A0及同一FP32渲染表示逐位比较，并另记往返误差。此项没有改变预测或阈值。

本轮全部六个新运行数值完成，全部未通过最终几何门禁。保留这些失败是实验交付的一部分，不改配置重跑制造PASS。
