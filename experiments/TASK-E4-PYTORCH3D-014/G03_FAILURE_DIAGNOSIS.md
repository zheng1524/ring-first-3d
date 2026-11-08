# G03 更新瓶颈的实际证据

| stage | accepted | attempts | max_displacement_mm | vertices | faces | dominant_rejection |
| --- | --- | --- | --- | --- | --- | --- |
| C0 | 21 | 62 | 0.4710 | 642 | 1280 | RING_WORSENING |
| C1_8 | 22 | 59 | 0.4396 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| C2_16 | 23 | 53 | 0.4387 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| C3_32 | 24 | 54 | 0.4386 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| C4_ALL | 24 | 54 | 0.4386 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| D_D1_split | 24 | 54 | 0.4386 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| D_D2_bidir | 23 | 53 | 0.4385 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| D_D3_combo | 23 | 53 | 0.4385 | 642 | 1280 | RING_CONTAINMENT_WORSENING |
| E0_none | 9 | 39 | 0.0000 | 642 | 1280 | RING_WORSENING |
| E1_global | 40 | 40 | 0.4715 | 2562 | 5120 | RING_WORSENING |
| E2_adaptive | 9 | 39 | 0.0063 | 1293 | 2582 | RING_WORSENING |
| FINAL_014 | 7 | 67 | 0.2000 | 642 | 1280 | RING_CONTAINMENT_WORSENING |

| arm | far_associated_vertices | far_vertices_in_local_candidate_bands | image_gradient_on_far_vertices | depth_gradient_on_far_vertices | image_depth_cosine_far | Ring_uncertain_target_contour_samples | target_contour_samples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C4_ALL | 239 | 30 | 0.0009 | 0.0017 | -0.1845 | 9478 | 19968 |
| D_D1_split | 239 | 30 | 0.0009 | 0.0017 | -0.1854 | 9478 | 19968 |
| D_D2_bidir | 239 | 30 | 0.0010 | 0.0017 | -0.1867 | 9478 | 19968 |
| D_D3_combo | 239 | 30 | 0.0010 | 0.0017 | -0.1876 | 9478 | 19968 |

| stage | Dxy_AE_mm | author_axis_span_mm | GT_span_mm | lowest_point_vs_author_base_mm | GT_to_pred_p95_mm | Chamfer_MAE_mm |
| --- | --- | --- | --- | --- | --- | --- |
| FINAL011 | 0.9681 | 18.5374 | 31.1805 | 12.6487 | 11.6352 | 1.2922 |
| FINAL013 | 0.5399 | 23.0674 | 31.1805 | 7.7245 | 7.2212 | 0.9579 |
| FINAL014 | 0.6311 | 18.4081 | 31.1805 | 12.6884 | 11.7002 | 1.2733 |

远目标只表示二维最近投影代理，不是真实三维对应；Ring带目标也可能是遮挡截断边而非真实主体外轮廓。本轮只诊断、不事后过滤或调整权重。局部候选带由总梯度选择，不能假设已覆盖全部远漏轮廓区域。应结合实际梯度分量、覆盖比例和逐候选Ring/目标拒绝原因，区分区域分配、约束不可行与顶点密度。旧013的G03材料穿透约0.05297mm，014约0.00618mm（011已有约0.00615mm）。旧013的大变形同时存在稀疏Ring漏检，不能将更严格物理检查后的位移减小单独归因于学习率。FACE_ORIENTATION检查使用候选面法向与该阶段初始面法向点积为正这一保守代理；大于90°的合法面片转向也可能被拒绝，不能把该拒绝原因直接等同于已证明的网格翻面或自交。AREA_DEGENERACY同样是相对初始面积的10%限制。这些固定保护与定位/优化的限制共同存在，本轮没有为G03放宽。

E1/E2增顶点本身不改变形状；只有继续更新后的实际Mesh和GT空间缺失才构成恢复证据。Dxy或高度跨度接近不能替代柄部完整性判断。三维GT只是冻结后的独立审计，未参与定位、选择或停止。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11个独立真实物理组，不将多视频或多实验臂算成独立病例 |
| 本算法独立成功 | 11/11生成本路线FINAL014数值模型；继承人工授权011初值，数值输出不等于测量正确 |
| 本算法失败 | 数值模型失败0/11；几何验收失败或自交精度分歧3/11；另G01有Ring接触精度分歧；高度NaN 1/11，严格实体IoU NaN 9/11；逐组见FAILURE_LEDGER.md，未剔除困难病例 |
| 历史测量值回退 | 0；011/012/013仅作明确标识的初值或评价对照，没有补填014测量值 |
| 失败组及具体原因 | metrics/FAILURES.csv、逐臂运行日志、全部原始模型及核心图 |
| 最终统计样本 | 数值模型11/11；各评价项实际可计算N分别汇报，空白CSV为NaN而非0 |
| 是否使用GT选择算法 | 否；C/D/E仅用预登记FIT规则；全部模型/尺度先冻结，GT访问时间在provenance/GT_ACCESS_START.json |
