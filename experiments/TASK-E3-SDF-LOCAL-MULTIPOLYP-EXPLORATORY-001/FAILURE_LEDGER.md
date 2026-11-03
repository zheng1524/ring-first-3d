# 失败、风险和未完成记录

|记录|事实及原因|处理/证据|
|---|---|---|
|M1_BASELINE_ABSENT|旧正式M1=0，仅一次性资源测试25步；旧后台仍为M0|已问研究者并获明确1000→10000；ACTUAL_M1_AND_M0_STATE_AUDIT.json，不假冒M1|
|M0_SCOPE_SUPERSEDED|旧200k作业被研究者新本地探索范围取代；不是数值或科学失败|只停止本人两个已核验PID；保全11k完整状态，最后日志11200，不声称未保存步已恢复；PREVIOUS_JOB_HANDOFF.json|
|CAMERA_UNCERTAINTY|9源中6份INSUFFICIENT_EVIDENCE、3份CONDITIONAL_USABLE，均条件研究入组|CURRENT_CAMERA_GATE_RECHECK.csv；保持数值阈值，不能认证绝对位姿|
|G07_NOT_SELECTED|仅两个可入组分区，其余B3来源未入组|使用G08三个分区；基于资格/分区，不基于模型输出|
|G08_CLEANUP_DAMAGE|同一固定A2/全B派生规则可能移除有效面并产生孔洞，不能写为无损|G08_005_CLEANUP_SUMMARY.json逐源计数；保留原深度/ID/决策，不补孔，评价仍计原分母|
|HERO_CONFLICT|不同来源存在深度冲突/共同上游相关性，.25权重是未校准代理|全源保留；不校正HERO、不用逐像素参数；不将训练视角作为独立GT|
|COMPUTE_NOT_CONVERGENCE|10000为探索预算，非论文200k充分训练|低Loss或较平滑不能判科学成功，早期差不能判路线失败|

三个非更新GPU探针均参数不变、损失/完整梯度有限；正式状态在groups/*/metrics/single_M1_STATUS.json，任何数值/OOM故障保留INTERRUPTION，不能改写为充分训练科学失败。

GT/Oracle/DXY、相机优化、新HERO、阈值搜索、输出后换源、其他用户作业干预均为0。未执行的组/阶段保留NOT_RUN/NaN，不通过历史预测回退补齐。
