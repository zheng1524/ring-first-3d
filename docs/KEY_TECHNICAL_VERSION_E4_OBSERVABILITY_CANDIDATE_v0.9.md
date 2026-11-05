# E4 可观测性 Gate A 候选 v0.9

状态：`REPORTED / GATE_A_COMPLETED / NATIVE_RECOVERY_NOT_CERTIFIED`。仅IIa6.5_R10一个原生CAD场景，Gate B/C/D未运行，等待人工。保留[v0.8](KEY_TECHNICAL_VERSION_E4_SAME_KERNEL_CANDIDATE_v0.8.md)和全部历史记录，不升级正式主线。

新实验将原生CAD目标与旧法向编辑/同核目标分开。N0底场由Ring规则独立生成：椭球中心为Ring中心+(0,0,0.5mm)、半轴(2.5,2.5,0.75mm)，不读取原生CAD底场；真正优化仍为局部中心XYZ及幅值四参数，九参数未开放。P0未做Mask九参数校准，结论仅针对该粗初始化/单核族。

固定五个相机、3拟合/2留出、Ring CAD；用户允许一致选择后保留原K的实际66.787°水平视场。全部Blender/Open3D主体/Ring重投影门禁通过；GT防火墙实测拒读原生GT、旧BASE_FIELD及.blend。冻结提交cb959b3，预测全部冻结后才做原生三维审计，无原生q_GT。

- 有限幅度证据：预登记弱方向改变约0.300mm/0.374mm³，五视角相互Mask IoU仍为1/1/1/1/0.99978。说明本例有轮廓难约束的三维变化。
- 数值限制：a=0三个中心列严格为零；非零seed弱J对ε减半敏感，相对变化约0.967，不能凭数值满秩认证可靠定位。3/4受控方向端点未达要求的物理幅度，失败保留。
- 目标偏置：旧同核B的错误幅值方向降低原loss，触发唯一一次0.5亚像素目标边界修正。原版/修正版使用同一P0、seed、数据和Powell预算，分别388/273次评价。原生CAD拟合/留出IoU分别0.667063/0.687805与0.666648/0.684812，修正版未优于原版。
- 三维限制：统一Chamfer MAE约0.319264/0.320797mm；固定Sobol差异体积P0 15.068→原版15.213/修正版15.245mm³，几何差异未改善。粗节点积分存在平底混叠，原表保留并以独立积分核验，不据此改预测。
- 表达上限：GT相对P0需要同时增加和删除体积，而一个非负核乘单幅值只能单符号改变占据。观测不足、目标偏置和表示不足均有证据，搜索失败仍inconclusive；不能仅换求解器归因。

所有保存轮次闭合单连通、无检出Ring碰撞；独立Blender端点无非邻接三角面自交检出，邻接/退化情形未作完整认证。未运行GPU、新网络、TRF、其他形态或多核实验。

[Gate A报告](../experiments/TASK-E4-2D3D-OBSERVABILITY-001/GATE_A_TECHNICAL_REPORT.md) · [来源防火墙](../experiments/TASK-E4-2D3D-OBSERVABILITY-001/SOURCE_AND_FIREWALL_AUDIT.md) · [原始指标](../experiments/TASK-E4-2D3D-OBSERVABILITY-001/metrics/NATIVE_POSTERIOR.json) · [失败记录](../experiments/TASK-E4-2D3D-OBSERVABILITY-001/FAILURE_LEDGER.md)
