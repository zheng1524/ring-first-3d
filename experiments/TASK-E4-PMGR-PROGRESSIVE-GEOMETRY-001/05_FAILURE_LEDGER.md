# 失败与未决记录


| 审计项目 | 必须汇报 / 本轮结果 |
| --- | --- |
| 目标组数 | 4个独立物理组G01/G06/G07/G08，4单视频；G01_005不入组；16个初值/seed案例不是16个息肉 |
| 本算法独立成功 | 4/4组均独立输出数值网格；本路线数值执行80/80臂运行；条件性2物理组、压力2组；科学真实几何/测量正确率不可评价 |
| 本算法失败 | 数值网格输出失败0/4组（NaN 0组）；运行硬失败0、未运行0；真实合格Is不可评价；几何/覆盖/FD风险见[失败账本](05_FAILURE_LEDGER.md)，测量及GT误差NaN |
| 历史测量值回退 | 0；父E1/E2九参数只作本轮明确批准P0，不以历史直径或融合模型补输出 |
| 失败组及具体原因 | [逐臂与来源](metrics/FAILURES.csv)、[完整分母](metrics/CASE_ARM_SEED_RESULTS.csv)、[Fig4](figures/Fig4_Ablation_Conflict.png) |
| 最终统计样本 | 4/4物理组的条件/压力配对；80臂只是同4组的重复条件；严格独立验证覆盖0/4（正确性未知），MedARE/MAE/p95/max均NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；GT/Oracle读取0；51116d0预注册、2f7e042最终CAD工程修正后冻结，未以B选参数/模式/初值/展示 |

## 已纠正工程问题

初轮CAD .01mm容差只相对上一状态，造成累计穿透；首轮输出全部保留于local_results/REJECTED_PRE_RING_BOUND_CORRECTION，拒收，不参与统计。e14c630首修误用min合并两个下界，独立回放再次拒收；2f7e042明确以max取两个下界的交集，并新增真实累积穿透回归测试。两轮诊断均不混入正式输出，原预算/阈值不变，全部从P0重跑；保存网格还必须通过独立断言。最终几何独立回放检查该上界，不靠总损失下降判断通过。

## 不可升级的资格

G01 CORE仍INSUFFICIENT_EVIDENCE、E1 Q-conflict弱输入；G06为条件性；G07历史HERO链与独立视角不足，G08压力，所有B非独立认证；G04/G05无合格相机链，真实正式Is NOT_EVALUABLE。背景全BASE_UNCERTAIN，不报伪毫米基底间隙。

## 实际统计风险

- A_VISIBLE_ANCHOR_COUNT_DECREASE: 35条来源/运行/控制记录（不是独立物理组）。
- FROZEN_P0_ALREADY_HAS_RING_COLLISION_PROXY: 60条来源/运行/控制记录（不是独立物理组）。
- A_FIXED_MASK_COVERAGE_DECREASE: 21条来源/运行/控制记录（不是独立物理组）。
- HELDOUT_FIXED_COVERAGE_DECREASE: 4条来源/运行/控制记录（不是独立物理组）。
- ARPACK_REPEATED_EIGENVALUE_COMPLETENESS_FAIL: 1条来源/运行/控制记录（不是独立物理组）。

FD控制>0.2有238/960次，最大1.410；高秩不构成物理可辨识证明。HERO软支持与D同源，相关性/冲突权重未校准。回缩拒绝不是被删去的失败病例，全部日志均有记录。额外精确球体ARPACK测试漏计一个重根，仍为FAIL；独立稠密参考与实际八份冻结谱一致，未改原准则或替换任何拟合输入。该限制不计入四个物理组成功分母。未知区闭合、面积或光滑不等于观测准确。完整失败见metrics/FAILURES.csv，覆盖见COVERAGE_DEGENERACY.csv，几何回放见RESULT_INTEGRITY.json。

不删除历史文件，若以后清理只能由研究者另行决定。本轮不做新实验修复这些科学限制。
