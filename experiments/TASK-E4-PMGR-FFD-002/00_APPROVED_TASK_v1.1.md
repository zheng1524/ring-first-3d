# TASK-E4-PMGR-FFD-002｜FFD 多视角主体优化：清理磁盘后直接执行

**PM 执行提示词 v1.1｜2026-11-05**  
仓库：https://github.com/zheng1524/ring-first-3d  
上位 RA 方案：`RA_E4_PMGR_FFD_PM_HANDOFF_v1.0.md`（人工已确认）  
实施范围：先完整执行 **G01_004/E2**，条件允许再执行 **G06_004/E1**；每例 P0→P1→P2→P3 和 C0–C3 最小对照。完成人工审阅后才扩展其他组。

## 0. 给现有 Codex 的直接指令

你就是此前长期承担本项目的同一个 Codex 执行智能体，已经亲自完成 A1/E1/E2、PMGR、R1、Ring-first、HERO 与 Camera Gate 相关实验。**不再重新讲解整个项目，不再重新梳理所有历史或重建一套开发环境。**

请读取本指令，并直接结合**你现有的本地代码、模型、日志和工作树**实施。先做安全空间清理，再审查现存可复用的实现，随即连续完成本轮实验。不要退回到只写建议、只做一个 P1 demo 或反复等待人工批准的模式。

本任务仍遵守已知冻结规则：不改 Ring-First 相机/P0 相机资产、HERO 权重与 Raw/Cleaned、Type-2、Camera Gate、CAD Ring 和 DXY 主线；不得用 GT 参与优化，不混合未经认证的跨视频坐标；不执行 B1 HERO 网格贴片和 B2 神经 SDF；不能为 Ip/Is/IIa 各写一套几何算法。必要的主体椭球九参数和 FFD 系数仍允许在新实验里更新。

**新增重要条件：本机磁盘仅约余 7 GB。禁止直接 `pip install physicsnemo pytorch3d ...` 或克隆数个完整大仓库。优先使用已有依赖，读取上游 GitHub 单文件与教程；只有证明轻量路径不可行且核算足够空间后，才安装额外模块。**

---

## 1. 第一件事：审计并清理 Codex 自己前期产生的实验占用

这一段是**本轮已获人工授权的清理**，但目标只限于你自己前段时间为本项目创建、目前暂停推进的**可再生实验产物和重复环境**，不是让你删除项目历史。

### 1.1 只读盘点并创建清单

在清理前记录 `df -h`、实际可用容量、项目工作树与各大目录 `du -sh`、GPU/CUDA 环境。重点调查你自己创建的旧实验 worktree、独立 Python 环境、重复模型权重、Python/pip/conda 下载缓存、大型中间点云/密集渲染、未继续推进的 TSDF、NeuralFusion、MonoSDF、旧 PMGR/R1 运行产物。

先生成 `DISK_AUDIT_BEFORE.md` 和可审核的 `CLEANUP_MANIFEST.csv`，每项至少包含：**精确绝对路径、大小、所属任务、是否仍有代码依赖、Git/远端是否已保存、保留/删除原因、可恢复方法**。先 `git status`，核对当前训练进程和其他工作树是否使用这些文件。

### 1.2 清理优先级与保护范围

按以下顺序清理，不得把大目录整棵删除作为默认动作：

1. **优先清理**：可再下载的 pip/编译缓存、临时安装包、测试缓存、重复生成的视频帧/图片、明确无训练进程使用的旧实验中间 checkpoint、可复算的逐迭代临时体素/渲染缓存、同内容重复副本。逐项验证归属，删除精确目录或文件。
2. **有条件清理**：已停止的旧实验的巨大 `local_results/`、密集点云、重复权重/环境。清理前必须保留该实验的 `TECHNICAL_REPORT`、`FAILURE_LEDGER`、`REPRODUCE`、协议/配置、资产索引、关键代码提交 SHA、最有判断价值的 **3–4 张真实证据图**、必要的最小/最终几何检查点。对不能从 Git 或冻结输入重建的结果，**不要删除**；如需要舍弃唯一结果，先向人工确认目标。
3. **禁止清理**：原始视频/图片/分割 Mask、唯一 Blender 场景或息肉 CAD、Ring CAD、冻结相机与标定、HERO 原始输出与冻结清理、DXY 仓库、活跃实验、未提交的代码、A1/R1 的唯一安全 P0、无法重新生成的关键检查点。多个工作树共享的环境不能因为某一实验暂停而删除。

