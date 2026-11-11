"""Final actual-results report. Descriptive comparisons never select a new pose."""
from geometry021 import *
from group_reports021 import md
import ast,platform

def write(name,s):(R/name).write_text(s,encoding='utf8')
def main():
 markers=['BA_INDEPENDENT_EVALUATION_COMPLETE','FOUR_GROUP_REPORTS_COMPLETE','ALL_FIGURES_COMPLETE','IDENTIFIABILITY_COMPLETE','PER_VIEW_COMPLETE','SHADOW_COMPLETE','BODY_ERROR_MAPS_COMPLETE','COVERAGE_FIGURES_COMPLETE','CO_VISIBLE_COMPLETE','REVERSE_RING_COMPLETE','COLLISION_FIGURES_COMPLETE']
 while not all((R/'runtime'/(m+'.json')).exists()for m in markers):time.sleep(5)
 reg=load(R/'metrics/REGISTRATION_COMPARISON.json');m={a['method']:a for a in reg};sf=load(R/'metrics/SYMMETRIC_SIFT_EVALUATION.json');ss={(a['method'],a['role']):a for a in sf};hero=load(R/'metrics/HERO_INDEPENDENT_AGGREGATE.json');hh={a['method']:a for a in hero};unused=load(R/'metrics/UNUSED_SIFT_TRACK_EVALUATION.json');uu={(a['method'],a['role']):a for a in unused};inf=load(R/'metrics/BA_IDENTIFIABILITY.json');ii={a['arm']:a for a in inf};neg=load(R/'metrics/NEGATIVE_CONTROL.json');score=load(R/'metrics/FOUR_GROUP_GEOMETRY_SCORECARD.json');p=load(R/'config/PROTOCOL.json');run=[]
 for name in ['B1','B2','B3','NEG_B1','NEG_B2','NEG_B3','SENS_B2_LightGlue','SENS_B2_020R2']:
  a=load(R/'results'/(name+'.json'));history=load(R/'optimization'/name/'HISTORY.json');why=collections.Counter(k for t in history if not t['accepted']for k in t['reasons']);run.append(dict(arm=name,iterations=a['iterations'],accepted=a['accepted'],rejected=a['iterations']-a['accepted'],initial_loss=a['initial_loss'],final_loss=a['loss'],last_segment_seconds=a['seconds'],completed_compute_lower_bound_seconds=a['seconds']+(574.4 if name=='B1'else 0),point_update=a['joint_X_optimized'],max_X_displacement_mm=float(np.linalg.norm(np.asarray(a['X'])-a['X0'],axis=1).max()),rejections=dict(why)))
 save('metrics/ACTUAL_RUN_SUMMARY.json',run);table('metrics/ACTUAL_RUN_SUMMARY.csv',run)
 jt=[]
 for a in inf:jt.append(dict(arm=a['arm'],landmarks_N=a['landmarks_N'],observations_N=a['observations_N'],Schur_rank=a['Schur_eliminated_point_pose_information']['numerical_rank'],Schur_condition=a['Schur_eliminated_point_pose_information']['condition_full'],Schur_to_fixed_trace=a['Schur_to_fixed_trace_ratio'],max_X_drift_mm=a['point_displacement_mm']['maximum'],video004_MAE_px=a['video004_reprojection_px']['MAE'],video005_MAE_px=a['video005_reprojection_px']['MAE'],point_gradient_video_cosine=a['point_gradient_video_cosine']))
 table('metrics/IDENTIFIABILITY_READABLE.csv',jt)
 siftrows=[]
 for a in sf:
  u=uu[a['method'],a['role']];siftrows.append(dict(method=a['method'],role=a['role'],fixed_anchor_F=a['normalized_symmetric_F'],fixed_anchor_E=a['normalized_E'],forward_N=a['forward']['N'],forward_MAE_px=a['forward']['error_px']['MAE'],forward_p95_px=a['forward']['error_px']['p95'],reverse_N=a['reverse']['N'],reverse_MAE_px=a['reverse']['error_px']['MAE'],reverse_p95_px=a['reverse']['error_px']['p95'],unused_track_F=u['F'],unused_forward_N=u['forward']['N'],unused_forward_MAE_px=u['forward']['error_px']['MAE'],unused_reverse_N=u['reverse']['N'],unused_reverse_MAE_px=u['reverse']['error_px']['MAE'],unused_status=u['symmetric_status']))
 table('metrics/SIFT_READABLE_SUMMARY.csv',siftrows)
 audit='''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | TaskA 1个物理组G01/1对视频/68视角；TaskB 4组，51原生来源=018核心43+G01额外005的8份 |
| 本算法独立成功 | 021独立产生3个正式BA位姿、3个负对照、2个敏感性结果；4/4新定量审计和图集。主体/HERO是明确授权只读输入，不冒充021新重建 |
| 本算法失败 | 优化停滞、未改善代理、继承穿入、G03长柄失败全部保留；数值输出成功不等于物理正确，绝对真误差NaN/NOT_EVALUABLE |
| 历史测量值回退 | 0；RoMa是授权初值/基线，018主体是授权评价输入，不读取旧Dxy测量补值 |
| 失败组及具体原因 | 全部4组见各组GEOMETRY_AUDIT.md、FAILURE_LEDGER.md、原面/原像素位置CSV和真实三维图 |
| 最终统计样本 | 全68/68计划视角；00552FIT+3HOLDOUT，0048FIT+5HOLDOUT；18共同轨迹/553实际FIT像素；TaskA21源固定HERO，TaskB51源不删失败项 |
| 是否使用GT选择算法 | 否；全部021位姿先冻结，再G01独立HERO/body/保护视角评价。TaskB非G01只读已冻结018结果并行，严格不反馈BA |
'''
 core=md(reg,['method','FIT_N','FIT_IoU','HOLDOUT_N','HOLDOUT_IoU','HOLDOUT_worst_IoU','HOLDOUT_contour_px_MAE','HOLDOUT_Inner_px_MAE','HOLDOUT_Outer_px_MAE','HOLDOUT_Ring_M','Ring_center_mm','Ring_normal_tilt_deg','correction_from_RoMa_translation_mm','correction_from_RoMa_rotation_deg'])
 shortcore=md([m[n]for n in ['B0_RoMa','B0_020_R2','B0_020_R3','B0_020_MASK','B1','B2','B3']],['method','HOLDOUT_IoU','HOLDOUT_Inner_px_MAE','HOLDOUT_Outer_px_MAE','correction_from_RoMa_translation_mm','correction_from_RoMa_rotation_deg'])
 # All comparisons are post-freeze descriptions. The displayed G01 pose was fixed to B3 in code before evaluation.
 a,b,c=m['B1'],m['B2'],m['B3'];h0,h2,h3=hh['B0_RoMa'],hh['B2'],hh['B3'];cond=ii['B2']['Schur_eliminated_point_pose_information'];moved=ii['B2']['point_displacement_mm']['maximum'];glink=lambda g:f'[{g}定量审计]({g}_GEOMETRY_AUDIT.md)'
 questions=f'''## 十五项科研回答

1. **18条同名身份质量？** 18/18保留真实描述子、原feature ID和547个跨图RGB-RANSAC链接，553个实际FIT像素逐项核对。全部为背景纹理，不是Polyp表面锚点。匹配通过多帧几何不代表物理GT；高光/重复纹理剩余歧义、原相机误差仍记录，未因独立3D差大删去13条。旧“5/18”属于020稳健3D候选的0.75mm诊断；RoMa初值下的实际逐点距离另外保存，不能混为一项。
2. **正反向为何冲突？** 020把各自独立三角化的位置固定，两套位置与已冻结轨迹不完全一致，同一T可能无法满足两者。021保存同18轨迹的两侧固定锚梯度、共同X两视频梯度、实际残差与Schur信息；不是把所有大3D差直接归因错误RGB。相机误差与三角化误差尚不能完全分离。
3. **共同BA能否降低冲突？** B2真实释放18×3个地标自由度，最大X移动{moved:.6f}mm；共同像素残差变化见下表。共享X消除了“两套点都当精确锚”的建模矛盾，但004直接pose梯度为0是参数化事实，点梯度互相抵消也可能是正常驻点，不能单独称冲突已解决。独立固定锚与未参与轨迹仍必须核查。
4. **B2相对B1独立收益？** 留出IoU {a['HOLDOUT_IoU']:.6f}→{b['HOLDOUT_IoU']:.6f}；未参与轨迹F {uu['B1','HOLDOUT']['F']}→{uu['B2','HOLDOUT']['F']}；固定HERO支持{hh['B1']['support_fraction_fixed']:.3%}→{h2['support_fraction_fixed']:.3%}；条件深度MAE {hh['B1']['known_MAE_mm']:.6f}→{h2['known_MAE_mm']:.6f}mm。必须结合Unknown/有效N与尾部，不能用训练损失下降替代独立收益；不据此反选输出。
5. **地标漂移/退化？** B2消元后位姿信息秩{cond['numerical_rank']}/6、条件数{cond['condition_full']}（参数尺度0.6mm/5°，相对秩阈值1e−8，未把先验算入观测信息）。逐点协方差为单位像素代理，非校准概率；点位移、白化幅度、正深度及空间奇异值全部给出。满秩不等于绝对姿态准确。
6. **Ring是否稳定共享SE3？** B2/B3的中心偏移分别{b['Ring_center_mm']:.6f}/{c['Ring_center_mm']:.6f}mm，法向倾角{b['Ring_normal_tilt_deg']:.6f}/{c['Ring_normal_tilt_deg']:.6f}°。尺度固定1、视频内部轨迹不动。纯yaw检查通过；绕法向信息来自实际纹理而非Ring网格锯齿。
7. **I/O容差是否有额外价值？** εI/εO={p['epsilon_px']['inner']:.3f}/{p['epsilon_px']['outer']:.3f}px，仅由FIT源边界q95+.5px确定。B2→B3留出内缘{b['HOLDOUT_Inner_px_MAE']:.6f}→{c['HOLDOUT_Inner_px_MAE']:.6f}px、外缘{b['HOLDOUT_Outer_px_MAE']:.6f}→{c['HOLDOUT_Outer_px_MAE']:.6f}px；独立HERO支持{h2['support_fraction_fixed']:.3%}→{h3['support_fraction_fixed']:.3%}。这是唯一新增项的固定对照；Mid仅诊断。不同指标若不一致，不宣布全面优越。
8. **是否超过RoMa/020？** 全部9候选使用同程序重算，见完整表。RoMa/020R3/020Mask/B2/B3留出IoU依次为{m['B0_RoMa']['HOLDOUT_IoU']:.6f}/{m['B0_020_R3']['HOLDOUT_IoU']:.6f}/{m['B0_020_MASK']['HOLDOUT_IoU']:.6f}/{b['HOLDOUT_IoU']:.6f}/{c['HOLDOUT_IoU']:.6f}。整体结论需同时看SIFT与固定分母HERO，不能只按IoU排名。B3作为TaskB默认共同坐标在评价前由代码固定，并非按留出优胜选出。
9. **负对照更稳定吗？** 统一列出Identity、020旧负对照和021三条负对照的实际mm/deg漂移与留出。没有事后设通过阈值；即使小量漂移，也不等于原轨迹绝对正确。
10. **HERO是否真正改善？** RoMa→B2→B3支持率{h0['support_fraction_fixed']:.3%}→{h2['support_fraction_fixed']:.3%}→{h3['support_fraction_fixed']:.3%}，Unknown{h0['unknown_fraction_fixed']:.3%}→{h2['unknown_fraction_fixed']:.3%}→{h3['unknown_fraction_fixed']:.3%}；条件MAE {h0['known_MAE_mm']:.6f}→{h2['known_MAE_mm']:.6f}→{h3['known_MAE_mm']:.6f}mm。N固定{h0['fixed_source_target_observation_denominator']:,}；降低条件MAE但减少支持不能叫全面一致性提高。HERO是独立代理，非GT。
11. **共享SE3不能解释残余冲突？** 有。同视频内HERO相对关系不会被一个视频级共同刚体改变；四组还存在源间分歧、合法后方和Unknown。G01有向对表明确区分同视频与跨视频，可复核共享刚体的能力边界；不能强拉原面以消除残差。
12. **G03为何没有完整长柄？** 本轮重新显示全部9份原生长柄片和短棱主体，原间隙/错层保留。G03多源深度MAE/P95={next(x for x in score if x['group']=='G03')['HERO_pair_MAE_mm']:.3f}/{next(x for x in score if x['group']=='G03')['HERO_pair_p95_mm']:.3f}mm；主体覆盖和正确首层代理、丢失/新增命中见独立报告。018 B2实际是642顶点自由位移+接触固定/Sobolev协调，COH16不是16个谱模式。历史016的未命中梯度/候选支持和方向限制证据仍适用作机制假说；本轮静态几何不能单独证明唯一原因，也不能将某一份长柄HERO直接当真值。
13. **G05/G06拼接条件？** G06来源一致性相对最好，G05次之，可作为未来局部原面保留/接缝验证候选。两者仍有继承CAD微小相交，G06局部面积压缩/边长伸长明显，G05基底WEAK；均不自动获得最终融合PASS。具体区域和原面ID见各组报告。
14. **哪些组继续跨视频？** G01已有完整双视频证据，适合继续低维几何可辨识性研究；G03/G05/G06仅按真实清点登记其他视频RGB/Mask/已有相机/HERO/SIFT，不将004叠加冒充跨视频结果。缺少相机或HERO标MISSING，不新推理或假定已恢复。
15. **是否需要逐帧微调？** 本轮不足以直接授权全部逐帧BA。应先核对未参与轨迹的逐视角残差、Schur信息、种子敏感性及停滞提案；只有能用独立证据定位到轨迹误差时，再提出有限相机实验，避免逐帧自由度吸收错误对应/HERO误差。当前不执行相机微调。
'''
 intro=f'''# 021 共同地标BA与四组定量几何审计

实际完成B1/B2/B3、3条同视频负对照、2条固定历史初值敏感性；4个历史B0仅作冻结参考。全部68视角保留，18条实际共同轨迹/553个FIT像素共同约束一个共享SE3；B2/B3确实优化共同XYZ，没有ICP替代。TaskB四组51个原生来源、六视角/GLB、逐面和固定原生ID指标全部完成。

**数值执行、残差改善、独立几何证据和绝对真实精度严格分开。** 没有读取项目GT，没有新主体/深度推理或曲面融合。020→021改变了观测表达与Ring目标，不能把它当只有一个变量的因果实验；B2对B1、B3对B2才是本轮受控比较。

'''+shortcore+'''
IoU无单位，边界为原640×360像素，平移mm、旋转deg。留出仅3个005视角，主体验证还受018模型与祖先使用范围限制，不能等同绝对相机精度。

'''
 quartet=md(score,['group','TRUSTED_sources_N','HERO_pair_MAE_mm','HERO_pair_p95_mm','co_visible_first_layer_candidate_N','co_visible_candidate_MAE_mm','co_visible_candidate_p95_mm','HERO_support_fraction','native_TRUSTED_pixel_N','B0_FIT_HERO_MAE_mm','B2_FIT_HERO_MAE_mm','gained_FIT_N','lost_FIT_N','B2_HOLDOUT_IoU','B2_Ring_FCL_surface_collision','B2_max_edge_stretch','B2_min_area_ratio'])
 summary=intro+questions+'\n## 四组统一定量摘要\n\n'+quartet+'\n'+ ' · '.join(glink(g)for g in GROUPS)+'\n\n历史可比较深度包含合法后方，首层共视候选另列且仍是几何代理。完整分母、误差尾部、CAD/Unknown、逐面定位见各组报告；来源面积不能相加称唯一解剖面积。\n\n'+audit+'\n八张核心图、四组完整图集及GLB见[RESULT_INDEX](RESULT_INDEX.md)。全部结果提交人工审核，不启动融合或逐帧BA。\n'
 write('TECHNICAL_REPORT_SUMMARY.md',summary)
 details=summary+'\n## 完整同分母位姿比较\n\n'+core+'\n## 实际优化与拒绝\n\n'+md(run,['arm','iterations','accepted','rejected','initial_loss','final_loss','last_segment_seconds','completed_compute_lower_bound_seconds','max_X_displacement_mm','rejections'])+'\nB1曾随会话中断，从ITER030恢复q/X/Adam。原段日志到574.4s；上表总计算时间为已完成检查点的下界，不包含未落盘工作和等待，不伪称精确端到端墙钟。其他秒数为各实际进程段。后期反复拒绝不等于全局收敛。\n\n## 独立SIFT与未参与轨迹\n\n'+md(siftrows,['method','role','fixed_anchor_F','fixed_anchor_E','forward_N','forward_MAE_px','forward_p95_px','reverse_N','reverse_MAE_px','reverse_p95_px','unused_track_F','unused_forward_N','unused_forward_MAE_px','unused_reverse_N','unused_reverse_MAE_px','unused_status'])+'\nF为逐轨迹归一鲁棒向量目标，px统计为真实观察点分布；二者权重口径不同。未参与BA集合排除18条源track及相同目标feature像素；若某方向N0则双向目标NOT_EVALUABLE，不能把空集合0当好结果。\n\n## 共同点消元信息与漂移\n\n'+md(jt,['arm','landmarks_N','observations_N','Schur_rank','Schur_condition','Schur_to_fixed_trace','max_X_drift_mm','video004_MAE_px','video005_MAE_px','point_gradient_video_cosine'])+'\n采用实际点局部Jacobian和向量Huber IRLS权重组装块稀疏信息，S=A−Σ Bk Dk⁺ Bkᵀ。这里是冻结后诊断，不是声称使用Schur BA优化器；不将RoMa/点先验加入观测秩。低条件数/满秩仍依赖固定相机与匹配模型，非物理置信度。不同历史种子还改变pose先验中心，因此敏感性不是完全固定先验的纯局部极小值试验；未根据结果择优。\n\n## 固定21来源跨视频HERO\n\n'+md(hero,['method','source_count','ordered_cross_source_target_pairs','fixed_source_target_observation_denominator','known_N','support_fraction_fixed','front_proxy_fraction_fixed','behind_fraction_fixed','Ring_occluded_fraction_fixed','unknown_fraction_fixed','known_MAE_mm'])+'\n使用020同一原源/目标配对、固定分母、实际CAD首次可见性；目标深度自身落在CAD之后则Unknown。前方是几何分歧代理，后方保留自遮挡解释。共同有效N变化不能从误差均值中消失。固定CORE原生射线多层见HERO_MULTILAYER_NATIVE_RAY_PROXY，非错误双层GT。\n\n## 同视频负对照\n\n'+md(neg,['method','translation_mm','rotation_deg','FIT_N','FIT_IoU','HOLDOUT_N','HOLDOUT_IoU','FIT_SIFT','HOLDOUT_SIFT'])+'\n## 冻结后影子提案\n\n'+md(load(R/'metrics/ENDPOINT_SHADOW_PROPOSALS.json'),['arm','mode','alpha','delta_loss','predicted_gradient_dot','actual_delta_translation_mm','actual_delta_rotation_deg','max_X_step_mm','fixed_state_repeat_loss_range'])+'\n影子只解释终点提案，不提交新输出，也不是历史各次拒绝的精确重放；全部冻结矩阵SHA保持不变。特别核对恢复Adam旧状态后的相同非下降方向、整方向回溯与Float32光栅数值抖动，不把停滞全部推给输入。\n'
 write('TECHNICAL_REPORT.md',details)
 method='''# 021 方法与实现忠实性

| 原定设计 | 实际代码 | 差异与限制 |
| --- | --- | --- |
| 实际跨视频身份 | prepare021.initialize / identity021.main | 02018同名轨迹全部回到真实原feature ID、描述子与RGB-RANSAC链接；不以3D近邻或0.75mm诊断删点；553观察全为背景，非Polyp特征 |
| 共同未知X | ba021.CommonPoints | 18×3个XYZ，004/005同名全部合法FIT观测共用；B1固定X0，B2/B3真实Adam更新X |
| 联合三角化初值 | prepare021.initialize | 全部相机DLT+SciPy least_squares点优化；初值用加权分量Huber，主优化用向量Huber，二者不冒称数学相同。单位像素协方差仅代理，正深度/视差/条件数/CAD关系保留 |
| 一个共享SE3 | ba021.BA.transform | exp(delta)左乘完整RoMa，004世界坐标、mm、scale1；不释放独立相机/尺寸。官方P3D se3_exp_map保留FP64，移除旧float32往返；实际FD校验通过 |
| 轨迹/视频/方向归一 | prepare021.initialize / weight_audit021 | 每条轨迹两视频各半；视频内按019方向块均分，再轨迹均分。004实际69条、005实际484条观测总目标质量各0.5；每条轨迹内部按其实际观察方向均分，跨轨迹汇总方向权重不必严格相等，实际表见ACTUAL_VIDEO_DIRECTION_WEIGHT_AUDIT。支持类别均分，但本数据全背景，无法凭空提供Polyp证据 |
| Ring实体/可见语义 | ring020.CADCurves / ba021.Ring021 | 真实CAD occluding edges+自遮挡、独立I/O、原Mask像素回溯；不是三平面圆。R10训练参数与020相同；四组诊断半径从各自固定CAD取得；代码可参数化R5/R10，本轮没有新增R5实测病例 |
| I/O带容差 | ba021.Ring021.term | L=M+.05(Ieps+Oeps)，eps由FIT源边界不确定性q95+.5px且至少1px；实际得1px。距离超过epsilon后sigma3px向量Huber；未观察弧不补，Mid只在独立评价记录 |
| 联合目标 | ba021.BA.evaluate | .2重投影+Ring+.01 posePrior+.001 whitenedPointPrior；点先验σ裁剪.05..3mm。对B1同一表达点先验为0，B2仅释放X，B3仅增加I/O。没有2D–2D EPI损失（只诊断），不把与020的差异说成仅BA一个变量 |
| 成熟求解/稀疏结构 | PyTorch Adam+020回溯；identifiability021 | 使用稀疏观察索引/点局部Jacobian，但未采用专用Schur/SLAM求解器；Schur消元仅后验诊断。单点初值用SciPy，官方P3D用于Ring，不新写通用BA框架 |
| 有界参数更新 | ba021.run | q lr.01、X lr.02mm；100候选、8级回溯、拒绝恢复参数及Adam；T≤1.2mm/10°，X≤3mm/白化6，正深度。全部参数固定，无HOLDOUT/HERO调权 |
| 不可辨识性 | identifiability021.main | 实际18点/9负对照点的局部块信息，Huber IRLS后消元；均为固定相机条件代理，不将先验提升的秩冒充观测信息 |
| 光栅像素中心核对 | raster_pixel_audit021 | 实际FIT CAD的964个顶点通过官方P3D screen接口核对；screen减0.5后与OpenCV半分辨率像素中心公式一致，最大分量差2.87e−5px。继承的Ksmall主点+0.25是光栅中心补偿，不将其误删为相机修正 |
| 独立评价 | eval021 / per_view021 / copied evaluate020 | 所有021 pose冻结后G01保护视角、未参与轨迹、body/HERO；9个候选全部55目标视角、全部68逐视角SIFT，失败N0保持；无GT |
| 四组并行 | group_audit021 / source_geometry021 | 非G01只读018冻结预测独立完成，不反馈G01 BA；G01等待021所有pose冻结。全部043+8来源保留，区分同视频和跨视频 |
| 真实几何与统计 | geometry021 / body_error021 / group_reports021 | 实际原生Pixel ID/Raw Face ID、轴向Z、三角面面积、固定分母、共同/新增/丢失；CAD与自遮挡，Front/Behind/Unknown分离；没有ICP/补洞/清面 |
| 首层共视与反向实体包含 | covisible021 / reverse_ring021 | 源自身CAD次序检查，首层候选剔除可能合法自遮挡后方；与020历史分母并列。实际CAD顶点/面心到闭合主体检查补充FCL；不伪称严格无穿透证书 |
| 几何检查 | geometry021.body_quality | 复用01864阶面内CAD检查，沿用001mm阈值，符号查询统一11射线；独立FCL、Open3D非邻接自交、拓扑和面片质量。底盖灰色推断身份，不作为可见表面监督 |
| 可视化 | visualize021 / body_error021 | 复用018 Open3D实际三角面射线着色，不用点云/解析体替代HERO或主体；GLB源独立node，所有原面保留，只紧凑化无引用顶点；mm→m为固定单位换算 |

Ring-First历史链只读核对：multigroup run_geometry→V6 local_ring_sfm initialize/triangulate_training/BA、ring_pose_contact decode/solve及v6实体轮廓；当前014背景SIFT/PnP扩展与018原生K/相机回执一致。输入完整性核对可读取原图/原生数组做哈希、像素绑定和坐标自检，但不评价021候选或反馈BA；G01的HOLDOUT几何指标、body/HERO一致性评价严格在全部位姿冻结后。轨迹连线复用018/019已验证raw-index绑定，不把历史声明帧号当新认证。ADDITIONAL_CAMERA_SOURCE_AUDIT记录文件SHA，未重估原始轨迹；不将整个历史初始化链描述为无深度。

官方接口参考：[PyTorch3D SE3](https://github.com/facebookresearch/pytorch3d/blob/main/pytorch3d/transforms/se3.py)、[SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)、[Open3D RaycastingScene](https://www.open3d.org/docs/release/python_api/open3d.t.geometry.RaycastingScene.html)。实际安装版本与源码位置见ENVIRONMENT_AND_CODE.json，不要求下载新包。

源码运行中唯一训练侧修补是中断恢复时不覆盖INITIAL/首次freeze；原训练源码另存ba_source_before_resume_preservation_fix，目标/输入/预算未改变。初次开发读取旧特征缓存把des写成desc，已在正式冻结前修正，并逐项验证全部原描述子；无数据重建替代。
'''
 write('METHOD_AND_INPUT_AUDIT.md',method)
 failure='''# 021 失败与不确定性台账

| 项目 | 真实证据与处理 |
| --- | --- |
| 特征缓存字段适配错误 | 准备期KeyError desc，实际缓存键为des；正式freeze之前修正，553条描述子及547链接逐项核对，无原数据修改 |
| 执行中断 | B1进程随会话中断退出，无数值错误trace；ITER030恢复q/X/Adam，旧INITIAL和首次预注册保留，累计耗时给下界而非伪造精确墙钟 |
| 优化后期停滞 | 各路线真实接受数/拒绝原因见运行表；保留整个100次轨迹。终点影子分解q/X提案，只诊断不提交结果，不把停滞说成科学否定BA |
| 非零点漂移不等于正确 | 地标只是RGB支持，背景重复纹理/高光/固定相机误差仍可能；协方差未校准；原独立3D差不能等同错匹配 |
| 仅背景共同地标 | 18条全背景，没有Polyp同名三维纹理锚；类别权重无法创造缺失观测；全部实际帧保留但部分SIFT方向/帧N0 |
| 独立轨迹检查缺方向风险 | 未参与源track和目标同像素均排除；若某方向N0，双向F明确NOT_EVALUABLE，不以0报改善；完整每帧N0/来源保留 |
| 原生HERO不是物理GT | 四组TRUSTED有噪声/错层/未知；后方可为正常自遮挡，前方也只是代理，不能自动删除或宣称错误双层 |
| G03长柄仍失败 | 真RGB有长柄Mask，HERO有长条片，主体仍短棱/翼；首层错误/未命中与来源不一致共同记录，新增命中可能数毫米错误，不声称已恢复 |
| G05/G06继承CAD相交 | B0/B2 FCL相交和微小负距离均如实记录；不以数值容差调高制造无碰撞PASS |
| G06局部质量 | B2边长伸长/面积压缩虽无非邻接自交，仍属局部形变质量问题，不通过平滑显示掩盖 |
| 补充覆盖图RGB背景归一化 | 初版将uint8 RGB乘0.4后作为float显示而被imshow截断；已仅修复为RGB/255再变暗，旧图保存在provenance/coverage_RGB_display_before_normalization_fix，深度/Mask/指标未改变 |
| 基底不确定 | G05等WEAK基底保持；估计平面/推断底盖非真实观察，主体模型Hmax不是实际测量精度 |
| 面积/覆盖代理限制 | 累计来源面积重复计数；0.25mm面心格依赖离散和格相位，不是去重解剖面积；灰色未知不是零误差 |
| 历史祖先独立性 | 本轮保护视角不进BA；018/014祖先可能曾使用部分评价图，不宣称端到端从未接触；HERO来源共享RGB不当独立统计票 |
| 缺绝对位姿GT | 绝对姿态/测量MedARE、MAE、P95、Max均NOT_EVALUABLE，不用旧Dxy或历史模型回退填值 |
| 其他视频缺资产 | 真实清单见OTHER_VIDEO_ASSET_INVENTORY，MISSING按具体RGB/Mask/相机/HERO/SIFT记录；本轮不新恢复其相机或推理HERO |

'''+md(run,['arm','accepted','rejected','rejections','max_X_displacement_mm'])+'\n全部原始负结果、错误区域原面ID、数值未命中和Unknown均保留。个别代理下降不等于绝对真误差增加或路线被否定。\n'
 write('FAILURE_LEDGER.md',failure)
 decisions=[]
 statements={'G01':('跨视频/深度残余不一致，背景锚点不能直接保证息肉','先核对消元信息、未参与轨迹和同层局部表面；不全局融合'),'G03':('长柄缺失/错误首层与源间分歧、方向覆盖不足','先区分原面错层与未命中；有针对性补互补方向，不盲目拉顶点'),'G05':('基底WEAK、局部源差异及继承Ring接触','同层可信局部面保留与受控接缝候选，先处理实体接触'),'G06':('局部三角伸长/压缩及继承Ring接触','优先局部原面保留/质量保护小试，不重复全局收缩')}
 for x in score:
  why,nxt=statements[x['group']];decisions.append(dict(group=x['group'],multi_HERO_MAE_p95_mm=f"{x['HERO_pair_MAE_mm']:.3f}/{x['HERO_pair_p95_mm']:.3f}",co_visible_MAE_p95_mm=f"{x['co_visible_candidate_MAE_mm']:.3f}/{x['co_visible_candidate_p95_mm']:.3f}",co_visible_N=x['co_visible_first_layer_candidate_N'],support_fraction=x['HERO_support_fraction'],native_coverage=f"{x['native_TRUSTED_pixel_N']}/{x['native_Polyp_pixel_denominator']}",cumulative_source_area_mm2=x['cumulative_source_area_mm2'],B0_B2_native_MAE_mm=f"{x['B0_FIT_HERO_MAE_mm']:.3f}→{x['B2_FIT_HERO_MAE_mm']:.3f}",Ring_Inner_Outer_HOLD_px=f"{x['Ring_HOLDOUT_Inner_MAE_px']:.3f}/{x['Ring_HOLDOUT_Outer_MAE_px']:.3f}",Ring_FCL=x['B2_Ring_FCL_surface_collision'],bottleneck=why,next_experiment=nxt))
 write('FOUR_GROUP_RESEARCH_DECISION.md','# 四组统一科研决策\n\n'+md(decisions,['group','multi_HERO_MAE_p95_mm','co_visible_MAE_p95_mm','co_visible_N','support_fraction','native_coverage','cumulative_source_area_mm2','B0_B2_native_MAE_mm','Ring_Inner_Outer_HOLD_px','Ring_FCL','bottleneck','next_experiment'])+'\n多HERO旧口径包括单列的后方/可能合法遮挡；首层共同可见候选另排除后方并检查源自身CAD次序，仍非GT共表面准确度。反向CAD包含与FCL/主体到CAD检查并列见各组报告。四组同一指标口径，实际N/单位/原面来源见FOUR_GROUP_GEOMETRY_SCORECARD.csv及独立报告。G03/G05/G06为同视频，G01默认B3派生坐标；不能比较成四个已认证跨视频结果。G06/G05只是下一轮局部保留/接缝研究候选，不是已授权融合。当前全部绝对3D精度NOT_EVALUABLE。\n\n'+audit)
 write('REPRODUCE.md',f'''# 021 复现

工作树`{REPO}`；分支`exp/TASK-E4-RING-ANCHORED-JOINT-BA-021`，根目录`{R}`。复用既有Python3.12/PyTorch/PyTorch3D/OpenCV/SciPy/Open3D，无新模型下载。完整输入在config/FOUR_GROUP_INPUTS.json及020只读链接；原始大型数据不在Git，按绝对路径+SHA恢复，缺失不得替换。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
T21=experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021
# 创建新的空白回放目录，不复制历史预测，不覆盖交付目录。
REPLAY21=/home/liu/ring_first_3d_e4_sdf_localization/replays/021_fresh
$PY -B $T21/code/setup_replay021.py --output "$REPLAY21"
T21=$REPLAY21
$PY -B $T21/code/prepare021.py
$PY -B $T21/code/identity021.py
$PY -B $T21/code/track_contactsheet021.py
$PY -B $T21/code/weight_audit021.py
$PY -B $T21/code/assets021.py
$PY -B $T21/code/gate021.py
$PY -B $T21/code/tolerance_check021.py
$PY -B $T21/code/raster_pixel_audit021.py
$PY -B $T21/code/ba021.py
$PY -B $T21/code/eval021.py
$PY -B $T21/code/identifiability021.py
$PY -B $T21/code/shadow021.py
$PY -B $T21/code/per_view021.py
$PY -B $T21/code/group_audit021.py
$PY -B $T21/code/source_geometry021.py
$PY -B $T21/code/reverse_ring021.py
$PY -B $T21/code/covisible021.py
$PY -B $T21/code/body_error021.py
$PY -B $T21/code/coverage_figures021.py
$PY -B $T21/code/collision_figures021.py
$PY -B $T21/code/visualize021.py
$PY -B $T21/code/group_reports021.py
$PY -B $T21/code/report021.py
$PY -B $T21/code/verify021.py
```

顺序执行或仅将明确独立的等待脚本放后台。已有FINAL时不重新优化；缺FINAL而有ITER_*.pt则恢复q/X/Adam/迭代。初始矩阵与点、全部100候选、拒绝原因、每10步完整状态均保存。恢复旧段耗时另外列，不伪称无间断墙钟。

可只重画已冻结evaluation上的图，不需要再次BA/HERO。完整GLB只在本地索引，不能把未上传文件说成在Git。单位从头到尾mm，GLB标准m仅固定.001换算。
''')
 index='# 021 结果索引\n\n'+md([dict(item='完整报告/方法/失败',path='TECHNICAL_REPORT_SUMMARY.md / TECHNICAL_REPORT.md / METHOD_AND_INPUT_AUDIT.md / FAILURE_LEDGER.md'),dict(item='四份独立定量报告',path='G01_GEOMETRY_AUDIT.md / G03_GEOMETRY_AUDIT.md / G05_GEOMETRY_AUDIT.md / G06_GEOMETRY_AUDIT.md'),dict(item='统一量化与决策',path='FOUR_GROUP_GEOMETRY_SCORECARD.csv / FOUR_GROUP_RESEARCH_DECISION.md'),dict(item='18真实身份/553像素/描述子',path='observations/CROSS_COMMON_TRACKS.json / CROSS_PIXEL_DESCRIPTOR_INDEX.csv / CROSS_DESCRIPTORS.npz'),dict(item='输入来源与SHA',path='config/FOUR_GROUP_INPUTS.json / provenance/UPSTREAM_READONLY.json / ADDITIONAL_CAMERA_SOURCE_AUDIT.json'),dict(item='全部矩阵与优化X',path='results/*.json / optimization/*/FINAL.json / HISTORY.json / ITER_*.pt'),dict(item='B1/B2/B3全部68派生相机',path='derived/ALL68_CAMERAS_B*.json / T004_from005_B*.json'),dict(item='全部005逐帧/双向SIFT',path='metrics/ALL005_FRAME_METRICS.csv / SIFT_READABLE_SUMMARY.csv / SIFT_ALL68_PER_VIEW.csv / UNUSED_SIFT_TRACK_EVALUATION.json'),dict(item='Schur信息/点漂移/初值/影子',path='metrics/BA_IDENTIFIABILITY.json / COMMON_POINT_MOVEMENT.csv / INITIALIZATION_SENSITIVITY.json / ENDPOINT_SHADOW_PROPOSALS.csv'),dict(item='同视频负对照',path='metrics/NEGATIVE_CONTROL.json / NEGATIVE_PER_VIEW.csv'),dict(item='21源跨视频HERO固定分母',path='metrics/HERO_INDEPENDENT_PER_PAIR.csv / HERO_INDEPENDENT_AGGREGATE.csv / HERO_MULTILAYER_NATIVE_RAY_PROXY.csv'),dict(item='四组完整逐源/逐面/原生Pixel ID',path='metrics/groups/ / evaluation/groups/*/*SOURCE_EVIDENCE.npz / *_RING_MATERIAL.npz / *_BODY_FACE_MM_ERROR.npz'),dict(item='其他视频轻量清点',path='metrics/OTHER_VIDEO_ASSET_INVENTORY.json/csv'),dict(item='大文件路径/SHA',path='assets_index/LOCAL_RESULTS.json')],['item','path'])+'\n## 八张核心图\n\n[全部18条实际RGB身份审计](figures/All18_Actual_RGB_Track_Identity_Audit.png)。\n\n'
 for f in sorted((R/'figures').glob('Fig*.png')):index+=f'- [{f.stem}](figures/{f.name})\n'
 index+='\n## 四组完整图集与本地GLB\n\n'
 for g in GROUPS:index+=f'- {glink(g)} · [六视角](figures/groups/{g}/Six_View_HERO_Body_Evidence.png) · [主体毫米误差](figures/groups/{g}/Body_Surface_Native_Depth_Error_mm.png) · GLB：`{R}/derived/{g}/{g}_INDEPENDENT_LAYERS_NOT_FUSION.glb`；独立图层与全部源SHA见`derived/{g}/SOURCE_LAYER_INDEX.json`。\n'
 index+='\nG01同尺度阶段对照：[RoMa→020R3→021B3](figures/groups/G01/Before020_After020_After021.png)。全部图层保持原面；不是融合Mesh。GLB/大数组未强制上传，完整本地路径和SHA均在索引。\n';write('RESULT_INDEX.md',index)
 # Full local outputs are indexed, not silently uploaded.
 large=[asset(p)for d in ['derived','evaluation','optimization','observations']for p in(R/d).rglob('*')if p.is_file()and p.suffix in ['.npz','.pt','.glb']];save('assets_index/LOCAL_RESULTS.json',large)
 import torch,scipy,cv2,trimesh,open3d,numpy
 code=[]
 for path in(R/'code').glob('*.py'):
  for n in ast.parse(path.read_text()).body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):code.append(dict(file=str(path),symbol=n.name,line=n.lineno,sha256=sha(path)))
 table('metrics/IMPLEMENTATION_CODE_LOCATIONS.csv',code);save('provenance/ENVIRONMENT_AND_CODE.json',dict(Python=platform.python_version(),torch=torch.__version__,scipy=scipy.__version__,OpenCV=cv2.__version__,Open3D=open3d.__version__,NumPy=numpy.__version__,trimesh=trimesh.__version__,P3D_commit='e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31',code=[asset(p)for p in(R/'code').glob('*.py')]))
 reports=[asset(p)for p in R.glob('*.md')if p.name not in ['RUN_STATUS.md']];save('provenance/DELIVERED_SOURCE_MANIFEST.json',dict(epoch=time.time(),files=[asset(p)for p in(R/'code').glob('*.py')],reports=reports,all_predictions_unchanged=all(sha(a['path'])==a['sha256']for a in load(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json')['files'])));print('021_REPORTS_COMPLETE',flush=True)
if __name__=='__main__':main()
