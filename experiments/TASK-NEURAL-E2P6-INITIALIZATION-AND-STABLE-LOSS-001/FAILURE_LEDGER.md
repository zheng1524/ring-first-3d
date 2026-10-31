# E2.6 失败记录

GPU NOT_AUTHORIZED；未训练、未更新参数。科学门槛失败保持原判。空值代表NaN/NOT_EVALUABLE，不能用0替换。

| 编号 | 类别 | 对象 | 失败机制/事实 | 证据 | 处置 |
| --- | --- | --- | --- | --- | --- |
| F01 | 科学门槛失败 | G01_004/ref13 small | 2/6=33.3% < 预注册50%；extra22/32不替代small | INITIALIZATION_VALIDATION.csv / THREE_REFERENCE_NEURAL_GATE.json / 图3 | 保留FAIL；单一校准停止，不删参考或换像素 |
| F02 | 潜在覆盖失败 | G01_004全部3源 | 相对历史A从6/6分别降为5/6、4/6、2/6；对B无下降 | metrics/HISTORICAL_FIXED_COVERAGE.csv / 图3 | 两种历史对照均列出；不跨视频切换候选制造PASS |
| F03 | 恢复机制失败 | 全负控制、两视频/6源/2精度 | Mask几何与trunk梯度12/12未达有效阈值；227/227高opacity但0前交叉 | STABLE_MASK_GRADIENT_TESTS.csv / metrics/ZERO_LEVEL_VS_OPACITY.csv / 图2 | 不以beta梯度或高opacity判恢复；仅检查预批准弱锚点 |
| F04 | 旧实现数值失败 | FP32 old BCE | 13项损失非有限：正常6、全负6、Ring1；全正尾梯度也被旧算法截断 | STABLE_MASK_GRADIENT_TESTS.csv / 图2 | 旧失败保留；稳定新项60/60有限、目标48/48对照 |
| F05 | 候选证据不足 | Reliable-HERO weak anchor | 24项真实几何梯度、96/96点方向通过；没有更新后前交叉或内外正确表面证据 | metrics/WEAK_ANCHOR_GATE.json / metrics/WEAK_HERO_POINT_DIRECTIONS.csv | candidate_only；不加入正式主线；不假设ROI入口在外 |
| F06 | 优化目标风险未消除 | 三种loss×固定small/extra | 各7个低覆盖低总loss选择反例；共21 | COVERAGE_DEGENERACY_VALIDATION.csv / metrics/COVERAGE_GATE.json | 新评价全部拒绝；不称目标已免疫或覆盖已改善 |
| F07 | 科学边界未改变 | G01两视频 | 严格全流程留出0；HERO来源相关/冲突仍在；无GT评价 | GPU_MVP_READINESS.md / E2冻结评价身份 | 不做参考级校正，不称独立精度/临床验证 |
| I01 | 已修复执行事故 | P2第一次运行 | torch.flatnonzero不存在；首跑退出非零 | 本地 runtime/STABLE_ATTEMPT001.log；最终 runtime/STABLE_FINAL.log | 改为torch.nonzero(as_tuple=True)，同规则/像素/阈值重跑；首日志不删除 |
| I02 | 已修复trace错误 | P1 start_sdf返回字段 | 此前trace占位NaN；实际前交叉计算已使用真实入口SDF | provenance/START_SDF_TRACE_CORRECTION.json | 同一SHA网络重放修复trace；assert opacity/交叉完全不变，门槛不变 |
| I03 | 已修复环境事故 | 新worktree稀疏检出 | git add-worktree时新admin info缺失造成sparse锁路径错误 | provenance/AUTHORIZATION.json | 只创建新worktree info并稀疏检出；不reset/clean任何旧目录 |
| I04 | 已修复交付脚本事故 | 来源manifest生成 | dict重复传入role关键字，报告脚本首跑退出 | 本地 runtime/REPORT_ATTEMPT001.log / runtime/REPORT.log | 删除重复关键字后仅重生成文档与来源SHA；不重跑神经实验 |

图证：[初始化](figures/Fig1_initialization_zero_and_front.png)、[数值/梯度](figures/Fig2_stable_mask_and_gradients.png)、[逐参考](figures/Fig3_three_reference_neural_gate.png)、[可见区域](figures/Fig4_ring_visible_supervision.png)。实现事故的失败日志仅本地保留并在DELIVERY_MANIFEST中记录SHA。完整实验统计与固定审计表见[唯一技术报告](TECHNICAL_REPORT.md)。
