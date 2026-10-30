# EX本轮交付｜等待PM独立验收和RA审查

任务：[TASK-NEURAL-E0-COMPARE-001](../../experiments/TASK-NEURAL-E0-COMPARE-001/TECHNICAL_REPORT.md)。此文件是执行者事实交接，不替PM更新验收结论或替RA作裁决。目录内较早PM_STATUS/PROPOSED/NOT_DISPATCHED资料作为历史附件保留。

2026-10-30用户直接授权有限P0/P1；追加授权清理明确陈旧产物后，实际完成一次MonoSDF场景优化和MapAnything M0–M3四种正式权重前向。36参考、4组5视频来源核清，发现G06 raw00351和G07 raw00293曾参与旧HERO。当前严格留出0。

SDF400步完成，但吸收边界域适配错误、0观测支持面；Map四配置均产生数值，M3目标覆盖3.67%/16.81%，Ring定位仍偏约22mm，没有证明改善。不存在有效双臂科学胜负；没有四组泛化或跨视频融合。

[4核心图和全部索引](../../experiments/TASK-NEURAL-E0-COMPARE-001/RESULT_INDEX.md)、[失败](../../experiments/TASK-NEURAL-E0-COMPARE-001/FAILURE_LEDGER.md)、[复现](../../experiments/TASK-NEURAL-E0-COMPARE-001/REPRODUCE.md)。清理仅58个INCOMPLETE_DO_NOT_LOAD旧下载/装配产物，回收6.05GiB；有效权重、预测、相机、CAD及Dxy未改。

待裁决：①SDF域修正的静态门禁与另一次优化授权；②Map厘米近距尺度/pose条件的独立无GT控制；③真正留出及正式竞争否决门槛。建议先解决这些门禁，不直接批量四组。EX已停止新模型工作，等待人工转交的独立验收。
