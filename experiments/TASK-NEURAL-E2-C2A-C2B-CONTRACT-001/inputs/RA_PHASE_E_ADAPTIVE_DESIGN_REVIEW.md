# RA_PHASE_E_ADAPTIVE_DESIGN_REVIEW

**项目**：Reference-Ring Anchored Visible-Surface Reconstruction of Polyps  
**身份**：研究架构师（RA）独立设计审查  
**日期**：2026-10-31  
**状态**：`DESIGN REVIEW / SCIENTIFIC RECOMMENDATION / NO GPU AUTHORIZATION`  
**研究约束**：Ring-First `K,c2w`、Ring CAD、HERO 权重、历史 P0、Dxy 固定；无 GT/Oracle 选模；不将推测的背面称为真实可见面；本报告不授权 Codex 或 GPU 运行。

## 0. 摘要与独立裁决

**推荐一条正式主线、一个独立竞争方案、一个仅作技术参考的辅助方案：**

1. **正式主线 S：Polyp-only Neural SDF + fixed CAD Ring + optional observed Background occluder**，使用冻结 MonoSDF 的成熟主体，仅在 adapter/ray/mask/loss 上做最小修改：ROI 限段 Polyp 不透明度、Ring CAD 首次射线交点截断、Mask 边界/可靠空域约束、带来源和互相关控制的多参考 HERO Z 深度。Ring 和 Background **不作为可学习的 Polyp 表面**。该设计的首要科学问题不是“多对象模型”，而是“已有多参考观测能否约束同一未知物体的可见表面”。
2. **独立竞争 M：MapAnything 结构化几何条件多视角推理**。允许同场景不同参考提供 RGB/K/冻结 Pose/轴向 depth_z，以及经严格来源投影的 Raw/Cleaned/F1/F2/F3 的互斥候选深度层；另可在确实可见 Ring 的像素提供精确 CAD 射线深度。保持官方原生 infer 模型与输入白名单；不得声称可以直接输入 Mesh/PLY、多层深度、Mask 字段或任意 confidence。不得把 Arm M 当 Arm S 初始化器或物理真值。
3. **辅助思想 O：ObjectSDF++ 的 instance-aware、occlusion-aware opacity**，仅借鉴数学机制与已知对象显式组合；不作为当期第三个需训练的大型物体网络。完整多对象学习和 Ring 重新学习进入独立探索候选，不抢主线预算。

**最便宜且最关键的小设计：替换 E0 失效的整射线 `weights.sum()` Mask 预测，改为排除终端吸收分支、受固定 CAD/可信背景遮挡截断的、具有梯度的 Polyp 有限射线段可见性监督。** 这是后续所有学习实验的**先决条件**，但其收益目前仅是明确的工程/数学预期，尚无 GPU 实验证据。

---

## 1. 真实 GitHub E1 审计（逐文件）

**实验分支**：`exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001`  
**目录**：`experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/`  
**报告**：[TECHNICAL_REPORT.md](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/TECHNICAL_REPORT.md)；[失败记录](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/FAILURE_LEDGER.md)。

直接核查代码 `code/sdf_contract.py`、`code/map_contract.py`、`code/source_audit.py`、`CODE_REUSE_E1.csv`、`SDF_GATE_STATUS.json`、`MAP_GATE_STATUS.json`、`REFERENCE_COVISIBILITY.csv`、`E1_SOURCE_DAG.json`、`MAP_OFFICIAL_INTERFACE_EVIDENCE.json`、`SDF_OFFICIAL_SOURCE_BEHAVIOR.json` 和 loss 合同，不仅依据报告结论。

### 1.1 已实际证实

- **来源与资格**：36/36 历史参考 native 文件可核对；47 个 HERO 上游 RGB 身份、154 条依赖边。G01_004 和 G01_005 各有 3 份冻结核心参考；4 个物理组 5 段视频受审，**E1 模型前向/训练为 0/4 组**。真实严格全流程 holdout 仍为 0；G07 相机不合格，只能作为压力组；三张照片 K/pose 未认证。
- **几何转换通过不等于神经重建成功**：36 基础坐标合同通过，合成 CAD 遮挡测试通过；这些仅证明转换/测试流程。无新 SDF 或 Map 表面，也无新物理精度。
- **MonoSDF 包装失效由代码支持**：`sdf_contract.py` 静态核对 MonoSDF 官方 `ErrorBoundSampler/UniformSampler`、`ImplicitNetwork` 中吸收球和 `LaplaceDensity` 行为，计算射线段、SDF 零交叉及终端不透明度；没有执行模型/官方 GPU sampler。E0 归一化相机中心约 3.2714、3.8705，吸收边界半径 2.5；但**“相机在球外”本身并非充分失败证明**，真正问题是射线前端在错误几何场内产生密度，以及官方全射线终端吸收使 `weights.sum(-1)` 几乎恒为 1。E1 CPU 预测 mask BCE=**3.837196032**，E0 实际400步恒定 **3.837196350**。两种更合理几何域候选并没有修复 mask 定义，当前状态 `ADAPTER_INVALID/STOP_SDF_BRANCH`。
- **当前真正接线的 SDF 损失：没有**。E1 只做 CPU 合同。`metrics/SDF_FUTURE_LOSS_CONTRACT.csv` 明确：有限ROI Mask `CPU_GEOMETRY_READY_NOT_WIRED`；HERO 多参考 `CPU_GEOMETRY_READY_NOT_WIRED`；RGB / 冲突权重 / Eikonal `FUTURE_REQUIRED`；MASt3R 锚点 `NOT_IMPLEMENTED`；CAD `CPU_GEOMETRY_READY_OUTPUT_GATE_ONLY`。E0 曾有 RGB/Mask/双深度等训练项，但适配和约束不满足科学任务；不能冒充 E1 已完成多视角监督。
- **深度冲突客观存在**：`REFERENCE_COVISIBILITY.csv` 中 G01_004 ref03→ref08 在投影共同深度候选 21,494 个样本上的中位绝对差约 **0.768 mm**、冲突比例约 **90.4%**（按该实验固定门槛）。方向、参考源/点数、遮挡、HERO 共享父系使其**不是独立几何误差真值**。G01 同视频核心参考镜头光轴差：004约 8.74°–17.56°，005约 4.57°–9.63°；共视候选不等于有效物理对应。
- **MapAnything CPU 接口适配已完成**：`map_contract.py` 使用官方 utils `preprocess_inputs`, `validate_input_views_for_inference`, `preprocess_input_views_for_inference`，复用旧投影/原三角面渲染；32/32 局部几何→合法 `depth_z` 转换和 8 项原生 M0–M3 CPU 配置通过，**没有新模型前向**。来源点/三角面 ID、Ring 遮挡/UNKNOWN、无效深度为 0、m/mm、K resize、冻结 c2w 均已记录。
- **Map 官方白名单经源码证明**：`img`, `data_norm_type`, `depth_z`, `intrinsics` **或** `ray_directions`, `camera_poses`, `is_metric_scale` 等工具字段；不能原生附加 `valid`, arbitrary `confidence`, PLY/GLB、多个同 RGB 深度层。历史 F1/F2/F3 只是和 HERO 存在父系依赖的深度先验，**同源重复不能冒充独立视角**。
- **E0 失败对照保留**：Map M3 旧缓存 Ring→CAD 中位误差约 22.348 / 21.941 mm，第二参考输出 pose 相对冻结 pose 平移差约 9.94 mm；E1 没有改尺度或重跑 Map，不证明 Map 作为方法一定失败。

