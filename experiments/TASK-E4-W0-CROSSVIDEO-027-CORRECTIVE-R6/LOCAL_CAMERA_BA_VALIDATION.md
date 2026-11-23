# LOCAL_CAMERA_BA_VALIDATION

- 参数布局：54（H 6 + 2×6 局部 + 36 点），X 从索引 18 开始；`test_M4_parameter_layout` 通过。
- `test_M4_updates_released_camera`：人为扰动 004 非锚点相机后，M4 使被释放相机 `dx != 0`，冻结相机 `dx == 0`。
- 端到端 B/F 组（0.25°/0.5° 相机扰动下的 M2/M3b/M4、F1/F2/F3 释放策略）本轮 **NOT_EXECUTED**（时间预算）。
- 结论：**M4 的工程正确性 PASS，科学结论未取得。**
