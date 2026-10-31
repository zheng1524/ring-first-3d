# TASK-NEURAL-E2P6-INITIALIZATION-AND-STABLE-LOSS-001

用户正式授权：沿用同一Phase E会话与E2.5真实官方MonoSDF，验证一个固定几何壳校准规则、稳定log-optical Mask BCE、必要时的弱HERO表面锚点及固定观测分母覆盖评价。独立分支从1eb9cc7续作；不重跑E1/E2/E2.5审计，不修改旧资产。

统一规则先冻结：同种子、固定ROI半径一半、128 Fibonacci壳点、bias0 raw SDF中位数校准，禁止在看到射线效果后调整壳或搜索其他规则。005困难参考全部保留。旧16条与不重合64条额外探针先固定，每源HERO前命中门槛50%。

真实官方网络CPU前向和完整参数autograd允许；初始化是构造期校准，不执行优化器或训练更新。P2检查正常、空场、全正、全负、Ring前缀及FP32/FP64；P3只有在稳定Mask不具备有效几何恢复梯度时启动弱HERO候选，权重/相关性/可见性沿用冻结数据，不宣称HERO为GT。

GPU、optimizer.step、训练、MapAnything、GT/Oracle、目标选参、HERO/Ring-First/CAD/P0/Dxy修改均禁止。离散hit计数只作评价/停机，不构成训练梯度。任一覆盖下降不得因总loss更低宣称改进。若单一规则失败，停止校准搜索并保留失败；其他测试只作同一规则下的机制诊断。

交付根目录的INITIALIZATION_VALIDATION.csv、STABLE_MASK_GRADIENT_TESTS.csv、COVERAGE_DEGENERACY_VALIDATION.csv、THREE_REFERENCE_NEURAL_GATE.json，以及单份TECHNICAL_REPORT、FAILURE_LEDGER、GPU_MVP_READINESS和四张证据图。