**操作纪律**：只对清单中已解析、核对过的精确目标执行删除；不使用 `$HOME`、`~`、工作区根目录、通配符或未解析变量作为递归删除目标。每一类先核对受影响路径及数量，再执行；不要只凭分支名推断可删。恢复本来就依赖的文件则必须保留完整路径/哈希与再生说明。

执行后输出 `DISK_AUDIT_AFTER.md`、释放空间量、删除目录清单及是否能够恢复。**磁盘释放不会自动发生于同盘目录内移动**，因此真正要腾空间时，确认可再生的文件可按上述边界删除；必须向人工明示删除了什么及恢复方式。若需清理不可再生的科研证据或他人文件，停止此部分并请求人工批准。

### 1.3 空间预算与安装策略

清理后估算本次新增源码/依赖/检查点的**峰值**（不只是安装包大小），给出 `free_after_cleanup`、`estimated_peak_need`、`safety_reserve`（至少预留数 GB 的系统余量）。空间仍不足时，**切换轻量复用方式**，不得自动下载整套重型训练框架。预设数据存储策略：只永久保存 P0/P1/P2/P3、BEST/LAST_SAFE、必要失败候选和精简日志；不重复保存每步大幅原图、全帧深度和上千个临时 Mesh。

这次清理属于新实验准备工作，不需要把其变成单独多轮审批项目；但清理对象的可恢复性有疑问时必须报告，不擅自删科研唯一证据。

---

## 2. 必须复用的成熟工程：GitHub 地址、复用位置和安装决策

**不是让你下载下面所有仓库。**按优先级读取官方源码/教程，先以本地已有 Torch、CUDA、nvdiffrast、FCL、Open3D、Blender 为基础，必要时只实现很小的项目适配层。

| 优先级 | 项目与直接地址 | 具体要复用什么 | 本轮安装决策 |
| --- | --- | --- | --- |
| **1 必读** | **PyTorch3D** 仓库 https://github.com/facebookresearch/pytorch3d；官方教程 https://pytorch3d.org/tutorials/fit_textured_mesh；Notebook 源码 https://github.com/facebookresearch/pytorch3d/blob/main/docs/tutorials/fit_textured_mesh.ipynb | 从已知初始球网格、多个视角的 soft silhouette loss 优化**一个共享 Mesh**的训练循环；view batch、可微损失与 edge/normal/Laplacian 正则。把教程可学习的逐顶点 offset 改成**低维 FFD 控制位移**，不要照搬教程的合成 GT 相机。 | **先读源码，不装 PyTorch3D**；仅当旧 renderer 不可用且磁盘/CUDA 审计允许时考虑安装 |
| **1 必读** | **NVIDIA nvdiffrast** https://github.com/NVlabs/nvdiffrast；核心例子 https://github.com/NVlabs/nvdiffrast/blob/main/samples/torch/cube.py；文档 https://nvlabs.github.io/nvdiffrast/ | 复用项目已有 `TASK-E4-PMGR-R1/code/camera_renderer.py` 的相机接口；按官方 `rasterize → interpolate → antialias` 得到可微前景 Mask，反传到世界顶点和 FFD；核对顶点索引、可见性/轮廓梯度。 | **优先复用已安装版本**，不要新克隆/重装；遵守 NVIDIA 许可 |
| **1 必读** | **NVIDIA PhysicsNeMo** https://github.com/NVIDIA/physicsnemo；FFD API https://docs.nvidia.com/physicsnemo/latest/physicsnemo/api/nn/functionals/geometry.html；`Mesh.free_form_deform` https://docs.nvidia.com/physicsnemo/latest/physicsnemo/api/mesh/transformations.html | `free_form_deform_points` 的 Bernstein / B-spline FFD 数学实现、`origin/extent`、控制点位移与 autograd。先验证零位移恒等、毫米坐标、梯度；FFD 仅作用主体。 | **不安装整个 PhysicsNeMo**。若现有环境已有可兼容函数则直接调用，否则按官方公式编写最小原生 Torch FFD（保留数学/许可来源） |
| **2 几何核对** | **PyGeM** https://github.com/mathLab/PyGeM；球体 FFD 教程 https://mathlab.github.io/PyGeM/tutorial-1-ffd.html；API https://mathlab.github.io/PyGeM/ffd.html | 使用球体控制格的显式位移例子作为 FFD 的**独立几何单元测试和可视化参照**，不用它承担多视角反向传播。 | **只读教程即可**，非必要不安装 |
| **2 碰撞增强** | **IPC Toolkit** https://github.com/ipc-sim/ipc-toolkit；项目文档 https://ipctk.xyz/ | 必要时使用 Python `ipctk` 的 barrier/`compute_collision_free_stepsize`；解决接近 Ring 时的可行更新步长，**不代替**优化器。 | 先重用现有 FCL + Blender EXACT；**仅连续碰撞导致停滞且空间充足时才考虑安装** |
| **2 几何 QA** | **libigl** https://github.com/libigl/libigl；Python 接口 https://libigl.github.io/libigl-python-bindings/；教程 https://libigl.github.io/tutorial/ | Laplacian/ARAP 正则、法向、曲率、网格质量与自交/几何审计；核对当前 mesh 质量函数。 | 旧 Open3D/SciPy 能完成则**不安装** libigl；CGAL 相关独立许可需审计 |
| **3 备选** | **Fast Free-Form Deformation** https://github.com/Yuliang-Huang/fast-free-form-deformation | 仅当原生 Torch FFD 明确成为瓶颈时，参考高性能 B-spline CUDA FFD 与 Jacobian；不引入其其他研究管线。 | **默认不用**，经性能/磁盘证明必要再引入 |

