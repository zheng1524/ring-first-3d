# TASK-MAINLINE-ASSET-CONSOLIDATION-001
# 息肉三维重建主线资产清理、集中与可复现性验收

## 一、任务角色与最终目标

你是 Ring-First Polyp 3D Reconstruction 项目的工程维护与资产管理负责人。

本轮不是科研算法实验，而是一次正式的：

- 存储空间清理；
- 技术路线收敛；
- 源码和依赖集中；
- 历史重要资产保留；
- 旧实验目录清理；
- 主线独立运行验证。

项目仓库：

`zheng1524/ring-first-3d`

本轮执行分支：

`maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001`

创建分支时使用以下冻结基线：

- 来源分支：`exp/TASK-E4-G01-G03-GROWTH-RECOVERY-001`
- 来源提交：`bac3fc89ef95db522b63cf6bb98e6914b9382864`

如果来源分支已经发生变化，先审计差异，不得覆盖新提交。

### 最终目标

建立一个统一的主线科研工作空间，使今后的研究者只需要找到一个明确的项目入口，就能理解和运行：

1. Ring-First 相机恢复；
2. MVSAnywhere / HERO 深度恢复；
3. 多视角数据与投影；
4. 前置二维几何及三维主体拟合；
5. 主体更新；
6. 嵌入式 B-spline 柄部生长；
7. 多视角轮廓与 Ring 约束；
8. 三维评价和可视化。

同时保留与主线相关的重要历史技术：

- MVS 的 A→B 重投影和可视化；
- 早期 PyTorch3D 主体优化；
- HERO 原生深度监督更新；
- 多视频相机配准和几何一致性诊断；
- 重要失败实验及其结论。

最终要求：

**集中的是技术资产和可复现入口，而不是把所有历史实验目录原封不动地复制到一个新文件夹。**

---

# 二、当前主线状态与不可改变的研究判断

本轮以最新 G01/G03 Growth Recovery 为研究方向基准。

当前技术路线：

二维息肉轮廓 + 主体初始化  
→ 多视角主体更新  
→ 嵌入式 B-spline 柄部生长  
→ Boolean Union 形成统一外部 Mesh  
→ 多视角投影验收  
→ Ring 碰撞门控  
→ 后续引入 HERO 深度约束  
→ 后续解决 G03 跨视频配准。

最新实验结果必须保留以下事实：

### G01

- 自动生长门禁通过。
- 外露柄长：1.726844 mm。
- FIT IoU：0.932784。
- HOLDOUT IoU：0.933253。
- 最终 Mesh 自交数量为0。
- 但近端截面仍有最大0.047185 mm的局部外露。
- 固定 INITIAL→GT 坐标框架下的 MAE 有所恶化。

### G03

- 正式生长未通过。
- 失败原因：`PER_VIEW_PROTECTION`。
- 视频005两个视角的 IoU 分别下降0.023444和0.012446。
- 正式柄长为 NaN。
- 失败尝试和近端截面审计必须保留。

本轮将这条路线标记为：

`ACTIVE_RESEARCH_MAINLINE`

而不是：

`CERTIFIED_SCIENTIFIC_BASELINE`

不得因为本轮工程测试通过，就宣称息肉三维重建已经完成科学验收。

---

# 三、最高优先级：保护范围

这是一个可能涉及大量文件删除、复制和目录移动的任务。

必须严格遵守以下保护条件。

## 3.1 保护 Git 历史

禁止：

- `git filter-repo`
- 重写历史；
- force push；
- 删除远程实验分支；
- `git reset --hard`；
- `git clean -fdx`；
- 无差别 `rm -rf`；
- 无差别 `git add .`。

本轮使用独立维护分支。

清理 Git 当前工作树中的文件，不等于删除 Git 历史中的文件对象。

不得宣称通过普通删除提交已经释放了 GitHub 历史存储空间。

如果未来需要重写历史、缩减远端仓库体积，必须单独提出方案。

## 3.2 保护其他研究项目

以下内容只读：

- `/home/liu/new-polyp-dxy`
- 旧宿主科研仓库 `/home/liu/polyp_research`
- 其他独立研究项目。

