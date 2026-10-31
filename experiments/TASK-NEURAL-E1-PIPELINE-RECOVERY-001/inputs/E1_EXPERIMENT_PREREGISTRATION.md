# E1_EXPERIMENT_PREREGISTRATION

**版本**：E1-PREREG-v2 / 2026-10-30 / 依据`RA_DECISION_E1_001` D1–D3。  
**状态**：`PREREGISTERED_DESIGN / C0+C1_ONLY_APPROVED_FOR_POTENTIAL_TRANSFER / C2-C4_NOT_AUTHORIZED`。本文详细定义**将来可能批准**的科学实验，不是本轮GPU运行许可；任何参数/资源预算均需在独立Task冻结、用户批准后执行。

## A. 可证伪命题与两条独立路线

**共同科学问题**：给定同一静止物理场景的多个真实内镜视角、已知Ring CAD公制尺度、完全冻结的Ring-First `K,T`、多份有误差的HERO axial-Z及其来源、RGB/Mask、真实匹配和已有局部面，哪条方法能在**不制造无来源背面**的前提下产生更多连续、有观测支持、能够解释未参与优化目标的可见表面？

- **SDF Arm S**：首选成熟MonoSDF，多个参考联合优化**同一个**隐式表面，以SDF几何与训练源RGB/Mask/HERO耦合；原相机不作为优化变量。
- **Map Arm M**：独立官方MapAnything，`M-native`和`M-geometry-conditioned`两个子路线；可充分消费**合法结构化**HERO/Raw/Cleaned/F1/F2/F3/匹配几何条件，但不能假装官方支持直接输入任意PLY/GLB或自定义置信度张量。
- 旧Cleaned/F1/F2/F3是具有共同原始来源的几何基线/先验，**不是GT、也不是增加的独立病例**。结果状态可以为`SCIENCE_INCONCLUSIVE`，不得保证必然有赢家。

## B. 输入单位与相机硬合同（D2）

- G01_004与G01_005先各自一个独立Ring局部坐标系统，分别拟合；只有经独立验收的跨视频 SE(3) 才能在**后续另外授权阶段**考虑统一，未通过时`CROSS-VIDEO CANDIDATE — NOT FUSED`。
- 相机为OpenCV `c2w`，右X/下Y/前Z；`K`包含图像resize主点调整；内部XYZ与CAD以mm表示，模型接口以其规定的m或网络单位表示；HERO是**相机轴向Z，不是射线长度**。
- **第一阶段全部Ring-First `K_i, c2w_i`冻结、`requires_grad=False`，优化器不含相机参数。** Map预测`camera_poses`属于模型输出，只能与条件pose比较，不能替换输入；容许预声明的首相机纯刚体gauge仅用于坐标表达比较，**不得后验scale-fit、ICP或Ring 6DoF拟合**。
- photo001/002/003没有认证K/pose，不可加入正式公制训练；可作为额外图像/匹配候选，不冒充三维真值。
- Ring CAD独立物理锚点，不当Polyp训练标签；不重新建Ring点云。

## C. 预先冻结的输入集和独立性

### C.1 第一科学MVP（待C0资格确认）

| 场景 | 初始候选参考（仅指向实际文件，C0需验证） | 最低条件 | 状态 |
|---|---|---|---|
| G01_004 | `ref03/ref08/ref13`及后续经资格的派生参考 | **至少3个有真实不同参考身份/观察方向、有冻结K/T及HERO的输入**，一个SDF、相同来源的Map条件实验 | C0待确认 |
| G01_005 | `raw00057/raw00459/raw00745`及合格后续参考 | 同上，独立于004 | C0待确认 |
| G06_004 | 既有ref04+新参考 | NORMAL 条件；后续逐组正式模型运行 | C4待授权 |
| G08_005 | 既有ref04+新参考 | LIMITED，独立统计 | C4待授权 |
| G07_004 | 既有ref04+新参考 | UNQUALIFIED_CAMERA_STRESS，只作压力分母 | C4待授权 |

不能仅因为“至少3份参考”就认为3份独立HERO监督：同一模型多参考可能共享源图像、相机或MASt3R依赖，须报告原始RGB身份、共享HERO输入边数和观察方向分布。实际最小集由C0输出与后续RA/研究者批准确定，不能依据未来目标误差选取。

