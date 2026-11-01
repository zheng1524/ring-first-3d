# TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001

## 一、任务目标

继续当前 Codex 会话。

研究者已停止 Phase E1–E2.7 的自由 MonoSDF 重建路线，正式启动 Phase E3。

本轮只执行：

**科研资产核验 → 来源与视角整理 → 历史失败模式诊断 → 数学问题定义 → 实验评价协议冻结。**

不要重新初始化项目。

不要再次开发 MonoSDF。

不要提前实现全局 SDF 优化器。

### 研究依据

RA 已提供：

1. `RA_PHASE_E3_LOCAL_TO_GLOBAL_SDF_FUSION_REVIEW_v1.1.md`
2. `RA_PHASE_E3_ALGORITHM_AND_EXPERIMENT_BLUEPRINT_v1.2.md`

如果本地可以找到原文，优先完整阅读，且以 v1.2 的实验组织和 v1.1 的数学约束为依据。

如果原文未在当前工作空间同步，不要假装已经阅读；本任务书包含第一轮所需的核心约束。报告中标记文档可访问状态，不得自行猜测缺失章节。

**本轮不选择 G0、G1 或具体 LocalField 算法。**

本轮要回答的是：

> 我们究竟拥有哪些合法三维观测，它们为什么不能直接融合，怎样建立一个可执行、可证伪的局部到全局隐式融合问题？

---

## 二、科研背景与已知事实

项目：

`zheng1524/ring-first-3d`

目前已经具备：

- Ring-First 公制相机；
- MVSAnywhere HERO；
- 原生深度；
- Raw/Cleaned 点云；
- 原始开放三角面；
- F1/F2/F3；
- Boundary Growth；
- MASt3R 视角分区；
- 来源相关性记录；
- Ring CAD；
- 真实 A→B 重投影；
- Phase E 的 Neural SDF 失败证据。

之前主要存在以下问题：

1. 不同 HERO 参考中的同一物理表面有小幅深度偏差。
2. 多来源叠加形成错层与重复曲面。
3. 每个 HERO 参考自身存在异常延伸、碎片和不合理表面。
4. 清理、选择和融合容易损失已有可见覆盖。
5. 某些真实细柄、侧面与基底过渡缺少足够几何支持。
6. G01 的 video004 和 video005 尚未通过严格的跨视频统一配准。
7. 某些区域即使使用全部合法视角，也可能无法直接观察。

此前自由 MonoSDF 路线在 E2.7 中首次训练就出现严重收缩。

因此，新路线不再允许网络从任意初始化重新预测完整息肉深度。

新研究命题为：

**每个 HERO 来源产生具有合法定义域的局部隐式几何证据；这些证据约束一个具有完整 ROI 定义域的全局隐式函数，同时保留真实观测支持、几何修正与先验推断的区别。**

---

# 三、P0：现有研究资产审计

## 3.1 只审计与新任务直接相关的资产

不要再次开展整个项目历史仓库的全面审计。

优先检查以下实验分支：

### HERO 与历史融合

`exp/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001`

`exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001`

### Boundary Growth

`exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001`

### Neural SDF 失败证据

`exp/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001`

以及现存 E1/E2 来源审计资产。

优先复用已经得到验证的：

- 相机和 CAD 工具；
- `unproject`；
- `depth_mesh`；
- 原始面索引；
- Source DAG；
- CAD raycast；
- MASt3R 历史匹配；
- 真实重投影；
- `visualization/real_p0_renderer.py`。

不得重新实现第二套 HERO 推理、相机模型或点云反投影流程。

## 3.2 建立代码复用表

输出：

`E3_CODE_REUSE_AUDIT.md`

对每项能力记录：

- 实际文件路径；
- 函数名；
- 所属分支；
- Commit SHA；
- 输入输出合同；
- 坐标单位；
- 是否依赖本地未上传资产；
- 是否已经过真实数据验证；
- 当前可否直接复用；
- 如不能复用，需要什么最小适配。

