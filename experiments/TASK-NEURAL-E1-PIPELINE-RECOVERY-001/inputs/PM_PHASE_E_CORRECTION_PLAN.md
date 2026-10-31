# PM_PHASE_E_CORRECTION_PLAN

**项目**：Reference-Ring Anchored Visible-Surface Reconstruction of Polyps  
**版本**：PM-E1-v2 / 2026-10-30 / 按 `RA_DECISION_E1_001` 修订  
**技术裁决**：`APPROVE WITH CHANGES — C0+C1 ONLY`  
**执行授权**：本次为供研究者转交的修订版；**只有用户明确批准并将单一 Task 交给新 Codex 后**，C0+C1 才可执行；C2–C4 均 `PROPOSED / NOT AUTHORIZED`。  
**角色**：RA 技术审核；PM 任务与验收；研究者批准；新单实例 Codex 执行及 Git 增量提交。

## 1. 独立 E0 审计与纠偏对象

已核对 E0 `TECHNICAL_REPORT`、`code/{audit,sdf_run,map_run}.py`、配置、Ring尺度表、目标评价、SDF域诊断与上游 F3/MASt3R 的来源记录。事实与推断分开：

- **工程已完成**：四物理组/五视频的资格审计；36 份历史/新增参考核对（9旧P0、5分区、22生长）；47个不同 HERO 输入图身份、154条输入依赖；MapAnything 四配置可前向；MonoSDF 一次400步优化；部分单位、相机重投影和来源索引可复算。
- **确定的SDF适配问题**：旧配置10 mm/network unit，bounding/absorbing sphere半径2.5；两实际相机中心归一化模长3.2714和3.8705；运行 silhouette loss 全程3.837196，57,176个输出三角面中按E0支持定义0个可见支持面。**注意：相机在球外本身不是普适失败条件**，必须按官方采样/吸收实现证明射线有效段、前背景分配与梯度为什么失效。
- **Map公制条件失败**：M3 Ring源像素预测至固定Ring CAD中位距约22.35/21.94 mm；两评价目标Polyp覆盖3.67%/16.81%，输出pose未硬锁输入pose；合法模型前向与有效公制场景是两件事。
- **科学命题未执行**：模型只运行G01_005的raw00057/raw00459两参考；G01_004没跑新模型，G06/G08/G07只有资格审计；跨视频几何未认证；严格全流程holdout=0。不得以四组审计代替四组算法泛化，也不能判断SDF或Map谁胜。
- **风险与历史保护**：有ENOSPC、依赖/dtype/API错误及已获授权清理记录，均独立于科学有效性。保留E0失败原件，状态`ENGINEERING_SMOKE_AND_AUDIT / DUAL_ARM_SCIENCE_INCONCLUSIVE`，不覆盖、不重跑E0。

**PM独立判断（待实验验证）**：根本流程偏差是用两个输入的最小跑通替代“多参考有误差的真实观测共同决定几何”的科学实验；正确纠偏需要先恢复来源—相机—几何—损失/条件—独立验证闭环，而不是简单延长训练步数。

## 2. 冻结主线、数据依赖与信息级别

```text
G01 video004(独立Ring局部系)            G01 video005(独立Ring局部系)
  RGB/Polyp+Ring Mask                     RGB/Polyp+Ring Mask
  条件K/c2w(完全冻结)                    条件K/c2w(完全冻结)
  HERO native axial-Z                    HERO native axial-Z
  Raw XYZ/源像素UV/原始开放面             Raw XYZ/源像素UV/原始开放面
  历史T2/Cleaned与F1/F2/F3               历史T2/Cleaned与F1/F2/F3
  MASt3R/共视/深度冲突                   MASt3R/共视/深度冲突
              \                             /
         两套**独立**数据DAG和观测质量/泄漏资格
                         ↓
 C0资产恢复（36份参考池，不等于36独立真实观测或病例）
                         ↓
 C1真实射线↔ROI/SDF域；source XYZ/mesh→source-view z-buffer/axial Z；
    Ring CAD和Map正式接口（全部无训练CPU合同）
                         ↓  单独授权后
 C2共同信息集+不同合法先验输入集；来源可靠性/多参考约束入图测试
                         ↓  单独授权后
  ┌───────────────────────────────┬──────────────────────────────┐
  │ Arm S：MonoSDF多参考联合优化 │ Arm M：官方MapAnything独立竞赛│
  │ 单视频≥3来源同一SDF；冻结pose │ M-native + M-geometry-conditioned│
  └───────────────────────────────┴──────────────────────────────┘
                         ↓
 同源公平对照 + 各臂最佳合法信息对照；A→B真实观测、CAD、六视角、支持域
                         ↓
 004/005先独立；跨视频位姿不通过则NOT FUSED；G06/G08/G07按资格分层
```