### 1.2 证据等级

| 对象 | 已证实工程事实 | 已观察到的几何问题 | 尚未经科学验证 |
|---|---|---|---|
| SDF | 包装吸收与全射线Mask错误；来源/坐标可追溯 | E0 0张观测支持面 | Polyp-only 能否稳定恢复细柄/薄曲面；分割监督是否提升准确性 |
| Ring | 固定 CAD 可精确作合成 Z-buffer 遮挡 | 历史融合有过 CAD 穿插 | CAD 遮挡/穿插直接加入训练后是否提升息肉几何 |
| HERO | 多参考深度存在显著差异 | 既有点云错层和不连续 | 冲突权重是否显著改善真实未用视角 |
| Map | 合法几何深度适配器CPU通过 | E0 Metric contract失败 | 多参考+Ring条件是否能在真实内镜域恢复更优场景 |
| 其他组 | G06/G08/G07有来源资产 | 资格分层不同 | 四组实际神经模型跨组表现，E1全部未运行 |

### 1.3 源码复用边界

- `code/sdf_contract.py` 是 **NumPy几何合同/官方源码静态审计**，不是修复后的训练器。不能直接以该文件 `PASS` 宣称真实梯度可用。
- `code/map_contract.py` 已能从 Raw/Cleaned/F1/F2/F3 单层几何得到一张相机视角合法 `depth_z` 及 provenance，建议保留不改；不能误造第二套反投影和Mesh光栅化代码。
- 真实相机、原 XYZ、MASt3R匹配、CAD Z-buffer、`visualization/real_p0_renderer.py`、原三角面真实 A→B 已由 `CODE_REUSE_E1.csv` 指出入口。对 `SameCameraScene` 和 CAD 遮挡可保留只读 wrapper；添加神经 loss 只允许 **薄 adapter**。

---

## 2. 相关论文：具体可借鉴与不该照搬的内容