不要只写“可复用”。

必须找到实际代码入口，并检查必要的输入是否存在。

## 3.3 原始来源与派生结果不得混淆

请建立真实来源关系。

例如：

```text
真实 RGB / 相机
        ↓
原生 HERO 深度
        ↓
Raw XYZ / Raw Mesh
        ↓
Cleaned
        ↓
F1 / F2 / F3
        ↓
Boundary Growth
```

其中：

**Raw、Cleaned、F1、F2、F3 不代表五份独立三维证据。**

必须按 HERO 的实际输入图像和父级来源建立 Source DAG。

同一祖先产生的多个派生结果不能重复投票。

如果某份新 HERO 使用了多张图像作为上游输入，需记录全部真实 RGB 身份及其 SHA，而不是只记录参考帧名称。

输出：

`E3_SOURCE_DAG.json`

---

# 四、P1：完整来源、视角与物理组审计

## 4.1 数据范围

至少检查：

| 数据 | 审计要求 |
|---|---|
| G01_004 | 正式主例候选 |
| G01_005 | 困难对照 |
| G06_004 | 跨形态案例 |
| G08_005 | LIMITED 条件案例 |
| G07_004 | UNQUALIFIED 压力案例 |
| G01 三张照片 | 外观、方向与位姿资格审计 |
| 其他 Is/R5 组 | 搜索是否存在合格 HERO 资产 |

G01 的两段视频仍然是一个物理组。

不得将不同视频当作独立病例。

对 G01 三张照片，不得仅凭历史候选位姿就建立正式公制局部场。

如果没有认证的 K/c2w，应保持：

`METRIC_GEOMETRY_NOT_QUALIFIED`

## 4.2 每个 HERO 来源至少记录

```text
physical_group
video_id
source_id
reference_frame
source_RGB_path
source_RGB_SHA256
HERO_input_RGB_IDs
HERO_input_RGB_SHA256s

camera_K
camera_c2w
camera_status
camera_coordinate_frame
camera_provenance

Ring_type
Ring_CAD_path
Ring_CAD_SHA256

Polyp_Mask_path
Ring_Mask_path

native_HERO_depth_path
native_HERO_depth_shape
native_depth_unit
depth_valid_fraction

Raw_XYZ_path
Raw_Mesh_path
original_vertices
original_faces
original_surface_area_mm2

Cleaned_asset_path
Type2_status
source_ancestry

view_direction
view_angle_group
camera_overlap_status

independent_geometry_status
qualification
```

字段可根据真实数据补充，但不能省略源身份和相机资格。

输出：

`E3_SOURCE_AND_VIEW_MANIFEST.csv`

## 4.3 所有来源都必须进入清单

第一轮不要只选择三份参考就忽略其余 HERO。

应首先列出同一视频内全部合法来源。

之后再将其划分为：

- `CORE`：主要几何代表来源；
- `BRIDGE`：用于连接观察方向或几何块；
- `RESERVED`：合法但暂不参与首次优化的补充来源；
- `UNQUALIFIED`：相机或来源条件不足；
- `DUPLICATE_DERIVED`：不能当独立证据的派生资产。

CORE/BRIDGE/RESERVED 只是实验角色，不是质量真值。

不得根据最终融合效果反向决定来源类别。

---

# 五、P2：视角覆盖与来源选择问题定义

这部分需要实际计算，而不是只画相机位置图。

## 5.1 观察方向

在同一个合格的局部坐标系中，计算相机中心相对 Polyp ROI 的观察方向。

\[
d_i=
\frac{c_i-p_c}{\|c_i-p_c\|}
\]

再计算来源间夹角：

\[
\theta_{ij}
=
\arccos(d_i^\top d_j)
\]

同时统计：

- 相机方向差异；
- 相机平移视差；
- 有效 Polyp Mask 共同观察范围；
- 原始 HERO 表面可重叠范围；
- 相机资格；
- 有效连续原面面积；
- 来源相关性。