### 来源的三重身份不得混淆

1. **真实观测**：来源RGB/Mask/独立相机与原生HERO深度；HERO是模型估计，不是GT。
2. **派生几何先验**：Raw/Cleaned、F1/F2/F3、MASt3R有效匹配/注册候选；它们可与原观测共享依赖，既不是独立视角也不是独立真值。
3. **模型输出**：SDF零水平集、Map pts3d/depth/pose/conf；不得使用自身confidence或闭合网格证明真实重建准确。

**固定第一阶段位姿规约（D2）**：
- 每一输入的原始 `K_i`、`T_i^{RingFirst}` 为冻结数据；**优化器不得包含相机变量**，不准修改它们的值或以Map输出pose替换；Ring CAD模型、中心、半径和mm尺度固定。
- 004、005仍属于两个未认证相互变换的独立Ring局部系；无正式跨视频联合模型。photo001–003未认证K/pose，仅可视为图像/匹配候选。
- 对Map允许预先声明的**纯表达规范转换**：例如第一输出相机坐标到第一冻结相机坐标的单一刚体gauge；必须保存原输出pose、转换及残差。此转换不优化、不缩放、不做Ring后验ICP，不能把其结果当原生公制能力。
- 以后如研究派生配准，必须另立任务、独立状态；当前C0+C1不实施。

### 历史可复用资产（先校验路径/SHA/可用性）

| 链路 | 优先复用位置/函数 | 不允许重造的部分 |
|---|---|---|
| 来源/相机 | E0 `code/audit.py`、`INPUT_ELIGIBILITY.json`、`FRAME_CONVENTION_TESTS.json`；F3 `code/common.py:source,target_source` | Ring-First/冻结K与c2w |
| HERO/公制XYZ | `ring_first_v1/scripts/common.py:unproject,depth_mesh`，既有native depth及source UV | 深度推理/反投影第二实现 |
| 清理/候选 | Phase-C T2；F1/F2/F3与F3面片来源 | 新密度阈值搜索 |
| 匹配 | View-Partition `matching.py`,`registration.py`及MASt3R缓存 | 重新训练匹配网络 |
| 渲染/几何 | `visualization/real_p0_renderer.py`、`SameCameraScene`、真实A→B、`cad_audit.py` | 替代真实点云的贴图平面 |
| 神经底座/输入包装 | MonoSDF官方`12513009…`、E0 `sdf_run.py`；Map官方`3d10cf7…`、E0 `map_run.py` | E0失败代码直接复跑、模型内部重写 |

## 3. 阶段门禁与执行顺序

| 阶段 | 实施内容 | 状态/验收产物 |
|---|---|---|
| **C0** | CPU只读恢复36参考、五视频源与三照片；来源SHA/DAG、Raw/Cleaned/F1/F2/F3的父子依赖、相机资格、至少两个G01视频各≥3多参考候选、共视和真实留出分层 | **本轮获技术准入**；冻结manifest/来源图/限制台账 |
| **C1** | CPU几何/接口合同：SDF真实射线+吸收体域；Map官方I/O与本地几何→合法`depth_z`转换；CAD遮挡、单位、pose不变断言；旧E0失败复现 | **本轮获技术准入**；各子项GATE_PASS/INVALID/BLOCKED及图 |
| **C2** | 多来源批组织与来源冲突权重；可微loss及多源梯度合同；Map条件先验合法输入组合冻结 | **未批准**；仅预注册描述，须新Task与用户授权 |
| **C3** | 有界科学实验：MonoSDF单视频各≥3来源共同约束一个SDF；Map native+geometry两子路线完整对照 | **未批准GPU**；不可自动执行 |
| **C4** | 冻结评价、跨组分层与真实六视角；无通过跨视频位姿不得FUSED | **未批准**；不承诺物理精度/体积 |

