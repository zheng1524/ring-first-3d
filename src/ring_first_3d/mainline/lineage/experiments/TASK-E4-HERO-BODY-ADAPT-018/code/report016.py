"""Measured paired results and explicit causal claims; never selects models by GT."""
from common import *
from collections import Counter
from safe_geometry import dense_face_distance
import ast

def main():
 native=load(R/'metrics/NATIVE_AND_GEOMETRY.json');gt=load(R/'metrics/GT_COMPARISONS.json');virtual=load(R/'metrics/VIRTUAL_GT_COMPARISONS.json');audit=load(R/'metrics/VIEW_SAMPLING_AUDIT.json');reg=load(R/'config/RUN_REGISTRY.json');cases=load(R/'config/CASE_LOCK.json');nr={(x['case'],x['tag']):x for x in native};gr={(x['case'],x['tag']):x for x in gt};pairs=[]
 for c in cases:
  n=c['name'];a,b=nr[n,'S0_015'],nr[n,'S1_BALANCED'];ga,gb=gr[n,'S0_015'],gr[n,'S1_BALANCED'];va=next(x for x in audit if x['case']==n);pairs.append(dict(case=n,morphology=c['morphology'],old_views=va['old']['N'],new_views=va['balanced']['N'],old_span_deg=va['old']['max_span_deg'],new_span_deg=va['balanced']['max_span_deg'],old_HOLDOUT_IoU=a['HOLDOUT']['IoU'],new_HOLDOUT_IoU=b['HOLDOUT']['IoU'],HOLDOUT_delta=b['HOLDOUT']['IoU']-a['HOLDOUT']['IoU'],old_commonFIT_IoU=a['FIT_common']['IoU'],new_commonFIT_IoU=b['FIT_common']['IoU'],old_Chamfer_mm=ga['Chamfer_MAE_mm'],new_Chamfer_mm=gb['Chamfer_MAE_mm'],Chamfer_delta_mm=gb['Chamfer_MAE_mm']-ga['Chamfer_MAE_mm'],old_Dxy_AE_mm=ga['Dxy_AE_mm'],new_Dxy_AE_mm=gb['Dxy_AE_mm'],old_fixed_HERO_hit=a['depth']['hit_rate'],new_fixed_HERO_hit=b['depth']['hit_rate'],new_vs_initial_HERO_coverage_decreased=b['coverage_decreased'],Ring64_mm=b['geometry']['Ring_dense64_penetration_mm'],self_N=b['geometry']['self_intersections_N'],accepted=b['run']['accepted'],attempts=b['run']['attempts']))
 save('metrics/SAMPLING_PAIRED_COMPARISON.json',pairs);table('metrics/SAMPLING_PAIRED_COMPARISON.csv',pairs)
 summary=dict(target_real_groups=11,new_real_models=13,new_virtual_models=3,reused_baseline_models=13,sampling_HOLDOUT_improved_N=sum(x['HOLDOUT_delta']>0 for x in pairs),sampling_GT_Chamfer_improved_N=sum(x['Chamfer_delta_mm']<0 for x in pairs),sampling_old_mean_Chamfer_mm=float(np.mean([x['old_Chamfer_mm']for x in pairs])),sampling_new_mean_Chamfer_mm=float(np.mean([x['new_Chamfer_mm']for x in pairs])),sampling_coverage_decreased_N=sum(bool(x['new_vs_initial_HERO_coverage_decreased'])for x in pairs),new_route_history_fallback_N=0,GT_used_for_selection=False)
 summary['sampling_coverage_lower_than_S0_N']=sum(x['new_fixed_HERO_hit']<x['old_fixed_HERO_hit']-1e-12 for x in pairs)
 save('metrics/RESULT_SUMMARY.json',summary)
 groupstats=[]
 for t in ['S0_015','S1_BALANCED','MECH_015_B','MECH_COHERENT']:
  rr=[x for x in gt if x['tag']==t];groupstats.append(dict(tag=t,target_N=11 if t.startswith('S')else 2,evaluable_N=len(rr),Dxy_AE_mm=stats([x['Dxy_AE_mm']for x in rr]),median_absolute_relative_error=float(np.median([x['Dxy_relative_error']for x in rr])),Chamfer_MAE_across_cases_mm=stats([x['Chamfer_MAE_mm']for x in rr])))
 save('metrics/GT_ROUTE_SUMMARIES.json',groupstats);table('metrics/GT_ROUTE_SUMMARIES.csv',groupstats)
 init_cache={};geo=[]
 for x in native:
  p=x['initial_source']['path'];n=x['case'];rg=np.load(R/'inputs'/n/'RING.npz');s=scene(rg['V'],rg['F']);z=np.load(x['source']['path']);key=(n,p)
  if key not in init_cache:
   a=np.load(p);init_cache[key]=dense_face_distance(s,a['V'],a['F_solid'],rg['V'],64,rg['F'])
  before=init_cache[key];after=dense_face_distance(s,z['V'],z['F_solid'],rg['V'],64,rg['F']);geo.append(dict(case=n,tag=x['tag'],new_face_penetration_N=int(((before>=0)&(after< -1e-5)).sum()),existing_penetration_worsened_face_N=int(((before<0)&(after<before-1e-5)).sum()),penetration_improved_face_N=int(((before<0)&(after>before+1e-5)).sum()),initial_dense64_penetration_mm=max(0.,float(-before.min())),final_dense64_penetration_mm=max(0.,float(-after.min())),comparison='same material face/barycentric sampling; independent64 vs original32guard, epsilon1e-5mm',self_N=x['geometry']['self_intersections_N']))
 save('metrics/INDEPENDENT_RING64_CHANGE.json',geo);table('metrics/INDEPENDENT_RING64_CHANGE.csv',geo)
 causal=load(R/'arms/DIAGNOSTIC/metrics/G03_CAUSAL_SUMMARY.json');binning=load(R/'arms/DIAGNOSTIC/metrics/G02_BINNING_CONTROL.json');safety=load(R/'arms/DIAGNOSTIC/metrics/G03_SHADOW_UPDATES.json');shadow=next(x for x in safety if x['direction']=='FULL'and x['mode']=='CONTACT_FACE_FIXED'and x['alpha']==1.)
 lines=['# TECHNICAL_REPORT_SUMMARY','','TASK-E4-UPDATE-CAUSALITY-016；分支 `exp/TASK-E4-UPDATE-CAUSALITY-016`；继承015提交 `905e2a9`。11个独立真实物理组，13条新真实更新、3条单一虚拟Ip场景控制。13条015输出是明确标识的只读对照，没有重新训练或冒充新结果。','',
 '## 核心答案','','**错误更新有三条已分离的来源：轮廓最近边对应不保证三维同物点、候选/参数支持范围不完整、以及整向量更新把局部危险位移和其他可行位移捆绑。另发现G02粗分箱光栅化的前向片元状态不稳定。** 新提案机制改善了局部可行性和部分指标，但仍没有恢复可信长柄，不升级正式主线。','',
 '1. **不是缺少梯度就一定没有更新。** G03的42个远轮廓关联顶点中，旧四条局部候选带覆盖0；Stalk-C局部表达仅支持13，余29点的局部Jacobian严格为零。silhouette的有限光栅支持不会在远处缺失像素凭空生成顶点；最近轮廓距离把信号传给当前轮廓边，那里也未必是同一解剖部位。','',
 '2. **存在被整网格方向捆绑阻塞的可行下降。** G03全梯度0.2mm影子提案降低完整目标，却触发RING_WORSENING和RING_CONTAINMENT_WORSENING；固定接触面坐标后，仍降低完整目标 %.8f，完整Guard通过。最坏CAD见证点的主要内向贡献来自HERO绝对深度，而不是轮廓项。Ring门禁阻止局部危险位移是合理的；把其余顶点一起放弃则损失了可行方向。这里证明的是几何可行下降，不是有GT认证的正确形状。'%shadow['full_objective_change'],'',
 '3. **三角翼并非仅靠更新平滑就会消失。** 015-B优先把图像梯度应用到远轮廓关联带，全目标下降和无自交不约束它必须形成管状柄。新接触固定+Sobolev方案仍得到片状突出。G03的整个单视频候选池方向跨度也只有17.5449°，重新均衡不能生成缺失方向。逐顶点3×3的“满秩”不能代替耦合形变可辨识性，更不能认证最近边对应正确。','',
 '4. **G02加法异常已定位到粗分箱片元选择。** 同一前向图内加法约1e-7；复用片元后全梯度重复约2.7e-8；冻结Ring可见性或权重无效。相同顶点的默认粗分箱可在一个像素更换面ID、重选重心及距离，silhouette梯度重复相差 %.6f；官方bin_size=0降至 %.3g。受控CuBLAS工作区没有消除粗分箱现象，不能把它归因于一般矩阵乘或形状先验。015的FAIL保留；本轮真实更新仍沿用原后端，防止把数值后端修正混入采样/提案对照。'%(binning['summary']['DEFAULT_COARSE'],binning['summary']['NAIVE_BIN0']),'',
 '## 原定算法与实际实现','','| 任务合同 | 实际实现/代码位置 | 一致性与限制 |','|---|---|---|',
 '| 单视频分区均衡 | prepare016.py:weights/coverage/main；multiview.py:weights | 复用已有方向分区，最小配额+区内角度/时间/质量，保留HERO锚点；不是时间分区 |',
 '| 分量→顶点→候选完整记录 | tape.py:view_terms/instrument/observability；actual_trace016.py:main | 逐视角原face/edge/vertex、实际attempt和ramp；梯度与Adam位移分开 |',
 '| Ring物理约束保留 | safe_geometry.py:GeometryGuard.inspect；ring_audit016.py | 原32阶+FCL+反向包含+自交保留，独立64复核；已有穿入不包装成无碰撞 |',
 '| 依据诊断改进顶点提案 | coherent016.py:coherent_directions；train016.py:main | Dirichlet接触面零位移+稀疏图Sobolev求解；没有实现ARAP，也不是完整非凸可行域投影 |',
 '| 可观测性 | tape.py:observability；coupled_observability016.py | 逐点与耦合轮廓Jacobian均保存；没有将未校准秩代理加入损失或数据筛选 |',
 '| 虚拟控制 | virtual_prepare016.py、render_virtual_grid016.py、virtual_grid_case016.py | 现有Ip4_R10，同GT/CAD/相机；修复320像素中心目标缓存，原失败和原始Mask保留 |',
 '| 独立评价 | evaluate016.py；best_rigid015.py:align/feret | 原公制观察指标；真实GT全部预测冻结后，同015的96起点/8细化、scale1 SE3 |','',
 '提案算子：接触面由当前CAD距离<0.02mm定义，其顶点位移置零；自由顶点解 `(I+L/median_degree)d=d_raw`，lambda=1；再按原提案最大毫米步长归一。原损失、相对边长/Laplacian、法向项、HERO权重和完整接受门禁不变。原始法向点积限制是相对初始方向的代理，不等于真实翻面的充要条件；本轮没有证明可以直接删除这一门禁。','',
 '## 视角均衡结果','','015所有实际FIT均有direction_block，默认分区坍缩实际发生数为0；权重原本按区块等质量计算。修复的是选帧配额与区内近重复。原HOLDOUT全部保护。G03/G04/G06新方案只有6/6/7帧，其余8帧，未用邻帧凑数。HERO源ID及原生样本完全相同；**实际每源256条缓存射线，不是4096**。缺少原始帧号的记录不编造时间。','',
 '| 病例 | 原/新视角数 | 方向跨度°原→新 | HOLDOUT IoU原→新 | ICP后CD mm原→新 | 新S1实际接受/提案 |','|---|---:|---|---|---|']
 for x in pairs:lines.append('|%s|%d/%d|%.2f→%.2f|%.4f→%.4f|%.4f→%.4f|%d/%d|'%(x['case'],x['old_views'],x['new_views'],x['old_span_deg'],x['new_span_deg'],x['old_HOLDOUT_IoU'],x['new_HOLDOUT_IoU'],x['old_Chamfer_mm'],x['new_Chamfer_mm'],x['accepted'],x['attempts']))
 lines+=['','HOLDOUT改善%d/11，GT Chamfer改善%d/11；跨组CD均值 %.4f→%.4fmm。结果为MIXED，不能将时间分散、方向跨度、区块质量和真实三维改善混为一谈。三个不足8帧的病例还改变了观测量，未声称纯等帧数角度消融。'%(summary['sampling_HOLDOUT_improved_N'],summary['sampling_GT_Chamfer_improved_N'],summary['sampling_old_mean_Chamfer_mm'],summary['sampling_new_mean_Chamfer_mm']),'','## 独立提案机制对照','','这两例固定旧8FIT，保持相同初始化、HERO和HOLDOUT；不把采样收益算进新算法。','', '| 病例/方法 | HOLDOUT IoU | GT CD mm | 最大累计位移mm | Ring64穿入mm | 接受/提案 |','|---|---:|---:|---:|---:|---:|']
 for n in ['G03','G01']:
  for t in ['MECH_015_B','MECH_COHERENT']:
   x,y=nr[n,t],gr[n,t];lines.append('|%s/%s|%.4f|%.4f|%.4f|%.6f|%d/%d|'%(n,t,x['HOLDOUT']['IoU'],y['Chamfer_MAE_mm'],x['geometry']['maximum_displacement_mm'],x['geometry']['Ring_dense64_penetration_mm'],x['run']['accepted'],x['run']['attempts']))
 lines+=['','新方案两例均40/40接受，但G03仍为扁平翼状结构，最大累计位移反而增加。它证明了局部可行提案能执行、部分条件下GT表面距离下降；未证明恢复合理柄骨架。固定接触面也限制了已有穿入的向外修复，因此下一步应研究允许外移/切向运动的接触可行锥，而不是永久锁定接触顶点。此处只是建议，不追加运行。','',
 '## 虚拟控制与边界','','初始直接投影正确，但640原生二值Mask最近邻缩到320与直接320光心采样不同，原P3D gate IoU约0.9585–0.9694，按原0.97门槛停止且未更新。随后以同一静止Blender几何/CAD/相机直接渲染320目标，原阈值不变，通过0.9938–1.0000；原Mask和失败证据未覆盖。仅虚拟目标缓存适配，真实输入与实验后端不变。GT用于目标Mask生成、投影审计和冻结后评价，没有进入形状先验或优化参数选择。','',
 '| 虚拟条件 | 原/最终Chamfer mm | 已知GT最近表面方向同向比例 | HOLDOUT IoU | 接受更新 |','|---|---:|---:|---:|---:|']
 for v in virtual:
  x=nr['virtual_Ip',v['tag']];lines.append('|%s|%.5f→%.5f|%.3f|%.4f|%d|'%(v['tag'],v['stages'][0]['Chamfer_mm']['MAE'],v['stages'][1]['Chamfer_mm']['MAE'],v['nearest_GT_direction_cosine_positive_fraction'],x['HOLDOUT']['IoU'],x['run']['accepted']))
 lines+=['','仅5次接受的机制探针：互补视角与协同方案的最近表面误差方向代理更好，但CD变化仅微米级，不是长柄成功恢复或充分重建。单视角→三视角同时改变数量与方向，不能当作等帧数的纯角度因果试验。原虚拟Ip GT有自交，严格实体体积/IoU不可评价；最近表面方向也不是作者材料点对应。原生控制未激发明显Ring接触，接触阻塞的直接证据主要来自真实G03影子对照。','',
 '## 必须保留的问题','','- 新S1相对自身初始固定HERO覆盖下降：%d/11；相对S0对照覆盖更低：%d/11。两种比较分开，不能以“自身未下降”掩盖相对基线退化。'%(summary['sampling_coverage_decreased_N'],summary['sampling_coverage_lower_than_S0_N']),
 '- 深度未命中/被CAD截断采用常数9.5，对缺失区域没有直接深度梯度；鲁棒饱和也可能为零，见DEPTH_MISSING_GRADIENT_CAUSES.csv。HERO命中率不是可微覆盖损失。',
 '- 逐点轮廓Jacobian常有3秩，耦合后G03仅277/1926个条件有效方向；这只统计显式轮廓项，未包含全部silhouette/HERO/先验，不冒称整个问题的秩。',
 '- 候选更新的边长/法向门禁、初始低分辨率和缺乏跨视图语义对应仍有影响；未用额外模型竞争给它们分配全部因果份额。',
 '- 初始B/C碰撞源自稀疏CAD软惩罚和“相对各自初值不恶化”继承，不能用零新增标记冒充物理无穿入；独立64结果和全部失败保留。',
 '- 真实ICP结果统一标注 After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment，只评价形状；没有部署GT固定标定，不报告绝对定位真值。','',
 '## 保留、修改与淘汰建议','','保留真实多视角、固定观测分母、Ring实体门禁、分量/提案状态追踪。修改整向量一票否决为局部可行提案；梯度审计复用同一前向状态，并另测光栅化重入稳定性。新Sobolev提案可作为研究模块保留，暂不作柄部主线。淘汰“接受40步/IoU提高/没有自交即可认定柄部正确”的判断；不再仅扩大旧候选带、增加迭代或沿用未验证单一中心线种子。','',
 '其他视频只提供待认证的观测可能性。本轮未导入跨视频相机或HERO；建议寻找离开当前窄方向簇的新观察；若进一步证实运动近共面，再增加离面观察，先独立验证相机，再考虑共同几何。具体当前方向与缺失角域见VIEW_SELECTION_AND_WEIGHTS、VIEW_SAMPLING_AUDIT；不以帧号均匀代替角度。','',
 '## 固定审计表','','| 审计项目 | 必须汇报 |','|---|---|',
 '| 目标组数 | 11个独立真实物理组；机制对照只2个Ip；另1个虚拟Ip场景的3条件 |',
 '| 本算法独立成功 | S1 11/11数值输出；新机制2/2；虚拟3/3；不等于几何正确 |',
 '| 本算法失败 | 缺模型0；G03柄部仍错误，密集穿入/覆盖退化/原虚拟gate失败完整保留；不可评价量保持NaN/NOT_EVALUABLE |',
 '| 历史测量值回退 | 0；13条旧输出只作为标识明确的评价对照，没有补填新路线 |',
 '| 失败组及具体原因 | FAILURE_LEDGER.md及实际候选、分量梯度、截图、密集CAD表 |',
 '| 最终统计样本 | S1与S0共同11/11；新机制共同2/2；虚拟3条件不合并为三个物理组；Dxy统计MAE/中位ARE/p95/max见GT_ROUTE_SUMMARIES |',
 '| 是否使用GT选择算法 | 否；真实预测/尺度全部冻结后才评价；虚拟例外仅已登记Mask生成和投影/独立评价 |','',
 '## 复现与交付入口','','REPRODUCE.md、RESULT_INDEX.md；四张核心图在figures/Fig1–Fig4，所有世界单位mm。真实原始几何与全部检查点本地保留，review_meshes为精确小型副本。代码、配置、输入、预测SHA及工程修复记录在provenance。参考稀疏求解器为[SciPy splu](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html)，实际方法公式以本报告和代码为准。','',
 '**本轮完成后停止，等待人工审核；不更改DXY、研究章程或正式主线，不启动跨视频融合。**']
 text='\n'.join(lines)+'\n';(R/'TECHNICAL_REPORT_SUMMARY.md').write_text(text);(R/'TECHNICAL_REPORT.md').write_text(text)
 failures=['# FAILURE_LEDGER','','数值输出、几何验收和科学结论分开；不删除失败模型。','','| 病例/条件 | 问题 | 证据 |','|---|---|---|',
 '| G03 / S1及新机制 | 仍为片状/尖状延伸，不能作为可信柄部骨架；高IoU未解决结构 | [真实几何对照](figures/Fig4_Actual_Geometry_Update_Strategy_Comparison.png) |',
 '| G02 / 数值 | 原默认粗分箱前向片元选择不稳定；保留015 FAIL，无分箱只做只读定位 | arms/DIAGNOSTIC/metrics/G02_BINNING_CONTROL.json |',
 '| 虚拟初始门禁 | 原640→320最近邻target像素采样不一致，原0.97门槛失败，优化步数0；修复仅新增匹配网格Blender目标 | provenance/VIRTUAL_P3D_GATE_BEFORE_GRID_REPAIR.json、VIRTUAL_GRID_REPAIR_AMENDMENT.json |',
 '| 工程中断 | 准备阶段空帧号、脚本语法及Blender seed超出int范围均在相关优化前修复；首次虚拟gate失败按门禁停止后再恢复；无模型覆盖 | runtime原始日志与provenance |',
 '| 原初始化 G03/G07/G05/G06 | 初始已有穿入及B/C新恶化分类，不当作Unknown遮挡 | metrics/INITIALIZATION_COLLISION_CAUSES.csv |','',
 '## 每条新路线原始停止状态','','| 病例 | 路线 | 接受/提案 | 状态 | 密集64新增/恶化面 | 深度覆盖下降 |','|---|---|---:|---|---|']
 for x in native:
  if x['kind']=='READ_ONLY_015_BASELINE':continue
  g=next(v for v in geo if v['case']==x['case']and v['tag']==x['tag']);failures.append('|%s|%s|%d/%d|%s|%d/%d|%s|'%(x['case'],x['tag'],x['run']['accepted'],x['run']['attempts'],x['run']['status'],g['new_face_penetration_N'],g['existing_penetration_worsened_face_N'],x['coverage_decreased']))
 (R/'FAILURE_LEDGER.md').write_text('\n'.join(failures)+'\n');(R/'RESULT_INDEX.md').write_text('# RESULT_INDEX\n\n[技术摘要](TECHNICAL_REPORT_SUMMARY.md)、[失败记录](FAILURE_LEDGER.md)、[协议](01_PROTOCOL.md)。\n\n- metrics/SAMPLING_PAIRED_COMPARISON.csv：11例采样配对。\n- metrics/NATIVE_AND_GEOMETRY.json：29个新/旧输出的同分母观察与几何。\n- metrics/GT_COMPARISONS.csv：26条真实路线，尺度固定1最佳SE3后评价。\n- metrics/VIRTUAL_GT_COMPARISONS.json：虚拟固定坐标、无ICP表面方向诊断。\n- arms/DIAGNOSTIC/metrics：逐视角face/edge/vertex、分量梯度、实际attempt/ramp、影子提案、G02数值隔离。\n- local_results/Gxx_RING_WITNESSES.npz：真实CAD与冲突见证点。\n- review_meshes/Gxx：全部新结果及标识明确的静态旧对照，精确原生mm NPZ/PLY。\n- config/RUN_REGISTRY.json、VIRTUAL_RUN_REGISTRY.json：全部最终Mesh绝对路径；同目录FINAL.pt为完整优化器/RNG，原始源不覆盖。\n- figures/Fig1–Fig4：四类核心图。源码/输入/预测哈希在provenance。\n')
 print('REPORT_AND_PAIRED_RESULTS_WRITTEN',summary,flush=True)
if __name__=='__main__':main()