不能只凭角度大就认定视角更好。

## 5.2 建立两个不同的覆盖概念

**A：观察方向覆盖。**

描述相机从哪些方向看过息肉。

**B：真实几何方向覆盖。**

描述已有 HERO 实际恢复了哪些表面法向和三维区域。

二者不能混淆。

例如：

相机从一个新方向观察，并不意味着 HERO 成功恢复了新侧面。

必须统计：

- 新增相机方向；
- 新增具有来源的连续表面；
- 与已有来源的实际重叠；
- 仍没有几何支持的区域。

## 5.3 选择一个可执行的来源组织方案

本轮只建立来源选择问题，不运行优化算法。

应给出：

- 全来源集合；
- 代表性来源集合；
- 各来源的相关性；
- 观察方向覆盖变化；
- 共视图连通性；
- 新增来源的边际覆盖。

允许使用简单的确定性贪心集合覆盖方法作**来源组织诊断**，但不能根据下游 SDF 重建结果调参。

输出：

`E3_VIEW_COVERAGE.csv`

`E3_SOURCE_SELECTION_PROPOSAL.md`

---

# 六、P3：历史 HERO 几何失败模式重新定义

这是本轮最重要的工作包。

我们不能仅仅写：

“多来源深度不一致，导致不能融合。”

必须尽可能明确地定位不同类型的失败。

## 6.1 需要审计的错误

至少包括：

**E1：参考级系统性深度偏差。**

同一物理表面的多个来源整体偏近或偏远。

**E2：局部几何错层。**

部分区域存在不同的深度模态。

**E3：异常延伸。**

单个 HERO 中出现不合理的长条面或大面积错误侧面。

**E4：离散碎片。**

原始面破碎、孤立、缺少真实连续性。

**E5：重复层。**

多个来源在相同物理区域同时保留不同曲面。

**E6：缺少可见几何。**

真实 RGB/Mask 已观察到，但 HERO 没有产生有效连续表面。

**E7：Ring 遮挡或其他合法遮挡。**

不是错误缺失，不允许据此否定后方物体。

**E8：不可观测区域。**

当前所有合法视角均缺少直接几何证据。

**E9：相机或对应关系不确定。**

当前坐标变换不足以确定是否为同一物理表面。

## 6.2 必须把错误与证据联系起来

针对每个物理组，选择具有代表性的实际位置：

- 主要息肉头部；
- Ring 邻近区域；
- 跨 Ring 两侧的息肉表面；
- 侧面；
- 细柄或基底连接区域；
- 典型异常延伸；
- 典型碎片；
- 原始多层错位区域。

需要记录：

- 来源；
- 原始像素；
- 对应 XYZ；
- 原始三角面身份；
- 相机；
- 法向；
- 跨来源对应资格；
- 深度差；
- 有效自由空间证据；
- CAD 遮挡状态；
- 人工是否确认真实结构。

不能将不同物理表面的距离差直接叫作深度预测误差。

也不能把所有与其他参考不一致的区域自动认定为伪面。

## 6.3 明确区分三种冲突

### A. SAME_SURFACE_DEPTH_CONFLICT

有足够几何和可见性证据表明两份来源观察同一物理表面，但位置不一致。

### B. DISTINCT_SURFACES_OR_OCCLUSION

存在合理遮挡或不同可见层，不应强行合并。

### C. CORRESPONDENCE_UNRESOLVED

来源身份或相机误差使对应关系无法认证。

这三类必须分别统计。

对于 C 类，不能为了减少未知数量而强制分配到 A 类。

输出：

`E3_ERROR_TAXONOMY.csv`

`E3_CONFLICT_CASEBOOK.md`

---

# 七、P4：建立局部隐式场的数学合同

本轮只定义统一接口，不选择具体算法。

RA 的研究目标要求每份 HERO Mesh 对应一个局部隐式几何对象。

建议定义：

