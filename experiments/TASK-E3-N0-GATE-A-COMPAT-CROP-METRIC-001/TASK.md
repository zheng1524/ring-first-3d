# TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001

## Role：Phase E3-N0 Research Execution Agent

你是 Reference-Ring Anchored Visible-Surface Reconstruction of Polyps 项目的现有Codex执行智能体。

**研究者已正式批准 Phase E3-N0 Gate A。**

本次只执行Gate A，不自动进入Gate B/C/D。

项目仓库：

https://github.com/zheng1524/ring-first-3d

NeuralFusion官方仓库：

https://github.com/weders/NeuralFusion

任务名称：

**Pretrained NeuralFusion — Official Model Compatibility, HERO Depth Adaptation and Cross-View Geometry Validation**

本轮目标是为NeuralFusion建立可靠的G01_004多视角HERO输入接口，并证明独立裁剪不会破坏原有Ring-First相机之间的三维关系。

本轮不执行NeuralFusion实际融合前向，不启动GPU推理，不训练任何模型。

---

## 一、执行前必须阅读

首先读取以下项目规范：

- `AGENTS.md`
- `COLLAB_STANDARD_v1.3.md`

以及PM审计和任务文件：

- `PM_E3N0_FEASIBILITY_AUDIT.md`
- `PM_E3N0_PREREGISTRATION.md`
- `CODEX_TASK_E3N0_GATE_A_DRAFT.md`
- `PM_E3N0_GATE_BC_PREVIEW.md`

如果这些PM文件尚未上传GitHub，可以从研究者提供的文件链接获取，不允许因文件缺失而自行编造研究规则。

然后重点核查现有五项研究成果：

1. `TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`
2. `TASK-E3-B-LOCAL-HERO-FIELDS-001`
3. `TASK-E3-C-VISIBILITY-CONSENSUS-001`
4. `TASK-CAMERA-GATE-G01-004-PILOT-001`
5. `TASK-E3-D0-OPEN3D-TSDF-BASELINE-001`

其中，**E3-A视角分区、Camera Gate和E3-D0输入适配必须优先复用**。

禁止重新开展完整资产审计、重新训练HERO、重新估计相机位姿或重复设计一套已有的投影算法。

### 本次必须优先寻找和复用的代码

| 模块 | 优先来源 |
|---|---|
| 视角分区及来源身份 | E3-A、历史View Partition |
| 相机资格与真实图像几何 | Camera Gate |
| 世界坐标与相机变换 | Ring-First已有代码 |
| HERO深度反投影 | E3-B、E3-D0 |
| K与native/archived转换 | E3-D0 `hero_tsdf_adapter.py` |
| 真实三维射线投影 | E3-D0 `evaluate.py`及其依赖 |
| CAD遮挡判定 | Camera Gate、E3-C、E3-D0 |
| 真实三维可视化 | `visualization/real_p0_renderer.py`及现有D0绘图代码 |

先实际检查函数及参数契约，形成：

`CODE_REUSE_MATRIX.md`

其中明确记录：

- 原代码路径；
- 实际调用函数；
- 复用方式；
- 是否需要薄适配；
- 是否与现有实现产生重复；
- 原始源码SHA。

**不得仅因为旧代码分散在多个实验目录，就重新实现同样的几何功能。**

---

## 二、固定实验对象与视角

首轮只使用G01_004。

按照以下固定顺序组织六个来源：

| 序号 | 来源 | 分区 | 角色 |
|---|---|---|---|
| 1 | ref08 | B3 | CORE |
| 2 | ref13 | B5 | CORE |
| 3 | ref03 | B2 | CORE |
| 4 | growth_r04 | B3 | 条件性桥接 |
| 5 | new_r00 | B1 | 条件性新增方向 |
| 6 | growth_r14 | B4 | 条件性新增方向 |

**不要根据点云数量、最终视觉效果或其他后验指标重新选取视角。**

必须继承：

- E3-A的View Partition结果；
- Camera Gate历史资格；
- D0的六来源白名单；
- 原始HERO来源DAG；
- 相机K/c2w及Ring CAD身份。

Camera Gate的`INSUFFICIENT_EVIDENCE`不能修改成`CAMERA_WRONG`或`CAMERA_CERTIFIED`。

growth_r14尚无充分独立相机资格，仍作为条件性候选保留。

Gate A的目标是验证输入变换，不是重新认证相机精度。

---

## 三、官方NeuralFusion兼容性审计

读取官方：

