# TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001

## 一、任务定位

继续当前 Codex 会话。

你已经完成：

- E1：MonoSDF 和 MapAnything 错误流程审计；
- E2 C2a：有限 Polyp opacity、Mask 语义、Ring CAD 遮挡；
- E2 C2b：G01 三参考数据流和来源不确定性；
- E2 CPU continuation：RGB、Mask、HERO、Eikonal 联合损失解析梯度，以及 MapAnything 共同几何输入合同。

**不要重新初始化项目，不要重复上述资产审计，不要重新进行大量解析 Sphere 实验。**

本轮由 PM 正式发布两个连续工作包：

**P1：真实多参考 HERO 深度不一致性诊断。**

**P2：官方 MonoSDF 网络的有限射线接线与 CPU 前向、反向验证。**

目标是为正式神经三维重建解决最后几个关键工程问题。

本轮不是重新寻找算法，也不要求发明新的网络结构。

### 执行权限

允许：

- 读取已有 RGB、Mask、HERO、相机和 Ring CAD；
- 运行 CPU 几何诊断；
- 实现必要的薄适配器；
- 实例化真实官方 MonoSDF 网络；
- 在极小 CPU batch 上进行前向、反向和梯度检查；
- 生成指标和可视化；
- 提交独立 GitHub 实验分支。

禁止：

- GPU 运行；
- 优化器更新模型参数；
- 正式神经网络训练；
- MapAnything 正式推理；
- 修改 HERO 原始深度；
- 重新估计 Ring-First 相机；
- 修改 Ring CAD、P0、Dxy；
- 使用 GT 或目标评价帧选择参数；
- 未经批准进行大规模实验。

若 CPU 实际网络检查受环境或资源限制，应报告阻碍，不通过运行 GPU 绕过授权。

---

# 二、研究问题

我们已经确认，同一静止场景的多个 HERO 参考存在明显深度不一致。

但目前尚未弄清这些不一致主要来自什么。

需要区分：

**H1：参考级系统偏移。**

某个 HERO 参考整体偏近或偏远。

**H2：局部形状预测错误。**

整体尺度相近，但局部曲率、边缘、侧面深度存在冲突。

**H3：相机与对应关系误差。**

冻结 Ring-First 相机或跨视角对应存在偏差，使两个实际上不同的表面点被当作对应点。

**H4：真实遮挡与不同观察范围。**

两个参考观察到的区域不同，不能强制进行深度一致性比较。

本轮首先量化这些问题，再判断是否值得加入简单的深度修正方法。

**不得预先假设所有深度冲突都应该通过校正 HERO 来解决。**

---

# 三、工作包 P1：多参考 HERO 深度一致性诊断

## 3.1 数据范围

只使用 G01 的两个视频。

video004：

```text
ref03
ref08
ref13
```

video005：

```text
raw00057
raw00459
raw00745
```

两段视频独立分析。

不得假设二者已经完成准确的跨视频刚体配准。

使用 E2 已经冻结的：

- K；
- c2w；
- 原生 HERO axial Z；
- Polyp Mask；
- Ring Mask；
- 固定 Ring CAD；
- 来源 DAG；
- ROI 和可见性合同。

不得重新估计这些资产。

## 3.2 正确比较两个参考的深度

不得直接计算：

\[
Z_A(u)-Z_B(u)
\]

因为两个相机的像素坐标和轴向深度不同。

必须使用：

\[
X_A= T_A\operatorname{Unproject}(u_A,Z_A)
\]

再投影至 B：

\[
(u_B,Z_{A\rightarrow B})
=
\operatorname{Project}_B(X_A)
\]

随后计算：

\[
\boxed{
e_{A\rightarrow B}
=
Z_{A\rightarrow B}
-
Z_B(u_B)
}
\]

比较之前必须检查：

1. 投影位于 B 有效图像区域；
2. 两侧均为有效 HERO 深度；
3. 对应区域具有相容的物体身份；
4. 不存在已知 Ring CAD 遮挡；
5. 不存在明显的前后表面混淆；
6. 不使用未经认证的背景补面制造对应关系；
7. 保留无法认证的对应，不将其强制纳入深度误差。