\[
\mathcal F_i=
\left(
\phi_i,\Omega_i,w_i,\mathcal P_i
\right)
\]

但需要由实际资产审计明确其中每一项的含义。

## 7.1 必须定义四类局部空间

### Surface domain

\[
\Omega_i^{surf}
\]

与原始有效三角面或深度表面具有明确关联的局部窄带。

### Free-space domain

\[
\Omega_i^{free}
\]

来源相机与合法首表面之间，具有实际可见性支持的自由空间子段。

### Occluded domain

\[
\Omega_i^{occ}
\]

被 Ring CAD 或其他已知几何遮挡的区域。

这里不能自动产生 Polyp 不存在的负证据。

### Unknown domain

\[
\Omega_i^{unknown}
\]

来源没有足够合法信息定义几何或符号的区域。

特别强调：

**Unknown 不等于 SDF 正值，也不等于背景。**

## 7.2 统一查询合同

暂定：

```python
LocalField.query(X) -> {
    "value": ...,
    "field_kind": ...,
    "valid_surface": ...,
    "valid_free": ...,
    "occluded": ...,
    "unknown": ...,
    "source_id": ...,
    "source_family": ...,
    "reliability_proxy": ...,
    "reason": ...
}
```

本轮定义字段及其数学语义即可。

不要实现完整 LocalField 模型。

特别需要区分：

- 欧氏 Signed Distance；
- Projective Truncated Distance；
- 局部有向距离；
- Unsigned Distance；
- 仅有表面位置约束的观测。

不能仅因为都以毫米表示，就直接平均它们的数值。

## 7.3 符号与观察资格测试

请设计必要的测试合同，至少覆盖：

1. 合法原始三角面；
2. 开放曲面边界；
3. Ring 遮挡；
4. 深度断裂；
5. 两个错误重叠层；
6. 两个真实不同表面；
7. 只有一个视角观察到的真实细柄；
8. 完全没有观察证据的空间。

本轮可使用少量实际几何查询核对定义是否自洽。

不开发新的神经隐式场。

输出：

`E3_LOCAL_FIELD_CONTRACT.md`

---

# 八、P5：全局隐式问题的良定义

这是 Phase E3 后续所有算法必须遵守的共同问题。

## 8.1 全局研究 ROI

定义：

\[
\Omega_G\subset\mathbb R^3
\]

要求：

- 单位毫米；
- 覆盖同一视频内全部合格 HERO 可见几何；
- 考虑合理的潜在未观测空间；
- 与 Ring CAD 保持已知几何关系；
- 在算法选择前冻结；
- 不能根据最终网络收缩后的表面重新缩小 ROI。

必须报告：

- ROI 坐标系；
- Ring CAD 原点与法向；
- Polyp 几何包络；
- ROI 的选择依据；
- 不确定边界的安全余量；
- 各来源的坐标变换。

Ring 中心可作为世界坐标原点。

但不允许把 Ring 中心当成息肉 SDF 的零水平集或内部网络唯一归一化中心。

## 8.2 全局函数

未来待求：

\[
\boxed{
\Phi:\Omega_G\rightarrow\mathbb R
}
\]

同时具有：

\[
U(X)
\]

和：

\[
\sigma(X)
\]

分别表示空间证据身份和不确定性代理。

请明确：

- 何谓“整个 ROI 有定义”；
- 何谓“有观测支持的表面”；
- 何谓“修正后的表面”；
- 何谓“先验推断表面”；
- 何谓“Unknown”；
- 何谓“冲突尚未解决”。

此外：

如果 \(\Phi\) 尚不满足真正距离函数的性质，应称为 implicit scalar field。

不能预先宣称已得到欧氏 SDF。

## 8.3 两类缺失

正式区分：

`OBSERVED_BUT_UNRECONSTRUCTED`

真实图像中能够观察，但原始 HERO 没有恢复出有效几何。

`TRULY_UNOBSERVED`

所有已认证视角都无法直接观察。

前者属于几何重建修复问题。

