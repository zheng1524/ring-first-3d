# TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002
# 科研主线恢复、全局资产审计与项目收敛方案

## 一、角色与任务定位

你是 Ring-First Polyp 3D Reconstruction 项目的科研基础设施负责人。

本轮由人工研究者授权，执行一次全面的：

1. 科研证据恢复；
2. 实验注册表修复；
3. Git Clone / Worktree 审计；
4. 本地科研资产审计；
5. 运行环境依赖审计；
6. 历史实验资产价值分类；
7. 后续项目收敛方案设计。

本轮不是简单的磁盘清理。

我们已经完成：

`TASK-MAINLINE-ASSET-CONSOLIDATION-001`

建立了规范主线，完成了247项回归测试和8项核心模块重放，但旧工作树仍然没有退役。

现在的核心问题是：

**我们需要弄清楚整个科研项目究竟有多少份代码、多少份独立科研资产、多少个 Git 对象库、多少套运行环境，以及它们之间究竟是什么关系。**

最终形成一份可供人工和另一个独立智能体审查的完整审计报告。

---

# 二、审计范围：本轮正式授权范围

必须审计以下三个区域。

## A. 主线相关 Clone 与 Worktree

首先检查：

`/home/liu/ring_first_3d`

`/home/liu/ring_first_3d_harness`

`/home/liu/ring_first_3d_*`

以及：

`/home/liu/ring_first_3d_mainline`

注意：

以上路径可能存在包含关系，也可能是独立 Git Clone。

必须通过实际 Git 元数据确认，不能根据目录名称推断。

对 `/home/liu` 下所有匹配 `ring_first_3d_*` 的目录进行发现和登记。

还要检查未被通配符覆盖的旧目录：

`/home/liu/ring_first_3d`

## B. 旧科研仓库

审计：

`/home/liu/polyp_research`

重点检查：

- `ring-first-3d`
- `ring_anchor_3d`
- 相关历史实验目录
- 原始源码和历史报告
- 独有模型权重
- ZIP 归档
- 独立虚拟环境
- 尚未迁移的科研资产

特别检查：

`smart_endoscope_20260805.zip`

此前审计发现该归档内包含2865张 JPG，但在解压目录中没有找到对应的完整集合。

本轮只检查归档目录、文件清单、大小和哈希，不要擅自解压或删除。

`/home/liu/polyp_research` 在本轮中允许全面只读审计，但不允许修改其内容。

## C. 其他相关资产

如果上述目录中的配置、脚本或 manifest 引用了其他位置的文件，可以继续追踪其依赖。

但必须区分：

- 项目内部资产；
- 外部科研依赖；
- 原始观测数据；
- 共享模型权重；
- 其他独立研究项目。

`/home/liu/new-polyp-dxy` 继续严格只读，DXY 算法和数据不得迁移、修改或覆盖。

---

# 三、本轮最高优先级：科研证据恢复

先处理已经明确发现的问题。

## 3.1 修复实验索引

检查：

`docs/registry/EXPERIMENT_INDEX.csv`

重点核查是否完整登记：

- TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001
- TASK-E4-G01-MULTISURFACE-BODY-FUSION-001
- TASK-E4-STRUCTURED-BODY-UPDATE-002
- TASK-E4-G01-G03-GROWTH-RECOVERY-001
- TASK-MAINLINE-ASSET-CONSOLIDATION-001

对每个任务，核查：

- 实际来源分支；
- 实际执行 commit；
- 报告所在路径；
- 原始技术路线；
- 工程状态；
- 科研状态；
- 重要失败证据；
- 可复用模块；
- 代表性可视化。

不能只根据文件名补充记录。

必须找到实际报告和代码证据。

如果某个任务的来源 commit 不明确，标记：

`SOURCE_COMMIT_UNVERIFIED`

不得使用当前分支 HEAD 冒充原始执行 commit。

## 3.2 修复模块注册表

检查：

`docs/registry/MODULE_REGISTRY.json`

此前发现注册表包含69个模块，后续 Structured Body 和 Growth Recovery 系列没有得到完整登记。

