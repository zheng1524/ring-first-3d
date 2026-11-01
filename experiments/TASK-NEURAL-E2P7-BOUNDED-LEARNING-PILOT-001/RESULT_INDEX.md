# E2.7 交付索引

**TRAINING_STOPPED / NO_LEARNING / ANCHOR_NOT_BENEFICIAL，本轮各1步。**

- [完整报告与八个科研问题](TECHNICAL_REPORT.md)、[失败记录](FAILURE_LEDGER.md)、[复现](REPRODUCE.md)
- [全部训练曲线](metrics/TRAINING_CURVES.csv)、[逐参考指标/梯度](metrics/PER_REFERENCE_METRICS.csv)、[覆盖历史](metrics/COVERAGE_HISTORY.csv)、[每步安全检查](metrics/SAFETY_EVERY_STEP.csv)
- [A/B结论](metrics/A_B_COMPARISON.json)、[最终状态](metrics/FINAL_STATUS.json)、[GPU parity](metrics/GPU_PARITY.json)、[采样比较](metrics/SAMPLING_COMPARISON.csv)
- [真实参数变化](metrics/ACTUAL_PARAMETER_UPDATES.csv)、[原分项梯度检查失败](provenance/COMPONENT_SUM_ADAM_CHECK.json)、[精确累积核验](metrics/EXACT_ACCUMULATION_VERIFICATION.json)
- [表面诊断](metrics/SURFACE_DIAGNOSTICS.json)、[区域覆盖](metrics/REGIONAL_COVERAGE.csv)、[实际低覆盖低RGB误差](metrics/LOW_COVERAGE_LOW_RGB_ERROR.csv)
- [A实际失败模型step1](checkpoints/A/STOP_UNSAFE_step001.pt)、[B实际失败模型step1](checkpoints/B/STOP_UNSAFE_step001.pt)
- [A最后安全模型step0](checkpoints/A/FINAL_LAST_SAFE_step000.pt)、[B最后安全模型step0](checkpoints/B/FINAL_LAST_SAFE_step000.pt)、[canonical FP64初始化](checkpoints/INITIAL_CANONICAL.pt)
- [检查点SHA](provenance/CHECKPOINT_HASHES.json)、[初始SHA](provenance/INITIAL_MODEL.json)、[环境](provenance/ENVIRONMENT.json)、[复用来源](CODE_REUSE_E2P7.csv)
- [Fig1 真实零面与未运行时点](figures/Fig1_SDF_learning.png)
- [Fig2 三参考图像拟合](figures/Fig2_three_reference_fit.png)
- [Fig3 真实可见零面与CAD](figures/Fig3_visible_surface.png)
- [Fig4 多视角解释和覆盖曲线](figures/Fig4_multiview_validation.png)
- [四图浏览页](figures/index.html)、[A可见冲突面PLY](figures/surfaces/A_STOP1_visible.ply)、[B可见冲突面PLY](figures/surfaces/B_STOP1_visible.ply)
- [完整性结果](metrics/FINAL_INTEGRITY.json)、[交付manifest](provenance/DELIVERY_MANIFEST.json)

所有可见面仅是被拒绝模型的证据，不是验收通过的3D重建；未把HERO当精确GT，未外推其他视频/形态。
