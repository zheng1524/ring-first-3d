# 成熟算法复用与实际差异

- [Conics estimate_pose](https://github.com/sergiud/conics/blob/c38fffd10125c42772656e8c7f69724959154342/conics/_conic.py)：实际提取并执行未修改的官方函数，保留Apache2许可证、源码与SHA。由KᵀEK构造圆的锥面；使用实际CAD中心线半径约5.6mm，而非把Inner/Outer当成共面圆。保留多解/正深度/法向分支。实际使用官方返回的c/n，不直接把R/t当作OpenCV外参；负Z约定显式转为OpenCV正Z。圆内yaw由P0规范初始化，再对入域分支由真实SIFT约束。未实现全yaw族预消歧，是本轮限制。合成圆验证只用于审计分支存在正确解，不参与真实选择。
- [M3T RegionModel](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/region_model.cpp)、[RegionModality](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/region_modality.cpp)、[Optimizer](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/optimizer.cpp)、[SilhouetteRenderer](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/silhouette_renderer.cpp)：阅读并保留MIT源码，用其渲染轮廓、对应/位姿交替、局部重线性化思想；**没有运行官方C++跟踪器、没有复现其区域概率模型或直接移植GeneratePointData**。Python使用Open3D全CAD深度/primitive渲染、OpenCV轮廓和CAD前后面候选边。新增一圈vertex-face primitive邻接门槛是项目适配，现已证实过严，不应称官方M3T行为。
- OpenCV SIFT、互检/RANSAC PnP及原019三角化缓存复用。原地图建立时已用原相机、至少3FIT、视差>0.5°、重投影<2px；不读HERO。当前没有额外调用solvePnPRefineLM替换真实方案，优化实际由SciPy TRF完成；不冒称所有列出的组件都运行。没有下载网络或模型。
- SciPy有界least_squares(method=trf)实际执行；float64 SE3/Jacobian沿用已验证PyTorch实现；并非Ceres、g2o、COLMAP或完整M3T优化程序。

| 设计 | 实际代码 | 差异/限制 |
| --- | --- | --- |
| 共同c2w/mm/无尺度 | base_geometric.pose + refine.q_from_pose | 相机中心为旋转参考，等价明确的世界左SE3；CAD分支绕Ring法向规范消除虚假yaw，SIFT保留真实方向信息 |
| 相同目标公平比较 | refine.Problem | S0/A1只SIFT+prior；A2/A3额外完整CAD尺寸的I/O残差；P0不更新。P0先验中心一致，不在Conics终点重置 |
| 固定对应求导 | cad_render.material_points | 冻结透视正确的最近CAD三维点，内循环不再对clamp分支求导；每个候选重新渲染/关联实际目标并回溯验收 |
| M3T式可见性 | cad_render.RenderedCAD.segments | 2倍分辨率渲染边界、1工作像素关联带、可见primitive邻接证据；MISS不直接visible，2µm深度阈值未增加。该邻接适配产生大缺口，是本轮失败机制 |
| 成熟优化 | refine.solve | 5轮对应更新×最多20nfev，8次回溯。外包q盒2，相对P0真实中心≤1.2mm/角度≤10°仍严格执行；不是事后提高危险位移限值 |
| Conics候选选择 | run_videos.run | 全部分支保留，只以FIT SIFT+同P0先验选可行候选；超界则NaN，不用P0/S0补齐。不以HOLDOUT或HERO决定候选 |
| 真实输入来源 | setup_inputs + frozen upstream | 原98canonical与RGB/Mask/特征/轨迹只读复用；不新选帧，不按Ip/Is/IIa改参数 |
| 独立评价 | evaluate_videos + enrich_metrics + facts | 全硬CAD图像投影、SIFT未拟合轨迹/极线、原HERO反事实、精确分母、共同成功集合；不做ICP或GT评价 |

目标：L_R=.5 meanHuber(dI/3)+.5 meanHuber(dO/3)；L_F=.2 meanHuber(norm(reprojection)/3)；L_P=.01 sum(q²)/12。Mid无损失项。相同方法的初始化对照只改变初值，预算/自由度/数据/先验均相同。

完整函数行号、源码SHA见CODE_LOCATIONS.csv。Stage2之前协议/源码回执保留，四组预测冻结后才读取独立指标。缺陷发现后的控制只有只读几何计算，未执行第六条路线或覆盖任何最终矩阵。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个物理组×4条新方法；81FIT×4=324条目标相机路线（不是324个独立物理样本），另17HOLDOUT只作冻结保护 |
| 本算法独立成功 | S0 81/81，A1 46/81，A2 81/81，A3 46/81：合计254/324独立数值位姿；不等于真实位姿正确或主线验收通过 |
| 本算法失败 | A1/A3各35例初始化不满足冻结界限，合计70/324条失败NaN；逐帧见FAILED_CAMERA_ROUTES。CAD轮廓完整性FAIL，12照片统一NOT_RUN_VIDEO_COMPLETENESS_GATE |
| 历史测量值回退 | 0；P0为用户要求的对照/先验，HOLDOUT按协议保留原相机，两者不冒充新拟合结果；Conics失败未用S0/P0补齐 |
| 失败组及具体原因 | G01 Conics32/60，G03 1/6，G05 2/8，G06 0/7失败；四组primitive邻接过滤均导致渲染曲线缺口，见初始化JSON、Figure4与失败台账 |
| 最终统计样本 | 全部4组、98canonical视角；254数值结果/324目标，70缺失完整保留。成对比较只用同一成功视角，并报告共同N；17HOLDOUT相机均未独立拟合 |
| 是否使用GT选择算法 | 否；已知CAD/合成相机仅作几何自检，不读真实息肉GT。无HERO/body位姿损失、无HOLDOUT调权/选初始化，照片A2在评价前已登记 |
