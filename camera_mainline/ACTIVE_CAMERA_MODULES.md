# ACTIVE_CAMERA_MODULES

| 功能 | 正式唯一实现 | 历史来源 | 允许修改 |
|---|---|---|---|
| 原始数据/身份解析 | `tools/run_w0_camera.py`（读 PREPARED.json + video SHA） | 004/006 准备流程 | 接口可改 |
| 分割 | 冻结 INIT（sha256 `981aa596…`） | 013-PATCH/006 | 只读 |
| Ring-First | `src/ring_first_3d/mainline/native/camera.py` | 005 | 只读 |
| RGB tracking | 冻结 `track005.py`（002/frozen_calibration） | V6 | 适配层可改 |
| BA | 冻结 `local_ring_sfm.py::BA` | V6 | 只读 |
| W0 | `tools/run_w0_camera.py` 的 stage `w0`（从 012 收敛） | 012 | 可维护 |
| Held evaluator | `camera_mainline/code/evaluate_held_geometry.py` | 013-PATCH | 可修正 |
| SO(3) | `camera_mainline/code/camera_rotation_metrics.py` | 013-PATCH | 可修正 |
| Gate | `camera_mainline/code/camera_admission.py` | 013-PATCH | 可修正 |
| J2/J3（双轮廓 BA） | 不进入生产主线 | 010/011/012 | 研究资产，冻结 |

**规则**：正式入口只调用上表"正式唯一实现"。历史实验脚本保留为证据，新任务不得引用。
