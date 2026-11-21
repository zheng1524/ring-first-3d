"""Read frozen results, report all outcomes; never choose a pose using evaluation."""
from common import *
import collections,platform
def md(rows,keys):
 def f(x):return 'NOT_EVALUABLE'if x is None else('%.6f'%x if isinstance(x,float)else str(x).replace('|','/'))
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(f(r.get(k))for k in keys)+' |'for r in rows)+'\n'
def write(name,text):(R/name).write_text(text,encoding='utf8')
def main():
 while not(R/'runtime/FIGURES_COMPLETE.json').exists()or not(R/'metrics/HERO_RING_SAMPLE_COLLISION_AUDIT.json').exists():time.sleep(5)
 reg=load(R/'metrics/REGISTRATION_COMPARISON.json');m={x['method']:x for x in reg};sf=load(R/'metrics/SYMMETRIC_SIFT_EVALUATION.json');sh={(a['method'],a['role']):a for a in sf};hero=load(R/'metrics/HERO_INDEPENDENT_AGGREGATE.json');hh={x['method']:x for x in hero};r0,r3,r4=m['R0'],m['R3'],m['R4'];neg=load(R/'metrics/NEGATIVE_CONTROL.json');out=[]
 for name in ['R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER','R4','NEGATIVE_R3']:
  a=load(R/'results'/(name+'.json'));out.append(dict(arm=name,accepted=a['accepted'],candidate_iterations=a['iterations'],initial_objective=a['initial_loss'],final_objective=a['loss'],seconds=a['seconds'],body_in_loss=a['body_in_loss']))
 table('metrics/ACTUAL_RUN_SUMMARY.csv',out)
 material={}
 for tag in ['CROSS_004','INDEPENDENT_005']:
  x=load(R/'landmarks'/(tag+'_OBSERVATIONS.json'));c=collections.Counter()
  for t in x:
   labels=[]
   for a in t['observations']:labels.append(int(np.load(R/'features'/(a['view']+'.npz'))['region'][a['feature_id']]))
   c['all_background'if all(k==0 for k in labels)else'all_polyp'if all(k==1 for k in labels)else'mixed_or_boundary']+=1
  material[tag]=dict(c)
 save('metrics/LANDMARK_MATERIAL_AUDIT.json',material)
 core=md([m[k]for k in ['R0','R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER','R4','HISTORY_LIGHTGLUE','019_A5','NAMED_3D_DIAGNOSTIC_NOT_ADOPTED']],['method','FIT_N','FIT_IoU','HOLDOUT_N','HOLDOUT_IoU','HOLDOUT_worst_IoU','HOLDOUT_contour_px_MAE','HOLDOUT_Inner_px_MAE','HOLDOUT_Mid_px_MAE','HOLDOUT_Outer_px_MAE','HOLDOUT_Ring_M','Ring_center_mm','Ring_normal_tilt_deg'])
 st=[]
 for x in sf:
  st.append(dict(method=x['method'],role=x['role'],F=x['normalized_symmetric_F'],E=x['normalized_E'],forward_N=x['forward']['N'],forward_MAE_px=x['forward']['error_px']['MAE'],forward_median_px=x['forward']['error_px']['median'],forward_p95_px=x['forward']['error_px']['p95'],forward_max_px=x['forward']['error_px']['maximum'],reverse_N=x['reverse']['N'],reverse_MAE_px=x['reverse']['error_px']['MAE'],reverse_p95_px=x['reverse']['error_px']['p95'],reverse_max_px=x['reverse']['error_px']['maximum']))
 table('metrics/SIFT_READABLE_SUMMARY.csv',st)
 audit='''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1个物理组G01，1对视频004/005，68个计划视角；另1个004同视频负对照 |
| 本算法独立成功 | 1/1配准对象产生020自身R3候选；7条更新路线实际完成，R0是静态历史基线；数值输出不等于真实相机认证 |
| 本算法失败 | 全部目标帧保留；不稳定/没有改善的指标照常记录；无绝对配准GT，物理姿态误差为NOT_EVALUABLE |
| 历史测量值回退 | 0；完整RoMa是明确授权初值/基线，不用旧Dxy或其他预测填补结果 |
| 失败组及具体原因 | 仅G01，见FAILURE_LEDGER.md、逐帧CSV；无GT不能保证真实融合正确 |
| 最终统计样本 | 00552FIT+3HOLDOUT；反向0048FIT+5HOLDOUT；HERO限定预登记21个原生来源，不冒称55帧都有深度 |
| 是否使用GT选择算法 | 否；R0-R3与Ring消融先冻结，随后仅R4获准读取body参与其损失；全部预测冻结后才独立读取HOLDOUT与HERO评价 |
'''
 # These are descriptive observations, never a post-hoc configuration/model selector.
 intro=f'''# 020 技术报告摘要

完成Ring四通道、video005独立SIFT地标、双向2D–3D、完整RoMa初始化、R0–R4、两条Ring消融及同视频负对照。**主候选始终是事前指定的R3，不根据HOLDOUT或HERO重新挑选输出。** 本轮未变形主体/相机轨迹内部结构，未修改HERO，未使用项目GT，没有曲面融合。

R3相对RoMa的005留出IoU为 **{r0['HOLDOUT_IoU']:.6f} → {r3['HOLDOUT_IoU']:.6f}**；Inner/Outer留出平均偏差分别 **{r0['HOLDOUT_Inner_px_MAE']:.3f}/{r0['HOLDOUT_Outer_px_MAE']:.3f} → {r3['HOLDOUT_Inner_px_MAE']:.3f}/{r3['HOLDOUT_Outer_px_MAE']:.3f}px**。R3中心偏移{r3['Ring_center_mm']:.4f}mm、法向倾角{r3['Ring_normal_tilt_deg']:.4f}°；相对RoMa新增平移{r3['correction_from_RoMa_translation_mm']:.4f}mm、旋转{r3['correction_from_RoMa_rotation_deg']:.4f}°。这些是观测代理，非绝对姿态真值精度。

## 同一评价分母的完整对照

'''+core+'''
IoU无单位，曲线/轮廓为原640×360像素，平移mm，角度deg；每帧独立计算后宏平均，worst为最差留出。RingMask M是正材料/已知非Polyp背景平衡的概率MSE，不是像素距离。Mid是相关辅助证据，不是独立第三份真值。

## 十一项科研回答

'''
 def curveavg(a,role='HOLDOUT'):return(a[role+'_Inner_px_MAE']+a[role+'_Outer_px_MAE'])/2
 gg={a['arm']:a for a in load(R/'metrics/ENDPOINT_GRADIENT_RELATIONSHIPS.json')};rw=load(R/'config/PROTOCOL.json')['ring_weights'];weighted={k:rw[k]*gg['R3']['gradient_norms'][k]for k in rw};dominant=max(weighted,key=weighted.get);io_cos=gg['R3']['gradient_cosines']['I__O'];body_cos=gg['R4']['body_to_Ring_SIFT_cosine']
 ans=f'''1. **曲线是否比Mask-only有效？** R3_MASK_ONLY、R3_INNER_OUTER、R3使用完全相同SIFT和80次预算；三者留出Inner/Outer均值分别{curveavg(m['R3_MASK_ONLY']):.4f}/{curveavg(m['R3_INNER_OUTER']):.4f}/{curveavg(r3):.4f}px。请同时看SIFT、Polyp、HERO，不用一项下降称全面成功。
2. **哪个贡献最大/重复计权？** R3终点统一左切空间的加权梯度范数最大通道为{dominant}，I/O梯度余弦{io_cos:.4f}；分量与初末取舍见Fig6/JSON。这只是该终点梯度，不能直接当独立信息增益排名。固定Ring总预算1，M/I/C/O=.25/.35/.05/.35；无Mid时I/O各.375；Mask-only为1。Mid是相关辅助，未当独立统计票。系数和相同不保证不同目标的梯度强度完全相同；不把曲线改善直接称作新增独立真值。
3. **可见性正确吗？** 原DXY实际弧映射到原始Ring Mask边界；未用完整外推I/O弧监督。真实Polyp在内缘一侧不等于它遮住Ring，已在正式优化前修复过严排除。CAD用真实tube遮挡轮廓、自遮挡、内外标签；原DXY形态学处理可能移动像素，最多2.5px回溯到原Mask边界，否则不作为观察。Mid双侧/单侧/未知分开，未知权重0。分割错误和局部Ring–Polyp先后仍有不确定性，不称物理可见性GT。
4. **双向是否比单向更稳定？** R2/R3只有F的单/双向区别，比较两向FIT/HOLDOUT残差和负对照。004侧153、005侧980个独立地标，18对真实跨帧SIFT身份支持的同名地标；两侧深度均非GT。没有多病例/多随机样本重复，不能凭一次均值宣称普适稳定。
5. **R3是否优于完整RoMa？** 留出IoU {r0['HOLDOUT_IoU']:.6f}→{r3['HOLDOUT_IoU']:.6f}；Inner/Outer均值{curveavg(r0):.4f}→{curveavg(r3):.4f}px；双向F {sh['R0','HOLDOUT']['normalized_symmetric_F']:.4f}→{sh['R3','HOLDOUT']['normalized_symmetric_F']:.4f}；独立HERO MAE {hh['R0']['known_MAE_mm']:.4f}→{hh['R3']['known_MAE_mm']:.4f}mm。多维存在权衡时应判混合证据，不按主体IoU一票否决或保证胜出。
6. **是否优于019 A5？** 相同020评价程序重算A5：留出IoU {m['019_A5']['HOLDOUT_IoU']:.6f}、边界均值{curveavg(m['019_A5']):.4f}px、双向F {sh['019_A5','HOLDOUT']['normalized_symmetric_F']:.4f}；R3对应{r3['HOLDOUT_IoU']:.6f}/{curveavg(r3):.4f}/{sh['R3','HOLDOUT']['normalized_symmetric_F']:.4f}。不能用019旧的单向损失数值直接与020双向损失比较。
7. **R4加入主体有何变化？** R3→R4留出IoU {r3['HOLDOUT_IoU']:.6f}→{r4['HOLDOUT_IoU']:.6f}，边界均值{curveavg(r3):.4f}→{curveavg(r4):.4f}px，双向F {sh['R3','HOLDOUT']['normalized_symmetric_F']:.4f}→{sh['R4','HOLDOUT']['normalized_symmetric_F']:.4f}。R4唯一新增项是同一冻结body的Ring-Aware轮廓，没有新顶点参数。
8. **是否有主体偏差直接证据？** R4终点统一左切空间的body梯度与加权Ring/SIFT梯度余弦为{body_cos:.4f}；结合R3/R4实际位姿变化与独立残差解释。IoU改善且独立几何恶化时，支持来源偏差的候选解释；若各项同时改善则承认body额外价值。终点梯度抵消也可能是多目标平衡，不单独证明物理偏差。没有绝对姿态GT，不把任一变化直接当真误差。
9. **同视频负对照？** 原坐标理论为I；实际R3平移{neg[1]['translation_mm']:.6f}mm、旋转{neg[1]['rotation_deg']:.6f}°。FIT/HOLDOUT IoU从{neg[0]['FIT_IoU']:.6f}/{neg[0]['HOLDOUT_IoU']:.6f}到{neg[1]['FIT_IoU']:.6f}/{neg[1]['HOLDOUT_IoU']:.6f}；见负对照完整Ring/SIFT记录。非零漂移如实报告。
10. **HERO是否改善？** 21个真实来源、208个有向跨视频对、固定分母{hh['R3']['fixed_source_target_observation_denominator']:,}（重复源–目标观测，非独立唯一面积）。R0→R3支持率{hh['R0']['support_fraction_fixed']:.3%}→{hh['R3']['support_fraction_fixed']:.3%}，前方分歧代理{hh['R0']['front_proxy_fraction_fixed']:.3%}→{hh['R3']['front_proxy_fraction_fixed']:.3%}，未知率{hh['R0']['unknown_fraction_fixed']:.3%}→{hh['R3']['unknown_fraction_fixed']:.3%}。条件MAE不能脱离固定分母和覆盖解释；更深层可为自遮挡，不直接算错误。
11. **可可信融合了吗？** 本轮提供独立Ring/纹理方向证据及派生共同坐标候选，尚无绝对位姿真值或完整一致的原生HERO证明。保留原曲面/未知身份，提交人工审阅，不自动融合或升级主线。
'''
 ans+=f'''
## 本轮明确判断

**总体：MIXED；R3是冻结的研究候选，尚不足以升级为可信跨视频融合位姿。**

- Inner/Outer相对Mask-only明显降低了本次留出边界偏差（均值{curveavg(m['R3_MASK_ONLY']):.4f}→{curveavg(r3):.4f}px），但Mask-only的留出Polyp IoU、双向SIFT和HERO支持率更好；不存在所有评价同时占优的Ring配置。新增Mid相对无Mid仅有极小变化，未证实额外稳定收益；没有单独Inner/Outer消融，不能可靠宣布其中哪一种贡献最大。
- R3相对R2的留出双向F从{sh['R2','HOLDOUT']['normalized_symmetric_F']:.4f}降至{sh['R3','HOLDOUT']['normalized_symmetric_F']:.4f}，主要改善反向重投影；留出Polyp IoU却从{m['R2']['HOLDOUT_IoU']:.6f}降至{r3['HOLDOUT_IoU']:.6f}，Ring边界亦略差。因此本病例有反向约束收益，不足以证明双向方案普遍更稳定。与历史019 A5的同程序重算相比，R3的主要代理较好。
- R3相对RoMa的Ring边界与Polyp留出投影改善，但留出双向F略差，HERO固定分母支持率下降，Unknown增加。条件深度MAE降低不能抵消覆盖变化；**未证明独立HERO几何一致性全面改善**，也不能据此否定无主体配准。
- R4与R3极接近，未改善留出Polyp IoU，SIFT仅小幅变化。没有出现足够明确的“主体投影更好、独立几何更差”证据，故**本次未证实主体来源偏差，也未证实主体有实质额外价值**。负梯度余弦不是物理偏差证明。
- 同视频负对照虽仅漂移0.0761mm/0.5224°，却出现FIT改善而留出IoU和两向SIFT变差；不能称为无漂移或泛化稳定。保留这一过拟合/输入系统误差候选信号，不事后设置通过阈值。
- SIFT地标以背景为主（004为147/153全背景，005为899/980），两个视频相机也并非GT。Ring边界系统误差、纹理偏向、原生轨迹误差与主体偏差仍无法完全分离。本轮没有足够证据给出绝对位姿正确性结论。
'''
 method='''# 方法与实现忠实性审计

| 原定设计 | 实际实现/代码 | 限制 |
| --- | --- | --- |
| 完整RoMa左SE3 | optimize020.py:main/run；R0精确复制019历史完整T，H=exp(qscale)H_RoMa，scale1、列向量004<-005、OpenCV c2w、mm | 没有提取yaw替代初值，没有360°重搜 |
| 无主体主线 | optimize020.py:no_body_hook；禁止读取BODY018与018arm网格；R0-R3和Ring消融完成并冻结后才启用R4 | 018归一化中心/尺度仅为等价坐标转换，不用它预测遮挡/权重或筛选点；输入视角继承祖先，不宣称端到端全独立 |
| 原相机/HERO/Mask/CAD | 全部019冻结native输入，68视角、原8个保护HOLDOUT；21源HERO名单在评价前登记 | 005绝大多数帧无原生HERO，不将21源报告成55帧深度验证 |
| Mask | ring020.py:RingRenderer，官方P3D Meshes/MeshRasterizer/SoftSilhouetteShader/OpenCV camera转换，180×320同019映射 | M=.5(正Ring均值MSE+已知非Polyp背景均值MSE)，不含019旧的混合无标签arc项；主体从不预测主线遮挡 |
| 真Inner/Outer | ring020.py:CADCurves，actual CAD面邻接的front/back符号变换边；O3D首次深度排除selfocclusion；hard-CAD内孔/外轮廓区分边身份；真实3D边端点Torch投影、obs到同标签投影线段距离求导 | 脱离梯度的边身份重选，投影距离本身有有效梯度；非平面r±.6圆，未自造通用渲染器 |
| 可见观察 | DXY可见语义点回溯到原始Ring-Mask边界≤2.5px，保持I/O；I/O无外推补弧 | DXY自身有5×5closing/opening；原Mask未改变，snapping避免将其合成边界直接当原观察。Polyp邻接不是遮挡真值 |
| Mid | 实际CAD中心线r5.6、720段投影；DXY中心线来自内外平均；72角bins，双侧权重1、单侧.25、未知0，再乘全局.05 | 与I/O相关；控制实验显示平均拟合Mid有约.16–.19px近似差；未当第三独立真值 |
| 距离目标 | I/O/C使用obs→对应投影curve的鲁棒Huber(d/3px)，按固定观察权重归一 | 是任务给定方向的曲线距离，没有替换为全部隐藏预测弧到观察DT，从而避免缺弧产生伪残差 |
| yaw对称性 | 所有Ring渲染/曲线只对相机绕Ring轴规范化，原实体CAD不变；pure-yaw控制与有限差分 | 不让离散CAD赋予理想Ring虚假yaw信息 |
| 独立地标 | features020.py直接复用features019.py的SIFT、RGB-MAGSAC、min3帧track、已知相机检验与3D点鲁棒优化；005仅自己的52FIT相机/RGB | 固定相机，无BA、无HERO辅助、无当前T互相生成点；Sigma仍unit-pixel代理非已校准物理置信度 |
| 同名3D身份 | 实际SIFT feature-ID跨帧RANSAC投票，至少两侧各2视角支持、按票数一对一；18对 | 非空间最近邻；3D辅助RANSAC5/18(.75mm)、中心偏移2.16mm，未满足预登记可行性，作为失败诊断完整评价 |
| 双向投影 | objective020.py:SymmetricFeatures；fwd: X004投影到H C005；reverse: H X005投影到C004；每轨迹先平均，再方向各半 | R2保留同一019正向观测，但使用020统一轨迹/向量Huber归一与共同2D-only EPI池，非逐位重演019损失；R2/R3可公平隔离方向项 |
| EPI | 真实2D–2D RGB-RANSAC，剔除两端都已可靠三角化的观测，按帧对/target归一 | 不因当前T误差重选内点；未补缺失观测 |
| 统一权重 | LR=.25M+.35I+.05C+.35O；F=.2、E=.02、prior=.01，q尺度.6mm/5°，prior=mean(q²) | noMid保持Ring总预算1(.25/.375/0/.375)，Mask-only=M；不按组/GT/HOLDOUT调参 |
| 统一优化 | optimize020.py，Adam.01、80候选、8级回溯、左修正≤1.2mm/10°、接受完整FIT目标≤旧+1e−6、拒绝恢复q与动量 | 与019相同提案基础；新四通道单位不同，没有套用019旧混合Ring loss的+.001硬阈值。物理CAD/尺度/SE3边界未放宽；四通道相互取舍必须报告 |
| 运行恢复 | 增加仅重启时q/Adam/步数恢复；原运行源码另存provenance/runtime_source_before_resume_support | 当前进程未更换损失或数据；恢复时seconds仅本段，不伪造总耗时 |
| 梯度 | 运行0/1/20/80各分量；冻结后另在每个endpoint的统一左切空间复核Ring与两向F梯度 | 梯度与Adam真实位移严格区分；后验shadow不回流优化 |
| R4 | 和R3同初值、视角、Ring/双SIFT、优化器、预算，仅增加019 FrozenRenderer.polyp | 主体不变形；R4在无主体预测冻结后进行，未用R4反选R3 |
| 评价 | evaluate020.py，所有pose冻结后才提取HOLDOUT对应、独立O3D body/CAD投影、真实原面HERO可见性 | body IoU只是模型重投影代理；HERO非GT；没有独立位姿真值、ICP或尺度对齐 |

最终输出只是视频级共同SE3，视频内相对相机严格不变。不重新推理HERO，不生成融合面，不把诊断叠加称融合。DXY保持只读。
'''
 method+='\n初始化来源链见provenance/R0_FULL_ROMA_MATRIX_LINEAGE.json：020←019注册表←Phase-D的D1_candidates←历史H_frozen←历史baselines，完整矩阵逐项相同。只读取授权的历史T，不读取历史融合Mesh生成预测；不把本轮无HERO损失描述为整个历史初始化链从未涉及深度。\n\n评价代码静态审查修正了019的一处Ring次序遗漏：若目标HERO深度自身已位于CAD后方，不得用它证明前方自由空间。020把这种目标支持标为Unknown并单列计数，原始源观测分母不变；所有方法含R0/019A5统一重算。修正发生在任何HERO/HOLDOUT评价前，有4项已知CAD射线控制测试，绝不回流优化。曲线观测是原Mask边界像素中心，仍有量化/分割不确定性；Mid控制误差包含拟合与离散采样，不单独归因为纯透视。\n'
 write('METHOD_AND_INPUT_AUDIT.md',method)
 layers=load(R/'metrics/HERO_MULTILAYER_NATIVE_RAY_PROXY.json');col=load(R/'metrics/HERO_RING_SAMPLE_COLLISION_AUDIT.json');extra=[]
 for tag in ['R0','R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER','R4','019_A5']:
  x=[a for a in layers if a['method']==tag];c=[a for a in col if a['method']==tag and a['video']=='005'];N=sum(a['fixed_native_TRUSTED_ray_N']for a in x);extra.append(dict(method=tag,three_CORE_reference_ray_N=N,multi_source_depth_modes_ge2_fraction=sum(a['multi_source_depth_modes_ge2_N']for a in x)/N,video004_baseline_modes_ge2_fraction=sum(a['video004_only_modes_ge2_N']for a in x)/N,video005_referenced_vertices_inside_CAD_N=sum(a['vertices_inside_CAD_N']for a in c),video005_face_centers_inside_CAD_N=sum(a['face_centers_inside_CAD_N']for a in c)))
 table('metrics/HERO_MULTILAYER_COLLISION_SUMMARY.csv',extra)
 summary=intro+ans+'\n## 实际运行与核心图\n\n'+md(out,['arm','accepted','candidate_iterations','initial_objective','final_objective','seconds','body_in_loss'])+'\n原始日志、检查点和拒绝原因全部保留。数值工程门禁不是科学精度PASS。\n\n'+'''[Fig1 曲线身份](figures/Fig1_Ring_Observed_CAD_Curves.png) · [Fig2 Ring消融](figures/Fig2_Ring_Channel_Ablation.png) · [Fig3 双向SIFT](figures/Fig3_Independent_Symmetric_SIFT.png) · [Fig4 R0–R4真实投影](figures/Fig4_R0_R4_Actual_Reprojection.png) · [Fig5 共同坐标诊断](figures/Fig5_Shared_World_NOT_FUSION.png) · [Fig6 梯度与位姿](figures/Fig6_Gradients_and_SE3_Changes.png)。

全部55目标帧详细图见figures/details；派生矩阵与完整索引见RESULT_INDEX.md。算法逐项对照与代码见METHOD_AND_INPUT_AUDIT.md。完成后停止，等待人工审阅，不自动开展融合。

## 固定审计表

'''+audit
 write('TECHNICAL_REPORT_SUMMARY.md',summary)
 write('TECHNICAL_REPORT.md',summary+'\n## 双向SIFT与长尾\n\n'+md(st,['method','role','F','E','forward_N','forward_MAE_px','forward_median_px','forward_p95_px','forward_max_px','reverse_N','reverse_MAE_px','reverse_p95_px','reverse_max_px'])+'\n每个方法使用同一固定真实对应。F按track宏平均，表中px统计按实际观察点，不是同一个权重口径；观察/track/帧数详见原JSON。\n\n## HERO独立评价\n\n'+md(hero,['method','source_count','ordered_cross_source_target_pairs','fixed_source_target_observation_denominator','known_N','support_fraction_fixed','front_proxy_fraction_fixed','behind_fraction_fixed','unknown_fraction_fixed','known_MAE_mm'])+'\n支持阈值沿用019 ±.5mm，Ring首次可见面遮挡，后方表面单独保留。表面积仅逐源face centroid代理，不能相加当唯一新表面。\n\n## 固定原生射线多层与Ring内部样本\n\n'+md(extra,['method','three_CORE_reference_ray_N','multi_source_depth_modes_ge2_fraction','video004_baseline_modes_ge2_fraction','video005_referenced_vertices_inside_CAD_N','video005_face_centers_inside_CAD_N'])+'\n射线为预登记004的ref08/ref13/ref03全部原生TRUSTED Pixel ID，分母固定。各原生来源分别求首次交点，再按.5mm相邻深度间隙记录模态，不合并原面；多层可能来自合法遮挡或不一致深度，非物理错误GT。CAD内部为全部引用顶点/面心的−.02mm样本代理，使用11射线多数投票避免单射线擦边奇偶误判，非精确三角相交认证。单射线误报及修复保留provenance/SIGNED_DISTANCE_PARITY_REPAIR.json。004内部已有多层，不能全部归因跨视频配准；新增来源可以桥接原深度簇，因此模态比例下降本身也不证明错误双层减少。\n\n## 方法忠实性\n\n'+method)
 # Keep explicit engineering mistakes/negative evidence, not just poor final scores.
 rejects=[]
 for x in out:
  rows=load(R/'optimization'/x['arm']/'HISTORY.json');cnt=collections.Counter(k for a in rows if not a['accepted']for k in a['reasons']);rejects.append(dict(arm=x['arm'],rejected=sum(not a['accepted']for a in rows),reasons=dict(cnt)))
 table('metrics/REJECTION_REASONS.csv',rejects)
 failure='''# 020 失败与不确定性台账

| 项目 | 实际原因/证据 | 处理 |
| --- | --- | --- |
| 初始Inner被错误清空 | 额外规则把nonmaterial侧Polyp当遮挡；初始gate只验有限差分相等，没拒绝0观察/0梯度 | 正式优化前修复，保留provenance/initial_gate_before_visibility_repair与VISIBILITY_REPAIR_REASON；不覆盖原证据；新gate必须观察非空和梯度非零 |
| 首次Unknown-Mid检查空覆盖 | 初次选005示例实际unknown_N=0，移动空集合导致不变性检查空通过 | 改用004 raw00152真实110个未知点，强制unknown_N>0再验证；旧记录保留SYMMETRIC_FEATURE_CHECK_WITH_VACUOUS_UNKNOWN_CASE，优化目标/数据不变 |
| DXY预处理边界不是逐像素原观察 | 原DXY closing/opening可能移位或补小间隙 | 回溯原Ring-Mask边界≤2.5px，I/O未观察处不补；参数固定，没有阈值搜索 |
| Mid并非独立物理中心线真值 | 同一I/O拟合派生、有限透视/离散化近似 | .05弱辅助、支持等级独立；MID_APPROXIMATION_CONTROL保留实际偏差 |
| 独立3D地标不一致 | 18对中仅5对在.75mm内；辅助SE3中心偏移2.16mm，不满足固定可行性 | 作为NAMED_3D_DIAGNOSTIC_NOT_ADOPTED在全部55帧完整评价，不替代RoMa、不强拉HERO |
| 005反向PnP不覆盖全部004帧 | 仅4/8 FIT有独立PnP，有限3D纹理；所有原帧仍保留 | 未填假匹配；Ring保留52目标帧，2D-only EPI提供其他真实约束；相同帧集比较所有方法 |
| 背景/轨迹系统误差 | 大部分SIFT是背景；相机已冻结但非物理GT | LANDMARK_MATERIAL_AUDIT列全数；双向残差不是正确相机保证 |
| 小量粗光栅数值抖动 | 使用既有官方bin32 RingMask | 新接受容差1e−6预登记，曲线FP64有限差分/yaw门禁通过，不把微小loss变化叫科学改善 |
| 主体祖先/相机留出独立性 | 本轮保护8个HOLDOUT，但历史018/014祖先可能使用评价图 | 仅本轮优化/选模独立，不宣称端到端从未接触 |
| 无绝对配准GT | 真实世界相机/GT固定映射未知；本轮禁用项目GT | 绝对姿态误差、测量MARE/MAE/p95/max均NOT_EVALUABLE；像素/深度代理分别标单位与分母 |
| 019目标深度Ring次序遗漏 | 目标HERO本身在CAD之后时，不能作为前方自由空间证据 | 在任何评价数据读取前静态修正，4项控制通过；所有R0-R4/019A5同规则重算，固定源分母和Unknown计数保留 |
| HERO只是原生可信子集 | 21预登记来源，包含可靠性噪声、可见性空缺和非一致深度 | 全方法同分母，前方分歧/更深/遮挡/Unknown分开；不清面、不补洞、不重新HERO |
| 单射线CAD符号误报 | 一个距管材7.297mm的外部面心被默认单射线记为内部，违背0.6mm线材几何；无符号距离及11射线复核确认外部 | 仅修复独立评价，原表保存single_ray_collision_before_repair；全部方法统一11射线重算，阈值仍−.02mm；无位姿重优化 |
| 3D碰撞未独立精确三角认证 | body与Ring都固定，真实HERO只是刚体坐标变换 | 不宣称零穿透或自动可信融合，保留源曲面与独立诊断 |

## 每条路线拒绝原因

'''+md(rejects,['arm','rejected','reasons'])+'\n## 所有数值与失败结果\n\n'+core+'\n逐帧和逐来源表不删困难项。若某指标下降，需结合相机、分割、形状和纹理源偏差解释；不根据失败后再调权重或替换病例。\n'
 write('FAILURE_LEDGER.md',failure)
 write('REPRODUCE.md',f'''# 020 复现

工作树`{REPO}`，分支`exp/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020`，任务目录`{R}`。沿用019已安装Python3.12/PyTorch2.7.1cu128/P3D commit e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31；无新大型依赖。

源码复用、输入SHA和完整RoMa来自UPSTREAM_READONLY、INPUT_MANIFEST和config。inputs/G01、019原SIFT缓存与原Ring证据是只读链接；不重跑019或改写旧目录。复制本实验到独立回放目录时，需要将common.R指向独立输出，保持所有上游路径只读。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK020=experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020
$PY -B $TASK020/code/setup_inputs020.py
$PY -B $TASK020/code/prepare020.py
$PY -B $TASK020/code/features020.py
$PY -B $TASK020/code/named_candidate020.py
$PY -B $TASK020/code/gate020.py
$PY -B $TASK020/code/feature_gate020.py
$PY -B $TASK020/code/validate_landmarks020.py
$PY -B $TASK020/code/visibility_check020.py
$PY -B $TASK020/code/optimize020.py
$PY -B $TASK020/code/evaluate020.py
$PY -B $TASK020/code/layer_diagnostic020.py
$PY -B $TASK020/code/collision_check020.py
$PY -B $TASK020/code/audit020.py
$PY -B $TASK020/code/figures020.py
$PY -B $TASK020/code/reports020.py
$PY -B $TASK020/code/verify020.py
```

完整输入链接和21份HERO评价名单已经冻结，不需要重新推理深度。HERO文件缺失则必须按原索引恢复原源，不能替代；源SHA在config/HERO_EVALUATION_SOURCES.json。上述prepare仅重建协议，不应在交付冻结目录覆写；请用独立副本。audit可与优化同时等待，但HERO/Body/HOLDOUT评价只在全pose冻结后运行。独立图像可从已有evaluation与模型缓存重画，不需要再次优化。

优化保存q、Adam、迭代数与初始完整T；后续重启可加载ITER.pt，无FINAL的路线从对应状态继续。当前运行采用provenance/runtime_source_before_resume_support记录的原源码；新增恢复分支不更改本轮运行损失。日志seconds是该次进程运行时间，若恢复应单独累计。

I/O由实体CAD occluding edges+O3D自遮挡和语义分类产生，Torch投影距离求导；M用官方PyTorch3D；C用实际r5.6中心线。不用三平面圆近似管材边界，不用body遮挡主线。所有模型输出计算mm，GLB仅标准米(.001单位导出)，不是估计scale。
''')
 write('RESULT_INDEX.md',f'''# 020 完整结果索引

根目录`{R}`。

| 产物 | 路径 |
| --- | --- |
| 核心报告/方法/失败 | TECHNICAL_REPORT_SUMMARY.md、TECHNICAL_REPORT.md、METHOD_AND_INPUT_AUDIT.md、FAILURE_LEDGER.md |
| 冻结输入 | INPUT_MANIFEST.json/csv、config/VIEWS.json、config/PROTOCOL.json、config/HERO_EVALUATION_SOURCES.json |
| RoMa原始及R0–R4全部矩阵 | results/*.json（含seed_T、共享T、物理尺度、实际更新次数） |
| R3派生相机及显式方向 | derived/T004_from005_R3.json、derived/VIDEO005_CAMERAS_R3.json |
| Ring原证据/原像素映射 | ring/、ring_evidence_v2/（xy对应原640×360Pixel ID=y*640+x）、metrics/RING_VISIBLE_EVIDENCE_COUNTS.json |
| 独立004/005地标 | landmarks/CROSS_004.npz、INDEPENDENT_005.npz及*_OBSERVATIONS.json |
| 双向真实匹配 | features/CROSS_PNP.json、REVERSE_PNP.json、CROSS_NAMED_3D_TRACK_PAIRS.json、matches/ |
| 完整FIT/HOLDOUT指标 | metrics/REGISTRATION_COMPARISON.csv、ALL005_FRAME_METRICS.csv、SIFT_READABLE_SUMMARY.csv |
| 梯度和拒绝日志 | optimization/每路线/HISTORY.json、metrics/ENDPOINT_GRADIENT_RELATIONSHIPS.json、REJECTION_REASONS.csv |
| 优化状态 | optimization/每路线/ITER_001/010/020/040/080.pt，q/Adam/iteration/seed |
| 同视频负对照 | metrics/NEGATIVE_CONTROL.json/csv、NEGATIVE_PER_VIEW.csv、results/NEGATIVE_R3.json |
| HERO逐源固定分母 | metrics/HERO_INDEPENDENT_PER_PAIR.csv、HERO_INDEPENDENT_AGGREGATE.csv、HERO_CENTROID_AREA_PROXIES.csv |
| 固定原生射线多层/CAD内部样本 | metrics/HERO_MULTILAYER_NATIVE_RAY_PROXY.csv、HERO_RING_SAMPLE_COLLISION_AUDIT.csv、HERO_MULTILAYER_COLLISION_SUMMARY.csv |
| 固定004相机与逐帧SIFT | metrics/REFERENCE004_FIXED_RING_ERRORS.csv、SIFT_PER_VIEW.csv |
| 核心6图和55帧详细图 | figures/Fig*.png、figures/details/All005_01..08.png |
| 诊断GLB | derived/G01_R3_DIAGNOSTIC_NOT_FUSION.glb，原Mesh独立组件，黑色Ring，非融合 |
| 大文件本地索引 | assets_index/LOCAL_RESULTS.json；完整绝对路径、字节、SHA，不上传大型原视频/深度/权重 |

R3为预指定主候选，未由HOLDOUT/GT/HERO选出；R4只是固定body对照。全部失败和未采用3D候选保留。最终等待人工审阅，不推进融合。
''')
 big=[asset(p)for folder in ['optimization','evaluation','ring_evidence_v2','derived']for p in(R/folder).rglob('*')if p.is_file()and p.suffix in ['.pt','.npz','.glb']];save('assets_index/LOCAL_RESULTS.json',big)
 save('provenance/DELIVERED_SOURCE_MANIFEST.json',dict(files=[asset(p)for p in(R/'code').glob('*.py')],reports=[asset(R/n)for n in ['TECHNICAL_REPORT_SUMMARY.md','TECHNICAL_REPORT.md','METHOD_AND_INPUT_AUDIT.md','FAILURE_LEDGER.md','REPRODUCE.md','RESULT_INDEX.md']]))
 print('REPORTS020_COMPLETE',flush=True)
if __name__=='__main__':main()
