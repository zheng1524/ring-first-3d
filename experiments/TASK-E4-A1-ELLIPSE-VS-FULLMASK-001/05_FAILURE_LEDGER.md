# 失败账本

| ID | 步骤/范围 | 具体原因 | 处理与证据 |
| --- | --- | --- | --- |
| I01 | 旧椭圆缓存 | 同帧号不等于同图；部分文件实为Ring位姿 | 未用；研究者追加授权后按最终DXY源码重新生成 |
| E01 | DXY首启环境 | Ring工程Python3.12缺skimage | 使用DXY原Python3.10依赖；数学不改，不安装新模型 |
| E02 | DXY worker只读保护 | 初稿路径规则误拦cv2/data模块 | 只修正为DXY根下outputs/data/validation，未放开旧预测/GT读取 |
| E03 | 合成测试脚本解析 | 初稿多余括号 | 优化前语法修复，冻结后数学不因此改变 |
| M01 | 首轮Mask区域池化 | 混合Ring/已知像素单元的未知量混入比例 | 首轮72完整保留并标拒收；修正后再次冻结、同预算重跑，见[修正](PROTOCOL_CORRECTION_v0.2.md) |
| Q01 | G01_004 | CORE相机INSUFFICIENT_EVIDENCE；E1全为Q恢复/Strict=false | 只作条件性比较；E1全A主解B仅25/32射线，低覆盖 |
| Q02 | G06_004 | A条件性相机；B证据不足，且删参考变单视角 | 不认证真实形态/独立泛化；两臂多初值有差解 |
| Q03 | G08_005 | 压力身份；两初值可落入低IoU局部解，E2微扰位移2.671mm | 保留差解，不选B最好解；[Fig4](figures/Fig4_Stability_And_Failure.png) |
| Q04 | G07_004 | 部分最新单相机条件通过，历史HERO链未合格 | 压力测试，不升级Is正式成功；E1相机副本主解未收敛 |
| M02 | G01全Mask | E2 IoU/覆盖较好，但D MAE .524→1.162mm，FP增加 | 统一椭球表达/证据耦合风险，不恢复头柄分割 |
| M03 | G06稳定性 | E2删视角变化较小、初值表面散布却较大 | 不只挑稳定性有利指标 |
| M04 | G07稳定性 | E2初值/删参考较好，相机副本却较差 | 不宣布E2全面更稳定 |
| Q05 | 全部B | 历史上游/Gate/选帧依赖，且Ring标签处仍有预测可见前层 | CONDITIONAL；单独保留Ring重叠数，不作Polyp负监督掩盖 |
| S01 | 类型标签与GT | 无独立真实3D GT、样本仅4物理组 | MARE/真值MAE/p95/max NOT_EVALUABLE；不把72求解当72息肉 |

正式预算耗尽：

| 实例 | 输入 | 条件 | 初值 | nfev | 终止 |
| --- | --- | --- | --- | --- | --- |
| G06_004 | E1 | camera_copy | 0 | 60 | The maximum number of function evaluations is exceeded. |
| G08_005 | E2 | drop_last_A | 2 | 60 | The maximum number of function evaluations is exceeded. |
| G07_004 | E1 | camera_copy | 0 | 60 | The maximum number of function evaluations is exceeded. |


保留其有限参数/损失/投影作为诊断，接受状态失败，accepted指标为NaN；不把预算耗尽自动算收敛，也不根据B换成另一个“好看”的初值。完整A8主模型均数值收敛，但不因此宣称真实准确。

没有主候选轴比>20（全72最大约7.92），未观察到模型家族意义上的自交/任意尖峰；闭合凸椭球仍可能错过细部或产生错误背面。本轮不增加第三种形状来消除失败。

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
