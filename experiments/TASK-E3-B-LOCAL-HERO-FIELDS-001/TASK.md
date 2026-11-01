
# TASK-E3-B-LOCAL-HERO-FIELDS-001

## 一、任务目标

继续当前 Codex 会话，直接继承 E3-A 的审计结果与 RA Phase E3 v1.2 设计。

**本轮目标：利用同一视频内多个合格 HERO 参考的原始深度和曲面，分别构建具有明确有效域的局部隐式场。**

我们已经完成来源、相机和视角审计，不再重复开展大规模历史审计。

本轮必须运行真实数据实验，而不是只编写数学合同。

---

## 二、最高优先级：严格区分 HERO 与历史融合结果

这是研究者本轮特别强调的要求。

### 2.1 HERO 原始几何——正式输入

允许使用：

- 各参考原生 HERO 深度；
- 直接由该深度反投影得到的原始 XYZ；
- 直接由该深度生成的原始开放 Mesh；
- 原始三角面索引与像素对应；
- 对应 RGB、Polyp Mask、Ring Mask；
- 冻结 Ring-First K/c2w；
- Ring CAD；
- HERO 来源和上游图像身份。

**必须严格追溯每个局部场到真实 HERO 深度及其原始三角面。**

特别注意：

Boundary Growth 过程中曾新增 HERO 参考。

如果这些参考确实具有独立的 HERO 深度输出及其直接生成的原始 Mesh，并且通过 E3-A 相机资格检查，可以使用。

但只能使用这些参考的**原始 HERO 几何**。

### 2.2 历史融合结果——禁止作为重建输入

以下结果不得用来构建局部隐式场：

- F1 多来源直接叠加结果；
- F2 来源选择性融合结果；
- F3 Boundary Growth 最终融合 Mesh；
- 历史局部 SE(3) 调整后的融合曲面；
- 历史跨视频融合结果；
- MonoSDF E2.7 预测表面；
- 任何已经通过其他融合算法修改过的最终 Mesh。

Raw/Cleaned 可以保留历史身份。

**本轮以 Raw HERO 为基准，Cleaned 只作为历史清理标签和辅助诊断，不得静默替代原始 HERO 几何。**

如果某个文件来源不明，不能因为文件名中包含 `HERO` 就认定它是合法输入。

必须核对其上游数据与生成过程。

### 2.3 强制防混淆检查

建立输入白名单：

`HERO_NATIVE_INPUT_MANIFEST.json`

每个来源记录：

- source_id；
- 原生 HERO depth；
- 原始 Raw XYZ；
- 原始 Raw Mesh；
- 来源参考帧；
- HERO 上游 RGB；
- K/c2w；
- 原始 Mesh 是否经过融合或几何修改。

对于来自 F1/F2/F3 的最终几何，必须明确标记：

`FUSION_OUTPUT_NOT_ALLOWED_AS_INPUT`

如果发现代码错误地加载了历史融合 Mesh，应立即停止该来源的局部场构建，修正输入路径后再继续。

---

## 三、直接复用已经建立的多视角选择方案

不要重新研究参考视角选择。

直接复用 E3-A：

`E3_SOURCE_SELECTION_PROPOSAL.md`

以及：

`geometry_audit.py::organize()`

现有原则：

1. 首先保证相机资格。
2. 继承 CORE/BRIDGE/RESERVED 分类。
3. 综合相机方向覆盖、实际 HERO 表面法向覆盖和空间覆盖。
4. 保证代表来源之间具有共视连通性。
5. 不因来源共享上游 RGB，就认为其没有独有几何。

### 正式实验来源

| 视频 | 本轮合格 HERO 来源 |
|---|---:|
| G01_004 | 3 |
| G01_005 | 8 |
| G06_004 | 4 |
| G08_005 | 2 |

共17份参考相机筛查通过的 HERO 来源。

注意：这些来源仍保留 E3-A 的条件性相机资格，不得宣称全部具有独立公制精度认证。