本轮C0/C1禁止：模型前向、训练、GPU调试、权重下载、新HERO、数据清理、自动进入C2。允许检查已存在模型缓存与官方源码；存在资源障碍标记BLOCKED，不用超范围动作绕过。

## 4. 两条独立科研路线（后续科学实验预注册，不是当前授权）

### Arm S — MonoSDF 优先（D1）

- 先用**官方实现真实采样路径**检查相机位置、射线与Polyp/近端背景ROI、near/far、bounding sphere/absorbing sphere的实际交叠、opacity和零交叉；E0旧配置为必须失败的回归样本，候选至多两个具有物理理由的域适配，不能简单把半径调大就PASS。
- **首个正式科学MVP：G01_004与G01_005分别取至少3份通过来源资格的不同参考，分别联合优化一个单视频SDF。** 不得跨越未认证视频SE(3)，不得把同源HERO衍生视角数当独立观测数。
- 真实可微最低损失：训练RGB鲁棒项（排除高光/遮挡/Ring）、真实前后景Mask射线、多个HERO **轴向Z** 的稳健深度项、Eikonal；训练时每源有效ray、权重、loss/梯度和支持贡献可复核；相机`requires_grad=False`且不进optimizer。
- 进行 `S0(no HERO)`、`S1(uniform HERO)`、`S2(source/conflict-weighted HERO)` 控制消融；权重来自**训练源**的相机条件、Raw/Cleaned及重投影冲突，归一化且不能全零；HERO并非GT。
- Ring CAD真实尺寸、射线遮挡、无新穿插是硬输出门禁；若加入可微CAD loss须单独通过梯度检查。可验证MASt3R真实对应可作为附加跨视角约束；**未接可微图时标`NOT_IMPLEMENTED`**，不得作为首个科学MVP已用约束。
- 只将具有真实观测支持的零水平集面计入可见面；`PRIOR_ONLY/UNKNOWN`不得充当真实面积/体积。MonoSDF域适配仍失败时提交RA评估NeuS2，不得自行切换。

### Arm M — MapAnything 完整独立几何条件竞争臂（D3）

**不降格为SDF初始化器**；保存官方固定版/权重和原生模型输出，源资格、物理尺度、公制评价与SDF共同审计，允许Map利用更丰富的合法几何信息并清楚申报信息优势。

- **M-native 消融**：M0 RGB；M1 RGB+K；M2 RGB+K+冻结pose；M3 RGB+K+pose+HERO native axial-Z。保留E0的四个原始结果为失败/工程基线，不自动认证。
- **M-geometry-conditioned 扩展**：Raw/Cleaned点云、F1/F2/F3开放面及有来源的局部几何（含通过资格的MASt3R位姿/邻接候选），依其实际来源相机K/pose投影到来源视图，构造轴向Z、有效掩码、z-buffer遮挡和逐像素溯源；必要时可比较多个不同来源参考的HERO条件及这些派生深度条件。固定Ring CAD独立供遮挡与公制验收，不与Polyp混成一种训练几何。
- **官方合法输入边界**：目前公开接口候选`img`, `intrinsics`/`ray_directions`, `depth_z`, `camera_poses`, `is_metric_scale`；必须按**锁定官方revision代码**验证组合、维度、valid/NaN规则。官方**未原生提供任意PLY/GLB/自定义置信度张量输入的保证**。派生点云需经最小光栅化适配转为被官方真实消费的输入；不能把无效值填洞、把dict中额外字段当生效条件或篡改模型内部网络。
- 名称M4/M5仅作**待验证的候选实验标识**：例如单来源派生深度 vs 多来源分视图合法深度条件；只有C1验证接口、C2冻结组合后才命名/执行。不同历史F1/F2/F3常共享原观测，**不可按派生包数量增加独立证据分母**。
- 同一个来源RGB若具有多个相互冲突的先验深度，除非官方支持对应多条件接口，否则只能作为**互斥的配置消融**或预冻结来源融合策略，不得伪装成新增相机/独立视角。
- 保存原始输出`pts3d`,`depth_z`,`camera_poses`,`K`,`valid/conf`；仅允许预声明的纯刚体gauge表达变换，输出pose与冻结输入pose的差必须记录；不得scale-fit、Ring/GT ICP救场。公制不合格即`METRIC_CONTRACT_FAILED`，而非自动判Map模型科学失败。

