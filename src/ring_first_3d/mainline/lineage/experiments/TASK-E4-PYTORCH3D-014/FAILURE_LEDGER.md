# 失败记录（原始结果完整保留）

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11个独立真实物理组，不将多视频或多实验臂算成独立病例 |
| 本算法独立成功 | 11/11生成本路线FINAL014数值模型；继承人工授权011初值，数值输出不等于测量正确 |
| 本算法失败 | 数值模型失败0/11；几何验收失败或自交精度分歧3/11；另G01有Ring接触精度分歧；高度NaN 1/11，严格实体IoU NaN 9/11；逐组见FAILURE_LEDGER.md，未剔除困难病例 |
| 历史测量值回退 | 0；011/012/013仅作明确标识的初值或评价对照，没有补填014测量值 |
| 失败组及具体原因 | metrics/FAILURES.csv、逐臂运行日志、全部原始模型及核心图 |
| 最终统计样本 | 数值模型11/11；各评价项实际可计算N分别汇报，空白CSV为NaN而非0 |
| 是否使用GT选择算法 | 否；C/D/E仅用预登记FIT规则；全部模型/尺度先冻结，GT访问时间在provenance/GT_ACCESS_START.json |


| case | stage | reason | evidence |
| --- | --- | --- | --- |
| G02 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G02 | EVALUATION | NOT_EVALUABLE_ENTITY_VALIDITY | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G03 | FINAL014 | Independent64-stage Ring worsening exceeds frozen1e-5mm epsilon | [metrics/POST_GEOMETRY_AUDIT.csv](metrics/POST_GEOMETRY_AUDIT.csv) |
| G03 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G03 | EVALUATION | NOT_EVALUABLE_ENTITY_VALIDITY | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G07 | EVALUATION | NOT_EVALUABLE_ENTITY_VALIDITY | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G04 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G04 | EVALUATION | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G05 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G05 | EVALUATION | NOT_EVALUABLE_ENTITY_VALIDITY | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G06 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G06 | EVALUATION | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G08 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G08 | EVALUATION | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G09 | EVALUATION | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G10 | FINAL014 | Independent Blender BVH nonadjacent self-intersection pairs detected | [metrics/POST_GEOMETRY_VALIDITY.json](metrics/POST_GEOMETRY_VALIDITY.json) |
| G10 | FINAL014 | No Chamfer improvement against013 under the same best rigid evaluator | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G10 | EVALUATION | NOT_EVALUABLE_ENTITY_VALIDITY | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G11 | EVALUATION | No verified author base; height remains NaN | [BLENDER_ALIGNMENT_METRICS.csv](BLENDER_ALIGNMENT_METRICS.csv) |
| G03 | C0 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G06 | C0 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | C1_8 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | C2_16 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | C3_32 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | C4_ALL | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | D_D1_split | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | D_D2_bidir | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | D_D3_combo | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | E0_none | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G04 | E1_global | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | E2_adaptive | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G04 | E2_adaptive | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G02 | FINAL_014 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G03 | FINAL_014 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G09 | FINAL_014 | FIXED_STALL_STOP | [运行汇总](metrics/ALL_RUNS.csv) / [拒绝统计](metrics/REJECTION_REASON_COUNTS.csv)；完整日志见本地索引 |
| G01 | POSE | B1 held background residual remains large; B2 not justified; time-negative control drifts0.381mm | [POSE_CORRECTION_REPORT.md](POSE_CORRECTION_REPORT.md) |
| G08 | OBSERVATION | video00640 raw candidates have no anchored metric camera; retained unknown, not fabricated | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| ALL | OBSERVATION | 34 independent photos lack verified metric projection; retained in inventory | [config/RAW_ASSETS.json](config/RAW_ASSETS.json) |
| G06 | ENGINEERING_RESOLVED | C0 resource interruption; exact optimizer/RNG checkpoint resume, original log retained | [provenance/G06_RESOURCE_INTERRUPT.json](provenance/G06_RESOURCE_INTERRUPT.json) |
| G01 | ENGINEERING_RESOLVED | Repeated-key score serialization failure after first C0 model; no retraining | [provenance/IMPLEMENTATION_AMENDMENTS.md](provenance/IMPLEMENTATION_AMENDMENTS.md) |
| G02 | C4_ALL_READ_ONLY_GRADIENT | Original1e-4 relative additivity check FAIL: 0.00016808258; numerical repeat floor separately measured, no threshold relaxation | [metrics/GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv) |
| G11 | C4_ALL_READ_ONLY_GRADIENT | Original1e-4 relative additivity check FAIL: 0.0002154809; numerical repeat floor separately measured, no threshold relaxation | [metrics/GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv) |
| G02 | D_D1_split_READ_ONLY_GRADIENT | Original1e-4 relative additivity check FAIL: 0.00055020661; numerical repeat floor separately measured, no threshold relaxation | [metrics/GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv) |
| G11 | D_D1_split_READ_ONLY_GRADIENT | Original1e-4 relative additivity check FAIL: 0.00021600104; numerical repeat floor separately measured, no threshold relaxation | [metrics/GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv) |
| G02 | D_D2_bidir_READ_ONLY_GRADIENT | Original1e-4 relative additivity check FAIL: 0.00027274001; numerical repeat floor separately measured, no threshold relaxation | [metrics/GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv) |
| G02 | D_D3_combo_READ_ONLY_GRADIENT | Original1e-4 relative additivity check FAIL: 0.00020639669; numerical repeat floor separately measured, no threshold relaxation | [metrics/GRADIENT_ADDITIVITY_CHECKS.csv](metrics/GRADIENT_ADDITIVITY_CHECKS.csv) |
| G01 | FINAL014_RING_CONTACT_PRECISION | FCL/Open3D double show no intersection; float32 Open3D reproduces4 Blender Ring-contact pairs, separation about5.89e-10mm; original evidence retained as unresolved precision-sensitive contact | [metrics/G01_RING_CONTACT_DISAGREEMENT.json](metrics/G01_RING_CONTACT_DISAGREEMENT.json) |
| G02 | OBSERVATION_PARTIAL | 6 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| G04 | OBSERVATION_PARTIAL | 21 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| G05 | OBSERVATION_PARTIAL | 16 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| G06 | OBSERVATION_PARTIAL | 19 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| G08 | OBSERVATION_PARTIAL | 40 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| G09 | OBSERVATION_PARTIAL | 17 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |
| G11 | OBSERVATION_PARTIAL | 3 raw candidates remain without a metric camera, not a group rejection | [metrics/UNPOSED_RAW_CANDIDATES.json](metrics/UNPOSED_RAW_CANDIDATES.json) |

逐候选级原因数并非独立物理病例数，见metrics/REJECTION_REASON_COUNTS.csv。未修改阈值制造PASS。