特别是：

DXY V9.1 主线与三维重建严格隔离。

不得为了集中资产而复制、修改或覆盖 DXY 的源码、权重和正式输出。

旧科研工作树中的源码可以作为只读迁移来源，但不得直接在原工作树中清理。

## 3.3 保护原始科学资产

以下内容默认保留：

- 原始 RGB；
- 原始视频；
- 原始 Polyp Mask；
- 原始 Ring Mask；
- GT；
- 原始 HERO 深度；
- 原始 Ring CAD；
- 官方模型权重；
- 原始相机数据；
- 具有唯一科研价值的预测结果。

大文件不等于废弃文件。

不要为了节省磁盘而删除唯一的原始观测或模型权重。

这些文件可以继续留在原有 LOCAL_ONLY 位置，通过 SHA256 和 manifest 统一管理，不要求全部复制进 Git。

---

# 四、阶段0：建立完整资产地图

先不修改任何文件。

必须对当前工作空间进行只读盘点。

## 4.1 盘点范围

至少检查：

1. 当前 `ring-first-3d` 仓库；
2. 当前仓库所有实验目录；
3. 历史 Git 分支；
4. Git worktree；
5. 本地独立实验工作目录；
6. Ring-First 原始源码目录；
7. MVSAnywhere/HERO 相关源码；
8. PyTorch3D 历史实验；
9. 可视化和 Mesh 输出目录。

预期工作区包括：

- `/home/liu/ring_first_3d`
- `/home/liu/polyp_research/ring_anchor_3d`

实际路径必须先核实，不能直接假定。

## 4.2 空间统计

执行：

```bash
df -h
du -sh *
du -ah . | sort -rh | head -200
git count-objects -vH
git worktree list
git branch -a
```

同时统计：

- 每个实验目录的大小；
- 每个实验的文件数量；
- 大于1MB、10MB、100MB的文件；
- 重复文件数量；
- 完全相同 SHA256 的文件；
- 已经失去调用关系的中间产物；
- 原始数据和派生数据的占用。

## 4.3 生成资产清单

新建：

`maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/`

生成：

- `INITIAL_STORAGE_REPORT.md`
- `ASSET_INVENTORY.csv`
- `ASSET_INVENTORY.json`
- `DUPLICATE_ASSET_REPORT.json`
- `DEPENDENCY_REFERENCE_GRAPH.json`
- `CLEANUP_CANDIDATES.json`

每个资产必须记录：

| 字段 | 内容 |
|---|---|
| path | 原始路径 |
| task_id | 来源实验 |
| size_bytes | 文件大小 |
| sha256 | 完整哈希 |
| tracked | 是否被 Git 跟踪 |
| asset_type | 源码/配置/原始数据/中间产物/最终结果 |
| dependencies | 被谁调用或引用 |
| reproducible | 是否能够重新生成 |
| scientific_value | 科研价值 |
| proposed_action | KEEP/COPY/ARCHIVE/DELETE |
| reason | 决策原因 |

不能只凭文件名判断文件是否重复。

必须以 SHA256 和实际依赖关系为依据。

---

# 五、阶段1：优先清理大型中间产物，释放空间

这是本轮第一个实际执行阶段。

用户已经授权清理：

- 已废弃探索路线的大型中间产物；
- 与当前主线无关且没有独立科研价值的庞大派生结果；
- 完全重复的可视化数据；
- 可重新生成的缓存和临时文件。

因此，本阶段不要只生成建议清单，而应实际完成符合授权范围的安全清理。

## 5.1 第一类：直接删除的对象

可以优先清理：

1. `__pycache__`；
2. 已确认无用的临时文件；
3. 重复的浏览器缓存；
4. 重复的渲染缓存；
5. 相同 SHA256 的重复可视化数据；
6. 多次复制的相同中间 JSON；
7. 已经失去用途的临时训练输出；
8. 可由保留脚本和输入直接重新生成的重复中间产物。

同一内容只保留一个规范副本。

删除其他完全相同的副本，并更新所有引用。