**代码复用优先级**：① 旧项目 `nvdiffrast` + 原 `K/c2w` + Ring CAD + 原生 Mask；② PyTorch3D 教程的训练组织；③ PhysicsNeMo FFD 的小型可微几何核；④ 现有 FCL/Blender 的 Ring 检查；⑤ 才考虑 IPC/ARAP/CUDA FFD。整个任务不需要完整安装多个大型工程。记录实际复用的**函数、源 URL、许可证、文件位置、兼容性**，不要只在报告列项目名字。

---

## 3. 本轮真正需要修复的三个问题

**问题 A：旧 R1 的损失与梯度路径不连续。** R1 已有 `camera_renderer.py`，但正式优化主要使用动态三角轮廓采样 + 最近点对应 + Jacobian/LM，并没有验证“FFD → antialiased Mask → autograd”的闭环。新任务必须证明该链在真实 Ring 遮挡内工作，并给梯度/有限差分小扰动对照。不能直接将旧动态轮廓 loss 换个名字继续训练。

**问题 B：观测和预测的 Ring 邻接忽略区不对称。** 统一使用 Ring CAD 的实际前后深度/遮挡关系和**预先固定**的 UNKNOWN 有效像素掩码；同一掩码同时作用预测与观测，Ring 背后和不确定边界不能硬当背景。训练目标采用固定像素分母的 soft Mask BCE/Dice/距离场和可信相对深度，原生/归档的 `352×640 / 360×640` 坐标、pixel-center 和单位均沿用历史接口。

**问题 C：旧训练把全源逐个误差下降视为硬限制。** 新损失允许视角之间的合理折中，采用全部训练视角的联合 soft objective + 不确定性相关的视角退让；**不再有** “某来源较 P0 恶化超过 0.5 px 就 veto” 的规则。真正硬约束仅为 Ring 实体不穿透、不可恢复翻折/自交与数值异常。采用自适应 trust-region 的实际/预测下降比调整步长；候选向 Ring 撞去时优先求可行新方向，而不是盲目反复缩步到零。

尤其注意：R1 已证明 G01 旧 P0 穿环约 `3.896047 mm³`，而保守 P0 的实体穿环为 0、最小三角间隙约 `0.082401 mm`。**主案例直接复用该安全 P0**（核对文件 SHA）；没有理由回到碰撞的旧 P0，也不能通过整体异常缩水换取形式安全。

## 4. 主体参数化与阶段计划

