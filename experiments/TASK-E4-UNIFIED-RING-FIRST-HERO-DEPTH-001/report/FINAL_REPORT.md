# 五组标准流程与 HERO 深度消融

**五组未全部通过。4/5 组的 004 完成新 HERO 和 B1/B2；G02 无合法完整相机输入。10 段视频中只有 4 段产生训练结果，G03/004 的 HOLDOUT 相机还存在 1/3 失败。**

B2 相对 B1 的独立 GT 表面 MAE 在 1/4 个共同有效组下降；组均 ΔMAE=-0.004848 mm。GT MAE 与可评价 HOLDOUT 均不退化的组为 1/4。严格 IoU 与条件占据分开报告，NaN 不补齐。

## 1. 实验目的

统一每视频 Ring-First → 正式新 HERO → 同一主体更新器，检验仅增加深度项的影响。没有跨视频联合主体、相机 BA、DXY 修改、HERO 训练或 HERO 重新定位。

## 2. 实验环境与代码来源

- 正式工作空间：`/home/liu/ring_first_3d_workspace`；remote `https://github.com/zheng1524/ring-first-3d.git`。普通工作空间按本任务要求初始化本地 Git，非复用废弃 Worktree。
- 分支：`exp/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001`；实现提交 `2cedd599f07f3ebc6978c226f4ee53dc202a4ba4`；基线为本地 003 源码快照，原主线来源提交见 `audit/WORKSPACE.json`，没有声称具有旧仓库的完整 Git 祖先链。
- Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；torch `2.7.1+cu128`；CUDA `12.8`；GPU `NVIDIA GeForce RTX 3060 Laptop GPU`。未建环境或安装依赖。
- Ring-First 复用 native RF5DoF 求解、RGB 内点和 yaw/normal 消歧；原方法内部 PnP 只用于 RGB 几何和种子，**最终相机仅可来自 Ring-First 候选**，没有使用纯 PnP 外参替代。
- 保留最初 mixed-candidate 诊断及冻结文件；`PROTOCOL_RF_ONLY.yaml` 在 GT 之前明确规定仅在既有 Ring-First 候选族内选择，求解器、评分和全部数值参数未改。它是透明的来源过滤，不是拒绝失败后暗中使用另一个相机算法。
- 正式 MVSAnywhere `5bd49bba0992aa56060e1aa3bb40b2150b04726f`；权重 SHA256 `00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d`。实际新加载/推理凭据为 `runs/RF_ONLY_V1/HERO_MODEL_RECEIPT.json`，环境文件的最初 `loaded_for_inference=false` 仅代表前置哈希检查时点。
- 当前 002 Deformation Graph/Smooth ARAP/Sweep 优化器原 36×3 预算、学习率、视角均衡和回缩不变。最小接口差异见每臂 `CONTRACT_*/ADAPTER.diff`：添加原 HeroDepth018；两臂均接入已接受 CurrentRingGate；记录深度诊断。不是新建自由顶点优化器。
- 历史 contour_objective/multiview/train_mesh/free_model/safe_geometry/depth_terms 和当前 Graph/Sweep/Boolean 均已定位；实际使用及 SHA 见 `audit/VERSION_SOURCES.csv`。旧结果只读。

## 3. 五组输入资产审计

当前冻结清单实际为每组 004、005 各 8 FIT，共 80 FIT、25 HOLDOUT、10 视频，超过用户给出的历史 6 段示例。未换视角或改变 split。

| Group | 004 FIT/HOLDOUT | 005 FIT/HOLDOUT | 初始主体 |
|---|---|---|---|
|G01|8/5|8/2|EXACT013，同原拓扑/尺度|
|G02|8/3|8/2|EXACT013，同原拓扑/尺度|
|G03|8/3|8/2|EXACT013，同原拓扑/尺度|
|G05|8/3|8/1|EXACT013，同原拓扑/尺度|
|G06|8/3|8/1|EXACT013，同原拓扑/尺度|

输入 RGB、Mask、缓存、K、Ring、初始主体及 GT 身份见 `audit/INPUT_MANIFEST.csv`；新相机/HERO 绑定见 `audit/OUTPUT_BINDINGS.csv`。105 张原图与 Mask 文件哈希以及缓存像素哈希均核对通过。原视频/照片/ZIP 的实际路径、大小、SHA 见 `audit/RAW_DATA_INVENTORY.json`。部分早期原始视频帧号仍继承未认证标签，本轮只证明归档图像/Mask/缓存身份，未声称重新认证所有采集帧号。