G07_004 保留不合格压力测试身份，不计正式成功率。

G01_004 与 G01_005 独立构建局部场，不进行跨视频融合。

### 执行顺序

先使用 CORE/BRIDGE 代表集合验证计算流程。

通过后，对全部17份合格 HERO 原始来源建立局部场。

**RESERVED 来源不能永久排除，其独有几何必须得到保留。**

代表集只用于控制初期计算成本，不是最终允许重建的全部范围。

---

## 四、构建两种局部隐式场

### B0：Projective Local Field

输入：

- 原生 HERO 深度；
- 冻结相机；
- 原始 Mask；
- Ring CAD。

定义：

\[
\phi_i^P(X)=D_i(\pi_i(X))-Z_i(X)
\]

这是投影深度差，不直接宣称欧氏 SDF。

必须明确区分：

- 合法表面窄带；
- 有条件支持的自由空间；
- Ring CAD 遮挡；
- 无效深度；
- Unknown。

不能将原始 HERO 深度缺失区域自动插值为曲面。

### B1：Mesh Local Distance Field

输入各来源的**原始 HERO 开放 Mesh**。

首先构建：

\[
\phi_i^U(X)=d(X,M_i)
\]

即原始 Mesh 的无符号距离。

在法向、最近面、开放边界关系可靠的区域，进一步构造局部有向距离。

必须：

- 保留原始三角面身份；
- 保留每个局部场的来源；
- 正确处理开放边界；
- 不自动封闭 Mesh；
- 不因为距离接近就合并不同物理表面；
- 不将错误延伸自动删除；
- 不因为缺乏第二来源就删除可能真实的细柄。

对于法向不可靠、最近面竞争或缺乏合法符号的位置，返回 `UNKNOWN_SIGN` 或 UDF。

---

## 五、必须保留每个局部场的定义域

每个局部场至少应包含：

\[
\mathcal F_i=
(\phi_i,\Omega_i,w_i,\mathcal P_i)
\]

其中：

- \(\phi_i\)：局部隐式几何；
- \(\Omega_i\)：合法定义域；
- \(w_i\)：可靠性代理；
- \(\mathcal P_i\)：来源身份。

统一查询接口：

```python
LocalField.query(X_mm) -> {
    "value": ...,
    "field_kind": ...,
    "valid_surface": ...,
    "valid_free": ...,
    "cad_occluded": ...,
    "unknown": ...,
    "sign_status": ...,
    "source_id": ...,
    "original_face_id": ...,
    "reliability_factors": ...,
    "reason_codes": ...
}
```

不得以零值代替未知值。

不得要求每个局部开放曲面独立定义整个物体内部。

**全局 SDF 才需要处理整个 ROI；局部场只在真实证据允许的范围内提供几何信息。**

---

## 六、重点检验多角度 HERO 的真实互补性

本轮不要将大量时间继续花在寻找旧融合失败案例上。

直接对真实多视角 HERO 进行以下实验。

### 实验1：单来源局部几何保持

验证每份原始 HERO Mesh 转换后：

- 原有连续曲面是否保留；
- 原始三角面附近距离是否接近零；
- 开放边界是否被正确保留；
- 原始来源身份是否完整；
- 是否存在错误符号或无根据的外推。

### 实验2：多个观察方向的局部场覆盖

使用 E3-A 的代表视角方案。

逐步加入：

`CORE → BRIDGE → RESERVED`

统计：

- 新增表面方向；
- 新增空间覆盖；
- 原始 Mesh 的独有区域；
- 多来源重叠区域；
- 没有任何来源提供几何证据的区域。

新增覆盖必须具有真实来源，不能通过隐式插值制造。

### 实验3：异常结构与独有真实结构

直接检查原生 HERO 中的：

- 破碎片状结构；
- 不合理延伸；
- 多层深度；
- 真实可能的细柄；
- 只有某个视角能够观察到的侧面。