| 论文、时间 | 论文已证实的方法 | 本项目最合适的复用 | 不适用处 |
|---|---|---|---|
| **MonoSDF**, NeurIPS 2022，[arXiv](https://arxiv.org/abs/2206.00665)，[官方代码](https://github.com/autonomousvision/monosdf) | 预训练几何先验深度/法向约束神经隐式场 | 原底座、SDF/可微体渲染、深度监督 | 当前吸收球和 mask wrapper 不合格；它没有自动解决Ring物体身份 |
| **VolSDF**, NeurIPS 2021，[arXiv](https://arxiv.org/abs/2106.12052) | SDF→Laplace CDF密度和有误差界的射线采样 | 数学检查有限区间密度/透射与SDF几何 | 终端吸收策略不等于可用的对象实例轮廓概率 |
| **NeuS**, NeurIPS 2021，[arXiv](https://arxiv.org/abs/2106.10689) | 更适合几何零水平集的体渲染 | 在不放弃MonoSDF底座前用于公式/梯度参考 | 直接切换整套NeuS有额外工程成本 |
| **ObjectSDF**, ECCV 2022，[arXiv](https://arxiv.org/abs/2207.09686) | 多对象SDF组合与实例语义监督 | 多对象标签与每条射线可见对象身份概念 | 为已知Ring训练一个自由SDF没有必要 |
| **ObjectSDF++**, ICCV 2023，[arXiv](https://arxiv.org/abs/2308.07868)，[代码](https://github.com/qianyiwu/objectsdf_plus) | 遮挡感知对象 opacity、避免对象互相侵占的正则 | **本轮最重要的现成数学参考**：instance opacity 与几何非穿插 | 不必整个框架与多自由对象网络同时移植；原代码环境较重 |
| **SparseRecon**, ICCV 2025，[arXiv](https://arxiv.org/abs/2508.00366) | 稀疏视图特征一致性、基于不确定性的深度约束 | 深度冲突分层、对低纹理/遮挡区别对待 | 论文的不确定性权重定义与本项目的来源质量并不天然相同；需独立消融 |
| **LightNeuS**, 2023，[arXiv](https://arxiv.org/abs/2309.02777) | 内镜相机运动照明变化的显式模型 | 解释为何不能硬把RGB残差当纯几何误差 | 其封闭结肠腔体先验不可直接用于开放息肉场景 |
| **NeuralUDF**, CVPR 2023，[arXiv](https://arxiv.org/abs/2211.14173) | 无符号距离场表达开放拓扑 | SDF封闭未知背面的独立对照 | 另一个重建底座；当前不优先切换 |
| **MapAnything**, 3DV 2026，[arXiv](https://arxiv.org/abs/2509.13414)，[代码](https://github.com/facebookresearch/map-anything) | 图像、位姿、深度、partial recon的统一feed-forward公制几何推理 | 独立 Arm M 的原生多视角输入、派生深度适配 | 不支持任意Mesh字段、不会自动锁死输出pose/满足本项目mm准确度 |

**严肃的创新边界**：Mask感知采样、CAD可见性、对象Opacity、稳健深度并非本项目独创。若未来形成论文贡献，其候选新意在于**把已知CAD实体、冻结Ring公制相机、受物体身份约束的有限射线、互相关HERO来源可靠性**融为一套针对内镜的可证伪系统。仍须实验证明。

---

## 3. 候选设计筛选表（独立批判）

**记号**：证据=已有论文/现有代码/本项目效益；复杂度含改造与调试；可推广性指能否迁移到其它已知标志物与未知软组织场景。

| 设计 | 针对现实失败 | 预期收益 | 现有证据 | 复杂度 | 风险 | 推广性 | 决定 |
|---|---|---|---|---|---|---|---|
| A1 Polyp-only SDF | 全景混淆Ring/背景，监督对象不清 | 减少自由度、集中几何 | 对象方法成熟；未在本项目验证 | 低-中 | 无效背景负约束或闭合未知背面 | 高 | **主线** |
| A2 Mask分区采样 | E0轮廓不变、背景被错监督 | 更有效训练信号 | Mask已有；数学直接 | 低 | 只采前景会膨胀 | 高 | **最高优先** |
| A3 有限ROI遮挡感知opacity | E0全射线终端吸收 | 恢复有梯度的真正前景Mask监督 | E1精确定位；ObjectSDF++ | 中 | clamp/积分截断不连续及模型偏差 | 高 | **硬门禁** |
| B1 固定Ring CAD射线首交点 | Ring遮挡误判、历史穿插 | 正确监督谁在谁前；避免假表面 | CAD合成遮挡已验 | 低-中 | ring mask误分割、接触误罚 | 高 | **主线** |
| B2 解析Torus/CAD SDF碰撞 | Ring实体可用但未训入 | 非穿插与公制局部关系 | 解析几何成熟；项目未训练 | 低-中 | Ring不接触时约束稀疏 | 中-高 | **主线次级** |
| D1 多来源稳健HERO-Z | 0.2–1mm级源差和错层 | 降低冲突主导、保留独有面 | MonoSDF/SparseRecon，E1冲突数据 | 中 | 不能以预测自证；互相关重复 | 高 | **主线** |
| D2 MASt3R可靠anchors | 共享对应不足，纹理变化 | 局部消除歧义 | 已有缓存；视角稀疏 | 中 | 锚点数量少、物理身份错 | 中 | **第二批条件加** |
| M1 Map几何条件+Raw/Cleaned/F1/F2/F3 | E0只用两RGB/未利用大量已有模型 | 快速检验feed-forward整合能力 | E1 32/32 CPU合同通过 | 低-中 | 预训练域偏差、尺度漂移 | 高 | **独立竞争** |
| M2 CAD Ring 深度条件 | 模型没显式使用公制Ring | 让Ring成为已知几何条件 | 官方 depth_z 合法；尚无前向 | 低 | 对Ring测试发生信息泄漏/同义反复 | 中-高 | **竞争消融** |
| C2 Two-object free SDF | 已知Ring被重复学习 | 不明确，更多自由度 | ObjectSDF已有先例 | 高 | 形态漂移/伪影/算力 | 中 | 淘汰主线 |
| C3 Shared multi-object net | 想共享特征提升Polyp | 无现有直接证据 | 学术存在，场景不匹配 | 高 | 把简单问题复杂化 | 中 | 淘汰主线 |
| R1自由Ring SDF | 重新估计已知CAD | 无明确新增Polyp信息 | 可作模型健壮性对照 | 中-高 | 循环验证、显式误差变大 | 低 | 独立研究候选 |
| R2 CAD约束可学Ring | 校正CAD轻微制造/装配误差 | 目前无已证实需求 | 无本项目独立真值 | 中-高 | 新的自由度吸收相机/息肉错误 | 低 | 延后 |
| R3 Ring辅助预测头 | 几何多任务学习 | 可能加快收敛 | 尚无具体实证 | 中 | 容易重复学习确定信息 | 中 | 延后 |
| 全局封闭、生成式补背面 | 所有视角不足 | 外观更完整 | 形状先验已知有帮助 | 高 | 假几何、误导面积/体积 | 中 | 独立Phase F |

---

## 4. 主线：Polyp-only Neural SDF + 固定 CAD + 可信背景遮挡

### 4.1 几何对象和坐标

在**单视频冻结 Ring-First 坐标**内（G01_004和005分开）：

- 唯一学习几何：`f_θ(X)` 为 **Polyp** 的神经SDF，零水平集 `S_P={X:f_θ(X)=0}`。对于真实物体若可闭合可建立内部SDF，但**无真实支持的封闭面必须标 `PRIOR_ONLY/UNKNOWN`**。
- Ring：固定物理CAD实体 `R_CAD`，已知相机和场景变换；用射线首交点 `t_R(u)` 与有符号实体距离 `d_R(X)`，**不学习 Ring**，不将 Ring 作为 Polyp 正监督。
- Background：真实历史XYZ/开放Mesh仅为条件性可见遮挡代理；有可靠三角面可获得 `t_B(u)`，没有有效投影深度的射线标 `UNKNOWN`，**不将Background模型当真值，也不训练新Background SDF**。
- 真实RGB、Polyp/Ring三类分割、各源HERO axial Z、来源ID、相机K/c2w，均严格同来源和冻结。

参考 `R10` 真实CAD的中心线半径 `R=5.6mm`、管截面半径 `r=0.6mm`；R5对应中心线 `3.1mm`、管半径 `0.6mm`（以仓库CAD为最终权威）。理想刚体正圆环在其局部坐标下有解析SDF：

\[
d_R(x,y,z)=\sqrt{\big(\sqrt{x^2+y^2}-R\big)^2+z^2}-r.
\]

这对理想torus成立。若实际CAD形状、偏置或放置与数学torus不同，以**CAD网格距离/射线求交**为准，不静默用torus取代经过标定的CAD。

### 4.2 真实相机射线与完整域

从像素 \(u=(u,v,1)^T\)、相机 \(K_i\)、冻结 \(T_i= [R_i|c_i]\) 出发：

\[
\tilde d_i(u)=R_iK_i^{-1}u,\quad
\bar d_i(u)=\tilde d_i/\|\tilde d_i\|,\quad
X_i(t)=c_i+t\bar d_i,\; t\text{为射线距离(mm)}.
\]

已存在 HERO 深度 \(Z^{HERO}_i(u)\) 是轴向Z，不是射线距离：
\[
X_i^{HERO}=c_i+Z^{HERO}_i(u)\,\tilde d_i(u),\quad t^{HERO}=Z^{HERO}\|K_i^{-1}u\|.
\]

网络坐标可取 `x_net=(X_mm-O_mm)/s_mm_per_net`，但 **K,c2w和Ring毫米坐标本身不变化**，且需双向回算。

采用两次单独检查：① ROI/camera ray interval 几何有效；② 神经 opacity 是否真正区分Polyp前景/可见背景。不要把二者视为同一个PASS。

### 4.3 终端吸收的最小修复路径（硬门禁）

E1证明旧公式 `mask_pred = sum_{k throughout full ray} weights_k` 在官方远端吸收下饱和。**不可再调用旧公式作为Polyp Mask。**

在冻结真实相机中，先定义物体可能出现的可信裁剪区间 \([t_a,t_\Omega]\)，并求已知遮挡首交点：
\[
t_{cap}(u)=\min\{t_\Omega(u),t_R(u),t_B(u)\},
\]

其中只对可靠、有来源的背景三角面引入 \(t_B\)。**当Ring处于图像上被Polyp遮挡的后方时，Polyp预测应在Ring之前成面；Ring预测不取代Polyp标签。** 当背景几何未知时，不凭空把整个远方当可靠负例。

定义只来自 **Polyp SDF的有限段密度** \(\sigma_P(f_\theta(X(t)))\)：
\[
\boxed{\alpha_P^{vis}(u)=1-\exp\left[-\int_{t_a(u)}^{t_{cap}(u)-\epsilon}\sigma_P(f_\theta(X_i(t)))\,dt\right]}.
\]

离散情况（不使用终端背景吸收）：
\[
\alpha_P^{vis}=\sum_{k\in\mathrm{ROI},t_k<t_{cap}} T_k^P\,[1-\exp(-\sigma_{P,k}\Delta t_k)],\quad
T_k^P=\exp(-\sum_{j<k}\sigma_{P,j}\Delta t_j).
\]

注意网络的 **raw SDF head** 与 MonoSDF 外侧 `min(sdf,R-||X||)` 吸收裁剪并不相同。Polyp轮廓计算必须取合格域内只归属于Polyp的密度，不得把背景/球终端吸收积分进Polyp。只改一个薄loss/ray adapter，**必须写合成球体前景/负例与Ring先后场景的梯度测试**。

Mask损失使用：
\[
L_{sil}=\frac{1}{N_{vis}}\sum_{u\in\mathcal V} q_M(u)\operatorname{BCE}(\alpha_P^{vis}(u),M_P(u)),
\]

其中 \(\mathcal V\) 包含具有可靠前景和可靠空域约束的射线。Ring遮挡后方的 `M_P=0` 不能被当作“整个射线空间没有Polyp”：只能说明 **Ring之前的可见区间无Polyp**。`M_P=1` 表示必须在首次可靠遮挡之前出现Polyp。若场景需要处理多个Ring交点，使用**首次正向相交**；自遮挡由Polyp SDF体渲染自身处理。

**CPU可证伪样例（零训练）**：球体位于Ring前、球体位于Ring后、无Polyp/Ring单独、细柄近背景、射线完全错过ROI、真实样本掩膜前景及背景；改变球半径/球心，验证 \(\alpha\) 随参数连续变化且 finite differences 与autograd（需后续授权可微CPU单测）一致，不被远端吸收固定为1。独立检查 \(N_{valid},N_{occluded},N_{unknown}\)，不删除失败射线以人为制造PASS。

### 4.4 由分割定义五类ray，不只裁剪训练图

| 类别 | 采样优先级 | 监督含义 | 具体防错 |
|---|---|---|---|
| `P_INTERIOR` | 高 | 可见射线段必须有Polyp前表面；辅以HERO Z | 高光/错误Mask降权；不把所有像素共享一个深度 |
| `P_BOUNDARY_BAND` | 高 | 真轮廓附近的前景/背景不透明度转换敏感；可加边界距离一致性 | 轮廓不是跨视角固定3D点；不能拿边界对点点匹配 |
| `VISIBLE_NONPOLYP` | 中 | 到可靠背景深度前为Polyp自由空间；约束不合理膨胀 | 若看不到真实背景深度，仅有限的可信空间可被标空 |
| `RING_OCCLUDED` | 中/审计 | Ring首次交点前应不出现可见Polyp；Ring后不可负监督 | Ring是已知遮挡对象，不训练Ring为Polyp |
| `UNKNOWN/LOW_CONF` | 低/不监督 | 作为未知记录；若有可靠独立来源可更新资格 | 不把未认证区域强制变空或补全 |

采样优先级可以在固定数量的 `ray budget` 中按**区域配额**分配，而不是改变目标数据本身的真实分布；梯度和损失可按区域概率作 `1/p_sample` 重要性校正或单独归一化，避免“边界采多了”本身改变统计学习目标。区域配额与阈值必须先在非评估训练源冻结。

**Mask的独立价值**：正像素约束物体存在，可靠负像素约束自由空间，CAD遮挡区域避免假负，边界区域帮助定位表面投影。**Mask不能确定像素真实深度**，所以必须同时使用 HERO 和多视角。

### 4.5 固定Ring CAD：两个训练期算子与一个纯验收项

**训练算子1：已知遮挡上界**。前述 \(t_R(u)\) 用固定CAD首交点。Ring不是可学习几何，\(t_R\) 对网络参数是常量，但会改变允许Polyp渲染和Mask损失的射线段，**梯度真实流向 Polyp SDF**。这直接利用已知物理世界，不增加训练自由度。

**训练算子2：实体非穿插**。如果有受支持的预测Polyp表面采样点 \(X_s(\theta)\)，用Ring有符号实体距离定义：
\[
L_{penetrate}=\frac{1}{N_s}\sum_{s}\left[\max(0,-d_R(X_s(\theta))-\epsilon_{tol})\right]^2.
\]

接触允许（\(d_R\approx0\) 不受惩罚），仅惩罚实质穿入CAD实体；\(X_s\) 必须以**可微渲染命中点/有梯度的表面点表达**形成，如果从离线Marching Cubes抽离参数，loss 不能回传。也可以将已知Ring实体内部采样点 \(X_R\) 的 Polyp SDF作为 `exterior` 的 soft penalty（例如 \(\mathrm{softplus}(-f_\theta(X_R)/\tau)\)），但前提是符号/拓扑有效且不误罚物理接触；此项与近表面穿插采用**一项即可，勿双重加权**。

**验收项**：Ring投影/源Mask、CAD穿插统计、固定尺度、真实A→B，不从这项评价反向挑参数。若CAD Ring已经作为Map输入先验，Ring近距误差仅是**条件自洽检查，不是独立Polyp精度证据**。

解析torus、已知 CAD 网格 SDF/BVH 树和可微接近查询可供选用；优先复用项目现有 CAD Z-buffer 与距离例程。无必要开发/训练Ring NeRF。

### 4.6 多参考HERO进入统一SDF：来源相关、遮挡感知、避免平均错误

对于真实参考 \(i\) 与像素 \(u\)，只在 `P_INTERIOR` 且有合法可见深度时取 HERO Z。使用统一SDF渲染轴向预测深度 \(\hat Z_i^P(u;\theta)\)；若在合法ROI没有命中Polyp，不能用零值与HERO做深度回归，而应由Mask占据损失与未命中标签处理。

\[
\boxed{
L_{depth}=\frac{1}{|\mathcal I|}\sum_{i\in\mathcal I}\frac{1}{W_i}\sum_{u\in\mathcal V_i}
 w_{i,u}\,\rho_\delta\!\left(\frac{\hat Z_i^P(u;\theta)-Z_i^{HERO}(u)}{s_i}\right),\quad W_i=\sum_{u\in\mathcal V_i}w_{i,u}.
}
\]

- \(s_i\) 为预先固定的物理单位归一化尺度；训练损失归一化只用于稳定权重，不是“GT标尺拟合”。
- 所有参考在**同一视频Ring局部世界系**内解释同一个 `f_θ`，不是对每个参考各训练一张SDF。
- `w_{i,u}` 由可追溯的来源质量代理预先冻结：相机条件、真实Mask置信、是否可靠Cleaned结构、局部法向/掠视角、可信跨图像对应、CAD遮挡、**排除被遮挡/非共视之后**的跨参考Z冲突。它不是科学真值概率。
- 相互不一致时不要简单取低Z、取中位数或按密度加权合成真值；稳健 \(\rho\)（Huber/Charbonnier）先抑制离群点。存在结构化深度偏差时，差异可报告为**未解决冲突**，不能让全体权重自由降为0。
- 按独立原RGB/HERO父系进行**相关性分组或每源权重封顶**。Raw/Cleaned/F1/F2/F3来自同一推理，应作为互斥几何先验消融，不可计为五个相互独立观测。
- 对只在一个视角看见的新增侧面：**不因没有第二套一致深度而自动降权到0**；依靠该视角清晰图像/单视图预测、Mask、Ring可见性约束并标记 `SINGLE_VIEW_OBSERVED_SUPPORTED`。
- 对重叠侧面：采用冻结的几何对应+遮挡检查后再计算残差；如果全不一致而不可判别可靠性，则公开 `CONFLICT`，不要用神经输出自身作为权重证据实现自我证明。

**可选低成本增强（第二批）**：以已有 MASt3R/LightGlue 的真实多视角匹配约束渲染命中位置重投影：
\[
L_{anchor}=\sum_{(i,u;j,v)\in\mathcal A_{valid}}\omega_{ij}\,
\rho\big(\|\pi_j(X_{i,\theta}(u))-v\|\big),
\]
要求物理同一点、视差、非高光、没有Ring遮挡及正确几何可观测性；历史缓存如无法满足则 `NOT_IMPLEMENTED`，不使用随机同位置最近邻伪造锚点。

### 4.7 RGB与真实可见支持域

第一轮RGB可以只对 `P_INTERIOR`、清晰有效像素采用稳健颜色损失，Ring和背景的颜色不应由Polyp外观网络承担。由于内镜跟随光照，RGB误差不能单独决定几何（LightNeuS提示）。RGB、Mask和HERO的损失均需打印**真正采样射线数、每源有效样本数、每项gradient norm、loss曲线**。

统一SDF的零水平集在未观察背面可能自然闭合。正式输出采用六类标签：`MULTI_VIEW_OBSERVED_SUPPORTED`,`SINGLE_VIEW_OBSERVED_SUPPORTED`,`CONFLICT`,`RING_OCCLUDED`,`PRIOR_ONLY`,`UNKNOWN`。支持域必须依据实际相机可见性+来源支持+深度/轮廓约束定义，不得只根据模型预测 confidence；背景未知不强制补全。

---

## 5. 四种对象表达的裁决（C1–C4）

| 架构 | 能解决的真实问题 | 额外自由度/风险 | 工程代价 | RA结论 |
|---|---|---|---|---|
| **C1 Polyp-only SDF + fixed CAD Ring + 条件背景遮挡** | 清晰对象监督；CAD几何确切；多深度统一Polyp | 背景缺失时空域边界弱、未知背面仍可能闭合 | **最低** | **首选主线** |
| C2 独立Polyp SDF与Ring SDF | 若Ring未知可解释多对象几何 | Ring真实形状已知，重复估计产生可补偿漂移 | 高 | 不选 |
| C3 共享backbone多对象输出 | 若多物体皆未知，能共享形状表征 | 增加共享特征耦合/训练难度 | 高 | 不选 |
| **C4 Hybrid：Polyp SDF + CAD Ring + 已观测背景网格/点云** | 用Ring+背景进行正确可见性裁剪、对象身份清晰 | 背景点云不全，需UNKNOWN资格 | **低-中** | **C1的工程落地形式** |

Ring独立实验 R0–R3：`R0固定CAD` 是默认；`R1自由Ring SDF` 只有在独立CAD测量/制造偏差研究才有价值；`R2 CAD约束可学Ring` 仅在存在**独立可测的实际CAD偏差**才允许；`R3 Ring辅助任务` 用于验证共享网络对Polyp学习是否带来明确净增益，必须和同等训练预算的 R0 做独立消融。否则都容易产生循环验证：把已知CAD作为训练目标，再以是否接近同一CAD宣布“学会了几何”。

---

## 6. 独立竞争 Arm M：MapAnything的合法项目化利用

E1的 `map_contract.py` 已验证官方合法白名单和32个几何输入转换，明确不存在任意附加字段通道。这是极重要的“直接复用的工程基础”。同一原RGB仅能**选择一份条件深度层**，如 HERO native/Raw/Cleaned/F1/F2/F3；不同参考视角各有自身来源深度。若F1/F2/F3投影到另一真实相机生成深度，需保留其点/面原始身份、三角面有效性与遮挡，未知保持0而非形态填补。

### 6.1 两种可互斥比较的几何条件

- **M-H（HERO基础条件）**：每一真实观测帧 `img+intrinsics+frozen camera_poses+depth_z(HERO)`；只使用同视频经过认证的 pose，毫米到米转换，追踪来源帧。
- **M-F（历史重建条件）**：在相同真实图像/K/pose上，用一个预注册的局部重建版本（例如 Cleaned 或 F3）渲染深度作为输入，作为独立模型配置，不与M-H的HERO在同一RGB上伪造额外视角。Raw/F1/F2/F3用于**固定上限数量**的互斥消融，不无限挑最好版本。
- **M-R（增加固定Ring CAD深度条件，可选）**：在真实相机的可靠Ring可见像素，用固定 CAD 首交点提供公制Z；非Ring区域保留所选H/F有效深度，未知0。若Ring被更近Polyp遮挡，不应强行将Ring深度写到该像素。必须确认模型对稀疏/不均匀深度的原生处理合法。**Ring已作为输入，则再以Ring近距误差判胜等同信息回灌**：该项只能作为输入输出合同，最终必须用Polyp未见图像/相对几何衡量收益。

**禁止**：将 Mask 或任意 valid/confidence、多个depth_layer、Ring CAD mesh直接作为模型 `infer` 新字段；若需改官方网络内部编码器来处理结构化Mask/显式CAD，属于**另立高成本研究支线**。当前 mask 仅用于定义输入depth的可信像素、裁剪策略和输出评价，并不是模型已经利用了 `mask` semantic token。

### 6.2 输出公制约束与 pose

官方 Map 模型可预测 `camera_poses`，但**不能用预测相机替代冻结 Ring-First K/c2w**。允许记录预测的raw pose、在相同首相机做**纯刚体gauge归一**的派生输出和条件几何重投影；禁止对各模型使用GT ICP、私下改变scale或为测试帧优化新的相机。经 Ring CAD 派生的受约束刚体候选若后续获批，必须另列 `DERIVED_RING_ALIGN`，不能算原生Map性能。若 CAD 作为输入，Ring CAD误差不可作为独立验证指标。

**Map模型失败条件**：多来源已合法使用且输出仍在内镜条件下显著错位、冻相机无法合理解释真实Polyp、存在严重穿插或只增加 prior-only 面，应据实报告 `MODEL_GEOMETRY_NOT_VERIFIED`，而不是再次用任意后验修正把它变成‘成功’。

---

## 7. 精简消融与跨组门禁

所有实验都要在**正式批准的后续任务**才执行；本报告无训练授权。C0/C1的基线失效不代表模型的科学基线，必须先完成**有限段 opacity 的CPU可微数学与几何合同门禁**。

### 7.1 主线 S，固定输入/相机/模型预算：只变化单个科学因素

| 实验 | 唯一新增设计 | 研究问题 | 主要判据 |
|---|---|---|---|
| `S0_VALID` | 经合同修复的多参考MonoSDF（RGB+HERO Z+Eikonal，可靠分割作为评估而非训练目标） | 无Mask监督时几何基线 | 有效射线/可见面积/损失非饱和 |
| `S1_MASK` | S0＋**Polyp-only有限段Mask opacity**和区域均衡采样 | Mask是否真正提高Polyp轮廓/抑制膨胀 | 留出Mask轮廓、错误外溢、有效梯度 |
| `S2_CAD` | S1＋固定 Ring CAD 遮挡截断（非穿插为可选单独消融） | 已知遮挡能否避免Ring后的假负/穿插 | Ring接缝、被遮挡区域误差、不破坏主体 |
| `S3_UNCERTAIN` | S2＋来源/可见性/冲突感知的稳健HERO深度权重 | 多源冲突能否改善同一个SDF | 跨帧真实重投影与几何双层，独有面保留 |
| `S4_ANCHOR_OPTIONAL` | S3＋已验证MASt3R几何锚点 | 稀疏共视是否继续降低歧义 | 留出角度受益与锚点资格；不足则NOT_RUN |

**注意**：S0/S1若区域采样分布不同，需保留相同计算预算与重要性采样校正，避免“样本更密”混淆。最关键的边际比较是 `S1−S0`,`S2−S1`,`S3−S2`。整体 `S3−S0` 仅表明组合总效益，不可作为单项创新证据。

### 7.2 独立 Map 消融

| 实验 | 输入 | 检验 |
|---|---|---|
| `M0` | RGB + 冻结 K/pose | 原生模型是否可在项目坐标合理预测，不偷用额外先验 |
| `M1` | M0 + 每真实参考的HERO Z | 深度条件增益 |
| `M2` | M0 + 一个预注册Cleaned/F3单层深度版本 | 历史重建能否代替原深度作为有效输入 |
| `M3` | M1或M2 + 可靠可见Ring CAD像素的公制Z | 已知CAD条件增益，注意Ring评价数据同源泄漏 |
| `M4`（可选） | M2分别切换F1/F2/F3合法单层先验 | 方法是否对错误几何来源稳健；数量受限不选最漂亮结果 |

与SDF比较分两层：**共同信息对照**（相同真实图像、K/pose、HERO）；**各方法最适配输入**（SDF显式CAD可微约束、Map官方合法CAD/局部深度条件）。不要让相同输入来自不同数量的真实帧，或把共享HERO衍生数据当独立监督。所有GPU内存/时间由PM后续预注册，RTX3060 6GiB条件下不应假定可同时训练大型多对象模型。

### 7.3 最小真实数据，失败门槛与升级

1. **CPU合成门禁（先）**：球体+torus CAD+背景平面，多种遮挡顺序；finite ROI opacity、对Polyp几何参数的正向导数、raw SDF与clamp分离、axial Z/射线距离、可见和UNKNOWN掩膜、同源去重。没有通过**禁止一切GPU训练**。
2. **单视频三参考（首个科学MVP）**：G01_004 ref03/08/13、G01_005 raw00057/00459/00745，独立训练两套SDF或Map输出；不得仅两张RGB。训练/评估源身份与F1/F2/F3父系提前冻结；正式相机固定。
3. **真实A→B与六视角**：保留真实RGB、源RGB投影预测、叠加、误差与分母、Ring黑色实体、实际XYZ侧视。比较先前Cleaned/F2/F3；真实相机/目标帧由预注册约束区分 `HOLDOUT_STRICT`（目前0）、`HOLDOUT_RECON_ONLY`、`DIAGNOSTIC_ONLY`。不得用历史评价帧反复调参并称盲测。
4. **扩到独立组**：通过后G06 NORMAL、G08 LIMITED，G07 UNQUALIFIED_STRESS_ONLY；至少记录四物理组 `MODEL_RUN_N` 和 `SUPPORTED_SURFACE_N` 实际分母，不能将资格审计分母替代新模型成功组数。可考虑增加正常Is/R5组以改善泛化验证。
5. **跨视频/照片**：004/005 仍分独立 Ring 局部系；照片未认证K/pose，只可图像分析；如无独立6DoF证据，第三列 `CROSS-VIDEO CANDIDATE — NOT FUSED`。不以学习网络代替未认证跨视频配准。

**失败条件**：前景opacity饱和、梯度对表面几何为零、有效采样未命中目标、模型仅使RGB误差下降而主体覆盖/真实可见支持减少、未经授权相机被改变、推测背面计入面积、Ring穿插增多或依靠删除困难像素提高MAE。遇域/合同失败不再增加训练步数。

**成功标准**（限科研候选）：在相同输入与已冻结评估协议下，至少出现**有原始视角支持的连续可见表面**，且相对于同输入历史强基线，改善真实未参与当前训练的轮廓/有效覆盖/几何冲突中的至少一项，同时未显著恶化真实CAD穿插或共同支持；面积与方向代理和分母均须公开。仅输出漂亮Mesh、计算图存在或步数结束不得判成功。

---

## 8. 给 PM 的八项明确决定

**Q1：MonoSDF 是否采用 Polyp-only？** **是，先在单视频采用Polyp-only SDF；Ring固定CAD，Background真实可信局部面只作遮挡。** 这是C1+C4的混合表示，不是删除背景证据。

**Q2：Mask怎样进训练？** 先用分割类别建立 `P_INTERIOR/P_BOUNDARY/VISIBLE_NONPOLYP/RING_OCCLUDED/UNKNOWN` 分区和采样，最重要是**有限ROI、可见性截断的Polyp opacity BCE**。Ring后和无真实背景支撑的未知射线不可全程负监督；关注梯度与实际输入数量。

**Q3：Ring最有价值的训练约束？** **固定Ring CAD首交点 `t_R` 裁剪Polyp可见射线段**；次要补充可微CAD实体非穿插。比最后只计算CAD距离更直接，也比重建Ring网络简单。

**Q4：Ring应由网络学习吗？** **不应该加入主线。** R1/R2/R3可以是独立探索或已知标尺回归压力测试，但没有增加 Polyp 真实信息的证据。且“用CAD训练再以CAD验收”会循环验证。

**Q5：多对象神经SDF必要吗？** **目前没必要**。唯一未知的主要几何对象是Polyp。Polyp SDF + 固定Ring CAD + 条件背景显式几何即可处理需要的可见性与遮挡；多对象网络自由度徒增。

**Q6：Map如何独立使用同样先验？** 通过官方合法 `depth_z+K+camera_poses` 将不同来源HERO或派生单层重建投影深度作为**互斥条件**；对于真正可见Ring像素可附加CAD的公制Z；Mask用于生成合法深度有效像素及评价，而非伪造官方语义输入。Map独立输出完整可比几何，输出pose不取代冻结相机；Ring若已作为条件，则不作为独立几何精度证明。

**Q7：最低成本最可能改善？** **先修复有限段Polyp Mask opacity**。因为已证实E0旧mask数学上饱和；修复能让分割成为非零的可微几何信号。但改善真实三维仍是可证伪假设，不能提前下科学胜负结论。

**Q8：MonoSDF射线/轮廓的最小修复？** 固定Ring相机、使用小的显式目标ROI和一致的mm↔network gauge；验证真实ray与正向目标交集；在ROI内取不含吸收球夹持的Polyp密度并在 `min(tROI,tR,tB)` 前积分；不再用全射线权重和；CPU有限场合成球/torus/平面导数测试；确认所有Mask/深度分区有效后才授权 GPU 科学MVP。当前 `ADAPTER_INVALID` 不能靠多训掩盖。

---

## 9. 工程交付建议与禁止事项

推荐 PM 在另一份独立任务书中按以下优先顺序组织工作，而不是把本文自动交给Codex执行：

**先做 C2a（零训练的有限ROI/Mask/CAD 数学适配设计与合成梯度合同）→ C2b（多参考同一SDF的数据流、深度权重与Map条件消融预注册）→ 新授权后 C3（G01两单视频有界MVP）→ C4（G06/G08/G07分层扩展）**。

对每步逐级展示四类核心证据：①真实来源/Mask/相机与Ring；② `valid ROI`/CAD射线前后几何与梯度；③ 不同HERO参考与不确定性权重；④ SDF/Map条件输入及输出支持；训练后增加A→B与六视角实际点云。复用固定 `visualization/real_p0_renderer.py`，Ring黑色CAD，实际XYZ与真实图像来源ID，不用光滑虚构Mesh遮蔽未知。

**不能启动**：新的GPU训练、任何网络权重更新或未知大规模下载；不能修改 Dxy、正式HERO/Ring-First相机、CAD/P0；不能用Oracle/GT挑参数；不能将Map输出pose替换相机；不能要求所有视角自然闭合到一个Mesh；不能把E1 CPU PASS叫做重建成功。

## 10. 参考资料与代码索引

- Yu et al., **MonoSDF**, NeurIPS 2022：[arXiv](https://arxiv.org/abs/2206.00665) / [官方代码](https://github.com/autonomousvision/monosdf)
- Yariv et al., **VolSDF**, NeurIPS 2021：[arXiv](https://arxiv.org/abs/2106.12052)
- Wang et al., **NeuS**, NeurIPS 2021：[arXiv](https://arxiv.org/abs/2106.10689)
- Wu et al., **ObjectSDF**, ECCV 2022：[arXiv](https://arxiv.org/abs/2207.09686)
- Wu et al., **ObjectSDF++**, ICCV 2023：[arXiv](https://arxiv.org/abs/2308.07868) / [代码](https://github.com/qianyiwu/objectsdf_plus)
- Han et al., **SparseRecon**, ICCV 2025：[arXiv](https://arxiv.org/abs/2508.00366)
- Batlle et al., **LightNeuS**, 2023：[arXiv](https://arxiv.org/abs/2309.02777)
- Long et al., **NeuralUDF**, CVPR 2023：[arXiv](https://arxiv.org/abs/2211.14173)
- Keetha et al., **MapAnything**, 3DV 2026：[arXiv](https://arxiv.org/abs/2509.13414) / [代码](https://github.com/facebookresearch/map-anything)
- [本项目E1代码与证明](https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001)
- [本项目E0故障源](https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-NEURAL-E0-COMPARE-001/experiments/TASK-NEURAL-E0-COMPARE-001)
- [本项目F3生长式对照](https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001)

**文献证据界限**：上述方法公开实验并未验证本项目真实息肉毫米级精度。本文新增的固定CAD+有限ROI+互相关深度权重组合属于**待验证的针对性工程/科研假设**，不是已经证实的本项目性能改进。

---

**RA状态：`DESIGN REVIEW / SCIENTIFIC RECOMMENDATION`。未执行 GPU、训练或新的推理；不改变任一冻结研究主线。由 PM 审查后转化为独立Codex任务书，经研究者批准方可执行。**
