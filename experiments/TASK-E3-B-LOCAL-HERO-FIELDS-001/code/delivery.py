"""Small report and independent delivery checks; no additional reconstruction."""
from mesh_local_field import *
import re
def md(headers,rs):
    def c(x):return str(x).replace('|','/').replace('\n','<br>')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(c(x)for x in r)+' |\n'for r in rs)
def write(name,text):(R/name).write_text(text.rstrip()+'\n')
def report():
    q=rows(R/'LOCAL_FIELD_QUALIFICATION.csv');coverage=rows(R/'SOURCE_COVERAGE_INCREMENT.csv');domains=rows(R/'LOCAL_FIELD_DOMAIN_STATS.csv');unique=rows(R/'metrics/UNIQUE_GEOMETRY_PRESERVATION.csv');b0=[x for x in q if x['method']=='B0'];b1=[x for x in q if x['method']=='B1'];man=load(R/'HERO_NATIVE_INPUT_MANIFEST.json')
    summary=[]
    for o in ORG:
        sid=o['scene'];rr=[x for x in coverage if x['scene']==sid]
        if not rr:continue
        core=[x for x in rr if x['role']=='CORE'];rep=[x for x in rr if x['role']in['CORE','BRIDGE']];res=[x for x in rr if x['role']=='RESERVED'];u=[x for x in unique if x['scene']==sid];qq=[x for x in b1 if x['scene']==sid]
        summary.append(dict(scene=sid,source_N=len(rr),representative_N=len(rep),RESERVED_N=len(res),raw_faces=sum(int(x['raw_faces'])for x in qq),
            CORE_voxels=int(core[-1]['cumulative_spatial_voxels']),representative_voxels=int(rep[-1]['cumulative_spatial_voxels']),all_voxels=int(rr[-1]['cumulative_spatial_voxels']),RESERVED_added_voxels=sum(int(x['new_spatial_voxels'])for x in res),
            raw_unique_faces=sum(int(x['unique_voxel_raw_faces_N'])for x in u),legal_unique_B1_faces=sum(int(x['unique_raw_faces_legal_B1_N'])for x in u),B0_active_unique_legal_B1_faces=sum(int(x['B0_unique_legal_B1_faces_active_N'])for x in u)))
    save('metrics/RESULT_SUMMARY.json',dict(scenes=summary,source_N=17,field_N=34,original_faces=sum(int(x['raw_faces'])for x in b1),
        original_face_UDF_max_mm=max(float(x['raw_face_centroid_zero_max_mm'])for x in b1),native_zero_max_mm=max(float(x['native_zero_max_mm'])for x in b0),
        B0_original_vertex_band_fraction_min=min(float(x['raw_vertex_native_band_fraction'])for x in b0),source_unique_original_faces=sum(int(x['unique_voxel_raw_faces_N'])for x in unique),
        geometry_deleted=0,geometry_moved=0,GT=False,consensus_readiness='CONDITIONAL_RESEARCH_READY; NOT_FULL_B0_RAW_MESH_EQUIVALENCE; NOT_METRIC_ACCURACY_CERTIFIED'))
    text='# E3-B TECHNICAL REPORT\n\n本轮已在CPU上对E3-A筛查通过的全部17份原始HERO来源构建并实际查询B0投影局部场与B1开放Mesh距离场，共34个场对象。先验证12份CORE/BRIDGE，再纳入全部5份RESERVED，未重新选择参考，未使用历史融合结果生成几何。B1完整保留461,023张原始三角面及其身份；B0原生深度零值正确，但与历史双线性缩放后的Raw Mesh不完全重合，不能声称两者逐面等价。相机、同表面对应和真实结构资格仍有条件性，Unknown及不可靠符号均显式保留。\n\n'
    text+='任务 `TASK-E3-B-LOCAL-HERO-FIELDS-001`；分支 `exp/TASK-E3-B-LOCAL-HERO-FIELDS-001`；直接父提交 `8f5f7ea59efb32a0f633409386431811444ee399`。沿用E3-A已阅读RA v1.2及既有局部合同，本轮明确任务授权覆盖其中“只定义未实现”的旧阶段限制。没有新HERO、历史融合重建、几何清理、全局SDF拟合、GPU或训练。\n\n'
    text+='## 固定审计表\n\n'+md(['审计项目','必须汇报'],[
        ('目标组数','正式3物理组G01/G06/G08、4视频、17来源；G01两视频同一组。另保留G07不合格压力身份。测量分母沿用4主物理组，本轮无测量'),
        ('本算法独立成功','局部场工程构建17/17源、34/34对象，3/3条件性正式组；不等于公制准确性。测量0/4'),
        ('本算法失败','构建失败0/17；B0对历史Raw Mesh完全等价的假设不成立，逐源差异完整保留；G07未构建不计正式成功；测量值均NaN'),
        ('历史测量值回退','0；未用S0/V2旧测量、照片直径或其他预测补齐'),
        ('失败组及具体原因','G01_004/005的原生/Raw离散化差异与相机条件、G06上游候选、G08 LIMITED、G07不合格；逐源链接见FAILURE_LEDGER'),
        ('最终统计样本','17源完整分母；原面统计为源观测次数而非独立解剖面积。测量样本0/4，MedARE/MAE/p95/max均NaN，共同成功配对N=0'),
        ('是否使用 GT 选择算法','否；输入白名单/协议/源码在字段运行前冻结，无GT/Oracle，无参数搜索，无依据结果扩大窄带')])
    text+='\n## 输入白名单和真实生成链\n\n`HERO_NATIVE_INPUT_MANIFEST.json`逐源记录原生深度、Raw XYZ/PLY、原索引、RGB/Mask、全部HERO父图像SHA、K/c2w和CAD。所有正式来源保留E3-A条件性资格；17参考中8份全部父相机非候选，其他仍有上游条件。17个场独立表示各来源，不代表17份独立统计证据。共享RGB家族不删除独有几何，也不能重复投票。\n\n'
    text+='两个G01_005旧native别名指向未融合的360×640缩放包：raw00057、raw00459。本轮通过现存package_surfaces.py追溯到raw/005_supported_refXXXXX.npz的352×640原始网络输出，未新推理。其余15份直接继承已审计native。17份Raw XYZ全部满足“原生深度→历史双线性缩放→原unproject”的一致性，最大允许2e-5mm；Mesh与原face数组及顶点一致。历史生成代码只读审阅，没有运行其模型main。\n\n'
    text+='源目录名含fusion不构成判定依据：只有E3-A指定的单参考Raw资产、且通过原生深度/UV/原面一致性检查才准入。F1/F2/F3最终几何、SE3调整后融合面、跨视频融合和E2.7预测列为`FUSION_OUTPUT_NOT_ALLOWED_AS_INPUT`。运行时几何白名单与路径守卫拦截未准入NPZ/PLY/OBJ；两个实际历史F2/F3路径负例均在读取前被拒绝，记录于provenance。Cleaned仅加载历史标签作可靠性/可视化，原面和原顶点不据此筛除。\n\n'
    text+='## B0 / B1的实际实现\n\nB0.query采用原生最近邻深度采样，`D_native(pi_native(X))-Z_camera(X)`。通过既有scaled_intrinsics精确进行半像素中心换算，冻结物理相机不变；有归档native K时逐项核对。没有插值缺深度或填洞；无效/域外/遮挡/后方超窄带返回NaN和原因。表面带±0.25mm；前方可见段仅是有条件自由空间，不假定ROI入口在物体外，不把未见后方写成inside。CAD首交排序沿用0.002mm数值余量。来源深度在CAD后方时保留矛盾状态，不能据此生成空无负票。\n\n'
    text+='B0在原生深度有效而既有Raw原面射线无交点时，仍可提供原生像素深度位置证据；此时original_face_id=-1并记录NO_ORIGINAL_FACE_AT_RAY，不虚构原面身份，也不能把这类深度位置证据叫完整连续原面。\n\n'
    text+='B1以全部原Mesh做Open3D最近原三角面距离查询。`raw_udf_mm`为诊断通道，独立于监督可见性；活动`value`只在合格表面带/条件自由空间有效，Unknown不赋零。法向朝源相机，边界顶点关联面、非流形邻域、低法向一致性、掠视、最近面竞争或长边代理返回UDF/UNKNOWN_SIGN；不封闭原Mesh。局部有向值仅在冻结条件下给出，不能解释成物体内外。原始face、顶点ID、UV、最近点与重心坐标均可回溯。\n\n'
    text+='最近面距离本身是全原Mesh BVH查询；**竞争筛查是32个最近三角面重心候选的实际三角面距离比较，不能保证发现任意大三角形/折叠的所有竞争面**。因此有向符号一律标LOCAL_CAMERA_ORIENTED_CONDITIONAL，未宣称认证欧氏SDF。UDF仍保留，不为获得符号而移面。边界规则与0.02mm竞争间隙、0.85法向一致性等均在数值输出前冻结，无阈值搜索。\n\n'
    text+='统一接口返回value、field_kind、valid_surface、valid_free、cad_occluded、unknown、sign_status、source_id/family、original_face_id、reliability_factors、reason_codes。向量化结果逐点携带类型，局部有向值与UDF不能直接混为同一标量平均。w_i为未校准质量因子，不是假装正确概率。所有场沿用E3-A冻结单视频ROI；域外只有原面距离诊断，不作为有效场监督。\n\n'
    text+='## 实验1：原始几何与数值资格\n\n'+md(['来源','角色','原面数','B0原顶点在0.25mm带%','B1零距重心/全原面','B1有向局部重心','边界错误符号'],[(x['source_id'],x['role'],x['raw_faces'],f'{100*float(next(z for z in b0 if z["source_id"]==x["source_id"])["raw_vertex_native_band_fraction"]):.3f}',x['raw_face_centroid_zero_N']+'/'+x['raw_faces'],x['conditional_oriented_face_centroid_N'],x['boundary_sign_violations_N'])for x in b1])
    text+='\n全部原面重心UDF最大误差 '+f'{max(float(x["raw_face_centroid_zero_max_mm"])for x in b1):.9g}'+'mm，原生点的B0零值最大误差 '+f'{max(float(x["native_zero_max_mm"])for x in b0):.9g}'+'mm。B1保留的是原始几何数值身份，不是声称这些面真实准确。CAD/自遮挡或Mask资格限制只影响合法监督，未从存储几何删除原面。边界符号违规0；1088次同primitive且仍有向的真实面±0.02mm检查未见反向符号。68项基础控制与51项局部符号/Ring控制均通过；其中缺深度反例只修改临时内存副本，原始HERO从未修改。\n\n'
    text+='B0在原生像素点处精确零值，但历史Raw使用352→360双线性插值形成的开放三角面，本轮B0使用原生最近邻，二者离散化不同。原顶点入带率最低96.8394%（growth_r11），raw00745为97.7745%；不提高0.25mm门槛制造100%。因此“B0完全保留所有历史Raw连续面”不通过。B1提供原面完整距离通道；B0保留原生观测而不冒充原面等价物。\n\n'
    text+='## 实验2–3：真实互补性与独有结构\n\n'+md(['视频','CORE→代表→全部空间格','RESERVED数/新增格','原面数','独有格内原面','B1合法独有面/B0仍活动'],[(s['scene'],f'{s["CORE_voxels"]}→{s["representative_voxels"]}→{s["all_voxels"]}',f'{s["RESERVED_N"]}/{s["RESERVED_added_voxels"]}',s['raw_faces'],s['raw_unique_faces'],f'{s["legal_unique_B1_faces"]}/{s["B0_active_unique_legal_B1_faces"]}')for s in summary])
    text+='\n覆盖以全原面重心0.5mm空间格与12×6朝相机法向格统计，逐源CORE→BRIDGE→RESERVED顺序完全继承E3-A。这里没有为删除异常而过滤原面，也未使用E3-A选择诊断中的长边过滤/1%法向面积激活规则；故这些数不能与E3-A过滤后的格数直接比较成“算法增益”。正常方向格是覆盖代理，不是独立表面真实度。\n\n'
    text+='G01_005的4份RESERVED额外贡献255个空间格，G06的1份RESERVED再增加4格；它们不能被永久排除。B1完整保留全部独有格中的原面，原始UDF零距身份不丢失；B0对其中一部分历史Raw独有面没有活动窄带支持，详见`UNIQUE_GEOMETRY_PRESERVATION.csv`。空间格重合不认证同一物理表面，独有也不等于错误；新增格含原生异常/碎片，不能全称真实新侧面。原有possible_stalk、长边、小片、开放边界只标记表达，没有清理或融合。细柄/基底真实身份缺人工标签，仍NOT_EVALUABLE。\n\n'
    text+='## 实验4：固定ROI完整定义域\n\n每视频使用同一25×25×25固定格点集（15625点），对17源×2表示共531250次格点查询，逐源主状态Surface/Free-space/CAD-occluded/Unknown/Ambiguous严格覆盖全部格点，未知活动值均为NaN。Ambiguous可能与UDF可用标志或Unknown标志并存：主状态是分类展示，布尔旗标说明具体信息可用性，不假称五个布尔互斥。表面窄带很薄，规则粗格点不能作为连续面积或体积精度测量。\n\n'
    text+=md(['视频','B0 Surface/Free/CAD/Unknown/Ambiguous（源次数）','B1 同项'],[(s['scene'],' / '.join(str(sum(int(d[k])for d in domains if d['scene']==s['scene']and d['method']=='B0'))for k in DOMAINS),' / '.join(str(sum(int(d[k])for d in domains if d['scene']==s['scene']and d['method']=='B1'))for k in DOMAINS))for s in summary])
    text+='\n多源只统计布尔证据覆盖并集/重叠，没有聚合标量值、生成统一Mesh或拟合全局函数。所有来源Unknown仅表示该目录证据不足，不认证那里没有息肉或一定存在未知背面。自由空间来源于尚有条件的HERO/相机，未来不能当不可违背的硬负票。\n\n'
    text+='## Q1–Q6明确判断\n\n'
    answers=[('Q1','是：17/17独立来源均有B0/B1可调用对象，34/34已在真实数据查询；12份代表门禁通过后再扩展5份RESERVED。独立对象不等于独立统计证据，相机资格保持条件性。'),
        ('Q2','部分通过且有明确区别：B1全部原面完整、UDF零值/边界/合法域保持；B0原生深度零值和域语义通过，但不与历史插值Raw Mesh逐面等价，因此不能宣布B0完全保持历史Raw连续面。未放宽窄带。'),
        ('Q3','存在实际空间互补：005代表1686格→全部1941格，G06为680→684；004三源1766格，G08两源1627格。它们是有来源Raw几何支持代理；新增格是否真实独立侧面尚未认证。'),
        ('Q4','B1是：所有独有格原面及原始身份保留，无删除/移动；可见性裁剪与数据保留分开。B0有原生/Raw离散化造成的独有面活动窄带缺口，逐源给出，不掩盖；真实细柄准确性尚不可评价。'),
        ('Q5','是：运行白名单、E3-A哈希、原生→Raw一致性及原face数组共同约束，F2/F3路径被实际读取守卫拒绝。未使用历史融合Mesh、历史调整面或E2.7输出，照片与跨视频配准均未参与。'),
        ('Q6','具备有条件进入“无训练、多源可见性共识资格研究”的工程输入条件，可提交PM；不等于统一全局SDF、同表面融合或公制准确性已经通过。下一轮必须保持原面存活，区分B0/B1量纲语义和离散化差异，保留来源相关性/未知/遮挡，不把条件自由空间硬否定独有结构；处理有限竞争筛查、相机不确定和物理对应未决。不得直接启动全局拟合或神经训练。')]
    for k,a in answers:text+='### '+k+'\n\n'+a+'\n\n'
    text+='## 图、复现和停机\n\n'
    for name,label in [('Fig1_multiview_HERO.png','全部17来源、原Mesh、相机'),('Fig2_local_fields.png','真实B0/B1局部场与定义域'),('Fig3_multiview_coverage.png','CORE/BRIDGE/RESERVED真实互补性'),('Fig4_real_geometry.png','原生结构、开放边界与CAD遮挡')]:text+=f'![{label}](figures/{name})\n\n'
    text+='[失败记录](FAILURE_LEDGER.md)、[复现](REPRODUCE.md)、[完整结果索引](RESULT_INDEX.md)。实际CPU控制、输入SHA、执行日志摘要及历史工作区保护快照随分支提交。源CSV中的seconds为ROI查询之前的诊断耗时，不冒充整流程性能或峰值RAM；本轮未测物理准确率。没有继续搜索参数，也没有执行共识融合、全局拟合或训练。交付后停止等待PM。\n'
    write('TECHNICAL_REPORT.md',text)
    ledger=[('S01','B0/Raw不等价','原顶点入带率96.84–100%；部分独有Raw面不被B0活动窄带覆盖','未放宽0.25mm。B1原面保留；B0原生身份/差异并列','[逐源资格](LOCAL_FIELD_QUALIFICATION.csv) · [独有面检查](metrics/UNIQUE_GEOMETRY_PRESERVATION.csv)'),
        ('S02','有向距离资格','边界、掠视、法向不可靠/竞争时无完整物体符号；32重心候选筛查非全局唯一性证明','返回UDF/UNKNOWN_SIGN；有向值仅条件性局部意义','[定义域](LOCAL_FIELD_DOMAIN_STATS.csv) · [真实场](figures/Fig2_local_fields.png)'),
        ('S03','G01_004','3参考仍含候选上游相机、跨来源物理对应未认证','只报告条件性结果，未调相机','[输入资格](HERO_NATIVE_INPUT_MANIFEST.json) · [来源图](figures/Fig1_multiview_HERO.png)'),
        ('S04','G01_005','8参考非候选链仍非GT；原生/Raw重采样导致B0保护缺口','全8源保留，不删困难raw00745或RESERVED','[增量覆盖](SOURCE_COVERAGE_INCREMENT.csv) · [局部场图](figures/Fig2_local_fields.png)'),
        ('S05','G06','4参考有上游条件；growth_r01新增仅4格但不删除','全部保留原面，不把小边际当错误','[完整来源](LOCAL_FIELD_MANIFEST.json) · [覆盖图](figures/Fig3_multiview_coverage.png)'),
        ('S06','G08','2参考LIMITED且上游候选','单列条件结果；不升级为绝对准确','[输入表](HERO_NATIVE_INPUT_MANIFEST.json) · [结构图](figures/Fig4_real_geometry.png)'),
        ('S07','G07','E3-A参考筛查0；本轮17正式源不含G07','继承UNQUALIFIED_STRESS身份，未构建不混正式成功率','[父阶段资格](../'+A.name+'/metrics/E3_CAMERA_QUALIFICATION.csv)'),
        ('S08','真实结构/精度','长边、小片、possible-stalk均无人工真值；独立全链路评价帧0','NOT_EVALUABLE，数值身份保持不等于三维正确','[结构证据](figures/Fig4_real_geometry.png) · [保护表](metrics/SINGLE_SOURCE_UNIQUE_REGIONS.csv)'),
        ('S09','自由空间','HERO/相机可能错误，正Mask与CAD也可能矛盾','条件证据，不作后方不存在/ROI入口外部硬约束','[场域统计](LOCAL_FIELD_DOMAIN_STATS.csv)'),
        ('ENG01','白名单初始化001','注册函数先哈希读取，守卫因尚未注册阻断首次原生NPZ','修复为临时准入指定路径后哈希，失败撤回；未变来源/数值标准','[执行日志索引](provenance/EXECUTION_LOG_INDEX.json)'),
        ('ENG02','字段脚本001/002','validate_local_fields.py两个append多余括号，解析失败；未运行场构建','修复语法；正式运行003记录保留','[执行日志索引](provenance/EXECUTION_LOG_INDEX.json)'),
        ('ENG03','native别名','两个005旧native为未融合缩放包，非真正原生网格','追溯既存raw输出，禁止新推理；全部Raw深度链数值一致','[原生白名单](HERO_NATIVE_INPUT_MANIFEST.json)'),
        ('ENG04','Fig3重叠标记','初版CORE阶段只按前一阶段判新格，未标同阶段多源重叠','改为同时统计活动源格重合；未改覆盖数值或构建标准','[图来源](provenance/FIGURE_PROVENANCE.json)')]
    write('FAILURE_LEDGER.md','# E3-B FAILURE LEDGER\n\n所有17源均计入分母；工程构建成功不能覆盖以下科学限制或失败假设。原失败日志保留本地，SHA与末行摘要公开。\n\n'+md(['ID','对象','失败/限制机制','处置','证据'],ledger)+'\n没有测量输出，沿用主审计四物理组的测量值均NaN，历史测量回退0。本轮不把“所有科学问题已解决”作为PASS定义。\n')
    write('REPRODUCE.md','# E3-B REPRODUCE\n\n仅依赖白名单原始资产和已核验的历史几何函数；大NPZ/PLY/视频/权重不复制。Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；CPU Open3D为原surface_fusion_v3/vendor，CUDA_VISIBLE_DEVICES为空。缺文件/哈希不符必须停止，禁止以旧融合结果、照片、其他预测补齐。\n\n初次执行顺序（必须是父提交8f5f7ea的新隔离分支，不能覆盖本次冻结）：\n\n```bash\nE3B_ROOT=/home/liu/ring_first_3d_e3b/experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001\nE3B_PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python\nexport PYTHONDONTWRITEBYTECODE=1\n"$E3B_PYTHON" "$E3B_ROOT/code/hero_native_adapter.py"\n"$E3B_PYTHON" "$E3B_ROOT/code/validate_local_fields.py"\n"$E3B_PYTHON" "$E3B_ROOT/code/visualize.py"\n"$E3B_PYTHON" "$E3B_ROOT/code/delivery.py"\n```\n\n本次实际运行003完成主检查，随后以`validate_local_fields.py --supplement-only`补充独有Raw面和原始法向/Ring控制；无参数变化。Fig3单独修正同阶段重叠显示。执行索引与代码冻结保存初始和最终状态。初始化器检查父SHA，已提交交付只运行`delivery.py`复核；完整重放应另建隔离目录，不删除父SHA或历史快照检查。\n\n可直接使用场（原始资产存在时，无需本地缓存）：\n\n```python\nfrom projective_local_field import ProjectiveLocalField\nfrom mesh_local_field import MeshLocalField\n# source_id来自HERO_NATIVE_INPUT_MANIFEST，不允许任意融合路径\na = ProjectiveLocalField("G01_005_raw00745")\nb = MeshLocalField("G01_005_raw00745")\nqa, qb = a.query([[0., 0., 1.]]), b.query([[0., 0., 1.]])\n# 按valid_surface/free、cad_occluded、unknown及field_kind解释；Unknown值NaN\n```\n\n坐标是该视频Ring局部毫米，t_hit为轴向Z；原生K通过现有半像素函数换算，无新相机模型。活动value与raw_udf_mm/raw_projective_delta_mm诊断分开。主域标签0 Surface /1条件Free /2 CAD /3 Unknown /4 Ambiguous；reason_codes为位掩码，字典见provenance/QUERY_REASON_CODES.json。竞争只检查32个最近原面重心候选，有向符号条件性，不能作全局物体内外。\n\nLOCAL_FIELD_MANIFEST保存可重建对象的工厂、输入SHA、冻结ROI/协议，而非训练权重。local_results仅存本机查询证据缓存，不是融合Mesh或神经预测；缺缓存仍可从原资产查询。68基础控制+51符号/Ring控制、34资格表、34域表、17来源增量全保留。全部原面/UDF、独有区域保护与来源祖先必须同时复核，不能用B0数值零值代替Raw Mesh等价。\n')
    save('provenance/QUERY_REASON_CODES.json',REASONS)
    fm=load(R/'LOCAL_FIELD_MANIFEST.json');fm['query_contract']=dict(Omega='frozen per-video ROI intersected with source legal support/free/visibility domain',w='reliability_factors, uncalibrated, not a correctness probability',P='native whitelist lineage + original face/vertex/UV identity',unknown='active value NaN',no_global_inside_outside=True)
    fm['preservation_caveat']='B1 immutable all Raw faces; B0 native nearest field not exactly equivalent to historical bilinear-resized Raw Mesh; no band expansion';save('LOCAL_FIELD_MANIFEST.json',fm)
    run=load(R/'provenance/FIELD_RUN_STATUS.json')
    if 'input_access'in run:run['input_open_attempts']=run.pop('input_access')
    run['access_semantics']='E1 audit hook records open attempts before the E3-B guard; denied F2/F3 attempts are negative controls, no file bytes read'
    save('provenance/FIELD_RUN_STATUS.json',run)
    index='# E3-B RESULT INDEX\n\n[技术报告](TECHNICAL_REPORT.md) · [失败记录](FAILURE_LEDGER.md) · [复现](REPRODUCE.md)\n\n'
    index+='\n'.join('- ['+p.name+']('+str(p.relative_to(R))+')'for p in sorted(R.glob('*'))if p.is_file()and p.suffix in['.json','.csv'])+'\n\n'
    for d in ['figures','metrics','provenance','config']:
        index+='\n'.join('- ['+p.name+']('+str(p.relative_to(R))+')'for p in sorted((R/d).glob('*'))if p.is_file())+'\n\n'
    write('RESULT_INDEX.md',index)