四个 004 RGB 标定库的历史参考角色均为 FIT，且与当前 HOLDOUT 的像素 SHA 无重叠。历史标定 FIT 不等于新增 Body 训练帧；本轮主体只使用冻结的 8 个 FIT。G01/005 缺少完整参考哈希且继承未认证跨视频坐标处理，未准入；G02 及其他 005 无可复用同视频库，未借用 004 库。参见 `BANK_ADMISSION.json`。

## 4. 标准流程验收

| Group | Video | Ring-First | HERO | PyTorch3D | Contour | Contour+Depth | FIT相机 | HOLDOUT相机 |
|---|---|---|---|---|---|---|---|---|
|G01|004|PASS|PASS|PASS|PASS|PASS|8/8|5/5|
|G01|005|FAIL|NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN|0/8|0/2|
|G02|004|FAIL|NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN|0/8|0/3|
|G02|005|FAIL|NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN|0/8|0/2|
|G03|004|PARTIAL|PASS|PASS|PASS|PASS|8/8|2/3|
|G03|005|FAIL|NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN|0/8|0/2|
|G05|004|PASS|PASS|PASS|PASS|PASS|8/8|3/3|
|G05|005|FAIL|NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN|0/8|0/1|
|G06|004|PASS|PASS|PASS|PASS|PASS|8/8|3/3|
|G06|005|FAIL|NOT_RUN|NOT_RUN|NOT_RUN|NOT_RUN|0/8|0/1|

每个 PASS 的输入、输出、源码版本、日志及证据见 [逐阶段记录](PIPELINE_STAGE_RECORDS.csv)。PARTIAL 保留固定分母；未通过视角不以历史相机补齐。

32 个冻结 FIT 目标均完成正式 HERO，保存原始轴向 Z、有限正值有效性、Raw XYZ、原生像素身份及完整开放 Mesh。预算为 32 个唯一目标；HOLDOUT 不作为训练深度目标。未插值补洞。另在全部 Body 冻结后，对相同 32 个输入元组重复推理以补存官方 sky 输出、depth_masked 与 cost_volume，合计 64 次实际推理。32 次重复的原始深度全部 BITWISE 相等，模型 depth_masked 中无效 Polyp 像素全部为 0。辅助输出未回写训练。见 HERO_AUXILIARY_AUDIT.csv 与每目标 RECEIPT.json。
官方 sky 输出和 cost_volume 不冒充校准置信度；本模型无独立校准置信度输出。保留模型有效性与有限正值有效性两套证据。

## 5. 深度消融实验结果

| Group | Arm | Strict IoU | Conditional IoU | GT MAE mm | GT P95 mm | FIT IoU | HOLDOUT IoU (有效/固定) |
|---|---|---|---|---|---|---|---|
|G01|B0|0.8497|0.8497|0.3481|1.0883|0.8333|0.8267 (5/5)|
|G01|B1|0.8586|0.8586|0.3286|1.0860|0.8575|0.8330 (5/5)|
|G01|B2|0.8713|0.8713|0.3021|0.9578|0.8872|0.8664 (5/5)|
|G02|B1|NaN|NaN|NaN|NaN|NaN|NaN (/)|
|G02|B2|NaN|NaN|NaN|NaN|NaN|NaN (/)|
|G02|B0|NaN|0.5666|0.4116|1.6570|NaN|NaN (0/3)|
|G03|B0|NaN|0.7675|1.2922|8.9077|0.8525|0.8662 (2/3)|
|G03|B1|NaN|0.7737|1.2850|9.0639|0.8562|0.8664 (2/3)|
|G03|B2|NaN|0.7675|1.2921|8.9076|0.8525|0.8662 (2/3)|
|G05|B0|NaN|0.8172|0.6556|3.8857|0.9688|0.9559 (3/3)|
|G05|B1|NaN|0.8172|0.6556|3.8857|0.9688|0.9559 (3/3)|
|G05|B2|NaN|0.8172|0.6556|3.8857|0.9688|0.9559 (3/3)|
|G06|B0|NaN|0.8815|0.2561|1.2245|0.9227|0.9236 (3/3)|
|G06|B1|NaN|0.8815|0.2561|1.2245|0.9227|0.9236 (3/3)|
|G06|B2|NaN|0.8815|0.2561|1.2245|0.9227|0.9236 (3/3)|

