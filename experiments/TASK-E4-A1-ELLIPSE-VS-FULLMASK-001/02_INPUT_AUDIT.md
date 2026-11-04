# 二维输入与来源审计

研究者追加授权后，实际使用最终官方DXY代码独立生成全部13源的主体圆/椭圆。GitHub远端main与本机HEAD均为75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95；[精确版本回执](provenance/DXY_VERSION_AUDIT.json)保留机器主线和源码SHA。官方路径 `dxy_mid.pipeline.measure_files`，配置V9.1，未调用旧实验拟合器替代。GitHub连接器暂不可用，使用只读git ls-remote核验origin/main；不更改DXY分支或文件。

初始查找：历史790帧回归缓存并不覆盖本轮源，同帧号可能是不同图像；另有dxy_original_fits及*_candidates只保存Ring几何/位姿。它们没有作为Polyp椭圆输入。本轮不会从错帧转移椭圆，也不根据文件名名义尺寸或旧测量值补齐。

生成输入为本轮冻结源RGB与原Mask，640×360，标签0背景/1Polyp/2Ring；与冻结K同坐标。内容SHA生成稳定RNG身份，不用类型/组名决定算法。已知Ring内径只用于官方接口，DXY毫米尺度输出被丢弃。记录完整像素center、basis、半轴和旋转，不再根据本轮3D效果重拟合。

官方DXY有通用A/B主体候选、Ring内外证据、通用开运算、短Q处理和Q恢复；这些规则对所有输入相同，没有Paris类型参数。本轮没有为Ip额外做头部/柄提取。E1仍是受该上游规则影响的主体近似，不能称真实解剖头部。E2完全不调用DXY候选Mask/开运算，直接使用全部原始Polyp像素。

| 源图/质量 | 形状 | 中心 px | 半轴 px | 角度 rad | Strict |
| --- | --- | --- | --- | --- | --- |
| G01_004_growth_r14 / Q_conflict_recovery | circle | 341.22, 195.65 | 66.41, 66.41 | 0.0000 | False |
| G01_004_ref03 / Q_conflict_recovery | ellipse | 423.82, 175.31 | 104.20, 82.75 | 2.2571 | False |
| G01_004_ref08 / Q_conflict_recovery | ellipse | 370.49, 201.82 | 71.92, 67.95 | 2.5634 | False |
| G01_004_ref13 / Q_conflict_recovery | circle | 358.98, 199.93 | 69.09, 69.09 | 0.0000 | False |
| G06_004_growth_r01 / normal_Gate_pass | ellipse | 233.77, 195.05 | 80.15, 46.44 | 0.0448 | True |
| G06_004_growth_r03 / normal_Gate_pass | ellipse | 232.43, 193.11 | 79.41, 47.50 | 3.1255 | True |
| G06_004_growth_r06 / normal_Gate_pass | ellipse | 399.02, 239.63 | 89.42, 62.62 | 3.0585 | True |
| G07_004_growth_r02 / normal_Gate_pass | ellipse | 232.38, 231.36 | 95.89, 76.92 | 3.0092 | False |
| G07_004_new_r06 / normal_Gate_pass | ellipse | 396.73, 122.23 | 95.94, 67.16 | 0.1930 | False |
| G07_004_ref04 / normal_Gate_pass | ellipse | 247.43, 171.87 | 99.42, 74.60 | 3.1340 | True |
| G08_005_growth_r01 / normal_Gate_pass | ellipse | 315.31, 225.61 | 106.39, 56.51 | 0.1815 | True |
| G08_005_growth_r02 / normal_Gate_pass | ellipse | 303.44, 220.74 | 102.89, 55.78 | 0.1073 | True |
| G08_005_ref04 / normal_Gate_pass | ellipse | 277.44, 196.25 | 111.31, 62.80 | 3.1023 | True |


圆的角度不唯一，列表中的角度只是basis的SVD表示；basis矩阵才是可复现的曲线定义。ellipse/circle不通过类型选择。G01均Q冲突恢复，不能冒充Strict椭圆；G07部分Strict=false。二维质量不等于相机认证。

每源RGB/Mask/HERO/K/c2w/CAD路径与SHA见[INPUT_ASSET_SHA](provenance/INPUT_ASSET_SHA.json)；原生/归档映射及D pixel ID、具体射线值在inputs/；两臂用同一份缓存。[逐源资格](metrics/INPUT_QUALIFICATION.csv)、[生成几何](provenance/DXY_GENERATED.json)。G01_005不入组、不跨视频合并；G07无当前合格清理缓存，保留Raw压力身份。源清理未重跑。

协议继承的G01 tier文字仍含旧HEAD_CUE字样，只是历史资格元数据；本轮没有任何旧头部Mask输入或操作，正式图/报告已明确采用全Mask。

| 审计项目 | 必须汇报 / 本轮结果 |
| --- | --- |
| 目标组数 | 4个独立物理组：G01_004、G06_004、G07_004、G08_005；004/005不混合 |
| 本算法独立成功 | E1数值主体4/4，E2数值主体4/4；8模型不是8个息肉，数值输出不代表测量正确 |
| 本算法失败 | 正式72次求解中3次预算耗尽；保留有限诊断候选，但接受状态失败/NaN；完整A主模型8/8数值收敛，严格独立相机/真值资格成功0/4 |
| 历史测量值回退 | 0；最终预测来自各自本轮9参数拟合；官方DXY仅提供本轮独立生成的2D像素几何 |
| 失败组及具体原因 | [逐组失败与来源](05_FAILURE_LEDGER.md)、[全部初值与扰动](03_E1_E2_METRICS.csv)、[Fig4](figures/Fig4_Stability_And_Failure.png) |
| 最终统计样本 | 配对4物理组/目标4；条件性2组G01/G06、压力2组G07/G08；无全流程独立B，不能按72个模型计算样本量 |
| 是否使用GT选择算法 | 否；真实GT/Oracle读取0；[协议](01_PROTOCOL.md)和[首轮冻结](provenance/PREOPTIMIZATION_FREEZE.json)先于首轮优化；[一次数值修正](PROTOCOL_CORRECTION_v0.2.md)及[再冻结](provenance/PREOPTIMIZATION_CORRECTION_v0.2.json)先于正式重跑 |

真实3D/直径 MARE、MAE、p95和最大GT误差均 NOT_EVALUABLE。本报告相对D残差是相对于HERO内部轴向深度差，不能冒充独立真实深度精度。
