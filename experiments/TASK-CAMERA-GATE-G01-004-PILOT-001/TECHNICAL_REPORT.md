# G01_004 Camera Gate Pilot 技术报告

日期：2026-11-02（Asia/Shanghai）。任务 `TASK-CAMERA-GATE-G01-004-PILOT-001`，继承E3-C提交 `e8feece0718fee24a1b04b5e250629820e4f8299`，独立分支 `exp/TASK-CAMERA-GATE-G01-004-PILOT-001`。

**结论：本轮没有证明两个新增参考存在实际位姿错误。按冻结v0.1试行规则，五份相机均为INSUFFICIENT_EVIDENCE。** 三份旧参考与growth_r04通过Ring，但旧ref03相关图像关系对匹配器/2px内点门槛敏感；new_r00只有到ref03的充分对应，Ring略超容差；growth_r04在ref03/ref08关系良好，ref13额外留出对应不足。未满足明确错误触发条件，**优化器调用0次**，没有修正相机输出。数值检查通过与相机取得资格是两个独立结论。

本轮返回的是新试行规范下的资格，**不覆写或撤销历史资格，不把旧相机变成GT**。没有重估轨迹、BA/SLAM、新神经匹配/HERO推理、GPU、全局场、几何变形、GT/Oracle或Dxy操作。F1/F2/F3从未作为输入。完成后停止等待PM。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1物理组G01、1视频004、固定5相机（3旧+2新增），不含其他6候选 |
| 本算法独立成功 | 5/5完成相机证据计算；新资格通过0/5；不能将数值完成等同物理准确 |
| 本算法失败 | 5/5资格未获充分证明，全部INSUFFICIENT_EVIDENCE；认证/修正位姿NaN；原相机仅作冻结候选保留 |
| 历史测量值回退 | 0；无S0/V2/照片直径/融合预测补齐 |
| 失败组及具体原因 | G01_004逐相机见[失败记录](FAILURE_LEDGER.md)及[三图](#核心图) |
| 最终统计样本 | 全5相机、9图像对、20原HERO辅助有向投影；测量成功0/1；本轮不执行直径或形状测量；MedARE、MAE、p95、最大测量误差均NaN；共同测量成功组N=0。 |
| 是否使用GT选择算法 | 否；正式计算前冻结协议/资产/匹配计划，参数SHA `eaf434973efafdc29d1f0c45634a11155f29ca47f49bafafada504d0547e9fe9`；未依结果换匹配器或视角 |

## 五相机汇总

| 相机 | 原资格 | Ring 中位/p95 | 图像几何 | HERO覆盖/精确率（辅助） | 修正前后 | 新判断 |
| --- | --- | --- | --- | --- | --- | --- |
| ref03 | 历史条件性 | 1.41/4.00 px；通过 | 2/2 必需关系通过 | 51.2%/97.8% | 未修正 | `INSUFFICIENT_EVIDENCE` |
| ref08 | 历史条件性 | 1.41/5.39 px；通过 | 2/2 必需关系通过 | 89.2%/94.0% | 未修正 | `INSUFFICIENT_EVIDENCE` |
| ref13 | 历史条件性 | 2.00/4.24 px；通过 | 1/2 必需关系通过 | 85.4%/98.0% | 未修正 | `INSUFFICIENT_EVIDENCE` |
| new_r00 | 未经验证 | 2.83/6.71 px；未通过 | 1/3 必需关系通过 | 48.6%/97.7% | 未修正 | `INSUFFICIENT_EVIDENCE` |
| growth_r04 | 未经验证 | 2.00/4.12 px；通过 | 2/3 必需关系通过 | 60.2%/97.5% | 未修正 | `INSUFFICIENT_EVIDENCE` |

HERO栏的“精确率”仅指原XYZ投影落入目标Polyp Mask的像素比例，不是三维正确率；全20投影在[辅助结果](config/HERO_AUXILIARY.csv)。汇总采用固定source ref08，目标ref08时用ref03，未按覆盖/误差选视角。没有HERO辅助指标进入相机资格判定。

## 输入与继承

直接复用E3-A身份/K/c2w/CAD与相机表、View Partition匹配器函数、V13原始匹配缓存、Phase D原色点投影raster和`real_p0_renderer`/`SameCameraScene`。只AST抽取必要函数，未执行历史main。[身份表](config/INPUT_IDENTITY.json)、[输入SHA](config/INPUT_HASHES_BEFORE.json)、[复用记录](config/CODE_REUSE.json)保留路径和SHA。

五份图像逐文件及解码尺寸绑定到同一冻结缓存身份，640×360；相机Xc=(Xw−C)R，c2w=(R,C)，轴向Z和XYZ单位mm，整数像素中心，K不加半像素偏移。相机包、HERO原始包的K/pose及元数据数值一致。历史 `G01_video004_LOCAL_RING_MM` 与 `G01_004_LOCAL_RING_MM` 视为已核验数值一致的同源别名，不进行坐标拟合。**缓存RGB身份充分，原视频逐帧号身份仍未独立认证**；没有为此重新解码或重新审计整段视频。固定K490及无新畸变校准仍是条件。

原3参考的相机上游均是冻结模型候选，历史筛查不是相机GT。Ring CAD是唯一固定公制参考，不以任何融合Mesh或HERO距离反向证明相机。

## Test 1：Ring

使用原始CAD全分辨率真实射线首次交点生成不透明投影；Ring Mask轮廓和CAD轮廓双向最近距离，报告中位、MAE、p95、原始未剔除统计。Polyp接触2px内及图像裁剪边界不作可观察Ring轮廓；没有把接触边缘当作真实环轮廓。可观察轮廓双向至少100点，MAE≤3px、p95≤6px；继承V13容差，明确矛盾阈值为MAE>6或p95>12px。Ring中心采用Mask/CAD像素质心差，形状采用二阶矩轴比与不含Polyp域IoU，**仅作描述**，部分遮挡会偏置质心。

new_r00的MAE=3.35px、p95=6.71px，属于容差未过而非本轮明确矛盾。其他四份通过。Ring旋转对称，不能据此认证完整六自由度或世界yaw。保留原CAD，未改Ring参数。

## Test 2：真实RGB几何

9个固定配对：原3两两3对，2新增分别对ref03/ref08/ref13共6对，不增加其他视角。复用4个SIFT缓存（含View Partition的new_r00↔ref03），补充5个CPU SIFT配对；只读复用原3的LightGlue/MASt3R/RoMa及new_r00↔ref03的MASt3R缓存，**没有运行任何神经匹配器**。缓存优先级固定SIFT→LightGlue→MASt3R→RoMa，仅按RGB-only F对应数量/覆盖充分性选择，不按候选位姿误差选获胜方法。全部匹配器输出保留在[完整结果](config/IMAGE_GEOMETRY_ALL_METHODS.csv)。历史SIFT缓存的检测Mask策略有差异，后处理语义规则统一，不能将匹配器差异解释成相机真值差异。

用同语义非Ring、非高光、图内点，按固定16px hash留出约20%；在非留出点拟合RGB-only Fundamental RANSAC（2px，seed0，2000次上限）。fit/held分别至少12/8个F相容点、各图≥4个32px格、凸包≥1%图像；pose判断使用这些**不由候选pose筛选**的对应及全部可用对应的原始统计。F筛查是真实RGB模型拟合，不是物理对应GT。ref13整对不进入本轮位姿拟合；对ref13自身做F诊断不等于调整它的位姿。它是本轮额外留出，**不是整个历史管线从未见过的盲测**。

| 图像关系 | 固定主方法 | F合格fit/held N | ≤2px内点比例fit/held | held中位/p95 px | 关系结论 |
| --- | --- | --- | --- | --- | --- |
| ref03 ↔ ref08 | SIFT | 48/10 | 0.417/0.400 | 2.78/4.06 | 不足/未通过 |
| ref03 ↔ ref13 | LightGlue | 96/18 | 0.562/0.722 | 0.76/3.57 | 不足/未通过 |
| ref08 ↔ ref13 | SIFT | 109/29 | 0.954/0.897 | 0.81/2.23 | 通过 |
| new_r00 ↔ ref03 | SIFT | 66/15 | 0.970/0.933 | 0.74/2.15 | 通过 |
| new_r00 ↔ ref08 | SIFT（数据不足，不作资格票） | 0/0 | NaN/NaN | NaN/NaN | 不足/未通过 |
| new_r00 ↔ ref13 | SIFT（数据不足，不作资格票） | 0/0 | NaN/NaN | NaN/NaN | 不足/未通过 |
| growth_r04 ↔ ref03 | SIFT | 97/23 | 1.000/1.000 | 0.42/1.11 | 通过 |
| growth_r04 ↔ ref08 | SIFT | 78/24 | 0.744/0.833 | 1.05/2.77 | 通过 |
| growth_r04 ↔ ref13 | SIFT（数据不足，不作资格票） | 26/3 | 0.538/1.000 | 0.59/1.49 | 不足/未通过 |

相机预测F=Kb^(-T)[t]×Rrel Ka^(-1)，报告平方根Sampson像素误差，fit/held中位≤3px、p95≤6px、≤2px内点率≥70%；实际两相机射线视差中位≥0.5°，三角化正深度≥95%。同时报告RGB-only homography相容比例≥90%及低视差退化，匹配覆盖与数值秩均不替代物理对应身份。

ref03↔ref08主SIFT的fit/held内点率41.7%/40.0%；ref03↔ref13固定回退LightGlue为56.3%/72.2%，均未过完整关系门槛，**但没有达到明确矛盾阈值**。ref08↔ref13通过。历史MASt3R在ref03两对均可通过；RoMa结论亦有差异。此差异保留为不确定性，不能事后换主方法使旧参考通过，也不能据SIFT未过就断言ref03实际错误。

new_r00↔ref03通过；到ref08/ref13仅11/5个raw SIFT点，无法建立独立F验证。growth_r04↔ref03/ref08通过；到ref13有36个raw点，但F相容fit/held仅26/3，且留出覆盖不足，未达到冻结充分性规则。**ref13整对作为额外视角并不允许事后取消该对预注册的空间留出检查。**

## 可观测性与有界修正

采用已有解析torus轮廓函数，并检查其与原CAD表面方程一致；仅用于局部导数与可能修正，正式Ring评分始终用原Mesh raycast。Ring残差必须保留已知共同世界yaw零空间；消除有限曲线采样产生的伪导数后计算Ring+真实匹配**无先验**Jacobian SVD，旋转/平移列尺度5°/.5mm，相对奇异值门槛1e-3。五份局部分支秩均6；不意味着全局Ring对称性、共同参考系统偏差、匹配身份或K畸变已被证明。单独Ring至多秩5。HERO不参与此秩或修正。

两个候选均未满足“明确的FIT侧几何错误”触发条件。new_r00还缺两拟合参考约束，因此均NOT_ATTEMPTED。未进行SE(3)优化，修正前后数值不存在，不能拿原相机冒称修正成功。已实现的有界薄适配采用成熟SciPy soft_l1、冻结初值、最多60次评估、总旋转≤5°/平移≤.5mm、固定Ring与K；只拟合ref03/ref08非留出图像点，不以HERO距离优化。参数/边界不会因留出结果改变。本轮未触发的优化路径**未获得真实修复效能验收**。

## Test 3：HERO辅助

前两项原始结果冻结后才读取原始HERO XYZ；核验XYZ由已归档原深度直接反投影，无清理替代、融合、SE3形变或重新推理。五视角20个有向投影均完成，Phase D原色点raster保持原始点ID、真实目标K/c2w和CAD首次交点。固定目标Polyp像素分母，同时报告投影覆盖、落Mask比例、CAD挡住的点数和RGB误差。

辅助结果显示可见Polyp投影可以较好落Mask，但覆盖不等于几何正确或相机已认证。原点集仅Polyp：主SIFT对应很多在背景，XYZ匹配偏移可计算数很少或0，明确保留N=0/NaN，不能以此证明不存在系统偏移。Mask覆盖、RGB误差同时受HERO形状、可见性和真实对应影响，**不能单独归因位姿**，也没有反馈进前两项。

## 验证与复现

[工程验证](config/VALIDATION_RESULTS.json)共25项通过，包括像素/轴向深度/相机F方向控制、Ring连续yaw对称、缓存匹配坐标与输入SHA、ref13必需身份、无HERO资格反馈、原始固定分母和历史工作树保护。[隔离CPU复现](config/REPRODUCTION_VALIDATION.json)对六类完整数值/决策结果逐项精确一致。工程通过不是相机认证：新资格仍0/5，优化器0次。三图经过实际视觉核对，全部来自本轮真实RGB/原CAD/原XYZ。

## 必须回答的四个问题

1. **三个旧参考是否仍具条件性资格？** 历史状态保留；在本轮更完整且预先冻结的v0.1试行标准下，三者均未取得完整COND，主因ref03相关关系的主方法内点比例不足，非Ring失效、非已证明实际错误。ref08↔ref13本身通过。
2. **两个新增参考失败在哪里？** new_r00是Ring边界略超容差，加ref08/ref13对应不足；growth_r04的Ring和ref03/ref08真实图像关系通过，但ref13空间留出证据不足。两者均INSUFFICIENT_EVIDENCE，不硬判几何错误。
3. **是否有无需大改即可恢复资格的候选？** growth_r04是现有最接近者：无需发现新的几何修正就能解释两个拟合参考，但仍需ref13充分且独立的图像几何证据，不能现在恢复资格。没有实际得到或认证的修正候选。本轮不扩展匹配搜索。
4. **哪些可用于统一Gate？** SHA/坐标/图像身份、可见Ring边界、深度独立RGB几何、拟合/额外留出分离、覆盖/退化/无先验秩、受限修正与HERO仅辅助的接口和四状态语义可作为统一流程候选。具体阈值、matcher缺失策略与跨匹配器一致性尚需PM/研究者审核；**v0.1不自动成为所有组正式冻结标准**。

## 核心图

- [Figure 1：五相机Ring验证](figures/Figure1_Ring_validation.png)
- [Figure 2：全部九对真实匹配及额外留出](figures/Figure2_real_matching_geometry.png)
- [Figure 3：原始HERO三维投影](figures/Figure3_original_HERO_projection.png)

完整失败及工程修复记录见[FAILURE_LEDGER](FAILURE_LEDGER.md)；[统一流程候选](CAMERA_GATE_PROTOCOL_v0.1.md)；[复现说明](REPRODUCE.md)；[资格表](CAMERA_QUALIFICATION.csv)。未删除失败、未扩展来源、未调阈值或评价规则制造PASS。
