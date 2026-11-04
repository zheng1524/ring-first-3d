# TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001｜Codex 科研执行任务书

**状态：人工已批准完整实验；PM 协议已制定；执行端尚未启动。** 2026-11-04，Phase E4。  
**项目：** `zheng1524/ring-first-3d`  
**执行分支（拟）：** `exp/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001`  
**基线分支：** `exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`，**不可从旧 `main` 直接起步**。  
**实验根目录：** `experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001/`

> **重要交接：** PM 已通过仓库连接完成只读审计，尝试从上述 A1/E1/E2 基线创建独立实验分支时得到 GitHub 403 `Resource not accessible by integration`。故目前 **没有创建远端分支、没有启动训练、没有实验结果**。以下是交给已授权、本地具备数据的现有 Codex 执行体的一份**完整、已批准、无需逐阶段审批**的任务。由执行端在其既有合法权限、数据和环境下创建分支并执行；若执行端也遭遇权限障碍，则停止相应外部写入并报告，不能绕过。

## 0. Role、授权与成功判定

你是 Reference-Ring Anchored Visible-Surface Reconstruction of Polyps 项目的 **Codex 科研执行智能体（EX）**。请先阅读 `AGENTS.md`、`COLLAB_STANDARD_v1.3.md` 和所有适用仓库规范。

**这一次不是单独做 P1 的可行性检查。** 完成一个统一实验周期：**P0 九参数椭球 → P1 低频形变 → P2 中频形变 → P3 观测驱动的局部精化，以及 C1 直接高自由度和 C2 纯频率逐级解锁两组对照。** 不必在 P1/P2 后等待人工回复。单组或单实验臂出现硬失败时，安全停止该臂、保留错误和日志、继续其他可执行组。

研究问题：在 **Ring-First 相机已知、HERO 局部深度固定、真实多视角 Mask** 的条件下，能否从共享九参数椭球逐步增加显式形变自由度，更稳定地解释真实可见几何，且相比直接释放全部自由度更好地泛化到留出视角？

科学成功不等于降低训练损失。必须报告真实三维连续演化、留出视角轮廓/深度、参数可辨识性、跨视角冲突、HERO 支持与失败，不能只上传漂亮的网格截图。

**严格边界：**

- 冻结 Ring-First 位姿、公制 `Ring_world_mm`、内参与裁剪约定；禁止以优化相机解释几何残差。
- 冻结 HERO 模型权重、原始预测、P0、Raw/Cleaned、Type-2 删除；不得通过重新清理/换深度使指标改善。
- Ring 仅为已知尺寸 CAD 实体、负责尺度与遮挡；不重建环点云或将环拟合成可形变物体。
- DXY 与 3D 完全隔离：只读复用**已产出的** E1 椭圆/九参数结果；不修改 `new-polyp-dxy`、DXY 算法及冻结结果。DXY 2D 椭圆不是精确三维截面。
- 不使用任何 GT 参与几何优化、参数选择或筛选展示。GT 若存在仅可经项目授权用于独立**最终**评价，本轮默认不用。
- G01 `video004`/`video005` 没有经认证的跨视频坐标变换前，**绝不**联合优化、拼接或聚合。
- 不做 B1 HERO 真网格贴片、B2/MonoSDF/Neuralangelo 神经 SDF、TSDF、NeuralFusion、假补面/强制闭合。
- **绝不编写依 Ip/Is/IIa 类别切换的几何拟合算法、loss 权重或特殊补丁。** 三类共用同一套优化。允许由**直接观测到的**开边界/背景支持决定边界条件，决不能仅凭类别臆造柄、背面或截面。

## 1. 已核实的仓库事实和必读入口

本协议依据 `exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001` 的实际文件组织，不要从较旧 `main` 推断最新 A1 状态。执行前拉取/核验该分支 HEAD、输入哈希、最新未同步的用户本地变更，并记录本轮基线 commit；存在更晚、已验证的 A1 资产则只读审计差异、显式记录取舍。

### 1.1 当前 A1/E1/E2 最关键资产

