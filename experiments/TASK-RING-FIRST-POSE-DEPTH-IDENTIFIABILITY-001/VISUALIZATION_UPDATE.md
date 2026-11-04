# 复用 PANEL2-003 并追加 SIFT 可视化

2026-11-04，研究者明确要求基于 `/home/liu/ring_first_3d_panel2_depth/experiments/TASK-AB-SCENE-PANEL2-DEPTH-COLOR-003` 的原显示方式修改。本次在现有独立分支和实验目录内增量交付。

[打开四案例图库](visualization_panel2_sift/index.html)。旧版全部图片保留。新版上方保留原五面板，下方追加 Ring-First 与 SIFT 完整场景并列、SIFT/真实B叠加、双方共同区域RGB差异及独有支持图。

直接AST调用原 `depth_colors`、`panel2_image`、`panel_canvas`；其完整场景依赖沿用原 AB-FULL-SCENE-002 的 `scene_image`、`point_projection`、`figure_pair`、`side_plot`，以及相同的 SameCameraScene/real_p0_renderer。三份基础renderer在旧、新工作树的源码SHA相同。没有另写一套深度着色或相机点云渲染器。

显示仍为原 Raw Polyp XYZ + 原冻结 Background XYZ；粉红与蓝绿共享A轴向Z的全体正深度min/max，近亮远暗；几何点大小.08、RGB点大小.8、实体CAD、Ring平面毫米比例尺、遮挡、像素坐标及原始ID沿旧版。SIFT仅采用上一轮冻结的SIFT + RF-scale位姿，重新绘制显示，不重新估计位姿。

四案例继续使用本轮固定历史帧对。G06相同历史A/B的整张原五面板PNG直接复制，新图上部逐像素不变；其他三个B与旧Panel2案例不同，先通过原五面板函数绘图，再由原Panel2函数替换对应区域，整张五面板再复制并追加SIFT条带。四个来源的A同相机深度着色图均与原Panel2缓存逐位一致。

新图清楚标注Raw旧场景显示和Background DISPLAY_ONLY。追加误差图采用相同P/BG类别的双方实际点中心共同支持，色阶0–80；属于显示诊断，不能与原Cleaned三角面、.05mm容差的正式指标混用。原A/B科学指标、SIFT位姿和配置四份文件SHA不变，原任务全部128项冻结输入也未变。G06原图历史资格标题保留，追加条带另列当前Camera Gate资格，未升级认证。

共4张新版，173项检查通过；检查及显示元数据见 [PANEL2_SIFT_VISUALIZATION.json](metrics/PANEL2_SIFT_VISUALIZATION.json)，复用脚本/资产SHA见 [PANEL2_SIFT_BEFORE.json](provenance/PANEL2_SIFT_BEFORE.json)。

| A → B | 原P / BG点数 | A轴向Z范围 mm | 新图 |
| --- | --- | --- | --- |
| G01_004_ref08 → G01_004_growth_r14 | 14029 / 39785 | 34.791–61.896 | [查看](figures/panel2_sift/G01_004_ref08__004_14_Panel2_plus_SIFT.png) |
| G01_004_ref03 → G01_004_growth_r07 | 24343 / 58623 | 25.904–59.892 | [查看](figures/panel2_sift/G01_004_ref03__004_07_Panel2_plus_SIFT.png) |
| G06_004_ref04 → G06_004_growth_r01 | 9282 / 41928 | 28.180–50.475 | [查看](figures/panel2_sift/G06_004_ref04__key01_raw00229_Panel2_plus_SIFT.png) |
| G08_005_ref04 → G08_005_growth_r03 | 19631 / 74212 | 30.123–60.613 | [查看](figures/panel2_sift/G08_005_ref04__key03_raw00531_Panel2_plus_SIFT.png) |

复现命令：

```bash
cd /home/liu/ring_first_3d_pose_depth
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/reuse_panel2_sift.py
```

该命令仅在本任务目录写派生图片、显示投影缓存和审计记录，原脚本/数据只读。所需旧source_layers/background资产不复制到GitHub。

| 审计项目 | 本次汇报 |
| --- | --- |
| 目标组数 | 3物理组，4个固定显示帧对 |
| 本算法独立成功 | 4/4可视化完成；不产生新的物理测量或科学资格认证 |
| 本算法失败 | 0显示失败；无GT绝对精度仍NOT_EVALUABLE |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | 上轮RGB反例、资格不足和误差耦合结论完整保留，未重新筛选 |
| 最终统计样本 | 4个显示案例，测量0/3，绝对MedARE/MAE/p95/max为NaN |
| 是否使用GT选择算法 | 否；仅对既定预测与相机重绘，无训练/融合/优化 |