- `pipeline/pipeline.py`
- `pipeline/model.py`
- `pipeline/extractor.py`
- `pipeline/integrator.py`
- `pipeline/translator.py`
- `pipeline/utils.py`
- `training/pipeline.py`
- `training/database.py`
- `environment.yml`

检查官方预训练权重：

**主候选：**

`pretrained_models/shapenet_noise_005/version_0/checkpoints/best.ckpt`

**备用静态对照：**

`pretrained_models/tanks_and_temples/version_0/checkpoints/best.ckpt`

本轮采用ShapeNet权重作为主兼容性对象。

需要核实：

1. Python/PyTorch/CUDA/Lightning依赖；
2. checkpoint实际SHA256；
3. checkpoint和配置是否严格匹配；
4. 官方128³潜在体素结构；
5. 17维特征与count通道定义；
6. 240×320输入限制；
7. SDF/occupancy解码接口；
8. 官方外部`graphics`等依赖来源；
9. 模型坐标与物理体素尺度。

允许CPU上的模型构造和严格checkpoint加载测试。

禁止通过`strict=False`忽略权重不匹配。

禁止运行NeuralFusion真正的多视角融合前向。

如果需要安装依赖，应首先评估是否能够在隔离环境完成；涉及修改用户主环境或额外权限时停止并报告。

---

## 四、正式裁剪策略

研究者已明确决定：

**各视角独立等比例裁剪。**

不要求不同视角使用相同二维缩放比例。

每个来源分别执行：

1. 读取原生HERO深度。
2. 读取对应Polyp和Ring Mask。
3. 确定Polyp∪可见Ring的外接框。
4. 按统一规则扩展ROI。
5. 等比例适配到320×240。
6. 必要时加入Padding。
7. 同步更新相机内参K。

初始ROI建议：

- 20%边界扩展；
- 至少16个原始像素保护；
- 保留完整息肉Mask及Ring上下文；
- 不允许因裁剪损失可能的细柄和独有侧面。

Depth只保留合法Polyp深度。

Ring、Background、Padding和Unknown不能被填充为假深度。

### 必须保留的逐源信息

每来源保存：

- 原始图像尺寸；
- 裁剪框；
- 缩放比例；
- Padding；
- 原始K；
- 裁剪后K；
- 原生合法深度数量；
- 裁剪损失；
- 原始与裁后像素映射；
- 原始输入SHA。

如果某个来源的细结构在320×240下严重损失，不允许通过手工调整该来源ROI获得漂亮结果。

应报告失败及需要修订的统一规则。

---

## 五、最重要的实验：跨视角空间关系保持

本节是Gate A的最高优先级。

### 实验A：单视角反投影一致性

对于每个来源，比较：

\[
X_{world}^{original}
\]

与

\[
X_{world}^{cropped}
\]

要求使用相同原始物理点身份进行比较。

不得仅计算两个点云的最近邻距离。

每个来源至少选取1000个固定、可追踪的合法深度点，并覆盖：

- 息肉头部；
- Mask边界；
- Ring邻域；
- 可能的细柄；
- 深度突变位置。

分别统计：

- 解析几何误差；
- 深度重采样误差；
- 有效像素保留情况。

### 实验B：CORE跨视角投影一致性

固定六组有向关系：

1. ref08→ref13
2. ref13→ref08
3. ref08→ref03
4. ref03→ref08
5. ref13→ref03
6. ref03→ref13

对同一个世界三维点，比较：

**原始相机投影再进行裁剪坐标变换**

与

**直接采用裁剪后K进行投影**

两者必须一致。

数学合同：