后者属于形态先验与不可辨识性问题。

请提出可执行的分类依据，允许：

`UNKNOWN_OR_INSUFFICIENT_EVIDENCE`

不能在数据不足时强制判断为 Truly-Unobserved。

## 8.4 明确什么时候允许融合

应提出一个初始、与具体算法无关的证据合同：

只有在满足以下条件时，才能将两个局部观测作为同一物理表面的融合候选：

- 位于同一合格坐标系；
- 相机和来源身份可追溯；
- 具有相容的物体身份；
- 可见性关系合法；
- 没有明确的 CAD/遮挡矛盾；
- 对应关系具有足够依据。

如果不能满足，保留：

`UNRESOLVED`

不能强制融合。

## 8.5 全局形态推断的独立身份

未来算法可以对未观测空间建立条件性形态。

但必须区别：

- 数学上的完整函数；
- 已观测的真实表面；
- 已修正的融合表面；
- 由先验生成的候选表面。

所有后续指标必须能够选择性地只统计观测支持区域。

输出：

`E3_GLOBAL_FIELD_PROBLEM_DEFINITION.md`

---

# 九、P6：评价协议冻结

我们现在不急于选算法，但必须先定义什么结果才有价值。

## 9.1 现有历史方法作为共同对照

保留：

- Raw HERO；
- Cleaned HERO；
- Single Primary；
- F1；
- F2；
- F3；
- Boundary Growth。

不能因为旧方法无法完全融合就只保留一个最弱基线。

不同历史方法使用的来源数量和投影协议可能不同。

必须同时整理：

1. **相同来源集合比较**；
2. **各方法原始历史配置比较**。

不能把新增 HERO 参考带来的收益归因于融合算法本身。

## 9.2 第一优先级指标

### 可见覆盖

固定原始真实观察分母。

记录：

- 完整 Polyp Mask 像素数；
- 合格 HERO 深度像素数；
- 已恢复有效原面覆盖；
- 融合后具有可信首次表面交点的像素数；
- 被新方法损坏的原可信区域。

### 连续结构

记录：

- 主要连续面面积；
- 碎片数；
- 开放边界；
- 断裂程度；
- 真实细柄保留；
- 侧面和基底附近的结构状态。

### 错误结构

记录：

- 多层面；
- 错误延伸；
- 明显异常片；
- CAD 穿插；
- 无观测支持却被认证的面。

这些指标需要区分已认证事实与代理判断。

## 9.3 第二优先级指标

记录：

- 多参考相容区域的几何偏差；
- 接缝；
- 修正量；
- 法向变化；
- 真实 A→B 重投影；
- 固定共同像素上的 RGB 残差。

不能以降低 RGB MAE 代替几何成功。

## 9.4 全域资格

未来全局场至少需要能够检查：

- 全域有限值；
- 有效性/身份场；
- 不确定性代理；
- 零水平集；
- 表面定义域；
- SDF 距离性质；
- 重距离化后的零面漂移；
- 未观测区域的推断身份。

但本轮只制定评价合同，不运行全局模型。

## 9.5 独立评价身份

严格审查每个候选评价帧是否已经参与：

- HERO 输入；
- 相机恢复；
- 历史匹配；
- 清理；
- 来源选择；
- 其他训练或调参过程。

如果没有真正独立视角，明确标记：

`FULL_PIPELINE_INDEPENDENCE_NOT_AVAILABLE`

可以保留诊断性真实视角评价，但不得宣称严格泛化准确率。

输出：

`E3_EVALUATION_PROTOCOL.md`

`E3_HYPOTHESIS_PREREGISTRATION.md`

---

# 十、P7：形成后续实验的固定输入

在完成审计和问题定义后，整理一个只读实验数据协议。

至少包括：

```text
physical_group
video
qualified_source_ids
source_families
camera_contract
world_frame
Ring_CAD
native_HERO_depths
original_meshes
raw_Cleaned_labels
evaluation_frames
protected_geometry
source_region_labels
ROI_definition
uncertainty_status
```