## 5.2 第二类：废弃探索路线的中间产物

根据：

`docs/registry/FAILURE_AND_DEPRECATED_ROUTES.md`

进行审计。

重点排查：

- TSDF；
- NeuralFusion；
- MonoSDF；
- Visual Hull；
- 已停止的 SDF/隐式表面实验；
- 已明确不再使用的自由顶点探索；
- 旧的独立主体拟合及重定位尝试；
- 与当前主体生长主线无关的失败融合中间产物。

对这些实验：

保留：

- TECHNICAL_REPORT；
- RESULT_CARD；
- FAILURE_REGISTRY；
- 核心算法源码；
- 重要的负面结论；
- 1–3张最能说明问题的代表性可视化；
- 可追溯的 commit 和来源 SHA。

允许删除：

- 大规模重复训练轨迹；
- 大量重复 Mesh；
- 无法提供额外信息的中间可视化；
- 重复的预测 JSON；
- 已经失去意义的训练 checkpoint；
- 仅用于调试且已被最终修复替代的输出。

注意：

MonoSDF 没有完成充分训练，不能将其描述为充分训练后的算法失败。

## 5.3 第三类：重复运行目录

重点检查：

- `attempts/`
- `runs/`
- `review_assets/`
- `evidence/`
- `visualization/`

不要直接删除整个目录。

应先区分：

- 唯一有效运行；
- 已被修复版本替代的失败运行；
- 重复复制的结果；
- 具有重要诊断价值的失败运行；
- 仅供可视化的重复数据。

特别注意：

上一轮 Growth Recovery 中：

- G01 被接受的 Mesh；
- G03 被拒绝的完整证据；
- iteration 24 的历史候选；
- G01/G03 根部截面审计；

均属于重要资产，不得清理。

## 5.4 删除执行规则

执行前生成：

`PHASE1_DELETE_MANIFEST.json`

每项记录：

- 原始路径；
- SHA256；
- 字节数；
- 删除原因；
- 保留的替代文件；
- 是否可重新生成；
- 是否涉及 Git 跟踪；
- 删除后空间变化。

对完全重复和明确可再生成的临时文件，直接按 manifest 执行。

对于唯一的原始观测、唯一模型权重、唯一预测、关键失败证据以及无法确认依赖关系的资产，保留。

不要为了满足释放空间的目标强行删除未知资产。

完成后生成：

`PHASE1_CLEANUP_REPORT.md`

报告实际释放的磁盘空间，而不是估算值。

---

# 六、阶段2：确定需要集中保留的主线技术资产

这是本轮最重要的科研资产筛选环节。

不要简单按照实验名称判断是否保留。

应按照技术路线和未来依赖关系判断。

## 6.1 A类：必须完整保留的当前主线

### A1. Ring-First

保留：

- Ring CAD；
- Ring-First 相机恢复核心源码；
- 相机标定及坐标转换；
- Ring 投影；
- 原始相机结果；
- 相机质量诊断；
- 相关测试和配置。

保留来源及版本：

- 原始 Ring-First 源码；
- 当前仓库的 Ring-First 适配模块；
- `TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001` 中实际使用的相机接口。

不能只保留最后的相机矩阵而丢失恢复源码和来源。

### A2. MVSAnywhere / HERO

保留：

- 官方模型加载；
- 原生深度推理；
- Depth Back-Projection；
- 原始点云生成；
- Native Mesh；
- 原始 FaceID/PixelID；
- 深度与相机坐标转换；
- 官方模型 commit；
- 权重 SHA；
- 推理配置；
- 相关可视化和评价代码。

重点参考：

`TASK-E4-HERO-BODY-ADAPT-018`

以及：

`TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`

官方权重和大型模型目录继续采用 LOCAL_ONLY/外部依赖管理，不重复复制。

### A3. 前置二维几何和主体拟合

这是当前柄部生长路线的基础，必须保留。

重点包括：

- DXY 像素几何接口；
- 二维椭圆拟合；
- 九参数主体模型；
- 解析椭球投影；
- 主体初始化；
- 完整 Mask 轮廓拟合；
- 主体基底约束。

