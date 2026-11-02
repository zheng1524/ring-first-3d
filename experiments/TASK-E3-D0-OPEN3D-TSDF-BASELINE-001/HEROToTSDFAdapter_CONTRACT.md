# HEROToTSDFAdapter v0.1 候选接口（NOT FROZEN）

输入：原生二维 depth_mm（相机轴向 Z，mm）；同尺寸 RGB uint8；同尺寸 Mask 0背景/1Polyp/2Ring；同尺寸 pinhole K；右手相机到世界 c2w_mm（仅平移 mm）；正的 depth_trunc_mm。各来源须有不可变来源身份、世界帧身份、SHA、RGB/Mask/深度分辨率和冻结相机来源。

输出：RGB-D depth_m float32；无效/Mask外/Ring/background严格0；metric w2c=inverse(c2w with translation×0.001)；原生K的Open3D intrinsic。RGB convert_rgb_to_intensity=False，depth_scale=1。官方融合器 voxel/sdf_trunc/depth_trunc 均同一米单位，Mesh只一次×1000返回mm。

前置转换：归档 RGB 用 INTER_AREA 到 native，类别 Mask 用 INTER_NEAREST。K调用已有半像素中心保持函数；不得把轴向 Z 当单位射线距离。没有新畸变估计、相机拟合、深度补齐、ROI剪裁、轮廓删面或权重。

来源载入器和 G01_004 的方向组织位于 common.py/freeze_inputs.py；适配器构造函数只接受上述数组，不按组名、GT或重建误差切换算法。其他物理组可复用同一 schema，但不宣称本轮已经验证其他组。

工程实测：输入代数、Mask、毫米量级和独立重放成立；严格单源命中与 mm/m 最大残差门槛尚未全通过。因此只发布可审阅候选接口，不签发正式冻结。失败与参数不得在未来组中静默放宽。
