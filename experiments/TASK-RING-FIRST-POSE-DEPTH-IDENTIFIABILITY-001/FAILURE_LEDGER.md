# 失败及证据不足台账

| 项目 | 实际问题 | 处理及证据 | 状态 |
| --- | --- | --- | --- |
| A首次调用 | AST提取的render进入common命名空间，主模块找不到render；预测前NameError | 原BEFORE_A保留；A_PORT_FIX_BEFORE_PREDICTION记录唯一命名空间端口修复，未改阈值/参数；重跑与历史Raw六字段逐位一致 | ENGINEERING_FIXED |
| 远端核实 | 严格SSH返回kex_exchange_identification Connection closed；不能证明租用资源状态 | 本轮全部本地CPU，未重连绕过主机检查，也未启动/终止服务器任务 | NONBLOCKING_FOR_CPU |
| G01 A第二帧对 | RF RGB共同MAE高于SIFT（23.07 vs17.64），虽覆盖/轮廓更好 | Fig1第二行、PAIRED_A_COMPARISON.csv，保留反例 | NO_UNIVERSAL_RGB_ADVANTAGE |
| G06/G08 A | RGB几乎相同；不能仅因RF覆盖高就认证绝对姿态 | Fig1后两行；实际资格不升级 | CONDITIONAL_DIAGNOSTIC |
| 全部A | SIFT只有方向，A-S1借RF平移长度；无独立姿态GT | A_POSES.json：R/t差异非真误差；原生SIFT公制结果NaN | ABSOLUTE_ACCURACY_NOT_EVALUABLE |
| G01/G06 B双视角 | 合格HERO-backed RGB 2D对应为0；RGB大多背景 | B_OBSERVATION_COUNTS.csv；空块保留，不用预测或背景假深度补点 | INSUFFICIENT_CORRESPONDENCES |
| B轮廓残差 | 不同视角Mask边界不是材料点，代理可制造额外信息；同源HERO不独立 | 追加去silhouette消融；主三消融不改写；Fig3/4不能单独认证物理可辨识性 | PHYSICAL_ATTRIBUTION_UNPROVEN |
| B可见性 | 大扰动会切换遮挡/覆盖；MAE可能受有效集合影响 | 固定J行及RMS；动态MAE/覆盖另列；±.2mm/±.25°不冒充小步局部导数 | NONLINEARITY_RECORDED |
| G06 6–8视角 | 当前只有5份合法HERO来源 | 按已有固定顺序2/4/5；未新推理、放宽Camera Gate或换有利视角 | NOT_EVALUABLE_SOURCE_COUNT |
| GT/测量 | 未执行独立物理精度或Dxy测量，不能计算MedARE/MAE/p95/max | 全部NaN/NOT_EVALUABLE；无历史测量回退 | OUT_OF_SCOPE |

本轮没有SIFT返回失败组（4/4数值恢复），不等于4/4相机科学认证。没有训练/OOM/参数发散。没有将无足够证据改写为结构性不可辨识；没有把诊断最小值采纳为新的相机/HERO。
