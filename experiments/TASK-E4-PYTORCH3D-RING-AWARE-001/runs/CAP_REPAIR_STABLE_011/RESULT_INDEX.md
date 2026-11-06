# 结果索引

核心图：

- [Figure 1 九例B→C截断继承](figures/Fig1_Nine_B_to_C_Initialization.png)
- [Figure 2 G05/G09冠面修复：同视角补充版](figures/Fig2b_G05_G09_Same_View_Cap_Repair.png)
- [Figure 3 九例优化前后](figures/Fig3_Nine_Optimization_Before_After.png)
- [Figure 4 低到高自由度过程](figures/Fig4_Low_to_High_Update_Process.png)
- [Figure 5 真实提案与几何保护](figures/Fig5_Geometry_Protection_and_Failures.png)

G05/G09分别完整的截断过程：

- [G05](figures/full/G05_Cap_Repair.png)
- [G09](figures/full/G09_Cap_Repair.png)

[预优化冻结原Fig2](figures/Fig2_G05_G09_Cap_Repair.png)保留原字节：其前两列为侧视、后两列为斜视，不能跨列直接比较投影形状。上面的Fig2b按相同侧视/斜视分别成行，所有模型在每行共用相机与毫米范围；仅修正展示，不改变任何模型或平面。

九例优化详细图：

- [G01](figures/full/G01_Optimization_Detail.png) · [G02](figures/full/G02_Optimization_Detail.png) · [G03](figures/full/G03_Optimization_Detail.png)
- [G07](figures/full/G07_Optimization_Detail.png) · [G04](figures/full/G04_Optimization_Detail.png) · [G05](figures/full/G05_Optimization_Detail.png)
- [G06](figures/full/G06_Optimization_Detail.png) · [G08](figures/full/G08_Optimization_Detail.png) · [G09](figures/full/G09_Optimization_Detail.png)

本地绝对根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011`

每例C初始化：`inputs/Gxx/INITIAL.npz`、`C_INITIAL_MODEL.json`、`BASE_SELECTION.json`、`CHART_BASIS.npz`和`CHART.json`。仅两例需要新C拟合，全部C0/C1/C2候选及B蓝区原顶点ID、软参考、足迹交点保存在`init_results`，未触发的级别不伪造。

每例正式结果：`local_results/Gxx/STEP_*.npz/.pt/*_mm.ply`和`FINAL`。FINAL是固定预算结束的最后接受状态，不是最佳checkpoint。`REJECTED_FIRST_GLOBAL/LOW/DETAIL.npz`为实际首个拒绝提案（有该类才生成），包含before_V、候选参数与原因。完整候选参数及每次回缩在metrics/Gxx_CANDIDATES.json/CSV，简版CANDIDATE_REVIEW只省参数以便仓库审阅，不修改失败记录。

主要数据表：C_INHERITANCE、INITIAL_COMPARISON、NINE_CASE_RESULTS、ALL_STAGE_WITH_BLENDER、PER_VIEW_METRICS、FAILURES、ADAM_CLOCK_REPLAY。完整参数、接受次数、动量回滚、低频/细节是否真正释放均可查验。

工程V1原失败现场、源码与日志保存在engineering_validation_v1，原有向基底和所有真实输入仍可按SHA对应。Git提交代码/配置/指标和五张核心图；原始数据、全部网格/checkpoint及九例详细图保留本地，路径与SHA见LOCAL_RESULTS_INDEX。未上传不等于删除。
