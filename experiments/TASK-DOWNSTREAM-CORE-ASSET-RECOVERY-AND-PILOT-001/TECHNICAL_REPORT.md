# TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001

2026-11-26，Asia/Shanghai。独立分支 `exp/TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001`；基础提交 `000f5f2998ad2a29ca454e8380b587b26ba9f21c`，即用户指定审计提交。工作树 `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-DOWNSTREAM-001`。主工作区初始 HEAD 为 `8e59081600db2739ab183325bbe5354c4d1d2b4c`；未切换、提交或清理它。

**恢复了从明确历史起点调用真实主体更新器的小闭环；没有恢复从原始观测重新生成最早初体的完整链。最重要的纠正：G01 的 EXACT013 INITIAL 实际就是 011 FINAL，已经经过优化。** 本轮选原 002 Graph + SmoothARAP + 显式轮廓/投影/碰撞门控组合；没有用 E1/E2 重写替代。另完成 018 原生深度梯度回归和单视频已知 SE3 控制。真实双视频配准仍 NOT_EVALUABLE，前半段路线未选定。

入口：[核心资产表](CORE_ASSETS.csv)（31项，逐文件提交、SHA、输入、依赖、状态、保留路径）；[执行计划/组合表](EXECUTION_PLAN.md)；[保留依赖清单](evidence/RETAIN_DEPENDENCIES.json)；[主体原图投影](evidence/PILOT_PROJECTIONS.png)；[同尺度主体](evidence/PILOT_SURFACES.png)；[刚体控制原图投影](evidence/RIGID_PROJECTIONS.png)；[同尺度曲面](evidence/RIGID_SURFACES.png)。

## 1. 初始化真正是什么

核对原提交 `db14df2627ab903925d18eb4f7c26bf85c3844d0` 的源码、011结果索引、012复制代码、013保留记录和当前 NPZ，得到以下链；**源码链找到不等于输入齐全或已重新生成**。

|阶段|真实方法与入口|与下一阶段的关系/当前状态|
|---|---|---|
|A1 早期椭圆/完整 Mask 对照|`TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/fitting.py::Problem`、`run.py::main`；同一9参数模型，E1消费二维椭圆，E2消费完整Polyp Mask，同时使用原相对深度、Ring未知域、冻结相机与先验；SciPy TRF、多起点，A-only objective选择|`PRIMARY_A_ONLY.json` → PMGR `p0()`；这是历史祖先，不是本轮后来重写的 E1/E2。A1-COARSE的decode是更早参数化组件，单有decode不能算生成链闭合|
|PMGR / R1 P0|R1 `inputs.py::p0` 读取上述选定参数，`run.py::conservative_p0` 加碰撞/体积约束作保守初值；不是只取单位球|Ring-aware `code/prepare.py` 明确复制 R1 `local_results/G01_004/P0.npz`；D2继承已有real输入。部分其他组走 PMGR E2 basis，不应混为G01路径|
|009低维主体生成|`BODY_BASE_INIT_009/code/lock_and_prepare.py`：G01读取D2 frozen P0和观测；`fit_body.py::main/Problem`：由P0 PCA建立9参数椭球，3起点，轮廓20/TRF深度30预算，必要时有界star，FIT诊断选B；按基底证据选C|包含完整Mask、绝对/相对HERO深度、CAD代理和参数先验；不是纯2D椭球。基底来自独立证据，不能用Ring平面代替|
|011真正原初体C|`CAP_REPAIR_STABLE_011/code/prepare_caps.py`、`parametric.py::body`：继承009有向基底/B蓝色部分；需要时cap 6/7/9参数重拟合，否则精确复用C|G01 `C_INHERITANCE.csv` 为 SMALL/WEAK、`EXACT_FROZEN_C_REUSED`、ellipsoid9；011 **inputs/INITIAL** SHA `e6a75df77147a6bedaa30bf29e36c3ed6e5f1c1dd44449d890967a09dc860c47`，不是本轮起点|
|011主体优化|`CAP_REPAIR_STABLE_011/code/train.py`、`chart.py`、`stable.py`：继承C起点进行原低维/谱形变优化，保存FINAL|G01 FINAL记录 `step=300, accepted=18, stage=LOW, active_modes=16`；SHA `3045a7546d1eaf2bfd8fcd05cfd0c83cadfcd92bd684ecc6efbd8c286fad8c9f`|
|012→013起点|012 `prepare_replay.py:13` 明确将011 inputs/INITIAL另存C_011，并将 **011 local_results/FINAL复制为012 inputs/INITIAL**；013 `HISTORY_012_PROTECTION.json`记录相同SHA|当前013 INITIAL与011 FINAL逐字节相同；013 A3+O3N是真自由顶点更新，013 FINAL又是不同主体。不能将013 INITIAL称最早生成初体|
|015 / 后续Init-A|015 `prepare.py`保留014输入、读取011参数模型为PARAMETRIC_START；`initialize.py` Init-B变换当前mesh，Init-C重拟合原参数族；`train_mesh.py`真实训练。后续 `inita/train.py`明确复制EXACT013 static INITIAL并调用015训练|当前G01 015 `initializations/Init-A.npz`同SHA3045…；015 Init-A训练FINAL为另一SHA `b31e6e518c694103c94b2a920a5d7b59dafbf8ccd7900703f8c25e32cb5d8d09`，不能用它冒充重新初始化|

