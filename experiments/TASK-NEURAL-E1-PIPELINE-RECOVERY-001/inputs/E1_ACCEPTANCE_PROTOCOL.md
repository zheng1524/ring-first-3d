# E1_ACCEPTANCE_PROTOCOL

**版本**：E1-C0C1-ACCEPT-v2 / 2026-10-30，落实RA `APPROVE WITH CHANGES — C0+C1 ONLY`。  
**范围**：仅第一份 `TASK-NEURAL-E1-PIPELINE-RECOVERY-001` 的C0+C1无训练门禁；**C2–C4未授权**。  
**判定原则**：`PASS`只能证明输入身份、几何/合法接口适配通过，**不代表神经几何科学成功**。每项必须有真实源SHA、代码入口/commit、测试方法、明确输入/输出、样本数、预定义容差、实际数值、图、可复现命令及失败状态。

## 1. 状态和全局一票否决

- `GATE_PASS`：全部适用强制合同通过，已登记条件限制；允许向RA申请新Task，但**不自动批准训练**。
- `PASS_WITH_LIMITATIONS`：部分资料、严格holdout或模型原生条件不具备，其他有效源合同通过；后续取舍由RA/研究者定。
- `EXPECTED_FAIL_E0`：旧MonoSDF几何域负例被正确拦截；**此负例结果FAIL是新测试机制的PASS证据**。
- `ADAPTER_INVALID`：真实射线采样/有效域、K/c2w/单位、z-buffer/无效值、官方输入消费合同不成立；停止该分支，不能通过GPU补救。
- `UNSUPPORTED_NATIVE_INPUT`：官方revision无相应点云/先验/valid字段合法入口；若薄adapter合法则单列`LEGAL_DERIVED_DEPTH`，否则禁止强塞。
- `DATA_INELIGIBLE / BLOCKED_MISSING_ASSET`：来源/资格不足，原样报告，不补造。
- `HOLDOUT_STRICT_UNAVAILABLE`：当前不能证明严格盲测，可进行C0/C1，不冒充后续严格评价。
- `NOT_RUN / RUNTIME_BLOCKED`：没有执行或资源异常；不能算科学失败或成功。

**一票否决**：修改任何冻结Ring-First K/c2w、Ring CAD、原始HERO/P0/历史报告、Dxy/GT；运行GPU模型训练/新推理/新HERO、下载大权重、清理旧工作树、用GT/Oracle/ICP或后验尺度拟合取得公制PASS、将跨视频候选默认为已配准、以缓存/模型输出冒充真实独立观测。发生则`TASK_SCOPE_VIOLATION`，停止任务并报告。

## 2. C0输入与科研身份验收

| 编号 | 硬检查与最低有效证据 | 合格条件/失败处理 |
|---|---|---|
| C0-01 | 新分支/worktree、base/E0/F3/MASt3R commit SHA；保护路径哈希与`git status` | 新改动仅任务目录；Git增量提交状态真实 |
| C0-02 | 实际校验36预期参考的RGB/Mask/nativeHERO/pack/UV/Raw XYZ/Cleaned及SHA（不是只读manifest） | 文件逐条`AVAILABLE/MISSING/UNRESOLVED`；实际通过数明确，不能把36当病例 |
| C0-03 | F1/F2/F3/新增面与其上游source/HERO/图片父系DAG | 单源派生不增计独立视角；清理和融合身份可溯 |
| C0-04 | G01_004与G01_005各至少3个合格不同参考候选、角度/Mask共视/Depth冲突及来源资格 | **均仅提出候选**，真实不同方向证据；不足则`BLOCKED_INPUT_SET`，不可机械两图替代 |
| C0-05 | G06 NORMAL、G08 LIMITED、G07 UNQUALIFIED压力以及photo001–003未认证状态 | 分层真实；004/005未注册分两个局部系；photo不当metric训练 |
| C0-06 | RGB/Mask/HERO依赖SHA级留出；G06 raw00351、G07 raw00293已知污染 | 严格holdout0如实披露，独立性不足不冒充验证 |
| C0-07 | 既有入口`unproject/depth_mesh`、F3来源、MASt3R、CAD、real_p0_renderer、E0模型包装的真实SHA/签名 | 复用表指明最小新接口；不实现第二套相机/深度/渲染系统 |