def verify():
    allow_manifest();checks=[]
    def ck(name,ok,detail):checks.append(dict(check=name,status='PASS'if ok else'FAIL',detail=detail))
    man=load(R/'HERO_NATIVE_INPUT_MANIFEST.json');q=rows(R/'LOCAL_FIELD_QUALIFICATION.csv');cov=rows(R/'SOURCE_COVERAGE_INCREMENT.csv');d=rows(R/'LOCAL_FIELD_DOMAIN_STATS.csv');un=rows(R/'metrics/UNIQUE_GEOMETRY_PRESERVATION.csv')
    assets={a['path']:a for r in man['sources']for a in r['assets'].values()};bad=[p for p,a in assets.items()if not Path(p).is_file()or sha(p)!=a['sha256']]
    ck('all_frozen_native_input_assets_SHA_unchanged',not bad,dict(asset_N=len(assets),mismatches=bad));ck('17_source_IDS_exactly_inherited',len(man['sources'])==17 and set(r['source_id']for r in man['sources'])==set(IDS),IDS)
    ck('no_fused_geometry_allowed',all(r['original_Mesh_fused_or_deformed']is False for r in man['sources'])and all('/glb/'not in r['assets']['raw_Mesh']['path']and'/pointcloud_blocks/'not in r['assets']['raw_Mesh']['path']for r in man['sources']),'raw XYZ/native resize equality and original face arrays checked independently')
    ck('12_representatives_passed_before_all17',len(load(R/'provenance/REPRESENTATIVE_GATE.json'))==12 and all(r['pass_gate']for r in load(R/'provenance/REPRESENTATIVE_GATE.json')),12)
    ck('34_local_fields_built_and_numerically_checked',len(q)==34 and all(r['numeric_contract_pass']=='True'for r in q),34)
    ck('all5_RESERVED_retained',sum(r['role']=='RESERVED'for r in cov)==5 and len(cov)==17,dict(all_sources=len(cov),reserved=5))
    ck('all461023_original_faces_retained_at_UDF_zero',sum(int(r['raw_faces'])for r in q if r['method']=='B1')==461023 and all(r['raw_face_centroid_zero_N']==r['raw_faces']for r in q if r['method']=='B1'),461023)
    ck('boundary_sign_violations_zero',all(int(r['boundary_sign_violations_N'])==0 for r in q),'topological boundary not closed or assigned global sign')
    ck('34_full_ROI_domain_partitions',len(d)==34 and all(sum(int(r[k])for k in DOMAINS)==int(r['query_N'])==15625 and r['all_unknown_values_NaN']=='True'for r in d),dict(grid_queries=34*15625))
    controls=rows(R/'metrics/CONTROL_TESTS.csv');signs=rows(R/'metrics/LOCAL_SIGN_AND_RING_TESTS.csv');ck('68_real_source_and_invalid_depth_controls',len(controls)==68 and all(r['pass_test']=='True'for r in controls),68)
    ck('51_local_sign_and_real_Ring_controls',len(signs)==51 and all(r['status']=='PASS'for r in signs),dict(checks=51,local_sign_queries=sum(int(r.get('same_primitive_and_oriented_N')or 0)for r in signs)))
    ck('all_source_unique_voxel_faces_kept',len(un)==17 and all(r['unique_voxel_raw_faces_N']==r['B1_unique_faces_UDF_zero_N']==r['B1_unique_faces_original_identity_retained_N']for r in un),sum(int(r['unique_voxel_raw_faces_N'])for r in un))
    fractions=[float(r['raw_vertex_native_band_fraction'])for r in q if r['method']=='B0'];ck('B0_non_equivalence_explicitly_recorded_not_hidden',min(fractions)<1 and'完全等价的假设不成立'in(R/'TECHNICAL_REPORT.md').read_text()or min(fractions)<1 and'不与历史插值Raw Mesh逐面等价'in(R/'TECHNICAL_REPORT.md').read_text(),dict(min_raw_vertex_band_fraction=min(fractions),criterion_unchanged_mm=cfg()['band_mm']))
    before=load(R/'provenance/PROTECTED_START.json');after=protected_state();ck('historical_worktree_HEAD_and_existing_modifications_unchanged',before==after,dict(worktrees=len(before)));save('provenance/PROTECTED_END.json',after)
    neg=load(R/'provenance/FUSION_INPUT_NEGATIVE_CONTROLS.json');ck('actual_F2_F3_input_reads_denied',len(neg)==2 and all(r['status']=='DENIED_BEFORE_FILE_READ'for r in neg),neg)
    # Reconstruct all factories from whitelist using final code; no caches required.
    schema=['value','field_kind','valid_surface','valid_free','cad_occluded','unknown','sign_status','source_id','original_face_id','reliability_factors','reason_codes'];errors=[]
    for cid in IDS:
        s=source(cid);x=s['P'][s['F'][len(s['F'])//2]].mean(0)[None]
        for obj in [ProjectiveLocalField(cid),MeshLocalField(cid)]:
            r=obj.query(x)
            if not all(k in r for k in schema)or r['source_id']!=cid or not np.isnan(r['value'][r['unknown']]).all():errors.append(cid)
    ck('all34_final_factory_query_schemas',not errors,errors)
    codebad=[]
    for p in(R/'code').glob('*.py'):
        t=ast.parse(p.read_text());compile(t,str(p),'exec')
        for n in ast.walk(t):
            if isinstance(n,ast.Import)and any(x.name.startswith(('torch','tensorflow','mast3r','mapanything'))for x in n.names):codebad.append((p.name,'neural import'))
            if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['step','backward','solvePnP','global_optimization','marching_cubes']:codebad.append((p.name,n.func.attr))
    ck('no_training_pose_fit_global_fit_or_isosurface_calls',not codebad,codebad)
    figs=[]
    for p in sorted((R/'figures').glob('*.png')):
        z=Image.open(p);z.verify();figs.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    ck('four_actual_project_figures_decode',len(figs)==4,figs)
    required=['TECHNICAL_REPORT.md','FAILURE_LEDGER.md','REPRODUCE.md','HERO_NATIVE_INPUT_MANIFEST.json','LOCAL_FIELD_MANIFEST.json','LOCAL_FIELD_QUALIFICATION.csv','SOURCE_COVERAGE_INCREMENT.csv','LOCAL_FIELD_DOMAIN_STATS.csv']
    ck('all_required_deliverables_exist',all((R/f).exists()for f in required),required)
    missinglinks=[]
    for p in R.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://'in target or target.startswith('#'):continue
            if not(p.parent/target.split('#')[0]).exists():missinglinks.append((p.name,target))
    ck('all_report_and_figure_links_resolve',not missinglinks,missinglinks)
    logs=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,exception_recorded='Traceback'in p.read_text(errors='replace')or'SyntaxError'in p.read_text(errors='replace'),tail=p.read_text(errors='replace').strip().splitlines()[-1:] )for p in sorted((R/'runtime').glob('*.log'))];save('provenance/EXECUTION_LOG_INDEX.json',logs)
    lineage=[asset(p)for p in [E1/'code/common.py',OLD/'ring_first_v1/scripts/common.py',E0/'code/evidence.py',SPARSE/'code/run.py',REPO/'visualization/real_p0_renderer.py',REPO/'visualization/same_camera_scene.py',A/'provenance/SOURCE_ORGANIZATION.json',A/'provenance/SOURCE_ROLES.json',A/'config/GLOBAL_ROI_FROZEN.json']];save('provenance/REUSED_CODE_AND_E3A_HASHES.json',lineage)
    save('provenance/INPUT_HASHES.json',dict(files=list(assets.values()),additional_sources=man['generation_code'],reused=lineage,GT_read=False))
    save('metrics/DELIVERY_VALIDATION.json',dict(status='PASS_ENGINEERING_INTEGRITY_AND_LOCAL_NUMERICS'if all(r['status']=='PASS'for r in checks)else'FAIL',checks=checks,
        B0_full_Raw_Mesh_equivalence='NOT_PASSED',physical_accuracy='NOT_EVALUABLE',consensus_readiness='CONDITIONAL_RESEARCH_INPUT_READY',GPU=0,model_forward=0,new_fusion=0,global_fit=0,geometry_deletion=0))
    table('metrics/DELIVERY_VALIDATION.csv',checks);freeze('FINAL_CODE_AND_PROTOCOL_FREEZE.json')
    print('E3B_DELIVERY',sum(x['status']=='PASS'for x in checks),'/',len(checks),flush=True)
    for c in checks:
        if c['status']=='FAIL':print(c,flush=True)
    assert all(r['status']=='PASS'for r in checks),'DELIVERY_VALIDATION_FAILED'

def hashes():
    ignore=['runtime','local_results','__pycache__'];p=R/'provenance/DELIVERABLE_HASHES.json';assets=[asset(x)for x in sorted(R.rglob('*'))if x.is_file()and not any(k in x.parts for k in ignore)and x!=p and x.name not in ['EXECUTION_LOG_INDEX.json','RESULT_INDEX.md']];save('provenance/DELIVERABLE_HASHES.json',dict(files=assets,excluded='self, runtime, local_results, generated result/log indexes'))
if __name__=='__main__':report();verify();report();hashes()
