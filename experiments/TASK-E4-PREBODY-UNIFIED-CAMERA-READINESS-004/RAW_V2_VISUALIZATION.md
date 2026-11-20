# RAW-V2 可视化说明

全部图来自**同一来源链**：体模视频 → 解码帧 → INIT 分割 → Mask → 相机（复用 005 求解器）。
不含旧冻结 Mask 或旧相机。

| 图 | 文件 | 内容 | 怎么读 |
|---|---|---|---|
| 1 | `density_comparison/fig1_metric_curves.png` | 10 段视频在 N=8/16/22/32 下的 held 中位与 Ring 门禁通过率 | 左图折线下降=密度有效；右图上升=覆盖变好。G03/004 始终在 100 px 量级 |
| 2 | `ring_projection/fig2_ring_panels.png` | 三行：好（G03/005 N=32）、中（G02/005 N=22）、差（G03/004 N=22）的 RGB / Mask+CAD 投影+观测点 / 观测点特写 | 黄点线=CAD 环投影，红点=Ring 观测，二者重合即 Ring 准；差例中红点明显偏离黄线 |
| 3 | `camera_network/fig3a_G03_005_N32.png` | G03/005 N=32 的相机三维布局 + Ring CAD（黑圈） | 相机环绕环心分布，无孤立点，对应 6 个 VALIDATED |
| 3b | `camera_network/fig3b_G03_004_N22.png` | G03/004 N=22 同视角 | 形状看似正常，但 RGB 一致性极差——说明**布局整齐 ≠ 相机正确** |
| 3c | `camera_network/fig3c_G02_005_N22.png` | G02/005 N=22 | held 6.61 px，介于两者之间 |
| 4 | `density_comparison/fig4_G02_005_layout.png` | G02/005 在 N=8/16/22/32 的相机布局（嵌套子集） | 看新增相机是否补到不同方位；N=32 并未带来更好的一致性（held 反而 8.58） |
| 5 | `ring_projection/fig5_perview_held.png` | 逐视角 held 误差（对数），按最差排序，三例对比 | 长尾=少数坏视角；G03/004 整条曲线都在高位 |

## 复核建议

1. 先看图 1：确认密度对哪些实例有效、对哪些无效。
2. 再看图 2 的第三行：这是本轮仍未解决的 G03/004。
3. 图 3b 与 3a 对比：说明"相机排布好看"不能替代 RGB 一致性证据。
