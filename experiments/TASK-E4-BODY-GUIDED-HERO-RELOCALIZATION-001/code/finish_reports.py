from common import *
from collections import Counter

def f(x,n=3):return 'NaN'if x is None else ('%.0f'%x if n==0 else ('%.'+str(n)+'f')%x)
def mdtable(rows,keys):
 return '| '+' | '.join(keys)+' |\n|'+ '|'.join(['---']*len(keys))+'|\n'+'\n'.join('| '+' | '.join(str(r.get(k,'MISSING'))for k in keys)+' |'for r in rows)+'\n'
def main():
 assert (R/'provenance/VISUALIZATIONS_COMPLETED.json').exists();vals=load(R/'metrics/VALIDATION.json');met=load(R/'metrics/COMPARISON.json');ctrl=load(R/'metrics/CONTROL_RESULTS.json');src=load(R/'config/REAL_SOURCES.json');groups=['G03','G05','G01','G06'];rows=[];counts=[]
 for g in groups:
  for a in ['A0','A1','A2-E','A2-U']:
   mm=next(x for x in met if x['group']==g and x['arm']==a and x['comparison']=='independent_HERO_HOLDOUT');vv=[x for x in vals if x.get('group')==g and x['Body']=='Body-'+a[-1]]if a.startswith('A2')else[];n=sum(s['group']==g for s in src);rows.append(dict(group=g,arm=a,native_sources=n,numerical=sum(v['numerical']for v in vv)if vv else n,conditionally_supported=sum(v['accepted_H']is not None for v in vv)if vv else'baseline; not new pose',heldout_fixed_N=mm['fixed_N'],heldout_known=f(mm['known_fraction']),heldout_MAE_mm=f(mm['effective_error_mm']['MAE']),heldout_P95_mm=f(mm['effective_error_mm']['p95']),heldout_support=f(mm['support_N_fraction']),heldout_fixed_penalty_mm=f(mm['fixed_10mm_penalty_mm']),SIFT_HOD_px=f(np.mean([v['derived_SIFT']['MAE']for v in vv if v.get('derived_SIFT',{}).get('MAE')is not None]))if vv else'not resected',Ring_boundary_px=f(np.mean([v['derived_Ring']['boundary']['MAE']for v in vv if v.get('derived_Ring',{}).get('boundary',{}).get('MAE')is not None]))if vv else'not resected'))
  for b in ['Body-E','Body-U']:
   vv=[x for x in vals if x.get('group')==g and x['Body']==b];counts.append(dict(group=g,Body=b,numerical=sum(x['numerical']for x in vv),accepted=sum(x['accepted_H']is not None for x in vv),total=n,reasons=dict(Counter(y for x in vv for y in x.get('reasons',[])))))
 save('metrics/FINAL_SCORECARD.json',rows);table('metrics/FINAL_SCORECARD.csv',rows);table('metrics/QUALIFICATION_COUNTS.csv',counts)
 # Explicit null/NaN accepted predictions, never silently restore A0 as a new result.
 accepted=[dict(group=x.get('group'),source=x['source'],Body=x['Body'],status=x['status'],accepted_transform=x['accepted_H']if x['accepted_H']is not None else'NaN',reasons=x.get('reasons',[]))for x in vals];table('metrics/ACCEPTED_RELOCALIZATIONS.csv',accepted)
 bodyrows=[]
 for g in groups:
  a=load(R/'local_results'/g/'Body-E_FIT.json');bodyrows.append(dict(group=g,center_mm=np.round(a['center_mm'],4).tolist(),semiaxes_mm=np.round(a['axes_mm'],4).tolist(),FIT_views=', '.join(a['fit_views']),image_cost=f(min(z['cost']for z in a['starts']))))
 crows=[dict(control=x['control'],Body=x['Body'],initial_mm=f(x.get('initial_point_error_mm',{}).get('MAE')),final_mm=f(x.get('final_point_error_mm',{}).get('MAE')),pose_translation_mm=f(x.get('final_pose',{}).get('translation_mm')),pose_rotation_deg=f(x.get('final_pose',{}).get('rotation_deg')),zero_pass=x.get('zero_drift_pass'),qualification=x.get('status'))for x in ctrl if'final_point_error_mm'in x];nnum=sum(x['numerical']for x in vals);nacc=sum(x['accepted_H']is not None for x in vals);fail=nnum-nacc
 audit=f'''|审计项目|必须汇报|
|---|---|
|目标组数|4个独立物理组；75来源；150个Body-E/U来源状态；A0/A1独立基线|
|本算法独立成功|{nnum}/150产生数值候选；{nacc}/150满足预登记条件性验证；不能等同真实定位准确或独立来源数量|
|本算法失败|{150-nnum}无数值候选；{150-nacc}未获条件性资格，accepted_H=null/NaN；绝对真实三维精度4/4 NOT_EVALUABLE|
|历史测量值回退|0；A0/A1与授权Body-U是明示对照/输入，未填入失败A2预测|
|失败组及具体原因|FAILURE_LEDGER.md及metrics/VALIDATION.csv逐来源原因与真实图集|
|最终统计样本|全部4组、75来源、150状态；每源最多1024固定原生ID；有效N与全N并列；没有融合Mesh监督|
|是否使用GT选择算法|否；provenance/REAL_SOLVER_CODE_FREEZE.json与ALL_REAL_PREDICTIONS_FROZEN.json；控制GT仅生成/冻结后审计|
'''
 summary='''# Body-Guided HERO重定位：技术报告摘要

已完成四组真实实验与受控验证。**二维区域候选可以突破旧三维近邻门控，但尚不能把Body自洽当作可靠真实重定位。** 本轮没有更新Body、没有融合、没有新模型训练；所有原始曲面和相机只读。

## 输入与实际方法

G03→G05→G01→G06全部运行。Body-E是从固定参考视频三幅二维Mask/通用核心椭圆新拟合的九参数椭球，未读HERO XYZ或旧训练Body参数；Body-U为正式R3 B3 FINAL。算法以二维归一化区域建立Body首层候选，联合区域误差、实际Ring和真实背景SIFT优化来源级六自由度派生位姿。同一个刚体作用HERO与来源相机，完整局部形态/原像素关系保持。**这不是019–021的视频共享T，不是正式新轨迹；不能证明源间相对相机变形是正确修复。** A1实际复现旧受限射线修正，四组theta与历史FINAL最大差均0。

区域描述子新采用同一Mask核心AMS椭圆，不声称DXY最终算法；外围细长区域不作为椭球头部强对应，但完整网格保留。原设计/实际逐项对照与源码位置见METHOD_AND_INPUT_AUDIT.md。实际PyTorch3D Body优化未运行，因本任务明确冻结Body。

## 固定分母独立评价

'''+mdtable(rows,['group','arm','numerical','conditionally_supported','heldout_fixed_N','heldout_known','heldout_MAE_mm','heldout_P95_mm','heldout_support','heldout_fixed_penalty_mm'])+'''
**实际独立结果偏负，不能推广替换：** G03原生留出MAE由2.842mm降到A2-U的2.471mm，但known从90.3%降到88.6%、支持率22.9%降到22.3%，两种Body条件资格均0/18；这不是可靠错层修复。G05的A2-E/U为0.676/0.679mm，均差于A0的0.593mm与A1的0.434mm。G01的A2-E条件MAE略降，但固定分母代价2.563→2.646mm、支持下降；A1更稳定。G06负对照明显被扰动，A0→A2-E/U为0.299→0.451/0.452mm，支持75.9%降到58.8%/58.0%。因此即使某些来源满足Ring/背景/区域条件检查，也不能将其称为完整独立几何验收通过。条件性通过仅为34/150状态（E=21/75，U=13/75），不支持全组替换。

MAE/P95仅在有效原生HERO留出对应上，support与known以全源–目标查询N为分母；10mm未解释代价为评价代理，不是GT误差。所有A2数字包含未获资格的**数值提案**，不能当作全来源合格新几何。原生留出HERO也有预测/相机噪声，不是GT。相同上游图像的来源并非独立统计证据。

## 控制实验

'''+mdtable(crows,['control','Body','initial_mm','final_mm','pose_translation_mm','pose_rotation_deg','zero_pass','qualification'])+'''
C2/C3能恢复较大的刚体错位，说明不依赖旧世界距离准入。C1的加性轴向深度误差改变三维局部形状，严格刚体A2没有足够表达能力，恢复失败。零扰动Body-U产生约0.156mm漂移，超过0.1mm预登记门槛，即使Ring/背景条件检查通过，也不能称定位精度已证明。C4保留独立真实左右曲面，未平均或合并；仅是最小控制，不证明任意复杂多分支都可判别。

## 五个科研回答

1. **初始椭球还是更新Body？** 上表必须结合独立指标与资格率判断，不按Body距离或漂亮截面选胜者。Body-E在G03拉长、G01/G05扁平，说明本次有限预算二维拟合未得到稳定合理的粗主体；相机、区域描述子和局部优化搜索都可能参与，不能据此唯一证明几何不可辨识；Body-U含更强历史观测，也会将形态偏差传入对应。没有一个Body已证明普适正确区域对应。
2. **远距离能生成合理候选？** 可以突破旧门控；控制C3恢复与真实旧距离/候选数见逐来源CSV。候选产生不等同真实身份正确。
3. **是否独立改善定位？** 只能按上表、背景留出、Ring全CAD和来源间可见性给局部条件证据。某些误差下降同时可能失去支持/覆盖；不足以认定四组错层可靠解决。绝对位姿精度NOT_EVALUABLE。
4. **G03长柄？** A2完整刚体保留原柄、连接、面片、长度和曲率，未将柄吸附椭球头；这只是局部形态保持，世界方向/位置仍受独立约束与歧义限制，不宣称长柄已经准确重定位。全部原面与候选图均保留。
5. **误差来自哪里？** C1证明深度形变不能由严格刚体表达；新椭球退化与零扰动U漂移证明Body区域并非精确材料对应；真实背景/Ring矛盾也可能来自原相机、背景非静态/重复纹理、Mask/CAD投影或HERO。现有真实数据不能唯一拆分所有原因，不把全部误差归因相机。

## 失败与结论

控制契约修复前结果归档，正式真实参数未按留出或GT调整。没有删除错层面制造改善。建议保留二维区域候选和独立约束的诊断接口，**暂不把本轮全部A2提案替换正式HERO/相机或进入自动融合**；下一步应先人工检查关键区域身份与独立背景/相机证据，若另行授权再隔离刚体定位与射线深度误差。完成后停止。

## 核心图与复现

- figures/Fig1_Region_Correspondences.png：实际二维对应与原图。
- figures/Fig2_Body_E_U.png：两种Body及同来源候选。
- figures/Fig3_HERO_All_Group_Comparison.png：全部原生三角面、同尺度错层对照。
- figures/Fig4_Independent_and_Control_Evaluation.png：独立评价与控制失败。
- 各组Three_Fixed_Directions、Actual_Common_Sections及GLB完整图层。

精确绝对路径与SHA见RESULT_INDEX.md、assets_index。运行命令见REPRODUCE.md。大数据/GLB/全部逐步记录本地保留，只有明确列入Git交付清单的文件声称上传。

## 固定审计表

'''+audit
 (R/'TECHNICAL_REPORT_SUMMARY.md').write_text(summary)
 report=summary+'\n## 新椭球参数与视角\n\n'+mdtable(bodyrows,['group','center_mm','semiaxes_mm','FIT_views','image_cost'])+'\n## 条件资格与原因\n\n'+mdtable(counts,['group','Body','numerical','accepted','total','reasons'])+'\n'+(R/'METHOD_AND_INPUT_AUDIT.md').read_text();(R/'TECHNICAL_REPORT.md').write_text(report)
 failures='# 失败台账\n\n失败保留，不以删除来源/GT选模/原生结果回填制造PASS。数值候选不是认证位姿。\n\n'+mdtable(counts,['group','Body','accepted','total','reasons'])+'\n## 控制与工程失败\n\n- C1：刚体不能消除原射线加性深度造成的形态扭曲；未静默改为非刚性算法。\n- C0 Body-U：0.156mm漂移，未通过预登记0.1mm；条件背景/Ring通过不等于正确。\n- Body-E：G03半轴达到约20mm边界，G01/G05出现扁平解；保留有限预算结果，无HERO初始化补救。\n- 首轮控制CAD轮廓子采样漏管截面、鲁棒化先后导致离群放大，已修复后全控制重跑；旧源码/结果在runtime/CONTROL_RING_AND_ROBUST_CONTRACT_FIX，不选旧版更好结果。\n- 早期Body-E遗漏bounds调用、控制导入/拆分身份等实现错误均归档；真实定位开始前修复冻结。\n- 图片SIFT几何有退化RANSAC异常时记录0匹配，不制造背景对应。\n- 来源级派生相机允许原视频相对关系变化，不能等同正式轨迹恢复；真实绝对位姿、测量精度NaN/NOT_EVALUABLE。\n- 真实相机/深度/Body/区域误配因果尚未完全可辨识；未获资格提案accepted_H=NaN，A0只独立对照。\n\n## 逐来源失败\n\n'
 failures+='- 29份旧Mesh无逐顶点原生PixelID，保留归档UV/K、原顶点序号及原面ID；原生ID缺失=-1/UNKNOWN，未伪造映射。所有区域锚的OBS原生PixelID仍完整。\n'
 for v in vals:
  if v['accepted_H']is None:failures+='- '+v['source']+' / '+v['Body']+': '+', '.join(v.get('reasons',[v['status']]))+'；候选/原生ID：local_results/'+str(v.get('group',''))+'/'+v['Body']+'/'+v['source']+'/CANDIDATES_FROZEN.json；证据：figures/'+str(v.get('group',''))+'_Three_Fixed_Directions.png。\n'
 import re
 failures=re.sub(r'；候选/原生ID：([^；]+)；证据：([^。]+)。',r'；[候选/原生ID](\1)；[可视化证据](\2)。',failures)
 (R/'FAILURE_LEDGER.md').write_text(failures)
 # All original input and frozen Body checks after rendering/export.
 receipts=load(R/'provenance/INPUT_SHA.json')+load(R/'provenance/BODIES_FROZEN.json')['files'];bad=[]
 for a in receipts:
  if sha(a['path'])!=a['sha256']:bad.append(a['path'])
 save('provenance/FINAL_IMMUTABILITY_CHECK.json',dict(epoch=time.time(),checked=len(receipts),mismatches=bad,passed=not bad));assert not bad
 # Dependency/version receipt.
 import scipy,platform
 save('provenance/ENVIRONMENT.json',dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,opencv=cv2.__version__,open3d=__import__('open3d').__version__,parent_commit='e2d1eb16da103c0fa198596b4434c4ddfaebef8a',new_model_training=False,Body_updates=False))
 index='# 结果索引\n\n实验根目录：`'+str(R)+'`。\n\n本地大型网格/GLB、缓存、原始匹配、逐seed轨迹保留，不因存在本地文件就声称已上传。正式Git文件清单和提交回执另外记录。\n\n'
 for pattern in ['figures/*.png','metrics/*csv','local_results/*/Body-?.npz','local_results/*/*ALL_LAYERS.glb','controls/ALL_PREDICTIONS_FROZEN.json','provenance/ALL_REAL_PREDICTIONS_FROZEN.json']:
  for p in sorted(R.glob(pattern)):index+='- ['+str(p.relative_to(R))+']('+str(p)+') | '+str(p.stat().st_size)+' bytes | SHA256 '+sha(p)+'\n'
 (R/'RESULT_INDEX.md').write_text(index);save('assets_index/LOCAL_RESULT_FILES.json',[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()and not p.is_symlink()]);print('REPORTS_COMPLETE',nnum,nacc,flush=True)
if __name__=='__main__':main()