[20份原源码保护记录](evidence/INITIALIZATION_SOURCE_PROTECTION.json)放在既有 `src/ring_first_3d/mainline/lineage` 路径，已有相同字节源码直接复用。没有复制整套实验。[预期缺失资产](evidence/INITIALIZATION_EXPECTED_ASSETS.json)保留原路径、字节数和历史SHA；工程验证版011 FINAL（f676…）与主版不同，**未标为精确恢复**。

已查当前 retained_sources、旧sdf/a1目录、旧仓库文件、Git树和[31个ZIP的成员目录](evidence/INITIALIZATION_ARCHIVE_SEARCH.json)。未找到G01 009 `C_SELECTED.json`、011 `C_INITIAL_MODEL.json`、009原始P0及完整基底/深度输入闭包；不声称全磁盘/所有离线介质绝对不存在。**缺的是009观测/参数/基底输入闭包及011生成与更新可重跑接线，而非再写一个EXACT013加载器。** 当前只恢复了这些阶段的真实方法和可追溯源，未执行009/011生成。

## 2. 哪个更新组合值得继续复用

选 `TASK-E4-STRUCTURED-BODY-UPDATE-002` 的 `238c2da1cd842c0eba710a4ec44db5f437bff8e4` 原组合。审计另记历史execution commit `cadde3e9efc64e0925933d0a663150db9031caee`；本轮不是重新执行该旧提交整套任务。

- 32节点、4节点混合的内蕴Deformation Graph，SO(3)旋转/平移；没有自由顶点变量。SmoothARAP λ=.7，spokes/rims、质量与拉普拉斯项、detach SVD局部旋转，Graph受限autograd全局步，不冒称论文原无约束线性解。
- 显式双向轮廓、Face/bary可见性、exact mutual/法向/切向/未知域过滤；每候选全FIT重渲染，检查区域和目标损失、单视图保护、对应覆盖、step/total trust、几何与双向Ring碰撞。原历史碰撞门控仍是离散采样，不能认证连续三角面完全无穿透。
- 真Adam提案、8级回溯、拒绝时参数与optimizer状态回滚。保留原配置、所有FIT、视频/方向块均衡权重；唯一预算变化36→3，inner_steps=3。修复原硬编码循环读取既有iterations字段，并让短程末步保存完整可见性及正确checkpoint名称；默认36行为保留。没有改变loss/阈值/学习率/数据筛选。
- 历史002 G01有局部改善，但P95变差，G03无可靠改善、G05停滞，002阶段没有Sweep获准。后续 `bac3fc89ef95db522b63cf6bb98e6914b9382864` 的embedded Sweep/Boolean是另一环；G01局部接受，G03 PER_VIEW_PROTECTION拒绝与正式柄长NaN保留，不追记成002成功。

013/015自由顶点多视角结果和Init-A包装保留作对照，未按“最新目录”替换原组合。013历史11组并非全成功；审计指出密集Ring检查不满足全面非穿透。Init-A历史目标11组、10组共同数值、严格体积IoU仅3组；这些均非本轮新增验证。

## 3. 实际小闭环：历史起点→新更新→投影评价

使用一个物理组G01、23个冻结缓存（FIT16/HOLDOUT7，两个历史视频）；选择理由是输入完整、002历史结果与STEP024可核验。相机本身为历史条件性资产；HOLDOUT仅相对主体更新留出，不能称上游完全独立测试。

**本次初始化标签：HISTORICAL_011_FINAL_AS_013_INITIAL_NOT_PRISTINE_INITIAL。** Graph旋转/平移从零新建，Adam新建；没有加载002 STEP024、013 FINAL或015 FINAL。本次未读取HERO或GT进入优化。