要求局部场能够**表达并标记这些结构**。

本轮不负责删除或融合它们。

特别注意：

单来源独有曲面不等于错误曲面。

### 实验4：局部场的完整定义域检查

在冻结的 Global ROI 中查询。

明确统计：

- Surface；
- Free-space；
- CAD-occluded；
- Unknown；
- Ambiguous。

不能因为局部场没有定义，就判定该区域不存在息肉。

---

## 七、本轮不做什么

明确禁止：

1. 不运行新的 HERO 推理。
2. 不使用 F1/F2/F3 结果生成局部 SDF。
3. 不开展历史融合流程重建。
4. 不进行新的几何清理或删除原始曲面。
5. 不重新研究视角选择算法。
6. 不训练 MonoSDF。
7. 不开展新的 GPU 模型训练。
8. 不拟合全局 SDF。
9. 不进行跨视频强制配准。
10. 不修改 Ring-First、CAD、HERO、P0、Dxy。

历史融合结果可以作为独立评价对照，但不得进入本轮局部场构建的数据通路。

---

## 八、可视化要求

本轮提交四张核心复合图。

**Figure 1：多角度原始 HERO 几何**

展示：

- 多个真实参考帧；
- 每个参考的原始 HERO Mesh；
- 多参考相机位置；
- 固定 Ring CAD。

要求使用统一毫米坐标系，展示各个参考真正恢复的曲面。

**Figure 2：局部隐式场**

同一来源展示：

- 原始 HERO Mesh；
- B0 Projective Field；
- B1 Mesh Field；
- 合法定义域。

**Figure 3：多视角互补性**

展示 CORE/BRIDGE/RESERVED 逐步加入时：

- 已覆盖表面；
- 新增独有表面；
- 重叠区域；
- Unknown。

**Figure 4：真实空间结构**

展示：

- 连续主体；
- 可能的细柄；
- 原始异常延伸；
- 局部断裂；
- 合法遮挡。

Ring 必须使用黑色 CAD 实体。

不允许用历史融合 Mesh、纹理平面或合成曲面替代真实 HERO 几何。

---

## 九、交付与验收

从当前 E3-A 分支继续：

`exp/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`

新建分支：

`exp/TASK-E3-B-LOCAL-HERO-FIELDS-001`

交付：

```text
TECHNICAL_REPORT.md
FAILURE_LEDGER.md
REPRODUCE.md

HERO_NATIVE_INPUT_MANIFEST.json
LOCAL_FIELD_MANIFEST.json
LOCAL_FIELD_QUALIFICATION.csv
SOURCE_COVERAGE_INCREMENT.csv
LOCAL_FIELD_DOMAIN_STATS.csv

code/
    hero_native_adapter.py
    projective_local_field.py
    mesh_local_field.py
    validate_local_fields.py
    visualize.py

figures/
    Fig1_multiview_HERO.png
    Fig2_local_fields.png
    Fig3_multiview_coverage.png
    Fig4_real_geometry.png
```

所有大型输入采用现有文件只读引用。

不重新复制原始视频和模型权重。

### 必须回答

**Q1：是否成功对全部17份合格 HERO 原始来源建立独立局部场？**

**Q2：B0/B1 是否能够保留原始 HERO 表面及其合法定义域？**

**Q3：多角度 HERO 的实际几何互补性如何？**

**Q4：是否完整保留单来源独有的可见曲面？**

**Q5：是否严格保证所有局部场都来自原始 HERO，而不是历史融合结果？**

**Q6：这些局部场是否已经具备进入多来源 V-FUSE 式可见性共识研究的条件？**

若某个来源不满足资格，必须报告原因，不得通过删除它提高成功率。

任务完成后停止，不自行启动全局融合或神经训练。

**最终目标：获得一套覆盖尽可能多真实观察方向、具有完整来源身份和严格有效域的 HERO 局部隐式几何集合，为下一阶段统一全局 SDF 提供直接输入。**

开始执行。