保留来源：

- `TASK-E4-A1-COARSE-BODY-001`
- `TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`
- `TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`
- `TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001`

重点保留实际使用的模型、投影、优化器、测试和重要对照结果。

不要把不同版本的主体拟合代码混成一个未经验证的新版本。

### A4. 主体更新

必须保留：

- `TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001`
- `TASK-E4-STRUCTURED-BODY-UPDATE-002`

尤其是：

- Deformation Graph；
- Smooth ARAP；
- 多视角轮廓对应；
- ProjectionGate；
- RingCollisionGate；
- B-spline Sweep；
- RMF；
- 主体与柄部连接；
- Boolean Union；
- 几何验收。

这些是当前柄部生长的直接技术基础。

### A5. 当前柄部生长主线

必须完整保留：

`TASK-E4-G01-G03-GROWTH-RECOVERY-001`

至少包括：

- 实际执行源码；
- 运行协议；
- 输入冻结文件；
- G01 最终结果；
- G03 失败结果；
- 根部几何审计；
- GATES；
- UPDATES；
- 指标；
- 回归测试；
- 代表性可视化；
- 完整报告。

不能因为 G03 失败而删除 G03 相关内容。

未来的 HERO 深度约束和跨视频配准都要在这条主线上继续推进。

---

# 七、阶段3：保留不直接属于主线但重要的技术资产

这部分不能简单删除。

## 7.1 MVS A→B 重投影与可视化

这是重要的独立诊断工具。

重点保留：

`TASK-VIEW-OBSERVABILITY-GT-EVAL-001`

尤其是：

`code/reprojection.py`

保留：

- `render`
- `evaluate`
- 对应的 `io_utils`
- CAD 和必要输入接口；
- 完整可运行的 A→B 可视化；
- 关键结果和报告。

同时搜索整个仓库中的：

- A→B；
- Source→Target；
- Reprojection；
- FaceID；
- Barycentric；
- Visibility；
- Depth Layer。

如果其他任务中存在更完整或更直观的 A→B 可视化，也应保留。

要求：

最终只保留一套明确的规范入口。

可以有多个历史实现，但必须说明各自的功能和差异。

不能因为 A→B 可视化不直接参与当前柄部生长，就将它删除。

## 7.2 PyTorch3D 深度监督更新

这是另一个必须保留的独立技术方向。

重点：

`TASK-E4-HERO-BODY-ADAPT-018`

以及：

`TASK-E4-PYTORCH3D-014`

`TASK-E4-PYTORCH3D-RING-AWARE-001`

重点保留：

- 原生 HERO 深度损失；
- 早期深度监督损失；
- PyTorch3D Renderer；
- Visibility 修复；
- 轮廓损失；
- 主体更新；
- 接触约束；
- 重要失败和梯度诊断；
- G03 深度监督失败证据。

特别注意：

历史 T28 深度块和 T30 完整原生 HERO 深度块是不同的观察模型。

必须分别保留，不能混成一个模块。

这些实验是未来将 HERO 深度误差引入当前主体—柄部更新路线的重要技术参考。

## 7.3 多视频相机配准

保留以下重要技术：

- RoMa/SIFT；
- Ring 与背景联合配准；
- BA；
- 跨视频坐标一致性；
- 多视频视角诊断；
- 主体锚定配准。

重点检查：

- `TASK-E4-RING-ANCHORED-JOINT-BA-021`
- `TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001`
- `TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001`

这些资产对于下一阶段 G03 的视角配准诊断非常重要。

保留核心源码、报告、指标和代表性可视化即可，不需要保留所有重复运行产物。

## 7.4 已批准的可视化工具

保留：

- Real P0 Renderer；
- 多视角重投影；
- Mesh 六视角可视化；
- Ring CAD 投影；
- HERO 与主体对照；
- A→B 源面重投影。

不能删除其依赖的数据接口。

---

# 八、阶段4：建立统一的主线资产结构

完成第一轮清理之后，开始复制和集中资产。

建议在仓库中建立：