|运行|真实执行|结果|
|---|---|---|
|PILOT_001|从同一历史起点，3外层/9 Adam，3次接受|最终保存 `visible_face` KeyError；保留日志、STEP记录与已写FINAL，不作为完整通过运行|
|PILOT_002|修复末步完整图保存后，从同一起点重新开始；3外层/9 Adam，3/3接受，0回溯拒绝|FINAL冻结；平均/最大位移0.061114/0.216679 mm；完整UPDATES、最终参数/网格与收据|
|历史G01/G03 STEP024|原Graph参数回放，**optimizer_steps=0**|最大顶点差8.88e-16/1.78e-15 mm；是资产回归，非训练|

因此本轮共执行18次Adam（包含失败运行），正式报告仅使用完整PILOT_002的固定最后结果。[收据](runs/PILOT_002/RUN_RECEIPT.json)、[逐步记录](runs/PILOT_002/UPDATES.json)、[失败日志](logs/pilot_001.log)、[历史回放](evidence/HISTORICAL_REPLAY.json)。FINAL SHA `f162f1e504db8af12c96a14eed56f45887e37be5267f6f04e555eda1483df291`。

|固定共同分母|INITIAL IoU|PILOT IoU|INITIAL边界MAE px|PILOT边界MAE px|
|---|---:|---:|---:|---:|
|FIT 16视图|0.876987|0.888184|30.660196|29.390263|
|HOLDOUT 7视图|0.865257|0.874994|24.976339|24.291372|

[逐视图完整表](evidence/PILOT_PER_VIEW.csv)同时保留边界F-score和R+/R−等分母。这些是未加权视图均值，优化器的原均衡权重另在INPUT_CONTRACT/UPDATES；不混为同一聚合。只验证短程可执行和二维条件性变化，**不能据此宣称三维精度或完整覆盖改善**。本轮GT形状评价 `NOT_EVALUATED_THIS_PILOT`，部署GT位姿未知；未将GT接入初始化、注册或选择。展示为实际RGB、原Mask/预测轮廓、mm同尺度网格，没有美化GLB。

配套018回归：[DEPTH_REPLAY](evidence/DEPTH_REPLAY.json)调用既有 `replays.depth_supervised`，未训练。原生轴向Z、首次命中重心插值监督，11766固定像素中11413 active、353 miss均保留；loss=0.0025616365855741416，与历史差0；梯度相对误差8.365e-8，低于既有1e-4容差。未把miss无梯度变成有效监督，也没有把旧相对深度替换称018。修复后的014 renderer以及018实际依赖仍须保留。

## 4. 快照和视频级刚体接口

本轮只读原格式并在下半段适配。没有要求前半段提前输出新格式，没有运行或修改V6/004相机/HERO任务。

|来源|已核实含义|可做/缺口|
|---|---|---|
|G01 002历史多视频包|每帧RGB/Mask/K/T SHA，360×640，OpenCV c2w，平移mm；FIT/HOLDOUT与video ID保留；R10表示10mm内径，CAD Rmid=5.6mm、wire半径=.6mm|支持冻结相机条件下主体拟合；部分raw_frame仅历史别名，meta明确rawframe unverified，不能据文件名认证原视频帧身份|
|G01_demo 004冻结样本|原source commit5636aa…，source_plan明确；4帧原RGB/Mask，K对应360×640；独立Kn对应352×640原生深度；153个参考地标、CAD、22733 HERO顶点/43746面|验证Target为raw00341，Support依次raw00326/raw00360/raw00204，native reference/source pose与帧表一致，逐原生像素反投影回到mesh。完整小快照已复制保护|
|001 reference_banks G01_004/005|分别153/980地标，描述子、协方差，OBSERVATIONS给各视频内部track/view/feature/uv|两视频track编号是局部身份，不是跨视频对应。没有核实共同地标ID/共同可见Ring方向信息及005完整Target/Support闭包，因此未启动真实注册|

[逐帧盘点](evidence/SNAPSHOT_INVENTORY.csv)、[004保护哈希](evidence/SNAPSHOT_PROTECTION.json)。允许的后续连接点是 `snapshot.load_snapshot()` / `move_video(snapshot,H)`：它只读取、验证和转换表达，不更新科学观测。深度为camera axial Z（mm），不是射线长度；不重采样深度，不把原K与native Kn混用。`move_video`同时左乘所有c2w、转换地标/HERO/Ring，并更新帧和HERO嵌套位姿；原manifest明确仅作不可变来源记录。