### C.2 冻结留出与泄漏等级

每一帧/来源记录 SHA：`RGB,Mask,native_HERO,Raw/Cleaned XYZ,pose,source UV,prior parents,MASt3R matching use`。预登记`CORE_TRAIN`, `TRANSITION`与目标帧`HOLDOUT_STRICT`（有全链证据）、`HOLDOUT_RECON_ONLY`、`DIAGNOSTIC_ONLY`、`NOT_EVALUABLE`。E0的严格holdout=0不可事后改写；G06 raw00351/G07 raw00293属于已知旧HERO输入，不能作为独立测试。严格盲测不足时只报告可用分级诊断。

**源集合不允许因测试表现更改**，冻结输入SHA、训练/评价身份、目标B及目标使用时间；新输出先冻结后读取B评价。历史数据的先前曝光如实披露，不冒充全流程盲测。

## D. Arm S：MonoSDF多参考统一SDF的正式科学MVP（待单独批准）

### D.1 C1先修复的几何域

保留MonoSDF官方revision`12513009cd20a08b35ddc2c55a7e42da2c7baf43`。静态/CPU测试必须验证官方实际吸收边界、scene centering、scale、相机射线与ROI/near-far、zero-crossing。E0旧配置应作为失败回归例；相机中心大于球半径不作为通用错误推断。至多两个物理合理候选方案，不开展大规模域搜索。C1失败时不启动任何SDF优化；请求RA审核才考虑NeuS2。

### D.2 联合多参考数据流与最小已实施损失

每视频至少3个有共视/角度意义的合格参考，按来源ID采训练RGB/Polyp Mask、source HERO Z、有效位姿和可靠性权重，在同一SDF网络与场景中交替/混合batch优化；以**每轮真实至少来自多个源**或跨相邻轮的受控覆盖记录证明共享参数被多源更新。必须报告每源有效射线数、loss、梯度/贡献和来源几何冲突。

建议的预注册目标（具体参数C2再定）：

\[
\mathcal L_S=\lambda_{rgb}\sum_v\rho(I_v-\hat I_v)
+\lambda_{mask}\sum_v L_{sil}(M_v,\hat M_v)
+\lambda_d\frac{\sum_{v,p}w_{v,p}\rho_\delta(\hat Z_{v,p}-Z^{HERO}_{v,p})}{\sum_{v,p}w_{v,p}+\epsilon}
+\lambda_e L_{eik}
+\lambda_a L_{anchor}+\lambda_c L_{CAD}.
\]

- `L_RGB`：**只有训练源**，Ring、强高光、已知遮挡和不可解释区域禁用/单独标记；正确的可微渲染图像梯度，不得复制目标B的RGB。
- `L_sil`：训练Polyp前景/邻近背景真实ray；与官方采样/吸收规则一致。Ring CAD用于遮挡，不能进入Polyp真值。
- `L_depth`：多个来源HERO axial Z的Huber/稳健误差；每源可复算非零有效权重，边缘/T2/视角/多源冲突只作质量代理，不等于GT；源间深度冲突应通过冻结K/T下真实重投影和共视分析计算，不靠全局点平均；权重不得全零或将单参考主导而冒充多源。
- `L_eik`：只作几何正则，不使prior-only闭合表面获得观测支持身份。
- `L_anchor`：只有真实可观测、验证过的MASt3R/LightGlue息肉或近端背景对应、且进入**可微计算图**时才能标`WIRED`；首个MVP非强制实现，未实现写`NOT_IMPLEMENTED`。
- `L_CAD`：固定Ring的投影/遮挡/穿插属于**强制输出验收**；若作为可微损失需额外梯度单测，否则`OUTPUT_GATE_ONLY`，不准写成已优化CAD约束。
- `K_i,T_i`无梯度且在模型前后保持相同；不得通过修改pose掩盖错误深度。

### D.3 有限消融与失败预判