请从实际源码和实验报告出发，建立完整模块关系。

特别关注：

- EXACT013 Init-A；
- Graph / Smooth ARAP；
- 多视角主体更新；
- 主体与二维轮廓对应；
- B-spline 柄部生长；
- RMF；
- Boolean Union；
- Ring Collision Gate；
- 多视角投影验收；
- G01/G03 的保护和拒绝机制。

每个模块必须记录：

1. 模块 ID；
2. 功能；
3. 源码路径；
4. 来源任务；
5. 来源 commit；
6. 具体函数或入口；
7. 输入输出；
8. 依赖；
9. 实际运行证据；
10. 工程状态；
11. 科研状态；
12. 是否属于当前主线。

不要为了增加模块数量而拆分没有独立功能的代码。

## 3.3 修复历史报告证据链接

此前发现8份 lineage 报告存在相对链接断裂。

必须逐份检查。

检查：

- Markdown 内部链接；
- 图片引用；
- HTML 引用；
- JSON 中的文件路径；
- 报告中的代码路径；
- 结果卡中的可视化路径。

对每个链接分类：

`VALID`

`BROKEN_TARGET`

`MISSING_ASSET`

`MOVED_TARGET`

`EXTERNAL_DEPENDENCY`

`UNRESOLVED`

特别注意：

历史报告必须保持原始版本不变。

不能直接修改原始历史报告来掩盖断链。

优先采用：

- 新建规范证据映射；
- 建立 canonical report；
- 添加迁移说明；
- 保留原始 commit 和 SHA256。

如果原图确实存在于其他工作树，可以记录其真实位置和哈希，暂不复制大型图片。

## 3.4 建立统一科研证据协议

每个重要实验应建立：

`EVIDENCE.json`

建议字段：

```json
{
  "task_id": "",
  "source_commit": "",
  "execution_commit": "",
  "source_files": [],
  "input_assets": [],
  "output_assets": [],
  "metrics": [],
  "visualizations": [],
  "failure_evidence": [],
  "dependencies": [],
  "scientific_status": "",
  "engineering_status": ""
}
```

所有文件必须能够追溯到实际路径和哈希。

---

# 四、第二优先级：全局 Git Clone / Worktree 法证审计

这是本轮最重要的系统调查。

不能只统计目录数量。

必须弄清楚这些目录之间的真实 Git 关系。

## 4.1 Clone 关系

对每个 Git 仓库检查：

- 仓库根目录；
- `.git` 是目录还是文件；
- `git-common-dir`；
- Git object directory；
- alternates；
- remote；
- fetch/push URL；
- branch；
- HEAD；
- 是否为独立 Clone；
- 是否为 Worktree；
- 是否存在共享对象库。

特别要确认：

A、B、C 三套历史 Clone 是否真正独立。

不能仅根据它们的 GitHub remote 相同就认定可以合并。

## 4.2 Worktree 清单

执行完整的：

`git worktree list --porcelain`

并结合文件系统实际目录核验。

每个 Worktree 记录：

| 字段 | 内容 |
|---|---|
| worktree_id | 唯一编号 |
| path | 实际路径 |
| clone_owner | 所属 Clone |
| branch | 分支 |
| HEAD | 完整 commit SHA |
| upstream | 上游分支 |
| ahead/behind | 提交差异 |
| detached | 是否游离 HEAD |
| dirty | 是否有未提交修改 |
| untracked | 未跟踪文件 |
| ignored | 被忽略的重要资产 |
| unique_commits | 独有提交 |
| unique_assets | 独有科研资产 |
| last_activity | 最后活动时间 |
| research_role | 科研用途 |
| retirement_candidate | 是否可能退役 |

尤其检查：

- 未推送的分支；
- detached HEAD；
- 未提交源码；
- 未跟踪预测结果；
- 被 `.gitignore` 忽略的大型资产；
- 只存在于单一 Worktree 的实验结果。

不得把未提交的科研修改当作普通垃圾。

## 4.3 Git 对象库关系

必须回答：

