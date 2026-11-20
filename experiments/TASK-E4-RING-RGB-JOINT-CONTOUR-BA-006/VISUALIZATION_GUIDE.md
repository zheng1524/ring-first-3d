# VISUALIZATION_GUIDE

本轮可视化尚不完整（P3 未运行），已生成的图：

| 图 | 文件 | 怎么看 |
|---|---|---|
| A（合成） | `visualization/A_method_comparison/figA_synthetic.png` | 左：真实位姿下的 CAD 内外投影（黄/橙）；中：DXY 式拟合椭圆（青/紫，含 4% 尺度误差）；右：两者叠加。用于判断 τ=1 px 的柔性带是否足以容纳该量级模型误差 |
| C（合成） | `visualization/C_loss_tradeoff/figC_tradeoff.png` | 横轴 E_ring、纵轴 E_rgb，不同 τ 的点。**注意**：当前点集未做对称对齐，离散程度主要反映 180° 对称解，不能直接用于选 τ |

## 颜色约定（后续图表统一）

- CAD 内轮廓：黄色实线；CAD 外轮廓：橙色实线。
- DXY 内：青色；DXY 外：紫红色。
- 真实可见弧：实线；推断弧：同色虚线（低透明度）。
- Ring Mask：蓝色；Polyp Mask：绿色（**不再合并显示**）。

## 未生成

图 B（Ring-Only vs JointBA）、图 D（多视角投影）、图 E（相机网络，需用 `c2w_mm[:3,3]` 取中心）、图 F（局部放大）——均依赖 P3 的 BA 结果。
