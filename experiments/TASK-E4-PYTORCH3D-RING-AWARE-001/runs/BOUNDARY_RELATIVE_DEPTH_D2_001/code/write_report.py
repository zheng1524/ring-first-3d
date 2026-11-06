from common import *

def main():
 cfg=load(R/'config/PROTOCOL.json');end=load(R/'metrics/ENDPOINTS.json');ex=load(R/'metrics/EXACT_GEOMETRY.json');bv=load(R/'metrics/BLENDER_CHECKS.json');sh=load(R/'metrics/SHAPE.json');gr=load(R/'metrics/PREFLIGHT.json');solidgt=load(R/'metrics/NATIVE_GT_SOLID_AUDIT.json');run=[];paired=[]
 def get(c,a):return next(x for x in end if x['case']==c and x['arm']==a)
 for c in cfg['cases']:
  for a in cfg['arms']:
   x=load(R/'metrics'/(c+'_'+a+'_RUN.json'));run.append(dict(case=c,arm=a,status=x['status'],optimizer_steps=x['optimizer_steps'],new_optimizer_steps=0 if c in cfg['reuse_B']and a=='B'else x['optimizer_steps'],elapsed_seconds=x.get('elapsed_seconds'),peak_GPU_bytes=x.get('peak_GPU_bytes')))
  for aa,bb in[('E1','B'),('E2','E1'),('E3','E2')]:
   a,b=get(c,aa),get(c,bb);paired.append(dict(case=c,comparison=aa+' minus '+bb,depth_kind='IDEAL_GT_DEPTH_UPPER_BOUND'if c.startswith('virtual')else'HERO_NATIVE',holdout_IoU_delta=a['holdout_IoU']-b['holdout_IoU'],holdout_depth_MAE_delta_mm=a['holdout_depth_MAE_mm']-b['holdout_depth_MAE_mm'],holdout_depth_hit_rate_delta=a['holdout_depth_hit_rate']-b['holdout_depth_hit_rate'],holdout_fixed_cost_delta=a['holdout_fixed_depth_cost']-b['holdout_fixed_depth_cost'],holdout_Mask_coverage_delta=a['holdout_coverage']-b['holdout_coverage'],Chamfer_delta_mm=a['Chamfer_MAE_mm']-b['Chamfer_MAE_mm']if c.startswith('virtual')else None,Ring_penetration_delta_mm=a['Ring_penetration_max_mm']-b['Ring_penetration_max_mm'],coverage_decreased=a['holdout_coverage']<b['holdout_coverage'],geometry_gate=a['geometry_gate'],multiview_HERO_used_for_ranking=False))
 table('metrics/RUNS.csv',run);table('metrics/PAIRED_COMPARISONS.csv',paired)
 total=sum(x['geometry_gate']for x in end if x['arm']!='P0');lines=['# TASK-E4-D2 技术报告','',f'完成六病例、四条件，每条件固定300步：22条新运行共6600次optimizer.step，另2条B直接复用历史冻结输出。24/24数值输出，{total}/24通过本轮网格几何门槛（仅G01的E1/E2/E3）。GT、留出和跨视角HERO诊断均未用于选checkpoint。结论为 **MIXED：绝对深度提供可复现的观测收益；边界权重与相对深度没有建立跨形态统一收益，当前流程不能作为已验收的统一重建方法。**','',
 '## 核心结论','',
 '1. **E1相对B有一致的深度观测收益，但几何收益有限。** 三个虚拟病例的参考CAD Chamfer均下降，三个真实病例的留出HERO误差均下降。G01的E1/E2/E3消除了旧B的微小穿环，保持约96%的P0净体积；这只说明网格约束门槛通过，真实三维准确度仍NOT_EVALUABLE。全部虚拟输出继续自交；G06/G07仍穿环。',
 '2. **E2不能认定统一优于E1。** 虚拟IIa/Ip的相交候选面数减少（93→72、277→148），但三个虚拟Chamfer均小幅变差；真实G06穿透从.253降至.200mm、G07从.562降至.535mm，仍然失败。G01留出HERO MAE .622→.635mm，G07 .774→.784mm。边界降权缓和了部分风险，却也弱化有效约束；本轮无边界深度真值，不能将“边界距离”宣称为已校准可靠概率。',
 '3. **E3不是跨形态稳定改进。** 相对E2，虚拟Ip/IIa Chamfer .597→.576、.269→.266mm；虚拟Is却1.588→1.614mm且穿透.304→.392mm，真实G07新增9对自交。G06/G07条件命中MAE微降但固定分母成本上升、命中率下降，不能宣布深度覆盖改善。',
 '4. **IIa的局部曲面距离改善不等于完整隆起恢复。** B/E1/E2/E3 Chamfer为.298/.267/.269/.266mm；最大Z高度为1.888/1.817/1.804/1.881mm，独立Blender为1.430mm。E3曲面平均距离略好而高度误差比E2更大；尖刺和底部错误没有解决。',
 '5. **保留E1作为下一次受控研究的观测基准，E2为候选；不推广当前E3。** 先处理已知初始穿环、局部网格折叠和未知底面的不可辨识性，再谈扩大自由度。没有证据仅靠更换SDFStudio/BundleSDF就能解决这些问题，本轮未部署或扩展。','',
 '## 病例与资格','',
 '| 病例 | FIT | UPDATE_HOLDOUT | 入组限制 |','|---|---|---|---|']
 for c in cfg['cases']:
  m=getcase(c);lines.append('|'+c+'|'+'/'.join(v['id'].split('_')[-1]for v in m['views']if v['role']=='FIT')+'|'+'/'.join(v['id'].split('_')[-1]for v in m['views']if v['role']!='FIT')+'|'+('已知Blender相机；理想深度上限'if c.startswith('virtual')else'; '.join(v['id']+':'+v['qualification']for v in m['views']))+'|')
 lines+=['','G07采用最新审查，不沿用旧E3-A不合格结论：ref04/r02为CONDITIONAL_USABLE，new_r06为INSUFFICIENT_EVIDENCE但被许可条件性研究使用。G06拟合r01/r03为CONDITIONAL_USABLE，留出r06条件性。G01资格仍INSUFFICIENT_EVIDENCE。留出只针对本轮更新，不是未参与历史P0的独立验证。G07两个FIT均属B1分区，不能称互补独立视角；本轮未因结果替换。各病例坐标完全隔离。','',
 '## 固定最终结果','',
 '以下深度MAE只针对实际命中；必须与覆盖和固定分母成本一起读。虚拟理想深度与真实HERO不混合汇总。Chamfer来自独立原生Blender参考曲面，不是完整物理准确度认证。','',
 '| 病例/条件 | FIT IoU | HOLD IoU | 深度MAE FIT/HOLD mm | HOLD深度命中率 | HOLD固定深度成本 | GT Chamfer MAE mm | Ring穿透 mm | 自交候选对 | 几何门槛 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
 for c in cfg['cases']:
  for a in cfg['arms']:
   x=get(c,a);b=next(y for y in bv if y['case']==c and y['arm']==a and y['step']==300);ch='NOT_EVALUABLE'if x['Chamfer_MAE_mm']is None else f"{x['Chamfer_MAE_mm']:.4f}";lines.append(f"|{c}/{a}|{x['fit_IoU']:.4f}|{x['holdout_IoU']:.4f}|{x['fit_depth_MAE_mm']:.4f}/{x['holdout_depth_MAE_mm']:.4f}|{x['holdout_depth_hit_rate']:.4f}|{x['holdout_fixed_depth_cost']:.4f}|{ch}|{x['Ring_penetration_max_mm']:.4f}|{b['self_pair_N']}|{'PASS_GEOMETRY_ONLY'if x['geometry_gate']else'FAIL'}|")
 lines+=['','完整逐参考MAE、中位绝对误差、p95、最大误差及命中/未命中数见`metrics/DEPTH_EVALUATION.csv`；Chamfer median/MAE/p95/max见`ALL_GEOMETRY_WITH_VALIDITY.json`；共同成功病例的配对变化见`PAIRED_COMPARISONS.csv`。本轮不产生直径预测，直径中位绝对相对误差NOT_EVALUABLE，不用曲面距离冒充直径误差。','',
 '## 边界、覆盖与机制','',
 'E1/E2/E3深度候选ID完全相同；边界权重不改变轮廓证据、不使用跨视角HERO筛选。权重总和与有效样本数见WEIGHTS_SUMMARY，逐像素见OBSERVATION_ID_WEIGHT_AUDIT。相对点对仅来自单视角可靠内部，路径不跨Ring/明确断裂，固定多尺度、固定分母。绝对和相对梯度均通过完整顶点有限差分、共同偏移不变性和差分变化响应；没有更换z-buffer梯度。','',
 '固定pre-step50机制快照：IIa/G01/G07轮廓与绝对深度梯度全局cos约−.091/−.104/−.116；共同非零顶点中支持/冲突分别431/1394、113/153、114/174。图B/C的箭头来自实际autograd数组，最后一列真实SGD位移包含动量与先验，不能把它归因于一个loss。此处只验证梯度冲突存在，不能仅凭梯度方向判定哪个观测正确。','',
 'E3相对E2：G06留出深度命中率.96094→.95898，固定成本.4373→.4552；G07 .89648→.89453，成本1.9488→1.9632，虽然条件MAE略降仍记为潜在覆盖退化。G01 Mask留出覆盖.91757→.91634亦下降（精确数值见表）。没有以删除射线或平均深度下降制造PASS。','',
 '## 虚拟GT与实体指标限制','',
 'Blender原生Ip/Is通过相机/Mask重投影，但原Mesh各有67/3对非邻接相交，FCL逐对确认；未修补或替换源GT。IIa原生GT无此问题。三类虚拟预测均自交，故全部最终的严格实体体积误差、差异体积为NOT_EVALUABLE；原始占据积分只能称诊断代理，不能用P0体积作GT。部分GT/预测超出继承的P0积分域，必须保留域截断标记，不能把局部积分称全体积。','',
 '顶/侧/底曲面误差、最大高度与截面曲线已保存。截面采用原三角面-平面交线，闭环鞋带公式与奇偶嵌套面积，解析立方体1/2/3mm测试通过；自交GT/预测只能称参考面积代理，未生成新的表面。真实Is/IIa无可靠基准面，准确隆起高度和真实体积均NOT_EVALUABLE。','',
 '旧C/D只做非同条件历史审阅：C/D最大高度1.705/1.617mm较GT1.430mm近于旧B1.888mm，但Chamfer .353/.312mm比B .298mm更差，底部最低Z −.961/−1.011mm（GT=0）。视觉更像隆起不代表整体三维更真；不能将旧C/D当本轮E1/E2/E3同条件对照。见HISTORICAL_C_D_ONLY。','',
 '## 失败归因与边界','',
 '- 虚拟三例：同一细密DMTet P0拓扑与自由顶点轮廓梯度继续产生折叠/尖刺；深度降低部分表面距离，未解决局部可行性。Is的Ring-only初始主体与原生GT相差较大，不能将此单次失败归因于“Is不适合深度”。',
 '- 真实G01：E1/E2/E3通过有限网格门槛，但仍有约4%净体积下降、部分指标与覆盖互有取舍；相机证据不足、HERO相关性/偏差和未观测底面仍限制准确性结论。',
 '- 真实G06/G07：旧P0已穿Ring（.087/.541mm），继续使用相同P0是本轮公平性要求；无新增碰撞loss的深度消融不能解决全部物理冲突。G07 E3额外产生自交，不能保留为有效主线。',
 '- 单视角相对深度不增加独立相机约束，且不能单独确定公制偏移/不可见底面；保留绝对项仍不能保证隐藏表面真实。',
 '- 多视角HERO只读诊断严格晚于预测冻结，输出NEAR/FRONT/BEHIND/CAD_OCCLUDED/UNKNOWN代理，不用于loss/权重/停训/排名，报告不以其共识票数宣称几何真值。','',
 '## 实现修复记录','',
 '未重跑、未调整任何优化权重或步数。后评价有两次工程问题：①验证器误假定全部Ring为R10；G07原始来源明确R5（内径5mm），其余内径10mm，毫米尺度与CAD均未更改，修正为逐来源身份校验。保留原错误验证脚本/日志。预注册中“内径10mm”表述不适用于G07，此处勘误，不回写冻结文件。②Trimesh截面多边形面积依赖未安装Shapely，首版部分缺失、无交线切片为0，初图不能用于判断；保留首版表/图，改用同一原Mesh交线的独立闭环面积算子，并通过解析控制检验，不安装新框架、不改预测。其余GT/输入问题全部保留。','',
 '## 固定审计表','',
 '| 审计项目 | 必须汇报 |','|---|---|','| 目标组数 | 6独立场景：3虚拟+3真实；每组4条件，共24条件 |','| 本算法独立成功 | 新E1/E2/E3每条件6/6产生数值结果；B 6/6其中2条历史冻结对照复用、4条新运行；不可冒称全部24条新计算 |',f'| 本算法失败 | 数值硬失败0；最终几何{24-total}/24失败，详见逐病例表和FAILURE_LEDGER；真实GT及无效实体体积NaN/NOT_EVALUABLE |','| 历史测量值回退 | 0；已有P0与明确冻结B对照不是新预测回退，没有融合其他路线输出 |','| 失败组及具体原因 | 三虚拟折叠；G06/G07初始及最终穿环，G07E3新增自交；图A/full对应病例与FAILURE_LEDGER逐组链接 |','| 最终统计样本 | 数值全分母6场景/24条件；三虚拟GT曲面统计独立报告，真实HERO代理独立报告；几何通过3/24仅G01 E1/E2/E3，不是三维测量正确率 |','| 是否使用GT选择算法 | 否；预注册0d14669与PREOPT_FREEZE，固定step300，预测先冻结后做3D评价；虚拟理想深度仅事先声明的授权例外 |','',
 '## 交付索引','',
 '- `METHOD_AND_LOSS_AUDIT.md`：损失与梯度契约；`REPRODUCE.md`：源路径、环境与命令。',
 '- `metrics/ENDPOINTS.csv`、`SUMMARY.csv`：最终及50/100/200/300；全部0/25/50/75/100/150/200/250/300检查点另保留本地。',
 '- `figures/FigA_Six_Case_Final_Comparison.png`：六病例P0/B/E1/E2/E3；`figures/full/FigA_{case}_Evolution.png`逐条件0/50/100/200/300。',
 '- `figures/FigB_Contour_Gradient_Actual_Update.png`、`FigC_Depth_Weights_Pairs_Gradients.png`：实际计算机制。',
 '- `figures/FigD_Virtual_GT_Surface_And_Height.png`：三类GT曲面、隆起高度、截面代理。',
 '- `local_results/{case}/{arm}/FINAL_mm.ply`、同名NPZ及STEP_*.pt：原始模型和完整可迁移状态；`assets_index/LOCAL_RESULTS.json`索引本地大型输出，不上传权重/视频/原模型。','',
 '**本轮已停止。保留候选证据，等待人工审查；不自动扩大自由度、转移框架、修正相机或开展新的配准实验。**','']
 (R/'TECHNICAL_REPORT.md').write_text('\n'.join(lines))
 failures=['# D2 失败记录','', '| 病例 | 失败与限制 | 证据 |','|---|---|---|',
 '| virtual_IIa | B/E1/E2/E3自交21/93/72/94对；Chamfer改善未消除尖刺，高度仍高于GT | [阶段网格](figures/full/FigA_virtual_IIa_Evolution.png)、BLENDER_CHECKS、EXACT_GEOMETRY、VIRTUAL_SHAPE |',
 '| virtual_Ip | 原GT非邻接相交67对；所有预测自交，E1至少256对已确认（候选277），不能报告有效实体体积 | [阶段网格](figures/full/FigA_virtual_Ip_Evolution.png)、NATIVE_GT_SOLID_AUDIT |',
 '| virtual_Is | 原GT相交3对；P0欠表达；全部最终穿环并大量自交；E3比E2 Chamfer更差 | [阶段网格](figures/full/FigA_virtual_Is_Evolution.png)、FigD、EXACT_GEOMETRY |',
 '| real_Ip | B微小穿环；E1/E2/E3几何门槛通过但无完整GT、相机仍INSUFFICIENT_EVIDENCE，E2/E3不统一优于E1 | [阶段网格](figures/full/FigA_real_Ip_Evolution.png)、ENDPOINTS |',
 '| real_IIa | 原P0穿环.087mm；B/E1/E2/E3均未消除，深度方案到.198–.253mm；E3命中率下降 | [阶段网格](figures/full/FigA_real_IIa_Evolution.png)、DEPTH_EVALUATION |',
 '| real_Is | 原P0穿环.541mm，全部条件仍穿环，E3新增9对自交；留出相机条件性不足 | [阶段网格](figures/full/FigA_real_Is_Evolution.png)、CASE_LOCK、EXACT_GEOMETRY |','',
 '工程问题：','',
 '- SCALE_VALIDATOR_V1：后验验证器错误地把G07 R5当R10。来源清楚，实际CAD内径4.999999mm，与来源R5一致。仅纠正验证契约，不改相机/CAD/尺度/预测。保留assets_index/VALIDATE_V1_ASSUMED_ALL_R10.py.txt和runtime/VALIDATE_V1_ALL_R10_ASSUMPTION_FAILED.log。',
 '- SECTION_DEPENDENCY_V1：Trimesh polygons_full缺Shapely，初版截面积为缺失/无交线0，不能解读为全零面积。保留assets_index/V1_SECTION_DEPENDENCY_FAILED_*；使用同原Mesh的闭环交线鞋带公式替代评价依赖，SECTION_OPERATOR_AUDIT含解析控制。未重跑优化。',
 '- 评估阶段未命中射线的inf-inf会发出RuntimeWarning；只在pair两端有效时统计，固定缺失代价保留，未将NaN用于训练。训练全过程无非有限梯度/损失停机。',
 '- 原生虚拟Ip/Is实体GT未通过，无效实体指标NOT_EVALUABLE；没有更换病例或修补GT制造成功。三维表面距离仅对原参考曲面可定义。','',
 '保留所有固定检查点，不删除面，不修补，不选中间最佳轮次，不增加调参或扩展任务。','']
 (R/'FAILURE_LEDGER.md').write_text('\n'.join(failures))
 save('metrics/RESULT.json',dict(status='COMPLETED_FIXED_SIX_CASE_PILOT_MIXED_GEOMETRY_FAILURES',case_N=6,arm_N=24,numerical_output_N=24,new_runs=22,reused_B=2,new_optimizer_steps=6600,geometry_gate_pass_N=total,geometry_gate_fail_N=24-total,absolute_3D_real_accuracy='NOT_EVALUABLE',virtual_final_valid_solid_N=0,E1='consistent observation-depth improvement, limited geometric validity',E2='MIXED_NOT_UNIVERSAL',E3='MIXED_WITH_COVERAGE_AND_GEOMETRY_FAILURES',stop=True,expand_framework=False,GT_model_selection=False,multiview_HERO_in_optimizer=False))
 print('REPORTS_WRITTEN')
if __name__=='__main__':main()