对 A→B 和 B→A 分别计算。

应记录方向差异，不允许简单把两个方向的结果当成独立样本。

## 3.3 分析误差的空间分布

对每个有效参考对，计算：

- 有效比较数量；
- 覆盖率；
- 有符号深度残差的中位数；
- MAD；
- 绝对残差中位数；
- P90；
- P95；
- 正负残差比例；
- 局部连续冲突区域面积；
- 不同区域的有效观测数量。

重点区分：

- 息肉主体；
- 息肉边缘；
- 环邻近区域；
- 侧面；
- 其他可靠可见区域。

如果缺少可靠的局部形态标签，可以使用明确的几何或 Mask 分区。

不能根据预测误差反向修改分割结果。

输出：

`HERO_PAIRWISE_DEPTH_CONFLICTS.csv`

## 3.4 检查是否存在系统偏移

研究每个参考的深度残差是否具有稳定方向。

例如：

某个参考相对于其他两个参考，是否持续表现为偏近？

必须注意：

跨视角残差包含相机误差和对应误差。

因此：

**不能直接把跨视角残差中位数当成某张 HERO 深度图的真实偏移量。**

本轮只形成：

`POSSIBLE_REFERENCE_BIAS`

或：

`NO_STABLE_REFERENCE_BIAS`

等诊断结论。

如果需要拟合参考级偏移参数，必须采用有界、预注册的几何模型，并保留原始结果对照。

---

# 四、工作包 P1-B：利用 Ring CAD 诊断深度偏差

这是本轮重点尝试的项目特色设计。

我们的 Ring 几何已知，且已经拥有冻结相机。

对于真实可见的 Ring 像素：

\[
Z_{\mathrm{Ring}}^{CAD}(u)
\]

可以通过固定 CAD 求交获得。

如果 HERO 在相应像素存在合法预测：

\[
Z_{\mathrm{Ring}}^{HERO}(u)
\]

则计算：

\[
\boxed{
e_R(u)
=
Z_{\mathrm{Ring}}^{HERO}(u)
-
Z_{\mathrm{Ring}}^{CAD}(u)
}
\]

要求：

1. 只使用可靠可见的 Ring 区域；
2. 排除 Polyp 遮挡的 Ring；
3. 排除 Mask 物体身份冲突；
4. 排除明显错误的 CAD 投影对应；
5. 同时报告有效像素数量与覆盖；
6. 如果 HERO 在 Ring 区域没有合法深度，明确标记不可评价。

注意：

当前 E2 的合格 Polyp 深度集合，不等于合法 Ring 深度集合。

不得为了完成这项分析，从 Polyp 深度或补插值中构造不存在的 Ring 观测。

对每个参考报告 Ring 残差的：

- Median signed residual；
- Median absolute residual；
- MAD；
- P95 absolute residual；
- Valid Ring pixel count。

分析是否存在稳定参考级偏差。

### 科研判断

如果 Ring 偏差显著，继续检查：

**Ring 偏差能否合理解释 Polyp 区域的部分几何冲突？**

但不得直接用 Ring 偏差替换全部 Polyp 深度。

因为不同材质、表面反光和视角可能导致不同的 HERO 误差。

本轮不直接修改 HERO。

---

# 五、工作包 P1-C：提出最小深度处理方案

根据诊断结果，比较三个候选方案：

### D0：原生 HERO

\[
Z_i'=Z_i
\]

保持所有原始深度不变。

采用现有冲突权重和稳健损失。

**这是正式基线。**

### D1：冲突感知权重

仍保留原始 HERO，但根据预先冻结的来源可靠性调整监督权重。

继续采用 E2 已有方案作为初始版本：

- 非冲突权重 1；
- 冲突权重 0.25；
- 同一来源相关分量按既有规则归一。

不得因为某个结果不好就临时降低其权重。

### D2：有界参考级偏移校正

仅当 P1 发现有证据支持系统性偏差时，提出：

\[
Z_i'=Z_i-b_i
\]

其中 \(b_i\) 是参考级常数。

