"""One technical report, failure ledger and final artifact-integrity checks."""
from check_consensus import *
import re
def md(headers,data):
    def cell(x):return str(x).replace('|','/').replace('\n','<br>')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(cell(v)for v in row)+' |\n'for row in data)
def write(name,text):(R/name).write_text(text.rstrip()+'\n')
def summarize():
    ev=rows(R/'VISIBILITY_EVIDENCE.csv');st=rows(R/'metrics/ALL_OBSERVERS_STRATUM_RESULTS.csv');cf=rows(R/'FREE_SPACE_CONFLICTS.csv');ab=load(R/'V0_V3_ABLATION.json');summary=[];sens=[]
    for sid in scene_ids():
        e=[r for r in ev if r['scene']==sid];strata={}
        for name in ['CO_VISIBLE_SMOOTH_PROXY','STRETCH_PROXY','SOURCE_UNIQUE_PROXY','POSSIBLE_STALK_PROXY']:
            rr=[r for r in st if r['scene']==sid and r['variant']=='V3'and r['stratum']==name];n=sum(int(r['candidate_N'])for r in rr);support=sum(int(r['any_external_support_N'])for r in rr);free=sum(int(r['any_free_proxy_N'])for r in rr)
            strata[name]=dict(N=n,valid_other_N=sum(int(r['any_valid_other_source_N'])for r in rr),support_N=support,free_N=free,support_fraction=None if not n else support/n,free_fraction=None if not n else free/n)
        summary.append(dict(scene=sid,source_N=len(scene_sources(sid)),candidate_N=len(e),class_counts=Counter(r['evidence_class']for r in e),strata=strata,
            simultaneous_external_support_and_free_N=sum(int(r['Support_count'])>0 and int(r['Free_space_violation_proxy_count'])>0 for r in e),unique_own_visible_no_V3_opposition_N=sum(r['source_unique_proxy']=='1'and r['own_visible']=='1'and r['Free_space_violation_proxy_count']=='0'for r in e),
            all_geometries_retained=True,RAW_mean_S=ab['ALL_OBSERVERS'][sid]['V3']['raw_channel_mean']['S'],correlation_mean_S=ab['ALL_OBSERVERS'][sid]['V3']['correlation_normalized_channel_mean']['S']))
    for a in IDS:
        for b in scene_sources(CC[a]['scene_id']):
            if a==b:continue
            q=np.load(observer_file(a,b));native_only=q['native_only'];finite=np.isfinite(q['M'])&(q['M']>0);sens.append(dict(origin=a,observer=b,native_V2_free_N=int(q['native_free'].sum()),native_only_with_finite_Raw_N=int((native_only&finite).sum()),native_only_no_Raw_first_hit_N=int((native_only&~finite).sum()),
                native_and_Raw_free_but_target_alignment_failed_N=int((q['native_free']&q['raw_free']&~q['align']).sum()),all_V2_withheld_by_V3_N=int((q['native_free']&~q['free3']).sum()),all_V3_free_N=int(q['free3'].sum()),physical_false_positive_truth='NOT_EVALUABLE'))
    table('metrics/REPRESENTATION_SENSITIVITY.csv',sens);save('metrics/SCIENTIFIC_FINDINGS.json',dict(scenes=summary,engineering='VISIBILITY_RESPONSES_AND_RETENTION_IMPLEMENTED',
        reliable_physical_error_discrimination='NOT_ESTABLISHED',geometry_label_to_hard_global_loss='NOT_READY',same_physical_surface_certified_N=0,all_candidates_retained=True,
        native_only_finite_Raw_N=sum(r['native_only_with_finite_Raw_N']for r in sens),native_only_missing_Raw_N=sum(r['native_only_no_Raw_first_hit_N']for r in sens)))
    return summary
