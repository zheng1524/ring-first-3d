# GROUND_TRUTH_LEAKAGE_AUDIT

| 入口 | GT 是否进入 |
|---|---|
| 生成观测 `rgb_observations` / `ring_observations` | **是（允许）** |
| 三角化初值 `triangulate(obs, cams_init/GT?)` | 初值用 **初始相机**（L1 用 GT 相机，因为"正确初始化"就是 GT）；**从不**用 GT 三维点 |
| 地标先验 `X0` | 来自三角化（L1 误差 1e-6 mm 是三角化正确，不是 GT 输入） |
| 可见边缘 | 来自初始相机 |
| 权重/门限/初始化选择 | 未使用 GT |
| 最终评价 | 用 GT（允许） |

**唯一争议点**：L1 的初始化相机 = GT 相机（这正是 Level 1 的定义"正确初始化"）。
L1 的地标来自二维观测三角化，非 GT 三维点。L2 的初始化 H = identity（不是 GT）。
