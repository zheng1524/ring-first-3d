# 复现

父提交4a09aedc669092d264f070ccac4fd12851097dd1；协议51116d0；CAD下界最终修正2f7e042（e14c630首修未通过独立回放，保留拒收证据）。先检出本任务独立分支，保持历史树与外部源只读。依赖数据见assets_index/LOCAL_DATA_SOURCES.json；大文件不在Git。无需DXY重新预测、HERO推理、GT或历史融合模型。

```bash
cd /home/liu/ring_first_3d_e4_pmgr
source experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001/code/env.sh
"$PMGR_PYTHON" "$PMGR_ROOT/code/replay_inputs.py"
# 若新检出缺本地输入，先加 --rebuild，必须逐SHA匹配
"$PMGR_PYTHON" "$PMGR_ROOT/code/spectral_control.py"
# 上项保留已发现的精确球体重根FAIL，返回非零；不要改阈值。
# 单独核对实际八份冻结谱：
"$PMGR_PYTHON" "$PMGR_ROOT/code/dense_spectral_audit.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/validate.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/contracts.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/run.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/finalize.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/audit_results.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/audit_results.py" --active-rank
"$PMGR_PYTHON" "$PMGR_ROOT/code/gradient_audit.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/figures.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/stage_diagnostics.py"
"$PMGR_PYTHON" "$PMGR_ROOT/code/report.py"
cp "$PMGR_ROOT/KEY_TECHNICAL_VERSION_E4_PMGR_CANDIDATE_v0.3.md" docs/KEY_TECHNICAL_VERSION_E4_PMGR_CANDIDATE_v0.3.md
```

run.py已完成案例不会重复优化。单案例可用`--scene G06_004 --initial E2 --seed 0 --arm PMGR`；数量配平对照依赖相同case/seed的PMGR数量结果。中途工程中断保留__progress日志和阶段npz；重新执行未完成案例从固定P0重跑，不能称断点无缝续训。完整已完成阶段可从npz精确恢复V、a、Adam状态与时间计数；随机子批由seed/step函数生成，不依赖隐含全局RNG。没有神经权重。

新环境安装：使用已验证PyTorch2.7.1+cu128和CUDA12.8工具链；任务runtime/packages安装ninja1.13.2，再构建NVlabs/nvdiffrast精确253ac4fcea7de5f396371124af597e6cc957bfae（--no-build-isolation --no-deps，CUDA_ARCH_LIST=8.6）。RTX其他架构只修改构建架构，不改实验目标。Open3D0.19.0CPU vendor、numpy1.26.4、scipy1.15.3、cv24.11及trimesh沿用当前合法环境。source/env.sh保持CUDA、包和缓存隔离，不导入旧A1 common.py。

首次构建失败或系统依赖不同时先记录，不能用新简化相机或假深度替换。原始输入SHA校验失败即停止对应输入。若迁移目录，只能显式重绑定本地源索引并逐SHA验证，不能凭文件名换源。

checkpoint/PLY/GLB/原生投影结果位于任务local_results/<case_id>/，完整路径及SHA见assets_index；PNG只有figures/四张核心图提交，所有种子/初值/臂的六视角保留figures/full/。GLB统一mm→m一次，PLY及全部科研数组为mm，禁止只转换Ring或主体其中之一。

本轮只保存实际输出和评价，不将未知背面、闭合初始化或数值收敛解释为真实重建。复现不自动进入B1/B2。
