# 复现与结果恢复

工作根目录：
`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011`

初始化预注册7ae5ab1，第一主循环52a014d，统一重启修复后的正式版本8e7c043。修复前G01/G02额外运行保留在engineering_validation_v1，详见ENGINEERING_V1_ARCHIVE/SOURCE_MAPPING，禁止删除或冒充正式对照。

使用原Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`；环境与父实验runtime/packages、runtime/pytorch3d一致；Blender5.0.1为 `/home/liu/blender/blender-5.0.1-linux-x64/blender`。无下载新框架、无新HERO预测或相机恢复。

PyTorch3D源码commit为`e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31`，源码工作树干净；编译扩展SHA、包版本及RTX3060 6144MiB环境见[环境回执](assets_index/ENVIRONMENT_RECEIPT.json)。这是只读环境记录，没有重装环境。

只读交付核验：

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY -B code/delivery_validate.py
```

原执行顺序：

1. 复制009原始帧/Mask/相机/CAD和原C，010固定内部深度ID/权重/点对；初始规则及源SHA先冻结。
2. `prepare_caps.py`按统一BROAD+实际上下分布规则，仅拟合缺失冠面的情况；其余C精确复用。
3. `preflight.py`生成固定谱基与完整梯度/回滚/半空间检查，`projection_gate.py`核对35相机-初值；`initial_blender.py`独立检查9初值。
4. `visual.py`和`cap_detail.py`输出九例初始化/两例详细图；所有C、代码、配置、输入和两张初始图写入PREOPT_FREEZE。原图此后不改。
5. 统一正式循环 `run_serial.py`按冻结顺序运行九例；每例只有C路线。不要再跑B裁切或S。
6. 最终预测冻结后运行 `evaluate_run.py`、Blender独立检查、`post_audit.py`、`figures_updates.py`与只读`objective_components.py`；随后`write_report.py`生成报告，`delivery_validate.py`生成模型路径索引。严格目标重放目前G02未通过，验证入口会保留FAIL并以非零状态退出，不应将其改成全PASS。

**不要直接在本交付根目录重跑prepare/freeze/train命令**，可能覆盖证据。若要完整复现，先复制代码与配置到独立目录，按SHA恢复相同原始输入/C和谱基，适配common.py中的本地路径，再建立新冻结记录。原数据不随Git上传，单独clone仓库不能恢复未上传的视频/深度。DXY、旧polyp_research、009和010只读。

新独立副本的训练入口：

```bash
$PY -B code/run_serial.py
```

该命令需要相同的PREOPT输入和通过的门禁。执行300外层提案不保证300接受；拒绝必须不推进参数/矩/step，梯度备选接受会明确重启Adam矩。checkpoint中accepted计数、active_modes、parameters54、Adam状态和NumPy/Torch/CUDA RNG全部保存，谱基与C初始化在inputs下。恢复时必须保持Chart、推断底盖元数据和当前active_modes，不可只加载顶点就声称无缝续跑。本轮结束后不自行续训。

Blender检查命令：

```bash
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --factory-startup --python code/blender_checks.py -- /绝对路径/独立副本
```

真实表面为NPZ中的F；F_solid包含单独标记的推断底盖，仅用于实体检查和诊断。PLY输出完整记账实体，必须连同inferred_base_faces理解，不得把灰色闭合面当真实可见组织。所有模型、参数、checkpoint及本地图的绝对路径/大小/SHA见LOCAL_RESULTS_INDEX。
