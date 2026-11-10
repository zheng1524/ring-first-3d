"""Generate reports from frozen predictions and independent evaluation; no fitting."""
from common import *
import collections,subprocess

def mdtable(rows,keys):
 def fmt(x):
  if x is None:return 'NOT_EVALUABLE'
  if isinstance(x,float):return '%.6f'%x
  return str(x).replace('|','/')
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(fmt(r.get(k))for k in keys)+' |'for r in rows)+'\n'

def write(name,s):(R/name).write_text(s,encoding='utf-8')

def main():
 reg=load(R/'metrics/REGISTRATION_COMPARISON.json');sift=load(R/'metrics/SIFT_GEOMETRIC_EVALUATION.json');h=load(R/'metrics/HERO_AGGREGATE_FIXED_DENOMINATOR.json');f=load(R/'results/CROSS_A5_FINAL.json');neg=load(R/'results/NEGATIVE_A5_FINAL.json');integ=load(R/'provenance/FINAL_INTEGRITY_AUDIT.json');counts=load(R/'metrics/EXPORT_COUNTS.json');depth=load(R/'metrics/RING_HERO_DEPTH_DIAGNOSTIC.json');vv=load(R/'config/VIEWS.json');coll=load(R/'metrics/HERO_CAD_INTERIOR_SAMPLE_AUDIT.json')
 regtable=mdtable([a for a in reg if a['scope']=='CROSS'],['method','FIT_N','FIT_IoU','HOLDOUT_N','HOLDOUT_IoU','HOLDOUT_worst_IoU','HOLDOUT_contour_px','FIT_Ring_boundary_px','HOLDOUT_Ring_boundary_px','center_displacement_mm','unsigned_Ring_normal_tilt_deg'])
 featuretable=mdtable([a|dict(reproj_N=a['reprojection_px']['N'],reproj_MAE_px=a['reprojection_px']['MAE'],reproj_p95_px=a['reprojection_px']['p95'],reproj_max_px=a['reprojection_px']['maximum'],epi_MAE_px=a['epipolar_px']['MAE'],epi_p95_px=a['epipolar_px']['p95'])for a in sift if a['scope']=='CROSS'and a['method']in ['A0_HISTORICAL_FULL_LightGlue','A0_HISTORICAL_FULL_RoMa','A1','A2','A3','A4','A5']],['method','role','normalized_robust_feature_loss','epi_MAE_px','epi_p95_px','reproj_N','reproj_MAE_px','reproj_p95_px','reproj_max_px'])
 audit='''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1个物理组G01、1对视频004/005；68个计划视角；另1个004同视频负对照 |
| 本算法独立成功 | 1/1视频对产生019自身的共享刚体候选；68/68图像、Mask、相机与Ring弧证据可读；数值输出不等于物理配准正确 |
| 本算法失败 | 主候选无数值NaN；可靠融合资格未通过。005的46/55帧无既有原生HERO深度，辅助深度指标为NOT_AVAILABLE，不补造 |
| 历史测量值回退 | 0；A0为明确命名的历史对照，未替代019输出 |
| 失败组及具体原因 | 仅G01；留出不优于历史RoMa、残留HERO矛盾与微小CAD内部样本；见FAILURE_LEDGER.md与逐帧CSV |
| 最终统计样本 | 跨视频52FIT+3HOLDOUT，全部55目标视角；HERO为13个004与8个005可信子集，Ring深度22来源；分别声明分母 |
| 是否使用GT选择算法 | 否；没有读取Blender/尺寸GT。预测先冻结，随后才建立HOLDOUT特征与评价；provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json |
'''
 conclusion='''019完成了Ring降维、双法向规范360°搜索、真实SIFT公制地标、共享视频级PyTorch3D精修、全部计划视角评价、同视频负对照及独立Ring深度诊断。**结果为有用的研究候选，但不优于最强历史对照，也未获得可信融合认证。**

A5在005留出上的平均IoU为0.882843，优于Ring规范ψ=0的0.833308和A4的0.870460，低于历史LightGlue的0.889585及RoMa的0.893435；3个留出均低于RoMa。配准改善存在，但不能声称本轮核心联合方法全面胜过历史方法。

实际最终目标分量为Polyp 0.003606、Ring 0.037803、加权SIFT 0.102498、加权先验0.000774。加权SIFT值约为Polyp项的28.4倍，且A3与A4落在相同yaw；这提示当前概率轮廓/鲁棒特征归一口径并未实现数值均衡，不能假定联合约束自动优于每项。数值大小不是梯度大小或唯一因果机制的证明；本轮未用留出结果事后改权重。
'''
 answers='''1. **是否发现历史遗漏的大角度？** 完整搜索两种法向规范各72个角度，独立支持约270°，但历史已有约−90°候选；不是首次发现该大角度。360°搜索避免狭窄初值限制，而非制造新发现。
2. **息肉几何是否能定向？** 只能提供弱至中等候选。A1为278.636°、A2为279.590°，偏离SIFT/联合270.439°约8–9°。冻结主体核心在Ring平面的投影较短，局部HERO中心受可见范围偏差影响，不能当完整头部真中心。
3. **SIFT有独立证据吗？** 有：153个至少3视角公制地标、196个FIT跨视频RANSAC帧对、34/52帧PnP成功。147地标仅来自背景，4仅Polyp、2混合；方向证据主要来自静态背景。尺度来自冻结相机，不来自HERO/GT。保留长尾极线残差，不等于相机完全认证。
4. **联合是否优于历史？** 优于Ring规范、纯yaw和A4初始，但未超过历史RoMa/LG的总体留出轮廓与SIFT重投影。不能选择性忽略A0。
5. **整段视频能同时解释吗？** 55个005帧共享一个变换，全部保留评价。A5 FIT/HOLDOUT IoU为0.883990/0.882843，最差留出0.871657；有稳定的近似解释，但残留柄部缺失和系统误差，不是完美匹配。
6. **是否有新Ring冲突？** A5中心偏移0.277755mm、无向法向倾斜2.353017°。FIT Ring弧误差从1.421309降至1.298087px，留出1.302292→1.292724px，改善较小且非处处改善。body/CAD完全冻结，二者关系未改变；005 TRUSTED表面采样仍有1个新增CAD内部引用顶点，不能宣称无碰撞。采样不是精确三角相交认证。
7. **同视频负对照稳定吗？** 最终平移0.016857mm、旋转0.270117°，yaw约−0.244°，小而非零。只有3/80次候选被接受；FIT IoU反而从恒等的0.917746降至0.914633，留出0.905361→0.905458。反映目标分量存在权衡，不能叫严格零漂移或独立物理真值认证。
8. **Ring HERO可作全图偏差标定吗？** 22/22原生来源有有限Ring深度，但0/22通过冻结稳定性检验；扇区中位残差跨度0.947–5.160mm，不支持来源级统一偏差。仅做Ring不相交扇区偏差诊断，未保存/采用全Polyp校正，也无新HERO推理。
9. **HERO关系实质改善吗？** 相对于“原生视频坐标直接重叠”的H0，H1跨视频已知投影的轴向差MAE由1.768095降到0.867141mm，固定源—目标观测分母的±0.5mm支持率24.893%→28.917%。前方分歧代理反而14.319%→22.003%，不能只报告MAE；更深曲面保留遮挡解释。H0不是历史最佳配准，故这不能证明优于历史RoMa的三维结果。
10. **能可信融合了吗？** 尚不能。本轮只输出共同坐标候选及原曲面诊断叠加；残留原生深度矛盾、局部异常结构和弱Polyp纹理约束未解决。可以人工审阅此候选，不能自动进入融合或修改主线。
'''
 method='''# 019 方法与输入实现审计

冻结输入：004沿用018实际8FIT+5HOLDOUT；005使用014全部55份相机/RGB/Mask，恢复`EXISTING_VIEWS`/`DERIVED_VIEWS`中的原生c2w，并逐项验证等于`ALL_VIEWS.T_original`，**排除014已叠加的跨视频修正**。输入保持条件资格；INSUFFICIENT_EVIDENCE等历史标签不被升级。005逐帧解码验证55/55真实像素；004读取018原帧/JPEG95完整链，声明帧号与实际帧号差异保留。8个HOLDOUT在搜索前固定；018主体和历史相机祖先可能使用部分评价图像，故仅本轮更新/选择独立，不宣称端到端完全独立。

R10实体CAD中心线半径5.6mm、线材半径.6mm。DXY只读调用`ring_component.recover`提取真实内/外弧，68/68输出有效；不调用DXY最终测量来填补019结果。Ring规范为中心0、法向±Z，负法向使用det=+1的180°旋转而非镜像。`X004=R X005+t`，列向量，OpenCV c2w，单位mm，尺度1。

| 原定组件 | 实际实现与代码 |
| --- | --- |
| 共享视频级SE(3)，冻结主体/相机 | `renderer019.py:FrozenRenderer`、`objective019.py:PoseObjective`；仅6个q可微，原K/c2w、主体顶点和HERO均固定 |
| 官方PyTorch3D | `Meshes/MeshRasterizer/SoftSilhouetteShader/cameras_from_opencv_projection/se3_exp_map`；沿用018 Ring-Aware A/B/C/D及detach深度次序；未实现新光栅器 |
| 公制与像素映射 | 原640×360评价；优化180×320，沿用验证过的像素中心映射，固定018归一化；O3D/P3D轴向深度p95≤7.63e−6mm（3帧门禁） |
| Ring yaw不提供信息 | `canonical_ring_camera`消除离散CAD绕轴锯齿；仍渲染实体CAD；三帧pure-yaw梯度0，loss浮动≤1.94e−7 |
| 多视角权重 | Mask/Ring按原生方向范围的4等宽分区均衡总权重；004方向跨度54.47°、00595.44°，不是全周相机覆盖；SIFT按有效帧/帧对归一，并未用方向权重 |
| 真实SIFT及地标 | `features019.py`：6000/ratio.72/双向、独立RGB-MAGSAC1.5px；Ring膨胀2px、高光/暗部/边框排除；至少3帧、已知相机4px、重投影<2px、视差>.5°；固定相机三角化+3D点鲁棒精修；不读取HERO |
| SIFT候选 | OpenCV EPNP-RANSAC+LM，成功至少6内点；正深度检查和空间覆盖独立记录；Sigma为unit-pixel几何代理，没有伪称已校准，也未用于白化损失 |
| 全360°与联合 | `search019.py`：两规范×72角，对所有52FIT帧；连续标量精修±5°；几何只提候选，SIFT/历史候选分别标记，不算术平均 |
| A1/A3独立范围 | `refine019.py:correct_scope`在读任何HOLDOUT前纠正A1仅轮廓grid/continuous、A3仅feature/grid/PnP；旧共享候选池选择另存RAW_POOL，A4不变 |
| 精修目标 | `Lpose=Lpolyp+Lring+.05Lfeature+.01mean(q²)`；`Lsearch=Lpolyp+.05Lfeature`。q按.6mm/5°归一，H=exp(qscale)Hseed；固定分母/鲁棒Huber归一3px |
| Ring损失 | 正Ring与已知非Polyp背景概率MSE各半，加.25×真实DXY弧上的(alpha−.5)²；**无量纲**。独立O3D可见内/外边界距离才是px；JSON旧`ring_sigma_px=3`未使用，不冒称像素距离项 |
| 80候选/3初值 | Adam.01，8级回溯；左平移≤1.2mm、旋转≤10°，FIT目标不增容差1e−9、Ring相对初值最多+.001；拒绝恢复q+Adam，全部终点保留 |
| 初值选取偏差 | 预注册文字称“局部极小”，实际是分数排序+20°角距离NMS，**非严格局部极小枚举**。不补写预注册，也不宣称全局唯一最优 |
| 正深度门禁偏差 | 原协议描述候选相机在前，实际迭代未单独对全部body顶点作硬cheirality拒绝；特征含behind常数惩罚，最终68帧另查全部body正深度。最终通过不能追认所有中间候选都通过 |
| 特征Ring可见性 | 训练用真实Ring Mask排除特征；未加入逐点CAD硬可见性筛选。预测冻结后全部成功PnP观测独立CAD检查为0个Ring遮挡点，未回流筛选 |
| 性能兼容修复 | 原hardRing bin0改官方bin32，104帧—位姿组合mask相等/z差为0，并验证3个loss/gradient；保留原代码/冻结证据。数值目标未换，未少用任何FIT像素 |
| 中断恢复 | CROSS seed0从第40步q+Adam恢复；保存RESUME说明，未声称全RNG bitwise无缝；FINAL.seconds仅恢复段，不能冒充全部任务耗时 |
| 数值抖动限制 | soft Ring bin32重入梯度相对差最大8.32e−5；负对照有约1e−6前向浮动，大于接受容差1e−9。77/80和3/80为实际执行记录，不能视为高精度严格单调证明；未据留出重调 |
| P1/H2 | `ring_depth019.py`固定材料/纹理/CAD与扇区检验，0稳定偏差；`hero_diagnosis019.py`在原native局部坐标比较同视频，避免共同H制造虚假内部改善；H2条件未触发 |

HERO的“TRUSTED”是017/018可解释规则标签，不是物理GT。004复用13份既有标签，005在8份原始来源上复用同一清理规则生成派生标签；`reused=False`表示本轮重建标签，不是重新HERO推理。005另1份new_r04仅有原生深度，未伪造TRUSTED曲面；其他46帧无原生HERO，可正常参与RGB/Mask配准。

原生子集NPZ保留完整原始V数组及子集F。初次交付诊断错误地把不被F引用的旧顶点计入显示范围和CAD内部计数，已纠正为**仅引用顶点+实际面片中心**；原计数保存在`provenance/UNREFERENCED_VERTEX_DIAGNOSTIC_SUPERSEDED.json`。没有删掉任何TRUSTED面片，也未改变配准。GLB仅紧凑重编号未引用顶点，原V/F/面ID保存在NPZ。

HOLDOUT SIFT在预测冻结后才提取，只供评价。所有三维深度比较使用轴向Z，正确投影、CAD首次表面与自遮挡区分；比目标表面更深不算可靠自由空间错误；前方分歧仅为含相机/HERO误差的几何代理。没有GT测量或ICP选取。H0指未统一原生坐标，非历史最佳配准。
'''
 write('METHOD_AND_INPUT_AUDIT.md',method)
 summary='# 019 技术报告摘要\n\n'+conclusion+'\n## 核心结果\n\n'+regtable+'\n目标表中IoU无单位、轮廓/Ring为640×360原像素、偏移为mm、倾角为deg；FIT52/HOLDOUT3。Ring边界为观测弧到对应CAD内/外轮廓的最近距离，非完整不可见圆环误差。\n\n## 十项研究回答\n\n'+answers+'\n## 实现与完成范围\n\n'+'''完成1/1物理组、1/1跨视频对及1个同视频负对照。68/68计划视角保留；A0全部8个历史矩阵包括5个旧GICP失败均重新评价；A1–A5结果保留。3×80次CROSS及3×80次NEGATIVE候选，主候选分别接受77次、3次。完整算法逐项审计、偏差与代码位置见[METHOD_AND_INPUT_AUDIT.md](METHOD_AND_INPUT_AUDIT.md)。

155项上游资产/配置/预测哈希核对通过，原RGB/Mask/相机、018主体、Ring、HERO未改。源码执行证据在`provenance`，性能修复和中断恢复单独保存。没有基于GT、HOLDOUT更改算法或选最后模型。

## 核心图与可复现产物

- [Fig1 双锚点](figures/Fig1_Dual_Anchors.png)、[Fig2 真实SIFT和地标](figures/Fig2_SIFT_Landmarks.png)、[Fig3 全角度搜索](figures/Fig3_Full360_Search.png)。
- [Fig4 多视角真实重投影](figures/Fig4_Real_Multiview_Reprojection.png)、[Fig5 三维共同坐标诊断](figures/Fig5_Unified_Scene_NOT_FUSION.png)、[Fig6 Ring深度](figures/Fig6_Ring_HERO_Depth.png)。
- `derived/T004_from005.json`是真正的刚体变换；`derived/VIDEO005_CAMERAS_IN004.json`为全部55个派生相机。大GLB/原生曲面/深度/优化状态本地索引见[RESULT_INDEX.md](RESULT_INDEX.md)。
- [REPRODUCE.md](REPRODUCE.md)提供分阶段命令；[FAILURE_LEDGER.md](FAILURE_LEDGER.md)包含逐来源Ring失败、无SIFT帧、历史失败与数值限制。

## 科研决策

保留SIFT多帧地标、Ring规范360°搜索、共享刚体与独立留出评价。当前候选尚不建议自动用于可信融合；主体误差与原生HERO误差仍需区分。任务已停止，不开展逐帧相机优化、主体变形、曲面拼接或重复HERO推理，等待人工审阅。

## 固定审计表

'''+audit
 write('TECHNICAL_REPORT_SUMMARY.md',summary)
 write('TECHNICAL_REPORT.md',summary+'\n## SIFT独立评价\n\n'+featuretable+'\n相同固定观测、3px归一Huber；像素统计包括长尾。PnP匹配有限，HOLDOUT只有17个真实地标对应；不能夸大显著性。\n\n## HERO固定分母评价\n\n'+mdtable(h,['condition','relationship','ordered_source_target_pairs','fixed_source_target_observation_denominator','known_N','supported_N_fraction_fixed_denominator','front_disagreement_proxy_N_fraction_fixed_denominator','behind_observed_surface_N_fraction_fixed_denominator','known_observation_weighted_MAE_mm'])+'\n分母为有向来源—目标对上的固定源观测重复计数，不是独立像素数或唯一表面积；共21个来源。同视频数值严格一致；跨视频支持有所增加而前方分歧也增加，不以降低MAE宣称全部矛盾消除。面积表为逐源原面中心的支持代理，不能相加为物理唯一新增面积。\n\n## 同视频负对照全部结果\n\n'+mdtable([x for x in reg if x['scope']=='NEGATIVE'],['method','FIT_N','FIT_IoU','HOLDOUT_N','HOLDOUT_IoU','center_displacement_mm','unsigned_Ring_normal_tilt_deg'])+'\n全部6个优化初值与终点见results；特征、轮廓与Ring目标可能相互权衡。\n\n## 实现忠实性与限制\n\n'+method)
 # Per-source failures, empty observation frames, and stopped historical methods remain explicit.
 epi={a['b']for a in load(R/'features/CROSS_EPI.json')};pnp={a['target']for a in load(R/'features/CROSS_PNP.json')if a['success']};missing=[dict(view=v['id'],SIFT_epi_available=v['id']in epi,PnP_available=v['id']in pnp,handling='Mask and Ring retained; absent feature channel not fabricated')for v in vv if v['video']=='005'and v['role']=='FIT'and(v['id']not in epi or v['id']not in pnp)];save('metrics/FEATURE_EVIDENCE_GAPS.json',missing);table('metrics/FEATURE_EVIDENCE_GAPS.csv',missing)
 ringrows=[dict(view=a['view'],video=a['video'],reliable_N=a['reliable_N'],MAD_mm=a['MAD_mm'],sector_spread_mm=a['sector_median_spread_mm'],Ring_held_before_MAE=a['disjoint_Ring_before_MAE_mm'],Ring_held_after_MAE=a['disjoint_Ring_after_MAE_mm'],status='REJECT_SOURCE_BIAS_TRIAL')for a in depth['rows']]
 failures='''# 019 失败与限制台账

所有失败保留，不改门槛造PASS。当前研究候选数值成功≠已认证配准/融合成功。

| 项目 | 具体原因与证据 | 处理 |
| --- | --- | --- |
| 未胜过历史基线 | A5 HOLDOUT0.882843，RoMa0.893435；3/3留出均更差；`metrics/PAIRED_FRAME_COMPARISON.csv` | 保留A0与A5，不替换输出、不挑帧 |
| 弱形状方向 | model核心到Ring法向轴的投影短、HERO局部可见中心偏；A1/A2与SIFT相差8–9° | 多候选，不算术平均/唯一真方向 |
| SIFT证据局限 | 147/153背景地标；FIT34/52PnP，HOLD17地标对应；极线p95有长尾 | 不冒称丰富Polyp纹理或充分认证 |
| 初始cv2数值失败 | 退化RGB帧对触发USAC断言；features.log保留 | 捕获cv2.error为无F/无内点，未补对应或放宽阈值；features_resume.log |
| 同视频非零漂移 | t0.016857mm、R0.270117°，3/80接受，FIT IoU轻微下降 | 如实记录分量权衡，不说零漂移 |
| Ring深度不稳定 | 22/22未通过扇区/MAD/留出稳定性；下表逐来源 | 原生深度不变，无来源级全图校正 |
| HERO仍不一致 | H1 known MAE0.867141mm；固定分母前方分歧代理22.003% | 不把自遮挡当自由空间真错误，不融合 |
| 小量CAD内部样本 | 005 growth_r03新增1个引用顶点深入CAD超过.02mm；面中心0，完整三角相交未认证 | 保留原面、不调相机掩盖、不声称无碰撞 |
| 原主体误差 | 冻结body不完全符合005全Mask，柄部仍缺失 | 不开放body自由度补偿配准 |
| HERO不可用帧 | 00546/55无原生深度，但camera/RGB/Mask完整 | 完整参加主配准；深度辅助项NOT_AVAILABLE |
| 准独立留出 | 本轮HOLDOUT不进入选择；018/014祖先可接触部分图像 | 标明更新阶段留出，不说端到端独立 |
| NMS实现偏差 | 文字预注册“局部极小”，实际score+20°NMS | 原证据保留，报告偏差，不扩大本轮搜索 |
| 未独立门禁所有候选正深度 | 实际只罚特征behind，不是全body候选硬约束 | 最终68帧另测正深度，不能追认所有提案 |
| 软Ring数值抖动 | 约1e−6的重复前向浮动>1e−9接受容差 | 小幅接受/拒绝不作严格单调证据，未留出后调参 |
| 性能修复/中断 | naive硬Ring慢，停自身进程、40步q/Adam恢复 | equivalence104组+3梯度通过；秒数仅恢复段，不伪造全程耗时 |
| 子集NPZ无引用V诊断 | 首次显示范围/内部计数误含F未引用顶点 | 仅诊断改为真实引用几何，旧计数另存，预测完全不变 |
| H2未执行 | 内部相对相机变化max1.42e−14，仅坐标规范统一 | 按任务条件不重复HERO；不包装新预测 |

## 全部Ring深度来源：均未通过来源级标定

'''+mdtable(ringrows,['view','video','reliable_N','MAD_mm','sector_spread_mm','Ring_held_before_MAE','Ring_held_after_MAE','status'])+'\n## 005 FIT的特征缺口（帧仍保留）\n\n'+mdtable(missing,['view','SIFT_epi_available','PnP_available','handling'])+'\n## 历史候选（包括旧失败）\n\n'+mdtable(load(R/'config/HISTORICAL_CANDIDATES.json'),['tag','status'])+'\n## 全部帧证据\n\n`metrics/ALL_FRAME_METRICS.csv`包含815个方法—帧评价记录；`evaluation/per_view`本地保存逐方法帧JSON，`figures/details`提供全部55个005帧的统一投影，不删差帧。\n'
 write('FAILURE_LEDGER.md',failures)
 write('REPRODUCE.md','''# 019 复现

工作树：`/home/liu/ring_first_3d_e4_sdf_localization`；分支`exp/TASK-E4-RING-POLYP-REGISTRATION-019`。

解释器：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`；实际Python3.12、PyTorch2.7.1cu128；官方PyTorch3D本地commit `e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31`。同一已安装OpenCV/Open3D/SciPy环境，通过`common.py`设置原本地依赖路径。不下载新模型/框架。硬件RTX3060Laptop6GiB，单GPU串行。

所有命令从工作树根目录执行，以下`$PY`仅为任务变量，`$TASK019`为本任务目录。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK019=experiments/TASK-E4-RING-POLYP-REGISTRATION-019
```

完整来源、精确输入SHA和原路径：`INPUT_MANIFEST_COMPLETE.json/csv`。RGB/Mask/视频/原生HERO/018主体/原始相机需在对应本地存储存在；Git仓库不含大文件。请在独立实验副本运行准备和训练阶段，勿在已冻结目录覆盖结果。

```bash
$PY -B $TASK019/code/prepare019.py
$PY -B $TASK019/code/frame019.py
$PY -B $TASK019/code/ring019.py
$PY -B $TASK019/code/clean_sources019.py
$PY -B $TASK019/code/features019.py
```

**预注册冻结注意**：`prepare019.py`是初始准备器，随后本轮在搜索前冻结了精确004前4→后4负对照与原生方向4分区。其最终`config/VIEWS.json`、`config/NEGATIVE_SPLIT.json`、`01_PROTOCOL.md`和`provenance/BEFORE_SEARCH_FREEZE.json`是权威输入。独立重跑在prepare后、features之前，从已交付原目录执行`restore_frozen_config019.py --destination /绝对路径/独立副本`恢复最终配置；它只重定位任务内缓存路径，保持原相机/方向/分割/划分完全不变，并拒绝写入原冻结目录或已有冻结预测的副本。不要把prepare的初始默认negative排序当最终协议。`frame019.py`只核查并产出证据，不修改原相机。SIFT数值退化帧对保持无F。

```bash
$PY -B $TASK019/code/gate019.py
$PY -B $TASK019/code/geometry019.py
$PY -B $TASK019/code/search019.py
$PY -B $TASK019/code/performance_gate019.py
$PY -B $TASK019/code/refine019.py
```

`refine019.py`已有FINAL则跳过，已有ITER.pt则恢复q+Adam。严格重跑请使用独立副本、独立输出，不能把恢复段秒数作为全训练耗时。最终选模必须在任何HOLDOUT提取前冻结，禁止后续GT或HOLDOUT回流。

下列为**纯冻结后评价/可视化**（不更新模型），也是此次续执行实际完成的后处理链：

```bash
$PY -B $TASK019/code/evaluate019.py
$PY -B $TASK019/code/ring_depth019.py
$PY -B $TASK019/code/hero_diagnosis019.py
$PY -B $TASK019/code/feature_evaluate019.py
$PY -B $TASK019/code/stability019.py
$PY -B $TASK019/code/deliver019.py
$PY -B $TASK019/code/audit_delivery019.py
$PY -B $TASK019/code/reports019.py
$PY -B $TASK019/code/verify_delivery019.py
```

已有全部缓存时可只重跑`deliver019.py`与`reports019.py`恢复核心图和文字；`audit_delivery019.py`核对原资产和冻结结果SHA，未通过应停止交付。`stability019.py`只复用搜索缓存做预定FIT子集yaw敏感性，不做留出驱动新优化。

尺寸定义：计算与NPZ/相机均为毫米，GLB仅按规范导出米(.001)，不是重新估计尺度。SIFT像素对应原640×360；HERO原生352×640。派生HERO只变换坐标，不插值或补面，不构成融合。
''')
 write('RESULT_INDEX.md',f'''# 019 结果索引

本地根目录：`{R}`。

| 产物 | 位置 | 含义 |
| --- | --- | --- |
| 简洁结论 | TECHNICAL_REPORT_SUMMARY.md | 十项研究回答及固定审计表 |
| 完整指标与方法 | TECHNICAL_REPORT.md、METHOD_AND_INPUT_AUDIT.md | 全部A0–A5、负对照与实现偏差 |
| 完整输入68行 | INPUT_MANIFEST_COMPLETE.json/csv | 文件SHA、相机、图像身份、HERO与SIFT可用性 |
| 真正注册矩阵 | derived/T004_from005.json | R,t和逆，mm，尺度1，候选未认证 |
| 全005派生相机 | derived/VIDEO005_CAMERAS_IN004.json | 55个c2w，原相机未修改 |
| 所有候选及竞争终点 | results/、metrics/*SEARCH* | 原始法向规范、144角度、3个SE3终点 |
| 优化状态 | refinement/CROSS或NEGATIVE/seed0..2/ITER_*.pt | q+Adam，不是网络训练权重 |
| 完整日志 | *.log、refinement/*/*/HISTORY.json | 断点、接受/拒绝、数值异常 |
| 全逐帧评价 | metrics/ALL_FRAME_METRICS.csv/json | 815个方法—帧，目标00555帧全部保留 |
| 原分辨率预测 | evaluation/CROSS/方法/帧.npz | 640×360 body/Ring轴向depth与Mask |
| 特征与匹配 | features/、matches/、landmarks/ | 全真实feature ID、UV、RANSAC/地标轨迹 |
| 核心6图 | figures/Fig1..Fig6*.png | 实际数据，黑色实体CAD，mm |
| 全005视角详细图 | figures/details/All005_Projection_01..08.png | 全55目标视角而非挑选成功图 |
| 共同坐标诊断GLB | derived/G01_SHARED_SCENE_DIAGNOSTIC_NOT_FUSION.glb | 一份Ring、018body、21HERO独立组件、68个camera；非融合 |
| 派生005曲面 | derived/HERO_in004/*.npz | 8个TRUSTED来源，原F/面ID保留，刚体坐标副本 |
| Ring深度诊断 | ring_depth/*.npz | 22份原生/HERO/CAD/选择区域/残差；无被采用全图校正 |
| H0/H1诊断 | metrics/HERO_* | 固定分母、遮挡/未知、前方代理分歧 |
| 哈希与预测冻结 | provenance/ | 搜索前/精修前/留出前/最终完整性 |

所有大二进制及原数据保留本地，不上传视频/模型权重。`assets_index/LOCAL_RESULTS.json`提供本轮大文件路径、字节与SHA。Git提交源码、最终配置、指标、变换、精选核心图和小型真实匹配证据；完整匹配缓存依照源码及输入SHA复现。

无物理配准GT，绝对姿态误差/MARE/测量MAE/p95/max为NOT_EVALUABLE。图像轮廓与SIFT残差并非物理精度真值。历史A0涉及旧跨视频点云候选，仅对照，019生成不读取历史尺寸值回退。
''')
 # Local large-file ledger is deliberately separate from Git staging.
 big=[]
 for folder in ['inputs','hero_fit','derived','evaluation','ring_depth','refinement','features','matches','landmarks']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file()and p.suffix in ['.npz','.pt','.glb','.ply']:big.append(asset(p))
 save('assets_index/LOCAL_RESULTS.json',big)
 # Actual installed/source versions, never secrets or environment credentials.
 import platform,torch,scipy,open3d
 save('assets_index/RUNTIME_VERSIONS.json',dict(Python=platform.python_version(),torch=torch.__version__,CUDA_runtime=torch.version.cuda,OpenCV=cv2.__version__,SciPy=scipy.__version__,Open3D=open3d.__version__,GPU=torch.cuda.get_device_name(0),PyTorch3D_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=str(REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runtime/pytorch3d'),text=True).strip()))
 save('provenance/FINAL_SOURCE_MANIFEST.json',dict(code=[asset(p)for p in sorted((R/'code').glob('*.py'))],role='final delivered code; historical pre-search/pre-refine versions separately preserved; new delivery scripts never fit'))
 print('REPORTS_COMPLETE',flush=True)
if __name__=='__main__':main()
