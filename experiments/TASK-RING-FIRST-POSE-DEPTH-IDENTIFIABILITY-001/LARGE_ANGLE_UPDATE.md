# 大视角 A→B 补充可视化

2026-11-04。研究者明确要求扩大A/B视角差异，并解释覆盖率和轮廓误差。本次沿用同一实验分支，仅添加补充输出；历史帧对、原A/B结果和旧图片保留。

[打开大视角图库](visualization_large_angle/index.html) · [指标解释](METRICS_EXPLAINED.md)。

选择在SIFT与新投影评价前冻结：只在当前Camera Gate已条件性入组、具有真实原始HERO的同视频相机之间，按光轴夹角降序排列，G01取前两对，G06/G08各取第一对；每对较大参考索引为A。所有候选和SHA见config/LARGE_ANGLE_PAIRS_FROZEN.json。没有依据匹配数量、覆盖率或结果好坏更换帧。

同时列出光轴夹角和绕Ring世界中心的相机观察方向差，二者定义不同。前者是相机朝向变化，后者描述相机从Ring中心看过去的方向变化。G01有40.35°的观察方向跨度，但对应光轴角25.62°；没有将前者冒充后者。G08在当前可入组来源中最大光轴角仅15.10°，不使用跨视频位姿拼大角度。

| A → B | 光轴差 ° | 绕Ring观察方向差 ° | 基线 mm | SIFT | 图片 |
| --- | --- | --- | --- | --- | --- |
| G01_004_growth_r14 → G01_004_new_r00 | 25.62 | 40.35 | 26.16 | 有效拟合1；证据不足 | [查看](figures/large_angle/G01_004_growth_r14__004_00_Wide_Panel2_SIFT.png) |
| G01_004_ref13 → G01_004_new_r00 | 24.03 | 36.83 | 23.67 | 有效拟合3；证据不足 | [查看](figures/large_angle/G01_004_ref13__004_00_Wide_Panel2_SIFT.png) |
| G06_004_growth_r06 → G06_004_new_r00 | 27.79 | 15.35 | 12.01 | 有效拟合21；返回R/t方向 | [查看](figures/large_angle/G06_004_growth_r06__key00_raw00107_Wide_Panel2_SIFT.png) |
| G08_005_growth_r05 → G08_005_new_r00 | 15.10 | 24.97 | 19.88 | 有效拟合10；证据不足 | [查看](figures/large_angle/G08_005_growth_r05__key00_raw00120_Wide_Panel2_SIFT.png) |

G01两对分别只有1、3个有效拟合匹配，G08只有10个，均低于旧规则要求的12个。它们没有SIFT公制投影、覆盖率或轮廓误差，值保留NaN/NOT_EVALUABLE；图中用文字注明，不以RF填充，也不把未投影的原B当作完美叠加。G06有21个拟合匹配，返回位姿；其留出只有2个匹配，不能据此认证相机。

保留Panel2-003原深度配色、全体正深度共享范围、点大小、真实XYZ/源RGB和实体CAD。新来源只从E1原始点及历史背景缓存既存display布尔选择组装同样的显示字典，未运行新的HERO或背景预测、未改变任何背景ROI/清理规则。复用原五面板函数及上轮SIFT追加函数，原始矩阵/相机文件只读。

Raw三角面评价按原代码定义单独写入LARGE_ANGLE_RESULTS.json/.csv，不回写REPROJECTION_ERRORS.csv或原A/B科学结果。三角面Polyp与离散点场景P/BG的覆盖口径仍分开。

| 帧对 | RF原三角面覆盖 | RF轮廓MAE px | SIFT原三角面覆盖 | SIFT轮廓MAE px |
| --- | --- | --- | --- | --- |
| G01_004_growth_r14 → G01_004_new_r00 | 69.84% | 8.717 | NaN | NaN |
| G01_004_ref13 → G01_004_new_r00 | 75.49% | 7.379 | NaN | NaN |
| G06_004_growth_r06 → G06_004_new_r00 | 90.34% | 1.509 | 70.00% | 5.721 |
| G08_005_growth_r05 → G08_005_new_r00 | 94.01% | 1.501 | NaN | NaN |

上述覆盖是二维B Mask解释比例，不是整个息肉的三维完整率。大角度出现未观测侧面与离散采样缺口，需要结合覆盖和RGB、越界、轮廓一起判断；不能从此次失败样本直接得出RF绝对相机精度更高的结论。

77项显示/数据不变检查通过；原A_POSES、A_REPROJECTION、B_SVD_RESULTS及PROTOCOL的SHA均保持不变。首次宽角度图中虽已标明SIFT失败，但无有效投影的叠加面板会只显示原B；已将这些面板全部改为NOT_EVALUABLE文本，首次显示保存在local_results/large_angle_initial_failure_display，修复前后数值SHA一致。

复现：

```bash
cd /home/liu/ring_first_3d_pose_depth
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/large_angle_panel2.py
```

| 审计项目 | 汇报 |
| --- | --- |
| 目标组数 | G01/G06/G08三个物理组、4个新大视角帧对；历史小角度4对另外保留 |
| 本算法独立成功 | RF已有几何投影4/4；SIFT数值位姿1/4对、1/3物理组；不等于相机真实精度合格 |
| 本算法失败 | SIFT 3/4对失败、2/3物理组无返回；公制精度/直径测量均NaN |
| 历史测量值回退 | 0；SIFT失败没有RF/S0/V2/其他方法回填 |
| 失败组及具体原因 | G01有效拟合1和3个；G08有效拟合10个；均不足12。G06留出2个，认证证据仍不足 |
| 最终统计样本 | 全部4对保留；成功配对比较仅G06一对，历史融合为0；绝对MedARE/MAE/p95/max均NaN |
| 是否使用GT选择算法 | 否；候选、角度与输入SHA在SIFT之前冻结，未按结果换帧 |