1. 三套 Clone 是否分别保存完整对象库？
2. Worktree 是否共享同一对象库？
3. 是否存在重复 pack？
4. 是否存在独有 commit？
5. 是否存在尚未推送的 commit？
6. 是否有对象只被 reflog 或 dangling reference 引用？
7. 是否存在 Git LFS 对象？
8. 是否有 submodule？
9. 是否有 alternates 指向外部对象库？

统计：

- `.git` 目录实际占用；
- objects 占用；
- pack 文件占用；
- refs；
- reflog；
- LFS 占用；
- 每个 Clone 的独有对象占用。

不要将共享对象重复计入磁盘节省量。

**本轮禁止执行 git gc、git prune、repack、filter-repo 或历史重写。**

可以只读检查 dangling objects，但不得删除。

---

# 五、第三优先级：完整科研资产审计

## 5.1 建立文件资产清单

覆盖所有已确认的项目目录。

统计：

- 文件数量；
- 文件类型；
- 逻辑大小；
- 实际磁盘占用；
- 唯一 inode 占用；
- 硬链接数量；
- 符号链接；
- 文件时间；
- SHA256；
- 所属实验；
- 所属工作树。

重点检查：

| 类型 | 重点 |
|---|---|
| Python | 重复代码与唯一算法 |
| JSON/NPZ | 预测、指标、训练轨迹 |
| PLY/OBJ/GLB | 三维几何结果 |
| PNG/JPG | 重要可视化与原始观测 |
| MP4 | 原始视频 |
| PT/PTH/CKPT | 模型权重 |
| MD/TXT | 科研报告与实验记录 |
| YAML/JSON | 配置与参数 |
| ZIP/TAR | 历史归档 |
| SQLite/CSV | 数据库和评价结果 |

对于大型文件采用流式哈希，不要创建临时复制件。

所有哈希必须标记：

`HASH_RECOMPUTED`

或：

`HASH_INHERITED`

不得混淆。

## 5.2 重复资产识别

区分四种情况：

A. SHA256 完全一致。

B. 内容一致但文件名不同。

C. 内容相似但存在不同版本。

D. 相同实验的不同运行结果。

只有 A、B 可以作为严格重复候选。

C、D 必须保留科研版本关系。

特别注意：

两个 Mesh 即使几何非常接近，也不能直接视为重复。

两张图片即使视觉相同，也需要检查分辨率、压缩和来源。

## 5.3 科研资产价值分类

每个重要资产分为：

`ACTIVE_MAINLINE`

`REUSABLE_REFERENCE`

`HISTORICAL_EVIDENCE`

`UNIQUE_RAW_DATA`

`UNIQUE_MODEL_WEIGHT`

`FAILED_BUT_INFORMATIVE`

`DUPLICATE_CANDIDATE`

`REGENERABLE_CACHE`

`UNKNOWN`

UNKNOWN 必须保留。

不要为了达到某个磁盘释放目标而强行分类。

---

# 六、第四优先级：运行环境与依赖审计

重点检查：

- Python 环境；
- PyTorch；
- CUDA；
- PyTorch3D；
- Open3D；
- FCL；
- Blender；
- MVSAnywhere / HERO；
- nvdiffrast；
- Ring-First；
- 外部模型权重。

特别检查此前使用的：

`/home/liu/polyp_research/ring_anchor_3d/.venv`

以及其他 Worktree 内的虚拟环境。

建立：

`RUNTIME_ENVIRONMENT_MATRIX.csv`

记录：

- 环境路径；
- Python 版本；
- PyTorch 版本；
- CUDA 版本；
- 关键包版本；
- ABI；
- 环境大小；
- 当前引用者；
- 是否唯一；
- 是否可以重建；
- 是否存在隐藏绝对路径依赖。

检查所有运行脚本中的：

- 硬编码路径；
- sys.path；
- 相对路径假设；
- 动态 import；
- 权重路径；
- 数据路径。

本轮不删除任何环境。

---

# 七、第五优先级：统一评价体系审计

必须专门调查当前项目中不同评价口径冲突的问题。

特别是 G01：

