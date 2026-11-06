# 结果索引

核心审阅图：figures/Fig_Overview_Nine_Cases.png，Fig_Ip_Detailed.png，Fig_Is_Detailed.png，Fig_IIa_Detailed.png。

每个G01–G09均有：

- `figures/full/Gxx_Detailed.png`：真实视角、内部深度、背景ROI、平面、A/B/C与实际更新过程。
- `figures/full/Gxx_All_Candidates.png`：三个初值轮廓/深度、星凸或冠面各级及最终选择；包括失败候选。
- `inputs/Gxx/INITIAL.npz` 和 INITIAL_PROVENANCE.json：真实旧A或首次实例化旧规则的来源。
- `inputs/Gxx/BASE.json` 和 BASE_EVIDENCE.npz：原始背景点、平面、稳定性、接触证据。
- `local_results/Gxx/B_seed{0,1,2}_{CONTOUR,DEPTH}.{json,npz}`：全部实际阶段。
- `local_results/Gxx/B_SELECTED.{json,npz}`、`C_SELECTED.{json,npz}`、对应`*_mm.ply`：最终冻结候选；NO_FEASIBLE也是有意保留的诊断模型。
- `local_results/Gxx/B_STAR_CANDIDATE.*`、`C0_BASE_CANDIDATE.*`/C1/C2：规则触发时的额外低维候选；不存在表示未触发，不代表文件遗漏。
- JSON中的history记录真实函数调用与参数/损失；history[0]保存实际扰动初值。`STAGE_PARAMETERS.csv`汇总每阶段，selected副本与原阶段重复，**不能累加该表的耗时作为实际总耗时**。实际耗时用runtime/SERIAL_STATUS.json。

所有模型文件的绝对路径、大小、SHA见assets_index/LOCAL_RESULTS_INDEX.json。大输入与网格保存在本机；Git仅代码、配置、小指标/索引与四张核心图。完整九例原始/失败模型不会因为没有上传到Git而被删除。