## 3. C1物理几何硬门禁

| 编号 | 试验项 | 验收逻辑与必要数值 |
|---|---|---|
| C1-01 | OpenCV `c2w/w2c`、K resize、轴向Z vs ray长度、mm↔m、UV↔XYZ、Mask绑定 | 合成+真实G01源；误差数值与预先阈值；冻结K/T一致；错误轴向Z映射应在合成负例被捕获 |
| C1-02 | Ring CAD投影与遮挡 | 实际R10/R5 CAD，黑实体与Mask/投影/深度z-buffer一致；不将Ring并入Polyp源面；来源统计分母完整 |
| C1-03 | SDF **旧E0失败的可复现静态拦截** | 旧10mm/unit、radius2.5、cam norm3.2714/3.8705；**结合官方真实Sampler/absorbing规则**计算前后景ray、可采样ROI和zero-crossing/opacity；输出`EXPECTED_FAIL_E0`与失败物理原因，不能只断言相机在球外 |
| C1-04 | SDF至多2个候选域 | 物理中心/scale/near-far/ROI明确，前景/背景有效采样分母、target Z是否在合法t区间、源XYZ回算、SDF符号和解析零交叉；若全无效`ADAPTER_INVALID`，禁止训练 |
| C1-05 | SDF后续loss数据合同（本轮不装配/训练） | 按真实来源清单列 `RGB,Mask,HERO_multi,source_conflict_weight,Eikonal,anchor,CAD`的`FUTURE_REQUIRED / CPU_GEOMETRY_READY / NOT_IMPLEMENTED`，**不得把未调用loss写WIRED**；相机不会被优化 |
| C1-06 | Map官方原生接口合同 | 固定官方revision的API签名/预处理、M0–M3字段，单位m、is_metric_scale、K/pose深度对应；证明实际消费合法输入的代码路径；**不执行forward** |
| C1-07 | **新增Map local XYZ/F1/F2/F3→source-view axial Z适配器** | 源相机K/T完全冻结；来源UV/tri ID追溯、真实z-buffer近表面/遮挡、valid/unknown/NaN/0处理、单位转换；原始源Z与派生Z的误差和覆盖比例；不凭空填洞 |
| C1-08 | **新增Map来源条件矩阵与冲突门禁** | Raw、Cleaned、F1/F2/F3、HERO不同参考、Ring CAD/有效MASt3R几何各列原生/派生合法性；同一RGB的多派生先验不得充当多相机；冲突层独立输出并标记 `LEGAL_DERIVED_DEPTH / UNSUPPORTED_NATIVE_INPUT / NOT_VERIFIED` |
| C1-09 | Map旧输出公制故障与相机pose残差 | 仅读E0缓存：M3 Ring→CAD median约22mm、p95、有效像素N；记录输入条件pose/原预测pose/预声明纯刚体gauge；**不得使用Map输出pose覆盖Ring-First**、不得以Ring ICP修补原生输出 |
| C1-10 | 观测支持/未知 | 多视角/单视角/冲突/Ring遮挡/先验补全/未知分标签；未观察背面不计面积；E0 SDF0有效支持面保持错误证据 |
| C1-11 | 图和复现闭包 | 3–4复合PNG、真实XYZ+固定mm轴+黑色Ring、源/遮挡/失败可审；`TECHNICAL_REPORT`一份、可重放CPU入口与本地HTML及Git commit |
| C1-12 | 授权和资源 | 无新SDF/Map/HERO forward、GPU训练、下载、旧目录清理、GT访问；冻结输入哈希未变；若blocked明确报告 |

**数值阈值**：K投影与反投影回算宜沿用E0已验证容差，必须在新测试执行前固定；不能为了PASS按结果放宽。C1真实ray域的有效比例应按真实前/背景类别报告，不以任意的“全部相机都在球里”作为替代。

