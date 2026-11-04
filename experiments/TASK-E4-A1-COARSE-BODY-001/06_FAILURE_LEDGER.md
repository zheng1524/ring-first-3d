# E4 A1 失败与限制账本

没有删除失败初值或不利参考，没有改参数搜索范围。数值求解收敛与科学失败分开记录。

| ID | 范围/步骤 | 原因与证据 | 处理/状态 |
| --- | --- | --- | --- |
| F00 | prepare元数据尾部 | 首次13输入生成后PART常量缺失触发NameError | 优化前修正常量，--finalize完成；输入/规则未改变 |
| F01 | 汇总代码 | summarize.py初次解析缺少括号 | 仅汇总代码语法修复；不影响冻结拟合代码、配置或模型 |
| Q01 | 全部B/严格G1 | 上游HERO、Gate或选帧历史依赖；没有真正独立全流程留出 | G1 NOT_PASSED，0严格通过；[资格](03_DATA_QUALIFICATION.csv) |
| Q02 | G01_004 Ip | 当前CORE Gate证据不足；头部是未认证软线索，r14与ref13角度接近 | 条件验证；不称真实头部GT；[Fig1](figures/Fig1_Frozen_B_Real_Projection.png) |
| Q03 | G01_005 | 缺本轮当前Gate/清理链，004/005空间未统一 | 仅审计，四消融NaN，不混合 |
| Q04 | G04/G05 Is | 归档相机UNQUALIFIED_ARCHIVED_CAMERA | 输入资格失败，两组全部消融NaN；[主动搜索](provenance/IS_PATHS_AND_METADATA_CORRECTION.json) |
| Q05 | G07 Is | ref04/r02最新单相机条件通过，但历史HERO链未合格；两个A同分区 | 压力测试，正式Is NOT_EVALUABLE；不放宽门槛 |
| Q06 | G06 IIa | A条件资格有用；B、历史背景源ref04仍证据不足 | 不能认证完整G1或自动启动A2 |
| Q07 | G08 IIa | 历史/最新资格、背景与形态限制 | 压力测试；不得冒充另一合格重复样本 |
| M01 | G06 A1-1 | B IoU .494、投影越界明显 | 数值必要门槛失败；[Fig1](figures/Fig1_Frozen_B_Real_Projection.png) |
| M02 | G01 A1-3 | 相对A1-2，D误差下降但B固定命中30→29、IoU下降 | 潜在覆盖退化，不能宣布模型优势 |
| M03 | G08 A1-3 | 轮廓略好但相对D MAE .413→.898mm；模型峰高约4.18mm | 错误形态/过拟合风险，不能凭平滑获PASS；[Fig3/4](figures/Fig4_Failure_Identifiability.png) |
| M04 | G07 A1-2/3 | 删除一个A后中心变4.729/4.603mm | 实例信息/流程不稳定，压力数值不认证真实主体 |
| N01 | 5个J | G01 A1-3、G06 A1-2、G08 A1-2/+H、G07 A1-2两步长差>.1；伴随hit开关 | NUMERICALLY_UNSTABLE_J；不采用伪精确条件数；[S4](05_IDENTIFIABILITY_REPORT.md) |
| N02 | G08 A1-0 | 厚度观测列为0，局部秩8/9 | LOCALLY_UNIDENTIFIABLE，不用先验填满观测秩 |
| N03 | 全部D删失 | 11个A源/模型记录覆盖低于初值；漏射残差删失可能换取低误差 | 保留固定分母，记录潜在失败；本轮不反复改损失重跑 |
| N04 | 导出Mesh离散化 | 2048条真实模型/源射线：1个hit分歧，最大连续/三角面深度差.215mm | 保留原网格/指标，不能把控制实验.003mm上界推广到真实掠射 |
| N06 | G01 A1-3首交点合同 | ref08原生Pixel ID 85489的两个近根落在同一33点扫描格内，被错误判无交点；加密Mesh仍有hit | 正式根合同FAIL，保留原结果，不认证该模型；[诊断](metrics/ROOT_BRACKETING_FAILURE.json) |
| N05 | H软支持 | 面积CDF样本再按顶点面积归一，非无偏面积积分；方向对应不是真正最近点SDF | 明确近似，未来修改须重新冻结；未换权重制造好结果 |
| R01 | 越界报告 | 原FP/predicted_N不是固定观测分母 | 保留原字段与Gate，补FP/head_N及FP/画幅，不按新分母重判PASS |
| R02 | 资格CSV附加搜索行 | 历史相机状态列误列为current；旧字段别名导致两个路径null | 原CSV冻结副本保留；补最新状态/正确路径，主实验入组不变；[修正记录](provenance/IS_PATHS_AND_METADATA_CORRECTION.json) |
| V01 | XYZ图绘制 | 初稿CAD绘制层级会盖住已可见的前方点 | 审图后仅改显示层级与点大小，真实XYZ/CAD/相机不变；模型和评价不改 |
| G01 | A2/B1/B2 | G1无严格通过实例；本轮只有A2设计授权 | 实际执行0；完成A1后停止 |

负面的科学结果不等于参数化路线已被否定；本轮证明的是有条件收益与仍未解决的证据/数值限制。

| 审计项目 | 本轮结果 |
| --- | --- |
| 目标组数 | E4-0资格覆盖6个物理组：G01/G04/G05/G06/G07/G08；A1实际拟合4组；G01_005是G01另一未统一视频空间，不另计物理组 |
| 本算法独立成功 | 独立产生数值主体4/6；仅指输出成功，严格独立资格及真实几何正确成功0/6 |
| 本算法失败 | 输入资格失败2/6：G04、G05，指标NaN；60次正式初值优化数值收敛60/60；另外保留G01_005不可评价记录 |
| 历史测量值回退 | 0；其他路线预测不参与本轮主体生成 |
| 失败组及具体原因 | [逐组失败](06_FAILURE_LEDGER.md)、[资格与路径](03_DATA_QUALIFICATION.csv)、[核心证据](figures/Fig4_Failure_Identifiability.png) |
| 最终统计样本 | 4个独立物理组的条件性/压力描述，完整资格分母6；不把帧、初值或模型当独立息肉；正式真值误差样本0 |
| 是否使用GT选择算法 | 否；真实GT/Oracle读取0；合成真值仅用于S1；[预注册](01_PM_PROTOCOL.md)和[冻结SHA](provenance/PREOPTIMIZATION_FREEZE.json)先于真实优化 |

真实测量 MARE、MAE、p95、最大GT误差均 NOT_EVALUABLE。本任务不输出独立真值直径。下文的D误差是相对HERO内部深度差的残差，不是独立三维精度。