\[
\boxed{\pi'_j(X)=A_j\pi_j(X)}
\]

其中：

- \(A_j\)：目标视角的裁剪/缩放/填充变换；
- \(\pi_j\)：原始投影；
- \(\pi'_j\)：使用裁后K的投影。

建议使用浮点精度下的严格数值容差，并在正式计算结果产生前冻结。

报告：

- median；
- p95；
- maximum；
- 有效投影数量；
- 图像边界外数量；
- Mask/CAD遮挡状态。

不能通过移除失败射线改善误差。

### 实验C：新增条件性来源

对growth_r04、new_r00、growth_r14进行同样的跨视角变换检查。

但要注意：

**这个实验只能证明裁剪没有改变原始相机关系，不能证明原相机位姿本身正确。**

严格保留Camera Gate原有资格标签。

---

## 六、统一模型体素与公制坐标

根据现有六份HERO有效深度与冻结相机，建立一个共同的物理ROI。

必须区分：

- `metric_frame_mm`
- `model_frame`

采用统一且可逆的相似变换。

所有来源共用：

- 模型空间原点；
- 模型尺度；
- 体素大小；
- 世界坐标系。

不同来源的图像裁剪缩放比例可以不同，但**不能对应不同的三维模型缩放比例**。

使用Ring CAD检查公制尺度逆变换。

还需要检查：

- HERO点是否越出共同体素ROI；
- 是否有异常远端深度；
- 主体占据多少体素；
- 模型体素是否足以表达细小结构。

若单个极端深度值造成明显的体素域问题，记录并停止请求判断，不自动删除输入。

---

## 七、Gate A正式验收条件

以下条件全部检查：

| 门禁 | 验收目标 |
|---|---|
| A1 来源身份 | 六来源及SHA一致 |
| A2 裁剪几何 | 单源解析反投影保持 |
| A3 跨视角关系 | 六组CORE有向投影一致 |
| A4 公制尺度 | Ring及共同模型坐标可逆 |
| A5 Mask有效域 | Polyp、Ring、Unknown、Padding正确分离 |
| A6 网络兼容性 | 官方checkpoint严格加载、结构匹配 |
| A7 代码复用 | 实际复用历史View Partition、Camera Gate和D0 |
| A8 数据保护 | 无GT、无训练、无旧资产修改 |

对于有限精度数值门槛，先明确精度与计算实现，预登记后才能开展正式验收。

**Gate A通过不意味着NeuralFusion的融合质量通过。**

它只证明后续能够在工程条件正确的情况下开展Gate B。

---

## 八、必须上传的四张核心复合图

### Figure 1：真实输入与裁剪

六来源真实RGB、Polyp/Ring Mask、ROI、320×240裁剪深度、Padding及K变化。

### Figure 2：裁剪前后三维一致性

最重要的一张图。

展示：

- 三CORE原始HERO点云；
- 三CORE裁剪后HERO点云；
- 统一毫米尺度；
- 相同观察相机；
- 黑色Ring CAD实体。

两侧的三维几何关系必须能够直接比较。

不得使用合成纹理平面或任意补面。

### Figure 3：跨视角几何投影验证

六组CORE有向投影关系。

展示：

- 原始目标RGB；
- 原始深度投影位置；
- 裁剪后投影位置；
- 逆变换后的投影误差；
- Mask边界和CAD遮挡。

包含完整数值表。

### Figure 4：模型尺度与失败案例

展示：

- 三维潜在体素ROI；
- Ring实体；
- 真实HERO点云；
- 细柄、边界和远端异常；
- 裁剪可能损失的结构。

必须包含真实的负面或不确定案例。

---

## 九、工程交付

在独立实验分支中提交：

`experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001/`

至少包含：

- `TECHNICAL_REPORT.md`
- `FAILURE_LEDGER.md`
- `REPRODUCE.md`
- `CODE_REUSE_MATRIX.md`
- `CHECKPOINT_COMPATIBILITY_MATRIX.csv`
- `SOURCE_AND_CROP_MANIFEST.json`
- `METRIC_TRANSFORM.json`
- `CROP_GEOMETRY_TESTS.csv`
- `CROSS_VIEW_PROJECTION_VALIDATION.csv`
- `GT_ISOLATION_AUDIT.md`
- 四张核心PNG

上传前检查：

- 是否修改历史资产；
- 是否误上传巨大原始数据或权重；
- 是否保留完整输入SHA；
- 是否有失败被静默排除；
- 是否所有图都来自真实输入与真实三维坐标。

不要在本轮生成NeuralFusion融合Mesh。

---

## 十、完成后必须停止

本次用户只批准Gate A。

禁止自动进行：

- F0–F2融合；
- F3–F5融合；
- 逆序网络推理；
- 新Open3D融合对照；
- GPU运算；
- NeuralFusion训练；
- 新HERO推理；
- 相机优化；
- G2轮廓删除或G3加权融合。

如果Gate A失败，保留全部失败证据。

如果Gate A通过，提交：

`GATE_A_PASS / GATE_A_FAIL / NOT_EVALUABLE`

并在最终报告中明确：

1. 官方模型是否兼容；
2. 六来源裁剪是否有效；
3. 三CORE跨视角关系是否严格保持；
4. 统一物理尺度是否可靠；
5. 是否建议申请Gate B。

**完成后停止，等待PM和研究者验收。**

不得把“Gate A通过”自动理解为“Gate B获得授权”。