每个组都需要说明：

- 现有可直接实验的数据；
- 需要修复的输入问题；
- 暂时不能进入正式实验的数据；
- 已有的真实原始三角面是否完整；
- 最适合观察哪一类失败模式。

输出：

`E3_BENCHMARK_MANIFEST.json`

不复制全量视频和大模型。

优先通过原始资产路径、哈希和只读引用复用。

---

# 十一、可视化要求

本轮必须生成 3–4 张核心复合图。

## Figure 1：完整来源和视角分布

至少包括：

- G01_004；
- G01_005；
- G06；
- G08；
- G07。

使用真实缩略图、相机方向、来源数量和质量标记。

G01 两视频不能假装已经处于同一个已认证世界坐标系。

## Figure 2：原始 HERO 三维几何

展示：

- Raw；
- Cleaned；
- 主要完整原三角面；
- F1/F2；
- 典型 F3。

统一公制尺度。

Ring 使用黑色 CAD 实体。

尽量采用已有真实点云和开放 Mesh，不重新绘制抽象球壳。

## Figure 3：实际失败区域

至少选择：

- 一处多来源错层；
- 一处单来源异常延伸；
- 一处真实薄结构或细柄；
- 一处观察缺失或 Ring 遮挡。

展示真实图像、原始三维几何、来源身份和局部放大。

## Figure 4：观测支持与未知问题

在同一视频的固定空间剖面中，展示：

- 有原始 HERO 曲面支持的区域；
- 已知遮挡；
- 有真实图像但缺少可靠深度的区域；
- 没有足够证据的区域；
- 明确存在冲突的区域。

如果尚不能可靠区分 Truly-Unobserved，明确标记 Unknown，不强行分类。

这一张图是**观测证据示意与定义域审计**，不能冒充新全局 SDF 的输出。

所有图必须有实际物理尺度和清楚的来源标签。

---

# 十二、执行权限与禁止事项

### 本轮允许

- 读取仓库和本地资产；
- 复用现有几何分析代码；
- 执行少量只读数值检查；
- 计算来源覆盖和视角分布；
- 生成指标与图像；
- 编写审计脚本；
- 建立独立实验分支；
- 上传报告、代码、CSV 和精选图。

### 本轮禁止

- 新 HERO 推理；
- MonoSDF 训练；
- 任何 GPU 模型训练；
- 新的全局 SDF 优化；
- 几何形变；
- 修改原始 Mesh；
- 重新估计 Ring-First 相机；
- 强制跨视频融合；
- 使用 GT/Oracle；
- 使用未经认证的照片生成公制点云；
- 修改 Dxy 正式研究；
- 删除历史失败结果；
- 开展大规模超参数搜索。

即使发现一个看起来很容易实现的融合方法，也不能未经 PM 审批直接运行。

---

# 十三、输出结构

建立独立分支：

`exp/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`

建议目录：

```text
experiments/
└── TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001/
    │
    ├── TASK.md
    ├── TECHNICAL_REPORT.md
    ├── FAILURE_LEDGER.md
    ├── RESULT_INDEX.md
    ├── REPRODUCE.md
    │
    ├── docs/
    │   ├── E3_CODE_REUSE_AUDIT.md
    │   ├── E3_SOURCE_SELECTION_PROPOSAL.md
    │   ├── E3_CONFLICT_CASEBOOK.md
    │   ├── E3_LOCAL_FIELD_CONTRACT.md
    │   ├── E3_GLOBAL_FIELD_PROBLEM_DEFINITION.md
    │   ├── E3_EVALUATION_PROTOCOL.md
    │   └── E3_HYPOTHESIS_PREREGISTRATION.md
    │
    ├── provenance/
    │   ├── E3_SOURCE_DAG.json
    │   ├── E3_BENCHMARK_MANIFEST.json
    │   └── INPUT_HASHES.json
    │
    ├── metrics/
    │   ├── E3_SOURCE_AND_VIEW_MANIFEST.csv
    │   ├── E3_VIEW_COVERAGE.csv
    │   ├── E3_ERROR_TAXONOMY.csv
    │   └── E3_CAMERA_QUALIFICATION.csv
    │
    ├── figures/
    │   ├── Fig1_sources_and_views.png
    │   ├── Fig2_existing_HERO_geometry.png
    │   ├── Fig3_geometry_failure_cases.png
    │   └── Fig4_observation_support_domains.png
    │
    └── code/
        └── minimal_readonly_audit_tools/
```

