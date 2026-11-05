# E4局部更新定位候选 v0.7

状态：REPORTED / PARTIAL_RECOVERY_LOCALIZATION_GATE_FAILED。未升级正式主线，等待首场景人工审核。

继承 [v0.6](KEY_TECHNICAL_VERSION_E4_SDF_CANDIDATE_v0.6.md) 的共享SDF与历史失败记录。本轮审计当前data.py实际对应链路，并使用DXY误差传播的源CAD做单局部隆起恢复；用户已明确授权控制实验GT构造/独立评价，不改变真实病例的GT禁令。

发现历史IIa6.5_R10_obs02与其他观测Ring高度相差0.118444mm，不能直接作为静止多视角。已固定obs01几何、复用五个已知相机重新渲染，3拟合/2留出。主体和Ring投影IoU均≥0.99、相机点误差<0.001px后才优化。

实际工具为官方Kaolin原样torch-only marching_tetrahedra（ee8b7eca1e56b1b9fd1509fc406f8d8ccbc9240b）+Open3D+SciPy CPU后备，未安装/运行完整Kaolin或PyTorch3D，不宣称SoftSilhouetteRenderer门禁。一个紧支撑C4核的中心3维和幅值1维，无逐顶点自由形变或类型专用分支；GT不进入优化目标。

首场景IIa6.5_R10：4轮/265函数评价/89.633秒，拟合全可见Mask IoU 0.940959→0.962467、留出0.942972→0.961862。核中心偏差0.571852mm，未达冻结0.5mm门槛；统一GT/预测几何算子后的实际更新质心偏差0.593718mm亦失败，区域IoU0.621496，GT修改区几何位移MAE0.145866mm。初步混用材料位移/距离变化的0.473mm审计已封存，不作最终结论。同法线核验保留1865/1921共同有效及56未命中，不填补NaN。方向基本正确、远处误更新低、无检出Ring交叠，但不足以认证可靠三维定位。

当前局部四参数轮廓Jacobian满秩、条件数2.247，不能简单归因为局部不可辨识；固定核与GT修改存在已知表达差异，轮廓NN/像素离散与局部优化亦为原因候选。核平滑不能保证最终离散Mesh处处光滑。

三个形态资产均已核对；按照用户“先一场景诊断后暂停”，只执行IIa，Ip/Is为HUMAN_HOLD，本轮完成1/3形态，不冒称三类型验证。完成后不自动新增凹陷、改核宽度、对照或其他病例。

[技术报告](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/TECHNICAL_REPORT.md) · [失败记录](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/FAILURE_LEDGER.md) · [投影门禁](../experiments/E4-SDF-LOCALIZATION-BLENDER-001/metrics/PROJECTION_GATE.json)
