# 021 方法与实现忠实性

| 原定设计 | 实际代码 | 差异与限制 |
| --- | --- | --- |
| 实际跨视频身份 | prepare021.initialize / identity021.main | 02018同名轨迹全部回到真实原feature ID、描述子与RGB-RANSAC链接；不以3D近邻或0.75mm诊断删点；553观察全为背景，非Polyp特征 |
| 共同未知X | ba021.CommonPoints | 18×3个XYZ，004/005同名全部合法FIT观测共用；B1固定X0，B2/B3真实Adam更新X |
| 联合三角化初值 | prepare021.initialize | 全部相机DLT+SciPy least_squares点优化；初值用加权分量Huber，主优化用向量Huber，二者不冒称数学相同。单位像素协方差仅代理，正深度/视差/条件数/CAD关系保留 |
| 一个共享SE3 | ba021.BA.transform | exp(delta)左乘完整RoMa，004世界坐标、mm、scale1；不释放独立相机/尺寸。官方P3D se3_exp_map保留FP64，移除旧float32往返；实际FD校验通过 |
| 轨迹/视频/方向归一 | prepare021.initialize / weight_audit021 | 每条轨迹两视频各半；视频内按019方向块均分，再轨迹均分。004实际69条、005实际484条观测总目标质量各0.5；每条轨迹内部按其实际观察方向均分，跨轨迹汇总方向权重不必严格相等，实际表见ACTUAL_VIDEO_DIRECTION_WEIGHT_AUDIT。支持类别均分，但本数据全背景，无法凭空提供Polyp证据 |
| Ring实体/可见语义 | ring020.CADCurves / ba021.Ring021 | 真实CAD occluding edges+自遮挡、独立I/O、原Mask像素回溯；不是三平面圆。R10训练参数与020相同；四组诊断半径从各自固定CAD取得；代码可参数化R5/R10，本轮没有新增R5实测病例 |
| I/O带容差 | ba021.Ring021.term | L=M+.05(Ieps+Oeps)，eps由FIT源边界不确定性q95+.5px且至少1px；实际得1px。距离超过epsilon后sigma3px向量Huber；未观察弧不补，Mid只在独立评价记录 |
| 联合目标 | ba021.BA.evaluate | .2重投影+Ring+.01 posePrior+.001 whitenedPointPrior；点先验σ裁剪.05..3mm。对B1同一表达点先验为0，B2仅释放X，B3仅增加I/O。没有2D–2D EPI损失（只诊断），不把与020的差异说成仅BA一个变量 |
| 成熟求解/稀疏结构 | PyTorch Adam+020回溯；identifiability021 | 使用稀疏观察索引/点局部Jacobian，但未采用专用Schur/SLAM求解器；Schur消元仅后验诊断。单点初值用SciPy，官方P3D用于Ring，不新写通用BA框架 |
| 有界参数更新 | ba021.run | q lr.01、X lr.02mm；100候选、8级回溯、拒绝恢复参数及Adam；T≤1.2mm/10°，X≤3mm/白化6，正深度。全部参数固定，无HOLDOUT/HERO调权 |
| 不可辨识性 | identifiability021.main | 实际18点/9负对照点的局部块信息，Huber IRLS后消元；均为固定相机条件代理，不将先验提升的秩冒充观测信息 |
| 光栅像素中心核对 | raster_pixel_audit021 | 实际FIT CAD的964个顶点通过官方P3D screen接口核对；screen减0.5后与OpenCV半分辨率像素中心公式一致，最大分量差2.87e−5px。继承的Ksmall主点+0.25是光栅中心补偿，不将其误删为相机修正 |
| 独立评价 | eval021 / per_view021 / copied evaluate020 | 所有021 pose冻结后G01保护视角、未参与轨迹、body/HERO；9个候选全部55目标视角、全部68逐视角SIFT，失败N0保持；无GT |
| 四组并行 | group_audit021 / source_geometry021 | 非G01只读018冻结预测独立完成，不反馈G01 BA；G01等待021所有pose冻结。全部043+8来源保留，区分同视频和跨视频 |
| 真实几何与统计 | geometry021 / body_error021 / group_reports021 | 实际原生Pixel ID/Raw Face ID、轴向Z、三角面面积、固定分母、共同/新增/丢失；CAD与自遮挡，Front/Behind/Unknown分离；没有ICP/补洞/清面 |
| 首层共视与反向实体包含 | covisible021 / reverse_ring021 | 源自身CAD次序检查，首层候选剔除可能合法自遮挡后方；与020历史分母并列。实际CAD顶点/面心到闭合主体检查补充FCL；不伪称严格无穿透证书 |
| 几何检查 | geometry021.body_quality | 复用01864阶面内CAD检查，沿用001mm阈值，符号查询统一11射线；独立FCL、Open3D非邻接自交、拓扑和面片质量。底盖灰色推断身份，不作为可见表面监督 |
| 可视化 | visualize021 / body_error021 | 复用018 Open3D实际三角面射线着色，不用点云/解析体替代HERO或主体；GLB源独立node，所有原面保留，只紧凑化无引用顶点；mm→m为固定单位换算 |

Ring-First历史链只读核对：multigroup run_geometry→V6 local_ring_sfm initialize/triangulate_training/BA、ring_pose_contact decode/solve及v6实体轮廓；当前014背景SIFT/PnP扩展与018原生K/相机回执一致。输入完整性核对可读取原图/原生数组做哈希、像素绑定和坐标自检，但不评价021候选或反馈BA；G01的HOLDOUT几何指标、body/HERO一致性评价严格在全部位姿冻结后。轨迹连线复用018/019已验证raw-index绑定，不把历史声明帧号当新认证。ADDITIONAL_CAMERA_SOURCE_AUDIT记录文件SHA，未重估原始轨迹；不将整个历史初始化链描述为无深度。

官方接口参考：[PyTorch3D SE3](https://github.com/facebookresearch/pytorch3d/blob/main/pytorch3d/transforms/se3.py)、[SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)、[Open3D RaycastingScene](https://www.open3d.org/docs/release/python_api/open3d.t.geometry.RaycastingScene.html)。实际安装版本与源码位置见[环境与源码回执](provenance/ENVIRONMENT_AND_CODE.json)，不要求下载新包。

源码运行中唯一训练侧修补是中断恢复时不覆盖INITIAL/首次freeze；原训练源码另存ba_source_before_resume_preservation_fix，目标/输入/预算未改变。初次开发读取旧特征缓存把des写成desc，已在正式冻结前修正，并逐项验证全部原描述子；无数据重建替代。