- `experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/TECHNICAL_REPORT.md`、`REPRODUCE.md`、`01_PROTOCOL.md`、`02_INPUT_AUDIT.md`、`04_STABILITY_ANALYSIS.md`、`05_FAILURE_LEDGER.md`。
- `config/PROTOCOL.json`，`metrics/PRIMARY_A_ONLY.json`、`ALL_FITS.json`、`ALL_MESH_INDEX.json`、`MULTISTART_STABILITY.json`、`PAIRED_COMPARISON.csv`、`INPUT_QUALIFICATION.csv`、`VALIDATION.json`、`ROOT_AND_VISIBILITY_AUDIT.json`，`provenance/INPUT_ASSET_SHA.json`。
- `code/common.py`（`decode`、`sphere_mesh`/`mesh`、公制相机/深度读取等）、`fitting.py`、`losses.py`、`prepare.py`、`run.py`、`replay_inputs.py`、`visualize.py`、`validate.py`、`synthetic.py`、`finalize.py`。
- E1 = 已有 2D DXY 主体椭圆辅助初始化；E2 = 完整 Polyp Mask 辅助初始化。**二者均为九参数椭球**，已经做过多启动与固定约束对照。此次不重新开发 DXY 椭圆。
- 现有 `mesh(p,R0)` 将标准球网格变换为公制椭球；`decode(p,R0)` 给出中心、旋转、半轴；`first_depth` 是椭球的解析首交深度。新谱形变不能继续用解析椭球 `first_depth`/conic 作为形变后几何的预测器。
- A1 常用 640×360 RGB/Mask，HERO 原生为 352×640；前者与后者的像素坐标不能未经验证就相互当作一致。固定 `K`、`c2w`、`Ring_world_mm`、裁剪/resize 关系、pixel-center 规则。
- A1 为复现实验包含特殊防护：`code/common.py` 在导入时会设置空 CUDA 设备并安装阻断 `torch`/网络的 Python audit hook。**GPU PMGR 不得直接 import 这个模块。** 请以只读代码审计方式提取/封装所需的纯数学与 IO 逻辑，验证数值一致；保留来源与 SHA，不移除旧文件的保护或污染旧 A1 实验。

### 1.2 其他必读与复用

- `RA_PHASE_E4_A1_A2_RESEARCH_TASK_v1.0.md`（若工作树中缺失，可读取人工附带的同名 RA 正式任务书；不要凭文件名声称已读）。
- `experiments/TASK-E4-A1-COARSE-BODY-001/`，尤其 `A2_PREPARATORY_DESIGN_ONLY.md`：背景基底资格有限，**A2 不是已经成立的真实贴片算法**。
- `experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/TECHNICAL_REPORT.md`：轴向相机平移与 HERO 深度偏差雅可比列余弦曾约 **0.95–0.97**；本轮冻结相机，优先相对深度，防止由主体形变错误吸收耦合。
- `experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py` 的历史 `render` 及 A→B 实投影验证，`visualization/real_p0_renderer.py` 的真实 XYZ 可视化；Camera Gate、视角分区、Ring CAD 遮挡与可见性函数。
- Phase D/Phase C Raw/Cleaned、真实 XYZ、背景资格，以及 TSDF/NeuralFusion/MonoSDF 失败记录：仅作经验与输入来源，不导入它们的融合优化器。

### 1.3 当前数据资格（初步审计，执行时必须复核）

| 场景/来源 | A 训练候选 | B 留出候选 | 资格及约束 |
|---|---|---|---|
| `G01_004`（Ip） | `ref08, ref13, ref03` | `growth_r14` | A1 标 `INSUFFICIENT_EVIDENCE`；E1 的 Q-conflict 严格资格不足；只能条件/诊断结论；**不得合入 G01_005**。|
| `G06_004`（IIa） | `growth_r01, growth_r03` | `growth_r06` | Camera Gate/背景来源条件复核后可作条件性主候选；背景是否可用由可观察证据决定。|
| `G07_004`（Is） | `ref04, growth_r02` | `new_r06` | `PRESSURE_HISTORICAL_HERO_CHAIN_UNQUALIFIED`；只能压力测试，**不计入严格合格真实 Is 成功率**。|
| `G08_005`（IIa） | `growth_r01, growth_r02` | `ref04` | `PRESSURE_LIMITED_CAMERA`；压力测试，不冒充相机合格样本。|