def pct(v):return 'N/A'if v is None else f'{100*v:.2f}%'
def report():
    summary=summarize();ab=load(R/'V0_V3_ABLATION.json');tests=load(R/'metrics/CONSENSUS_VALIDATION.json');modes=rows(R/'MULTIMODAL_DEPTH_CANDIDATES.csv');wins=rows(R/'metrics/RAY_WINDOWS.csv');run=load(R/'provenance/CONSENSUS_RUN_STATUS.json')
    text='# E3-C TECHNICAL REPORT\n\n本轮完成17份原始HERO局部场的多视角可见性证据计算、V0–V3消融及真实射线多峰窗口，但尚不能证明这些证据能可靠识别错误延伸。53,615个冻结原面重心、76个同视频有向来源对形成241,229次候选—观察源查询；所有原始面和候选保留。数值语义、遮挡次序和坐标检查通过，并不等于物理错误分类通过。G01长条代理的合格冲突比例低于光滑共视代理，故不把本轮标签升级为删面依据或全局场硬负监督。\n\n'
    text+='任务 `TASK-E3-C-VISIBILITY-CONSENSUS-001`；分支 `exp/TASK-E3-C-VISIBILITY-CONSENSUS-001`；父提交 `a7c6233f33f9a2ec84b4ce19f668a187bd90b9c8`。本轮直接继承已获PM通过的E3-B；三份场源码和本地场协议字节一致，不调用旧初始化、来源审计、视角选择或融合main。原输入Hash、ROI、来源组织和真实观测分母不变。没有新HERO、CNN、GPU、训练、几何删改或全局拟合。\n\n'
    text+='## 固定审计表\n\n'+md(['审计项目','必须汇报'],[
        ('目标组数','正式3物理组G01/G06/G08、4视频、17源；G01两视频同组。另保留G07压力身份，不纳正式成功率'),
        ('本算法独立成功','证据工程17/17源、76/76有向对完成；不产生新重建或物理测量，可靠物理错误识别未确立'),
        ('本算法失败','科学目标“可靠区分错误延伸与合理/独有表面”未通过证明；测量未执行，沿用4主组测量值均NaN'),
        ('历史测量值回退','0；无S0/V2旧直径/照片或其他预测补齐'),
        ('失败组及具体原因','G01两视频合理性代理也大量冲突；G06/G08无长条样本，不能报0%错误率；G07不合格。逐组链接见FAILURE_LEDGER'),
        ('最终统计样本','53,615固定候选及241,229观察源事件；分层采样频率不是独立病例准确率。测量0/4，MedARE/MAE/p95/max均NaN，共同成功配对N=0'),
        ('是否使用GT选择算法','否；协议与候选在源间证据前冻结，未调阈值、未改评价标准制造科学PASS，未读GT/Oracle')])
    text+='\n## 输入、采样与执行边界\n\n正式源为004三份、005八份、G06四份、G08两份，CORE/BRIDGE/RESERVED及源DAG直接继承。读取E3-B独有格/可见性flag仅作固定采样分层，XYZ/法向/三角面身份始终来自原始Raw。F1/F2/F3最终几何、历史SE3调整面、跨视频融合及E2.7预测没有进入通路。只做运行时原输入完整性断言，不重新进行历史审计。\n\n'
    text+='每源原面按均匀原face索引2048点，加开放边界、可见面、独有格、长边、碎片、Ring邻域和possible-stalk分层，最多3584个重心，联合后排序去重。总53,615张采样面；其余407,408面保持UNASSESSED，不能把重心证据推广为整面/整片真值。BASE是原面总体成员标志，BASE_N并非“只由2048基础抽样选中”的计数。分层重叠允许，频率不外推总体错误率。\n\n'
    text+='两阶段固定全部17源候选与自身原始锚点，只改变**外部观察源**：先12个CORE/BRIDGE，再加入5个RESERVED。REP阶段不宣称只用代表源重建，来源自身从不计为外部票。前阶段142,114次查询，RESERVED增加99,115次；无需25³稠密ROI作为主要采样，没有创建全ROI体积。\n\n'
    text+='## 几何通道与消融定义\n\n候选A的毫米轴向误差沿其非单位射线转到观察源B相机，取区间半宽之和；见合同中的准确公式。Support为冻结宽度的Gaussian响应；Occlusion/Free-space为相反方向sigmoid。前方区间严格分离才计数自由空间冲突，后于首表面只是可能被遮挡。合法不同物理层的身份没有独立真值，不强制把它们当同表面误差。\n\n'
    text+='V0保存数值Support；V1加入可能首表面/CAD遮挡及基本域资格；V2加入最低相机/Polyp Mask/有限深度/CAD合法性下的自由空间代理；V3再加源与观察源原生/Raw一致性、Mask/Ring边缘、首面质量、起源可见性、来源相关性和条件相机代理。Raw UDF仅作几何邻近资格，绝不与轴向差数值平均。\n\n'
    text+='**消融解释限制**：原预注册V0数值Support与V1有效域门控并不完全相同，不能将V0→V1差异全部归于Occlusion。增加了明确标记的观察后`MATCHED_C0_CHANNEL_ADDITION_AUDIT`：只用已冻结同一C0与最低合法域，V0–V2 Support逐点保持一致，再依次加入O/F，V3与原结果完全相同。没有新阈值、场查询或替换原结果；它是控制审计，不冒充新预注册科学假设。图4展示此控制，原结果完整保留在同一JSON和CSV。\n\n'
    text+='原B0内置CAD且任务要求所有自由空间都具合法遮挡次序，因此V2也保留最低CAD/Mask门槛，不故意构造危险的无CAD负票基线。V3增加的是更严格边缘/几何/来源条件；本轮无法单独归因Ring-only的因果收益。数值裸响应始终记录，不能将其当合格负票。\n\n'
    text+='Jaccard归一按真实HERO父RGB集合计算，另报原始计数和归一响应。权重为未校准依赖/质量代理，不是正确概率或独立样本量；共享图像不抹掉独有几何。普通参考筛查链和全部上游非候选链分列，二者都不是绝对相机GT。\n\n'
    text+='## 全部来源后的证据分布\n\n'+md(['视频','源数/候选','MULTI','SINGLE未核验','FREE代理','CAD','对应未决','UNKNOWN','同时有外部S和F'],[(s['scene'],f'{s["source_N"]}/{s["candidate_N"]}',*[s['class_counts'].get(k,0)for k in ['MULTI_SUPPORTED','SINGLE_SUPPORTED_UNVERIFIED','FREE_SPACE_CONFLICT','CAD_OCCLUDED','CORRESPONDENCE_UNRESOLVED','UNKNOWN']],s['simultaneous_external_support_and_free_N'])for s in summary])
    text+='\n标签有优先级：存在合格F时记FREE_SPACE_CONFLICT，但表中仍保存同点的Support/Occlusion等证据，不能把类名当唯一事实。10,205个候选同时收到外部Support和F；高支持不能证明物理准确。CAD标签表示已知源遮挡证据，不认证所有视角都看不见。\n\n'
    text+='## Q1：共同观察的合理表面是否较高Support？\n\n'+md(['视频','共视光滑代理N','存在外部Support','同组仍存在V3自由冲突'],[(s['scene'],s['strata']['CO_VISIBLE_SMOOTH_PROXY']['N'],pct(s['strata']['CO_VISIBLE_SMOOTH_PROXY']['support_fraction']),pct(s['strata']['CO_VISIBLE_SMOOTH_PROXY']['free_fraction']))for s in summary])
    text+='\n**CONDITIONAL / 物理合理性NOT_EVALUABLE**。该分层按源可见、光滑/非长边、非独有格和至少一个合法观察源定义，没有用深度残差或Support选“合理”组。很多候选获得支持，但G01同时有较多冲突；共视/光滑代理不认证同一物理表面，不能宣布真实合理面识别成功。\n\n'
    text+='## Q2：错误延伸是否常违反可靠自由空间？\n\n'+md(['视频','长条代理N','其中可被他源合法观察N','V3冲突候选N','V3冲突比例','对照光滑共视冲突比例'],[(s['scene'],s['strata']['STRETCH_PROXY']['N'],s['strata']['STRETCH_PROXY']['valid_other_N'],s['strata']['STRETCH_PROXY']['free_N'],pct(s['strata']['STRETCH_PROXY']['free_fraction']),pct(s['strata']['CO_VISIBLE_SMOOTH_PROXY']['free_fraction']))for s in summary])
    text+='\n**未证明，当前数据不支持把该代理作可靠错误检测器。** G01_004长条代理仅17/674得到V3冲突（2.52%），005为260/1621（16.04%），低于对照。长条可能在其他源视场外/遮挡后、缺少可靠首面，或因边界/原生-Raw资格未能产生强反证；G01主体也可能受深度/相机偏差、不同层或对应身份未决影响。上述原因未被独立分解成物理错误真值，不能唯一归因。G06/G08长条样本N=0，比例N/A，未修改长边标准造样本。\n\n'
    text+='## Q3：单来源独有侧面能否保留？\n\n**数值守恒VERIFIED；真实侧面身份未认证。** 全部9,637个独有格候选保留，其中7,313个自身可见且无V3合格反对；其余即使出现冲突也保留原几何。没有第二来源不是反对票，遮挡/未知不导致删除。独有格是E3-B原面空间代理，不能保证是已确认真实侧面；图3案例为确定性几何/字典序规则的说明，不是只挑成功样本作统计。\n\n'
    text+='## Q4：Ring后方是否错误记成自由空间？\n\n**数值语义VERIFIED，物理投影资格仍条件性。** 全241,229源间事件中16,548个CAD遮挡事件没有进入V2/V3自由空间冲突；17源各16条真实Ring像素射线的272个控制同样为0。裸sigmoid响应可能非零，但被记录为不可采纳响应。此处保护从最低资格就存在，不能当作V3新产生的检测收益。\n\n'
    text+='## Q5：0.5–1mm分歧是否保留多峰或连续区间？\n\n**候选表示VERIFIED；物理层身份UNRESOLVED。** 16条实际源相机射线保留64个来源标记候选，各视频2条预定0.5–1mm差异窗口均保留起源原面和观察源native深度。原面相交点使用观察源非单位实际射线，t等于其轴向毫米Z；区间用局部平面误差传播，掠视不定不伪造精确边界。没有平均、soft-argmax选层或输出第三层。每Mesh只枚举首次交点加原候选，未声称穷尽所有背层。\n\n'
    text+='## Q6：B0/Raw离散化差异是否制造敏感冲突？\n\n**表示敏感性VERIFIED；真实“虚假冲突率”NOT_EVALUABLE。** 28,137条V2源间冲突中2,939条native判前方而Raw不判：737条有有限Raw首交，可见表示选择会改变判断；另2,202条无Raw首交，可能是开放Mesh缺面，不应全叫重采样假错误。V3对这些全部弃权，合计6,484条未通过强门槛，保留21,653条条件性代理（其中17,268条上下游均非候选链）。这些计数不证明谁更接近真实面，不能把Raw自动当GT。\n\n'
    text+='## 科学判断、消融与下一阶段\n\n四个视频均完成V0–V3，增加RESERVED使24,875个候选的V3类别或S/F计数变化；这是证据增量而非重建精度增量。相关性归一降低重复票质量但不会消除系统偏差：\n\n'+md(['视频','原始S总响应/固定候选','相关性归一S/固定候选'],[(s['scene'],f'{s["RAW_mean_S"]:.5f}',f'{s["correlation_mean_S"]:.5f}')for s in summary])
    text+='\n**总体答案：可以按冻结几何假设区分数值Support、可能遮挡、合格自由空间代理和Unknown；尚不能可靠认证物理同一表面、真实错误延伸或真实独有结构。科学目标未确立，不据此推进标签驱动的全局删改/硬负监督。** 建议PM先审查证据误差/对应资格与未决机制；本轮不扩大参数搜索，不替换输入，不启动全局拟合。\n\n'
    text+='## 验证、失败与可视化\n\n17项数值/守恒检查通过：实际轴向误差传播、非单位射线、CAD不作F、同分母、原面/输入Hash、依赖归一、多峰存活等。补充34条同C0审计检查通过；这些不是“科学检测通过”。整个旧worktree状态和已有修改保留，所有原始面不移动/删除。CSV导出耗时故障和native模式可见性标注修正详见失败记录；均未改判据或模式位置。\n\n'
    for name,label in [('Fig1_multisource_consensus.png','全来源证据'),('Fig2_visibility_channels_and_modes.png','三通道与多峰区间'),('Fig3_extension_and_unique_surfaces.png','延伸/独有候选对比'),('Fig4_multiview_multigroup_ablation.png','多视频、多组与V0–V3')]:text+=f'![{label}](figures/{name})\n\n'
    text+='[失败记录](FAILURE_LEDGER.md) · [后续全局场证据合同](CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md) · [复现](REPRODUCE.md) · [结果索引](RESULT_INDEX.md)。严格全链路独立评价身份沿用父阶段不足，本轮不作泛化/毫米测量准确率宣称。程序查询数在预算内；CSV首次重复解压耗时另录，未采样峰值RAM，不冒称完整性能认证。任务完成后停止，等待PM审计。\n'
    write('TECHNICAL_REPORT.md',text)
    failures=[('SCI01','核心科学门槛','长条代理比光滑共视代理更少被F3标出，无法可靠认证错误延伸','不改误差窗/质量门槛；总体科学资格NOT_ESTABLISHED','[分层结果](metrics/ALL_OBSERVERS_STRATUM_RESULTS.csv) · [图4](figures/Fig4_multiview_multigroup_ablation.png)'),
        ('SCI02','G01_004','长条2.52%冲突，对照光滑共视50.83%；相机上游仍有条件','保留所有源与冲突，不能判谁错','[源矩阵](SOURCE_SUPPORT_MATRIX.csv) · [图1](figures/Fig1_multisource_consensus.png)'),
        ('SCI03','G01_005','长条16.04%冲突，对照45.12%；高Support与冲突可并存','全部8参考保留，包括RESERVED和困难参考','[逐候选证据](VISIBILITY_EVIDENCE.csv) · [图3](figures/Fig3_extension_and_unique_surfaces.png)'),
        ('SCI04','G06/G08','无长条代理样本，不能验收异常识别；相机仍条件性/LIMITED','N=0显示N/A，不报零错误率','[分层结果](metrics/ALL_OBSERVERS_STRATUM_RESULTS.csv) · [图4](figures/Fig4_multiview_multigroup_ablation.png)'),
        ('SCI05','G07','未获父阶段相机资格，不在17正式源','保留压力身份，不因排除它称四物理组数值成功','[父阶段资格](../'+A.name+'/metrics/E3_CAMERA_QUALIFICATION.csv)'),
        ('SCI06','真实物理对应/结构','共同Mask/法向/空间格不认证同表面；无真实错误或侧面标签','物理准确性NOT_EVALUABLE，所有physical_truth保持UNRESOLVED','[合同](CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md)'),
        ('SCI07','表示敏感冲突','737条有限Raw比较发生分歧，2202条缺Raw首交','不把弃权数当纠正真误检；native模式也保留','[表示敏感性](metrics/REPRESENTATION_SENSITIVITY.csv) · [冲突表](FREE_SPACE_CONFLICTS.csv)'),
        ('SCI08','消融归因','原预注册V0/V1的Support资格不同，且B0已有CAD','保留原结果；追加同C0通道控制，明确为观察后审计；不能隔离Ring-only因果收益','[完整消融](V0_V3_ABLATION.json)'),
        ('SCI09','模式/采样局限','每面只用重心；每Mesh仅首次射线交点；误差窗/依赖权重未校准','未采样面UNASSESSED，不能认证全域或穷尽隐藏层','[模式表](MULTIMODAL_DEPTH_CANDIDATES.csv) · [合同](CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md)'),
        ('ENG01','首次CSV导出','逐行重复解压NpzFile造成耗时，完成几何查询后在导出段INT停止','保留未完成gzip与日志；只重做导出，场查询和分数不变','[执行索引](provenance/EXECUTION_LOG_INDEX.json)'),
        ('ENG02','native模式可见性标注','初版使用候选位置的可见性，非native模式自身位置','更正位置上的标志；64模式位置逐项未变，旧表保留runtime','[模式检查](metrics/CONSENSUS_VALIDATION.json)'),
        ('ENG03','图4空分层','G06/G08没有长条样本','显示N/A，未调规则生成样本','[图4](figures/Fig4_multiview_multigroup_ablation.png)'),
        ('ENG04','首次交付链接检查','执行日志索引在链接检查之后才生成，首次报缺链接','把索引生成移到链接检查之前；保留失败日志，不改验证标准','[执行索引](provenance/EXECUTION_LOG_INDEX.json)')]
    write('FAILURE_LEDGER.md','# E3-C FAILURE LEDGER\n\n工程实现完成，科学错误识别门槛未确立。所有源、候选和原面保留；不存在以低冲突/高支持制造物理PASS。\n\n'+md(['ID','对象','具体机制','处置','证据'],failures)+'\n没有物理测量输出，历史测量回退0；测量误差MedARE/MAE/p95/max均NaN，共同成功配对N=0。\n')
    index='# E3-C RESULT INDEX\n\n[技术报告](TECHNICAL_REPORT.md) · [失败记录](FAILURE_LEDGER.md) · [后续证据合同](CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md) · [复现](REPRODUCE.md)\n\n'
    for p in sorted(R.glob('*')):
        if p.is_file()and p.suffix in['.csv','.json']:index+=f'- [{p.name}]({p.name})\n'
    for d in ['figures','metrics','provenance','config']:
        for p in sorted((R/d).glob('*')):
            if p.is_file():index+=f'- [{p.name}]({p.relative_to(R)})\n'
    write('RESULT_INDEX.md',index)
