# 020 运行状态

COMPLETED — 全部优化、冻结后独立评价及六张核心图完成，等待人工审阅。

- 004：8 FIT + 5 HOLDOUT；005：52 FIT + 3 HOLDOUT，68视角全部保留。
- R0完整RoMa静态基线；R1/R2/R3/R3_MASK_ONLY/R3_INNER_OUTER/R4/NEGATIVE_R3各80次候选。实际接受数为68/71/48/23/47/48/9。
- R0–R3与消融不读取body/HERO参与优化；无主体预测先冻结，再执行R4；全部位姿冻结后独立评价。
- 65项工程/来源合同检查通过；这不代表科学姿态精度通过。
- 六张核心图和55目标帧的8页详细图已完成并本地保存；核心图提交Git，GLB与大文件有本地SHA索引。
- 评价阶段修复单射线CAD符号误判，原表保留；11射线复核、固定−.02mm阈值，不更改位姿。
- 科研判断MIXED：R3改善Ring与主体留出投影，但未全面改善SIFT/HERO；本轮不自动融合或升级主线。

权威冻结证据：provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json；最终检查：metrics/DELIVERY_CONTRACT_CHECKS.json。
完整结论、代码差异、失败及指标见TECHNICAL_REPORT_SUMMARY.md、METHOD_AND_INPUT_AUDIT.md和FAILURE_LEDGER.md。
