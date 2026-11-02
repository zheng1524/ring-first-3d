# V6 本地定向清理：等待人工确认

V5 **103,678** 点 → 本轮屏蔽 **578** 点 → V6 **103,100** 点。六来源均逐点检查；没有沿用V5的121代理范围或两分区反证门槛。未启动NeuralFusion或GPU。

| 来源 | V5有效点 | 本轮屏蔽 | V6有效点 | 原生有效域连通分量 | 新增封闭孔洞像素 |
| --- | ---: | ---: | ---: | --- | ---: |
| ref08 | 13457 | 78 | 13379 | 3→3 | 0 |
| ref13 | 12497 | 89 | 12408 | 4→5 | 0 |
| ref03 | 23326 | 87 | 23239 | 8→4 | 0 |
| growth_r04 | 20552 | 139 | 20413 | 9→8 | 0 |
| new_r00 | 22392 | 134 | 22258 | 5→5 | 0 |
| growth_r14 | 11454 | 51 | 11403 | 2→2 | 0 |

## 定位、规则及完整身份

在完整V5的X–Z、Y–Z、X–Y及径向–Z图中定位研究者指定条带，再投回各自原生RGB核对Pixel ID。条带沿原生轮廓边缘形成一至数行离散深度，六来源共同贡献；r14还包含一段分离片层。预先固定一次区域：**世界Z＜−10.5 mm 且 X＞−3 mm**。所有来源同一规则，未根据清理后图像修改阈值。此前两个只读定位图亦保留。

这是研究者授权的人工定向区域清理，不能当作自动多视角错误认证。原有C/D标签只记录、不作为本轮否决条件。原生邻接深度跃变及8邻域分量见V6_SOURCE_COUNTS.csv；0.6mm空间邻接仅作连通诊断，不决定额外删除：选区有12个空间分量，大小[480, 50, 29, 6, 5, 2, 1, 1, 1, 1, 1, 1]。条带局部平滑、与主体根部连续的部分也被区域规则屏蔽，并非每个点都有强深度跳变。

被屏蔽点XYZ范围：[-2.959110459311146, -2.38119854963427, -15.70429100900511] 至 [14.74839649718748, 9.397363341494465, -10.500122219318623] mm。与原CAD三角面最近距离 **10.088 mm**，没有选择Ring邻近组织。V6_SUPPRESSED_NATIVE_POINTS.csv逐点保存来源、原生ID/u/v、原深度、原XYZ、旧A2标签及原因；六份V5输入完整备份并核验SHA。V4/V5及全部既有文件（486份）SHA未变；原HERO/RGB/Mask/K/c2w/CAD未改。

## 保留、缺口及限制

选定远端条带范围内剩余0点。所有Z≥−10.5mm或X≤−3mm的原V5点逐值保留，不补深度。头部Mask/Ring投影代理新增损失 **0** 点；原Mask距边界＞2px的内部代理新增损失 **18** 点。后者说明人工区域清理可能牺牲部分真实边缘，不能声称解剖表面绝对无损。

本轮新增封闭孔洞像素 **0**；原生连通域发生分裂 **3** 个。原Mask有效域拓扑只是二维代理，不能证明三维组织连通性。条带根部形成新的输入截断边缘；没有补面或连接点。r14既存头部缺口与Ring连接检查点的深度/有效性保持不变。真实细柄与独有侧面完整性需结合图3人工判读，不用已废止3px指标宣称通过。

原Raw距离＞1mm代理还剩 **107**（本轮移除14）。此指标不是真值，不是本轮目标范围，也不再自动删除其他结构。没有宣称全部异常已清零。

六来源裁剪A、320×240内参变换和输出原生ID网格与V5完全相同，所有保留深度逐值相同；坐标解析转换误差＜1e−5mm。模型域保持旧V1共用27.959mm尺度，不缩域换分辨率。

## 本地交付

- 图1：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/figures/V6_Fig1_V5_vs_V6.png`
- 图2：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/figures/V6_Fig2_Removed_Structure.png`
- 图3：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/figures/V6_Fig3_Body_Multiview.png`
- 深度/有效性：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/local_results/inputs/V6`
- 同裁剪输入：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/local_results/crops/V6`
- 全部原生XYZ：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/local_results/V6_reference_V6_points_mm.ply`
- V5冻结副本：`/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/local_results/V5_backup_before_V6`
- 决策：V6_SUPPRESSED_NATIVE_POINTS.csv；结果：V6_RESULT.json；几何核对：V6_GEOMETRY_CHECK.csv。
- 复现代码：code/v6_local.py；执行命令：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B /home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/code/v6_local.py`。脚本禁止覆盖既有V6结果；当前目录不可直接重跑，以免覆盖已冻结V6或重复删除；复现须保持V5只读并另存输出。

| 审计项目 | 本轮汇报 |
| --- | --- |
| 目标组数 | 1视频，6来源；不是尺寸测量 |
| 本算法独立成功 | 6/6派生输入；仅数值生成成功，物理正确待人工 |
| 本算法失败 | 无I/O/坐标失败；真实表面无损性未认证 |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | 未做测量，无测量值；余留代理及既存孔洞如上 |
| 最终统计样本 | V5全部103678点为固定分母 |
| 是否使用GT选择算法 | 否；先冻结config/V6_LOCAL_FIXED_REGION.json，未读GT |

**阶段一完成即暂停。未创建任务分支、未提交或推送GitHub；无NeuralFusion、GPU、模型权重读取、训练或新TSDF。等待研究者明确认可和阶段二授权。**

## 最终看图核对与停止记录

三张图已逐一人工式查看：远端长条显著移除；条带根部及其他区域仍有少量散点/短枝，没有宣称所有异常清零。固定视图未见新出现的大块主体缺失，六来源最大原生连通分量均未变。3处分裂分别为ref08保留5057+2点、ref13保留4598+1点、r04保留8696+4+2点；不是主体被均分，但周边碎点/输入缺口风险保留。详见V6_COMPONENT_RETENTION.csv与V6_FINAL_REVIEW.json。

已经完成一次固定屏蔽，未追加删除或扩大范围。现暂停，待研究者明确认可图像并授权阶段二；未开始NeuralFusion。
