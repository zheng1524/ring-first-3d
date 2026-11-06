# 复现与恢复

本地根目录：
`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010`

预注册commit：5aeec8b。当前结果含8个FINAL300与10个明确中断条件，不是18个完整300步结果。先看TECHNICAL_REPORT和FAILURE_LEDGER。

Python使用 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`，依赖沿用父实验runtime/packages和runtime/pytorch3d，官方PyTorch3D commit见FRAMEWORK_REUSE；Blender为 `/home/liu/blender/blender-5.0.1-linux-x64/blender`。没有重新安装/下载新框架。

只读核验（建议）：

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY -B code/delivery_validate.py
```

原始执行顺序：复制009冻结输入与小型源码→base_observations.py（平面反号修复）→prepare_initializations.py（P精确裁切/S独立球体与固定观测）→preflight.py→projection_gate.py→freeze.py→预注册commit→run_serial.py→freeze_predictions.py→evaluate_updates.py→Blender检查→post_diagnostics.py/extra_audit.py/replay_failures.py→figures.py→write_report.py。

**不要在本交付目录重跑准备、冻结或训练程序**，它们可能覆盖既有结果。完整复现应复制源码/配置到另一个独立根目录，按PREOPT_FREEZE与HISTORY_PROTECTION索引恢复同SHA原始输入，并将common.py的本地路径适配到新根目录后生成新的预注册。无需重新运行HERO、分割或恢复相机；不要照旧数据的路径重写旧实验。

在新的完整副本中正式运行命令为：

```bash
$PY -B code/run_serial.py
```

程序按固定九例和P/S逐一执行，最终失败条件也保留并继续其余案例。预检查没有optimizer.step；正式实际2729步、其中10步是未通过紧急检查的候选。按相同配置重现中断是有效复现，不应擅自改权重追求18个PASS。

独立Blender几何检查入口：

```bash
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --factory-startup --python code/blender_checks.py -- /绝对路径/独立副本
```

数据和状态：

- `inputs/Gxx/B_UNCUT.npz`：冻结B的静态副本。
- `inputs/Gxx/P_INITIAL.npz`：真实裁切，上面F/完整F_solid/推断面flag/边界顶点flag/原生顶点边面ID。
- `inputs/Gxx/S_INITIAL.npz` 与 SPHERE_INITIALIZATION.json：官方球体实际顶点、独立中心/半径来源；不是网络权重。
- `config/INITIALIZATIONS.json`：小型公开初始化参数索引，P/S共享归一在NORMALIZATION。
- `depth_observations`：原生固定候选及点对/权重，原HERO不改。
- `local_results/Gxx/{P,S}/STEP_*.npz`、`FINAL.npz`：真实毫米坐标表面。FINAL仅8个；失败条件有LAST_SAFE/UNSAFE_CANDIDATE。用于投影/深度只能用F，不得把F_solid中的推断盖当作可见组织。
- `.pt`：优化器、动量、global_q、origin/local、当前stage/step、NumPy/Torch/CUDA RNG及完整配置；用于工程恢复，不是预训练模型。恢复需同一current()边界投影与stage参数组，不能只加载顶点就称无缝续跑。本轮不恢复失败条件。
- 所有二进制与网格的绝对路径、字节和SHA见LOCAL_RESULTS_INDEX；原资产仍在本机持久存储，Git不包含整个数据集，单独clone仓库不能凭空恢复未上传输入。

派生评价/画图也会写本轮指标或图，默认不必重跑。未读取GT/Oracle；保持旧polyp_research、DXY与009只读。任何修改迭代策略的后续实验需新的人工授权和预注册，不能覆盖本轮失败证据。
