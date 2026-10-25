# TASK-PHASEC-DENSITY-MULTIGROUP-001｜结果索引

状态：ENGINEERING_COMPLETE / DIAGNOSTIC_ONLY / STOPPED_FOR_HUMAN_REVIEW。8独立组、9视频、13参考、213,654原点全部保留；D0/D1候选2,224/535，无真实准确率。

- 唯一完整[技术报告](TECHNICAL_REPORT.md)，含Q1–Q4、全部分母、基线、GT=NONE、失败和停止原因。
- [运行前规则](PROTOCOL.md)、[冻结配置](config.json)、[输入身份](metrics/input_identity.csv)、[输入SHA](provenance/INPUT_FREEZE.json)。
- [逐参考D0/D1](metrics/reference_metrics.csv) / [结构化完整分布](metrics/reference_metrics.json)、[逐物理组](metrics/group_metrics.csv)、[正常/压力/形态/环分层](metrics/stratified_macro.csv)、[配对支持集](metrics/D0_D1_paired.csv)。
- [G01过渡剖面](metrics/transition_profiles.csv)、[描述区域](metrics/qualitative_regions.csv)、[采样相关性](metrics/sampling_correlations.csv)。
- [反例](metrics/dense_conflict_counterexamples.csv)、[细结构/边界风险](metrics/thin_boundary_risks.csv)、[Ring姿态条件风险](metrics/Ring_visibility_risk.csv)、[全13参考失败清单](metrics/failure_ledger.csv)。
- [11项数值检查](metrics/numerical_tests.json)、[109项最终核验](metrics/validation.json)、[源码哈希清单](provenance/EXECUTION_SOURCES.json)、[冻结输出哈希](provenance/DIAGNOSTIC_OUTPUTS_FROZEN.json)。
- [四图哈希/渲染身份](provenance/FIGURE_MANIFEST.json)、[公开文件清单](provenance/PUBLICATION_MANIFEST.json)。

| 真实PNG | 主要审查内容 |
| --- | --- |
| [Fig1](figures/Fig1_004_ref13_density_continuity.png) | 004_ref13密度、拉伸、过渡与D0/D1，同视角/尺度 |
| [Fig2](figures/Fig2_005_raw00057_dense_sparse.png) | 005_raw00057内部密集/稀疏对比及另两原参考 |
| [Fig3](figures/Fig3_multigroup_real_P0.png) | Ip、Is、IIa、R5真实P0及压力条件 |
| [Fig4](figures/Fig4_counterexamples_failures.png) | 细结构潜在误伤、密集模型冲突与不合格相机反例 |

本地完整字段：`/home/liu/ring_first_3d/experiments/TASK-PHASEC-DENSITY-MULTIGROUP-001/local_fields/`，每份`*_fields.npz`含全部原XYZ毫米和源u/v，另存group/actual_video/reference_frame及D0/D1软分数、候选、原密度/归一密度、kNN、法向可靠性、梯度与邻接。每点身份`(group, actual_video, reference_frame, source_u, source_v)`；无删除，原Mesh路径见CASES。完整源码在同任务`code/`，原始输入/缓存继续原位只读。未公开任何源码全文、NPZ、PLY/GLB、原RGB/Mask、视频、权重。

实际阶段提交：协议`e4ab4ae17ee856c84b7522ffce53c358bb3a0294`；结果/四PNG`d541afe8d32dd228ea3720c512e922135112e35b`。最终报告提交以本文件所在commit及交付消息为准；[分支提交记录](https://github.com/zheng1524/ring-first-3d/commits/exp/TASK-PHASEC-DENSITY-MULTIGROUP-001)。本地产物`provenance/REMOTE_RECEIPT.json`在最终push读回后记录最终SHA与远程blob核验，不自引用写入报告。

任务结束，等待PM与用户验收。未自动启动清理、融合、配准或扩组推理。