现有 B 视角整体是 `CONDITIONAL_UPSTREAM_GATE_SELECTION`，**不是完全独立、端到端合格的留出测试集**。执行端查找是否有其他合格 Is，若没有，可加公开记录参数的合成/扰动 Is 压力测试并如实写“真实合格 Is 不可评价”；**不得降低 Camera Gate 或删除困难组来凑满三类**。视角分组、B 的选择应在模型拟合前冻结，B 不得反向用于超参数调优或选最漂亮初值。

现有 A1 的初步结论为 E1/E2 `MIXED`：例如 G01 E2 Mask IoU 较高但深度残差较大，G06 E1 的多启动稳定性较好，G08 均不稳定。不能根据“哪一臂图最好”事后选种子。至少从合格 E1/E2 中预先登记两个代表性初始条件；若一个场景两臂存在，则两臂都跑，按固定种子成对比较，并保留失败。

## 2. 开发/运行准备与不可越过的预检

1. 在**有合法仓库写权限的执行环境**从指定 A1 分支创建上述全新 PMGR 分支（若分支已存在，先检查归属和工作树状态）；现有 A1/A2/E3 文件、目录、历史资产只读。不得强制推送、`git reset --hard`、清空目录、批量删除用户改动。
2. 新建 `experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001/`，所有代码、配置、轻量指标、图、任务文档独立保存。大文件模型、原视频/权重留本地外部结果目录，仅在 Git 保存校验信息与索引。
3. 检查可用 CUDA/CPU、SciPy sparse eigensolver、PyTorch、可微渲染器与依赖；**优先 nvdiffrast**，不兼容或安装失败可显式切到 **PyTorch3D** 并保留错误日志；不允许在未验证的情况下改写核心相机模型。若 GPU 不可用且 CPU 计算可行，可缩小训练采样预算**但不得省略 P2/P3/C1/C2 的诊断**；资源完全不足则记录阻碍、可执行的部分和重现命令，不能伪造全流程。
4. 只读获取已冻结的 E1/E2 参数、Mask、HERO、Ring CAD、K、c2w、资格状态与 SHA。检查真实深度毫米尺度与三角网格法向、外向方向、面索引合法性。不得静默修改摄像机与 HERO 资产。
5. 初始椭球三角化。优先较均匀的三角网格（如等面积细化的 icosphere），避免 UV 球两极顶点造成谱计算退化。与旧 A1 `mesh` 的形体、尺寸和投影一致；如为了更均匀质量替换**拓扑而非几何**，说明误差并给出固定随机/细分等级。
6. **P0 核验硬门**：对至少多个 A 和 B 视角，将新渲染器 P0 三角网格预测与旧 A1 解析椭球投影、历史 A→B 投影进行定量同位比较（轮廓、首交深度、像素中心、背景/环遮挡），验证 `K`、`c2w`、camera +Z、毫米、640×360/352×640 映射。阈值事前规定并记录；如果发生**系统性坐标错误**，停止受影响实验臂而不是错误地调整椭球/相机补偿。该门是完整执行的内置准备步骤，不需要人工单独审批。

## 3. 形变表示：P0→P3 必须共享连续网格

### 3.1 P0、谱拉普拉斯和防重复自由度

P0 取冻结的九参数椭球 `S0=S_ellipsoid(theta0)`，三维中心三参数、半轴三参数、旋转三参数。其网格 `M0=(V0,F)`。

构造 cotangent 离散 Laplacian `L` 和 lumped/consistent mass 矩阵 `M`，求解

`L phi_k = lambda_k M phi_k`，`phi_i^T M phi_j ≈ delta_ij`。

首选 libigl Python bindings；环境困难则经一致性测试使用 SciPy 稀疏求解，固定符号与归一化。零特征值、常数模、翻转/退化三角形、数值病态必须审计。候选低频模式 `phi_k` 的实际顶点位移场为 `B_k(j)=n_j phi_k(j)`。