G03 的 HOLDOUT 子集均值明确为 2/3；完整冻结 HOLDOUT 均值保持 NaN，不能充作全体通过。GT 评价在所有预测冻结之后开始，采用原 015 真正的尺度固定刚体对齐；仅保存评价副本，世界坐标预测的 SHA 保持不变。所有方法共享固定 2^17 占据样本域，双向表面各 8192 样本。配准后的误差是形状误差，不代表公制世界位置更准确。

| Group | ΔGT MAE B2−B1 mm | ΔConditional IoU | ΔFIT IoU | ΔHOLDOUT 子集 IoU | Depth MAE B1→B2 mm | Depth coverage B1→B2 |
|---|---|---|---|---|---|---|
|G01|-0.0265|0.0127|0.0297|0.0334|0.6413→0.4836|0.8168→0.8567|
|G03|0.0071|-0.0063|-0.0037|-0.0002|1.1764→1.1711|0.8566→0.8539|
|G05|0.0000|0.0000|0.0000|0.0000|0.2882→0.2882|0.9615→0.9615|
|G06|0.0000|0.0000|0.0000|0.0000|0.3221→0.3221|0.9203→0.9203|

深度有效覆盖率保留固定原生观测分母；缺失命中使用原 018 的固定最坏范围惩罚。深度 MAE 只统计 active 命中，必须连同固定分母覆盖率解释，不能把低覆盖下的低残差视为成功。每视角 MAE/P95、固定 N 和 active N 见 `DEPTH_METRICS.csv`。


深度实际参与证据：

| Group | INITIAL 非零深度顶点梯度视角 / 固定 FIT |
|---|---|
|G01|8/8|
|G03|8/8|
|G05|8/8|
|G06|8/8|

`DEPTH_GRADIENT_EVIDENCE.csv` 保留 INITIAL/FINAL 的逐视角实际梯度和参与顶点，属于端点审计，未冒称每个中间迭代都被逐像素梯度追踪。`BOUNDARY_DISTRIBUTIONS.csv` 及逐视角 NPZ 保存双向轮廓距离的中位、MAE、P95、最大值和完整误差向量。Figure2_HERO_Auxiliary 展示真实官方辅助输出及全部原生 Raw XYZ；Figure6_LocalMorphology 使用同尺度正交视图暴露基底和未恢复柄部。

B1 的共享 IO/梯度契约检查也会读取新 HERO 并保存诊断梯度，但不执行参数更新。其训练闭包在 B1 时立即返回零深度项，既无深度梯度也无深度模型选择。旧 INPUT_CONTRACT 中 HERO_read=False 表示训练目标不依赖 HERO，并非整个进程从未读取文件；B2 使用同一适配器且启用深度项。

逐组解释：

- G01：B2 相对 B1 的 GT MAE、P95、FIT 和全部 5 个 HOLDOUT 的平均 IoU 均改善；这是本轮支持深度增益的病例，仍仅是该固定协议的一个组。
- G02：B0 只供独立形状参考；没有本路线 B1/B2 预测，NaN 不回填。
- G03：B2 相对 B1 的 GT MAE 增加约 0.007115 mm，条件 IoU、FIT 及有效 HOLDOUT 也降低。B2 基本停留在初始主体，没有恢复连续柄部。P95 下降不能抵消其余指标退化；HOLDOUT 仅 2/3 有效。
- G05/G06：B1/B2 的条件 IoU、FIT/HOLDOUT IoU 完全相同，GT MAE 的 B2−B1 分别约 1.52e−7 / 1.25e−6 mm。这些量级不构成可信形状改善；保留原始数值，没有将微小浮点变化宣传成获益。深度梯度非零并不保证几何门禁会接受明显更新。

Ring 门禁精确范围：每次接受更新均通过冻结的 CurrentRingGate（带重复查询/float32 ULP 容差）。这不等于最终穿透数值绝对不增加：例如 G06/B2 的 Ring→Body 最大穿透相对 INITIAL 累积增加约 1.50e−5 mm，超过单步约 3.34e−6 mm 容差。`RING_COLLISION_METRICS.csv` 明确记录逐步通过与累计漂移，Failure Registry 保留该数值门禁局限；本轮没有改门禁或事后回写预测。
## 6. 五组结果可视化

