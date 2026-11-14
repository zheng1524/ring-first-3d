# 原始Ring-First复用审计

已读取并保存SHA快照：geometry.py::torus_contours、V5 g5_common/ring_observations、recover/torus_geometry、V6 local_ring_sfm、V8 registration、V9 local_pose_refinement、V13 rigid13及021。实际版本见ORIGINAL_SOURCE_READ_RECEIPT，不凭报告重写物理模型。

原方程 n(X)·(C−X)=0 给出厚Torus的两条透视表观轮廓，非共面圆。Torch仅将同方程改为64位可微接口，98视角与原函数逐点对照；不是021的网格候选边筛选。四组冻结CAD均核验为内径10mm的同一R10参数。

V5的Polyp邻接5×5 UNKNOWN规则用于实际I/O观测；既有DXY点需真实Mask支持，不使用完整椭圆/Mid补弧。保持原生像素中心坐标与K。原始源码存在+.5边界坐标的接口，当前继承021已核验的整数像素中心+K319.5/179.5，投影函数前向和独立CAD光栅逐项核对，未静默换K。

V8/V9的法向翻转、全局axial yaw分支逻辑已读；本轮从冻结RF分支出发，不重新进行72yaw全搜索，不声称所有分支已经被联合枚举。局部SE3修正和共享H保留SO(3)，Ring实体不变、尺度不开放。原资产全部只读。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；98 canonical视角=81FIT+17HOLDOUT。G01含004/005；其他三组只有004 |
| 本算法独立成功 | B1实际76个独立局部求解，另5个参考相机受保护；B2仅G01一个共享SE(3)求解；B3四个真实联合问题，76个五维局部相机块+一个六维H+1377个XYZ，数值输出不是绝对精度认证 |
| 本算法失败 | 无用旧位姿填充的失败预测；B4四组NOT_RUN，照片12/12 NOT_RUN；初次PyCeres冷调用崩溃保留，显式Jacobian预求值后实际组级运行完成；独立RGB科学可信性尚未建立（不是当前严重数值阈值FAIL） |
| 历史测量值回退 | 0；B0/参考相机/HOLDOUT是预登记对照或规范，不冒充新恢复结果。B2不适用的三组保持NaN/N/A，不复制B0 |
| 失败组及具体原因 | G01初版005地图评价坐标错误已纠正；当前未超过冻结严重退化阈值，但四组独立RGB仍有权衡；B3四组留出极线代理均增大；G01/G06旧深度相容性下降。见FAILURE_LEDGER、逐视角/逐来源CSV和Figure4–8 |
| 最终统计样本 | 全部4组完整保留；按每指标真实视角、轨迹或source-target像素分母统计；不把重复源观测当独立物理样本。真实GT测量MAE/MedARE/尺寸p95为NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；协议/输入/源码在运行前冻结，候选在HERO之前冻结；HOLDOUT不进目标，不按HERO选路线，保留预登记主初值而非较低损失的敏感性候选 |