**避免冗余：**对当前九个刚体/半轴参数的顶点运动雅可比及已释放模式，用质量加权 QR/SVD 对候选法向位移基进行投影消除重合；同时做观测残差雅可比的独立性检查。不能把刚性平移/旋转的等价变形重复算作“新增可辨识几何”。如初始椭球重参数化导致 `theta0` 不适合再次优化，可将九参数视为 P0 基线且冻结后在其切空间相对校验，明确说明策略，保持 C1/C2 相同处理。

### 3.2 固定几何拓扑上的法向位移

首版统一：

`X_j(a)=X_j^(0) + n_j^(0) * sum_{k∈A_L} a_k phi_k(j)`。

`X_j^(0)` 是**同一个** P0 网格的顶点，`n_j^(0)` 为固定基准法向，`A_L` 是该阶段已解锁模式。每次阶段从上阶段所有 `a_k` 无损继续，**不得重设新椭球或丢弃先前形变**。如为数值稳定要在阶段边界重计算形变基，必须实现旧网格→新网格的严格几何保形传递、报告最大传递差并提供对照；优先始终固定基准网格及其谱基。

### 3.3 四阶段全执行（数值为候选预算，不强迫释放）

| 阶段 | 形变预算 | 主要观察 | 输出 |
|---|---:|---|---|
| P0 | 9 参数椭球 | A1 现状、两种固定初值、跨视角误差 | 共有基准/初始 checkpoint |
| P1 | 新增约 8–16 个低频模式 | 整体非对称与低频形状 | 网格/曲线/资格与失败记录 |
| P2 | 再新增约 20–50 个中频候选 | 多视角支持的局部隆起、局部冲突 | 模式解锁/拒绝日志 |
| P3 | 候选总形变自由度约 100 或更高 | 可见可靠区域的局部精化，谨防振荡 | 完整候选审计、最终 checkpoint |

P3 候选超过可观测有效秩时**可拒绝激活**，但必须真正生成/测试候选并报告拒绝比例、原因、测试的计算预算；不可只做到 P1 然后笼统称“P3 不合适”。优先继续全局谱；若高频表现为全局振荡，可预登记并明确启用局部紧支撑样条、低维 embedded deformation graph 或 ARAP 局部正则，保留**统一共享主体**和 `P3_GLOBAL_SPECTRAL` 的失败证据。不得偷偷切换神经 SDF。

### 3.4 无类特化与真实可见区域

Ip/Is/IIa 采用同一基、训练器、解锁规则、正则化和评估分母。只允许基于每个**具体场景已经认证的**背景支持与开放边界输入决定 `E_Base` 是否激活。没有证据的后侧、柄、基底不被强行当作真实目标；如果全封闭椭球是当前初始化的数学表面，要明确标注“未观测部分仅是初始化表面/推断区域”，不可冒充已重建真实几何。

## 4. 可微投影、多视角损失和观测来源

每组每次只有一个共享参数向量 `a` 与一张共享三维网格。**不能每个视角独立训练形变再拼接。** 已认证 A 视角作为训练组，预先固定 B 视角作为留出，不参与优化与人工调参。

`E_total = λ_M E_Mask + λ_D E_Depth + λ_H E_HERO + λ_B E_Base + λ_R E_Reg`。

实现和记账：