采用同一个冻结拓扑的公制三角网格，在模板局部坐标 `u` 上定义 `FFD(u;d)`，随后通过一直开放的九参数中心/旋转/半轴变换进入真实世界。FFD 控制位移以毫米为单位、初值全零；新增自由度采用嵌套残差或精确细化，确保**进入下一阶段时旧曲面不变**。几何更新始终共享一个三维实体，不为视角创建私有 Mesh。

| 阶段 | 释放的有效自由度 | 视角规则 | 预期观察 |
| --- | --- | --- | --- |
| P0 | 原安全九参数，FFD=0 | 统一 CAD 遮挡、有效像素和输入单位 | 安全起点及可微训练闭环通过 |
| P1 | 九参数 + 约 8–16 个低频 FFD 方向 | 从研究准入源选 3–5 个分布较好的主视角，其他研究准入源保持非零软监督/监控 | 产生肉眼可见的全局不对称或大小调整 |
| P2 | 累计约 32–64 个有效 FFD 方向 | 全部同场景合格来源联合优化 | 获得多视角一致支持的局部偏离椭球 |
| P3 | 尝试约 80–128 个局部方向 | 仅在多视角/可信 HERO 支持区域进一步解锁 | 观察更细形态，不让不可见背面无证据发散 |

参数预算是候选规模而不是必须全部开放的指标；对 Jacobian 高耦合、单视角不足、相互冲突的模式报告 `UNOBSERVABLE/CONFLICT`。P2、P3 被阻塞也必须保存有预算的尝试与诊断，不能仅复制 P1 并声称完成。网格背面标 `inferred`，不可称真实表面。

联合目标包含：固定像素的软 Mask/轮廓、HERO **相对深度差**、可信局部 HERO XYZ 的低权重软支持、FFD 弯曲/Laplacian/ARAP、软视角退让、Ring 近接 barrier；Ring 穿透及网格自交另做**接受前物理硬检查**。不设体积守恒为硬条件；也不得用面积/体积下降替代可信可见覆盖。

## 5. 实际案例、资格与 C0–C3 对照

1. **G01_004/E2 优先**，只取同一 `video004` 的已准入候选。R1 共有 7 个研究候选，但**严格相机资格仍是 `INSUFFICIENT_EVIDENCE`**；只能称条件性几何探索，不能认证物理精度。主实验允许把全部已准入视角用于训练，**此时不能再宣称有独立留出视角**。
2. **G06_004/E1 第二**，R1 有至多 5 个候选，其中部分是 `CONDITIONAL_USABLE`，资格不能升级。R1 过去没有执行该案例，需按同一物理规则生成安全 P0。缺少必要资产则 `NOT_EXECUTABLE`，保留 G01 完整结果。
3. 若希望独立测试，另外预冻结一个角度扇区作真正留出并**从头到尾不参加该实验臂训练/调参**；不能把主实验的全视角训练结果伪称为该留出协议的结果。资源紧张时，优先完成全视角主体实验，独立测试缺失如实写 `NO_HOLDOUT_AVAILABLE`。

| Arm | 几何 | 方法 | 本轮动作 |
| --- | --- | --- | --- |
| C0 | 旧谱法向形变 | 旧逐视角硬否决 | 冻结历史结果、以新稳定固定像素指标**只读复评**；R1 的 P2/P3 为 `NOT_RUN`，不要伪造 |
| C1 | 原谱法向形变 + 九参数 | 新联合 Mask/HERO 目标 + 可行 Ring 更新 | 真正运行；分离优化框架的贡献 |
| **C2（主线）** | **FFD 实体 + 九参数** | 新联合目标 + P0→P3 渐进式解锁 | 真正运行；与 C1 对比表示改变 |
| C3 | 与 C2 相同 FFD / P0 | 从一开始释放最终候选自由度 | 真正运行；检验渐进解锁贡献 |

C1/C2/C3 使用同一输入、相机、有效像素、目标尺度、计算预算与最终可候选自由度；差异必须能归因于模型/解锁策略。C0 是历史负基线，其运行条件不完全可匹配，不能强行计算优势百分比。

---

## 6. 具体执行顺序（不需要分阶段人工批准）

