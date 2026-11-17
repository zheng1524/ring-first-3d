from context import *
from evaluate_geometry import new_sources
from coverage import direction_stats
import platform,re,tarfile

def md(name,text):p=N/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(text.strip()+'\n')
def num(x,n=3):return 'NaN'if x is None else f'{x:.{n}f}'
def audit_table():return '''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个独立物理组；8视频+12照片；7650原始视频帧，实际处理884候选 |
| 本算法独立成功 | 877/884产生数值相机（含弱/留出）；550/884条件性验证；4/4组完成新HERO；47/47真实推理+分类 |
| 本算法失败 | 7/884相机无数值（NaN）；其余弱候选和25留出不作正式目标；新增几何未达到可直接Body适配结论 |
| 历史测量值回退 | 0；新HERO推理47次均reused=false；历史相机/原生几何为明确授权的输入及对照 |
| 失败组及具体原因 | 全四组逐来源/逐相机见FAILURE_LEDGER.md与metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv；G03错层、G06支持图反例见Figure6/E4 |
| 最终统计样本 | 全体分母保留：4组、884候选、47推理；几何共同有效N和固定native-pair像素N分别列出，不能以条件MAE代替覆盖 |
| 是否使用 GT 选择算法 | 否；无GT/Oracle数据读取；各组相机和HERO计划freeze早于首次新HERO；旧相机/地图/Body的历史留出依赖不宣称独立 |
'''
def main():
 pool=[]
 for g in GROUPS:
  p=N/'config/G01_FINAL_CAMERA_POOL_CORRECTED_HELD_MAP.json'if g=='G01'else camera_file(g);pool+=load(p)
 inf=load(N/'metrics/HERO_INFERENCE_RESULTS.json');cl=load(N/'metrics/HERO_CLEANING_RESULTS.json');src=load(N/'metrics/SOURCE_CAMERA_COUNTS.json');sc=load(N/'metrics/HERO_COVERAGE_AND_CONFLICT_SCORECARD.json');grad=load(N/'metrics/RING_RGB_GRADIENT_COMPETITION.json');maps=load(N/'metrics/COMMON_LANDMARK_DRIFT.json');schur=load(N/'metrics/CONDITIONAL_RGB_SCHUR_INFORMATION.json');e4=load(N/'metrics/E4_FIXED_COMMON_NATIVE_PIXEL_COMPARISON.json')[0];env=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,opencv=cv2.__version__,GPU=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True).strip(),HERO=load(N/'provenance/HERO_MODEL.json'),source_base=load(N/'provenance/START.json'));save('provenance/ENVIRONMENT.json',env)
 flat=[];quality=[];failed=[];regions=[]
 for v in pool:
  r=dict(group=v['group'],id=v['id'],capture_type=v['capture_type'],video=v['video'],role=v['role'],raw_frame=v.get('raw_frame'),source_video=v.get('source_video'),source_video_SHA=v.get('source_video_SHA256'),RGB=v['RGB_source'],RGB_SHA=v['RGB_SHA256'],Mask=v['Mask_source'],Mask_SHA=v['Mask_SHA256'],K=v['K'],C_mm=v.get('C'),status=v['status'],formal_conditional=v['formal'],HERO_eligible=v['HERO_target_eligible'],aliases=v.get('aliases',[]),binding=v.get('frame_binding'),no_absolute_pose_GT=True);flat.append(r);q=v.get('RGB_evaluation',{});rr=v.get('Ring',{});quality.append(dict(group=v['group'],id=v['id'],video=v['video'],role=v['role'],status=v['status'],formal_conditional=v['formal'],reasons=v.get('qualification_reasons',[]),FIT_N=q.get('FIT',{}).get('N'),FIT_MAE_px=q.get('FIT',{}).get('MAE'),held_N=q.get('FEATURE_HELD',{}).get('N'),held_MAE_px=q.get('FEATURE_HELD',{}).get('MAE'),held_median_px=q.get('FEATURE_HELD',{}).get('median'),held_p95_px=q.get('FEATURE_HELD',{}).get('p95'),Ring_IoU=rr.get('Ring_IoU'),Inner_N=rr.get('inner',{}).get('N'),Inner_MAE_px=rr.get('inner',{}).get('MAE'),Inner_median_px=rr.get('inner',{}).get('median'),Inner_p95_px=rr.get('inner',{}).get('p95'),Outer_N=rr.get('outer',{}).get('N'),Outer_MAE_px=rr.get('outer',{}).get('MAE'),Outer_median_px=rr.get('outer',{}).get('median'),Outer_p95_px=rr.get('outer',{}).get('p95'),RGB_rank=v.get('RGB_rank'),RGB_condition=v.get('RGB_condition'),world_unit='mm',map_independence='historical conditional map; current held feature IDs not fit'))
  if not v['formal']and v['role']!='HOLDOUT':failed.append(r|dict(reason=v.get('qualification_reasons',[v.get('error',v['status'])]),evidence_RGB=v['RGB_source'],registration_log='registration/'+v['id']+'/INITIAL.json'))
  pp=Path(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'))
  if pp.exists():
   mm=load(pp)['fit_pnp_inliers'];cc=collections.Counter(m.get('region','UNKNOWN')for m in mm);regions.append(dict(group=v['group'],id=v['id'],RGB_inlier_N=len(mm),BG_N=cc.get(0,0),Polyp_N=cc.get(1,0),Ring_N=cc.get(2,0),optimization_used=v['role']=='FIT',region_weights_not_tuned=True))
 table('ALL_CAMERA_CANDIDATES.csv',flat);table('CAMERA_QUALITY_AND_UNCERTAINTY.csv',quality);table('metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv',failed);table('metrics/RGB_FIT_INLIER_REGIONS.csv',regions)
 selections=[];counts=[];supports=[];hero=[];final=[];summary=[];abl=[]
 for g in GROUPS:
  a=load(selpath(g,'_SELECTION.json'));selections+=a['ranked'];ct=load(selpath(g,'_COUNT_ABLATION.json'));counts+=ct;supports+=load(selpath(g,'_SUPPORTS.json'));actual=[r for r in sc if r['group']==g and r['scope']=='NEW_OLD_FIT'][0];vs=[v for v in pool if v['group']==g];cn={s:sum(v['formal']and v['video']==s for v in vs)for s in ['004','005','PHOTO']};newN=sum(r['group']==g and r['variant']=='GEOMETRIC3'for r in inf);summary.append(dict(group=g,candidates=len(vs),numeric=sum(v.get('C')is not None for v in vs),formal004=cn['004'],formal005=cn['005'],formalPHOTO=cn['PHOTO'],recommended_research_target_N=a['recommended_N'],actual_new_HERO_targets=newN,new_old_depth_MAE_mm=actual['depth_MAE_mm'],new_old_depth_median_mm=actual['depth_median_mm'],new_old_depth_p95_mm=actual['depth_p95_mm'],fixed_pair_pixel_N=actual['fixed_native_pair_pixel_N'],known_pair_N=actual['known_N'],same_layer_fraction_fixed=actual['same_layer_N']/max(1,actual['fixed_native_pair_pixel_N']),direct_Body_promotion=False,absolute_accuracy='NOT_EVALUABLE'))
  final.append(dict(group=g,research_target_ids=[r['id']for r in a['ranked']],research_target_N=a['recommended_N'],approved_for_automatic_Body_update=False,reason='newdepths lack consistent independent improvement; G03 severe layers, E4G06 supports negative; wait review',camera_pool_count=cn,geometric_unknown_regions='head/stalk/base unannotated; unknown back not counted recovered'))
  for r in ct:abl.append(dict(group=g,requested=r['requested'],actual_N=r['actual_N'],IDs=r['IDs'],direction=r['direction'],HERO_proxy_visible_mm2=r['HERO_proxy_visible_mm2'],HERO_proxy_total_mm2=r['HERO_proxy_total_mm2'],body_visible_mm2=r['body_visible_mm2'],direction2_mm2=r['direction2_mm2'],direction3_mm2=r['direction3_mm2'],status=r['status']))
 for r in inf:
  root=N/'hero_fit'/r['id'];c=next(x for x in cl if x['id']==r['id']);hero.append(dict(group=r['group'],id=r['id'],target=r['view_id'],variant=r['variant'],rank=r['rank'],success=r['success'],new_inference=True,reused=False,source_ids=r['source_ids'],target_RGB_SHA=r['target_SHA'],support_RGB_SHA=r['source_SHA'],native_depth=str(root/'HERO_native.npz'),native_depth_SHA=sha(root/'HERO_native.npz'),Raw_mesh=str(root/'Raw_open_mesh.ply'),raw_mesh_SHA=sha(root/'Raw_open_mesh.ply'),face_evidence=str(root/'FACE_EVIDENCE.npz'),face_evidence_SHA=sha(root/'FACE_EVIDENCE.npz'),TRUSTED_mesh=str(root/'TRUSTED_HERO.npz'),TRUSTED_SHA=sha(root/'TRUSTED_HERO.npz'),depth_definition='axialZ mm',native_resolution=[352,640],depth_interpolation=0,C=r['C'],K=r['K'],native_pixel_N=c['native_pixels'],original_face_N=c['original_faces'],state_counts=c['state_counts'],area_mm2=c['area_mm2'],trusted_native_N=c['trusted_native_observations'],official_checkpoint_SHA=env['HERO']['checkpoint_SHA256'],actual_3D_accuracy='NOT_EVALUABLE'))
 table('MAX_COVERAGE_VIEW_SELECTION.csv',selections);table('VIEW_COUNT_ABLATION.csv',abl);table('HERO_SUPPORT_FRAME_SELECTION.csv',supports);table('NEW_HERO_SOURCE_MANIFEST.csv',hero);save('results/RECOMMENDED_RESEARCH_TARGET_SETS.json',final);table('metrics/FOUR_GROUP_FINAL_SCORECARD.csv',summary);save('metrics/FOUR_GROUP_FINAL_SCORECARD.json',summary)
 # Complete pose arrays and actual solver state in a compact public result.
 save('results/ALL_FINAL_METRIC_CAMERA_POSES.json',[dict(group=v['group'],id=v['id'],video=v['video'],role=v['role'],C=v.get('C'),K=v['K'],status=v['status'],conditional_eligible=v['formal'])for v in pool]);save('results/ACTUAL_CERES_FINAL_STATES.json',[load(N/'registration'/g/(m+('_NATIVE005'if g=='G01'else'')+'_FINAL.json'))for g in GROUPS for m in ['SHARED_SE3','JOINT_FULL6']]);save('results/HISTORICAL_SE3_CANDIDATES.json',load(P/'config/HISTORICAL_CANDIDATES.json'))
 # All figure paths, and algorithm/code-line fidelity index.
 loc=[]
 for p in sorted((N/'code').glob('*.py')):
  for i,line in enumerate(p.read_text().splitlines(),1):
   if line.startswith('def ')or line.startswith('class '):loc.append(dict(file=str(p.relative_to(N)),line=i,definition=line.strip(),sha256=sha(p)))
 table('metrics/CODE_LOCATIONS.csv',loc)
 head='| 组 | 候选 | 条件相机004/005/照片 | 新目标 | 新旧深度差MAE/Median/P95 mm | 共同可比/固定pair像素N |\n| --- | ---: | --- | ---: | --- | --- |\n'
 for s in summary:head+=f"| {s['group']} | {s['candidates']} | {s['formal004']}/{s['formal005']}/{s['formalPHOTO']} | {s['actual_new_HERO_targets']} | {s['new_old_depth_MAE_mm']:.3f}/{s['new_old_depth_median_mm']:.3f}/{s['new_old_depth_p95_mm']:.3f} | {s['known_pair_N']}/{s['fixed_pair_pixel_N']} |\n"
 base='''# TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001

完成四组原始数据发现、相机恢复、条件配准、覆盖选帧、真实HERO推理和独立几何评价。**工程流程完成；未证明新增HERO能直接改善Body输入，不自动提升为主线。**

8段视频全部存在并逐帧解码7650帧；12张同批次照片RGB/Mask核对完成。全时段8Hz网格、端点、014缓存及历史canonical去重后884候选。未对全部7650帧逐一分割/恢复，未处理帧的Mask/Ring资格明确UNKNOWN；不能把884说成全部真实帧或独立方向。

'''+head+'''
“条件相机”是多证据工程资格，不是绝对位姿认证。每张照片K仍为共享内窥镜K的假设。877候选有数值相机，7例无解保留NaN；25留出不进入新目标/支持；550候选满足本轮预登记的组合条件。照片10/12有数值位姿，仅4/12条件入组。

实际完成46个覆盖目标＋1个G06支持图对照，共47次全新官方HERO推理，全部保留原生352×640轴向毫米深度、Raw Mesh与017四类Face标签。没有复用旧深度冒充推理，没有深度插值、补洞、ICP或融合；保留全部来源及失败。

## 科研结论

1. **原始视频确有遗漏方向，但更多帧不等于更多可靠几何。** 选中004-only方向跨度G03约21.86°，004+005约43.54°。照片001有数值RGB支持但对既有代理曲面的新增面积有限；另外两张没有形成正式增益。历史约17.5°来自旧相机/定义，应看同口径重算与真实RGB图，不能混算。
2. **固定已有HERO代理很快饱和。** G01/G03/G05/G06覆盖优先目标实际18/12/8/8；保留历史8/6/8/7原始基线，S20/S28/S36不足时标N/A，不凑数。Body与HERO代理分开，未知背面不计入已恢复面积。同数量E1对E0没有统一收益，差异很小且部分略低。
3. **新HERO增加的面积并不全是可信新增表面。** G03出现大幅错层与片层扩展，深度差P95达16.34mm；这是几何分歧代理，不是GT误差。017内部正常不等于跨来源几何正确。不能将新面积-bin之和称为唯一解剖表面积。
4. **新支持评分没有得到普遍改善证据。** G06固定共同native像素、共同可见集合N=19560，新几何评分三图与原018三图的深度差MAE分别约0.533/0.137mm。原三图与留出HERO可能共享上游RGB，相关性已另列；该比较是独立目标一致性代理，仍非三维真值准确度。
5. **Ceres执行、FIT下降和物理位姿精度应分开。** 完成共享SE(3)及共享XYZ/完整局部6DoF两条候选，只有受控子集89相机参与联合局部更新，其余保留恢复结果并应用来源级变换。共883个RGB地标变量；89/89初始RGB局部Jacobian数值rank6是事后核查，不冒称预登记的rank门禁。71/89相机Ring/RGB梯度方向有冲突。完整6DoF下H与局部修正分解存在冗余规范，原解靠先验正则；交付了锚定首个005局部的等价变换，世界相机保持不变，不能将分解当作唯一真实跨视频SE(3)。
6. **下一阶段仍需人工审核。** 推荐保留18/12/8/8作为冻结研究候选及失败证据；不推荐将它们全部自动送Body。G06优先保留原支持策略作受控参考；G03先诊断来源/支持条件/相机与深度不可分辨性。Body、HERO原资产、相机、CAD和DXY均未修改。

## 实现忠实性

| 原定设计 | 实际实现与边界 | 代码 |
| --- | --- | --- |
| 原始厚Torus与真实弧、Polyp UNKNOWN | 原版image_seeds/decode/solve与V5 Mask区域残差；保留2起点、35nfev固定预算，yaw72相位＋法向双支只用RGB；无无厚度圆替代 | code/cameras.py / code/torus.py |
| 多来源共享SE(3)与成熟BA | 真正PyCeres2.6/Ceres2.2 LM/Schur；005共享变换先跑，再受支持局部6D＋共同XYZ；G03/G05/G06的005初始化依赖004RGB地图，不能称独立005 SfM | code/register.py / code/ceres_backend.py |
| Ring与RGB联合 | 内层为真实typed I/O Torus曲线＋RGB＋先验；**完整V5 Mask区域目标用于外层接受，不是全部直接放进同一个内层Ceres残差**。此差异明确保留 | code/register.py Bundle.objective/build/run |
| 共同地标与去重权重 | 轨迹/视频归一；G01仅真实18跨视频RGB身份合并。其他未知同名点不按XYZ最近邻合并。背景纹理可能占主导，region统计单列 | code/rgb.py / code/native005_extension.py / metrics/RGB_FIT_INLIER_REGIONS.csv |
| 贪心最大覆盖 | 固定FIT-only、非evaluation_only曲面source-tagged surfel并集；0.2mm位置/法向bin；近等增益优先方向，属于epsilon-near-greedy，不声称全局最优；1.5°去重、5°独立方向代理 | code/coverage.py |
| 支持图单独评分 | 实际mutual SIFT＋冻结相机极线3px内点、网格占据、视差与重叠；每目标3图，未按新HERO结果调参 | code/coverage.py support_pairs |
| 原生HERO＋018Mesher | 未改官方网络/权重；沿用mm↔m与K半像素；因本轮禁止插值，将同一个018Mesher直接用于原生352网格，**区别于018先升采样360的接口** | code/infer.py |
| 017冻结分类 | 原函数AST读取，原阈值＋018一次冻结gap规则；只输出原始三角面子集，保留精确原始V、Face/Pixel ID和UNKNOWN | code/clean_native.py |
| 独立评价 | 真实射线首层、CAD前后次序；supported±0.5mm，另报±0.2/1mm；front只是自由空间分歧代理，deeper保留合法自遮挡解释；报告分母、相关性及原始source面积 | code/evaluate_geometry.py / code/lineage.py |

本轮早期实现错误均在新HERO前修复并保留：代理自射线MISS不得计visible；evaluation_only旧005 HERO排除选帧；历史E0不能被重新筛成另一批视角；014留出别名恢复。G01补读原生005地图是输入完整性修复，未改阈值/损失，第一轮004-only结果保留。代码位置和SHA见metrics/CODE_LOCATIONS.csv与provenance。

## Q1–Q10

- Q1：四组两视频均存在；有效条件相机数量见表，G06视频005为0，不能因其存在就宣称几何可用。
- Q2：照片数值10/12，条件性4/12；其余保留弱候选或无解。未认证照片不进入正式HERO。
- Q3：RGB/Ring梯度冲突、弱照片K、背景地图与息肉非刚体/预测深度误差不可完全区分；新HERO分歧证明仍有未解决问题，但不能只凭它反选位姿。
- Q4：G03既有少量004漏选，又有005互补方向；仍集中在单侧范围。新增帧能增加方向，但未证明恢复更多可信长柄侧面。
- Q5：见MAX_COVERAGE_VIEW_SELECTION.csv逐目标边际面积；新增方向与新增真实表面要分开。头/柄/基底没有可靠标注时全部UNKNOWN，未强行分类。
- Q6：完整数量表与真实native结果见VIEW_COUNT_ABLATION.csv、metrics/HERO_COUNT_ACTUAL_COVERAGE.csv；可用不足不会伪造S20/S28/S36。
- Q7：同数量没有稳定优于历史基线的证据；固定代理本来已被旧视角大面积看到，极小差异不能宣传选帧获胜。
- Q8：没有普遍改善证据；G06对照为负。未基于这个结果修改支持图或重新推理挑优。
- Q9：005提供互补方向（尤其G01/G03），照片增益很小或不合格；E5同一合法池比较，实际新表面需看冲突和UNKNOWN，不把数据增加归因于BA算法收益。
- Q10：研究候选18/12/8/8；**本轮不批准直接Body推广**，先人工看完整错层、支持图反例与来源资格。

## 交付与复现

8张核心图、四组六视角图集、局部图及4个可交互HTML已保存。每个GLB保留Ring、B0/B2、独立旧/新HERO、Raw/Unknown等独立对象、相机与轨迹。GLTF米坐标为固定mm→m单位转换，非拟合尺度。浏览器实际加载与UI检查记录见metrics/BROWSER_ATLAS_TESTS.json；大文件获取见REPRODUCE.md及assets_index。

未采用任何三维GT；GT绝对精度、MAPE、直径/高度真值误差一律NOT_EVALUABLE。没有Body训练或曲面融合。

'''+audit_table()
 md('TECHNICAL_REPORT.md',base);md('TECHNICAL_REPORT_SUMMARY.md',base[:base.index('## 实现忠实性')]+'''\n完整算法逐项对照、代码位置、Q1–Q10及失败见[TECHNICAL_REPORT.md](TECHNICAL_REPORT.md)。\n\n核心图：[全部方向](figures/Fig1_All_Candidate_Directions.png)、[G03真实RGB](figures/Fig2_G03_Real_RGB_Directions.png)、[真实HERO对照](figures/Fig4_Actual_HERO_Surface_Sets.png)、[G03冲突](figures/Fig6_G03_Actual_Added_Surface_And_Conflicts.png)。\n\n'''+audit_table())
 source_table='| 组/来源 | 原始帧或照片 | 处理候选 | 数值位姿 | 条件验证 | 留出 |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'+''.join(f"| {r['group']}/{r['source']} | {r['raw_frame_N']} | {r['processed_candidates_N']} | {r['numeric_pose_N']} | {r['validated_conditional_N']} | {r['HOLDOUT_N']} |\n"for r in src)
 md('SOURCE_DISCOVERY_AND_IDENTITY_AUDIT.md', '# 来源审计\n\n'+source_table+'''\n完整7650帧时间戳见metrics/RAW_VIDEO_FRAME_TIMELINE.csv。501新Mask来自同一冻结INIT checkpoint；已有Mask未覆盖。旧local005/ledger005命名不能当video005身份：多组该文件实际绑定video004。本轮检查原始视频路径、SHA、帧绑定。12照片只读使用smart_endoscope_20260805同批原图及Mask，旧20260415同名照片隔离。K490为640×360工作格，照片原K仅假设共享，不是新标定。静态同一息肉身份由采集目录与RGB支持；息肉组织跨视频完全刚体仍为条件假设。未采样帧的Ring/Mask状态UNKNOWN，不将候选检测数量当全部原始视频Ring帧数量。\n\n'''+audit_table())
 md('RING_FIRST_POSE_RECOVERY_AUDIT.md','''# Ring-First恢复\n\n复用原厚Torus R=5.6/r=0.6mm，CAD内径10mm。原始recover.py函数与V5区域、真实typed Inner/Outer弧、Polyp邻接UNKNOWN；RF五维与RGB yaw/法向分支分开。不用HERO/Body恢复相机。物理正深度、properSO(3)、相机不在Torus材料内；正式候选另需空间覆盖、独立描述子留出与Ring质量的组合证据。8/20px等工程边界不代表校准置信区间，未用旧3px单门槛一刀切。弱候选保留。

50项控制/真实Jacobian/单位/HOLDOUT合同测试通过。首次控制点落到图像外，未真正测试selfMISS，修正为图像内三角形外的控制点，初始失败完整保留。没有改变评价阈值。

'''+source_table+'\n'+audit_table())
 md('MULTI_SOURCE_REGISTRATION_REPORT.md','''# 多来源配准\n\n原RF_RGB、共享SE3、JOINT_FULL6以及命名的RoMa/LightGlue历史候选均保留。8个主问题实际调用Ceres；G01补原生005地图另有独立记录。没有预设新BA胜过RoMa。完整6D只在有至少10RGB内点的受控子集释放，事后89/89初始矩阵rank6，不冒称预检查。完整H/局部自由度存在分解规范：以先验正则求解，交付等价首005锚点规范，所有世界相机误差<1e-10。固定局部后共享RGB-Schur rank6也不能证明原始全参数问题绝对可辨识。

原始G03/G05/G06的005通过004真实RGB地图直接PnP定到004，再做共享变换精修；**不是独立恢复两段轨迹后才发现一致**。G01具有153/980两张独立地图和18个真实RGB共名链接。共同XYZ自由度可能吸收相机/轨迹误差，drift和梯度竞争均列出；不按HERO/HOLDOUT选最优路线。内层typedTorus与外层完整Mask目标的差异见主报告。\n\n'''+head+'\n'+audit_table())
 photos=[v for v in pool if v['video']=='PHOTO'];pt='| 照片 | 数值 | 条件入组 | 留出N | 主要原因 |\n| --- | --- | --- | ---: | --- |\n'+''.join(f"| {v['id']} | {'是'if v.get('C')is not None else'NaN'} | {'是'if v['formal']else'否'} | {v.get('RGB_evaluation',{}).get('FEATURE_HELD',{}).get('N',0)} | {','.join(v.get('qualification_reasons',[v['status']]))} |\n"for v in photos)
 md('PHOTO_REGISTRATION_REPORT.md','# 12照片配准\n\n'+pt+'''\nG01三张旧数值位姿是命名历史对照，结果与同图新Ring/RGB评价另存metrics/G01_HISTORICAL_PHOTO_SAME_DATA_EVALUATION.json。没有把历史3–5px残差自动当完全认证，也未仅凭旧3px门槛终止研究。Ring-only yaw未定位的照片只在列表展示，不画入共同世界。仅4张有条件入组资格；是否被最大覆盖选中另由同一规则决定。\n\n'''+audit_table())
 md('VIEW_COVERAGE_METHOD.md','''# 可见覆盖定义\n
固定原018 FIT-only TRUSTED、排除evaluation_only旧005来源；相机先冻结，禁止用HERO校正相机。每个原三角面质心保留source/Original Face ID；0.2mm位置与约30°法向bin，bin面积取各占据来源面积的均值，避免相同来源面积直接相加。该量不是唯一解剖表面积，曲面离散、深度错层、法向噪声会影响bin。Raw Mesh不合并、不改点。

真正可计visible需原Polyp Mask、正深度、自己原生曲面first-hit在0.15mm容差内，且在CAD前方。自射线MISS=UNKNOWN。每个原来源独立自遮挡，不能用冲突来源的最近点当统一表面。Body代理单独评估，Body未观察背面不计恢复。

贪心边际ΔA以固定HERO-bin权重求并集。增益差<0.001总面积视作近等，再偏好方向、质量；不声称严格全局最优。最小目标方向1.5°；8张后，新增面积<0.002总面积且最佳新增方向<5°即饱和，不为凑36保留重复。嵌套顺序保留，历史8/6/8/7集合不被改写。5°独立仅方向代理，不是统计独立：上游RGB DAG另列，相关性敏感性权重未进入选帧或优化。

候选池对已知原生曲面覆盖高不等于未知背面已恢复。新增HERO-bin需独立可见性支持才能解释为几何收益。本轮不以新面积或低loss宣布成功。

'''+audit_table())
 ledger='''# 失败与限制台账

| 项目 | 实际机制与处理 | 证据 |
| --- | --- | --- |
| G01新几何未通过推广 | 方向增多但新旧深度差MAE1.19mm；RGB/Mask合格不代表HERO可靠；保留18来源不改图不反选 | Figure4、HERO_PER_NATIVE_PAIR.csv |
| G03错层与片层扩大 | 新旧共同深度差MAE4.10/P9516.34mm；旧长柄可见，新层不能宣称可信侧面；相机/场景/深度原因尚不可完全区分 | Figure6、G03_Ring_Near_Local_Detail.png |
| G05弱005与照片 | 005仅2个条件相机，1张照片条件通过；新预测仍有约0.96mm差，不能直接拼接 | ALL_CAMERA_CANDIDATES.csv、Figure7 |
| G06新支持策略反例 | 同一目标/相机及共同19560观测对，几何评分三图差0.533mm，原三图0.137mm；可能共享上游RGB，不能作GT胜负 | E4_FIXED_COMMON_NATIVE_PIXEL_COMPARISON.json |
| 数值相机无解7例/弱候选 | 逐候选NaN/特征少/独立误差偏高/Ring不足，非缺失整组；全部保留 | metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv |
| 12照片未全部可用 | 数值10/12、条件4/12；照片K假设、yaw多解、观测弱。未定位不合入世界 | PHOTO_REGISTRATION_REPORT.md |
| 第一次覆盖实现失败 | selfMISS误计visible；evaluation_only旧005误入代理；E0误取重筛子集。新HERO前修复，第一轮selection/保留供诊断而非结论 | config/VISIBILITY_FIX.json、selection_verified/ |
| G01初轮遗漏005地图 | 004-only初始化漏用既有980005真实地标；单独扩充输入，同阈值/目标，旧预测不覆盖 | native005_extension.py、registration/G01/NATIVE005_EXTENSION |
| 014留出别名 | 初始新raw池未继承全部UPDATE_HOLDOUT；复核无一参与共享BA。恢复25留出；单图诊断不作独立留出pose，评估改用旧冻结相机＋共享H | provenance/PROTECTED_014_ALIAS_REPAIR.json |
| 005留出地图坐标 | 非共名005留出点需随H动，真实共名004点固定；纠正后正式成员变化0，不换位姿 | metrics/G01_HELD_MAP_GAUGE_CORRECTION.json |
| Ceres完整目标差异 | 内层typed I/O＋RGB，V5完整Mask区域是外层接受目标；不能冒称原020所有残差都在内层。少数内层到预算NO_CONVERGENCE，不称充分收敛 | register.py、optimization/ |
| H/local规范 | 完整6D分解有冗余，靠先验；等价规范化不改预测，不能把Schur条件rank当绝对位姿认证 | EXACT_SOURCE_GAUGE_CANONICALIZATION.json |
| 预检查与事后rank | 10内点为实际前置；89/89 rank6为冻结后追溯，明确实现差异 | ACTUAL_RELEASED_CAMERA_INITIAL_RANKS.json |
| 研发运行错误 | discover语法/None帧映射、画图语法、控制点越界均有原日志；修复不改科研阈值 | runtime/logs与provenance/CONTROL_FIXTURE_INITIAL_FAILURE.json |
| 未知解剖区和未观测背面 | 不从Body猜头柄基底，不插值补洞，不输出假面积 | Figure5/6及各source UNKNOWN面 |
| 覆盖范围有限 | 完整帧清单7650，但仅884候选实际处理；没有证明两采样时间间隔内绝无遗漏方向 | RAW_VIDEO_FRAME_TIMELINE.csv |
| GT及绝对精度 | 本轮无GT，所有绝对3D精度、MAPE/尺寸真值误差NOT_EVALUABLE | 所有报告固定审计表 |

所有原始资产、旧失败记录和Body只读；没有因失败修改阈值、重复调支持图、删面美化或改相机解释新深度。

'''+audit_table();md('FAILURE_LEDGER.md',ledger)
 md('FOUR_GROUP_FINAL_RESEARCH_DECISION.md','# 四组决策\n\n'+head+'''\n候选推荐18/12/8/8是“有新增方向、可追踪、完成一次官方推理”的研究集合，不是批准全部进入Body训练。四组均已完成，本轮停止。共同结论：已有代理饱和；真实新预测有错层；新支持评分未稳定胜出。优先人工审查G03长柄与片层、G06 E4负例。保持原可信来源及全部新来源分层；不自动融合，不删除未知表面，不更新Body。\n\n下一轮若另行授权，先验证具有足够Polyp信息与稳定几何的支持组合及相机/深度不可辨识问题；不要因本轮结果差就追加重复帧。\n\n'''+audit_table())
 # Mandatory provenance and rendered-frame index.
 table('metrics/FIGURE_INDEX.csv',[dict(file=str(p.relative_to(N)),bytes=p.stat().st_size,sha256=sha(p),role='scientific true-mesh or realRGB figure')for p in sorted((N/'figures').glob('*.png'))]);save('results/FINAL_INDEPENDENT_SUCCESS_AND_FAILURE_COUNTS.json',dict(groups=4,raw_video_frames=7650,independent_photos=12,processed_candidates=884,numeric_cameras=sum(v.get('C')is not None for v in pool),conditional_eligible=sum(v['formal']for v in pool),protected_HOLDOUT=sum(v['role']=='HOLDOUT'for v in pool),numeric_failures=sum(v.get('C')is None for v in pool),new_inferences=len(inf),new_inference_successes=sum(r['success']for r in inf),historical_measurement_fallback=0,old_depth_reprojected_as_new=0,GT_used=False,automatic_Body_promotion=False))
 print('REPORTS_AND_TABLES_DONE',len(flat),'cameras',len(hero),'actualHERO',flush=True)
if __name__=='__main__':main()
