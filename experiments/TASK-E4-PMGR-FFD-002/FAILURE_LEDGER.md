# 失败台账：数值门禁未通过，全部负结果保留

| ID | 案例/环节 | 事实与原因 | 状态/证据 |
|---|---|---|---|
| FFD-01 | G01真实Mask预检 | h=1e-3有限差分跨显隐/片元事件失败；4×、8×分辨率未消除差异 | 原FAIL保留，G01仅两个更小尺度局部通过；不宣称全局连续。[原失败](metrics/PRE_RUN_VALIDATION_INITIAL_FAILURE.json)、[4×](metrics/SS4_LOCAL_AA_DIAGNOSTICS.json)、[8×](metrics/SS8_LOCAL_AA_DIAGNOSTICS.json) |
| FFD-02 | G06数值梯度与验证流程 | 训练前16项只覆盖G01，未逐案例核验即继续G06；同方向/尺度的事后QA四项均FAIL（相对差0.819–1.122） | **整体数值门禁FAIL**，G06数字输出不能称工程验证成功。已添加每案例更新前guard；没有挑新尺度/改阈值/再训练。[逐案例QA](metrics/POST_HOC_CASE_MASK_GRADIENTS.json) |
| FFD-03 | G06初始化入组实施错误 | 错误沿用R1 Mask下降门槛作为硬拒绝，首次结果NOT_EXECUTABLE；v1.1要求观测软折中 | 纠正后直接用同一候选继续原预算，无新P0搜索。原Mask下降9.210pp、体积+23.99%、原拒绝记录均保留，不改成PASS。[登记](02_G06_ADMISSION_CORRECTION.md)、[初次结果](metrics/INITIAL_EXECUTION_RESULTS.json) |
| FFD-04 | G01/C1 | P2/P3释放48/96方向后均无接受；近Ring碰撞/连续路径无法认证、QP/小步限制 | STAGE_BLOCKED。C1末端间隙约5.18e-5mm，接近实现误差带。保留失败提案和原阶段，不用同一Mesh冒充P3学习成功。[日志](metrics/G01_004_C1_UPDATE_LOG.json) |
| FFD-05 | G01/C2 | P1/P2/P3接受6/5/5，但均提前达到数值信赖域极限 | 有真实0.4285mm形变，未收敛；r10少2条命中、ref03 IoU略降也保留。[日志](metrics/G01_004_C2_UPDATE_LOG.json) |
| FFD-06 | G01/C3 | 从开始96方向，P1/P2接受13/1，P3为0；最终局部曲率代理0.9867/mm，高于C2的0.5312/mm | 更好投影/覆盖不能认作更真实，P3 BLOCKED。[日志](metrics/G01_004_C3_UPDATE_LOG.json) |
| FFD-07 | G06三个臂 | C2/C1/C3均完成实际提案，后期多无接受或数值限制；C3有约0.068mm间隙仍停滞 | 不能全部归咎Ring；Mask梯度FAIL是更根本风险。[C2](metrics/G06_004_C2_UPDATE_LOG.json)、[C1](metrics/G06_004_C1_UPDATE_LOG.json)、[C3](metrics/G06_004_C3_UPDATE_LOG.json) |
| FFD-08 | 来源与统计资格 | G01相机全INSUFFICIENT_EVIDENCE，G06部分证据不足；原B全部训练 | NO_HOLDOUT_AVAILABLE，GT/物理精度NOT_EVALUABLE，不升级资格 |
| FFD-09 | 输出计算修正 | 初次阶段非椭球位移误相对P0计算；有接受但提前结束的阶段误标BUDGET_COMPLETED | 停止后仅修派生数值/标签。原PROGRESS、更新日志、原字段与修正记录保留，几何完全未变。[修正](metrics/DERIVED_OUTPUT_CORRECTION.json) |

所有接受端点均通过既有物理检查；拒绝候选中真实存在穿环/自交，不能因为最终端点无穿环就省略。只读复核未删预测面、平滑几何或改评价分母。没有OOM、未终止他人任务、未安装新重型依赖。未执行B1/B2、未扩展其他测量组。

本轮不能宣称“FFD路线被否定”，同样不能宣称“成熟渲染库已保证真实场景可靠”。实际得到的是两组有限几何输出、明确的跨案例梯度失败与接触更新瓶颈，交由人工/PM审阅。