1. **Mask**：在真实 K/c2w 上可微光栅化首层可见三角面轮廓。真实 Ring CAD 可见遮挡优先；Ring 遮挡、无标注未知区域及 Mask 的有效/无效边界需分类，不能把“未知”当作背景负例。可用 soft silhouette 或 signed-distance contour loss，保存硬 IoU、Chamfer/平均轮廓距离、Mask 外预测比例。E1 的 2D conic 只能对 P0 提供初值/比较，P1 以后必须真的渲染网格。
2. **相对 HERO 深度**：统一相机坐标下的相对深度差、相邻有效样本深度差、低频基准去偏后的 robust residual；不得将绝对轴向偏差强制写进形变。深度失效、CAD 遮挡、遮挡顺序错误、不同视角对应像素未真正可见时，显式标记 unknown/invalid 而非零残差。
3. **HERO 软几何支持**：冻结清理后可信的原生真实 XYZ 及来源视角，以鲁棒有界残差（可见/最近表面、法向及可见性判定）软支持主体；**不是把所有 HERO 点强行贴上主体，也不是 B1 原网格贴片**。与相对深度来自同一 HERO 预测的两项不得统计为独立信息来源，权重/源有效样本簇要说明。
4. **Base**：只在有合格、同一坐标系的背景 XYZ/平面时启用软附着/非穿透约束；不能以 Ring 平面替代全部背景接触。先审计 G06 等背景资格，G01_004 不能继承 G01_005 的背景，G07 不伪造。
5. **Regularization**：谱系数的频率加权 L2、曲面 Laplacian/弯曲能、异常面面积/翻转、必要时 ARAP 软正则；固定模板拓扑时做几何体积与自交/接近自交报警，避免尖峰/局部折叠。强约束只用于不可信区域及退化保护；不能把真实可见凹凸全部平滑掉。
6. **RGB**：仅作解释和留出视角可视化；第一版不纳入未经光度标定的原 RGB photometric loss，高光、曝光变化不得驱动形变。

**样本预算：**旧 A1 曾固定每源约 32 HERO rays 与 16 相对深度 pair；这对 P3 数十至百余参数的观测秩可能明显不足。请在不重跑 HERO 的前提下，从**原有冻结深度图**、资格 Mask 与冻结 CAD 可见性中预先构建更丰富但固定的分层样本池（如每源 256–1024 个合格候选，按面积/视角/边界与可见性分层，具体数量先由数据决定）；P0–P3/C1/C2 使用同一批注册样本和相同权重，保留完整选取规则、随机种子、来源像素及失败统计；不要在看到优化结果后再换有利像素。低密度与高密度样本可作为预登记灵敏度对照，**固定同一评估分母**。同一视角高度相关的多个像素不得冒充多个独立视角。

**权重：**在 P0 用原始量纲定义尺度（毫米、像素、归一化距离）、稳健损失阈值及白化策略；所有实验臂共享同一初始主权重设定、归一化方式和优化器。可进行事前登记的有限灵敏度组，报告全部而非只挑最优。主指标同时呈现各物理量，不能仅凭不同单位混合后的 `E_total` 得结论。

## 5. 每一步物理信赖域 + 全视角回归检查

必须用实际世界坐标中**最大顶点位移**控制每次候选更新：

`max_j ||X_j(a_new)-X_j(a_old)||_2 ≤ τ_L (mm)`。

对于约 12 mm 主体，初始候选 `τ≈0.1–0.2 mm/accepted step`，但这是试验范围，不是全类别固定绝对步长；记录尺寸归一比例和真实毫米值。可使用 PyTorch+Adam/L-BFGS 或 SciPy 最小二乘，但对**候选几何**实际检验、必要时沿更新方向线搜索/回缩，然后重新评估全部训练视角。普通参数上限不能代替物理位移上限。

接受条件至少包含：全局鲁棒训练目标改善或预声明的有限容差、单个原本合格视角不发生严重破坏、有效 Mask 覆盖不通过删点虚增、环/背景不被穿透、无严重自交/面翻折、可信 HERO 支持不大面积失配。拒绝则记录原因、步长收缩与回退次数；未收敛保留最后安全 checkpoint 而非假装成功。

对于多个视角的冲突，先记录每视角参数梯度/预测位移，再合成同一共享更新：**视角提出建议，唯一模型执行受控联合优化**。保存 per-view loss、gradient cosine/conflict fraction 与哪块几何受影响；不可为了降低某一视角误差直接毁掉其他视角。

## 6. 观测驱动解锁与雅可比（PMGR 的独立研究贡献）

为每个候选新模式 `B_k` 记录：空间支撑/受影响面积、可见 A 视角及其视线分布、各源梯度的方向和幅值、相对于旧参数的独立残差信息、解锁/拒绝与原因。

