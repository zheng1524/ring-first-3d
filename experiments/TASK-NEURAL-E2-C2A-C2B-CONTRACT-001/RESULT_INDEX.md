# E2交付索引

- [完整技术报告](TECHNICAL_REPORT.md)：唯一实验报告，含固定审计表、数值、图、可进入GPU条件判断。
- [失败/限制记录](FAILURE_LEDGER.md)、[CPU复现](REPRODUCE.md)、[复用审计](CODE_REUSE_E2.csv)。
- [四张核心图浏览](visualizations/index.html)：全部标注CPU/解析控制，无新模型输出。
- [C2a总门槛](metrics/C2A_GATE.json)：81；[C2b数据](metrics/C2B_DATA_GATE.json)：44；[Map输入](metrics/C2B_MAP_GATE.json)：150；[最终完整性](metrics/FINAL_VALIDATION.json)：257。
- [GPU readiness](metrics/GPU_READINESS.json)：false；GPU NOT_GRANTED。
- [源数据Manifest](provenance/C2B_DATA_MANIFEST.json)、[Map Manifest](provenance/MAP_M0_M4_DATA_MANIFEST.json)、[留出身份](provenance/EVALUATION_IDENTITIES_FROZEN.json)。
- [最终交付SHA清单](provenance/DELIVERY_MANIFEST.json)、[增量上传实测](provenance/GIT_SYNC_VERIFIED.json)。最终HEAD同步回执在本地runtime/FINAL_GIT_SYNC.json，避免自引用提交SHA。
- LOCAL_ONLY：local_results与runtime；122输入来源清单为provenance/E2_READONLY_INPUTS_AND_SHAS.json。未上传原视频、深度NPZ、权重、GT。

物理组G01共1组、2视频、6参考；新测量独立输出0/1，误差NaN，无历史回填。C2a/C2b CPU合同通过有明确限制，均不能直接启动正式GPU科学实验。
