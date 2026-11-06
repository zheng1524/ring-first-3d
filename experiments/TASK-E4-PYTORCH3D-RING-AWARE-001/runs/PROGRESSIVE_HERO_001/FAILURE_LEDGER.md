# 失败记录

没有为了终点指标改变规则、删面、平滑、换参考或回退到较好中间轮。

|病例|条件|失败|证据|
|---|---|---|---|
|virtual|B|CONFIRMED_SELF_INTERSECTION；Ring面对0 / 自交面对21，顶点最深穿环0.000000mm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|
|virtual|C|CONFIRMED_SELF_INTERSECTION；Ring面对0 / 自交面对5，顶点最深穿环0.000000mm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|
|virtual|D|CONFIRMED_SELF_INTERSECTION；Ring面对0 / 自交面对7，顶点最深穿环0.000000mm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|
|real|B|RING_PENETRATION；Ring面对28 / 自交面对0，顶点最深穿环0.005486mm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|
|real|C|RING_PENETRATION；Ring面对134 / 自交面对0，顶点最深穿环0.041189mm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|
|real|D|RING_PENETRATION；Ring面对212 / 自交面对0，顶点最深穿环0.053264mm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|

补充限制：

- 虚拟B虽曲面距离比A低，p95法向粗糙度更高且有自交；C/D更圆滑也不能掩盖约2倍体量与GT误差。
- D相对C的Mask覆盖下降：虚拟留出约1.98个百分点，真实约0.092个百分点，均保留为潜在覆盖退化；未以更低深度误差宣布整体成功。
- 真实HERO为相关模型观测，不是精确GT；未校正参考尺度、相机或原生深度。真实六相机INSUFFICIENT_EVIDENCE，更新留出并非初始化独立。
- 虚拟D理想GT深度上限不能冒充HERO迁移成功，也未解决隐藏底面。
- FP32联合方向FD初检失败记录见PREFLIGHT_FP32_FD_FAILED.json；FP64同条件通过。
- 第一次B在SHA检查中被观测隔离hook提前拦截，实际optimizer.step=0；源代码/旧freeze/stdout保留于assets_index/pre_run_guard_failure和PREOPT_FREEZE_V1_GUARD_REJECT。修正hook安装时机后重新冻结，没有改目标/参数。
- 后验公平性首次错误地比较FP32世界坐标往返与原始FP64数据，原日志保留；改为与A0及同一渲染表示逐位比较，另报最大浮点往返差。没有修改任何Mesh。

本轮数值停止阈值用于非有限/爆炸候选，未把Ring/自交纳入优化目标；离线几何失败如实报告，不追调为PASS。
