# Role：Ring-First 3D Reconstruction Research Engineer

# Phase E2.7 — Bounded Neural SDF Learning Pilot

任务编号：

`TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001`

中文名称：

**基于三参考联合监督的 Neural SDF 短程学习与可见表面恢复实验**

---

# 一、正式授权与任务边界

研究者已经明确批准本轮：

1. 真实 MonoSDF 神经参数更新；
2. GPU 训练；
3. Adam 优化；
4. 模型检查点保存；
5. 有界 A/B 对照实验。

因此，本任务不需要再次请求训练授权。

但是授权严格限定为：

- 一个物理场景：G01_005；
- 三个真实参考视角；
- 两个预注册实验组；
- 每组最多100个 optimizer steps；
- 单次运行最多30分钟；
- GPU allocated memory 不超过5 GiB；
- 两组串行运行，不允许并行占用 GPU。

本轮不自动授权：

- G01_004 训练；
- 1000步或更长时间训练；
- 大规模超参数搜索；
- MapAnything 训练；
- 相机、位姿、Ring CAD 或 HERO 深度修正；
- GT/Oracle 参与训练或选择模型。

**本轮目标是证明神经网络能否真正学习，而不是追求最终三维重建精度。**

---

# 二、代码与研究资产继承

## 2.1 Git 分支

从以下分支的最新提交开始：

`exp/TASK-NEURAL-E2P6-INITIALIZATION-AND-STABLE-LOSS-001`

基准 commit：

`a69a17099e4ed5ff34ed8e1be49157fbda329615`

创建独立分支：

`exp/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001`

所有新增内容放在：

`experiments/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001/`

不得修改 main、E2.5、E2.6 或其他历史实验。

## 2.2 必须继承的成果

直接复用：

1. E2 的有限 ROI、五类语义、Ring CAD 首次交点约束；
2. E2.5 的真实官方 MonoSDF 网络；
3. E2.6 的唯一几何壳初始化规则；
4. E2.6 稳定 log-optical-depth Mask BCE；
5. E2.6 弱 HERO 表面锚点；
6. 原生 HERO 深度及1/0.25冲突权重；
7. 原有 source component 1/3 权重；
8. 已有真实相机、内参、ROI 和坐标转换。

官方网络保持：

- MonoSDFNetwork；
- plain MLP；
- 8层256维隐式网络；
- positional encoding 6；
- skip connection 4；
- 256维 feature；
- 官方 rendering network。

官方代码 revision：

`12513009cd20a08b35ddc2c55a7e42da2c7baf43`

不得重新设计一个更简单的 MLP 代替官方网络。

---

# 三、实验对象与固定数据

本轮仅使用：

`G01_005`

三个参考：

1. `raw00057`
2. `raw00459`
3. `raw00745`

三个参考对应同一静止 Polyp + Ring + Background 场景。

**三个参考必须共同监督同一个神经 SDF，不允许每个视角单独训练一个网络。**

## 3.1 训练集与监测集

使用 E2.6 已经冻结、互不重叠的像素集合。

| 数据 | 每参考射线 | 用途 |
|---|---:|---|
| extra | 64 | 实际训练 |
| small | 16 | 固定像素留出监测 |

三个视角共计：

- 训练射线：192；
- 训练集合格 HERO：96；
- 监测射线：48；
- 监测集合格 HERO：18。

初始前表面命中：

| 参考 | extra 初始命中 | small 初始命中 |
|---|---:|---:|
| raw00057 | 27/32 | 6/6 |
| raw00459 | 29/32 | 6/6 |
| raw00745 | 31/32 | 6/6 |

这些是本轮固定基线。

禁止重新挑选容易命中的像素，禁止删除困难射线。

small 只用于监测，不允许参与 RGB、Depth、Mask、Anchor 或 Eikonal 的训练。

注意：small 与 extra 虽然像素不重叠，但来自同一组三张图像。因此只能称为像素级留出监测，不能称为独立视角或独立物理场景测试。

## 3.2 训练射线

每一步同时使用三个视角的全部64条 extra 射线。

即每个 optimizer step 使用：

`64 × 3 = 192 rays`

三个视角分别计算损失，再进行等权联合。

如 GPU 显存不足，允许采用严格等价的梯度累积，不允许减少参考视角或删除困难样本。

Eikonal 使用每参考预先固定的6个 P_INTERIOR 射线中点，共18个固定点，全部来自训练集 extra。

---

# 四、初始化：完全冻结，不再搜索

采用 E2.6 唯一通过 G01_005 三参考门槛的初始化规则。

固定参数：

