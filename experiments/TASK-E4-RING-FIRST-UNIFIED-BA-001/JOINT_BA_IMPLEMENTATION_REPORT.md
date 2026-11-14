# 联合BA实现逐项对照

| 原定组件 | 实际实现 | 位置 |
| --- | --- | --- |
| 原始物理Torus | 原函数逐点复现的Torch64表观轮廓 | code/torus.py::torus_uv_t/curves |
| 可见实际I/O | V5 Polyp邻接UNKNOWN+已冻结真实Mask支持点 | code/visible_arcs.py::qualified |
| SE3公制更新 | H Exp(local) RF，SO3始终成立，无尺度 | code/torus.py::pose_t |
| 共同XYZ | 同一真实RGB身份一个3D变量，18跨视频link合并 | code/prepare.py；config/TRACKS.json |
| 鲁棒Ring/RGB | vectorHuber/3px，按曲线/视角或轨迹内video方向归一 | code/ceres_backend.py；code/joint_ba.py |
| 成熟LM/Schur | 实际pyceres.solve；每组一个多相机多点Problem | code/ceres_backend.py::solver；Joint.build |
| 先验/规范 | 固定004参考，首005局部固定；弱q、XYZ与相邻q差先验 | Joint.build |
| 逐帧完整6D | L2仅5D局部图表，B4完整释放被独立门禁暂停 | STAGE_DECISION.json |
| 条件可辨识性 | 数据J消去XYZ，排除所有先验；图连接与FD | code/joint_information.py |
| 外层可见性/接受 | 重算对应+真实全目标+物理域+回缩 | Joint.run/physical |

B3实际目标为Ring1、RGB0.2、pose0.01、XYZ0.001。Ring每曲线/每视频/方向归一；RGB每轨迹内video/方向归一，非全局等视频。相邻q差是固定Ring坐标中的一阶轨迹先验，不是精确相邻SE3测地距离；XYZ先验是1mm等方弱正则，不是GT协方差。没有重复加第二份RGB损失。

B2只用实际跨视频共同轨迹约束H，内部同视频轨迹保持固定；B3加入同视频轨迹、共同XYZ和局部5D。故B2/B3是预定层级比较，不能把全部差异仅归于“释放XYZ”单因素。B1是固定XYZ独立局部对照，所有路线的差异公开。

元数据命名纠正：通用serialize曾给B1_LOCAL/B2也写入FROZEN_NUMERIC_JOINT字符串，名称不准确；它只是通用数值状态，不能据此称联合BA。原始FINAL和SHA保持不变，NUMERIC_STATUS_SCOPE_CORRECTION及ACTUAL_PROBLEM_SCOPE_AUDIT按真实Ceres活动块明确纠正：B1单相机、B2共享H固定XYZ、只有B3为多相机和XYZ联合。顶层B1始终标INDEPENDENT_LOCAL_NOT_JOINT_BA。

完整函数行号及SHA见CODE_LOCATIONS.csv，避免只按方法名宣称实际忠实。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；98 canonical视角=81FIT+17HOLDOUT。G01含004/005；其他三组只有004 |
| 本算法独立成功 | B1实际76个独立局部求解，另5个参考相机受保护；B2仅G01一个共享SE(3)求解；B3四个真实联合问题，76个五维局部相机块+一个六维H+1377个XYZ，数值输出不是绝对精度认证 |
| 本算法失败 | 无用旧位姿填充的失败预测；B4四组NOT_RUN，照片12/12 NOT_RUN；初次PyCeres冷调用崩溃保留，显式Jacobian预求值后实际组级运行完成；独立RGB科学可信性尚未建立（不是当前严重数值阈值FAIL） |
| 历史测量值回退 | 0；B0/参考相机/HOLDOUT是预登记对照或规范，不冒充新恢复结果。B2不适用的三组保持NaN/N/A，不复制B0 |
| 失败组及具体原因 | G01初版005地图评价坐标错误已纠正；当前未超过冻结严重退化阈值，但四组独立RGB仍有权衡；B3四组留出极线代理均增大；G01/G06旧深度相容性下降。见FAILURE_LEDGER、逐视角/逐来源CSV和Figure4–8 |
| 最终统计样本 | 全部4组完整保留；按每指标真实视角、轨迹或source-target像素分母统计；不把重复源观测当独立物理样本。真实GT测量MAE/MedARE/尺寸p95为NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；协议/输入/源码在运行前冻结，候选在HERO之前冻结；HOLDOUT不进目标，不按HERO选路线，保留预登记主初值而非较低损失的敏感性候选 |