要求：

- 不允许逐像素自由修正；
- 不允许自由尺度和偏移同时拟合；
- 不允许使用 GT；
- 不允许使用目标评价帧；
- 必须限制参数范围；
- 必须保留未校正深度；
- 必须先验证是否存在实际的可辨识性。

不得仅根据其他不一致的 HERO 参考，就宣称已经求得真实偏移。

### 重要限制

**本轮只进行诊断和候选方案预注册，不直接将 D2 作为正式神经训练输入。**

如果证据不足，应明确建议放弃 D2。

最终输出：

`DEPTH_CORRECTION_DECISION.md`

回答：

1. 当前主要是局部误差还是系统误差？
2. Ring 是否提供了有用的偏差证据？
3. 冻结相机误差是否可能是主要限制？
4. 原生 HERO + 稳健权重是否足够作为首轮方案？
5. 是否值得在后续单独开展 D2 消融？

---

# 六、工作包 P2：真实 MonoSDF 网络接线

P1 完成后，直接开展 P2。

**不要再进行一轮大规模解析 Sphere 验证。**

## 6.1 复用现有工程

重点复用：

```text
code/finite_joint_adapter.py
code/opacity.py
code/multiview.py
```

以及已有：

- Ring CAD 射线交点；
- 五类 Mask 采样；
- 三参考数据 Manifest；
- HERO 可靠性权重；
- RGB/Mask/Depth/Eikonal 联合损失。

不得重新开发已经验证的模块。

## 6.2 实例化官方 MonoSDF

使用此前已审计的官方代码版本。

允许：

- 实际构造网络；
- 在 CPU 上进行极小批量前向；
- 计算四项损失；
- 调用 autograd；
- 检查真实神经参数的梯度。

禁止：

- GPU；
- optimizer.step()；
- 模型权重更新；
- 正式训练；
- 利用评价结果选择最佳模型。

本轮为：

`OFFICIAL_NETWORK_CPU_WIRING_TEST`

不是科学重建。

## 6.3 有限射线采样

正式网络仍必须使用：

\[
[t_a,t_{\mathrm{cap}}]
\]

进行 Polyp 监督。

不得恢复旧整射线吸收机制。

特别注意官方采样器可能：

- 依赖 CUDA；
- 使用旧吸收球；
- 使用被截断的 SDF；
- 生成超出有限 ROI 的采样点。

如果这些情况出现，只允许采用明确的薄适配器，使实际采样点进入合法有限段并重新查询 raw SDF。

不得静默重写 MonoSDF 的完整渲染算法。

如果官方自适应采样器暂时无法合法接入，允许使用固定有限采样方案作为 CPU 接线诊断，但必须明确标记：

`FIXED_SAMPLER_DIAGNOSTIC_ONLY`

不能冒称官方采样器已经通过。

## 6.4 初始化与物理 beta

重点检查：

G01_004 与 G01_005 的实际网络初始化。

E2 已发现：

- 旧解析初始化在 004 有前表面交点；
- 旧解析初始化在 005 没有有效前表面交点；
- 旧 beta 的物理尺度明显大于解析测试值。

因此必须检查：

- raw SDF 是否有合理零水平集；
- 零交叉是否位于 ROI；
- 实际网络是否在有效 Polyp 射线上提供前表面命中；
- beta 是否使用正确物理单位；
- 有效积分是否产生非饱和梯度。

最多保留两个具有明确物理依据的初始化/采样候选。

不得进行大规模参数搜索。

候选应在检查预测表现之前依据场景几何预注册。

## 6.5 三参考联合梯度

对 G01 两段视频分别检查。

每段视频使用三个不同参考。

检查每个参考是否都能够通过：

- RGB；
- Mask；
- HERO depth；
- Eikonal；

对同一网络产生有效约束。

Eikonal 是共享场正则，不需要人为拆成三个独立参考来源。

必须记录每个参考：

- 输入射线数量；
- 正 Mask 数量；
- 合格 HERO 深度数量；
- 前表面命中数量；
- 未命中数量；
- Mask Loss；
- RGB Loss；
- Depth Loss；
- 梯度范数；
- 不同参考的梯度方向关系。

