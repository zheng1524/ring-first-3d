# E4 同核双向局部恢复候选 v0.8

状态：`REPORTED / MIXED_A_UNDER_EXPANSION_B_PASS`。仅授权的两个 IIa6.5 控制实验完成；不升级正式主线，不推广其他形态，等待人工审核。原 [v0.7](KEY_TECHNICAL_VERSION_E4_LOCALIZATION_CANDIDATE_v0.7.md) 及其 FINAL、失败与审计记录保持不变。

记录位于原实验目录下 `runs/SAME_KERNEL_BIDIRECTIONAL_001`，运行前源码与协议冻结提交 `fceeef873fbbe38d53267cdd4d4a669b3059387b`。GT、初始及预测共用原 0.15 mm 四面体网格、同一 Wendland C4 核、1.8200001 mm 支持半径及官方原样 Kaolin DMTet。预登记同一位置、SDF 幅值 −0.39/+0.39 mm，四参数优化、原初始化和目标、Powell 预算均保持。GT 参数只用于生成及预测冻结后的审计；没有 GT 重启或中间结果选模。

两组分别重新执行五相机 BASE/TARGET 与 Ring 投影门禁，全部通过。相机、Ring、三个拟合及两个留出视角不变。所有保存轮次闭合、单连通、无全三角面 FCL Ring 碰撞，初始/GT/最终的独立 Blender EXACT 交集体积均为零。

- 扩张：拟合/留出 Mask IoU 为 0.995801/0.997997，核中心误差 0.493503 mm，Z 偏差 −0.476294 mm；统一最近曲面距离算子的物理峰值 0.124478 mm，对应 GT 0.297222 mm，仅恢复约 42%，物理幅度门槛失败。新增体积 0.249708 mm³，对应 GT 0.561476 mm³。
- 收缩：拟合/留出 IoU 为 0.996088/0.996587，中心误差 0.133960 mm，Z 偏差 +0.037237 mm；更新区域表面 IoU 为 0.915914，真实封闭 Mesh 删除 0.552374 mm³，对应 GT 0.591593 mm³。固定积分删除区 IoU 代理为 0.904070，满足本次冻结控制门槛，仍不等于精确重现或真实病例认证。

GT 与预测均采用初始 DMTet 表面同一有符号最近面距离变化进行主评价；没有混用材料顶点位移。独立同法线射线检查中，收缩组缺失 351/11,374，保留 NaN 和完整分母。相同 SDF 系数不代表相同物理位移或二维信息量。

冻结后原目标代入 GT：扩张 GT/最终损失 0.023825/0.024973，GT 略好但未达预登记“明显更优”；收缩为 0.024346/0.023791，原目标反而偏好略不准确的几何。GT 前向渲染通过门禁，轮廓像素采样偏置、初始化及耦合搜索仍需区分，尚不能证明唯一原因。同核后扩张仍失败，不足以将旧偏差主要归因于表达不匹配。本轮没有修订目标或继续搜索。

[技术报告](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/runs/SAME_KERNEL_BIDIRECTIONAL_001/TECHNICAL_REPORT.md) · [完整指标](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/runs/SAME_KERNEL_BIDIRECTIONAL_001/PAIRED_SUMMARY.json) · [失败记录](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/runs/SAME_KERNEL_BIDIRECTIONAL_001/FAILURE_LEDGER.md) · [复现](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/runs/SAME_KERNEL_BIDIRECTIONAL_001/REPRODUCE.md)
