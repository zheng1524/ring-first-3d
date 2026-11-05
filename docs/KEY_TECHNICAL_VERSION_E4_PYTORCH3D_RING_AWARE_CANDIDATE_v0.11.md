# E4 PyTorch3D Ring-Aware 候选 v0.11

状态：完成一个官方复现及虚拟IIa6.5/真实G01_004两个病例的快速对照，等待人工审核；不升级正式主线。保留v0.10渐进SDF和全部P0/S1/S2。此候选为PyTorch3D共享Mesh顶点优化，不将其称作神经SDF训练。

官方提交 `e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31`，源代码未修改。本地RTX3060 Laptop 6GiB、torch2.7.1+cu128、CUDA12.8独立编译。官方cow多视角轮廓教程2000步SGD复现：完整20视角MSE 0.186132→0.002302，真实Mesh更新，16位OBJ重载V/F位级一致，官方bin_size=0独立重渲染差0。默认粗分箱同Mesh重复渲染有像素波动，原失败保留。密集项目P0分箱容量溢出仅增加容量到至少全Mesh面数，未改相机/Mask/几何/门槛。

11视角P0与Open3D硬轮廓IoU全1，native Blender GT投影IoU 0.999288–1.0；官方OpenCV相机转换与像素中心映射明确。真实六相机仍INSUFFICIENT_EVIDENCE，条件研究入组；真实“留出”只针对更新阶段，初始化曾用其他视角。

新增Ring组件只借鉴DXY截面出口及两侧Mask邻接，不调用P/Q或DXY拟合。A=PP、B=PB、C=BB、D=未知；2D证据与CAD深度互补，局部未知负监督放宽，可见正监督保留，CAD前方错误Mesh仍受官方轮廓梯度约束。Ring/CAD不学习，三维碰撞单独检查。

初版连续软zbuf反传在真实G01产生1e8–1e13异常梯度，有限差分约1e-4，首步几何爆炸；原有限/非零梯度门禁误判，全部失败证据不回写。仅一次隔离数值修复：每轮离散重算前后次序，不对zbuf次序反传，官方轮廓顶点梯度继续有效。当前实现与结果在 `runs/VISIBILITY_ORDER_REPAIR_001`，原根目录local_results是失败初版，不能混淆。

修复配对两病例各Baseline/Ring-Aware 300步，初值、相机、两随机训练视角序列、SGD(lr1,momentum.9)、官方正则和采样设置一致。0/100/200/300全保存，最终固定300步，不按GT选中间轮，无新增HERO/对应损失或优化器。每次预测单独冻结再评价，修复不由GT好坏驱动。

- 真实G01：留出IoU 0.879616→0.896136。65个被Ring遮挡的P0首次面固定顶点平均内缩代理1.155257→0.899249mm，约减少22%，但65/65仍内缩；P0体积858.919mm³，Baseline500.807、Ring-Aware516.426，仍约损失40%。无完整GT，不认定真实隐藏组织恢复。
- 虚拟IIa：无PP/PB截面，6000个GT样本中Ring遮挡分母0。两条件轮廓改善，平均Chamfer较P0减小，但差异体积变大，出现锯齿。Ring-Aware与Baseline几何差异很小，不证明遮挡收益。
- 修复版Mesh闭合、单连通；FCL/Blender未检出Ring交集或非邻接自交；光滑、闭合和高IoU不代表准确。没有额外平滑、补洞或删面。

原版优化前遮挡位置图已检查；修复权重图因只读元数据副本缺失在运行后补生成，时序限制明确记录，不伪称重新人工通过。后续复跑必须先生成图。

工程基线可以作为下一阶段候选，尚未证明几何正确。若人工授权，值得验证真实HERO约束能否保护主面；本轮不自动增加损失、不扩组、不改DXY。

[技术报告](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/TECHNICAL_REPORT.md) · [当前结果](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/metrics/FINAL_RESULT.json) · [失败记录](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/FAILURE_LEDGER.md) · [复现](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/REPRODUCE.md)
