"""Generate one technical report and linked audit annexes from frozen facts."""
from common import *

def mdtable(headers,rows):
    def cell(x):return str(x).replace('|','/').replace('\n','<br>')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(cell(x)for x in row)+' |\n'for row in rows)
def write(name,txt):(R/name).write_text(txt.rstrip()+'\n')
def num(x):return f'{float(x):.3f}'
def main():
    summary=load(R/'provenance/INVENTORY_SUMMARY.json');org=load(R/'provenance/SOURCE_ORGANIZATION.json');raw=readrows(R/'metrics/E3_RAW_SURFACE_DIAGNOSTICS.csv');ret=readrows(R/'metrics/E3_HISTORICAL_FACE_RETENTION.csv');cov=readrows(R/'metrics/E3_HISTORICAL_SOURCE_RAY_COVERAGE.csv');miss=readrows(R/'metrics/E3_OBSERVED_WITHOUT_TRIANGLE.csv');pairs=readrows(R/'metrics/E3_VIEW_COVERAGE.csv');manifest=readrows(R/'metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv');cases=readrows(R/'metrics/E3_CASEBOOK_POINTS.csv');roles=load(R/'provenance/SOURCE_ROLES.json')
    # Detailed source selection proposal retains every available source.
    text='# E3 来源组织提案（非优化执行授权）\n\n来源和阈值在下游方法输出之前固定。全来源清单为40份 native HERO、3张照片及51条主派生记录，共94条；其中36份主目录原始面身份已验证，另外4份目录来源仅做筛查。家族按全部真实上游 RGB SHA 的共享连通分量归并；每视频主源同属一个相关家族，不意味着几何完全相同或没有互补信息。派生结果不能多票。\n\n'
    text+=mdtable(['视频','全部 / 参考筛查 / 代表','方向格 代表/全筛查','法向格','0.5mm空间格','共视组件'],[(o['scene'],f'{len(o["all_available_sources"])}/{len(o["reference_screened_sources"])}/{len(o["representative_sources"])}',f'{o["selected_camera_bins"]}/{o["all_camera_bins"]}',f'{o["selected_normal_bins"]}/{o["all_normal_bins"]}',f'{o["selected_spatial_voxels"]}/{o["all_spatial_voxels"]}',f'{o["representative_components"]}/{o["all_screened_components"]}')for o in org])
    text+='\n相机方向为 `(camera_center - frozen_ROI_center)/norm`，不是光轴；ROI中心是完整包络中心，长尾会影响该规约，不是解剖中心。另报光轴角、平移基线和共投影。方向10°分格；原面法向12×6方向格，非长边原面面积达到源总合格代理面积1%才记格；空间格为非长边原面重心0.5mm格。相机格不能代替实际几何法向/空间格，后两者仍是 raw HERO 支持代理。\n\n'
    for o in org:
        sid=o['scene'];pp=[p for p in pairs if p['scene']==sid and p['pair_camera_reference_eligible']=='True'];text+='## '+sid+'\n\n'
        text+='\n'.join(f'- `{r}`：{roles[r]}'for r in o['all_available_sources'])+'\n\n'
        if pp:text+=f'筛查参考对 ROI 方向夹角 {min(float(p["ROI_camera_direction_angle_deg"])for p in pp):.2f}–{max(float(p["ROI_camera_direction_angle_deg"])for p in pp):.2f}°，共视图组件={o["all_screened_components"]}。边需双向各≥10%固定采样原顶点在对方原面/Mask内且不被CAD挡住；每源最多2048个均匀原索引点。连通仅是几何候选，不认证物理对应。\n\n'
    text+='G01_004 只保留既有三参考作为条件性 CORE，没有合格新增桥。G01_005 在三 CORE 外按冻结贪心增加 growth_r20，仍有其他合法 RESERVED；代表集保留全部38个法向格，但只覆盖1620/1873空间格，不能声称无损替代8份参考。G06增加new_r00与growth_r03；G08两筛查源仅占同一个相机格，几何仍需分别看来源；G07无CORE，全部UNQUALIFIED。\n\n规则保留既有 G01 三参考及其他已筛查旧主参考，再在G01最多4源/其他最多3源预算内，以新增空间格/法向格/相机格的全筛查集合归一化边际比例等权和贪心选桥，要求与已选源共视连通，同分按source_id排序。边际数见 `E3_MARGINAL_SOURCE_COVERAGE.csv`；没有读取SDF输出、GT或误差选择角色。\n\n额外有界检索覆盖 G02–G05 四份旧 native HERO。G04/G05为Is/R10；G07为Is/R5但未合格。该目录中额外合格Is/R5=0，不把有界检索写成全磁盘不存在。G02参考曾筛查但上游链和原索引未获E1级认证，四份均未加入正式源集合。三张照片K候选/c2w空，METRIC_GEOMETRY_NOT_QUALIFIED，不使用历史候选配准。\n'
    write('docs/E3_SOURCE_SELECTION_PROPOSAL.md',text)
    # Code entrypoints with their real lineage, not a generic reusable assertion.
    text='# E3 实际代码复用审计\n\n读取实际文件并AST核对入口，完整记录见 `provenance/E3_CODE_REUSE_AUDIT.json`。所有历史模块main均未调用；真实数值审计执行的入口在下表明确标注。本轮未导入MonoSDF/MapAnything/MASt3R模型、未打开checkpoint。\n\n'
    for r in load(R/'provenance/E3_CODE_REUSE_AUDIT.json'):
        text+='## '+r['capability']+'\n\n'+f'文件：`{r["path"]}`。分支 `{r["branch"]}`，commit `{r["commit"]}`，文件SHA256 `{r["sha256"]}`。\n\n'
        text+='入口：'+('; '.join(f'`{f["name"]}({f["signature"]})` L{f["line"]}'for f in r['functions'])or'仅报告/元数据读取，禁止导入该运行时')+'。\n\n'
        text+=f'输入输出：{r["input_output"]}；单位：{r["units"]}。真实验证：{r["validation"]}。必要输入：{r["required_inputs"]}。依赖本地未上传大资产：是。最小适配/限制：{r["minimum_adaptation"]}。\n\n'
    text+='depth_mesh 的归档配置路径为旧 ring_first_v1/config.json，原跳变阈值0.75mm；本轮不重新三角化。所有原面直接从旧PLY/NPZ核对。薄适配只做源格式桥接、Open3D BVH查询、固定分母统计和画图；不实现第二套相机/反投影。第三方CPU几何库缓存为旧vendor，模型权重不属于本轮运行依赖。源码SHA与检查时所属commit一起给出，不能用commit替代本地实际文件哈希。\n'
    write('docs/E3_CODE_REUSE_AUDIT.md',text)
    text='# E3 真实几何冲突案例册\n\n288条定位记录覆盖36源的8类位置/保护代理；原UV、面ID、XYZ、K/c2w、朝相机法向、CAD首交、相邻源投影及深度差见 `metrics/E3_CASEBOOK_POINTS.csv`。HEAD/SIDE/ABOVE/BELOW等是确定性坐标位置，THIN_BASE是既有保护代理；没有人工真实解剖确认，不能把这些名字视为标签。每源peer取固定采样原面重叠最高者，只为展示，不是认证对应。\n\n'
    text+='A `SAME_SURFACE_DEPTH_CONFLICT` 认证数=0；B `DISTINCT_SURFACES_OR_OCCLUSION` 仅认证“固定CAD在候选之前”的数值次序，不认证后方为真息肉面；C `CORRESPONDENCE_UNRESOLVED` 保留其余可投影候选。低循环误差/大深度差不能把C升成A。B中的正Mask矛盾仍需解释，不能自动称合法遮挡。按案例的实际分类数：\n\n'
    text+=mdtable(['视频','A认证','B次序','C对应未决','无该保护代理'],[(sid,0,sum(r.get('conflict_class')=='DISTINCT_SURFACES_OR_OCCLUSION'for r in cases if r['scene']==sid),sum(r.get('conflict_class')=='CORRESPONDENCE_UNRESOLVED'for r in cases if r['scene']==sid),sum(r['status']=='UNKNOWN_NO_PROXY_CANDIDATE'for r in cases if r['scene']==sid))for sid in scenes()])
    text+='\n主参考的位置实例（完整目录仍包含其余来源，不只展示有利参考）：\n\n'
    out=[]
    for sid in scenes():
        primary=next(c['id']for c in D['references']if c['scene_id']==sid)
        for r in cases:
            if r['source_id']!=primary:continue
            out.append((sid,r['region'],r.get('original_face_id','无'),r.get('original_vertex_pixels','无'),r.get('XYZ_mm','无'),r.get('projected_depth_difference_mm','无'),r.get('conflict_class','UNKNOWN')))
    text+=mdtable(['视频','区域代理','原face','原像素(3顶点)','重心XYZ mm','对方射线深度差mm','资格'],out)
    text+='\nE1系统性偏差和E5错误重复面目前均缺认证对应真值。E2统计投影分离候选；E3统计max-edge/像素足迹>8原面；E4统计面积<最大组件1%的小组件；它们不是已确认错误率。E6是全Mask内无原面首交像素，可能是栅格边/连通缺口而非无XYZ；E7另列正Mask/CAD矛盾。E8未知空间不等于已定位的隐藏解剖面；E9明确来源/相机/对应未决。所有分母与级别见 `E3_ERROR_TAXONOMY.csv`。\n\n'
    text+='历史损失分两层：`E3_HISTORICAL_FACE_RETENTION.csv` 统计同一原face-ID的保留/省略面积与保护代理；`E3_HISTORICAL_SOURCE_RAY_COVERAGE.csv` 用现存F1/F2/F3几何和冻结相机查询全部源Polyp像素，记录原有效首交现在miss及替代交点偏移。没有运行新的融合。省略重复原面不等于丢真实覆盖；保留首交也可能击中错误层。原始输入集合不同，不能排名或直接归因算法。\n\n'
    text+='[真实定位图](../figures/Fig3_geometry_failure_cases.png)与[全部历史原面图](../figures/Fig2_existing_HERO_geometry.png)供人工审阅。当前缺人工确认的真实细柄、同一物理面对应和隐藏解剖面标签，因此这些类别的物理准确率为NOT_EVALUABLE。\n'
    write('docs/E3_CONFLICT_CASEBOOK.md',text)
    # Aggregate source denominators, not physical surface union or error truth.
    groups=[]
    for o in org:
        sid=o['scene'];f=[r for r in raw if r['scene']==sid];m=[r for r in miss if r['scene']==sid];p=[r for r in pairs if r['scene']==sid and r['pair_camera_reference_eligible']=='True'];r3=[r for r in ret if r['scene']==sid and r['stage']=='F3'];v3=[r for r in cov if r['scene']==sid and r['method']=='F3_BoundaryGrowth_original']
        groups.append(dict(scene=sid,source_N=len(f),screened_N=len(o['reference_screened_sources']),parent_noncandidate_N=sum(r['camera_parent_candidate_N']=='0'and r['camera_reference_screened']=='True'for r in manifest if r.get('source_id')in CC and CC[r['source_id']]['scene_id']==sid),
            original_faces=sum(int(r['raw_faces'])for r in f),source_raw_area_mm2=sum(float(r['raw_area_mm2'])for r in f),
            stretch_area_percent=100*sum(float(r['stretched_area_proxy_mm2'])for r in f)/sum(float(r['raw_area_mm2'])for r in f),minor_components=sum(int(r['minor_component_proxy_N'])for r in f),
            no_triangle_pixels=sum(int(r['no_raw_first_triangle_N'])for r in m),CAD_positive_contradiction_pixels=sum(int(r['raw_triangle_behind_CAD_positive_Mask_N'])for r in m),
            full_source_Mask_pixels=sum(int(r['full_Polyp_Mask_N'])for r in m),F3_original_area_retained_percent=100*sum(float(r['original_area_retained_mm2'])for r in r3)/sum(float(r['raw_area_denominator_mm2'])for r in r3),
            F3_original_hit_now_miss_pixels=sum(int(r['baseline_raw_hit_now_miss_N'])for r in v3),raw_visible_source_pixel_N=sum(int(r['raw_visible_triangle_N'])for r in v3),
            angle_range_deg=[min(float(r['ROI_camera_direction_angle_deg'])for r in p),max(float(r['ROI_camera_direction_angle_deg'])for r in p)]if p else None))
    save('metrics/E3_REPORT_SUMMARY.json',dict(scene_summaries=groups,all_counts='source occurrences / source area sums; no physical union or GT error',
        source_roles={x:sum(r==x for r in roles.values())for x in set(roles.values())},actual_model_forward_N=0,new_fusion_N=0,optimizer_steps=0,GT_access=False))
    opener='本轮完成 Phase E3-A 的只读科研资产核验与问题定义，未恢复 MonoSDF 路线，也未运行新 HERO、融合优化或训练。主审计覆盖四个物理组、五段视频的三十六份来源，原始面身份均可追溯；另筛查四个物理组的四份旧来源。参考相机筛查与上游相机资格仍有层级差异，不能把资产存在等同于正式认证。实际计算已分开观察方向、原面法向与空间支持，并定位历史覆盖变化、投影错层和 CAD 次序矛盾。局部域、全局 ROI、来源身份与固定评价分母已冻结；同表面纠错真值、严格独立评价视角和真实细柄标签仍不足。本轮只交付可执行、可证伪的合同，不选择下一阶段算法。'
    assert 200<=len(opener)<=350,len(opener)
    text='# E3-A TECHNICAL REPORT\n\n'+opener+'\n\n'
    text+='任务 `TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`；独立分支 `exp/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`；父提交 `fcdcefb13c00a3c940926dd2266137847eb768b6`。当前任务书是执行授权；RA原文是设计依据，其中旧版建议/未授权下一阶段不能取代本轮边界。两份原文均完整读取，SHA及阅读收据见 `provenance/RA_DOCUMENT_ACCESS.json`、`RA_READING_RECEIPTS.json`；v1.1数学约束、v1.2组织规则使用新版优先。\n\n'
    text+='## 固定审计表\n\n'+mdtable(['审计项目','必须汇报'],[
        ('目标组数','主审计4物理组/5视频；G01两视频不是两病例；补充4组仅目录筛查'),('本算法独立成功','测量0/4；本轮没有测量预测。资产审计完成4/4，不能冒充测量正确'),('本算法失败','4/4未执行测量，值NaN；不是4次算法测量失败'),('历史测量值回退','0；未读取旧直径/S0/V2测量或GT补齐'),('失败组及具体原因','G01跨视频未认证及004上游候选；G06链条件；G08 LIMITED；G07相机未合格。见FAILURE_LEDGER.md及案例图'),('最终统计样本','测量0/4；MedARE/MAE/p95/max均NaN；共同成功配对N=0；原面统计为36源观测次数而非独立组数'),('是否使用 GT 选择算法','否；GT/Oracle未读，未选算法。配置/源码/输入SHA及预输出benchmark冻结均保留')])
    text+='\n## 资产与相机资格的实际结果\n\n'+mdtable(['视频','来源/参考筛查/父相机非候选','完整原面','长边面积代理%','小片组件代理','全源Mask像素','无原面首交','正Mask/CAD矛盾'],[(g['scene'],f'{g["source_N"]}/{g["screened_N"]}/{g["parent_noncandidate_N"]}',f'{g["original_faces"]:,}',f'{g["stretch_area_percent"]:.2f}',g['minor_components'],g['full_source_Mask_pixels'],g['no_triangle_pixels'],g['CAD_positive_contradiction_pixels'])for g in groups])
    text+='\n全部36源共1,070,754张原面，已核对原face数组、原顶点、UV与相机往返。40份native是36主目录+4补充目录，94条manifest还含3张照片、36份Cleaned及15份F1/F2/F3场景派生；派生几何不增加独立证据。主参考筛查17份，19份不合格；全部上游相机没有候选状态的8份均在G01_005，仍不等于绝对公制GT认证。旧组级31份NORMAL/LIMITED标签不能替代17份逐参考资格。原始材料依赖本地大文件，本分支只上传审计表、源码、报告和图，不声称远端包含全部输入。\n\n'
    text+='## 来源方向、几何覆盖与历史变化\n\n'+mdtable(['视频','参考对方向差°','方向格代表/全','法向格代表/全','空间格代表/全','F3保留原源面积%','F3原交点变miss/原有效源像素'],[(g['scene'],'未合格'if g['angle_range_deg']is None else f'{g["angle_range_deg"][0]:.2f}–{g["angle_range_deg"][1]:.2f}',f'{o["selected_camera_bins"]}/{o["all_camera_bins"]}',f'{o["selected_normal_bins"]}/{o["all_normal_bins"]}',f'{o["selected_spatial_voxels"]}/{o["all_spatial_voxels"]}',f'{g["F3_original_area_retained_percent"]:.2f}',f'{g["F3_original_hit_now_miss_pixels"]}/{g["raw_visible_source_pixel_N"]}')for g,o in zip(groups,org)])
    text+='\n全部252对同视频有向检查使用预定原索引采样、真实投影和原面/CAD首交。相机角度、共同Mask、原面共投影、方向法向/空间边际覆盖分别计算；数值代理不证明物理同一面。代表角色为来源组织诊断，不是正式优化输入获批。详细来源与边际增益见来源提案和CSV。\n\nF3原面省略量远大于其实际首交缺失量，显示原面数量不能直接解释成可见解剖损失。旧算法的去重、选择和几何修改均可能参与；对同一个源原面可核对省略面积和保护代理，对现存输出可核对固定源像素首交，但没有资格把所有省略面判为真实面遭破坏。输入集不同、源本身有误且对应未认证，因此这些是风险证据，不是公平算法排名或物理错误率。F2未包含的22份growth源写NOT_IN_HISTORICAL_INPUT_SET，不记作零保留。\n\n'
    text+='## 十个问题的明确回答\n\n'
    answers=[
        ('Q1','VERIFIED / CONDITIONAL','共发现40份现存native深度；36主目录具完整可追溯原面，17份参考相机筛查合格可作条件性只读几何实验，8份全上游非候选；其余19主源和4补充源不能直接升级为正式合格输入。严格完整相机链绝对认证数量UNKNOWN，不报40份全部合法。'),
        ('Q2','VERIFIED / CONDITIONAL','G01_004为11源，其中3筛查参考方向差8.50–21.07°，保留三CORE；G01_005为9源/8筛查，2.77–36.70°，三CORE+growth_r20桥。005代表集保留38/38法向格但只有1620/1873空间格。所有主源共享上游相关家族；互补几何不等于独立重复票。详见252对CSV及边际表。'),
        ('Q3','VERIFIED (bounded search)','额外G02–G05目录有4份旧HERO；G04/G05是Is/R10且链不足，G07是Is/R5但不合格。已审计目录额外合格Is/R5=0，未声称全磁盘不存在。'),
        ('Q4','CONDITIONAL / UNKNOWN','已区分系统偏差候选、局部错层、长边延伸代理、小片、重复层候选、缺首交、CAD次序/Mask矛盾、未知和相机/对应不确定。认证同一物理表面深度冲突0；投影残差不能证明E1/E2真误差。A/B/C分别统计，不强行把C变A。'),
        ('Q5','VERIFIED proxies / NOT_EVALUABLE anatomy','36源长边面积比例、小组件、主要连续面、边界及原面位置均已计算；上表为源面积加权代理。288条实际定位含头部/跨Ring/侧面/保护柄/长边/碎片位置。是否真实异常或真实细柄缺人工标签，不声称代理就是错误比例。'),
        ('Q6','VERIFIED bookkeeping / CONDITIONAL physical loss','每源Raw/Cleaned/F2/F3原face保留、面积省略和保护代理损失已落表；108条历史输出固定源射线查询记录原hit变miss和替代层深度差。少面可能去重，多hit也可能错层，真实有效面破坏尚未全部认证；不能拿不同来源集排名。'),
        ('Q7','VERIFIED image/triangle evidence / CONDITIONAL cause','逐源完整Mask内无原面首交与CAD前遮挡矛盾分开列UV/数量。前者包括边界栅格和断裂，不能全叫缺HERO点；只有图像证据而无深度定位的像素不映成假定三维孔洞。见E3_OBSERVED_WITHOUT_TRIANGLE.csv和Fig3/4。'),
        ('Q8','UNKNOWN / CONDITIONAL domain support','固定ROI切片显示无合法原面窄带、域外或CAD后方的证据缺口；仅能支持目录不约束该位置。相机链/真实隐藏面身份不完整，无法认证整个真实背面为Truly-Unobserved；不足处保持UNKNOWN_OR_INSUFFICIENT_EVIDENCE。'),
        ('Q9','VERIFIED specification / NOT_RUN implementation','局部四域和五种距离类型、有限有效符号/权重来源已定义。全局Phi完整ROI有限值须配U/sigma并分开观测/修正/先验/未知/冲突；尚非欧氏SDF。不实现LocalField或全局模型。'),
        ('Q10','VERIFIED preregistration / CONDITIONAL future execution','同来源/同原面/相机/Mask/CAD/ROI/家族/预算/固定分母比较，历史原配置另作面板，保留全部强基线。覆盖与结构优先、miss-inclusive诊断、物理对应资格、保护预算及先验身份必须检查。9目标全有历史暴露，严格独立帧0；没有GT几何准确率宣称。具体算法/拟合预算待PM冻结，不预选赢家。')]
    for q,status,a in answers:text+='### '+q+' — '+status+'\n\n'+a+'\n\n'
    text+='## 合同、验证与限制\n\n局部合同、全局问题、评价协议、假设预注册均在docs目录。108次实际面重心/法向偏移查询全部有限数值校验通过；这只验证表面位置和UDF，不验证全局正负符号。两个121×121固定切片仅是有限查询可视化，没有输出可调用的场、全局Phi或融合优化器。四图均用真实源XYZ/原面/图像，未训练结果没有称新三维重建。\n\n数值完整性与科学资格分开：原面/坐标往返PASS不等于相机绝对正确；无独立对应不报真实深度误差；没有独立视角不报泛化；缺人工结构标签不报细柄准确率；GT未读不报物理测量误差。机器验证与不可评价项见 `metrics/DELIVERY_VALIDATION.json`，失败记录见 `FAILURE_LEDGER.md`。全部历史受保护worktree的HEAD/已有修改与输入SHA在交付前后核对；没有删除旧产物，未修改Ring-First/HERO/CAD/P0/Dxy。\n\n'
    text+='## 四张核心图\n\n'
    for name,label in [('Fig1_sources_and_views.png','完整来源/相机方向/资格'),('Fig2_existing_HERO_geometry.png','全部原面与历史输出、黑色CAD、统一毫米尺度'),('Fig3_geometry_failure_cases.png','实际失败候选、像素与多层证据'),('Fig4_observation_support_domains.png','观测支持/条件自由空间/CAD/Unknown审计')]:text+=f'![{label}](figures/{name})\n\n'
    text+='## PM 接口\n\nE3-A 审计与合同可提交审阅；不等于后续科学算法已经具备真实性PASS。建议E3-B比较局部projective与mesh窄带等资格，E3-C比较support/occlusion/free-space及来源相关性消融，E3-D再比较受保护的非学习/残差/条件推断。相机链、真实对应、人工结构标签和严格独立评价仍是门槛。当前没有选择G0/G1，没有执行E3-B/C/D，没有启动GPU。任务交付后停止等待PM。\n'
    write('TECHNICAL_REPORT.md',text)
    failures=[('F01','科学资格','G01_004','3参考筛查通过但全部上游含候选相机；其余8参考未合格','CONDITIONAL / 未修相机','Fig1; E3_CAMERA_QUALIFICATION.csv'),
        ('F02','科学资格','G01_005','8参考上游均非候选，但同表面对应和绝对公制真值未认证','CONDITIONAL','E3_VIEW_COVERAGE.csv'),
        ('F03','科学资格','G06','4/5参考筛查；上游仍各含候选','CONDITIONAL','Fig1; camera CSV'),('F04','科学资格','G08','2/6参考筛查，LIMITED且上游有候选','LIMITED CONDITIONAL','Fig1; camera CSV'),
        ('F05','科学资格','G07','0/5参考筛查合格，不能进入正常成功分母','UNQUALIFIED_STRESS','Fig1/3'),('F06','来源','照片/跨视频','3张照片无认证K/c2w；G01跨视频fusion_certified=false','不公制融合','CROSSVIDEO_GATE历史哈希; PHOTO manifest'),
        ('F07','物理对应','全部组','同表面独立标签缺失；投影残差/循环/历史匹配不能单独认证','A类认证0，保留C','E3_CASEBOOK_POINTS.csv'),('F08','结构真值','全部组','长边、小片、thin/stalk均为代理，无人工解剖确认','NOT_EVALUABLE','Fig3; 原面定位CSV'),
        ('F09','独立评价','9候选目标','HERO/相机/历史匹配/选择暴露；严格全链路独立帧0','FULL_PIPELINE_INDEPENDENCE_NOT_AVAILABLE','E3_EVALUATION_FRAMES_FROZEN.json'),('F10','公平比较','历史方法','F1/F2/F3输入集不同，过滤F3输出不能恢复共同输入重放','共同输入重放NOT_RUN','E3_BASELINE_INPUT_SCOPES.csv'),
        ('F11','输入缺口','额外Is/R5','有界目录额外合格Is/R5=0；4补充HERO链/原索引未达主目录资格','不强行扩正式组','manifest supplemental rows'),('F12','可见性','全部组','正Mask射线可能落在CAD后方；几何/相机/分割矛盾未决','与无原面首交分列，非自动合法遮挡','Fig3/4; E3_OBSERVED_WITHOUT_TRIANGLE.csv'),
        ('F13','未知区域','全部组','没有全解剖与全部认证视线身份，不能确定真实隐藏面','Unknown保留，不补全','Fig4; 全局合同'),('F14','本地依赖','复现','原生深度/大NPZ/视频/PLY仅只读引用，没有全量上传','路径/SHA缺失应fail closed','INPUT_HASHES.json; REPRODUCE.md'),
        ('ENG01','执行失败','inventory attempt001','重复status关键字导致TypeError；未生成来源结果','修复字段名access_status，不改标准','runtime日志摘要保留于EXECUTION_LOG_INDEX.json'),('ENG02','执行失败','inventory attempt002','补充RESULTS.csv按group查找失败；实际主键为id','修复精确主键；未改资格','EXECUTION_LOG_INDEX.json'),
        ('ENG03','执行失败','geometry attempt001','AST返回namespace未绑定face_components导致NameError，源几何数字输出前停止','显式绑定既有函数；无科学阈值变化','EXECUTION_LOG_INDEX.json'),('ENG04','元数据修正','RA access','早期库存代码把文件存在等同read_complete','修正为按阅读收据SHA；现两全文实际读完','RA_READING_RECEIPTS.json'),
        ('ENG05','绘图修订','Figure2/4','完整长尾范围使主体过小；切片行距不足','增加统一±13mm主窗+完整范围小窗、调行距；不改数据/阈值','FIGURES_LAYOUT002 log; FIGURE_PROVENANCE.json'),
        ('ENG06','案例字段修正','THIN_BASE_PROXY','初次位置选择用了stalk或Ring保护并集，可能只代表Ring邻域','改为仅possible_stalk；无此代理则UNKNOWN，分别输出两种保护flag；未改评价门槛','初版CSV留runtime/CASEBOOK_POINTS_ATTEMPT001.csv；REV002记录')]
    write('FAILURE_LEDGER.md','# E3-A FAILURE LEDGER\n\n审计完成不删除未解决项；失败不能靠重定义资格制造PASS。本轮没有测量，四主物理组测量值均NaN。\n\n'+mdtable(['ID','层级','对象','具体原因','处理/状态','证据'],failures)+'\n逐组证据：\n\n'+mdtable(['组','可审查证据'],[(g,'[相机逐源资格](metrics/E3_CAMERA_QUALIFICATION.csv) · [原面定位](metrics/E3_CASEBOOK_POINTS.csv) · [真实失败图](figures/Fig3_geometry_failure_cases.png) · [来源/视角图](figures/Fig1_sources_and_views.png)')for g in ['G01_004/005（同一物理组）','G06_004','G08_005','G07_004']])+'\n所有失败尝试日志保留在本地runtime，公开[小型执行索引](provenance/EXECUTION_LOG_INDEX.json)保存退出/原因和日志SHA。没有从模型、历史直径或其他路线回退。未运行项目外部“Residual+TSDF”新实验；RA所述旧负面经验未在本轮冒充独立复核。\n')
    write('RESULT_INDEX.md','# E3-A RESULT INDEX\n\n[唯一完整技术报告](TECHNICAL_REPORT.md) · [失败记录](FAILURE_LEDGER.md) · [复现](REPRODUCE.md) · [任务原文](TASK.md)\n\n'+''.join(f'- [{p.name}]({p.relative_to(R)})\n'for d in ['docs','metrics','provenance','config','figures']for p in sorted((R/d).glob('*'))if p.is_file())+'\n原始大资产不复制，见INPUT_HASHES和benchmark。GPU/新HERO/融合优化/模型前向=0。E3-B/C/D等待PM。\n')
    print('E3_REPORT_GENERATED opener_chars',len(opener),flush=True)
if __name__=='__main__':main()