| 参数 | 数值 |
|---|---:|
| seed | 20261031 |
| ROI origin X | 0.2917828830804057 mm |
| ROI origin Y | -0.793891385404947 mm |
| ROI origin Z | -4.4124351955893335 mm |
| mm_per_unit | 28.3780268204276 |
| ROI radius | 10.27908157050465 mm |
| shell radius | 0.5 ROI radius |
| shell points | 128 Fibonacci |
| bias_network | 0.33739213617088626 |
| beta initial | 0.08 mm |

初始模型 SHA256：

`7b5b64e57523d72ededf4c27f2314dd84776066f66197056c44bf014b2b3c81c`

必须从相同 seed 和冻结 bias 重建初始模型，并验证参数哈希。

建议先在 CPU 上构造 FP64 canonical model，验证 SHA256，再转换为 FP32 并移动到 GPU。

不得在 GPU 上重新随机初始化，导致模型权重与 E2.6 不一致。

训练过程中不再调整：

- shell radius；
- bias；
- beta 初值；
- ROI；
- world origin；
- mm_per_unit。

beta 可以按照后续优化器配置学习，但不得手工修改其初值。

---

# 五、训练前必须通过的工程门槛

这里允许执行 GPU 前向与反向诊断，但尚未允许 optimizer.step。

## 5.1 固定采样一致性

E2.6 已验证128个有限采样单元，但尚未证明其对真实表面变化充分。

进行一次有界比较：

- 128 cells；
- 256 cells。

在同一冻结模型、同一射线、同一积分区间下比较。

至少记录：

- 前表面交点；
- opacity；
- RGB；
- Mask；
- Depth；
- 隐式网络梯度；
- beta。

要求检查：

- Mask 损失相对差异；
- 深度预测差异；
- 前表面命中集合变化；
- 梯度余弦相似度；
- 梯度范数相对差异；
- Δt/beta 分布。

若128与256结果基本一致，使用128。

若差异明显，使用256，并如实记录采样尚未完全收敛。

不允许继续无限搜索采样密度。

官方 adaptive sampler 仍未经过验证，本轮不得直接使用。

## 5.2 GPU 数值一致性

对六份冻结数据包进行 CPU/GPU 对照。

检查：

1. FP32 损失有限；
2. CPU/GPU 损失差异在预注册数值容差内；
3. 完整隐式参数梯度余弦不低于0.995；
4. 梯度范数相对误差不超过2%；
5. 前表面命中结果无明显设备差异；
6. 预测深度差异不超过预注册容差。

采用 E2.6 已验证的稳定 Mask 数值实现。

关闭 AMP 和 TF32，避免额外精度变量。

如果 GPU parity 失败，停止，不得直接开始训练，也不得偷偷改成 CPU 参数更新。

**通过上述两项门槛后，直接开始本任务训练，不需要再次向研究者请求授权。**

---

# 六、核心竞争实验：A/B 两组

这是本轮最重要的设计。

两组必须具有：

- 完全相同的初始化；
- 完全相同的三个参考；
- 完全相同的训练像素；
- 完全相同的采样密度；
- 完全相同的优化器；
- 完全相同的训练步数；
- 完全相同的损失权重。

唯一差异：

**B 组增加弱 HERO 表面锚点。**

## A组：Stable Mask Baseline

损失：

\[
L_A=
L_{RGB}
+0.1L_{Depth}
+0.1L_{Mask}
+0.1L_{Eikonal}
\]

其中：

### RGB

使用官方颜色网络和原有稳健 RGB 损失。

Huber：

\[
\delta_{RGB}=0.05
\]

保持原有 P_INTERIOR 和可见前表面资格。

### Depth

使用原生 HERO 轴向深度。

Huber：

\[
\delta_{Depth}=0.5\text{ mm}
\]

不允许：

- 深度平移；
- 深度缩放；
- 逐像素偏移；
- 参考级深度校正。

未命中深度保持 NaN，不允许用0代替。

### Mask

使用 E2.6 已经验证的稳定有限段 BCE：

\[
L_{Mask}
=
\operatorname{BCE}
\left(
M_{\mathrm{pred}},M_{\mathrm{source}}
\right)
\]

必须保留：

- log-optical-depth 稳定计算；
- 固定有限 ROI；
- 原始 mask_weight；
- Ring CAD 截断；
- 固定观测分母。

不得使用旧的数值不稳定 BCE 代替。

### Eikonal

使用官方 SDF 梯度范数正则。

只计算一次共享 Eikonal，不要为三个参考重复增加三份正则权重。

## B组：Stable Mask + Weak HERO Anchor

在 A 组基础上增加：

\[
L_B=L_A+0.01L_{Anchor}
\]

锚点：

\[
L_{Anchor}
=
\sum_i w_i
\rho_{0.5}
\left(
f_\theta(X_i^{HERO})
\right)
\]

其中：