### 比较协议：双表而非单一赢家数字

1. **共同信息集**：两臂同一物理组/同一个视频、同源ID/相机/评价资格；对照Raw、Cleaned、F1/F2/F3时固定同源版本，公平区分方法而非数据数量差异。
2. **各臂最佳合法信息集**：Map可用合法的额外来源几何先验，SDF可用已预注册可微约束；报告每项来自哪些真实观测及相关历史派生，**不把额外先验收益冒充模型本体优势**。

## 5. C0+C1 预期四幅核心可视化

1. **来源/共视与数据身份图**：G01_004、G01_005、三照片，G06/G08/G07；源/HERO DAG、相机空间、合法输入与条件性来源。
2. **SDF域错误与修复候选**：E0旧相机/采样射线/absorption真实ROI遮挡情况，候选至多两种，同一mm尺度及有效射线统计；旧失败要可视化。
3. **多参考HERO冲突图**：Raw/Cleaned及已存在原面，源pixel UV/深度不一致、视角/不确定性代理、Ring遮挡、未知。
4. **Map几何接口图**：真实来源XYZ/F1/F2/F3→来源视图轴向Z+valid+来源ID与z-buffer；对照E0 M3 Ring/CAD偏差和输出pose残差。全图Ring黑色CAD，真实XYZ；不生成虚构新Mesh或新模型结果。

固定使用既有真实点云 renderer，完整本地HTML文件夹，3–4核心复合PNG上传GitHub，配置/SHA/版本、独立失败台账与单份TECHNICAL_REPORT齐全。

## 6. 主要风险与前置停止

- 上游HERO跨源依赖/历史相机暴露导致严格holdout仍为0；如实分层`HOLDOUT_RECON_ONLY/DIAGNOSTIC_ONLY`，不能在看目标误差后更换评价帧。
- 相机冻结导致不同来源深度冲突不能通过pose优化消除；本阶段接受冲突作为科学输入，禁止静默调整pose。
- SDF修复不能靠无界搜索边界/near/far或GPU训练，必须先通过真实ray/ROI域合同。
- Map几何先验可能在重投影时遮挡/深度冲突/输入有效值约定失败；失败标`UNSUPPORTED_NATIVE_INPUT`或`ADAPTER_INVALID`，保持独立竞争资格，不能强行注入内部特征。
- 非观察背面/过度平滑不可视为真实重建；G07非合格相机仅压力；G08有限条件独立列示。
- E0权重、历史输出、GT/DXY、main/worktrees不可修改；禁止清理旧目录、GPU、权重下载、原始数据上传。

## 7. 科研状态与下阶段研究者决策

- E0：`REPORTED / ENGINEERING_SMOKE_AND_AUDIT / DUAL_ARM_SCIENCE_INCONCLUSIVE`。
- E1 C0+C1：RA `APPROVE WITH CHANGES` 已落实，**新Codex仍需研究者明确批准并转交任务**。
- C2–C4：`PROPOSED / NOT_AUTHORIZED`，独立后续Task与GPU预算审批；两臂均未判胜负。

依据：资料库`RA_DECISION_E1_001.md`及正式纠偏要求；GitHub E0分支`exp/TASK-NEURAL-E0-COMPARE-001`，上游F3`exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001`、视角分区`exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001`。本文件只改变后续设计，不覆盖历史失败。