## 4. 当前任务的必答问题（报告摘要要直答）

1. 旧MonoSDF的400步为何只证明adapter错误，而非理论失败？哪些静态ray/absorber测试会在训练前拦住它？若官方吸收规则有例外，是否如实说明？
2. G01_004和G01_005是否各找到≥3份相机合格、具有不同观察方向的参考，HERO依赖冲突/共享父系如何记账？
3. 36份参考以及F1/F2/F3到底有多少**独立来源图片**？每个Map条件深度来自什么父系？
4. Map官方哪类条件是原生合法的，Raw/Cleaned/F1/F2/F3如何只通过最小深度/来源适配进入？无效深度和多层遮挡如何表示？不支持的输入是否被拒绝？
5. 两臂全程K/T是否完全冻结？Map旧输出pose差与CAD偏差是否分开报告？
6. C0/C1通过是否**没有**被冒充为SDF或Map科学成功？四组的`AUDIT_N / MODEL_RUN_N=0 / SCIENCE_N=NOT_EVALUATED`是否写清？

## 5. C2–C4的后续门禁（**未授权执行**）

### C2：共同数据与损失/适配冻案

- **SDF**：同一视频≥3合格不同参考，共享一个SDF、训练源RGB/Mask/多HERO axial Z/Eikonal在真实计算图中有梯度；至少恒权多源S1与来源/冲突权重S2对照，且有S0无HERO消融；weights可复算且不全零；Ring CAD为强制硬验收，若可微损失未实现写`OUTPUT_GATE_ONLY`；MASt3R锚点未接计算图写`NOT_IMPLEMENTED`。
- **Map**：M-native M0–M3全部保留，M-geometry-conditioned的合法条件路径/valid/遮挡/来源SHA及相关信息说明完整；M4/M5只有接口通过才冻结正式名称；完全独立竞争，而非SDF初始化。
- 冻结评价源、双表比较、参数/随机数/GPU预算；新Task由RA/研究者批准。**C1通过不构成C2/GPU自动授权。**

### C3：模型科学候选而非工程烟测

- SDF：报告每源实际ray数量、深度/Mask/RGB梯度、loss曲线、共同模型与支持面/先验面，冻结pose不变；旧错误域不能复用；异常则停止该臂。
- Map：报告官方原始输出与预声明gauge、Ring/CAD、pose残差与多视图输出；不能使用事后GT/ICP/任意缩放救场。分别给原生与派生几何条件消融，异常状态保留。
- 有新模型输出≠`SCIENTIFIC_ACCEPTED`；失败保留且不要求两臂都有效才结束单臂审计。

### C4：独立真实视角、公制与多组

- 两视频先独立；G01三列 `004 / 005 / CROSS-VIDEO CANDIDATE — NOT FUSED`，跨视频位姿未独立认证不得写FUSED。
- 实际真实A→B五面板（A源图/A真实XYZ/B真实图/A RGB+几何投B/共同支持差异和未知）、六视角真实XYZ、来源可见面支持/先验/UNKNOWN；同源Raw/Cleaned/F1/F2/F3强对照和各臂最佳合法信息表。
- 覆盖、溢出、同像素RGB、独有真实支持面积代理、连续性、跨源冲突、Ring CAD median/p95和穿插全部报告；**不能只看MAE，不得藏掉低覆盖/高误差失败例**。
- G06 NORMAL、G08 LIMITED、G07 UNQUALIFIED压力分开报告实际运行/未运行/不合格；一个视频不等于独立病例。没有独立真值则绝对三维毫米误差`NOT_EVALUABLE`；未知背面不可计可见面积或体积。

## 6. 交接流程

当前RA裁决`APPROVE WITH CHANGES — C0+C1 ONLY`，**用户单独批准和转交本修订版 Task 才开始新 Codex 执行**。结束后PM按本协议独立验收，RA审查科学技术，再由研究者决定是否开启新C2/C3/C4任务。本协议不自动授权任何后续运行。
