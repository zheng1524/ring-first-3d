# 方法与实现忠实性审计

| 原定设计 | 实际实现/代码 | 限制 |
| --- | --- | --- |
| 完整RoMa左SE3 | optimize020.py:main/run；R0精确复制019历史完整T，H=exp(qscale)H_RoMa，scale1、列向量004<-005、OpenCV c2w、mm | 没有提取yaw替代初值，没有360°重搜 |
| 无主体主线 | optimize020.py:no_body_hook；禁止读取BODY018与018arm网格；R0-R3和Ring消融完成并冻结后才启用R4 | 018归一化中心/尺度仅为等价坐标转换，不用它预测遮挡/权重或筛选点；输入视角继承祖先，不宣称端到端全独立 |
| 原相机/HERO/Mask/CAD | 全部019冻结native输入，68视角、原8个保护HOLDOUT；21源HERO名单在评价前登记 | 005绝大多数帧无原生HERO，不将21源报告成55帧深度验证 |
| Mask | ring020.py:RingRenderer，官方P3D Meshes/MeshRasterizer/SoftSilhouetteShader/OpenCV camera转换，180×320同019映射 | M=.5(正Ring均值MSE+已知非Polyp背景均值MSE)，不含019旧的混合无标签arc项；主体从不预测主线遮挡 |
| 真Inner/Outer | ring020.py:CADCurves，actual CAD面邻接的front/back符号变换边；O3D首次深度排除selfocclusion；hard-CAD内孔/外轮廓区分边身份；真实3D边端点Torch投影、obs到同标签投影线段距离求导 | 脱离梯度的边身份重选，投影距离本身有有效梯度；非平面r±.6圆，未自造通用渲染器 |
| 可见观察 | DXY可见语义点回溯到原始Ring-Mask边界≤2.5px，保持I/O；I/O无外推补弧 | DXY自身有5×5closing/opening；原Mask未改变，snapping避免将其合成边界直接当原观察。Polyp邻接不是遮挡真值 |
| Mid | 实际CAD中心线r5.6、720段投影；DXY中心线来自内外平均；72角bins，双侧权重1、单侧.25、未知0，再乘全局.05 | 与I/O相关；控制实验显示平均拟合Mid有约.16–.19px近似差；未当第三独立真值 |
| 距离目标 | I/O/C使用obs→对应投影curve的鲁棒Huber(d/3px)，按固定观察权重归一 | 是任务给定方向的曲线距离，没有替换为全部隐藏预测弧到观察DT，从而避免缺弧产生伪残差 |
| yaw对称性 | 所有Ring渲染/曲线只对相机绕Ring轴规范化，原实体CAD不变；pure-yaw控制与有限差分 | 不让离散CAD赋予理想Ring虚假yaw信息 |
| 独立地标 | features020.py直接复用features019.py的SIFT、RGB-MAGSAC、min3帧track、已知相机检验与3D点鲁棒优化；005仅自己的52FIT相机/RGB | 固定相机，无BA、无HERO辅助、无当前T互相生成点；Sigma仍unit-pixel代理非已校准物理置信度 |
| 同名3D身份 | 实际SIFT feature-ID跨帧RANSAC投票，至少两侧各2视角支持、按票数一对一；18对 | 非空间最近邻；3D辅助RANSAC5/18(.75mm)、中心偏移2.16mm，未满足预登记可行性，作为失败诊断完整评价 |
| 双向投影 | objective020.py:SymmetricFeatures；fwd: X004投影到H C005；reverse: H X005投影到C004；每轨迹先平均，再方向各半 | R2保留同一019正向观测，但使用020统一轨迹/向量Huber归一与共同2D-only EPI池，非逐位重演019损失；R2/R3可公平隔离方向项 |
| EPI | 真实2D–2D RGB-RANSAC，剔除两端都已可靠三角化的观测，按帧对/target归一 | 不因当前T误差重选内点；未补缺失观测 |
| 统一权重 | LR=.25M+.35I+.05C+.35O；F=.2、E=.02、prior=.01，q尺度.6mm/5°，prior=mean(q²) | noMid保持Ring总预算1(.25/.375/0/.375)，Mask-only=M；不按组/GT/HOLDOUT调参 |
| 统一优化 | optimize020.py，Adam.01、80候选、8级回溯、左修正≤1.2mm/10°、接受完整FIT目标≤旧+1e−6、拒绝恢复q与动量 | 与019相同提案基础；新四通道单位不同，没有套用019旧混合Ring loss的+.001硬阈值。物理CAD/尺度/SE3边界未放宽；四通道相互取舍必须报告 |
| 运行恢复 | 增加仅重启时q/Adam/步数恢复；原运行源码另存provenance/runtime_source_before_resume_support | 当前进程未更换损失或数据；恢复时seconds仅本段，不伪造总耗时 |
| 梯度 | 运行0/1/20/80各分量；冻结后另在每个endpoint的统一左切空间复核Ring与两向F梯度 | 梯度与Adam真实位移严格区分；后验shadow不回流优化 |
| R4 | 和R3同初值、视角、Ring/双SIFT、优化器、预算，仅增加019 FrozenRenderer.polyp | 主体不变形；R4在无主体预测冻结后进行，未用R4反选R3 |
| 评价 | evaluate020.py，所有pose冻结后才提取HOLDOUT对应、独立O3D body/CAD投影、真实原面HERO可见性 | body IoU只是模型重投影代理；HERO非GT；没有独立位姿真值、ICP或尺度对齐 |

最终输出只是视频级共同SE3，视频内相对相机严格不变。不重新推理HERO，不生成融合面，不把诊断叠加称融合。DXY保持只读。

初始化来源链见provenance/R0_FULL_ROMA_MATRIX_LINEAGE.json：020←019注册表←Phase-D的D1_candidates←历史H_frozen←历史baselines，完整矩阵逐项相同。只读取授权的历史T，不读取历史融合Mesh生成预测；不把本轮无HERO损失描述为整个历史初始化链从未涉及深度。

评价代码静态审查修正了019的一处Ring次序遗漏：若目标HERO深度自身已位于CAD后方，不得用它证明前方自由空间。020把这种目标支持标为Unknown并单列计数，原始源观测分母不变；所有方法含R0/019A5统一重算。修正发生在任何HERO/HOLDOUT评价前，有4项已知CAD射线控制测试，绝不回流优化。曲线观测是原Mask边界像素中心，仍有量化/分割不确定性；Mid控制误差包含拟合与离散采样，不单独归因为纯透视。