```text
mainline/
│
├── README.md
├── PIPELINE.md
│
├── manifests/
│   ├── MAINLINE_ASSET_MAP.json
│   ├── DEPENDENCY_LOCK.json
│   ├── EXTERNAL_INPUTS.json
│   ├── SOURCE_PROVENANCE.json
│   └── REPRODUCIBILITY_STATUS.json
│
├── configs/
│   ├── ring_first/
│   ├── mvs_hero/
│   ├── body_initialization/
│   ├── body_update/
│   └── stalk_growth/
│
├── scripts/
│   ├── run_ring_first.sh
│   ├── run_hero.sh
│   ├── run_body_initialization.sh
│   ├── run_body_update.sh
│   └── run_stalk_growth.sh
│
├── visualization/
│   ├── a_to_b/
│   ├── hero/
│   ├── body/
│   └── stalk_growth/
│
├── references/
│   ├── depth_supervised_pytorch/
│   ├── cross_video_registration/
│   └── historical_diagnostics/
│
└── results/
    ├── G01/
    └── G03/
```

实际代码优先集中到现有：

`src/ring_first_3d/`

如果已有模块能够作为规范入口，优先复用，不要再创建第二套重复 Python 包。

`mainline/` 主要承担统一入口、配置、资产映射、运行脚本和精选结果组织。

## 8.1 复制规则

本阶段必须以 COPY 为主，不得先移动原始源码。

每个复制的源码文件都必须记录：

- 原始路径；
- 来源任务；
- 来源 commit；
- 原始 SHA256；
- 新路径；
- 新文件 SHA256；
- 依赖；
- 是否修改；
- 修改原因。

如果只做了目录整理，文件内容必须保持完全一致：

\[
SHA256_{\mathrm{source}}
=
SHA256_{\mathrm{copy}}
\]

如果因为路径、导入等原因必须修改代码，应另行记录：

`ADAPTED_COPY`

不能将修改后的文件称为原始源码。

## 8.2 不要复制大型原始数据

大型原始数据、权重和环境继续保留在原来的位置。

通过：

`EXTERNAL_INPUTS.json`

记录：

- 原始路径；
- 文件大小；
- SHA256；
- 来源；
- 依赖任务；
- 数据用途；
- 是否可用。

确保新主线可以找到这些资产。

不要复制多个相同的模型权重。

---

# 九、阶段5：建立真正可运行的依赖闭包

这是本轮核心验收。

不能仅仅将文件复制到一起，就声称整理成功。

需要检查所有跨目录依赖。

特别注意：

1. 动态 Python import；
2. `sys.path` 修改；
3. `Path(__file__)` 的父目录假设；
4. 硬编码绝对路径；
5. 外部模型权重；
6. 官方 MVS/HERO 代码；
7. Open3D；
8. PyTorch3D；
9. Blender Boolean；
10. Ring CAD；
11. 数据路径；
12. 相机与坐标转换。

要求：

从新主线入口执行时，不能依赖某个已经被清理的旧实验目录。

对于无法复制的官方模型或外部项目，应通过明确的版本和路径依赖管理，而不是偷偷依赖本机某个未记录的目录。

---

# 十、阶段6：独立运行和结果一致性验证

这是本轮最重要的验收。

所有核心资产复制完成后，必须在新主线目录中运行。

不能直接调用旧实验目录中的脚本来假装验证成功。

## 10.1 第一层：工程测试

执行：

- 当前已有的247项 Growth Recovery 回归测试；
- 现有 Harness Preflight；
- Contracts；
- Reuse Audit；
- Smoke Tests；
- 主体初始化测试；
- PyTorch3D Renderer 测试；
- B-spline Sweep 测试；
- Ring CollisionGate 测试；
- A→B 重投影测试。

所有测试结果记录在新主线目录。

## 10.2 第二层：关键模块重放

至少完成以下重放：

| 模块 | 验证内容 |
|---|---|
| Ring-First | 固定输入下的相机结果和坐标转换 |
| MVS/HERO | 固定样本的一次原生深度推理 |
| Body Initialization | 固定样本的主体初始化 |
| Body Update | 固定输入下的主体更新 |
| Stalk Growth | G01 接受结果的几何重放 |
| G03 | 复现原始投影门控失败 |
| A→B | 固定源面和目标相机的重投影 |
| Depth-supervised PyTorch | 固定输入的前向、损失和梯度计算 |

