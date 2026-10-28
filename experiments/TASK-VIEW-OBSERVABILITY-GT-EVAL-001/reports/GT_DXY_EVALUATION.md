# 三维投影Feret原型：候选误差与正式有效性

正式Dxy主线没有导入、执行或修改。GT按实际作者底盖法向投影全部GT顶点，最大凸包点对给出Feret；与原型数学定义相同，但完整GT和可见/条件支持预测的覆盖不同，基底方向也分别独立估计。没有使用GT部署位姿或ICP。

| 组 | GT Feret mm | 全部数学候选范围 mm | 数学候选数 | 全条件数 | 正式成功 | 主要限制 |
| --- | --- | --- | --- | --- | --- | --- |
| G01 | 12.0000 | [10.211078014025192, 11.57021784919287] | 54 | 54 | 0 | 基底/表面支持/端点条件失败 |
| G06 | 14.0000 | [12.62254466532105, 12.623883982220798] | 9 | 9 | 0 | 两端点独立支持均失败 |
| G07 | 14.0000 | NaN / NOT_EVALUABLE | 0 | 9 | 0 | 相机不合格，候选也NaN |
| G08 | 22.0000 | [21.350058761860222, 21.357873727356992] | 9 | 9 | 0 | 一端点独立支持失败 |

72/81有数学候选可比较，9/81没有候选；**正式81/81仍NOT_EVALUABLE，0/4组成功**。3/4组有数学候选，不表示3/4正式测量成功。预指定组统计见[高度/配对统计](GT_HEIGHT_EVALUATION.md)，数学MAE1.1877mm来自3/4组，正式MAE为NaN。G06候选比GT小约1.376–1.377mm，G08约0.642–0.650mm。G08相对接近，但一端点缺独立观测支持，不能由GT接近升级成功。

端点支持失败不证明端点本身一定错误：可能因遮挡、Mask、相机、反光或模型本身。候选偏小也不能独断归因HERO；还包含可见边界缺失、基底方向和全形状定义差异。本轮不重选端点、改支持阈值、补面或读取历史直径回填。

全部81条件如下，primary/second/core可能是同一个单参考别名，不是独立样本。