| 消融 | 同一多源输入集合 | 实际变化 | 必须检查 |
|---|---|---|---|
| S0 | ≥3来源RGB/Mask | 不提供HERO loss | baseline源数/Mask/RGB支持 |
| S1 | 同集合 | 恒定权重多源HERO Z | 多源Z是否进入图、对齐程度 |
| S2 | 同集合 | 来源可靠性+多参考冲突的可复算权重 | 与S1相比新可见面/冲突/实际B表现 |

可额外将已实现的L_anchor、L_CAD作为明示独立消融，但不得在S2未跑通时凭空宣称实现。C2批准前不确定具体权重、步数、seed/GPU；必须使用独立Task冻结预算，先小规模检验有效ray/梯度，再正式运行。只通过400步或生成完整Mesh不算成功。

## E. Arm M：独立MapAnything双子路线（D3，待单独批准）

### E.1 模型与合法条件边界

官方代码rev`3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9`，Apache checkpoint revision`00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a`，以E0本地SHA验证。只从锁定官方API证实合法的`img`,`intrinsics`/`ray_directions`,`depth_z`,`camera_poses`,`is_metric_scale`构造条件；不能将输出`pts3d`误认为官方也能输入任意点云。官方网络内部不改，不能以零/NaN填充绕过无效像素合同。

**M-native（保留所有E0消融）**：M0 RGB；M1 RGB+K；M2 RGB+K+冻结pose；M3 RGB+K+pose+HERO-native-Z。必须注明多参考和共同源集合的实际区别。

**M-geometry-conditioned（扩展的完整独立竞争路线）**：可利用有来源、有相机资格、坐标一致的任意适用几何先验，包括单参考Raw XYZ、历史T2/Cleaned、F1/F2/F3的源索引点和实际原三角面、邻接MASt3R获得的条件性几何及Ring CAD遮挡信息。先用**来源相机及现有真实Z-buffer**转换为匹配每个输入RGB视图的`depth_z`/validity/来源像素ID/原网格三角面ID；只有官方接口能合法消费的部分才可送入模型。多来源派生面共享的真实输入不得当独立监督。

### E.2 建议条件矩阵（本轮C0+C1只核验，不推理）

| 配置族 | 输入身份 | 主要科学问题 | 是否已认证可运行 |
|---|---|---|---|
| M0–M3 | 同来源 RGB / K / 冻结pose / native HERO Z | 原生条件增加是否改善输出 | E0接口工程已跑；E0公制失败须保留 |
| M4-proposed | 同一来源RGB/K/pose + 本来源Raw或Cleaned派生Z（互斥版本） | 深度来源/清理选择对Map影响 | 待官方valid处理与CPU投影合同 |
| M5-proposed | 多个**真实不同参考视图**的RGB/K/pose及各自HERO或派生Z | 不同视角有来源几何条件能否相互解释 | 待官方多视图输入合同与C2冻结 |
| F-prior-ablation | 同源集的F1/F2/F3经来源投影的深度先验，逐方案对照 | 聚合先验是否有附加价值/可能引入偏差 | `NOT_RUN`，不得把F3当GT或独立观测 |

M4/M5仅在**确证接口、有效值与来源合同**且C2获批准后正式编号。不支持某种字段必须标`UNSUPPORTED_NATIVE_INPUT`；不能伪造官方能力。若F1/F2/F3共享相同RGB和HERO输入，在同一view构成的多个深度版本是**可选择的不同条件假设**，不是新相机、新独立证据。附加信息的上限是“有来源的已知几何”，不允许把目标B/未认证照片或跨视频错系几何塞进训练/推理条件。

### E.3 Map输出合同、公制验证与独立竞争身份

全部保存官方raw `pts3d,depth_z,camera_poses,K,valid/conf`及原始单位；另存只用首输出相机与首冻结相机的**预声明纯刚体gauge**表达转换（禁止额外优化/缩放/ICP）。按输入Mask中的Ring像素对固定CAD统计中位/p95距离与有效分母、Ring遮挡、相机pose残差、共视层冲突；预测pose**不能替换Ring-First输入**。若公制条件失败标`METRIC_CONTRACT_FAILED`，仍保留原始预测与科学未定结论，不得从事后Ring尺度拟合中恢复原生PASS。

Map可利用SDF未使用的更多合法先验并以完整独立臂竞争，但需同源信息表与附加信息表**两套比较**；单靠更多历史面获益不能推断Map网络本体比SDF好。