将不同物理量残差先做一致尺度白化，建立 `J_L=∂r_whitened/∂θ_L`，计算奇异值、有效秩、稳定的条件数（声明阈值、零奇异值截断），并检查

`J_new,independent = (I - J_old J_old^+) J_new`。

数值实现用稳定 QR/SVD 的正交残差而非显式构造巨大稠密投影阵，说明内存/秩截断。识别相机轴向深度不可辨识风险；**相机变量不得解冻**。视角支持至少分成：(1) 多独立视角一致；(2) 仅单视角；(3) 多视角明显冲突；(4) 与现有模式冗余；(5) 完全不可观测。对 (2) 可以更强约束并标注低置信，(3)–(5) 按事前阈值拒绝释放，绝不能为了凑参数数目而开放。

至少提供：不同阶段奇异值谱图、有效秩/条件数表、每个候选模式的 `released/rejected` CSV、可见支持热图、单/多视角梯度对比，以及模式候选数与已激活数。低样本覆盖或 camera gate 不足应形成明确的**研究结论**，不是自动认定算法失败。

## 7. 同条件消融（强制 C1、C2）

从与 PMGR **逐案例逐 seed 完全相同的 P0 椭球**和固定视角/约束出发。提前冻结每臂的计算预算（gradient evaluations、render passes、实际墙钟和显存用量均记录），保证公平，不能以“都跑 1000 epoch”掩盖阶段计算差异。

| 臂 | 参数释放 | 控制目的 |
|---|---|---|
| `PMGR` | P0→P1→P2→P3；频率+观测支持解锁；毫米信赖域 | 完整新路线 |
| `C1_DIRECT_HIGH_DOF` | P0 后立即给出**同一最终候选基池/自由度预算**；不做分阶段增量 | 排除“只是参数更多”解释 |
| `C2_FREQ_ONLY_PROGRESSIVE` | 同样 P0→P3 的数量/频率进度，但**不按观测支持拒绝或调整候选排序** | 隔离观测驱动解锁的贡献 |
| `C3_NO_TRUST`（可选） | 同 PMGR，但不限制每步物理形变 | 验证信赖域稳定性 |

严格可比策略：按完整实验 `P3` **预先固定候选模式全集与最大候选数量**，C1 一开始开放这些候选（物理信赖域及正则仍开启）；若 PMGR 最终未解锁部分模式，C1 的自由度上限仍可高于 PMGR 实际激活量，必须**同时报告候选匹配与实际激活数量的配平子比较**，否则不能把表现差异单独归因于“渐进”。C2 预先冻结“与 PMGR 各阶段同数量预算”的频率顺序，禁止通过观察 PMGR 结局重新挑 C2；另外提供 `C2_count_matched`（仅作补充诊断）以分离“筛选规则 vs 激活数目”的作用。所有臂保留**一致** A/B、同一网格、Mask/Depth 样本池、loss 项、正则、optimizer 基础参数、收敛上限和失败判断，P0 checkpoint 可共享只读但不能重新拟合。

对每臂保存逐阶段/逐预算可比曲线、形变的几何幅度及 B 留出结果。拒绝“某一臂只展示最佳 seed，另一臂统计所有失败”的做法。

## 8. 输出、可视化、统计纪律

每个场景×初值×实验臂，在**同一物理网格坐标系**保存独立可回滚的 `P0/P1/P2/P3` checkpoints、可视化 GLB/PLY、配置 SHA、每步收敛日志、优化前后 `a_k`、退化检测以及可复现命令。保持 P0→P3 连续；禁止把 P1/P2 失败样本从 P3 统计分母中静默移除。

**关键图（本轮对人工仅上传 3–4 张核心 PNG，其他图入目录）：**

