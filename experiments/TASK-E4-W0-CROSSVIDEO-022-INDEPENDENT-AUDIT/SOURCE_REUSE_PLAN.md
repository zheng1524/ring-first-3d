# SOURCE_REUSE_PLAN（函数级）

| 历史功能 | 文件/函数 | 当前 021 状态 | 023 必须做什么 |
|---|---|---|---|
| SIFT 特征 | `019/features019.py::features(v)` | 未调用；021 自己用 `cv2.SIFT_create(6000,0.01)` | 用历史函数替换 021 的提取，缓存 `features/<id>.npz`；路径已验证可行（019-REPAIR 中 619 特征） |
| 同视频轨迹/三角化 | `019/features019.py::matches/landmarks` | 未调用 | 接入：ratio 0.72、mutual、MAGSAC、≥3 视角、soft_l1 三角化；产出 004/005 各自 3D 地标 |
| 跨视频身份 | `020/features020.py` | 未调用 | 接入，产出 2D-2D / 2D-3D / 3D-3D 三类，供 `L_F` |
| Ring 目标 | `020/ring020.py::RingRenderer/CADCurves` | 未调用（用 `torus_contours` 代替） | 恢复 M/I/C/O 四项（权重 0.25/0.35/0.05/0.35）与可见弧/自遮挡；若缓存缺失，先用 W0 DXY 观测构造并做与 `torus_contours` 的数值对照 |
| 目标函数 | `020/objective020.py::SymmetricFeatures` | 手动重述（Ring+EPI+Prior） | 复现双向 3D 重投影 `L_F`，权重 0.2；EPI 去重 |
| 优化器 | `020/optimize020.py` | numpy 重写 | 或直接复用（torch Adam + deepcopy state_dict + LOCAL_SE3_BOUND）；必须提供 checkpoint |
| 门控 | `020/gate020.py`、`feature_gate020.py` | 未调用 | 可选择性接入做梯度/纯 yaw 检查；不替代 W0 准入 |

**不动**：`tools/run_w0_camera.py`、`camera_mainline/*`（除 022 建议的 positive_depth 补丁）、DXY、Ring CAD、HERO、Body。
