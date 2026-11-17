# 失败与限制记录

| ID | 事实 / 状态 | 具体证据与处置 | 未证明的原因 |
| --- | --- | --- | --- |
| A01 | OBSERVED：ref08 主 SINGLE 命中 89.56%，门槛 ≥90%，FAIL | config/SINGLE_FIRST_ATTEMPT_FAILURE.json；单源断言后停止多源，保存输出；881/1436 未命中邻近 Mask 边界，555 在内部 | 不能仅用边界解释全部未命中 |
| A02 | OBSERVED：单位等价表面代理最大 0.0020026695 mm >0.002 mm，FAIL | config/SINGLE_DIAGNOSIS.json；不四舍五入、无门槛修改；原最近顶点实现另存 | 主要残差可能与 FP32/网格交点有关，但未完全定位；连续数学 Hausdorff 未算 |
| A03 | OBSERVED：唯一 0.05 mm 对照命中 96.01%；总体严格门槛仍 FAIL | voxel 对照预登记，G0/G1 仍 0.1 mm；未扩搜索 | 对照不能证明所有区域均可靠 |
| D01 | OBSERVED：G0/G1 1700/2526 分量，封闭分量 722/853 | config/TOPOLOGY_AND_SUPPORT.json；所有原输出面保留。封闭总面积 25.79/16.59 mm²，整体均非水密 | 深度冲突、相机与 TSDF 贡献混淆 |
| BC01 | OBSERVED：ref08 合格深度一致率 50.22%→27.98%，但 Mask 覆盖提高 | G0_G1_METRICS.csv；固定原始分母、未命中计失败；不能以更高覆盖或小近邻距离宣称成功 | 哪个新增来源造成多少因果影响本轮未做逐源消融 |
| CD01 | OBSERVED：G1 远端面距六个原 Mesh 43.845 mm；>1 mm 的面积 1.5748 mm² | NATIVE_RAW_DISCRETIZATION_DIAGNOSTICS.csv、config/EXTENSION_DIAGNOSIS.json、Fig3/4；保留异常，无删面 | 孤立 Mask 深度、边界离散化及原面有效域共同作用；不是错误解剖 GT |
| C01 | OBSERVED：native 与 Raw Mesh 有效域不完全相同 | 六来源 >1 mm 原生点数 243/110/134/124/283/200；原面身份/深度未改 | 不自动把 native/Raw 不同视为来源篡改 |
| B01 | UNRESOLVED：new_r00/growth_r14 只获条件性准入 | VIEW_COVERAGE_SELECTION.csv；全部 5 区有来源，未认证绝对位姿；未用旧融合认证相机 | 深度与位姿误差难区分；不得据 Mesh 好坏重选 |
| E01 | UNRESOLVED：细柄与未知背面的物理真实性 | Fig3 标注可能细结构，缺少认证解剖身份；召回率/直径/形状误差 NaN | 不把孤立面或生成面称为已认证解剖 |
| S01 | API 限制：legacy ScalableTSDFVolume 无完整 Python volume 序列化/权重导出 | LOCAL_RESULTS_INDEX.json；保存官方观测带、完整 Masked RGB-D、参数/顺序/重放；G0 独立重放验证通过 | 带不是全量体积快照，不可直接恢复全部权重，只能重放 |
| P01 | 流程偏离透明记录：严格单源门槛未全通过仍完成诊断 G0/G1 | config/DIAGNOSTIC_CONTINUATION.json；定位非严重单位/相机方向错误和部分离散化问题后，按任务要求运行失败机制基线；未冻结适配器 | 不将诊断输出升级为验收成功 |

F1–F3 依冻结的三项来源选择规则取原面；F2 个别位置近邻距离仍小，不能把小变化包装为大失败。F3 为改善对照且邻 CAD 遮挡，不认证新可见解剖。F4 是明确标识的后验远端异常，不改变主评价分母。所有实际坐标/Face ID 在 TSDF_FAILURE_CASES.csv；状态为 OBSERVED、原因 HYPOTHESIS/UNRESOLVED。

保护：原始输入 SHA、历史工作树 HEAD/脏文件状态核对通过；无 GT、GPU、新推理、训练、自定义权重、相机更新、清理或几何删改。