## F. 两套公平比较表与最终评价

### F.1 同等信息表（Main apples-to-apples）

比较S0/S1/S2、Map合法M0–M3以及相同来源身份Raw/Cleaned/F1/F2/F3：固定物理组、视频、各源RGB/Mask/HERO依赖和冻结相机资格；模型可不同，但输入数量与条件等级必须显式配平。严格区分“同参考”与“同参考的衍生包”。

### F.2 各臂最佳合法信息表（Capability under allowed information）

允许Map M-geometry-conditioned使用更多合格历史几何；SDF用预注册多源/可微锚点。记录输入父系DAG、数据重复和未测试先验；评价同样使用不参与输入的真实目标与固定CAD，不能把方法输入先验本身当独立真值。

### F.3 输出门槛（先适配再科学）

1. **公制与冻结相机**：K/T/单位/scene/gauge自洽，Ring固定CAD残差/遮挡公开；两视频不同坐标未注册则NOT FUSED。
2. **可见支持域**：每面标`MULTI_VIEW_OBSERVED_SUPPORTED / SINGLE_VIEW_OBSERVED_SUPPORTED / CONFLICT / RING_OCCLUDED / PRIOR_ONLY / UNKNOWN`；SDF0水平集或Map有效点不自动算有源面。预注册前景/深度支持分母，不能事后改变容差掩盖失败。
3. **真实A→B**：A真实RGB、A真实XYZ、B真实RGB、以A RGB/XYZ预测B、覆盖/外溢/UNKNOWN/共同支持RGB差异/侧视；禁止B RGB重新上色、删除困难区改善指标。
4. **连续可见面**：开放面有效来源、最大连通片面积代理、独有表面方向、错层/重复层、已接受可信结构损伤、CAD新穿插。prior-only闭合不算可见面积/体积。
5. **统计分母**：独立物理组为主；G01两个视频不是两个病例；G07压力单列，G08有限单列；运行/未运行/输入不合格/适配失败/模型输出失败/科学未定分别列示。GT/Oracle不参与任何参数或位姿选择；真实部署GT未知时绝对毫米三维精度`NOT_EVALUABLE`。
6. **有效结论级别**：`ENGINEERING_PASS`≠`ADAPTER_PASS`≠`SCIENTIFIC_CANDIDATE`≠`SCIENTIFIC_ACCEPTED`。只有独立目标和多组重复/不确定性支持才讨论最终科学采纳；若任一臂0有效支持/严重公制失败，不能强制选赢家。

## G. 资源预算与阶段停止

**C0+C1本次唯一可能批准范围**：CPU静态几何、来源投影、官方代码审计、只读旧Map/SDF缓存；不运行新模型forward、GPU/权重下载/HERO/清理。旧SDF配置预期FAIL，CPU门禁先定位错误；Map geometry adapter必须证明 `source XYZ/F1/F2/F3 → 合法输入depth_z`，且有无效与遮挡正确处理。失败各自标`ADAPTER_INVALID/UNSUPPORTED_NATIVE_INPUT`。

C2多源batch/可微接入测试、C3 GPU有限运行、C4多组真实评价必须**另行RA审核+研究者明确批准**。GPU限额、步数/时长、随机种子、可视支持容差均应在对应任务运行前冻结，不得用目标误差回调。不开展无界网格搜索；缺少有效数据/硬件时停止分支，不能以CPU极慢模型前向隐瞒失败。

## H. 预期图与交付

C0+C1：来源/共视+Ring/三照片；MonoSDF E0旧域失败与修复ray+ROI；HERO多源冲突、Cleaned支持；Map来源XYZ/F1/F2/F3→axis Z/valid/遮挡/父系并展示旧M3 CAD偏差。每阶段3–4核心复合图、实际mm、黑色CAD Ring、真实XYZ、源码SHA及本地HTML/单份中文报告。

正式模型阶段（仍未批准）：G01三列004独立/005独立/cross-video candidate-not-fused；真实A→B五面板；一致坐标六视角；单视频可见支持面和prior-only/UNKNOWN明确区分；G06/G08/G07实际运行与失败同等披露。**绝不以美观GLB、400步loss或更多点数代替可靠几何。**
