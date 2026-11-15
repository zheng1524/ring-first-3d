# Body-Guided HERO重定位：技术报告摘要

已完成四组真实实验与受控验证。**二维区域候选可以突破旧三维近邻门控，但尚不能把Body自洽当作可靠真实重定位。** 本轮没有更新Body、没有融合、没有新模型训练；所有原始曲面和相机只读。

## 输入与实际方法

G03→G05→G01→G06全部运行。Body-E是从固定参考视频三幅二维Mask/通用核心椭圆新拟合的九参数椭球，未读HERO XYZ或旧训练Body参数；Body-U为正式R3 B3 FINAL。算法以二维归一化区域建立Body首层候选，联合区域误差、实际Ring和真实背景SIFT优化来源级六自由度派生位姿。同一个刚体作用HERO与来源相机，完整局部形态/原像素关系保持。**这不是019–021的视频共享T，不是正式新轨迹；不能证明源间相对相机变形是正确修复。** A1实际复现旧受限射线修正，四组theta与历史FINAL最大差均0。

区域描述子新采用同一Mask核心AMS椭圆，不声称DXY最终算法；外围细长区域不作为椭球头部强对应，但完整网格保留。原设计/实际逐项对照与源码位置见METHOD_AND_INPUT_AUDIT.md。实际PyTorch3D Body优化未运行，因本任务明确冻结Body。

## 固定分母独立评价

| group | arm | numerical | conditionally_supported | heldout_fixed_N | heldout_known | heldout_MAE_mm | heldout_P95_mm | heldout_support | heldout_fixed_penalty_mm |
|---|---|---|---|---|---|---|---|---|---|
| G03 | A0 | 18 | baseline; not new pose | 55296 | 0.903 | 2.842 | 13.561 | 0.229 | 3.136 |
| G03 | A1 | 18 | baseline; not new pose | 55296 | 0.903 | 2.842 | 13.561 | 0.229 | 3.136 |
| G03 | A2-E | 18 | 0 | 55296 | 0.889 | 2.631 | 11.516 | 0.195 | 3.150 |
| G03 | A2-U | 18 | 0 | 55296 | 0.886 | 2.471 | 11.102 | 0.223 | 3.061 |
| G05 | A0 | 16 | baseline; not new pose | 49152 | 0.935 | 0.593 | 1.963 | 0.574 | 1.206 |
| G05 | A1 | 16 | baseline; not new pose | 49152 | 0.939 | 0.434 | 1.524 | 0.707 | 1.018 |
| G05 | A2-E | 16 | 0 | 49152 | 0.936 | 0.676 | 1.942 | 0.500 | 1.272 |
| G05 | A2-U | 16 | 7 | 49152 | 0.915 | 0.679 | 2.113 | 0.525 | 1.470 |
| G01 | A0 | 26 | baseline; not new pose | 133120 | 0.854 | 1.293 | 3.437 | 0.248 | 2.563 |
| G01 | A1 | 26 | baseline; not new pose | 133120 | 0.864 | 1.142 | 3.067 | 0.312 | 2.349 |
| G01 | A2-E | 26 | 10 | 133120 | 0.841 | 1.256 | 3.257 | 0.243 | 2.646 |
| G01 | A2-U | 26 | 0 | 133120 | 0.832 | 1.280 | 3.295 | 0.231 | 2.740 |
| G06 | A0 | 15 | baseline; not new pose | 46080 | 0.949 | 0.299 | 0.837 | 0.759 | 0.794 |
| G06 | A1 | 15 | baseline; not new pose | 46080 | 0.949 | 0.206 | 0.504 | 0.901 | 0.701 |
| G06 | A2-E | 15 | 11 | 46080 | 0.928 | 0.451 | 1.123 | 0.588 | 1.139 |
| G06 | A2-U | 15 | 6 | 46080 | 0.908 | 0.452 | 1.164 | 0.580 | 1.330 |

**实际独立结果偏负，不能推广替换：** G03原生留出MAE由2.842mm降到A2-U的2.471mm，但known从90.3%降到88.6%、支持率22.9%降到22.3%，两种Body条件资格均0/18；这不是可靠错层修复。G05的A2-E/U为0.676/0.679mm，均差于A0的0.593mm与A1的0.434mm。G01的A2-E条件MAE略降，但固定分母代价2.563→2.646mm、支持下降；A1更稳定。G06负对照明显被扰动，A0→A2-E/U为0.299→0.451/0.452mm，支持75.9%降到58.8%/58.0%。因此即使某些来源满足Ring/背景/区域条件检查，也不能将其称为完整独立几何验收通过。条件性通过仅为34/150状态（E=21/75，U=13/75），不支持全组替换。

MAE/P95仅在有效原生HERO留出对应上，support与known以全源–目标查询N为分母；10mm未解释代价为评价代理，不是GT误差。所有A2数字包含未获资格的**数值提案**，不能当作全来源合格新几何。原生留出HERO也有预测/相机噪声，不是GT。相同上游图像的来源并非独立统计证据。

## 控制实验

