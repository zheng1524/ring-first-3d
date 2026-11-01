# E3-C FAILURE LEDGER

工程实现完成，科学错误识别门槛未确立。所有源、候选和原面保留；不存在以低冲突/高支持制造物理PASS。

| ID | 对象 | 具体机制 | 处置 | 证据 |
| --- | --- | --- | --- | --- |
| SCI01 | 核心科学门槛 | 长条代理比光滑共视代理更少被F3标出，无法可靠认证错误延伸 | 不改误差窗/质量门槛；总体科学资格NOT_ESTABLISHED | [分层结果](metrics/ALL_OBSERVERS_STRATUM_RESULTS.csv) · [图4](figures/Fig4_multiview_multigroup_ablation.png) |
| SCI02 | G01_004 | 长条2.52%冲突，对照光滑共视50.83%；相机上游仍有条件 | 保留所有源与冲突，不能判谁错 | [源矩阵](SOURCE_SUPPORT_MATRIX.csv) · [图1](figures/Fig1_multisource_consensus.png) |
| SCI03 | G01_005 | 长条16.04%冲突，对照45.12%；高Support与冲突可并存 | 全部8参考保留，包括RESERVED和困难参考 | [逐候选证据](VISIBILITY_EVIDENCE.csv) · [图3](figures/Fig3_extension_and_unique_surfaces.png) |
| SCI04 | G06/G08 | 无长条代理样本，不能验收异常识别；相机仍条件性/LIMITED | N=0显示N/A，不报零错误率 | [分层结果](metrics/ALL_OBSERVERS_STRATUM_RESULTS.csv) · [图4](figures/Fig4_multiview_multigroup_ablation.png) |
| SCI05 | G07 | 未获父阶段相机资格，不在17正式源 | 保留压力身份，不因排除它称四物理组数值成功 | [父阶段资格](../TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001/metrics/E3_CAMERA_QUALIFICATION.csv) |
| SCI06 | 真实物理对应/结构 | 共同Mask/法向/空间格不认证同表面；无真实错误或侧面标签 | 物理准确性NOT_EVALUABLE，所有physical_truth保持UNRESOLVED | [合同](CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md) |
| SCI07 | 表示敏感冲突 | 737条有限Raw比较发生分歧，2202条缺Raw首交 | 不把弃权数当纠正真误检；native模式也保留 | [表示敏感性](metrics/REPRESENTATION_SENSITIVITY.csv) · [冲突表](FREE_SPACE_CONFLICTS.csv) |
| SCI08 | 消融归因 | 原预注册V0/V1的Support资格不同，且B0已有CAD | 保留原结果；追加同C0通道控制，明确为观察后审计；不能隔离Ring-only因果收益 | [完整消融](V0_V3_ABLATION.json) |
| SCI09 | 模式/采样局限 | 每面只用重心；每Mesh仅首次射线交点；误差窗/依赖权重未校准 | 未采样面UNASSESSED，不能认证全域或穷尽隐藏层 | [模式表](MULTIMODAL_DEPTH_CANDIDATES.csv) · [合同](CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md) |
| ENG01 | 首次CSV导出 | 逐行重复解压NpzFile造成耗时，完成几何查询后在导出段INT停止 | 保留未完成gzip与日志；只重做导出，场查询和分数不变 | [执行索引](provenance/EXECUTION_LOG_INDEX.json) |
| ENG02 | native模式可见性标注 | 初版使用候选位置的可见性，非native模式自身位置 | 更正位置上的标志；64模式位置逐项未变，旧表保留runtime | [模式检查](metrics/CONSENSUS_VALIDATION.json) |
| ENG03 | 图4空分层 | G06/G08没有长条样本 | 显示N/A，未调规则生成样本 | [图4](figures/Fig4_multiview_multigroup_ablation.png) |
| ENG04 | 首次交付链接检查 | 执行日志索引在链接检查之后才生成，首次报缺链接 | 把索引生成移到链接检查之前；保留失败日志，不改验证标准 | [执行索引](provenance/EXECUTION_LOG_INDEX.json) |

没有物理测量输出，历史测量回退0；测量误差MedARE/MAE/p95/max均NaN，共同成功配对N=0。