1. **先清理并做空间预算**（第 1 节）。只在有足够安全余量时继续安装必要的小依赖；环境允许时使用已有 GPU 与 CUDA。
2. 新建独立工作树/分支 `exp/TASK-E4-PMGR-FFD-002` 和 `experiments/TASK-E4-PMGR-FFD-002/`，从本地已有 R1/A1 路径复用输入，写 `INPUT_FREEZE`、磁盘审计和 1 页实验协议。**不要复制大数据到多个实验目录**，优先只读引用或只读符号链接并核验权限与 SHA；禁止将可写硬链接指向冻结资产。
3. 实现/适配最小的 `torch FFD`、旧 renderer 的真正可微 Mask loss、联合多视角训练循环与 Ring feasible step。优先直接复用表中 1 级项目的接口，不另建深度模型，不改相机。
4. **训练前必过测试**：零 FFD 控制位移保持已有安全椭球；控制点和九参数梯度非零且与有限差分局部一致；nvdiffrast antialias 前后梯度差有解释；真实/预测 Ring UNKNOWN 区一致；同一 K/c2w A→B 投影对齐；正/负间隙的 FCL/Blender EXACT 检查；P1→P2 零新增模式无几何跳变。
5. 按 P0→P3 连续执行 G01/C2，之后 C1/C3 和历史 C0 固定指标复评；有资源再执行 G06。**放弃 R1 的“累计拒绝超过 50% 立即全局停止”**。采用有限且有日志的方向重求与 trust-region budget；遇到不可恢复坐标/物理错误才停止该案例，不影响其他案例。
6. 完成科学报告并停止，等待人工确认。**禁止**未经批准扩展 39 组、回写 DXY 主线、进行 B1/B2、合并 G01 不同视频。

### 产物存储上限原则

持久保存每个案例/arm/阶段一份 Mesh、BEST/LAST_SAFE、精简 loss/梯度/物理指标 CSV、少量具有代表性的失败提议，以及核心 3–4 张图；所有短期优化中间量尽量流式统计，不持久化大量相同原生帧/重复权重/逐步渲染。所有被清理的科研中间文件如确属可再生，保留再生命令和源码哈希。

## 7. 交付与人工验收

本轮提交新分支代码与 `TECHNICAL_REPORT.md`、`REPRODUCE.md`、`DISK_AUDIT_BEFORE/AFTER.md`、`CLEANUP_MANIFEST.csv`、`SOURCE_REUSE_AUDIT.md`（所用外部仓库的函数、URL、许可、具体项目文件）、`FAILURE_LEDGER.md`、各阶段 Mesh/指标与核心图片。

**必须上传 3–4 张人工能直接判断的核心真实图：**

- 同一相机/尺度下 P0→P1→P2→P3 的**实际三维形变**（Ring 黑色 CAD）；
- 真实 RGB+Polyp/Ring Mask 与各阶段投影、Ring UNKNOWN 和轮廓差异，重点呈现 R1 曾被误判的 r06/r10；
- 可信 HERO XYZ、实体主体与 Ring 最小间隙/碰撞热图，颜色区分真实观测和推断区域；
- C0/C1/C2/C3 同源对照、更新接受率、固定 Mask/HERO-relative 指标以及典型失败。

每组另存六视角三维渲染与原 A→B 投影核对。报告必须公开所有失败和固定评价分母，包括 `NOT_RUN/NOT_EXECUTABLE/STAGE_BLOCKED`。不能仅凭训练 loss 下降宣布成果，更不能把保留的 HERO 点云画成已推断 Mesh。

**最后用一页总结回答：**

1. 清理了哪些可再生旧实验？实得腾出多少空间？哪些关键历史成果被保留、如何恢复？
2. FFD→可微 Mask→控制参数的反向传播闭环是否真正成立？实际最大/中位顶点移动是多少毫米？
3. 旧 R1 的轮廓采样跳变与 Ring 忽略带不对称是否已修复？多视角冲突能否通过软联合优化合理折中？
4. C1、C2、C3 中真正改善和不稳定分别出现在何阶段？Ring 是否始终零实体穿透，网格是否无折叠和自交？
5. 相机/Mask/HERO 证据是否足以支持 P3，还是应保留适度复杂主体、下一轮再申请 B1 可信 HERO 表面贴片？

把最终 **commit SHA、实验目录、四图链接、对照表、磁盘 before/after、复现实验入口**交给人工，然后停止等待审阅。