不得因为三个参考进入同一个函数调用，就宣称完成了有效三参考监督。

**必须实际验证三个参考均对共享神经参数产生了可解释的梯度贡献。**

---

# 七、必须专门检查深度损失的退化问题

这是 PM 新增的强制要求。

当前：

\[
L_{\mathrm{depth}}
\]

只对预测命中的射线计算回归。

这可能引入风险：

**网络减少前表面命中，使剩余深度的平均损失降低。**

因此请建立专门的反例测试。

保持固定的真实深度观测集合：

\[
\mathcal V_{\mathrm{observed}}
\]

比较：

1. 正常命中；
2. 部分射线未命中；
3. 大量射线未命中；
4. 全部未命中。

观察：

- 深度 Loss；
- Mask Loss；
- 总 Loss；
- 有效命中比例；
- 梯度是否仍然指向恢复可见表面。

不得将没有命中的深度写成 0。

不得只使用：

\[
\frac{1}{N_{\mathrm{hit}}}
\sum_{\mathrm{hit}}L
\]

的下降证明优化改善。

建议采用固定观测分母报告：

\[
\boxed{
C_{\mathrm{hit}}
=
\frac{N_{\mathrm{hit}}}
{N_{\mathrm{observed}}}
}
\]

并考虑在后续训练中将缺失命中的约束交给可微的正 Mask / 占据监督处理。

如果需要新增损失，必须明确其数学定义与梯度来源，不得使用不可微的命中计数假装形成训练梯度。

**本轮必须给出明确结论：当前联合损失是否存在“降低覆盖换取更低误差”的潜在退化。**

---

# 八、评价与可视化

本轮没有正式训练，因此不要求高质量三维 Mesh。

但必须生成四组核心证据。

### 图1：HERO 跨视角深度冲突

真实 RGB + 对应 Polyp Mask。

展示：

- A 原始 HERO 深度；
- A 投影到 B 的深度；
- B 原始 HERO 深度；
- 合法重叠区域；
- 有符号残差；
- 遮挡/无效区域。

004 与 005 分开统计。

### 图2：Ring CAD 深度残差

展示：

- 真实 Ring Mask；
- CAD 合法可见像素；
- HERO Ring 深度；
- Ring 残差分布。

如果无合法 Ring 深度，必须明确展示不可评价原因，不得生成替代的虚构数据。

### 图3：真实 MonoSDF 接线

展示：

- 实际有限射线采样；
- raw SDF；
- 预测有限 opacity；
- 前表面命中；
- beta/初始化检查；
- 真实网络梯度。

明确标记：

`UNTRAINED OFFICIAL NETWORK / CPU TEST`

### 图4：三参考共同监督

展示两段视频各三个真实参考的：

- 参考图像；
- Mask；
- 有效深度；
- 命中比例；
- RGB/Mask/Depth 梯度；
- 冲突分布。

不得把无训练网络的随机输出称为真实重建效果。

---

# 九、工程交付

建立独立分支：

`exp/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001`

优先从当前 E2 continuation 的已验证提交继续。

交付：

```text
experiments/
└── TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001/
    ├── TECHNICAL_REPORT.md
    ├── FAILURE_LEDGER.md
    ├── REPRODUCE.md
    │
    ├── code/
    │   ├── depth_consistency.py
    │   ├── ring_depth_audit.py
    │   ├── bias_diagnostics.py
    │   ├── official_sdf_cpu_adapter.py
    │   └── test_miss_degeneracy.py
    │
    ├── metrics/
    │   ├── HERO_PAIRWISE_DEPTH_CONFLICTS.csv
    │   ├── RING_DEPTH_RESIDUALS.csv
    │   ├── DEPTH_BIAS_DIAGNOSTICS.csv
    │   ├── OFFICIAL_SDF_CPU_GATE.json
    │   └── DEGENERACY_TESTS.csv
    │
    ├── docs/
    │   ├── DEPTH_CORRECTION_DECISION.md
    │   └── GPU_MVP_PREREGISTRATION.md
    │
    └── figures/
        ├── Fig1_depth_conflicts.png
        ├── Fig2_ring_depth_residuals.png
        ├── Fig3_official_sdf_cpu.png
        └── Fig4_three_reference_gradients.png
```