1. `Fig1_Progressive_Geometry`: 同场景 P0/P1/P2/P3，相同世界相机、缩放与颜色；可见可信区域/仅推断区域明显区分；黑色 Ring CAD 实体。
2. `Fig2_Heldout_B_Reprojection`: 真实 B RGB + Mask、四阶段首层轮廓 overlay、差异和 coverage/unknown；从相同 A 数据建模，B **不训练**；注明 B 资格条件。
3. `Fig3_HERO_XYZ_Relation`: 原始可信 HERO **真实 XYZ 点云**（按来源染色）与四阶段主体叠合；不可用主体渲染面替代 HERO。背景如有则显示证据，Ring 仍 CAD。
4. `Fig4_Ablation_Conflict`: PMGR/C1/C2 并排的留出曲线、最大位移/拒绝/梯度冲突或典型失败，自交/高频尖峰证据。

完整图集另含真实六视角（A 近似/B 近似/第三真实或近真实/世界 X/Y/Z）、历史 A→B 样式 RGB 预测叠合/差异、阶段 GLB、每源 loss 曲线、模式位移与可观测支持热图、奇异值谱、连续迭代动画可选。六视角 3D 按现有 `real_p0_renderer.py` 风格，颜色一致，清楚标注“真实 XYZ”与“优化主体”。

**固定指标/分母：** 预注册 A/B 和有效 Mask/深度像素资格；输出 Mask IoU、contour distance、Mask 外像素比例、首层深度偏差、相对深度和可信 HERO 点到主体的 robust 距离分布；同时输出每源覆盖率、未知/遮挡/失效计数、自交/翻折/尖峰、相邻阶段最大 mm 位移、网格长宽高、不同种子曲面距离（需配准坐标已固定）、参数预算/已放行数、Jacobian 有效秩及条件数、单视角恶化程度。**只统计相同资格和有效域上可比误差；变化的可见采样 hit 数要做 common-ray paired evaluation，不能直接将不同 N 的平均误差宣布显著变好。**

所有场景有不可变 `case_id`、`source_video`、`A_refs`、`B_ref`、`qualification_label`；区别严格合格、条件合格、压力测试和无法评价，不混合成“真实三类通用成功率”。所有运行都要出一行，包括资源失败、坐标门失败、自交中断、未激活模式、Gate 失效、B 没有可用视角的 `NA`；绝不为了美观改分母。

## 9. 一次完整执行的调度次序（无需逐阶段人工审批）

**阶段 A：审计+冻结协议（同次任务一气执行）。** 将基线分支/commit、输入来源和 SHA、K/c2w、A/B、E1/E2 初值、合格 Gxx、相机与遮挡规则，写为 `01_PROTOCOL.md`、`02_SOURCE_AND_RENDERER_AUDIT.md`、`config/LOCKED_PROTOCOL.json`。在新分支首次提交协议与可执行预检。不能使用未知的跨视频外参。

**阶段 B：实现核心代码与 P0 数值测试。** 低维谱形变基生成、GPU 可微网格渲染、CAD depth/occlusion 与原 A1 解析及 A→B 投影数值对照、固定 Mask/Depth/HERO 样本池、物理信赖域、回退、几何自交检查、模式支持与 SVD。包含合成椭球/受控局部凸起的确定性单测，确保新代码允许正确梯度传回几何而不重新引入 camera optimization。若门失败只冻结相应臂并出报告，其他场景继续。

**阶段 C：从 P0 开始连续执行 P1/P2/P3。** 对 G01/G06/G07/G08 可执行数据以及新找到的合格 Is，按在场景层冻结的 E1/E2 初值及多种固定种子，跑完各阶段与相应评估；阶段末保存安全 checkpoint。没有足够观测支持要明确 reject modes，但继续试探 P3 候选并给解释。

**阶段 D：C1/C2 全部对照。** 同一 P0、视角、样本、候选池与计算约束，完成 C1 直接高自由度和 C2 无观测支持解锁；可选 C3。即使某 arm 失败，也有失败表和同等预算的其他 arm 结果。

**阶段 E：完整科学复核。** 固定 B 留出回归、六视角 3D、HERO 真实 XYZ、A→B、GLB、模式图、J 谱、形变过程、跨组分层与失败病例，验证图上尺寸与颜色图例不误导。保存轻量核心图并按仓库规范推送（3–4 PNG）。

