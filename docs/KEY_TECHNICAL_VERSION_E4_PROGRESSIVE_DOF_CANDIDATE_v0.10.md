# E4 渐进自由度候选 v0.10

状态：`REPORTED / MIXED_GLOBAL_CORRECTION_LOCAL_NO_EFFECTIVE_SIGNAL`。只一个IIa场景、一条P0→S1→S2轨迹；中心释放未触发，Gate B/C/D未运行，不升级正式主线。保留[v0.9](KEY_TECHNICAL_VERSION_E4_OBSERVABILITY_CANDIDATE_v0.9.md)和全部Gate A原证据。

新目录TASK-E4-PROGRESSIVE-DOF-001复用原生CAD GT、五相机、Ring、目标标签和同一独立P0，不重渲染/导出数据。P0零面V/F完全一致；全局中心/三半轴通过参考四面体网格的六参数仿射更新，旋转固定。各向异性字段不伪称严格单位梯度SDF，所有物理误差从实际零面Mesh取得。

冻结代码668dbe1，S1开放6参数，S2保留全局6并增两个相反符号核幅值，核中心只由三拟合视角轮廓残差medoid选取。半径固定1.8mm；原版Powell/原轮廓目标不变，没有同时替换损失。固定残差J只作诊断，实际优化未使用其梯度。

- S1：500次评价、5轮、286.6秒，预算终止未充分收敛。拟合/留出IoU从0.638480/0.673665升至0.969566/0.957964；Chamfer MAE从0.325187降至0.270066mm。但统一差异体积代理从15.025004升至15.873093mm³，质心误差增大；全局ΔZ靠近预登记下界。
- S2：216次评价、2轮、约126.1秒，最终拟合/留出IoU为0.968642/0.961934，Chamfer MAE 0.267582mm，差异体积代理15.782871mm³。此阶段全局仍开放，不能把总变化都归于核。
- 局部幅值约−0.005109/+0.002402，停用两核反而令实际拟合loss略低。固定最终全局参数下局部最大外扩/内缩约0.007162/0.003367mm，固定GT点方向平均误差只改善约0.0000556mm，不认定实质独立局部收益。因此按预登记信号门槛不释放核中心，S3 NOT_TRIGGERED。

所有优化结果先冻结SHA再读原生GT。统一2^19 Sobol查询域由P0与最大仿射范围定义，阶段内一致；GT/预测均用实际闭合Mesh占据，差异体积为积分代理，Mesh净体积另报。体积代理不可与Gate A不同采样域的小读数直接比较。无GT选初始化/核/模型，无历史测量回退。

后验诊断发现S2约6.116mm³占据低于GT最低Z，约76%的较大GT曲面误差在两核支撑外。轮廓改善与真实三维并不一致；当前局部支撑有限、短程搜索未收敛均有证据，但没有GT最优表达试验，不能将原因唯一归于表达或搜索，也不能据此否定全部SDF路线。未据GT添加地板约束、重选核或增加复杂模型。

同一六参族的S1第1→2轮，loss从0.666171降至0.139669、拟合IoU从0.821192升至0.939609，而Chamfer MAE从0.264342增至0.276600mm、差异体积从13.990456增至15.850538mm³。此保存轨迹直接证明更低二维目标并不保证更接近GT；未据此回退到GT更好的中间轮。全部连续转移另存审计表。

保存的Mesh闭合、单连通、Euler=2，Ring碰撞未检出；Blender端点EXACT Ring交集和非邻接自交均未检出。几何连续/光滑不等于真实恢复。完成后停止，等待人工审核。

[技术报告](../experiments/TASK-E4-PROGRESSIVE-DOF-001/TECHNICAL_REPORT.md) · [结果汇总](../experiments/TASK-E4-PROGRESSIVE-DOF-001/metrics/RESULT_SUMMARY.csv) · [归因证据](../experiments/TASK-E4-PROGRESSIVE-DOF-001/metrics/DIAGNOSIS.json) · [失败记录](../experiments/TASK-E4-PROGRESSIVE-DOF-001/FAILURE_LEDGER.md)