刚体控制复用现有 `sim.geometry.rigid_fit/transform/se3`。在一个真实004场景上施加已知SE3，77个合成身份对应地标估计一个B→A，76个地标留出；Ring CAD仅检查公制尺度和同步变换，不凭轴对称Ring猜yaw。全部4帧投影和三个不相交地标子集检查一致性，没有逐帧自由修正，也没有主体形变或“只移动HERO、固定相机”的定位替代。

控制结果：留出地标最大误差1.46e-14 mm，Ring1.19e-14 mm，HERO1.13e-14 mm，视频内相对相机最大矩阵差7.11e-15，投影约1e-13 px。[完整数值](evidence/RIGID_CONTROL.json)含已知/估计变换。**真实视频分母1，人工坐标帧2，真实双视频配准NOT_EVALUABLE**；三个子集和四帧不是独立配准样本，不是噪声/错配鲁棒性实验。

## 5. 保护、复现与限制

任务fixtures实际保护了28个主体输入、16个004快照文件、14个历史Graph/柄部参数与正负结果，共约12.1MB原始字节；不是只写路径或哈希。G03拒绝CHOSEN_GATES、FAILED_ATTEMPT与G01 FINAL分别保留。既有原源码复用，20份祖先源码/小证据以原字节保护；准确位置见核心资产表与保留清单。当前工作树内源/fixture受Git保护；外部大权重、环境、全视频没有上传或移动。**不宣称离线外部备份已完成。**

执行仍依赖本机只读 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（实际Python3.12.13）、共享 `.runtime`、Open3D vendor；torch2.7.1+cu128，RTX3060 Laptop。018回归另外依赖保留目录中的原arm输入及native观察；柄部完整Boolean需Blender5.0.1。当前有可重复调用命令和小主体fixture，但不是全平台无外部依赖安装包，也不是可直接接任意新数据的初始化系统。

所有命令在本独立工作树根目录执行；新优化及018回归运行目录必须新建，拒绝覆盖。评价/清单命令会重写本任务对应摘要，复核固定交付时应使用独立检出副本。日志/失败/大对应数组保留本地；Git只上传精选参数、mesh、小表和PNG。

```bash
T=experiments/TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001
bash "$T/run_python.sh" -m unittest test_recovery -v
bash "$T/run_python.sh" "$T/code/replay_graph.py"
# 新优化，明确从011 FINAL / 013 INITIAL启动；使用未存在的新目录
bash "$T/run_python.sh" "$T/code/pilot.py" --out "$T/runs/PILOT_NEW"
bash "$T/run_python.sh" "$T/code/evaluate_pilot.py" --run "$T/runs/PILOT_NEW"
bash "$T/run_python.sh" "$T/code/rigid_control.py"
# 零步018回归，依赖保留的外部输入；使用新目录
bash "$T/run_python.sh" "$T/code/replay_depth.py" --out "$T/runs/DEPTH_REPLAY_NEW"
bash "$T/run_python.sh" "$T/code/build_inventory.py"
```

边界验证：预算非法值、SE3投影与相机基线保持、拒绝scale/reflection、全部嵌套位姿和原深度/RGB一致，共4项通过。002原Graph/SmoothARAP/投影/碰撞/Sweep测试26项通过。首次测试调用缺旧模块路径、首次短程保存失败、native深度字符串读取差异都记录并修复；不删除失败运行。独立代码审查发现工程验证版与主版SHA身份误标，已纠正；未由审查员运行科研训练。最终验证/发布集合见 [VALIDATION.json](evidence/VALIDATION.json)。

## 6. 下一轮最小问题

最优先是补齐 **009 G01生成输入与011原初体C**：按已记录SHA找回参数/基底/原深度，恢复009→011生成与011优化，逐阶段比较C_011和FINAL011，再决定是否值得把新观测送入原初始化方法。当前不能回答“从明确原始观测生成初体再更新”已全链成功，只能回答更新器从明确历史起点确实可运行。

跨视频独立推进的最小验证是：在一组004/005中冻结真实可核验的共同地标对应，确认各自相机和HERO Target/Support身份；用单个每视频SE3验证多帧投影一致性，保留错配/无解。不需要等待或干预前半段最终格式；由适配器逐源适配。只有这一步成立，才值得再试共同主体拟合和HERO局部对应；本轮不据G01短程成功自动扩全组或长柄生长。

## 发布回执

代码与证据提交 `6e6b7a3c5a1993e4976e0aa24ca0747ef73ef5c4` 已push到本任务独立分支，并实测 `git ls-remote` 返回相同SHA；见 [PUBLICATION_RECEIPT.json](evidence/PUBLICATION_RECEIPT.json)。随后仅追加本发布回执及报告说明；最终分支tip在人工交付消息中给出。未合并或更改前半段分支。
