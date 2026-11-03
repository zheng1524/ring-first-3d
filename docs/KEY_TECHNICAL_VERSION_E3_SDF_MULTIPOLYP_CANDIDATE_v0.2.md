# E3-SDF 多物理息肉探索候选 v0.2

2026-11-03，EXPERIMENTAL / WAIT_PM_REVIEW，未提升正式主线。v1.0和SDF v0.1历史不改。

任务：TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001。研究者将原单参考200k安排改为本地多物理组探索；核实旧正式M1=0后，明确批准新M1以1000为基线、累计10000。旧M0完整11k状态及全部历史保留，不假充M1。

冻结G01_004 ref08/ref13/ref03；G06_004 ref04/r01/r06；G08_005 ref04/r02/r01。每视频三参考共享一个SDF，三个物理组独立初始化、独立优化器/状态、公制域，不混G01_005。9源均按最新统一Camera Gate复核，6份INSUFFICIENT、3份CONDITIONAL_USABLE，研究入组不等于GT位姿。G07仅两可入组方向块，未放宽阈值。

官方MonoSDF commit12513009，沿v0.1真实完整自适应采样、体渲染、runner更新块与M1损失；数据派发/监测/恢复端口有逐项diff。源/Mask/HERO/K/c2w/CAD不变；G01/G06派生输入逐字复用当前N0，G08按同一固定A2派生法一遍，新增孔洞和风险保留。网络输入等比crop320×240、原生ID和轴向Z/欧氏ray转换不变。

各10000次真实Adam；1024rays；1000步warmup和原200k指数调度不压缩。保存1000/2000/5000/10000连续模型，同一256³网格提取真实iso0全部面，无删面/补洞/几何平滑。串行本地GPU；固定原生观测分母，GT全部NOT_EVALUABLE。

状态及最新结果由[任务报告](../experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001/TECHNICAL_REPORT.md)与各组STATUS维护。短程横向趋势不作MonoSDF最终成败结论，完成后不自动扩大预算。云端推荐单4090 24GB/8vCPU/32GB RAM/100GB持久化盘，按实际环境和完整检查点迁移；不在本任务自动购买云算力。