**阶段 F：报告与总结。** 最终报告真实反映七个问题：① 能否连续突破椭球；② 何阶段首次得到留出改善；③ 何阶段开始不稳；④ PMGR 是否优于 C1；⑤ 观测驱动解锁是否优于 C2；⑥ 现有 Camera Gate/Mask/HERO/背景到底支持哪些形变复杂度；⑦ 后续应增加自由度还是转向经另行授权的 B1 可信 HERO 贴片。必须给出**支持/反证/证据不足**三态而不是二元成功故事。

## 10. 独立目录与交付结构

建议（具体文件可补充，禁止覆盖既有项目）：

```text
experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001/
  00_APPROVED_CODEX_TASK.md
  01_PROTOCOL.md
  02_SOURCE_AND_RENDERER_AUDIT.md
  03_GEOMETRY_AND_OPTIMIZER.md
  04_IDENTIFIABILITY_AND_CONFLICT.md
  05_FAILURE_LEDGER.md
  TECHNICAL_REPORT.md
  REPRODUCE.md
  config/LOCKED_PROTOCOL.json
  code/{inputs,mesh_basis,camera_renderer,losses,trust_region,observability,run,validate,figures}.py
  metrics/{INPUT_QUALIFICATION,CASE_ARM_SEED_RESULTS,STAGE_METRICS,MODE_UNLOCK,
           JACOBIAN_SPECTRUM,PER_VIEW_LOSS,FAILURES,PROVENANCE}.*
  figures/{Fig1_Progressive_Geometry,Fig2_Heldout_B_Reprojection,
           Fig3_HERO_XYZ_Relation,Fig4_Ablation_Conflict}.png
  figures/full/...
  assets_index/{CHECKPOINTS,GLB,LOCAL_DATA_SOURCES}.json
```

保存真实脚本/包版本/CUDA/seed/命令及输入哈希；大网格 checkpoints、私有原图、原始深度、高权重文件可以保存在本机**任务专用**目录并在 Git 记录 SHA 与相对索引，不能把敏感路径/口令、巨量数据上传 Git。已有本地 4090/远端 GPU 如需用，只使用执行端原有正规 SSH/许可和用户已配置的凭据，不输出口令、不将训练所需的私有大文件在无授权条件下迁移到公共空间。

每完成 P0+renderer、P1–P3、C1/C2+报告，可做有意义的分段 commit；最终向仓库同步本任务分支，不覆盖 main，不强制推送。若权限错误，停止 push 并提供本地 commit/hash/补丁位置，不绕过集成权限。每个被判无用的实验只在报告列“后续清理候选”，本轮不删除任何历史文件。

## 11. 完成时回复人工的格式（必须）

1. `TASK STATUS`：`COMPLETED` / `PARTIAL_WITH_EXPLICIT_FAILURES` / `BLOCKED`，严禁将任务文档完成说成实验完成。
2. `REPO`：分支、commit SHA、新实验目录链接、是否成功同步远端。
3. `EXECUTION COVERAGE`：每个场景× E1/E2 初值× PMGR/C1/C2 的 P0/P1/P2/P3 状态矩阵和固定分母、资格标签。
4. `QUANTITATIVE`：训练 vs B 留出、几何异常、可信 HERO、J 有效秩、mode unlock、信赖域拒绝、预算公平表，指出统计不可比部分。
5. `CORE VISUALS`：直接给人工最关键 **3–4 张仓库真实 PNG 路径**，简短解释每图能说明什么，其他图索引/六视角/GLB 在目录中。
6. `SCIENTIFIC VERDICT`：按七个问题分别判定结果支持程度，尤其是否到达 A2/未来 B1 的合理起点；**不自动开启 B1/B2**。
7. `FAILURE/UNRESOLVED`：坐标核验、Is 合格数据不足、G01/G08 资格、模式病态、残差耦合、GPU/权限等必须如实留下。

**人工已批准以上完整 PMGR 实验周期；现在请在已授权且输入资产齐全的 Codex 执行环境中真正实现、运行并上报，不要停在‘方案已设计’或 P1 小试验。**