目录可根据现有仓库结构调整，但相应证据不可省略。

考虑到近期磁盘空间不足：

- 不复制大型 HERO 权重；
- 不重复下载 MapAnything；
- 不复制原始视频；
- 不生成无意义的大规模中间点云；
- Git 只保存代码、指标、报告和精选图；
- 大型临时文件使用已有工作空间并记录来源；
- 不主动删除其他实验资产。

---

# 十、最终验收

必须分别给出以下结论：

| Gate | 验收目标 |
|---|---|
| DEPTH_CONSISTENCY | 正确计算真实跨视角深度残差 |
| RING_DEPTH_DIAGNOSTIC | 有效利用或明确否定 Ring 深度诊断 |
| BIAS_IDENTIFIABILITY | 判断是否有证据支持参考级偏移 |
| OFFICIAL_SDF_CPU | 真实官方网络完成有界前向与反向 |
| THREE_REFERENCE_GRADIENT | 三参考对同一网络产生有效梯度 |
| MISS_DEGENERACY | 明确识别或排除降低覆盖的退化风险 |
| GPU_MVP_READINESS | 给出进入科学训练仍缺少的具体条件 |

若其中一项失败，应记录失败原因，不允许通过删减困难样本制造成功。

本轮正式状态：

```text
MODEL_FORWARD: CPU_DIAGNOSTIC_ONLY
MODEL_TRAINING: NOT_RUN
OPTIMIZER_STEP: 0
GPU: NOT_AUTHORIZED
MAPANYTHING_FORWARD: NOT_RUN
NEW_RECONSTRUCTION_RESULT: NOT_CLAIMED
```

---

# 十一、下一阶段科学实验的预注册

本轮最后需要提出一个真正可执行的 GPU MVP。

但不得提前运行。

建议：

### S0：原生 HERO 基线

使用：

- 同视频三参考；
- 真实 RGB；
- 原生 HERO 深度；
- 已冻结相机；
- 共享 Polyp SDF。

### S1：Mask + Ring

增加：

- 有限 Mask 监督；
- Ring CAD 真实遮挡。

### S2：不确定性感知

在 S1 基础上加入：

- 冻结的来源可靠性；
- 稳健深度损失；
- 冲突感知权重。

### S3：可选偏移校正

仅当 P1 证明存在有物理依据的参考级偏移时考虑。

否则取消此消融。

MapAnything 仍然是独立竞争路线，沿用 E2 已建立的 M0–M4，不得将其降格为 SDF 初始化。

正式 GPU MVP 必须明确：

- 视频与三个参考身份；
- 模型结构；
- 初始化；
- beta；
- 学习率；
- 损失权重；
- 最大优化步数；
- 资源预算；
- 固定随机种子；
- 真实可见表面覆盖；
- Ring CAD 物理一致性；
- 多视角真实图像解释；
- 失败停止规则；
- 历史 Raw/Cleaned/F1/F2/F3 对照；
- 非严格留出评价的披露方式。

**如果发现模型无法获得有效梯度，不得启动正式训练。**

---

# 十二、最终工作要求

请直接执行 P1 和 P2。

不要先返回一份计划等待批准。

不需要重新初始化 Codex。

优先完成真实数据诊断和真实网络接线，而不是继续扩大抽象数学实验。

完成后提交：

1. 完整技术报告；
2. 实际代码；
3. 数据和实验指标；
4. 四张核心图；
5. 失败记录；
6. 深度校正是否必要的明确判断；
7. 下一阶段 GPU MVP 的正式配置建议。

**本轮最重要的科研问题是：不同 HERO 深度之间的偏差是否会阻碍统一 Polyp SDF，以及当前真实 MonoSDF 网络是否已经具备接受多参考联合监督的条件。**

不要求本轮给出高精度三维模型，但必须为下一轮真正恢复三维表面提供可靠的技术基础。