不要求重新运行所有大型历史实验。

但必须证明关键模块能够从集中后的新路径独立执行。

## 10.3 第三层：结果一致性

每个重放都与历史冻结结果比较。

对完全确定性的结果：

优先检查 SHA256。

对浮点数、GPU 推理和不同运行环境：

使用原实验已经冻结的数值容差。

至少比较：

- Camera Pose；
- HERO Depth；
- Body 顶点；
- Mesh 顶点和面；
- Projection IoU；
- Boundary MAE；
- A→B 有效像素和深度；
- Loss；
- Gradient。

不得在看到新结果后再临时放宽容差。

如果结果不同：

1. 找到不同来源；
2. 判断是环境、代码还是输入变化；
3. 检查坐标系和单位；
4. 记录最大绝对误差及相对误差；
5. 不允许覆盖历史结果。

无法取得真实输入或权重时，标记：

`NOT_EVALUABLE_EXTERNAL_DEPENDENCY`

不得用模拟数据冒充真实重放。

## 10.4 第四层：主线最小端到端运行

尽可能在新目录下执行一次：

Ring-First 冻结相机  
→ HERO 固定样本  
→ Body Initialization  
→ Body Update  
→ Stalk Growth  
→ 最终 Mesh  
→ 投影评价。

优先使用 G01 作为可运行样本。

G03 用于验证失败门控和异常状态保留。

这一步不允许重新研究或调参。

目标只是证明集中后的主线仍然能够得到与历史相同的结果。

---

# 十一、阶段7：最后清理原始重复目录

只有在以下条件全部满足后，才进入最终清理：

1. 主线源码已经集中；
2. 文件 SHA 已验证；
3. 依赖关系已经闭合；
4. 工程测试通过；
5. 关键模块重放通过；
6. 结果一致性通过或明确记录不可评价原因；
7. 所有重要可视化均可打开；
8. 当前 G01/G03 结果均可追溯。

之后清理：

- 已复制且验证一致的重复源码；
- 旧工作区中的重复运行目录；
- 已被规范主线替代的代码副本；
- 已废弃路线的大型剩余中间产物；
- 不再使用的独立实验输出目录。

但必须保留：

- 原实验的 TECHNICAL_REPORT；
- RESULT_CARD；
- FAILURE_REGISTRY；
- 重要源码的 commit 引用；
- 关键可视化；
- 唯一输入和唯一输出的 SHA；
- 能够解释历史技术决策的资料。

不允许为了让目录整齐而删除整个历史实验记录。

如果旧目录包含尚未纳入清单的唯一科研资产，保留并报告，不要冒险清理。

Git 历史和远程分支本轮不删除、不重写。

本地 worktree 仅在确认干净、无唯一资产且其内容已经完成迁移后，才允许移除。

---

# 十二、阶段8：更新项目文档和主线入口

必须更新：

- `README.md`
- `docs/PROJECT_HOME.md`
- `docs/architecture/SYSTEM_OVERVIEW.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/registry/DEPENDENCY_GRAPH.mmd`
- `docs/registry/TECHNICAL_ROUTE_MATRIX.md`
- `docs/registry/REUSABLE_MODULES.md`
- `docs/registry/EXPERIMENT_INDEX.csv`
- `docs/registry/ASSET_MANAGEMENT_POLICY.md`

新增：

`mainline/README.md`

要求任何新加入的智能体只阅读：

1. 根目录 README；
2. PROJECT_HOME；
3. mainline README；
4. PIPELINE；
5. MAINLINE_ASSET_MAP；

就能够理解当前项目。

主线文档必须明确：

### 当前活动主线

主体初始化 → 多视角主体更新 → 嵌入式柄部生长 → 几何与投影验收。

### 下一阶段研究方向