def final_checks():
    allow_manifest();out=[]
    def ck(name,okay,detail):out.append(dict(check=name,status='PASS'if okay else'FAIL',detail=clean(detail)))
    numerical=load(R/'metrics/CONSENSUS_VALIDATION.json');ck('17_numerical_contract_checks',numerical['status']=='PASS_NUMERICAL_EVIDENCE_CONTRACT',len(numerical['checks']))
    audit=load(R/'provenance/MATCHED_C0_ADDITION_AUDIT.json');ck('34_matched_C0_addition_controls',audit['status']=='PASS_C0_CONSTANT',len(audit['checks']))
    ab=load(R/'V0_V3_ABLATION.json');keys=['candidate_N','class_counts','raw_channel_mean','correlation_normalized_channel_mean','all_candidates_retained_N'];ck('supplement_does_not_change_V3',all(audit['results'][stage][sid]['V3'][k]==ab[stage][sid]['V3'][k]for stage in ['REP_OBSERVERS','ALL_OBSERVERS']for sid in scene_ids()for k in keys),'original preregistered results retained, no V3 threshold/decision change')
    ev=rows(R/'VISIBILITY_EVIDENCE.csv');ck('all53615_candidates_present_and_retained',len(ev)==53615 and all(r['geometry_retained']=='1'for r in ev),len(ev))
    n=0
    with gzip.open(R/'metrics/OBSERVATION_SOURCE_EVIDENCE.csv.gz','rt')as f:
        for row in csv.DictReader(f):n+=1
    ck('full241229_observer_rows_gzip_CRC_and_header',n==241229,n)
    ck('all76_same_video_source_pairs',len(rows(R/'SOURCE_SUPPORT_MATRIX.csv'))==76,76)
    findings=load(R/'metrics/SCIENTIFIC_FINDINGS.json');ck('negative_scientific_result_not_hidden',findings['reliable_physical_error_discrimination']=='NOT_ESTABLISHED'and'科学目标未确立'in(R/'TECHNICAL_REPORT.md').read_text(),findings['reliable_physical_error_discrimination'])
    logs=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,last_lines=p.read_text(errors='replace').strip().splitlines()[-2:],local_full_log_retained=True)for p in sorted((R/'runtime').glob('*.log'))];save('provenance/EXECUTION_LOG_INDEX.json',logs)
    missing=[]
    for p in R.glob('*.md'):
        for t in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://'not in t and not t.startswith('#')and not(p.parent/t.split('#')[0]).exists():missing.append((p.name,t))
    ck('all_report_links_resolve',not missing,missing)
    figs=[]
    for p in sorted((R/'figures').glob('*.png')):
        im=Image.open(p);im.verify();figs.append(asset(p))
    ck('four_original_HERO_evidence_figures_decode',len(figs)==4,figs)
    bad=[]
    for p in (R/'code').glob('*.py'):
        tree=ast.parse(p.read_text());compile(tree,str(p),'exec')
        for node in ast.walk(tree):
            if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr in['step','backward','marching_cubes','global_optimization','solvePnP']:bad.append((p.name,node.func.attr))
            if isinstance(node,ast.Import)and any(k.name.startswith(('torch','tensorflow','mast3r','mapanything'))for k in node.names):bad.append((p.name,'model import'))
    ck('code_no_training_global_fit_pose_fit_or_model_import',not bad,bad)
    before=load(R/'provenance/PROTECTED_START.json');after=protected_state();ck('all_historical_worktrees_unchanged',before==after,dict(worktrees=len(before)));save('provenance/PROTECTED_END.json',after)
    ck('exact_E3B_field_code_whitelist_and_protocol_inherited',all(sha(R/'code'/name)==sha(B/'code'/name)for name in['hero_native_adapter.py','projective_local_field.py','mesh_local_field.py'])and sha(R/'HERO_NATIVE_INPUT_MANIFEST.json')==sha(B/'HERO_NATIVE_INPUT_MANIFEST.json')and sha(R/'config/PROTOCOL_FROZEN.json')==sha(B/'config/PROTOCOL_FROZEN.json'),'no E3-B implementation modifications')
    inputs={a['path']:a for r in load(R/'HERO_NATIVE_INPUT_MANIFEST.json')['sources']for a in r['assets'].values()};bad_hash=[p for p,a in inputs.items()if sha(p)!=a['sha256']];ck('original_HERO_camera_CAD_inputs_unchanged',not bad_hash,dict(files=len(inputs),mismatch=bad_hash))
    logs=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,last_lines=p.read_text(errors='replace').strip().splitlines()[-2:],local_full_log_retained=True)for p in sorted((R/'runtime').glob('*.log'))];save('provenance/EXECUTION_LOG_INDEX.json',logs)
    save('provenance/INPUT_HASHES.json',dict(native_inputs=list(inputs.values()),inherited=load(R/'provenance/INHERITED_LOCAL_FIELDS.json'),flag_caches=load(R/'provenance/INHERITED_FLAG_BINDINGS.json'),
        files=[asset(A/'provenance/E3_SOURCE_DAG.json'),asset(A/'config/GLOBAL_ROI_FROZEN.json'),asset(A/'provenance/SOURCE_ROLES.json'),asset(B/'LOCAL_FIELD_MANIFEST.json'),asset(REPO/'visualization/real_p0_renderer.py'),asset(REPO/'visualization/same_camera_scene.py')]))
    save('metrics/DELIVERY_VALIDATION.json',dict(status='PASS_ENGINEERING_DELIVERY'if all(r['status']=='PASS'for r in out)else'FAIL',checks=out,
        scientific_goal='NOT_ESTABLISHED',hard_global_field_loss_readiness='NOT_READY',new_model_forward=0,GPU=0,new_geometry=0,deleted_faces=0,global_fit=0,GT_read=False));table('metrics/DELIVERY_VALIDATION.csv',out)
    freeze('FINAL_CODE_PROTOCOL_FREEZE.json');print('E3C_DELIVERY',sum(r['status']=='PASS'for r in out),'/',len(out),flush=True)
    for r in out:
        if r['status']=='FAIL':print(r,flush=True)
    assert all(r['status']=='PASS'for r in out),'DELIVERY_FAILURE'
def hashes():
    paths=[p for p in sorted(R.rglob('*'))if p.is_file()and not any(v in p.parts for v in['runtime','local_results','__pycache__'])and p.name not in['DELIVERABLE_HASHES.json','RESULT_INDEX.md','EXECUTION_LOG_INDEX.json']]
    save('provenance/DELIVERABLE_HASHES.json',dict(files=[asset(p)for p in paths],exclude='self, runtime/local_results, generated result/log indexes'))
if __name__=='__main__':report();final_checks();report();hashes()
