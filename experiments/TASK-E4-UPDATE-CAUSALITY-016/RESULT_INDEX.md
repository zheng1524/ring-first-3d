# RESULT_INDEX

[技术摘要](TECHNICAL_REPORT_SUMMARY.md)、[失败记录](FAILURE_LEDGER.md)、[协议](01_PROTOCOL.md)。

- metrics/SAMPLING_PAIRED_COMPARISON.csv：11例采样配对。
- metrics/NATIVE_AND_GEOMETRY.json：29个新/旧输出的同分母观察与几何。
- metrics/GT_COMPARISONS.csv：26条真实路线，尺度固定1最佳SE3后评价。
- metrics/VIRTUAL_GT_COMPARISONS.json：虚拟固定坐标、无ICP表面方向诊断。
- arms/DIAGNOSTIC/metrics：逐视角face/edge/vertex、分量梯度、实际attempt/ramp、影子提案、G02数值隔离。
- local_results/Gxx_RING_WITNESSES.npz：真实CAD与冲突见证点。
- review_meshes/Gxx：全部新结果及标识明确的静态旧对照，精确原生mm NPZ/PLY。
- config/RUN_REGISTRY.json、VIRTUAL_RUN_REGISTRY.json：全部最终Mesh绝对路径；同目录FINAL.pt为完整优化器/RNG，原始源不覆盖。
- figures/Fig1–Fig4：四类核心图。源码/输入/预测哈希在provenance。

- metrics/CHECKPOINT_INDEX.json：16个本轮完整优化器/RNG检查点的绝对路径、SHA与实际状态字段；projected非Adam接受后动量状态可能按算法清空，这仍是完整实际状态。恢复只在相同配置/资产的新派生目录执行对应train脚本的 --resume。辅助脚本可在运行期间增补，正式优化器/损失/Guard/配置的34文件冻结哈希保持不变。
