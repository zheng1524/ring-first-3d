# E2当前交付索引

- [单份完整技术报告](TECHNICAL_REPORT.md)：第1–8节为原冻结交付，第9节为本轮CPU继续执行。
- [新增证据索引](continuation_cpu/README.md)、[六张核心图浏览](continuation_cpu/visualizations/index.html)。
- [最新失败记录](FAILURE_LEDGER.md)、[仅新增CPU复现](REPRODUCE.md)。
- 本轮新增：联合接线72项、输入合同70项；[完整性核验](continuation_cpu/metrics/FINAL_CONTINUATION_VALIDATION.json)。原275项阶段检查和257项完整性记录保留，未重跑。
- [共同HERO几何Manifest](continuation_cpu/provenance/COMMON_HERO_GEOMETRY_MANIFEST.json)、[本轮交付Manifest](continuation_cpu/provenance/CONTINUATION_MANIFEST.json)。原Map M0–M4的16配置和30派生深度未改变。
- [GPU门槛](continuation_cpu/metrics/GPU_READINESS.json)：NOT_READY / NOT_GRANTED。官方神经模型/采样器执行0、更新0、新测量0/1、误差NaN。
- 原冻结分支exp/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001保持5d4bcbb；本轮独立续作分支exp/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001-cpu-continuation。远端回执在本地runtime/CONTINUATION_FINAL_GIT_SYNC.json。
