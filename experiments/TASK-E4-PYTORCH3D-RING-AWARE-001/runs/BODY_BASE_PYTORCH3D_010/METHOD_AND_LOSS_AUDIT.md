# 方法与损失审计

本轮新增内容仅为平面符号等价修复、冻结B的几何裁切、独立球体初始化与现有统一更新/诊断的薄适配；不是新的SDF、相机配准或神经模型。类型只在名单、统计与图版出现，base_observations/clip_mesh/train不按Ip/Is/IIa分支。

## 复用与差异

- 官方PyTorch3D源码 `e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31`，不下载/重装。官方ico_sphere函数文件及SHA见FRAMEWORK_REUSE；不是预训练网络。复用原项目SoftSilhouetteRasterizer/Shader、Meshes、SGD和正则。
- VISIBILITY_ORDER_REPAIR_001的Ring-Aware前后次序与A/B/C/D代码不变：每步重算离散CAD可见性，禁止不稳定z-buffer次序梯度。保持真实Mask/CAD的前后关系诊断；没有新增三维Ring碰撞损失。
- PROGRESSIVE_HERO_001的100 GLOBAL6 + 200 LOCAL与SGD lr1/momentum.9，D2的E3可靠绝对/相对深度。原D2曾为隔离损失只做LOCAL；本轮依照用户渐进更新要求恢复这条既有GLOBAL6日程，其稳定性未被预先认证。结果确实暴露它不适合全部九例；不称为成熟稳定性的再次证明。
- p3d.Case只扩展route初始化、同病例共享归一和F/F_solid/底盖元数据；camera/renderer/aware公式不变。Depth仅加载FIT中实际有深度者，RGB-only不造深度。
- P的推断底盖始终不在c.F中。形状保护与可见性判定也仅用上表面。底盖边界通过切平面投影限制法向运动，作用于有该元数据的所有Mesh；S无人工底盖。没有对整个上表面添加半空间可行性屏障，因此后续出现穿基底/自交是本轮真实失败。

## 平面与裁切

`normalize(n,d)=(n,d)/||n||`；与参考n0点积负时同步翻转n,d。夹角用atan2叉积模和点积，距离变化在同一可靠原生内部参考位置x*比较 `|(n-n0)·x*+(d-d0)|`。真正保留侧使用内部可靠HERO点中位符号作为代理，不能从稳定性推出解剖正确。G09内部点中位高度约0.026mm，小于背景拟合0.3mm容差；记录不确定，不按此取消运行。

P读取009 B_SELECTED真实顶点和面；使用逐三角形Sutherland–Hodgman半空间裁切，共享原始边交点缓存，保留完整上方面。沿切割边界环用平面耳切生成独立推断底盖。当前九例单环；若遇多环或非流形将明确报错，禁止填洞伪造。几何容差1e-10mm；无重拟合、重缩放、平滑和GT。原生Vertex/Edge/Face ID在P_INITIAL.npz中保留。低于基底的完整B仅静态画图，不回写009。

弱平面统一最近ROI优先，使用独立真实背景点；不调用Ring平面替代。原始接触证据冻结，BROAD必生成候选，包含G05/G09。G05弱平面候选不被标为可靠基底。

## S输入与公平性

官方ico_sphere3，642V/1280F。以同一主要FIT完整Mask bbox的中心射线和HERO中位轴向深度定位；半径为两方向公制投影半径最大值（下限0.25mm），光轴后移0.5r。只平移/统一缩放，不读B半轴、GT或优化结果。NORMALIZATION完全由该观测规则给出，P/S共享，学习率的物理尺度同例一致。

两路线逐步使用相同随机视角序列、可靠候选ID、边界权重、同视角点对、损失/正则和预算。裁切后P约478–1280个可见三角面、球体1280；局部参数3V减去P边界法向限制，详细DOF见metrics/DOF_AND_SCALE_AUDIT.csv。均值归一并不能消除拓扑与初始形状先验不同的影响，必须视为整体初始化策略比较。

## 损失与固定分母

`L = L_ringaware_mask + L_edge_relative + L_laplacian_relative + .01 L_normal + .01 L_unknown_displacement + .01 L_absolute + .01 L_relative`。

Mask是既有全图MSE与Ring-Aware权重，不是均衡IoU；本轮不偷偷切换为009低维拟合的轮廓均衡目标。绝对/相对深度采用D2 Huber，r=e/0.5mm，`h(r)=min(.5r² if |r|<1 else |r|-.5,9.5)`。未命中/遮挡/掠射也取9.5，分母固定，丢掉一个高误差命中不能减少该样本自身代价。

深度第一面由Open3D离散选择，在固定面内用FP64射线平面公式求导；相机/尺度/参考深度固定。只使用Polyp可靠内部候选，源选择条件继承009。边界权重在原640×360标签坐标：`w=.1+.9*(1-exp(-(min(d_background,d_ring)/8)^2))`，像素中心EDT定义，不从320×180训练图计算。点对同视角4/16/48原生像素，要求内部权重>=.5、路径不跨Ring/无效区和>.5mm断裂。P/S相同候选和点对，不使用跨来源HERO一致性。

每步最多两个FIT；总深度项按被选视角数归一，RGB-only视角贡献零深度。只有一个深度源的组会有部分纯轮廓步，P/S同序；不静默归一成每步都有相同深度信息量。实际深度使用频率单独记录。

## 检查、诊断与停止

正式优化前118项检查及70视角/初始化投影核查通过。相对深度共同偏移不变性、有限差分梯度、真实初始化完整参数梯度有记录。正有限梯度不保证大步SGD稳定。

循环继承原2mm单步、0.1–10体积紧急范围与梯度/有限性检查。这里是工程保护而非正确性标准。未增加线搜索或步长调参，十个拒绝候选有真实UNSAFE状态，FINAL300缺失。拒绝候选已执行的一次optimizer.step计入实际次数，accepted单独报告。

MECHANISM保存实际空间损失梯度、参数动量和真实顶点位移；空间负梯度不能直接等同执行位移，后者还包含GLOBAL6/基底投影Jacobian及动量。失败回放只读，近似FP32重建之前状态，无optimizer.step；误差及逐项梯度独立记录，不参与后续选模或调权重。

评价只取固定FINAL300，失败NaN；最后安全、UNSAFE和其他checkpoint均单独诊断不选优。全Mask固定分母IoU/覆盖、深度原始固定成本、条件MAE/median/p95/max均报告。Mesh面积/体积/基底高度只是模型估计；真实GT误差NOT_EVALUABLE。碰撞深度来自顶点/面中心/边中点有符号距离采样，不是严格全局最大穿透上界。自交/碰撞由实际CAD及Blender独立核查，不修理网格再评价。

说明：LAST_SAFE 仅指上一次通过数值/单步紧急检查的状态，仍可能穿环或自交，不是物理安全认证。TRAINING/DEPTH_TRACE记录接受步骤；首步即拒绝的G03-S/G08-S为零行表（保留表头），实际一次optimizer.step及拒绝原因在RUN/FAILURE_DIAGNOSIS中。
