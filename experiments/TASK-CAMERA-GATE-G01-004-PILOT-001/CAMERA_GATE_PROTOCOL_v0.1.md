# Camera Gate Protocol v0.1 — 候选规范，待PM与研究者审核

本轮验证范围仅G01_004五份相机。以下接口与语义可供未来各组使用，**没有自动推广本轮阈值为所有物理组正式标准**。禁止按组名、GT、通过率或重建效果调整规则。

## 输入接口

每个camera record包含：`camera_id / physical_group / video_id / RGB_path+SHA256 / Mask_path+SHA256 / image_size / pixel_center_convention / K / distortion_identity / c2w / unit / world_frame / upstream_identity / prior_qualification`。

CAD record包含不可修改的`mesh_path+SHA256 / CAD_world_frame / unit`。匹配record包含`pair_id / A / B / matcher / p / q / original_match_id / image_hashes / resize_crop_affine / origin_cached_or_CPU / confidence_semantics / fit_held_partition`。原RGB匹配点始终不是物理对应GT，不使用匹配器点图或预测深度补造几何。

先核对图像身份、像素中心、尺寸、K缩放/裁剪、c2w方向和右手正交性、世界坐标及公制单位。无法核验返回`INSUFFICIENT_EVIDENCE`，不得猜测跨视频变换。缓存帧键绑定与原视频逐帧身份分别记录。

HERO record可选，必须是已审计原始XYZ/原始点面身份和原始source K/c2w；只在前两项冻结之后作辅助，不用融合Mesh、历史配准结果或HERO距离决定相机资格。

## 顺序与输出

1. 冻结输入SHA、配对、评价规则、拟合参考、额外留出、匹配器优先级和修正预算。
2. Test1以原CAD射线投影对真实Ring Mask计算可观察边界误差，保存未剔除统计、Polyp遮挡/裁剪排除理由、质心/形状诊断；独立声明Ring的连续旋转对称性与可能离散分支。
3. Test2使用真实RGB匹配，记录全部可用对应与独立RGB几何相容子集。相机预测F评分不得用待测pose先筛掉高误差对应；同时报告原始/拟合/留出误差、内点数比例、双图覆盖、低视差、近共面、正深度和其他不可观测性。
4. 原始完整结果先保存并哈希。只有明确FIT侧几何误差、充分对应和无先验局部可观测性才允许一次冻结边界内的修正；Ring与K固定，候选另存，额外留出仅评分，不能选择初值/阈值/迭代结果。
5. Test3读取原始HERO，对其他真实RGB/Polyp Mask投影并执行真实CAD遮挡；固定目标分母，保留未覆盖/无匹配/NaN。不得借辅助结果反向使相机过关。
6. 输出`Ring_metrics / image_geometry / observability / status / reasons / original_pose_identity / optional_corrected_candidate / formal_pose_updated=false`及三项可视化。全部候选保留。

## 本轮冻结数值与公式

机器可读权威值：[config/protocol.json](config/protocol.json)，正式运行前SHA见[BEFORE_FORMAL_RUN](config/BEFORE_FORMAL_RUN.json)。本文说明不替换该JSON。