- Huber delta = 0.5 mm；
- weight = 0.01；
- 使用原生合格 HERO 点；
- 保留 source component 1/3；
- 保留已有1/0.25冲突权重；
- 不依赖当前网络是否已经命中表面。

锚点只使用训练集 extra。

不得将 HERO 当作精确 GT。

不得通过修改 HERO 深度让其与当前模型吻合。

## 重要的联合规则

对每个参考分别计算 RGB、Depth、Mask、Anchor。

三个参考等权：

\[
L_{\mathrm{joint}}
=
\frac13
\sum_{v=1}^{3}L_v
+
0.1L_{Eikonal}
\]

B 组只在这个表达式中额外加入锚点项。

禁止通过某个参考较大的像素数量使其支配整个训练。

---

# 七、优化器与训练预算

采用：

**Adam**

| 参数组 | 学习率 |
|---|---:|
| implicit network | 1e-4 |
| rendering network | 1e-4 |
| density beta | 1e-5 |

其余：

- betas = (0.9, 0.999)；
- weight_decay = 0；
- 不使用学习率搜索；
- 不使用随机数据增强；
- 不使用 AMP；
- 不增加额外正则项。

每组：

`MAX_STEPS = 100`

检查点：

- step 0；
- step 25；
- step 50；
- step 75；
- step 100。

每5步记录一次固定探针指标。

两组串行执行。

A 结束后重新加载完全相同的初始化，再运行 B。

不能把 A 的训练结果作为 B 的初始化。

不能挑选中间最漂亮的检查点替代最终结果。

如果提前触发停止条件，保留最后一个安全检查点。

---

# 八、训练过程中的重点监测

这部分优先级高于总 Loss。

## 8.1 覆盖率

每个参考分别记录：

\[
C_v=
\frac{N_{\mathrm{front-hit}}}
{N_{\mathrm{qualified\ HERO}}}
\]

同时记录：

- 固定观测数；
- 前表面命中数；
- 未命中数；
- opacity；
- 前交点位置。

不允许因为某条射线未命中而从统计分母中删除。

离散 hit count 只能用于评价与停机，不允许将其冒充可微损失。

## 8.2 几何变化

每5步记录：

- SDF 零水平集；
- 中心切片；
- 固定 ROI 内表面范围；
- 前表面命中深度；
- 各参考的预测 Mask；
- 三参考之间的几何一致性。

特别关注：

1. 原先未命中的区域有没有形成合理表面？
2. 息肉头部有没有过度膨胀？
3. 息肉下部是否形成合理的连续结构？
4. 是否出现多个不合理零水平集？
5. 是否出现整个 ROI 被预测成物体内部？

## 8.3 Ring

严格保留：

- Ring CAD；
- 首次 CAD 交点；
- 积分终点不超过 Ring 首交点减0.05 mm；
- 不在 Ring 后方监督。

Ring 继续作为黑色 CAD 实体展示，不重建 Ring 点云。

## 8.4 损失和梯度

每5步记录：

- RGB Loss；
- Depth Loss；
- Stable Mask Loss；
- Eikonal Loss；
- Anchor Loss；
- 各项完整参数梯度范数；
- beta 物理值；
- 总梯度范数；
- 参数更新幅度。

不得只报告一个总 Loss。

---

# 九、严格停止条件

满足任一条件，立即停止当前实验组：

1. 出现 NaN/Inf；
2. 任一参考在固定 HERO 集合上完全没有前表面命中；
3. 任一参考的固定观测命中率低于50%；
4. 相对初始化，某参考覆盖率下降超过10个百分点，并连续3次固定探针检查仍未恢复；
5. 支持表面出现超过0.1 mm 的 CAD 穿插，且比例超过1%；
6. 未知区域或 Ring 后方进入训练监督；
7. GPU 显存超过5 GiB；
8. 单组训练超过30分钟。

A 组因科学性原因停止后，B 组仍可在相同软件和硬件条件下运行，以验证弱锚点是否有帮助。

如果是 GPU 数值错误或软件实现错误，则必须先解决工程错误并重新完成 parity，不能直接进入 B。

任何覆盖率下降均标记为：

`POTENTIAL_FAILURE_COVERAGE_LOWER`

即使总 Loss 更低，也不能宣称改善。

---

# 十、最终验收与可视化

本轮必须交付真实训练结果，而不只是训练日志。

至少生成以下四张核心证据图。

### Figure 1：SDF 学习过程

同一坐标系下展示：

- Initial；
- Step25；
- Step50；
- Step100。

显示实际 SDF 零水平集和固定 ROI。

A/B 分开展示。

不得用解析球替代实际网络输出。

### Figure 2：三个参考的真实图像拟合

每个参考显示：

