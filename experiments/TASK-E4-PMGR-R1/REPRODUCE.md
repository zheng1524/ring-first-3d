# 复现与恢复

本轮已触发停止。以下命令是人工复现说明，不是继续运行的授权；当前无后续优化任务。

## 当前本地结果

工作树：`/home/liu/ring_first_3d_e4_pmgr_r1`。

实验根目录：`/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1`。

最后安全网格：该根目录下`local_results/G01_004/LAST_SAFE.ply`及`.npz/.glb`。`P0.*`是新安全初始化，不是历史P0。历史与候选另存`G01_004_HISTORICAL_P0.npz`和`G01_004_P0_CANDIDATE.npz`。10个`G01_004_P1_iter*_trial*.npz`均含before/proposed/accepted真实顶点和参数；对应JSON保存原责任Face/Edge及实际投影。六视角详图在`figures/full/G01_004_Six_Views.png`。

本地依赖、输入、完整结果和运行日志不进Git；全部文件路径/大小/SHA见`assets_index/LOCAL_RESULTS.json`、`SOURCES.json`。保持目录中的输入原生ID、K/c2w和CAD不变。PLY/NPZ为mm，GLB为m；没有补面、几何平滑或Mesh后处理。

## 只读复算报告与图

```bash
cd /home/liu/ring_first_3d_e4_pmgr_r1
source experiments/TASK-E4-PMGR-R1/code/env.sh
"$PMGR_R1_PYTHON" "$PMGR_R1_ROOT/code/postprocess.py"
"$PMGR_R1_PYTHON" "$PMGR_R1_ROOT/code/diagnose_boundary.py"
"$PMGR_R1_PYTHON" "$PMGR_R1_ROOT/code/figures.py"
"$PMGR_R1_PYTHON" "$PMGR_R1_ROOT/code/integrity.py"
```

这些命令只评价保存端点/候选，无优化器调用。`postprocess.py`恢复basis时使用保存的phi/frequency与新P0，不重新求解几何。源路径随原项目资产按清单恢复，不下载模型。科学Python审计钩子限制写入本任务目录，不打开GT/Oracle/其他融合结果。

## 精确执行版本与最小适配

正式运行使用`eea53d74e645f58fc67e6b4d01ce4db96e716524`，唯一一次`code/run.py`；全部数值验证先通过、源码和输入SHA先冻结。固定规则见`01_PROTOCOL.md`。停止后`run.py`仅把可行性报告文件名改为`_P0_FEASIBILITY.json`，修复原文件覆盖；未修改优化目标、阈值或重跑拟合。

要独立重新做正式求解，须在新复现目录中恢复冻结输入和依赖、调整任务根指向、核对所有SHA，先`validate.py`再`run.py`；不要在当前已完成目录直接重跑，因为会覆盖本次派生输出。`prepare.py`只用于空目录，已有配置时会拒绝初始化。原父代码按函数AST受控读取，不能直接导入其旧写入Guard。

## 依赖

- 既有Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`。
- Open3D0.19.0复用已有vendor；无需GPU。
- `python-fcl==0.7.0.11`安装在本任务`runtime/packages`，未修改全局Python。全三角面BVH碰撞/距离接口依据[python-fcl上游说明](https://github.com/BerkeleyAutomation/python-fcl)，这是FCL Python绑定，不冒称官方科研模型。
- Blender5.0.1现有二进制：`/home/liu/blender/blender-5.0.1-linux-x64/blender`。使用`--factory-startup --background --threads 2 --python-exit-code 2`，仅载入本任务生成的主体/CAD数组，未打开任何历史`.blend`。
- 精确包版本见`metrics/ENVIRONMENT.json`，准入、输入及调用源码SHA见freeze与sources清单。

最终数值验收：8项预检PASS；127项冻结资产SHA未变；P0与LAST_SAFE封闭/绕序/符号正确；最后候选数10、接受1、拒绝9，无P2或G06数值输出。局部梯度验证不涵盖所有轮廓显隐切换，已在失败记录明确。
