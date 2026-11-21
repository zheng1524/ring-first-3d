# ERROR_FIX_LEDGER（014 的八项）

| # | 原问题 | 根因 | 修改文件 | 最小验证 | 状态 |
|---|---|---|---|---|---|
| 1 | 004 直接沿用旧 005 相机 | 无 004 的 W0 | `tools/run_w0_camera.py` | 004 用同一入口重跑：held 70→1.78 px | **FIXED** |
| 2 | 视角顺序与相机绑定混乱 | 未按 raw_frame 排序 | 同入口（`sorted(key=raw_frame)`） | 排序后重算 rotation_to_previous 中位 0.13/0.49° | **FIXED** |
| 3 | Held 统计口径混乱 | raw/valid/degenerate 语义不清 | `camera_mainline/code/evaluate_held_geometry.py` | 每条轨迹单一主失败类别 + 守恒计数 | **FIXED** |
| 4 | K 未显式传递 | 使用 `K_DEFAULT` | 同文件（`project/triangulate` 均带 K） | 单测 `test_k_used`（K 改变输出改变） | **PARTIAL**：默认值仍在签名中，但所有调用显式传 K |
| 5 | 来源正深度失败未统计 | 未计数 | `evaluate_held_geometry.py`（source_depth_fail） | 计数守恒 | **FIXED** |
| 6 | Ring MAE 口径变化 | 顶点 KD-tree vs 线段距离 | 未统一 | 005 复现 0.964 vs 0.829 | **OPEN**：需把汇总评价切到线段距离 |
| 7 | 可视化与 CSV 不一致 | 手工状态 | 图由 `CAMERA_ADMISSION.csv` 生成 | 本图状态来自 CSV | **FIXED** |
| 8 | 014 缺复现入口 | 一次性脚本 | `tools/run_w0_camera.py` + 本报告命令 | dry-run 与实跑均可 | **FIXED** |