- 原始 RGB；
- 原始 Polyp/Mask；
- 预测 Mask/Opacity；
- 预测深度；
- 真实与预测边界叠加。

所有参考必须使用同一个共享 SDF。

### Figure 3：三维可见表面

使用真实训练得到的零水平集提取可见表面。

要求：

- Ring 为黑色 CAD 实体；
- 保留真实相机坐标；
- 展示三个相机视角；
- 展示世界 X/Y/Z 方向；
- 显示表面支持区域；
- 区分 supported、conflict、unknown。

不得：

- 强制封闭背面；
- 补造不可见曲面；
- 强制 watertight；
- 使用合成平面替代真实点云或表面；
- 将未知区域包装成真实重建结果。

### Figure 4：多视角验证和训练曲线

展示：

- 三参考真实图像；
- 共享模型预测；
- A→B、B→C 等真实视角解释；
- RGB 差异；
- Mask 覆盖；
- Depth 残差；
- 固定观测覆盖率随训练变化。

不能用目标视角 RGB 重新给错误几何贴纹理。

---

# 十一、成功判定

不要把训练结束等同于研究成功。

最终分为以下类别：

| 状态 | 定义 |
|---|---|
| PREFLIGHT_BLOCKED | GPU/数值一致性门槛失败，未训练 |
| LEARNING_FEASIBLE | 至少一组完成短程训练，覆盖稳定，几何有可信改善 |
| ANCHOR_BENEFICIAL | B 在不牺牲覆盖的情况下，比 A 获得更好的留出监测结果 |
| ANCHOR_NOT_BENEFICIAL | B 没有改善，或引入额外几何问题 |
| NO_LEARNING | 两组均未形成可信改善 |
| TRAINING_STOPPED | 触发停止条件，保留失败结果 |

认定 LEARNING_FEASIBLE 至少要求：

1. 完成预注册训练预算，或有充分证据说明提前停止原因；
2. 三个参考都保留有效前表面；
3. 固定留出监测覆盖没有被牺牲；
4. Mask、Depth 和 RGB 至少有合理的改善证据；
5. 零水平集没有明显膨胀或多重伪面；
6. 三个真实视角能够共同解释同一表面；
7. Ring 几何关系正确。

B 组是否优于 A 组必须单独判断。

不允许因为 B 的 HERO 深度残差更小，就直接宣布 B 更好。

本轮不进行绝对三维误差认证。

GT 继续封存。

---

# 十二、交付与仓库管理

实验目录：

`experiments/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001/`

要求：

```text
TASK.md
TECHNICAL_REPORT.md
FAILURE_LEDGER.md
REPRODUCE.md
RESULT_INDEX.md

config/
    PREREGISTERED.json
    TRAINING_CONFIG.json

code/
    gpu_model_adapter.py
    fixed_renderer.py
    train_arm.py
    evaluate.py
    visualize.py

metrics/
    TRAINING_CURVES.csv
    PER_REFERENCE_METRICS.csv
    COVERAGE_HISTORY.csv
    A_B_COMPARISON.json
    GPU_PARITY.json
    FINAL_STATUS.json

checkpoints/
    A/
    B/

figures/
    Fig1_SDF_learning.png
    Fig2_three_reference_fit.png
    Fig3_visible_surface.png
    Fig4_multiview_validation.png

provenance/
    INITIAL_MODEL.json
    SOURCE_PIXELS.json
    ENVIRONMENT.json
    CHECKPOINT_HASHES.json
```

保留 A/B 最终模型及必要的中间检查点。

模型权重使用精简 state_dict，不上传原始视频、完整原始数据包或大型临时缓存。

所有结果上传独立 Git 分支，不修改 main。

---

# 十三、最终科研报告必须回答的问题

请不要只汇报训练完成情况。

必须回答：

1. 同一个 MonoSDF 能否真正联合解释三个视角？
2. 稳定 Mask BCE 是否在实际参数更新中帮助了表面形成？
3. 弱 HERO Anchor 是否真正改善了几何，而不是简单贴近 HERO 深度？
4. A/B 哪一组更能保留真实可见表面？
5. 训练是否存在通过牺牲覆盖率降低 Loss 的现象？
6. 息肉头部、下部和基底分别发生了什么变化？
7. 是否出现球壳膨胀、伪面或 Ring 穿插？
8. 下一步应该继续优化当前神经隐式路线，还是重新考虑几何表示？

最后明确：

**本轮只研究 G01_005 的短程神经学习能力，不得将结果外推为整个 G01、所有息肉形态或完整三维重建系统已经成功。**

完成后提交：

- Git 分支；
- 完整技术报告；
- A/B 模型；
- 四张核心图；
- 全部训练曲线；
- 失败记录；
- 下一阶段建议。

开始执行。