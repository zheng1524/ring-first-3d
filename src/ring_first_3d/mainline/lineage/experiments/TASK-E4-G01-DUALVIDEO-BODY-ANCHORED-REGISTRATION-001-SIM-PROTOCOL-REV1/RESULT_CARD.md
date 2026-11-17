# SIM_PROTOCOL_REV1：执行完成，二维主体配准尚未达标

**G0–G4全部实际运行，Runner 14个阶段及产物检查通过，82项回归通过。科学结论：M2在5/5主条件产生独立数值输出，但0/5同时满足冻结的0.5°/0.2mm相对位姿门限。没有按GT结果重调参数、重新选择Body或重跑DXY。**

S1的M2相对误差由2.000°/0.500mm变为1.925825°/0.126307mm；GT曲面MAE/p95为0.015705/0.060733mm。Robust ICP为1.500132°/0.009874mm，曲面MAE/p95约0.003588/0.012816mm；这些小曲面残差均不能证明正确相对旋转。Ring-only在本轮Y倾斜设置下5/5通过，不能将这项恢复归功于二维主体。

实现提交：`4bc294b982b07df97bc609c1af8a303f2c7d9dfa`。原始Runner冻结指纹：`60d5d4a602cd3c24dffebc9e163f9aa43f3e70be5e3ba80ff3a8a2616c2ec4ad`。历史原G0、TASK与失败记录原样保留，本轮为独立SIM_PROTOCOL_REV1。

[完整曲面交互](visualization/mesh_registration.html) · [真实对应逐点CSV](visualization/G2_CANDIDATE_AUDIT.csv) · [全部负结果/未匹配台账](visualization/FAILURE_LEDGER.json) · [共同数值条件配对](visualization/PAIRED_COMPARISONS.json)

DXY仅为当前Body初始化与中介映射提供冻结API的中心、basis、质量；没有算法修改或P/Q/直径精度研究。合成/原图各33帧数值候选；严格稳定分别11/33和5/33，不能将数值候选称为严格测量通过。E1/E2/显式代理各三初值均收敛；Body依冻结优先级选E1，并在全部配准中保持SHA不变。原TRF多初值使用冻结历史源码中的20261104+start种子；仿真协议的20261116种子与无随机误差矩阵分开记录。

G2数值覆盖和独立可评价覆盖分开报告：合成中介2670/3168有Body候选，984/3168同时可独立评价且非Ring接触未知；直接原像素1549/3168有候选，117/3168独立可评价。真实原图分支仅为G01-like虚拟射线诊断。所有12672个目标查询点、Face ID=-1、NaN、接触未知及置信度均已导出，不只展示成功点。

本地运行共822.655s，低于7200s预算；没有新的主体重建训练、实际HERO推理或跨视频BA。表面统计为完整局部Mesh顶点对独立GT三角面的距离，所有视频完整顶点均在分母内；这不是直径精度评估。L1与主S0–S4独立。


[完整报告](TECHNICAL_REPORT.md) · [RUN_MANIFEST](RUN_MANIFEST.json)
