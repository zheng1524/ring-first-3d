# 本地恢复、只读复评与执行版本

根目录：`/home/liu/ring_first_3d_e4_ffd/experiments/TASK-E4-PMGR-FFD-002`。

工作树：`/home/liu/ring_first_3d_e4_ffd`；分支`exp/TASK-E4-PMGR-FFD-002`。本轮已停止，整体数值门禁失败，不自动追加优化。

## 已保存输出

- 主方法：`local_results/G01_004/C2/P3.ply`、`local_results/G06_004/C2/P3.ply`及同名NPZ/GLB。后者P3没有接受新更新，须结合状态解释为最后安全端点。
- 每组/arm有P0/P1/P2/P3、BEST/LAST_SAFE，NPZ含实际V/F/q；FFD/spectral基底在`inputs/<scene>_<kind>_BASIS.npz`，参数q前9为中心/旋转/log轴，后为固定基底系数。
- NPZ/PLY、深度、相机平移及图用mm；GLB用m。固定拓扑642点1280面，无几何平滑、补洞或后处理删除。
- 本地完整文件、原始来源、冻结输入和SHA见`assets_index/LOCAL_RESULTS.json`、`INHERITED_SOURCES.json`与`metrics/INPUT_FREEZE.json`。大文件不提交Git，原始视频/深度不重复拷贝。
- 每个阶段的每源`__*_NATIVE_EVAL.npz`含首层深度/命中/深度对命中；原生Pixel ID仍在只读输入池。
- 六视角和原A/原B图位于`figures/full/`。原B已参与训练，绝不能称独立留出。

## 不运行优化的复算入口

```bash
cd /home/liu/ring_first_3d_e4_ffd
source experiments/TASK-E4-PMGR-FFD-002/code/env.sh
"$PMGR_FFD_PYTHON" "$PMGR_FFD_ROOT/code/evaluate.py"
"$PMGR_FFD_PYTHON" "$PMGR_FFD_ROOT/code/case_gate.py"
"$PMGR_FFD_PYTHON" "$PMGR_FFD_ROOT/code/figures.py"
"$PMGR_FFD_PYTHON" "$PMGR_FFD_ROOT/code/audit.py"
"$PMGR_FFD_PYTHON" "$PMGR_FFD_ROOT/code/report.py"
```

这些命令读取已保存Mesh/基底/固定源，仅做评价、梯度QA和制图，不调用优化器。`case_gate.py`不assert丢掉负结果，会输出G06 FAIL。`correct_derived_outputs.py`已执行且有防重复归档保护，不要将修正结果冒充原始日志。

## 精确执行历史和当前代码区别

1. **24232c8**：预注册、输入/源码SHA及G01训练前16项数值验证。`code/run.py`实际执行G01三臂及G06唯一P0求解，错误沿用初始化观测硬门槛而停G06。原日志`logs/FORMAL_RUN.txt`及初次结果保留。
2. **c775bfe**：先登记纠正入组，再用`code/continue_g06.py`读取同一个已保存G06 P0候选执行三臂，未重求初始化、重跑G01或改变损失/预算。该执行版本没有逐案例Mask数值gate，事后发现G06 FAIL，必须按负结果解释。
3. 当前代码仅在上述基础上修复输出派生字段、把初始化观测退化改成警告，并**强制每组更新前执行同一局部数值gate**。因此新的完整执行会在G06梯度检查失败时提前阻塞，不会默默复现验证缺失的更新。不能把已保存G06结果说成由修复后的gate放行。

要精确审查历史程序，使用Git相应提交及冻结清单；不要在当前完成目录重跑，因为会覆盖派生文件。若另行获准复现优化，创建新隔离根目录、恢复只读资产/路径和哈希，再按对应源码的`validate.py → run.py`执行；只有审查历史负结果时才涉及原`continue_g06.py`，不得用它绕过当前数值门禁。当前结果已经保存，无需重训来复评。

没有承诺跨GPU驱动bitwise一致，光栅显隐数值敏感正是本轮主要失败；不得把不同的失败轨迹静默当成功复现。

## 环境与权限

复用Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`、Torch2.7.1+cu128、已有nvdiffrast0.4.0源码253ac4fcea7de5f396371124af597e6cc957bfae、python-fcl0.7.0.11、Open3D0.19.0、Blender5.0.1。具体路径和版本见ENVIRONMENT/SOURCE_REUSE_AUDIT。新任务没有安装PyTorch3D/PhysicsNeMo/libigl/IPC，无新权重。

Blender只以`--factory-startup --background`打开本任务生成的主体/CAD数组，不读任何GT `.blend`。输入通过符号链接读取，目标保留原权限；Python审计Guard禁止解析到任务外写入，没有改原始权限或使用可写硬链接。

清理仅两份R1 pip HTTP缓存，安装目录未删；恢复下载用同版本`python -m pip download --no-deps python-fcl==0.7.0.11`。精确删除路径、SHA及4.66MB实际回收见CLEANUP_MANIFEST/DISK_AUDIT。共享UV/Conda/Torch缓存和所有唯一科研结果均保留。