尽量复用现有函数，不要新建大量重复代码。

---

# 十四、必须回答的十个问题

**Q1.** 目前究竟有多少份合法、可直接复用的 HERO 原始深度和完整原始三角面？

**Q2.** 在 G01_004 和 G01_005 中，各来源真实观察方向如何分布？哪些来源互补，哪些只是重复？

**Q3.** 是否有可用的额外 Is/R5 合格物理组？

**Q4.** 现有无法融合的几何主要有哪些不同错误？哪些确实属于同一物理表面之间的深度偏差？

**Q5.** 单个 HERO 参考自身的异常结构比例和典型空间位置是什么？

**Q6.** 哪些已有有效表面在历史 F1/F2/F3 流程中被丢失或破坏？

**Q7.** 哪些区域已经在图像中观察到，却没有可靠的三维几何？

**Q8.** 对于所有视角仍然无法约束的空间，目前有哪些证据能够支持 Unknown 判断？哪些区域尚无法区分真正不可观测与观测失败？

**Q9.** 局部场和全局隐式场分别应具有哪些合法定义域、符号、来源与可信度状态？

**Q10.** 如果下一轮比较局部 Projective Field、Mesh Narrow-band Field、V-FUSE 式共识和全局 SDF，什么才是公平且可以证伪的实验条件？

所有答案必须注明：

- `VERIFIED`
- `CONDITIONAL`
- `UNKNOWN`
- `NOT_EVALUABLE`

不得为了形成完整报告而猜测缺失数据。

---

# 十五、下一阶段接口，但不提前执行

完成本轮后，向 PM 提供三份下一步建议：

### E3-B：局部场资格实验

比较：

- Projective narrow-band；
- Mesh signed/unsigned narrow-band；
- 其他必要局部表示。

不预选赢家。

### E3-C：V-FUSE 式可见性共识

比较：

- Support；
- Support + Occlusion；
- Support + Occlusion + Free-space；
- 再加入 Mask/Ring 和来源相关性。

### E3-D：全局隐式场拟合

在同一输入和固定评价协议上，比较：

- 稳健非学习式全域拟合；
- HERO 锚定的局部/神经残差融合；
- 有条件的未知区域推断。

这些是研究候选，并非本轮执行授权。

本轮不准自行选择算法并直接开展 E3-B/C/D。

---

# 十六、最终验收标准

只有满足以下条件，E3-A 才算完成：

1. 所有可用合法 HERO 来源均被清点。
2. 历史 Raw/Cleaned/F1/F2/F3 的来源关系清楚。
3. 相机资格与跨视频限制清楚。
4. 主要视角覆盖和共视关系清楚。
5. 至少四个物理组进入审计。
6. 真实错误结构已有对应案例和指标。
7. 局部场定义域具有可执行的数学语义。
8. 全局 ROI、身份场和不确定性要求明确。
9. 下一轮评价数据与固定分母已预注册。
10. 不存在静默修改或损坏历史科研资产。
11. 已输出四张能够供人工判断的核心图。
12. 尚未运行任何新的融合优化或模型训练。

完成后直接提交 Git 分支、技术报告、结果索引和四张核心图。

**不要再返回一份计划等待批准；这次已经获得 E3-A 审计任务的执行授权。**

**任务完成后停止，等待 PM 审查并确定 E3-B 的算法候选。**