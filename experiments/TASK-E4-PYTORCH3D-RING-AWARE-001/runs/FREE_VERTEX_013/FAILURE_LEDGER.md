# 失败与异常台账

不删除失败、不把低损失视为几何正确。全部11例保留同一数据和观察方向。

前期工程异常：新增初始化配置最初缺少depth字段，尚未发生优化更新即报错；补齐相同012配置后重跑，原失败日志保留runtime/NEW_FIT_G10.log和G11.log。不存在以此更换病例。

## G01

ACCEPTED_TARGET_REACHED，300/300接受；最大累计位移2.40237mm。拒绝原因计数：{'FULL_FIT_OBJECTIVE': 319, 'FACE_ORIENTATION': 1145}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：VALID_SOLID_SAMPLED_ESTIMATE。
[原坐标完整图](figures/full/G01_Native_Detail.png) · [纯主体六视图](figures/full/G01_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G01_CANDIDATES.json。

## G02

FIXED_CONSECUTIVE_REJECTION_STOP，82/162接受；最大累计位移0.438132mm。拒绝原因计数：{'FACE_ORIENTATION': 648, 'AREA_DEGENERACY': 4226, 'FULL_FIT_OBJECTIVE': 38}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_ENTITY_VALIDITY。
[原坐标完整图](figures/full/G02_Native_Detail.png) · [纯主体六视图](figures/full/G02_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G02_CANDIDATES.json。

## G03

FIXED_CONSECUTIVE_REJECTION_STOP，156/236接受；最大累计位移5.53818mm。拒绝原因计数：{'RING_WORSENING': 5267, 'FULL_FIT_OBJECTIVE': 905, 'RING_CONTAINMENT_WORSENING': 843}。
独立几何：Ring相交=True，采样穿透=9.98231e-06mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_ENTITY_VALIDITY。
[原坐标完整图](figures/full/G03_Native_Detail.png) · [纯主体六视图](figures/full/G03_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G03_CANDIDATES.json。

## G07

ACCEPTED_TARGET_REACHED，300/300接受；最大累计位移0.0213304mm。拒绝原因计数：{'RING_WORSENING': 2380}。
独立几何：Ring相交=True，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_ENTITY_VALIDITY。
[原坐标完整图](figures/full/G07_Native_Detail.png) · [纯主体六视图](figures/full/G07_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G07_CANDIDATES.json。

## G04

FIXED_CONSECUTIVE_REJECTION_STOP，125/215接受；最大累计位移0.763935mm。拒绝原因计数：{'FACE_ORIENTATION': 846, 'AREA_DEGENERACY': 602, 'FULL_FIT_OBJECTIVE': 2779, 'BASE_HALFSPACE_OR_BOUNDARY': 2535}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE。
[原坐标完整图](figures/full/G04_Native_Detail.png) · [纯主体六视图](figures/full/G04_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G04_CANDIDATES.json。

## G05

ACCEPTED_TARGET_REACHED，300/300接受；最大累计位移0.00644072mm。拒绝原因计数：{'RING_WORSENING': 2400}。
独立几何：Ring相交=True，采样穿透=1.01874e-05mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_ENTITY_VALIDITY。
[原坐标完整图](figures/full/G05_Native_Detail.png) · [纯主体六视图](figures/full/G05_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G05_CANDIDATES.json。

## G06

FIXED_CONSECUTIVE_REJECTION_STOP，25/105接受；最大累计位移0.624507mm。拒绝原因计数：{'RING_WORSENING': 2855, 'FULL_FIT_OBJECTIVE': 1540}。
独立几何：Ring相交=True，采样穿透=9.99316e-06mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE。
[原坐标完整图](figures/full/G06_Native_Detail.png) · [纯主体六视图](figures/full/G06_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G06_CANDIDATES.json。

## G08

ACCEPTED_TARGET_REACHED，300/300接受；最大累计位移0.771514mm。拒绝原因计数：{'NEW_CAD_COLLISION': 2373, 'RING_WORSENING': 594, 'RING_CONTAINMENT_WORSENING': 297, 'FULL_FIT_OBJECTIVE': 178}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE。
[原坐标完整图](figures/full/G08_Native_Detail.png) · [纯主体六视图](figures/full/G08_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G08_CANDIDATES.json。

## G09

FIXED_CONSECUTIVE_REJECTION_STOP，52/132接受；最大累计位移0.179735mm。拒绝原因计数：{'FACE_ORIENTATION': 925, 'FULL_FIT_OBJECTIVE': 2979, 'AREA_DEGENERACY': 888}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE。
[原坐标完整图](figures/full/G09_Native_Detail.png) · [纯主体六视图](figures/full/G09_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G09_CANDIDATES.json。

## G10

ACCEPTED_TARGET_REACHED，300/300接受；最大累计位移0.878665mm。拒绝原因计数：{'FULL_FIT_OBJECTIVE': 2325}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：VALID_SOLID_SAMPLED_ESTIMATE。
[原坐标完整图](figures/full/G10_Native_Detail.png) · [纯主体六视图](figures/full/G10_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G10_CANDIDATES.json。

## G11

ACCEPTED_TARGET_REACHED，300/300接受；最大累计位移0.271603mm。拒绝原因计数：{'FULL_FIT_OBJECTIVE': 6313}。
独立几何：Ring相交=False，采样穿透=0mm，非流形边=0，退化面=0。严格体积IoU：VALID_SOLID_SAMPLED_ESTIMATE。
[原坐标完整图](figures/full/G11_Native_Detail.png) · [纯主体六视图](figures/full/G11_Body_Six_Views.png)。原始日志与全部拒绝候选：arms/FINAL_UNIFORM/metrics/G11_CANDIDATES.json。

<!-- DENSE_RING_ADDENDUM -->

## 三角面内部Ring漏检（冻结后独立发现）

违反非恶化代理的病例：G03, G07, G05, G06。原始稀疏采样可漏掉面内部材料穿透，未修改预测或阈值。详见DENSE_RING_AUDIT.csv/GEOMETRY_ACCEPTANCE.csv。G03最大穿透0.00615→0.05292mm，不能认证正式非穿透。所有候选仅保留研究结果身份。

G02完整012复现不逐位一致，最大顶点差0.170mm；源输入、核心代码、先验缓存逐项一致，尚未充分隔离数值/离散分支来源。源代码和历史结果均保留，不制造复现PASS。

## G11作者基底不可评价
原始Blender仅1个最低顶点、0个最低平面三角面，不能把zmin强当组织基底；Hmax/H95及基底距离保留NOT_EVALUABLE。完整有效实体/表面评价和条件作者XY Dxy仍报告，病例不移除。
