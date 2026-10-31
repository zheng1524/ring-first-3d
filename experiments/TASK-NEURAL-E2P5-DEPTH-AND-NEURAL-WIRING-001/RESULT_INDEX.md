# E2.5交付索引

- [唯一完整报告](TECHNICAL_REPORT.md)、[失败记录](FAILURE_LEDGER.md)、[复现](REPRODUCE.md)。
- [四张核心图浏览](visualizations/index.html)。
- [深度处理决定](docs/DEPTH_CORRECTION_DECISION.md)：首轮原生HERO+稳健权重，D2不建议。
- [具体GPU MVP建议](docs/GPU_MVP_PREREGISTRATION.md)、[机器可读配置](config/GPU_MVP_PROPOSED.json)：BLOCKED/NOT_AUTHORIZED。
- [跨视角残差](metrics/HERO_PAIRWISE_DEPTH_CONFLICTS.csv)、[Ring残差](metrics/RING_DEPTH_RESIDUALS.csv)、[偏移诊断](metrics/DEPTH_BIAS_DIAGNOSTICS.csv)。
- [真实官方CPU Gate](metrics/OFFICIAL_SDF_CPU_GATE.json)：CPU计算通过，三参考范围失败；[完整逐源梯度](metrics/NEURAL_PER_REFERENCE_GRADIENTS.csv)。
- [退化反例](metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv)、[明确结论](metrics/DEGENERACY_EXPLICIT_CONCLUSION.json)。
- [交付完整性](metrics/DELIVERY_VALIDATION.json)、[SHA清单](provenance/DELIVERY_MANIFEST.json)、[增量上传](provenance/GIT_SYNC_STAGE12.json)。最终HEAD远端回执在runtime/FINAL_GIT_SYNC.json，避免自引用。

MODEL_FORWARD CPU_DIAGNOSTIC_ONLY；TRAINING NOT_RUN；OPTIMIZER_STEP0；GPU NOT_AUTHORIZED；MAPANYTHING NOT_RUN；NEW_RECONSTRUCTION NOT_CLAIMED。