- G01_004只用ref03/ref08拟合约束，ref13整对为本轮额外检查；原3互检，新增各需三条指定参考关系。不能只获得两拟合关系就跳过ref13。此留出独立于本轮pose拟合，未声称历史相机/匹配器完全没见过该图像。
- 整数像素中心、640×360，`Xc=(Xw−C)R`，c2w的R将相机方向转到世界，`u=K Xc/Z`；Z、CAD、XYZ为mm。跨图实际射线为`R K⁻¹[u,v,1]`，不能把Z当单位射线长度。
- Ring双向可观察轮廓至少各100像素；距Polyp≤2px和图边2px排除，MAE≤3px、p95≤6px。MAE>6px或p95>12px才是本轮明确矛盾代理。原始未剔除轮廓误差仍输出；部分遮挡的质心/轴比/IoU仅描述，不单独认证pose。
- CPU SIFT参数继承8000特征、contrast .01、双向ratio .72。优先复用缓存。固定方法顺序SIFT→LightGlue→MASt3R→RoMa；仅第一种在RGB-only F计数/覆盖充分的方法用于主Gate，**不会遇到pose不通过就继续挑下一种**；其他方法全部报告。缓存检测Mask策略差异作为限制记录。本轮额外5对只补SIFT，不作新神经匹配推理。
- 语义相同、非Ring、非高光（min RGB<245）、图内点；canonical配对方向下`(floor(p.x/16)+3 floor(q.y/16)) mod 5=0`为空间留出。seed0、2px RANSAC、confidence .999、2000上限，仅在非留出拟合F；分别验证F相容fit≥12/held≥8、双图各≥4个32px格、凸包≥1%图像。低数量/覆盖返回不足。
- 相机F由冻结相对位姿给出。平方根Sampson残差为`|qᵀFp| / sqrt(||(Fp)xy||²+||(Fᵀq)xy||²)`，单位px。fit/held中位≤3、p95≤6、≤2px比例≥70%，射线中位视差≥.5°，三角化正深度≥95%。独立F相容只是观测代理，不是物理对应真值。全可用点统计同时输出。
- Homography相容比例≥90%或视差不足作退化标记。Ring加匹配的Jacobian必须不含先验，列按5°/.5mm标准化，相对奇异值门槛1e-3；单Ring已知yaw零空间必须显式保留。局部满秩不解决共同参考偏差、全局离散对称分支或K/畸变错误；近共面需联合其他条件解释，不能仅据优化器输出认证。
- 相机通过必须Ring通过、**所有指定外部参考关系充分且通过**、数据约束局部分支满秩。相机间约束只相对于冻结参考家族，不能证明绝对真实位姿。

## 四状态语义

| 状态 | 统一含义 |
| --- | --- |
| CONDITIONAL_USABLE | Ring、指定真实图像关系、覆盖和局部可观测性支持条件使用；仍非绝对相机GT |
| CORRECTION_CANDIDATE | 一次有界修正改善FIT目标≥10%，同一原/修正评价集上的Ring和全部指定关系通过、无边界接触、局部满秩；仍需进一步确认，不自动替换相机 |
| UNQUALIFIED_GEOMETRY | 有充分的明确Ring或相对于参考家族的图像几何矛盾；必须注明矛盾对象和归因限制，不能凭未通过就断言实际pose错误 |
| INSUFFICIENT_EVIDENCE | 缺对应/覆盖/留出/资格，或处于未通过但未达明确矛盾区间，或退化/归因未决；不优化制造数字，不默认为无错 |

## 一次有界修正（本轮没有触发，真实修复效能未验收）

从冻结T0初始化，用世界轴旋转向量更新朝向和世界中心平移构造SE(3)候选，原CAD和K固定。每轴界为总界/√3，保证总旋转≤5°、中心位移≤.5mm；成熟SciPy `least_squares(loss='soft_l1', max_nfev=60)`，Ring/图像/初值先验固定权重，Ring误差/3px、signed Sampson/2px，模态按√N归一，先验按5°/.5mm。无HERO残差。

明确FIT侧触发为Ring明确矛盾或充分FIT图像的中位误差≥6px/≤2px内点≤30%，并且两指定FIT参考充分、无先验局部满秩。额外留出不触发优化。所有原始/修正候选用相同数据完整评价；边界接触≥98%或留出不足不能称修复成功。最多一次，无重启、无参数搜索、无按留出选择迭代。

## 待审核问题

本轮显示匹配器方法依赖和留出稀疏可能比数值秩更限制资格。需审核70%/2px主规则、RGB-only F筛查可靠性、缓存Mask差异与跨方法一致性如何解释。不可在本轮改规则以提高通过率；未来修订必须新版本、重新预注册、独立于GT与成功率。没有跨其他组运行或把本规范升级为正式模块。
