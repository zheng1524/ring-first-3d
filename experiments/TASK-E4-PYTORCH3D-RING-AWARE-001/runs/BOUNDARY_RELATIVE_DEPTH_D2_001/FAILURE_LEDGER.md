# D2 失败记录

| 病例 | 失败与限制 | 证据 |
|---|---|---|
| virtual_IIa | B/E1/E2/E3自交21/93/72/94对；Chamfer改善未消除尖刺，高度仍高于GT | [阶段网格](figures/full/FigA_virtual_IIa_Evolution.png)、BLENDER_CHECKS、EXACT_GEOMETRY、VIRTUAL_SHAPE |
| virtual_Ip | 原GT非邻接相交67对；所有预测自交，E1至少256对已确认（候选277），不能报告有效实体体积 | [阶段网格](figures/full/FigA_virtual_Ip_Evolution.png)、NATIVE_GT_SOLID_AUDIT |
| virtual_Is | 原GT相交3对；P0欠表达；全部最终穿环并大量自交；E3比E2 Chamfer更差 | [阶段网格](figures/full/FigA_virtual_Is_Evolution.png)、FigD、EXACT_GEOMETRY |
| real_Ip | B微小穿环；E1/E2/E3几何门槛通过但无完整GT、相机仍INSUFFICIENT_EVIDENCE，E2/E3不统一优于E1 | [阶段网格](figures/full/FigA_real_Ip_Evolution.png)、ENDPOINTS |
| real_IIa | 原P0穿环.087mm；B/E1/E2/E3均未消除，深度方案到.198–.253mm；E3命中率下降 | [阶段网格](figures/full/FigA_real_IIa_Evolution.png)、DEPTH_EVALUATION |
| real_Is | 原P0穿环.541mm，全部条件仍穿环，E3新增9对自交；留出相机条件性不足 | [阶段网格](figures/full/FigA_real_Is_Evolution.png)、CASE_LOCK、EXACT_GEOMETRY |

工程问题：

- SCALE_VALIDATOR_V1：后验验证器错误地把G07 R5当R10。来源清楚，实际CAD内径4.999999mm，与来源R5一致。仅纠正验证契约，不改相机/CAD/尺度/预测。保留assets_index/VALIDATE_V1_ASSUMED_ALL_R10.py.txt和runtime/VALIDATE_V1_ALL_R10_ASSUMPTION_FAILED.log。
- SECTION_DEPENDENCY_V1：Trimesh polygons_full缺Shapely，初版截面积为缺失/无交线0，不能解读为全零面积。保留assets_index/V1_SECTION_DEPENDENCY_FAILED_*；使用同原Mesh的闭环交线鞋带公式替代评价依赖，SECTION_OPERATOR_AUDIT含解析控制。未重跑优化。
- 评估阶段未命中射线的inf-inf会发出RuntimeWarning；只在pair两端有效时统计，固定缺失代价保留，未将NaN用于训练。训练全过程无非有限梯度/损失停机。
- 原生虚拟Ip/Is实体GT未通过，无效实体指标NOT_EVALUABLE；没有更换病例或修补GT制造成功。三维表面距离仅对原参考曲面可定义。

保留所有固定检查点，不删除面，不修补，不选中间最佳轮次，不增加调参或扩展任务。
