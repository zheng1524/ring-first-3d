"""One final technical report from frozen numbers; no prediction generation."""
from deliver import *
def table(headers,rows):return '|'+ '|'.join(headers)+'|\n|'+ '|'.join(['---']*len(headers))+'|\n'+'\n'.join('|'+ '|'.join(str(v)for v in row)+'|'for row in rows)+'\n'
def main():
    sums=load(R/'metrics/multigroup_summary.json');regions=load(R/'metrics/novel_regions.json');structures=load(R/'metrics/F2_source_structure_audit.json');ev=load(R/'metrics/evaluation_summary.json');identity=load(R/'metrics/evaluation_support_identity.json');marginal=load(R/'metrics/new_HERO_marginal_validation.json');gate=load(R/'metrics/CROSSVIDEO_GATE.json')
    body='P8/P9已实算并完成本轮：4个独立物理组、5段视频、14份参考（旧9＋新5）；主输入为CLEAN_FOR_FUSION。全部输出保留原始来源XYZ/UV/点ID/原三角面，**没有补面、焊接或移动反投影后的点**。F1是来源块叠加，F2是条件性来源选择，F3未实施。照片3/3仍只有图像与候选关系，未生成公制XYZ。GT模式NONE。\n\n'
    body+='### 冻结规则与真正实现\n\n负责者评分是相机质量×(0.35方向余弦＋0.25法向可靠比例＋0.20原面连续性＋0.10非留出邻帧Mask支持＋0.10保留原面积比例)。方向块候选限18°或同块。实际实现由方向块负责者形成每视频的来源优先序，再用真实相机反向投影逐点分类；**尚不是逐个三维点的全局方向分区优化**。原主来源全部保留，后续只接纳NOVEL候选的原像素8邻接区域≥3点、原面法向可靠比例≥0.5、邻帧Mask支持≥0.65，并只保留有该支持的原点。不是按3D最近距离一票否决新点，也没有平均错层。\n\nEXPLAINED/NOVEL_CANDIDATE/OCCLUDED/GEOMETRIC_CONFLICT/UNKNOWN均逐点保存。反投影轴向容差max(0.5mm,3个像素物理足迹)为诊断判据，不是准确度保证。法向来自原始有效面，≥3邻面且一致性≥0.85；未重新引入被拒绝的掠射角清理。参数及来源顺序分别见[规则](config/aggregation_rules.json)、[先行冻结](provenance/P8_RULES_AND_SOURCE_FROZEN.json)、[负责者](metrics/surface_ownership.csv)。原rules.json未改；分阶段新增参数独立存放。\n\n'
    rows=[]
    for s in sums:
        reg=[x for x in regions if x['scene']==s['scene']and x['method']=='ViewPartition_Cleaned_F2'and x['accepted_N']]
        rows.append([s['scene'],s['condition'],s['references'],s['initial_owner'],s['F2_points'],s['accepted_additional_points'],s['new_HERO_contributed_points'],f'{s["accepted_additional_area_exposure_proxy_mm2"]:.3f}',len(reg),max(x['accepted_N']for x in reg),str(s['single_normal_direction']['normal_bins_2pct'])+'→'+str(s['aggregate_normal_direction']['normal_bins_2pct'])])
    body+=table(['视频','相机条件','参考数','初始主来源','F2点','其他来源接纳点','其中新HERO点','接纳面积暴露代理mm²','接纳源区域','最大区域点','活跃法向格/24'],rows)
    body+='\n所有“接纳”仅表示冻结规则下的有来源候选，不是真实解剖标签。面积代理是原面分摊到点后的暴露量，会包含重复与局部非完整面；**不是去重后的可信新增表面积**。法向24格按当前暴露总量2%定义，分母会变化，不等于真实可见面覆盖率。五个场景都保留初始主来源100%，但其他来源的细柄代理可能被判为重复/冲突而不进入F2，原点仍在F1和逐源NPZ。\n\n'
    body+='### 结构、清理与碎片反例\n\n'
    rows=[]
    for s in sums:
        ss=[x for x in structures if x['scene']==s['scene']and x['rank']>0];nn=next(x for x in ss if x['new_HERO'])
        rows.append([s['scene'],sum(x['became_novel_after_cleaning_raw_explained_N']for x in ss),sum(x['accepted_unreferenced_by_complete_faces_N']for x in ss),nn['accepted_complete_face_components'],f'{nn["accepted_complete_original_face_area_mm2"]:.3f}',f'{nn["largest_complete_source_face_component_mm2"]:.3f}',str(nn['stalk_in_F2_source_N'])+'/'+str(nn['stalk_in_Cleaned_N'])])
    body+=table(['视频','Raw已解释→Clean后接纳点','补充点无完整原面引用','新参考完整原面分量','新参考完整原面面积mm²','新参考最大原面分量mm²','新参考细柄代理F2/Cleaned'],rows)
    body+='\n清理造成的空缺可以被另一个来源标为NOVEL；004出现719点、005出现92点，不能将这些点都解释为新观察方向。新参考的完整原面分量为70/26/22/17/16，且有只剩离散点而没有完整原面的接纳点，说明**连续性问题未解决**。细柄是源像素启发式保护代理，不是人工或GT确认的解剖真值；Cleaned保护层完整保留，F2并未保证所有来源保护点都显示。不能宣称真实细柄已认证无损。详见[结构审计](metrics/F2_source_structure_audit.csv)。\n\n'
    body+='### 真实帧分母与历史强对照\n\n图像评价为完整B Polyp Mask分母、实际点中心z-buffer，CAD遮挡；A颜色来自A源像素，B只参与评价。Full Scene背景单独DISPLAY_ONLY，不混入Polyp指标。表中为帧均值；帧/ROI不当作独立病例，逐帧像素分母和共同支持数见[全部评价](metrics/scene_evaluation.csv)。\n\n'
    rows=[]
    for sid in [s['scene']for s in sums]:
        for e in ev:
            if e['scene']==sid and e['pool']=='ALL_PRE_FROZEN_DIAGNOSTICS':rows.append([sid,e['method'],e['target_frames'],f'{100*e["mean_frame_coverage"]:.2f}%',f'{e["mean_frame_RGB_MAE"]:.3f}',str(e['covered_pixel_exposures'])+'/'+str(e['target_Polyp_pixel_exposures']),f'{e["mean_frame_common_single_MAE"]:.3f}→{e["mean_frame_common_method_MAE"]:.3f}'])
    body+=table(['视频','方法','帧','平均覆盖','RGB MAE/255','覆盖/目标像素暴露','与Single共同支持MAE'],rows)
    body+='\n历史B/C及上轮主体优先结果只读，用同一本轮点中心投影核复算；其输入仅历史参考，本轮含新增参考，不能把全部变化归因于聚合规则。B/C并非其历史Mesh光栅化协议，本表是统一点中心对照。Raw F1/F2和Cleaned F1/F2完整保留，未只展示主方法。T2输入对照及损伤见[清理表](metrics/cleaned_input_audit.csv)，Raw/T2/Cleaned图在P1。\n\n**留出身份复核纠正**：004的两个A阶段HOLDOUT恰为旧ref08/ref13源图，G07一个HOLDOUT为旧ref04源图。这些不能算整条流程的独立验证。只把“未用于新增HERO/新增匹配”的局部身份冻结并不够；已附加独立的source-image SHA审计，原角色和所有数值均保留，未重选更好帧。G08没有预先冻结的独立HOLDOUT，只作既有目标诊断。\n\n'
    rows=[]
    for sid in [s['scene']for s in sums]:
        for e in ev:
            if e['scene']==sid and e['pool']=='NON_SELF_PRE_FROZEN_HELD'and e['method']in ['Single_Cleaned','ViewPartition_Cleaned_F2']:
                fmt=lambda x:'NOT_EVALUABLE'if x is None else f'{x:.3f}'
                rows.append([sid,e['method'],e['target_frames'],fmt(None if e['mean_frame_coverage']is None else 100*e['mean_frame_coverage']),fmt(e['mean_frame_RGB_MAE']),fmt(e['mean_frame_common_single_MAE'])+'→'+fmt(e['mean_frame_common_method_MAE'])])
    body+=table(['视频','方法','非自投影预冻结帧数','覆盖%','独立支持MAE','共同支持MAE'],rows)
    body+='\n以上也不是从未使用历史数据的全流程盲测；G07始终不合格压力测试。005覆盖增益5.21个百分点，但共同MAE16.981→17.025略差；G06增益0.42个百分点，共同MAE21.948→21.949基本不变。G07非自投影压力帧增益7.07个百分点，不能进入正常成功率。004没有满足此口径的帧，G08缺预冻结留出，均不补造成功。\n\n新增HERO的独立归因还固定F2不变，只去掉新来源点：005新增来源的平均覆盖增益约0.31个百分点；G06约0.42个百分点，G08诊断约2.06个百分点；G07非自投影压力帧7.07个百分点。004两个自/旧来源图上仅0.07/1.00个百分点，同时共同MAE恶化2.372→6.771、24.119→27.093。新推理产生XYZ是真的，普遍提高可信解释能力尚无证据。[逐帧边际贡献](metrics/new_HERO_marginal_validation.csv)。\n\n'
    body+='### 跨视频最终门禁：NOT FUSED\n\nPnP/Ring/图像条件形成的边与“可融合表面认证”是两层不同判断。005→004的派生SE(3)存于[CROSSVIDEO_GATE.json](metrics/CROSSVIDEO_GATE.json)，使用MASt3R全图的公制3D–2D约束；不是GT或神经点图坐标。Ring中心约0.393mm、绕法向大约−87.85°的候选旋转约束了一个数值解，两个固定初始化一致也不能证明全局旋转已经正确。\n\n'
    rows=[]
    for x in load(R/'metrics/crossvideo_geometry_validation.json'):rows.append([x['source']+'→'+x['target'],x['source_N'],x['overlap_N'],f'{x["point_to_surface_mm"]["median"]:.3f}',f'{x["point_to_surface_mm"]["p95"]:.3f}',f'{100*x["conflict_area_exposure_fraction"]:.2f}%'])
    body+=table(['方向','源点分母','目标Mask重叠点','点到原面中位mm','p95 mm','重叠轴向冲突面积暴露比例'],rows)
    body+='\n门禁预设：轴向冲突比例≤25%、源点到目标原面中位≤0.75mm、p95≤2mm，并要求双向真实图像支持。**两个几何方向均失败**；图像覆盖/Mask支持虽通过，不能推翻几何冲突。点到面使用全部源点，含无共同观测部分，因此也是诊断量，不是物理精度；重叠轴向冲突66%/70%仍直接否定简单合并。位姿与深度误差仍不能仅凭这些量唯一分离。\n\n位姿图Batch B的cross_video_unified=true只表示条件相机约束连通，最终审计不认可表面统一；独立局部分量及旧状态保留，最终解释见[最终图状态](metrics/POSE_GRAPH_FINAL_REVIEW.json)。跨视频GLB文件明确registration_candidate_not_fused，只把两个有来源局部块置于候选变换中，未焊接去重，也不计新增可信跨视频面积。\n\n'
    for p in ['P8_selective_pointcloud/G01.png','P8_selective_pointcloud/G07_G08.png','P9_final_comparison/G01.png','P9_final_comparison/G01_six_views_not_fused.png']:body+='!['+p+'](figures/'+p+')\n\n'
    body+='P8含3张核心图，P9含4张核心图；P0–P7各阶段均有3张覆盖四组的复合图。另保留5视频原始P0的L1–L5、近相机RGB/深度、XYZ三轴及8组A→B五面板（含跨视频和photo003候选）于本地图库。公开核心图保留全Raw共同窗口，004长异常影响显示尺度，未裁去异常以放大主体。\n'
    update('Batch D — 来源负责制聚合与最终验证',body)
    body='### Q1 代码复用\n\nload_official、原unproject/depth_mesh、原源像素连通、原反向投影classify/source_regions、SameCameraScene与accepted real_p0点绘制均实际复用；HERO/相机/渲染没有第二套内部实现。本轮新增的是调度、ROI坐标映射、派生PnP/Ring约束、方向块与来源选择封装。完整代码入口、文件SHA和[代码复用审计](CODE_REUSE_AUDIT.md)可追溯。\n\n### Q2 四组实际执行\n\nG01两视频各新增1参考，G06/G07/G08各1；四组均实际运行SIFT、MASt3R全图/ROI、2种子PnP/Ring、HERO新推理、Raw/Cleaned F1/F2和真实帧诊断。不是用其他组旧结果冒充验证。总分母4物理组、5视频、14参考、9匹配配对、27匹配臂（18新MASt3R），不把两段G01视频当两病例。\n\n### Q3 观察方向\n\n旧六参考在G01各自视频局部Ring坐标内分布；新004_00与v005_00229距最近旧参考方向10.19°/12.50°。这补足了已有相机候选中的方向空档，尚不能证明真实解剖覆盖。两视频局部Ring绕法向自由度须配准；三照片只有图像与K490假设/候选位姿，没有已认证方向或公制点云。[方向分区](metrics/view_partition.csv)和G01五来源图保留未知项。\n\n### Q4 MASt3R与旧方法\n\nROI显著增加F一致Polyp候选（跨视频118→828、G06 92→750），近BG也保留；但密集相邻输出相关，F一致不是真对应。跨视频旧RoMa194、LightGlue0，MASt3R全图118，不能宣称普遍胜过RoMa。相同新帧没有旧缓存时实际跑SIFT，不借其他旧配对补缺。没有独立匹配真值，准确率/有效对应真值数为NOT_EVALUABLE。\n\n### Q5 相邻刚体关系\n\nG06得到有条件的公制相邻约束并用于新参考；G01跨视频只有条件图像约束，最终几何失败。其余同视频和照片保留候选，G08缺留出。尚无统一独立协议证据证明新刚体比历史LightGlue/RoMa更准确，也未认证解决Ring旋转歧义。21节点、19分量的位姿图只能组织两个条件边，不能制造未知连接。\n\n### Q6 新HERO XYZ\n\n实际5次新推理产生80419个Raw点、75273个Cleaned点，非旧缓存重命名。接纳进F2的新参考点分别1919/308/185/1500/626；源点与原深度、UV、RGB一一对应。新参考有连续片段，同时仍有碎片与异常深度；新XYZ不等于正确新表面。三照片因未认证K/pose，未运行冒充公制的重建。\n\n### Q7 方向负责制是否更连续\n\n相对F1减少显示重复点并保留主来源，但没有证据证明真实表面连续性普遍提升；原面碎片、无完整面点和冲突保存，清理空缺可被重新填入。004新参考让共同RGB误差明显恶化，是重要反例。法向格数量的增长不构成真实新增方向认证。当前简化的“方向负责者→来源序→反投影选择”仍有FUSION_RULE_LIMITED风险。\n\n### Q8 完整场景\n\n004/005均输出多参考Polyp＋实际背景＋黑色CAD局部可见场景，且比单主来源包含更多有来源点；不能称为闭合或真实完整表面。005非自投影覆盖增加但共同误差稍差，004独立留出不足且存在恶化。跨视频只产出NOT FUSED候选，可信独有跨视频面积为NOT_EVALUABLE，不报告为0mm²或新增点成功。\n\n### Q9 跨组证据\n\nG06支持“可复用成熟匹配得到相邻公制约束”，但仅185点、最大新增区域97点、覆盖增加0.42个百分点，否定“新方向必然带来大幅连续新增”的预期。G07仍是相机不合格压力测试，7.07个百分点诊断增益不能算正常成功。G08虽然新增626点，但没有预冻结独立留出且相机有限，不能证明泛化。正常条件只有G01/G06两个物理组；不汇成4/4科研成功率。\n\n### Q10 下一步只优先两项\n\n1. **局部深度一致性与独立视角证据**：先固定真正未作为任何P0源图的验证帧，定位同一区域的系统性深度差；这是66%/70%跨视频冲突和004共同误差恶化的直接证据指向。不继续用刚体把深度错层强拉到一起。\n2. **在已通过局部相机关系的区域验证新参考覆盖**：优先G06式相邻关系，检验新增完整原面而非新增点；修正方向负责制中清理空缺被当新视角和碎片接纳的问题。已有ROI MASt3R可继续作为工具，不急于扩大全局Pose Graph。\n\n停止无界匹配/阈值搜索、对未认证照片直接生成公制面、强行跨视频融合、以更平滑/更多点证明改进和无证据的开放Mesh焊接。本轮不自动执行下一项研究，等待PM与研究者验收。\n'
    update('最终问题回答 Q1–Q10',body)
    body='本轮未开展物理测量或GT评价，Dxy/H95主线完全冻结。因无独立几何真值，三维MAE、相对误差中位、p95、最大误差和共同成功组物理误差均为NOT_EVALUABLE/NaN，不用RGB MAE替代。下表区分工程产物与科学正确性。\n\n'+table(['审计项目','必须汇报'],[
        ['目标组数','4独立物理组（G01/G06/G07/G08），5视频；G01两视频仍1病例'],
        ['本算法独立成功','数值/工程产物4/4组；5/5视频新HERO和F2输出，不等于测量正确'],
        ['本算法失败','数值输出0/4组失败；绝对几何与测量认证4/4组NaN/NOT_EVALUABLE；跨视频融合未通过'],
        ['历史测量值回退','0；B/C与主体优先只作隔离对照'],
        ['失败组及具体原因','G01深度冲突/004非独立留出与误差恶化；G06新增很小/碎片；G07不合格相机；G08有限相机/缺留出；照片3/3未认证，见failure_ledger.csv'],
        ['最终统计样本','工程4/4；正常物理组2/4、压力1/4、有限1/4分列；可靠非自投影留出为G01_005五帧、G06两帧，G07一帧另列；无物理准确率统计'],
        ['是否使用GT选择算法','否；GT文件访问拒绝器、输入/规则/预测/源码SHA先行冻结；未读GT、未用Oracle'],
    ])+'\n工程验证见[最终检查](metrics/final_validation_checks.csv)，11个受保护旧工作空间HEAD/分支/index/脏文件SHA及状态逐项未变。初次Pose Graph不连通、背景包装依赖缺失、D参数误触原规则冻结守卫都保留日志；前两项作最小修复，第三项在算法运行前被拦截并改为独立新增配置，原输入哈希最终一致。没有为填失败而伪造位姿/精度。\n\n展示层：已产出，人工验收待定。融合层：未认证为普遍可信改善，跨视频明确NOT FUSED。物理测量层：NOT_EVALUABLE，无GT。GLB只本地，详见[GLB索引](metrics/GLB_INDEX.csv)；单位GLB米、精确NPZ毫米，源身份保留。\n\n本地根目录：`'+str(R)+'`；[HTML图库](visualizations/index.html)；[复现说明](REPRODUCE.md)。阶段A/B/C提交已推送：`ecfd2647d932365848d76fcd36e76db5a632a457` / `6576c9172fb218bad59147ce04e59be70a3b862a` / `9723cd593523cee0f7a02f08eb898d674c7cb636`；最终Batch D SHA以本分支Git HEAD和最终汇报为准，避免自引用哈希。\n'
    body+='\n最终图片核查还修正了反向跨视频诊断封装的来源身份判断：raw00459字符串包含004，现以显式video字段选择SE(3)方向。A/B配对、冻结变换、预测XYZ及原数值评价均未改变；首版展示配对记录完整保留于D_DISPLAY_PAIRS_INITIAL_TRANSFORM_BINDING.json，修正后重新生成诊断图。该问题只影响发布前的一张反向展示相机封装，不参与配准或最终几何门禁。\n'
    update('验收身份、完整分母与停止',body)
    p=R/'TECHNICAL_REPORT.md';text=p.read_text().replace('状态：RUNNING / EXPERIMENTAL。','状态：COMPLETED / EXPERIMENTAL，等待人工验收。',1);start=text.index('中文摘要：');end=text.index('\n## ',start);abstract='中文摘要：四组实际完成18次官方MASt3R前向、5次冻结HERO新参考推理，以及方向负责制Raw/Cleaned F1/F2聚合。新参考产生80419个Raw XYZ，5视频分别接纳1919/308/185/1500/626个新来源点。005真实非自投影覆盖提高5.21个百分点，G06提高0.42个百分点，但共同支持误差未普遍改善；004有明显恶化和留出身份限制，新增原面仍碎裂。跨视频双向轴向冲突约66%/70%，联合场景明确NOT FUSED。工程实现完成，可信新增解剖面积和绝对精度尚不能认证，三照片未伪造公制XYZ。GT、旧P0、正式相机、HERO权重和Dxy均保持冻结。\n';text=text[:start]+abstract+text[end:];p.write_text(text)
    index();print('Final single technical report updated',flush=True)
if __name__=='__main__':main()
