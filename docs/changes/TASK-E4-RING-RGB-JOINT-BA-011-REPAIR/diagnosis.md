# 011-REPAIR 诊断

## 新发现 1：参考帧静默替换

配置要求 459，冻结 16 视角帧号 70–287 不含 459 → 程序静默取最近帧 287（索引 15）。
影响：参考相机与世界规范由 287 决定；不同实验臂若视角集合不同，参考帧可能不同。
规则：参考帧缺失必须失败或走显式批准的统一回退。

## 新发现 2：J2 的 CAD 无效状态处理缺失

`torus_contours` 在相机过近时抛 `invalid torus apparent-contour regime`，旧适配层未捕获 → BA 崩溃。
修复：返回 `CAD_INVALID_PENALTY` 残差块 + 状态；不得返回零残差。

## 门禁有效性证据

`check_modules()` 在本轮实际拦截两次：
1. `joint_ring_observation` / `contour_geometry` 从 011 目录加载（sys.path 顺序错误）；
2. 修复后再次验证失败路径。
→ 门禁不是形式主义，已产生真实拦截。
