# TASK-NEURAL-E0-COMPARE-001｜Codex 首轮任务草案

**状态：PROPOSED — 仅供 PM 审计和用户审批；不是立即执行授权。**

## Role
你是Ring-First 3D已有单实例 Codex 执行智能体。任务不是训练新的医学基础模型，而是以冻结数据、可复用工程和独立验证建立两条候选重建路线的公平竞争基线。

## 本轮只允许的工作包

**A. Repo+官方代码复用审计**：读取 `AGENTS.md`、`COLLAB_STANDARD_v1.3.md`、最新边界生长/MASt3R分区的 `TECHNICAL_REPORT`、`REPRODUCE`、SOURCE manifest；查找冻结HERO输入和原始RGB/K/c2w/Mask/UV/XYZ及每组valid pose；验证现有`real_p0_renderer.py`与A→B复用入口；查官方 MapAnything/NeuS2/MonoSDF/SparseRecon 实现、版本、权重及许可证。只添加adapter，不重写camera/depth/render系统。

**B. E0输入协议**：四物理组 G01/G06/G08/G07，冻结有效图像及真正留出帧；G07不合格相机单列；G01 004/005必须先分别处理；三照片位姿尚未认证只做诊断；严格转换mm↔m、K resizing、c2w/w2c、Z-depth与射线距离，记录SHA。GT资产设置只读阻断选择路径。

**C. 小规模烟测**：在独立环境对MapAnything 官方预训练模型跑最小RGB/K/已认证pose/depth合法组合；对成熟SDF实现做最小单场景形状优化。出现GPU故障写出完整错误并停止该GPU分支，不能换成CPU极慢运行掩盖硬件阻塞，也不能称算法失败。

**D. 公平对照（需单独批准）**：在相同训练/留出场景中完成SDF vs MapAnything和历史F3/Cleaned的相机、Ring、Polyp覆盖、真实A→B、CAD穿插、支持区与运行成本比较；四组报告、重点G01两个视频；不允许误把未经认证跨视频H作为共同GT。仅在用户批准后的明确任务中执行GPU批量运行。

## 阶段门槛

- A阶段：可复用脚本索引；外部权重依赖与可用性；4组实际资格；不能用论文推断本地GPU通过。
- B阶段：sample/holdout源身份、两臂输入条件、相机物理单位全部通过静态检查。
- C阶段：两臂最小真实样本产生公制单位可审计输出；失败明确分类（CUDA/权重/接口/方法）。
- D阶段：同视角/同分母/共同像素的真实证据和 4 物理组完整状态，允许 NOT_EVALUABLE 和 BOTH_NOT_PROVEN。

## 强制可视化

每阶段3—4张核心复合图。四组至少各有输入资格与相应真实可评估结果。G01必须并列标明：`SINGLE-VIDEO — video004`、`SINGLE-VIDEO — video005`、`CROSS-VIDEO — NOT FUSED`（未通过认证时）；源真实XYZ、相同CAD Ring尺度、真实RGB目标/投影、Mask与未知区域。MapAnything点云和SDF提取点云的可视化渲染器应复用历史固定相机视角/点大小；若无法直接使用旧函数，在adapter层转换为通用XYZ格式。

## 保护

任何原始 P0、冻结相机、HERO权重、Ring CAD、Dxy文件不可改；不读取GT用于算法选择；不将不受真实观测支持的神经补全区冒充可见面；不创建不存在的三维相机位姿；不得直接在旧脏main执行。使用独立任务分支、显式git add、小文件与关键PNG增量推送。最终提交 TASK-ID、commit SHA、中文技术报告、逐阶段图和失败证据。

## PM需在正式派发前补全的细节

1. 具体输入source manifest与4组参考帧；
2. 所采用的Neural SDF官方实现、安装方式、训练配置；
3. MapAnything实际版本及官方支持模式；
4. 预冻结留出帧与是否被HERO源使用；
5. GPU预算上限与不扩大搜索原则；
6. 分阶段任务编号/commit位置；
7. 已批准的科学边界与核验方式。
