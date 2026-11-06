# 交付索引

四张核心图：

- [九例总览](figures/Fig1_Nine_Case_Overview.png)
- [G05/G09精确裁切](figures/Fig2_G05_G09_Exact_Clipping.png)
- [Ip/Is/IIa固定阶段变化](figures/Fig3_Representative_Progression.png)
- [实际轮廓、深度与执行位移](figures/Fig4_Observation_Update_Mechanism.png)

九例详细图：

- [G01](figures/full/G01_Detailed.png) · [G02](figures/full/G02_Detailed.png) · [G03](figures/full/G03_Detailed.png)
- [G07](figures/full/G07_Detailed.png) · [G04](figures/full/G04_Detailed.png) · [G05](figures/full/G05_Detailed.png)
- [G06](figures/full/G06_Detailed.png) · [G08](figures/full/G08_Detailed.png) · [G09](figures/full/G09_Detailed.png)

完整本地根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010`

每例Detailed包含近原始参考方向、世界侧视和斜视P0/S0/P终态/S终态，原图Mask叠加、基底、Ring与UNSAFE候选；STOP终态仅是最后安全诊断，不是FINAL300输出。每个病例所有几何图使用包括不安全候选在内的共同边界，毫米坐标，黑色CAD与灰色推断底盖。

本机各组所有18正式尝试均保存：

- `local_results/Gxx/{P,S}/STEP_0000`及实际到达的预定checkpoint（.npz/.pt/_mm.ply）。
- `FINAL`仅完成300者；中断者`UNSAFE_CANDIDATE`与`LAST_SAFE`均保留。
- `MECHANISM_0001/0050/0100/0150/0200/0300.npz`在实际安全到达时保存，含真实before/after顶点、损失梯度和动量；未到达的轮次不伪造。
- `metrics/Gxx_{P,S}_TRAINING.csv`、DEPTH_TRACE.csv、RUN.json；runtime/中原始stdout日志。
- `inputs/Gxx/`精确初值与来源参数、BASE_SIGN_REPAIRED_45PX、BASE_SELECTION、背景与接触原始证据。

权威指标：ALL_STAGE_WITH_BLENDER、PER_VIEW_METRICS、FINAL_300_FIXED_DENOMINATOR、PAIRED_FINAL_COMPARISON、FAILURE_DIAGNOSIS、FAILED_PROPOSAL_GRADIENT_REPLAY、FIRST_SAVED_SELF_INTERSECTION与DOF_AND_SCALE_AUDIT。所有原始9组/18条件分母均保留，失败无历史测量回填。

Git只提交四张核心图、小型配置/审计/指标与代码，完整九例图和全部网格/状态保留本机；路径/大小/SHA见assets_index/LOCAL_RESULTS_INDEX.json。灰色底盖只在F_solid中，用于闭合记账和实体检查，不是测得的组织表面。

说明：LAST_SAFE 仅指上一次通过数值/单步紧急检查的状态，仍可能穿环或自交，不是物理安全认证。TRAINING/DEPTH_TRACE记录接受步骤；首步即拒绝的G03-S/G08-S为零行表（保留表头），实际一次optimizer.step及拒绝原因在RUN/FAILURE_DIAGNOSIS中。
