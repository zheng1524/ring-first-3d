"""Generate reports from frozen predictions and measured evaluation only."""
from common import *
from collections import Counter
def mdtable(fields,rows):
    def fmt(v):
        if isinstance(v,float):return f'{v:.4g}'
        if isinstance(v,(dict,list)):return json.dumps(clean(v),ensure_ascii=False)
        return str(v).replace('|','/')
    return '| '+' | '.join(fields)+' |\n| '+' | '.join(['---']*len(fields))+' |\n'+''.join('| '+' | '.join(fmt(r.get(k,'')) for k in fields)+' |\n' for r in rows)+'\n'
def write(name,text): (R/name).write_text(text.rstrip()+'\n',encoding='utf-8')
def main():
    plan=load(R/'config/BODY_FIT_VIEWS.json');ss=load(R/'config/SOURCE_BINDING.json');dxy=load(R/'provenance/DXY_GENERATED.json');rel=load(R/'metrics/NEXT_STAGE_ELIGIBILITY.json');vv=load(R/'metrics/ALL_VIEW_EVALUATION.json');stab=load(R/'metrics/MULTISTART_STABILITY.json');jac=load(R/'metrics/JACOBIAN_IDENTIFIABILITY.json');geom=load(R/'metrics/GEOMETRY_AUDIT.json')
    primary=[x for x in rel if plan[x['pool']]['primary']];failstarts=[]
    save('provenance/PHASE0_INPUT_FILES.json',dict(load(R/'provenance/PHASE0_CORRECTION.json'),corrected_binding=asset(R/'config/SOURCE_BINDING.json'),superseded_draft='provenance/SUPERSEDED_PHASE0',all75_native_poses_present=True))
    save('provenance/PHASE0_SOURCE_BINDING.json',ss)
    for p in sorted((R/'local_results').rglob('START_*.json')):
        m=load(p)
        if not m['eligible']:failstarts.append(dict(pool=m['scene'],arm=m['arm'],start=m['start'],reason=m['ineligible_reasons'],nfev=m['nfev'],evidence=str(p.relative_to(R))))
    audit='''## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；75来源（74唯一RGB）；主分析每方案4组，附加005有2池 |
| 本算法独立成功 | E1=4/4、E2=4/4主组独立数值输出；附加各2/2池；完整科研验收0/4组每方案，不能当作测量正确 |
| 本算法失败 | 主组无数值输出失败；完整验收8/8主组方案失败；3单视角池×2方案为null/NaN；36初值有2个未收敛且排除主解 |
| 历史测量值回退 | 0；Body-U和旧DT+AMS只在预测冻结后作对照 |
| 失败组及具体原因 | [逐组失败台账](FAILURE_LEDGER.md)，关联候选、逐帧投影和图集 |
| 最终统计样本 | 仅独立成功主分析4组每方案；23张相同HOLDOUT（各池9/4/5/5）；全部75来源始终登记；不把来源数当独立组数 |
| 是否使用 GT 选择算法 | 否；GT未读，协议→DXY→视角/源码冻结→全部预测冻结→独立评价的SHA回执见provenance |

'''
    overview=[]
    for r in rel:
        sc=plan[r['pool']];g=next((x for x in geom if (x['pool'],x['arm'])==(r['pool'],r['arm'])),{});s=next(x for x in stab if (x['pool'],x['arm'])==(r['pool'],r['arm']))
        held=[x for x in vv if x['pool']==r['pool'] and x['arm']==r['arm'] and x['available'] and x['role']=='HOLDOUT']
        overview.append(dict(pool=r['pool'],arm=r['arm'],FIT=len(sc['FIT']),HOLDOUT=len(sc['HOLDOUT']),numerical=r['numerical_available'],eligible_starts=s['eligible_N'],heldout_IoU=r.get('holdout_median_IoU'),fixed_boundary_MAE_px=r.get('holdout_mean_fixed_boundary_px'),surface_multistart_p95_mm=s['surface_max_p95_mm'],Ring_min_mm=g.get('Ring_signed_min_mm'),HERO_gate=r['advance_to_HERO']))
    means=[]
    for arm in ['E1','E2']:
        group_iou=[];boundary=[]
        for group in ['G03','G05','G01','G06']:
            rows=[v for v in vv if v['pool']==group+'_004' and v['arm']==arm and v['available'] and v['role']=='HOLDOUT'];group_iou.append(float(np.median([v['IoU'] for v in rows])));boundary.extend(v['fixed_source_boundary_px']['MAE'] for v in rows)
        means.append(dict(arm=arm,physical_groups=4,median_group_heldout_IoU=float(np.median(group_iou)),group_IoU=group_iou,fixed_source_boundary_MAE_px=stats(boundary)))
    save('metrics/PRIMARY_GROUP_SUMMARY.json',means)
    fixedstats=[]
    for arm in ['E1','E2']:
        for group in ['G03','G05','G01','G06']:
            rows=[v for v in vv if v['pool']==group+'_004' and v['arm']==arm and v['available'] and v['role']=='HOLDOUT']
            distances=np.array([v['fixed_source_boundary_px']['MAE'] for v in rows]);fixedstats.append(dict(group=group,arm=arm,heldout_N=len(rows),IoU_median=float(np.median([v['IoU'] for v in rows])),per_view_fixed_boundary_MAE_px=stats(distances),FN_total=sum(v['FN'] for v in rows),FP_total=sum(v['FP'] for v in rows),full_polyp_total=sum(v['full_mask_N'] for v in rows),absolute_measurement_GT='NOT_EVALUABLE',MARE='NOT_EVALUABLE_NO_GT',MAE_mm='NOT_EVALUABLE_NO_GT',p95_mm='NOT_EVALUABLE_NO_GT',max_mm='NOT_EVALUABLE_NO_GT'))
    table('metrics/PRIMARY_GROUP_STATISTICS.csv',fixedstats)
    qc=Counter(x['quality']['quality_class'] for x in dxy)
    comparison=list(csv.DictReader((R/'metrics/DXY_VS_OLD_DT_AMS.csv').open()));shifts=np.array([float(x['center_shift_px']) for x in comparison]);geo_iou=np.array([float(x['geometry_IoU_known']) for x in comparison])
    numerical='\n'.join(f"- {r['pool']}/{r['arm']}: {', '.join(r['reasons']) or 'PASS'}; [实际投影图](figures/{r['pool']}_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/{r['pool']}_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/{r['pool']}/{r['arm']}/SELECTION.json)。" for r in primary)
    report='''# Body-E DXY初始化修复技术报告

本轮已按顺序执行Phase0–5。官方DXY重新计算75/75产生候选；四组主分析及两个附加005池的E1/E2均产生独立收敛数值解，但**无结果达到预登记的完整下一阶段门槛**，本轮不建议接入HERO对应。高IoU不能消除多初值、Ring穿透或留出轮廓矛盾。

## 输入审计纠错

前一条聊天所称“32来源缺位姿”有误：只查了新Git checkout和RAW initial_pose，漏查原始资产目录的FINAL_CAMERA_POOL。现已按旧prepare的真实绑定核验75来源原生K/T；原错误产物完整归档于provenance/SUPERSEDED_PHASE0。18个OLD018原生位姿与最终池存在小幅版本差异，采用原native T并逐源记录，未修改相机。详见METHOD_AND_INPUT_AUDIT.md。

## 官方二维几何

'''+f"DXY固定commit `75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`，VERSION=DXY-MID-1.0.0rc1，Geometry=V9.1；73个measure_files和2个640×360缓存measure_frame。R10内径10mm。质量为{dict(qc)}；75/75是候选覆盖，不等于解剖边界正确。没有缺失candidate，缺失名单为空；没有读取/保存DXY毫米结果。所有Ring/P/Q质量和原生basis见metrics/DXY_QUALITY_AUDIT.csv。\n\n"+f"预测冻结后才重算旧DT+AMS作对照：中心位移median={np.median(shifts):.3f}px、p95={np.quantile(shifts,.95):.3f}px、max={shifts.max():.3f}px；新旧几何区域IoU median={np.median(geo_iou):.3f}。逐源数值见metrics/DXY_VS_OLD_DT_AMS.csv。差异来自完整正式Ring/P/Q/候选选择流程，不能称官方几何只是旧AMS的缩放；此对照未进入拟合。\n\n"+'''## 公平性、视角与实际代码

E1仅将官方中心/basis按A1矩阵约定转换；E2完整原始Mask，柄和外围结构均保留。九参数模型、解析投影、二维损失与TRF.solve均从历史源码AST原样执行，非另写近似损失。唯一拟合适配为当前75源接口、删除所有depth_parts调用、成功资格筛选和轨迹保存。相同R0、三初值、权重、边界、预算经实际参数逐项核对。max_nfev=60，36次拟合；两个预算耗尽结果保留并排除。实际复用函数、行号、完整源码SHA和AST SHA见CODE_REUSE_MAP.md与provenance/CODE_REUSE_FUNCTIONS.json。

四组004各8FIT，未使用原来的固定三帧名单；G01/G03的005独立6/4FIT。所有未选合格帧留出，全部75登记，重复RGB不作独立证据。未证明跨视频坐标关系可忽略版本与条件依赖，故不合并；两个独立照片及G05单帧005不足多视角，不生成椭球。021身份审计实际重放553个描述子观察和547条RGB-RANSAC链接，但证据只适用于G01且全部背景；不推广至G03/G05/G06。MAX直接PnP共用004地图仅提供条件证据。

## 数值输出与完整验收

'''+mdtable(['pool','arm','FIT','HOLDOUT','numerical','eligible_starts','heldout_IoU','fixed_boundary_MAE_px','surface_multistart_p95_mm','Ring_min_mm','HERO_gate'],overview)+'''IoU在相同完整原始Mask上、排除Ring未知像素。轮廓距离单位px；实际每帧双向/固定源mean、median、p95、maximum及FN/FP固定分母见metrics/ALL_VIEW_EVALUATION.csv，FIT/HOLDOUT明确区分。主分析共同成功23张HOLDOUT的配对比较见metrics/PAIRED_HOLDOUT_COMPARISON.csv；按4物理组汇总而非把23帧当独立物理组。

这些HOLDOUT未参与本轮Body拟合，但历史相机/RGB地图/分割祖先可能已经用过相关图像；因此是条件性留出，不冒充完全外部独立测试。全部来源原来属于HERO FIT库存，新的Body FIT/HOLDOUT身份与旧任务身份分别记录。

## E1/E2何者更适合

主组HOLDOUT中位IoU：E2高于E1的是G01/G03；E1高于E2的是G05/G06。G01/G03的E1三初值更稳定且没有<-0.05mm表面Ring穿透，但完整Mask固定源轮廓误差仍未过门槛。E2可提高完整Mask覆盖，却可能通过不同三维形状解释类似二维轮廓。结论为MIXED/INSUFFICIENT_EVIDENCE，不宣布某方案普适更优，不用GT或Body-U挑结果。

## 退化与可辨识性

新主解不再出现上一轮20mm长轴或0.3mm薄轴；G06 E1仍触及旋转参数边界。许多池存在大于2mm的多初值表面差异；G05近球形使旋转本身歧义，不能把旋转差单独当形状差。actual mesh表面距离已经计算，失败台账不隐藏这种区别。

不含先验的二维观测Jacobian已SVD。全多视角局部条件数显著优于大多数单视角，但含CAD软可见性及float32射线离散时，单视角数值rank9也可能出现；它不是九个独立轮廓自由度的证据。另提供每视角5个解析椭圆系数的conic-only Jacobian，单视角至多rank5。多视角局部信息改善不证明全局唯一，更不能消除多初值和Ring矛盾；未跑单视角反事实拟合，因此不能声称严格因果改善。

## Ring与历史对照

所有六方向图采用mm等比例，灰色真实Ring CAD，粉色E1、蓝色E2、橙色历史Body-U。Body-U仅预测冻结后读取，属于历史正式R3 B3多HERO训练结果，含历史整合，不能作GT。metrics/BODY_U_COMPARISON.json只报告差异。整个椭球背面及被遮挡轮廓都是推断，绿色原Mask可观察轮廓与Ring接触未知边界在图中区分。Ring检查为实际网格/2048表面样本、11射线有符号距离的有限采样证据，不冒充无穿透数学证书；G03 E2最浅穿透接近阈值，需结合数值精度审阅。

## 失败和下一阶段

'''+numerical+'\n\n'+'''附加005两个池同样未通过全部门槛。G05_005、G01_PHOTO、G05_PHOTO只有1个源，E1/E2均为null/NaN、不能声称充分多视角。失败来源/帧、候选、图像和三维证据见FAILURE_LEDGER.md。没有执行A2、resection、融合、新训练或修改HERO。下一步是人工审阅这些失败证据，不是自动启动重定位。

真实GT未读取，因此中位绝对相对误差、真实mm MAE/p95/max均NOT_EVALUABLE，不能用投影px指标冒充真实尺寸准确度。可计算的投影误差完整报告固定分母、mean/median/p95/max。验证通过不等于科学验收。

'''+audit
    write('TECHNICAL_REPORT.md',report)
    write('TECHNICAL_REPORT_SUMMARY.md','# 执行摘要\n\nPhase0–5全部完成；DXY75/75候选，38 normal_Gate_pass、37 Q_conflict_recovery。四组004主分析每组8FIT，E1/E2均独立数值成功4/4；附加005分别拟合，照片/单帧池不强行混合。36初值中的2个不收敛结果均排除；无历史回退。\n\n当前无结果通过完整HERO接入门槛：主要是多初值、完整Mask留出轮廓和Ring穿透。E1/E2结论MIXED。主表、逐帧指标与图像见[技术报告](TECHNICAL_REPORT.md)，[失败证据](FAILURE_LEDGER.md)。\n\n'+audit)
    inv=[]
    for g in ['G03','G05','G01','G06']:
        q=[s for s in ss if s['group']==g];inv.append(dict(group=g,total=len(q),v004=sum(s['video']=='004' for s in q),v005=sum(s['video']=='005' for s in q),photos=sum(s['video']=='PHOTO' for s in q),native_pose=len(q),pool_formal=sum(s['pool_formal'] for s in q)))
    write('METHOD_AND_INPUT_AUDIT.md','# 方法与输入审计（更正并完成）\n\n原Phase0误将RAW initial_pose缺失当成无相机；正式FINAL_CAMERA_POOL在原资产目录中存在。旧报告/代码归档于provenance/SUPERSEDED_PHASE0，不能继续引用其“32缺位姿”结论。\n\n'+mdtable(['group','total','v004','v005','photos','native_pose','pool_formal'],inv)+'46个MAX源以view ID+target SHA精确匹配，29个OLD018使用其显式target_cache并验证RGB/Mask。75原生T均有效；18个与最终池C版本差异在VIEW_INVENTORY.csv逐源列明。原生352×640到360×640的K映射严格沿用半像素公式；从未用HERO XYZ/深度决定Body。全部Mask uint8类别0/1/2。DXY73文件接口+2照片缓存帧接口；所有输入、实际RGB/Mask字节SHA、K/T与Ring CAD见config/SOURCE_BINDING.json。\n\n正式DXY与底层源码SHA已冻结；对照DT/AMS和Body-U均在全部预测冻结后读取。2个上游探索性相机仅作诊断，重复RGB不进入独立留出。跨视频不合并，照片单列。完整公平性/输入冻结检查见metrics/VALIDATION.json，数值一致性见metrics/NUMERICAL_CONTRACTS.json。\n\n'+audit)
    ledger='# 失败台账\n\n所有失败保留；数值主解与科研验收分别列报。\n\n'+mdtable(['pool','arm','start','reason','nfev','evidence'],failstarts)
    for r in rel:
        if r['advance_to_HERO']:continue
        name=r['pool'];sc=plan[name]
        ledger+=f"## {name} / {r['arm']}\n\n原因：{'; '.join(r['reasons'])}。\n\n"
        if sc['FIT']:
            ledger+=f"[主解与全部初值](local_results/{name}/{r['arm']}/SELECTION.json)；[全来源投影](figures/{name}_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/{name}_SIX_DIRECTION_BODIES.png)。\n\n"
        else:ledger+=f"[不足多视角状态](local_results/{name}/{r['arm']}/SELECTION.json)；[原始图像证据](figures/{name}_ALL_VIEW_OVERLAYS.png)。\n\n"
        for cid in sc['raw_sources']:
            v=next((v for v in vv if v['pool']==name and v['arm']==r['arm'] and v['source']==cid),{})
            reason=f"role={v.get('role')}, IoU={v.get('IoU')}, FN={v.get('FN')}, FP={v.get('FP')}"
            ledger+=f"- `{cid}`：{reason}；[逐帧本地图](figures/overlays/{cid}.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。\n"
        ledger+='\n'
    ledger+='## 上游资格及重复身份\n\n'+''.join(f"- {x['source']}：{x['reason']}；保留诊断，不作为独立FIT/HOLDOUT。\n" for sc in plan.values() for x in sc['excluded'])+'\n'+audit
    write('FAILURE_LEDGER.md',ledger)
    # Exact reused function audit, with full file and AST hash and actual source lines.
    reuse_records=load(R/'provenance/CODE_REUSE_FUNCTIONS.json')
    reuse_records+=load(R/'provenance/EVALUATION_COMPLETED.json')['source_reuse']
    # DXY helpers and the 021 replay execute in isolated namespaces; append
    # their exact original AST receipts instead of claiming an indirect import.
    for path,names in [(A1/'generate_dxy.py',['sha','asset','clean','guard']),(REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/identity021.py',['main'])]:
        for node in ast.parse(path.read_text()).body:
            if isinstance(node,ast.FunctionDef) and node.name in names:
                reuse_records.append(dict(file=asset(path),function=node.name,line=node.lineno,end_line=node.end_lineno,AST_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),mathematics_modified=False))
    unique={(r['file']['path'],r['function']):r for r in reuse_records}
    auditrows=[dict(function=r['function'],source=r['file']['path'],line=r['line'],end_line=r['end_line'],SHA256=r['file']['sha256'],AST_SHA256=r['AST_sha256'],direct='YES: compile unmodified AST',math_modified=False) for r in unique.values()]
    table('provenance/CODE_REUSE_MAP.csv',auditrows)
    mapping='''# 实际代码复用审计

| 新实验模块 | 历史代码 | 直接复用 / 修改 | 修改原因及实际调用 |
| --- | --- | --- | --- |
| DXY输入 | A1 generate_dxy.py + 官方pipeline | 官方API直接调用；A1 guard/sha/asset/clean AST原样执行；仅输入映射适配 | 75当前来源替代旧13来源CC；不读毫米输出 |
| 二维几何转换 | A1 prepare.py:22 | 原表达式逐字沿用 | q=(alluv-center)@inv(basis).T；75个basis roundtrip已检验 |
| 九参数模型 | A1 COARSE models.py | decode/sphere_mesh直接AST | 没有形态分支或新参数 |
| 解析椭球投影 | A1 losses.py | ellipse_projection/signed_distance直接AST | 未修改公式 |
| 二维损失 | A1 losses.py | target_data/cad_visibility/two_d_parts等直接AST | 未修改公式；保留全部Mask和Ring未知 |
| 优化框架 | A1 fitting.py:Problem.solve | solve方法AST原样挂载；Problem输入/residual适配 | 原solve不可直接构造旧CC，因此适配75视角，只拼2D+原prior，不调用depth_parts；新增资格选择器 |
| 稳定性评价 | A1 analyze.py | geom/sample_mesh/surface_distance/canonical_orientation/difference直接AST | 原样计算实际网格距离及等价旋转 |
| 多视角选择 | 015 prepare.py | skeleton_proxy直接AST；评分/贪心表达式复用到当前池 | 原main含历史Body中心及固定名单，不能直接执行；改Ring原点方向和独立源池，不读取旧Body |
| 跨视频身份审计 | 021 identity021.py:main | AST原样执行，输出重定向本任务 | 实际核验553观察/547链接；prepare021/geometry021只读审阅其坐标约定，不运行BA/变换 |
| 来源完整性 | A1 validate.py检查思路 | 当前格式检查适配 | 逐输入SHA、冻结、主解资格、实际初值公平性和固定分母均复核 |

求解/损失/投影函数保持原AST，无新旧数学差异；接口不同使历史main不能整体import（会创建旧目录并读旧CC/深度）。采用受限AST抽取只执行所列成熟函数，调用与原文件行号一致。335项数值契约包含native basis roundtrip、解析投影与实际网格射线深度、完整Mask保留、E1/E2同设置。来源binding/K仿射严格沿用旧prepare；跨视频新配准未执行。

所有直接调用函数的完整源码SHA256、AST SHA和行号如下；本轮源码冻结另见SOLVER_CODE_FREEZE.json。

'''+mdtable(['function','source','line','SHA256','AST_SHA256','direct'],auditrows)
    mapping+='\n## 适配的整文件源码SHA\n\n'+mdtable(['file','SHA256'],[dict(file=str(p.relative_to(REPO)),SHA256=sha(p)) for p in [A1/'generate_dxy.py',A1/'prepare.py',A1/'fitting.py',A1/'validate.py',REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py',REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/prepare021.py',REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/geometry021.py',OLD/'code/prepare.py']])
    write('CODE_REUSE_MAP.md',mapping)
    code=[dict(file=p.name,SHA256=sha(p),purpose=(p.read_text().splitlines()[0] if p.read_text() else '')) for p in sorted((R/'code').glob('*.py'))]
    write('CODE_MAP.md','# Code map\n\n'+mdtable(['file','SHA256','purpose'],code)+'\nphase0_audit.py为旧错误审计，已停用；正式入口prepare_inputs.py。历史resection.py/validate_pose.py未复制、未修改或运行。\n')
    write('REPRODUCE.md','''# 复现

环境：Body/评价使用 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；DXY使用 `/home/liu/new-polyp-dxy/.venv/bin/python`；版本见provenance/ENVIRONMENT.json。所有实验资产绝对路径和SHA见provenance/INPUT_SHA.json与config/SOURCE_BINDING.json。原始75缓存不上传Git；无原始资产时只能审阅已交付冻结结果，不能声称完整重跑。

本任务的已冻结目录不能覆盖运行。要完全重跑，先在另一个独立工作树/目录保留相同repo历史路径结构并复制本任务代码，删除新副本中的预测/冻结产物（只针对新副本），然后按以下顺序运行；不得删除本任务当前冻结结果。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK=experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001
$PY "$TASK/code/prepare_inputs.py"
$PY "$TASK/code/run_dxy.py"
$PY "$TASK/code/qualify_views.py"
$PY "$TASK/code/contracts.py"
$PY "$TASK/code/run_fits.py"
$PY "$TASK/code/evaluate.py"
$PY "$TASK/code/legacy_compare.py"
$PY "$TASK/code/visualize.py"
$PY "$TASK/code/validate.py"
$PY "$TASK/code/report.py"
```

无需新训练或下载权重。冻结求解脚本固定三初值×60nfev，仅2D损失，无HERO/GT。DXY逐源记录及全部优化TRACE JSON/NPZ保留；worker日志在runtime。可在当前目录安全重跑validate.py进行只读输入/冻结/公平性验证；其输出只更新验证回执，不优化。Git交付仅精选全视角图集与六方向图、报告、小表、冻结JSON和主体小NPZ/PLY；全部逐帧独立PNG、每像素投影/Jacobian/NPZ轨迹留在本地并列SHA索引。
''')
    write('RESULT_INDEX.md','# Result index\n\n[技术报告](TECHNICAL_REPORT.md) · [摘要](TECHNICAL_REPORT_SUMMARY.md) · [失败台账](FAILURE_LEDGER.md) · [复现](REPRODUCE.md)\n\n'+''.join(f"- {name}: [实际全部视角图](figures/{name}_ALL_VIEW_OVERLAYS.png)"+(f" · [六方向主体与Ring](figures/{name}_SIX_DIRECTION_BODIES.png) · [全部初值（含失败）](figures/{name}_MULTISTART_SHAPES.png)" if sc['FIT'] else '')+'\n' for name,sc in plan.items())+'\n完整库存见VIEW_INVENTORY.csv，DXY质量见metrics/DXY_QUALITY_AUDIT.csv；所有初值的START、TRACE和资格在local_results；仅合格收敛主解有Body-E-DXY/Body-E-FULLMASK。所有失败保留null。完整本地文件路径/SHA在assets_index/LOCAL_ARTIFACTS.json。\n')
    save('assets_index/LOCAL_ARTIFACTS.json',[asset(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='LOCAL_ARTIFACTS.json' and '.git' not in p.parts])
    print('REPORTS_COMPLETE',dict(qc),'primary numeric',sum(r['numerical_available'] for r in primary),'primary gates',sum(r['advance_to_HERO'] for r in primary),flush=True)
if __name__=='__main__':main()