- HERO 原生深度误差引入；
- G03 视频005视角配准诊断；
- 根部截面完全嵌入；
- 主体和柄部联合更新；
- 进一步的三维精度验证。

### 历史参考技术

- Ring-First；
- MVSAnywhere；
- A→B 重投影；
- 深度监督 PyTorch；
- PyTorch3D；
- 跨视频 BA。

明确区分：

`ACTIVE_MAINLINE`

`REUSABLE_REFERENCE`

`HISTORICAL_EVIDENCE`

`DEPRECATED_EXPLORATION`

不要将所有历史路线都写成当前仍在使用的技术。

---

# 十三、最终交付文件

本任务目录：

`maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/`

必须包含：

```text
TASK.md

INITIAL_STORAGE_REPORT.md

ASSET_INVENTORY.csv
ASSET_INVENTORY.json

DUPLICATE_ASSET_REPORT.json
DEPENDENCY_REFERENCE_GRAPH.json

PHASE1_DELETE_MANIFEST.json
PHASE1_CLEANUP_REPORT.md

MAINLINE_ASSET_MAP.json
MAINLINE_DEPENDENCIES.json

COPY_VERIFICATION.json

REPRODUCIBILITY_TESTS/
    RING_FIRST.json
    HERO.json
    BODY_INITIALIZATION.json
    BODY_UPDATE.json
    STALK_GROWTH_G01.json
    STALK_GROWTH_G03.json
    A_TO_B.json
    DEPTH_SUPERVISED_PYTORCH.json

RESULT_EQUIVALENCE_REPORT.md

FINAL_STORAGE_REPORT.md

CLEANUP_RECEIPTS.json

FAILURE_REGISTRY.json

TECHNICAL_REPORT.md
```

最终 `TECHNICAL_REPORT.md` 必须回答：

1. 整理前总占用多少？
2. 第一阶段实际释放多少？
3. 删除了哪些大型中间产物？
4. 哪些废弃探索路线已清理？
5. 哪些历史技术被保留？
6. 当前主线集中到了哪里？
7. Ring-First 是否能正常运行？
8. MVS/HERO 是否能正常运行？
9. 主体拟合和更新是否能正常运行？
10. G01 柄部是否能够重放？
11. G03 失败门控是否能够重放？
12. A→B 可视化是否能够运行？
13. PyTorch 深度监督更新是否能够运行？
14. 哪些结果与历史一致？
15. 哪些资产仍然依赖外部路径？
16. 还有哪些问题阻碍真正的跨机器复现？

---

# 十四、最终验收标准

本轮需要同时满足四个目标。

### A. 存储收敛

- 重复的大型中间产物已清理；
- 明确废弃路线的无用输出已删除；
- 原始数据和重要失败证据未丢失；
- 实际释放空间有准确统计。

### B. 技术集中

- Ring-First、MVS/HERO、主体拟合、主体更新、柄部生长形成明确的技术目录；
- 重要辅助模块得到保留；
- 代码来源和依赖可追溯；
- 不存在大量无意义的重复副本。

### C. 工程可运行

- 核心测试通过；
- 核心模块可以从新入口执行；
- G01 结果可重放；
- G03 失败状态可重放；
- A→B 和 PyTorch 深度监督工具仍然可用。

### D. 科研状态准确

- 没有改变历史实验结果；
- 没有删除重要负面证据；
- 没有将工程测试通过等同于科学验收；
- 没有修改 DXY；
- 没有擅自改变当前柄部生长研究方向。

---

# 十五、执行原则

请严格按照：

**只读盘点 → 清理大型可删除中间产物 → 集中复制核心资产 → 独立运行 → 结果一致性验证 → 清理原有重复副本 → 更新文档 → 最终验收。**

本轮不要开展新的算法实验。

不要为了集中资产而重写已经验证的算法。

不要为了通过测试而修改历史参数。

不要因为某个历史实验失败，就把其所有源码和证据全部删除。

不要为了节省空间而删除原始数据和模型权重。

**最终目标是让当前息肉重建主线拥有一套干净、精简、可追溯、可运行的技术资产，而不是留下一个只有 README、却无法真正运行的空壳仓库。**