| control | Body | initial_mm | final_mm | pose_translation_mm | pose_rotation_deg | zero_pass | qualification |
|---|---|---|---|---|---|---|---|
| C0_ZERO | Body-E | 0.000 | 0.045 | 0.045 | 0.258 | True | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C0_ZERO | Body-U | 0.000 | 0.156 | 0.155 | 0.488 | False | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C1_DEPTH | Body-E | 3.052 | 2.785 | 0.266 | 0.665 | None | INDEPENDENT_CONFLICT_OR_UNEXPLAINED |
| C1_DEPTH | Body-U | 3.052 | 2.743 | 0.309 | 0.752 | None | INDEPENDENT_CONFLICT_OR_UNEXPLAINED |
| C2_POSE | Body-E | 1.948 | 0.043 | 0.043 | 0.269 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C2_POSE | Body-U | 1.948 | 0.157 | 0.155 | 0.547 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C3_FAR | Body-E | 10.221 | 0.043 | 0.043 | 0.262 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C3_FAR | Body-U | 10.221 | 0.158 | 0.157 | 0.501 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_LEFT | Body-E | 0.000 | 0.023 | 0.029 | 0.297 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_LEFT | Body-U | 0.000 | 0.139 | 0.149 | 0.429 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_RIGHT | Body-E | 0.000 | 0.038 | 0.041 | 0.218 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_RIGHT | Body-U | 0.000 | 0.036 | 0.035 | 0.112 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |

C2/C3能恢复较大的刚体错位，说明不依赖旧世界距离准入。C1的加性轴向深度误差改变三维局部形状，严格刚体A2没有足够表达能力，恢复失败。零扰动Body-U产生约0.156mm漂移，超过0.1mm预登记门槛，即使Ring/背景条件检查通过，也不能称定位精度已证明。C4保留独立真实左右曲面，未平均或合并；仅是最小控制，不证明任意复杂多分支都可判别。

## 五个科研回答

1. **初始椭球还是更新Body？** 上表必须结合独立指标与资格率判断，不按Body距离或漂亮截面选胜者。Body-E在G03拉长、G01/G05扁平，说明本次有限预算二维拟合未得到稳定合理的粗主体；相机、区域描述子和局部优化搜索都可能参与，不能据此唯一证明几何不可辨识；Body-U含更强历史观测，也会将形态偏差传入对应。没有一个Body已证明普适正确区域对应。
2. **远距离能生成合理候选？** 可以突破旧门控；控制C3恢复与真实旧距离/候选数见逐来源CSV。候选产生不等同真实身份正确。
3. **是否独立改善定位？** 只能按上表、背景留出、Ring全CAD和来源间可见性给局部条件证据。某些误差下降同时可能失去支持/覆盖；不足以认定四组错层可靠解决。绝对位姿精度NOT_EVALUABLE。
4. **G03长柄？** A2完整刚体保留原柄、连接、面片、长度和曲率，未将柄吸附椭球头；这只是局部形态保持，世界方向/位置仍受独立约束与歧义限制，不宣称长柄已经准确重定位。全部原面与候选图均保留。
5. **误差来自哪里？** C1证明深度形变不能由严格刚体表达；新椭球退化与零扰动U漂移证明Body区域并非精确材料对应；真实背景/Ring矛盾也可能来自原相机、背景非静态/重复纹理、Mask/CAD投影或HERO。现有真实数据不能唯一拆分所有原因，不把全部误差归因相机。

## 失败与结论

控制契约修复前结果归档，正式真实参数未按留出或GT调整。没有删除错层面制造改善。建议保留二维区域候选和独立约束的诊断接口，**暂不把本轮全部A2提案替换正式HERO/相机或进入自动融合**；下一步应先人工检查关键区域身份与独立背景/相机证据，若另行授权再隔离刚体定位与射线深度误差。完成后停止。

## 核心图与复现

- figures/Fig1_Region_Correspondences.png：实际二维对应与原图。
- figures/Fig2_Body_E_U.png：两种Body及同来源候选。
- figures/Fig3_HERO_All_Group_Comparison.png：全部原生三角面、同尺度错层对照。
- figures/Fig4_Independent_and_Control_Evaluation.png：独立评价与控制失败。
- 各组Three_Fixed_Directions、Actual_Common_Sections及GLB完整图层。

精确绝对路径与SHA见RESULT_INDEX.md、assets_index。运行命令见REPRODUCE.md。大数据/GLB/全部逐步记录本地保留，只有明确列入Git交付清单的文件声称上传。

## 固定审计表

|审计项目|必须汇报|
|---|---|
|目标组数|4个独立物理组；75来源；150个Body-E/U来源状态；A0/A1独立基线|
|本算法独立成功|150/150产生数值候选；34/150满足预登记条件性验证；不能等同真实定位准确或独立来源数量|
|本算法失败|0无数值候选；116未获条件性资格，accepted_H=null/NaN；绝对真实三维精度4/4 NOT_EVALUABLE|
|历史测量值回退|0；A0/A1与授权Body-U是明示对照/输入，未填入失败A2预测|
|失败组及具体原因|FAILURE_LEDGER.md及metrics/VALIDATION.csv逐来源原因与真实图集|
|最终统计样本|全部4组、75来源、150状态；每源最多1024固定原生ID；有效N与全N并列；没有融合Mesh监督|
|是否使用GT选择算法|否；provenance/REAL_SOLVER_CODE_FREEZE.json与ALL_REAL_PREDICTIONS_FROZEN.json；控制GT仅生成/冻结后审计|