静态图入口为 [visualization/README.md](../visualization/README.md)，没有 HTML。每组 Figure1 是实际 Ring/CAD 投影及分别显示的两视频相机分布；Figure2 是新 HERO 或明确 NOT_RUN；Figure3 是 B0/B1/B2 实际世界 Mesh；全部 004 冻结视角含 HOLDOUT 对照在各组 `004/`；Figure5 使用真正 GT 刚体对齐后的完整 Mesh；Figure6 为实际位移和训练轨迹。所有三维图使用毫米坐标及同组统一范围。

此前 `figures/` 与 `PRE_RF_ONLY_DIAGNOSTIC` 属最初未准入诊断，其中旧的合并视频相机散点图不能视为共同世界坐标认证；正式交付 `visualization/*/Figure1_CameraPoses.png` 分开两视频坐标系，避免该歧义。

## 7. 失败与异常

- G02：缺少同视频 RGB yaw 参考库；圆环自身无法确定绕轴 yaw，保持 FAIL，不使用历史/PnP 补齐。
- 所有 005：缺库或来源/共同坐标处理未核清，保持 FAIL；不能通过复制 004 机位完成。
- G03/004：一个 HOLDOUT Ring 投影超过统一 3px 门限，保留该视角及 NaN；没有删除原 split。
- 每臂全部接受、回缩、拒绝及碰撞记录均在 `UPDATES.json`。源码中的 CurrentRingGate 只做当前状态碰撞非恶化判断，无额外排斥 Ring 梯度。
- 单视频任务无法满足原有至少两个视频的 Sweep 生长证据门槛；两臂同样拒绝生长，未恢复旧的局部面片挤出，也未静默删除 Boolean 模块。没有合格生长候选，所以本轮未激活 Boolean；原有 G01 成果和 G03 拒绝结果均未修改。
- 深度损失首命中切换导致全栅格有限差分跳变；失败和一次无效零导数探针均保留。最终非零公制位移导数检验相对误差 8.34e−6；这是稳定可见区的条件导数，不是对可见性跳变可微的宣称。训练未因此删观测。
- 严格 IoU 的实体/基底无效状态保留 NaN；条件占据与表面指标不冒充严格实体 IoU。

## 8. 阶段性结论

1. 五组未全部通过；相机/数据问题与几何质量分开。4/5 组的 004 获得合法新 HERO 和实际 B1/B2，G03 的 HOLDOUT 评价仍为部分有效。
2. HERO 深度使 1/4 个共同组 GT MAE 下降，平均变化 -0.004848 mm；不能仅凭训练深度下降声称三维精度提高。
3. G03 是否改善以本表相对 B0/B1 的固定指标判断；本轮没有连续新柄部，不能宣称解决此前柄部恢复失败。旧跨视频/旧相机实验不是同协议配对对照。
4. 即使阶段执行 PASS，GT/HOLDOUT 仍可能恶化；这些是保留的科研负结果，不通过模型挑选隐藏。

固定审计表：

| 审计项目 | 必须汇报 |
|---|---|
|目标组数|5 物理组，10 视频，80 FIT、25 HOLDOUT|
|本算法独立成功|4/5 组产生 B1/B2 数值结果，仅各自 004；不等于正确重建|
|本算法失败|G02 B1/B2 为 NaN；其他组 005 无训练；G03 HOLDOUT 部分不可评价|
|历史测量值回退|0；无历史相机/HERO/Body 预测补齐|
|失败组及具体原因|逐帧 `FAILURE_REGISTRY.json`、每视频验收表及对应 PNG|
|最终统计样本|B1/B2 共同 4 组，固定总分母 5；全视频目标分母 10|
|是否使用 GT 选择算法|否；全部预测 SHA 冻结后才读取 GT，FINAL 固定 36，不选 checkpoint|

表面误差单位为毫米；相对误差按 GT 包围盒对角线归一化，仅是形状表面统计，不冒充息肉直径测量。每组 MAE/P95/最大值及相对中位误差均在 BODY_METRICS.csv。

## 9. 下一阶段建议

先补齐缺失同视频 RGB yaw 标定与真实来源绑定，复核 G03 留出相机；再人工审阅本轮固定深度项造成的几何与 HOLDOUT 变化。若要恢复柄部，应单独审批能同时满足场景坐标和原生长证据门槛的协议。本轮不放宽门槛、不执行新相机配准研究、不扩大实验。

本地分支与所有源码/输入/预测/输出锁定记录齐全；未向 GitHub 推送。最终交付提交 SHA 由任务结束时的 Git HEAD 给出。
