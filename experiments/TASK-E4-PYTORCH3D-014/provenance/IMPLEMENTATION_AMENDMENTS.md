# 实施修复记录

1. 新增原帧Ring轮廓触边暴露已有ring_sides.py空ROI负维数组错误：仅夹紧数组索引，空截面保留Unknown，未收紧遮挡。
2. 第一次C0/G01训练已完整结束，后处理重复字典键造成score014异常；修复指标字典写入并复用已有FINAL，没有重训或改评价公式。
3. 完整32阶CAD查询在C0/G06出现资源瓶颈。基于精确已知CAD环面的Lipschitz外界剔除保证在材料外的点；所有可能穿透点仍查询同一实际CAD、同32阶采样及1e-5mm阈值。G06初始逐面负距离与完整查询最大差0；3.65s→0.16s。正间隙为保守下界，最终独立64阶全查询报告实际值。原6例未使用加速，负距离判定数学相同。旧C0源文件按原预冻结SHA精确恢复在source_versions，供复现。
4. 主动中断自己的慢G06子进程，保留原JSON/日志和optimizer checkpoint，从精确检查点恢复参数、Adam及CPU/CUDA/NumPy状态。回退到最近已保存接受点，不冒称零浪费或位级复现。资源中断不视为科学失败；原始故障记录保留。
5. E阶段的细分密度先验实现只在存在SHAPE_REFERENCE.npz时启用，C/D数学不变；逐病例保存实际执行源码快照。BMesh float32插值用原三角面双精度重表达，原顶点不变；不平滑、不生成目标形状。


2026-11-08 21:49 local: post-freeze native evaluation scheduled with3 CPU workers across independent physical groups, serial models within each group, ordered aggregation. No score, camera, Mask, ray, or geometric formula changes. Every existing common-FIT serial score will be compared with native post-evaluation at1e-10 tolerance; failures stop evaluation, not trigger retraining. GPU remains strictly serial. No GT accessed for this engineering adaptation.


2026-11-09 post-freeze, before GT: G02 read-only split-gradient sum failed original1e-4 relative threshold (0.00016808; absolute3.0075e-7); all components finite. Same-state FULL-vs-FULL repeat control is worse:0.00038989relative /6.9764e-7absolute, lossdifference−3.1849e-8. Specific kernel not localized; numerical/nondeterministic execution floor demonstrated. Original diagnostic criterion remains unchanged and FAIL is retained; --record-only saves failures and continues independent geometric evaluation without promoting them toPASS. No optimizer, weight, prediction, camera, data or metric formula changed. Original console traceback retained under runtime/EVALUATION_GRADIENT_INITIAL_FAILURE.log. All44 outcomes will be reported in GRADIENT_ADDITIVITY_CHECKS.