- 独立 SE(3) 对齐 GT 后 MAE：0.334906 → 0.303623 mm。
- 固定 INITIAL→GT 框架下 MAE：0.335972 → 0.356988 mm。

这两组数据不能简单合并。

需要检查其原始指标文件和计算脚本，明确：

- 对齐框架；
- 评价对象；
- 评价分母；
- 点云采样；
- 单位；
- GT 使用方式；
- 是否存在重新配准。

同时检查：

- FIT IoU；
- HOLDOUT IoU；
- Chamfer；
- Hausdorff；
- HERO 深度误差；
- Ring 碰撞；
- 表面覆盖率；
- 柄部长度；
- 根部截面外露；
- 多视频评价。

交付：

`METRIC_DEFINITION_AUDIT.md`

`METRIC_DEFINITION_MATRIX.csv`

提出统一的未来 Metric Protocol。

但不要擅自决定哪种历史指标才是正确的，也不要重新计算历史结果。

---

# 八、第六优先级：建立未来项目收敛方案

在完成上述调查之后，设计新的项目组织结构。

建议目标：

```text
ring_first_3d_mainline/
│
├── src/
│   └── ring_first_3d/
│
├── mainline/
│   ├── configs/
│   ├── manifests/
│   ├── scripts/
│   ├── results/
│   ├── references/
│   └── visualization/
│
├── experiments/
│   └── TASK-ID/
│       ├── TASK.yaml
│       ├── TECHNICAL_REPORT.md
│       ├── RESULT_CARD.md
│       ├── EVIDENCE.json
│       ├── metrics/
│       └── figures/
│
├── archive/
│
├── .runtime/
│
└── runs/
```

这是建议目标，不是要求立即创建和迁移。

必须提出：

1. 唯一规范 Clone 应该是哪一个？
2. 哪个 Worktree 应成为唯一活动工作树？
3. 哪些历史 Worktree 可以退役？
4. 哪些应冷归档？
5. 哪些资产应该继续留在 LOCAL_ONLY？
6. 哪些值得考虑外部存储？
7. 如何保留 Git 历史和科研证据？
8. 如何让 Codex 自动创建和结项实验？
9. 如何避免再次形成大量重复源码？

对每个拟议退役对象给出明确理由和恢复方案。

---

# 九、独立审计：必须准备第二智能体审查包

本轮不能由同一个 Codex 自己宣布审计通过。

必须生成：

`INDEPENDENT_REVIEW_PACKAGE/`

包括：

1. 审计范围和方法；
2. Clone/Worktree 清单；
3. Git 对象关系图；
4. 重复资产报告；
5. 唯一科研资产清单；
6. 实验索引问题；
7. 模块注册表问题；
8. 报告断链清单；
9. 指标口径冲突；
10. 运行环境依赖；
11. 拟议退役计划；
12. 未解决问题。

另生成：

`INDEPENDENT_REVIEW_TASK.md`

供另一个智能体独立审计。

第二智能体的任务：

- 不接受第一个智能体的结论作为事实；
- 独立核验 Git Clone 和 Worktree；
- 独立检查唯一资产；
- 检查 SHA256 和重复判断；
- 重点挑战删除候选；
- 检查是否遗漏未提交修改；
- 检查指标体系判断；
- 对每项退役建议给出 ACCEPT / REJECT / NEEDS_MORE_EVIDENCE。

两个智能体的结论不一致时，必须保留争议，不允许自动合并。

---

# 十、本轮绝对禁止事项

本轮是恢复和审计，不是删除执行。

禁止：

- rm / rm -rf；
- git worktree remove；
- git branch -D；
- git clean；
- git reset --hard；
- git gc；
- git prune；
- git filter-repo；
- force push；
- 删除 Git LFS 对象；
- 移动原始科研资产；
- 覆盖模型权重；
- 覆盖实验结果；
- 清理虚拟环境；
- 执行新的 GPU 训练；
- 修改 DXY；
- 修改当前科研算法。

不得通过脚本批量删除所谓重复文件。

不得为了获得整洁目录而修改历史实验目录结构。

所有源目录必须保持原状。

---

# 十一、交付文件

在独