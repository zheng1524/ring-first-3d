# 缓存复算与实际执行

默认只读核验和CPU重绘；不自动重启模型、清理或下载。公开仓库没有原视频、权重、完整NPZ/GLB、隔离包，单独GitHub checkout不能无数据复跑。

```bash
cd /home/liu/ring_first_3d_neural_e0
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
TASK_E0_PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$TASK_E0_PY" experiments/TASK-NEURAL-E0-COMPARE-001/code/verify.py
```

[最终核验](metrics/FINAL_VALIDATION.json)不做训练/模型前向/配准，不读取GT。依赖版本：[原环境](provenance/ENVIRONMENT_CHECK.json)、[任务隔离包](provenance/ISOLATED_DEPENDENCIES.json)。原Torch2.7.1+cu128和CUDA环境未变；Open3D0.19从旧vendor只读使用。不要用系统Python3.8运行依赖Python3.12的检查。

需要重绘时，在保留本轮图版本之后，仅调用 `code/evidence.py`（CPU，重算已冻结几何的投影及图）和 `code/geometry_audit.py`（CPU几何诊断）。不重做神经预测；实际XYZ图调用仓库固定renderer，A→B逐字AST复用已有原三角面渲染器。重绘会修改同名派生图/指标，须在新复制的任务目录执行，并重建派生manifest。不可变神经输出冻结仍是 [ALL_MODEL_OUTPUTS_FROZEN_BEFORE_EVALUATION](provenance/ALL_MODEL_OUTPUTS_FROZEN_BEFORE_EVALUATION.json)；最终缓存重绘记录不冒充首次盲冻结。

本轮真实执行顺序：导入附件/独立worktree → `audit.py`（36输入契约及来源）→第一阶段commit/push → 用户追加清理授权 → `cleanup_stale.py`（一次58失效下载文件）→ `runtime/python`隔离安装 → 官方仓库固定版本 → `download_map.py`（600秒）→ `resume_map_tail.py`（唯一终段16.95秒，SHA通过）→ `sdf_run.py`（一次400步，域失败）→ `map_run.py`（加载别名和dtype机械适配错误均保留，M0–M2完成，M3布尔接口失败）→ `map_run.py --m3-only`（唯一M3补充成功）→ 全部模型输出冻结 → `evidence.py`/`geometry_audit.py`/`package_outputs.py` → 仅布局与CAD全范围图调整 → 最终核验、报告、manifest。

上述是实际记录，不是要求在本目录再次运行。`sdf_run.py`、`map_run.py`、下载与清理入口均拒绝覆盖已有运行记录。SDF的本轮一次优化预算已使用；另一次优化须由用户/PM明确重新授权，不能因本次失败自动加时。严禁重放清理脚本。

官方代码与原始权重SHA：[模型来源](provenance/MODEL_DEPENDENCIES.md)、[官方revision](provenance/OFFICIAL_SOURCE_REVISIONS.json)、[本地权重下载核验](provenance/MAP_DOWNLOAD_RECOVERY_RESULT.json)。SDF只延迟未用hash-grid import，原生MLP/MonoSDFNetwork/RenderingNetwork AST在verify中与官方源逐一核验；没有自制体渲染器。Map仅有数据/公制/精度边界适配，完整配置在 [Map](config/map_minimal.json)、[SDF](config/sdf_minimal.json)。失败初版源码SHA在各BEFORE_*文件和Git增量版本；最终可执行适配代码随本分支提交。

Source RGB/Mask/pack/native链和冻结相机完整身份：[输入资格](provenance/INPUT_ELIGIBILITY.json)、[旧004真正native补证](provenance/NATIVE_DEPTH_CHAIN_SUPPLEMENT.json)、[源码函数复用](provenance/CODE_REUSE_EXECUTED.json)。旧路径全部只读，除用户明确批准的58个失效下载文件；绝不写Dxy、GT或旧预测。失败保留NaN，不补历史值。

留出访问范围补充：P0为源身份/尺寸核验读取过B文件并解码RGB；没有在P0计算本轮B误差。神经loader只读取两个源视角，不接收B RGB/Mask；模型全部冻结后才开始新方法B评价。因此只称HOLDOUT_RECON_ONLY，不声称整个会话从未接触目标图。见 `provenance/HOLDOUT_ACCESS_SCOPE_NOTE.json`。