| 场景 | 基底参考/ROI | 模型 | 数学候选mm | GTmm | 有符号差mm | 端点独立支持 | 正式状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | G01_004_ref03/5-30 | primary | 10.4018 | 12.0000 | -1.5982 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-30 | second | 10.5705 | 12.0000 | -1.4295 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-30 | core | 10.5705 | 12.0000 | -1.4295 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-45 | primary | 10.3825 | 12.0000 | -1.6175 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-45 | second | 10.5214 | 12.0000 | -1.4786 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-45 | core | 10.5214 | 12.0000 | -1.4786 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-60 | primary | 10.5928 | 12.0000 | -1.4072 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-60 | second | 10.5928 | 12.0000 | -1.4072 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref03/5-60 | core | 10.7249 | 12.0000 | -1.2751 | [True, False] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-30 | primary | 10.2932 | 12.0000 | -1.7068 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-30 | second | 10.2932 | 12.0000 | -1.7068 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-30 | core | 10.4565 | 12.0000 | -1.5435 | [True, False] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-45 | primary | 10.3743 | 12.0000 | -1.6257 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-45 | second | 10.3743 | 12.0000 | -1.6257 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-45 | core | 10.5352 | 12.0000 | -1.4648 | [True, False] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-60 | primary | 10.4749 | 12.0000 | -1.5251 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-60 | second | 10.4749 | 12.0000 | -1.5251 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref08/5-60 | core | 10.6338 | 12.0000 | -1.3662 | [True, False] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-30 | primary | 10.8075 | 12.0000 | -1.1925 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-30 | second | 10.8075 | 12.0000 | -1.1925 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-30 | core | 10.9487 | 12.0000 | -1.0513 | [True, False] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-45 | primary | 10.7838 | 12.0000 | -1.2162 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-45 | second | 10.7838 | 12.0000 | -1.2162 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-45 | core | 10.9253 | 12.0000 | -1.0747 | [True, False] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-60 | primary | 10.7828 | 12.0000 | -1.2172 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-60 | second | 10.7828 | 12.0000 | -1.2172 | [True, True] | NOT_EVALUABLE |
| G01_004 | G01_004_ref13/5-60 | core | 10.9241 | 12.0000 | -1.0759 | [True, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-30 | primary | 10.7423 | 12.0000 | -1.2577 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-30 | second | 10.7423 | 12.0000 | -1.2577 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-30 | core | 10.7423 | 12.0000 | -1.2577 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-45 | primary | 10.6983 | 12.0000 | -1.3017 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-45 | second | 10.6983 | 12.0000 | -1.3017 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-45 | core | 10.6983 | 12.0000 | -1.3017 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-60 | primary | 10.5877 | 12.0000 | -1.4123 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-60 | second | 10.5877 | 12.0000 | -1.4123 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00057/5-60 | core | 10.5877 | 12.0000 | -1.4123 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-30 | primary | 10.2111 | 12.0000 | -1.7889 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-30 | second | 10.2111 | 12.0000 | -1.7889 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-30 | core | 10.2111 | 12.0000 | -1.7889 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-45 | primary | 10.2155 | 12.0000 | -1.7845 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-45 | second | 10.2155 | 12.0000 | -1.7845 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-45 | core | 10.2155 | 12.0000 | -1.7845 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-60 | primary | 11.5702 | 12.0000 | -0.4298 | [True, True] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-60 | second | 11.5702 | 12.0000 | -0.4298 | [True, True] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00459/5-60 | core | 11.5702 | 12.0000 | -0.4298 | [True, True] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-30 | primary | 10.7260 | 12.0000 | -1.2740 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-30 | second | 10.7260 | 12.0000 | -1.2740 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-30 | core | 10.7260 | 12.0000 | -1.2740 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-45 | primary | 11.0690 | 12.0000 | -0.9310 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-45 | second | 11.0690 | 12.0000 | -0.9310 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-45 | core | 11.0690 | 12.0000 | -0.9310 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-60 | primary | 11.0991 | 12.0000 | -0.9009 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-60 | second | 11.0991 | 12.0000 | -0.9009 | [False, False] | NOT_EVALUABLE |
| G01_005 | G01_005_raw00745/5-60 | core | 11.0991 | 12.0000 | -0.9009 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-30 | primary | 12.6225 | 14.0000 | -1.3775 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-30 | second | 12.6225 | 14.0000 | -1.3775 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-30 | core | 12.6225 | 14.0000 | -1.3775 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-45 | primary | 12.6231 | 14.0000 | -1.3769 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-45 | second | 12.6231 | 14.0000 | -1.3769 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-45 | core | 12.6231 | 14.0000 | -1.3769 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-60 | primary | 12.6239 | 14.0000 | -1.3761 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-60 | second | 12.6239 | 14.0000 | -1.3761 | [False, False] | NOT_EVALUABLE |
| G06_004 | G06_004_ref04/5-60 | core | 12.6239 | 14.0000 | -1.3761 | [False, False] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-30 | primary | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-30 | second | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-30 | core | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-45 | primary | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-45 | second | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-45 | core | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-60 | primary | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-60 | second | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G07_004 | G07_004_ref04/5-60 | core | NaN / NOT_EVALUABLE | 14.0000 | NaN / NOT_EVALUABLE | [] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-30 | primary | 21.3579 | 22.0000 | -0.6421 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-30 | second | 21.3579 | 22.0000 | -0.6421 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-30 | core | 21.3579 | 22.0000 | -0.6421 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-45 | primary | 21.3576 | 22.0000 | -0.6424 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-45 | second | 21.3576 | 22.0000 | -0.6424 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-45 | core | 21.3576 | 22.0000 | -0.6424 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-60 | primary | 21.3501 | 22.0000 | -0.6500 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-60 | second | 21.3501 | 22.0000 | -0.6500 | [False, True] | NOT_EVALUABLE |
| G08_005 | G08_005_ref04/5-60 | core | 21.3501 | 22.0000 | -0.6500 | [False, True] | NOT_EVALUABLE |

[CSV](../metrics/gt_dxy_evaluation.csv)保留原始严格状态、后验定义审计状态、表面比例、足迹比例及所有失败原因。
