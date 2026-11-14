# 成熟BA实际复用

实际环境：Python3.12.13、PyCeres2.6/Ceres2.2.0、PyCOLMAP4.2.1；PyCeres安装在本任务runtime/packages，未改共享旧环境。Ceres使用LM信赖域和DENSE_SCHUR；G01官方FullReport的自动消元顺序为888个点块、59个相机/共享块。不是普通PyCOLMAP BA自然支持Torus。

自定义Python代价包含解析Torus和真实SIFT，Torch64求导；Ceres负责原生求解。没有运行C++AutoDiffCostFunction或GradientChecker，采用外部独立FD检查同一残差。没有自编LM/Schur；joint_information的3×3点块消元只用于信息诊断，不参与更新。

实际参考：
- [Ceres官方BA教程](https://github.com/ceres-solver/ceres-solver/blob/2.2.0/examples/simple_bundle_adjuster.cc)
- [Ceres LM/Schur官方说明](https://ceres-solver.readthedocs.io/latest/nnls_solving.html)
- [PyCeres官方Python代价示例](https://github.com/cvg/pyceres/blob/v2.6/examples/test_python_cost.py)
- COLMAP官方bundle_adjustment源码已小量获取，准确commit和源码SHA见MATURE_SOURCE_READ_RECEIPT；仅参考数据结构/规范，不宣称调用了COLMAP默认BA。

**冷回调绑定故障**：PyCeres v2.6 cost_functions.h的cached_flag初始化分支，无条件读取jacobians[idx]，首次若只有残差求值则jacobians==nullptr，可原生崩溃。独立复现和gdb堆栈保留。先调用同一Problem.evaluate_jacobian建立非空缓存后，重复调用与四组全部实际运行完成。此接口处理不更改损失、变量、LM或Schur。原未修复backend快照和事故日志保留，不能把该崩溃归因于Torus数学。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；98 canonical视角=81FIT+17HOLDOUT。G01含004/005；其他三组只有004 |
| 本算法独立成功 | B1实际76个独立局部求解，另5个参考相机受保护；B2仅G01一个共享SE(3)求解；B3四个真实联合问题，76个五维局部相机块+一个六维H+1377个XYZ，数值输出不是绝对精度认证 |
| 本算法失败 | 无用旧位姿填充的失败预测；B4四组NOT_RUN，照片12/12 NOT_RUN；初次PyCeres冷调用崩溃保留，显式Jacobian预求值后实际组级运行完成；独立RGB科学可信性尚未建立（不是当前严重数值阈值FAIL） |
| 历史测量值回退 | 0；B0/参考相机/HOLDOUT是预登记对照或规范，不冒充新恢复结果。B2不适用的三组保持NaN/N/A，不复制B0 |
| 失败组及具体原因 | G01初版005地图评价坐标错误已纠正；当前未超过冻结严重退化阈值，但四组独立RGB仍有权衡；B3四组留出极线代理均增大；G01/G06旧深度相容性下降。见FAILURE_LEDGER、逐视角/逐来源CSV和Figure4–8 |
| 最终统计样本 | 全部4组完整保留；按每指标真实视角、轨迹或source-target像素分母统计；不把重复源观测当独立物理样本。真实GT测量MAE/MedARE/尺寸p95为NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；协议/输入/源码在运行前冻结，候选在HERO之前冻结；HOLDOUT不进目标，不按HERO选路线，保留预登记主初值而非较低损失的敏感性候选 |
