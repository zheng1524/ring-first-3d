# v0.2：Ring混合单元数值合同修正

原预注册提交10f70a1及首轮72个求解完整保留。代码复核发现：4×4面积池化单元若含Ring未知像素，原代码仍把它们混入区域目标比例。全部Ring的单元权重为0，但混合单元不满足原协议“未知像素不提供负证据”的要求。

修正仅在该单元的已知像素内归一前景比例；前景/背景质量按各自已知面积归一。新增控制：一个单元一半为已知Polyp、一半为Ring，其条件前景比例必须为1，原实现为0.5。该测试不依赖任何真实拟合结果或GT。

模型、源数据、A/B、D射线/像素对、初值、R0、正则、权重、求解预算和停止条件全部不变。两臂共同修正；不以B重新挑选模型。将首轮标为REJECTED_RING_UNKNOWN_POOLING_IMPLEMENTATION，保存在metrics/PRE_RING_POOL_FIX_ALL_FITS.json及对应PRIMARY，首轮模型/像素输出在local_results/pre_ring_pool_fix。修正后在再次冻结代码后按原72次预算重跑一次，以此作为正式比较。

原PREOPTIMIZATION_FREEZE.json仍原样保留，科学代码的有意差异由provenance/PREOPTIMIZATION_CORRECTION_v0.2.json绑定。不是阈值搜索，不增加第三种实验或形状。
