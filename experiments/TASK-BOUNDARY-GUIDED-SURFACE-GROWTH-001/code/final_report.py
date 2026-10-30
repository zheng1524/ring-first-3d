"""Write the single final report from frozen predictions and audited metrics."""
from deliver import *

def table(headers, rows):
    return '|'+ '|'.join(headers)+'|\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('|'+ '|'.join(map(str,r))+'|\n' for r in rows)+'\n'

def main():
    summary=load(R/'metrics/growth_summary.json');ev=load(R/'metrics/crossframe_comparison.json');tri=load(R/'metrics/actual_triangle_crossframe_support.json');new=load(R/'metrics/new_HERO_sources.json');common=load(R/'metrics/identical_common_support_RGB.json');cad=load(R/'metrics/CAD_penetration_diagnostic.json');layers=load(R/'metrics/overlap_layer_diagnostic.json');novel=load(R/'metrics/joint_created_novelty_audit.json');lineage=load(R/'metrics/growth_lineage.json')
    mean=lambda rows,k:float(np.mean([x[k]for x in rows]))
    text='''# 可信边界引导的增量可见表面生长与局部联合配准

状态：**REPORTED / EXPERIMENTAL_RUNTIME_LIMITED，等待PM与研究者验收**。GT使用模式：**NONE**；绝对物理精度及唯一新增解剖面积：**NOT_EVALUABLE**。

中文摘要：本轮按用户最新调整，先以相机质量和连续支持面积选择主体，再从Cleaned F1的完整原始三角面提取连接带及边界延伸；允许已有主体和新补片共同作有界刚体调整。4个独立物理组、5段视频均得到有来源的开放曲面生长版本，共300次接纳、22份成功的新HERO参考。工程上实现了连续原面生长、逐轮边界更新和真实跨帧检验，但未认证整体三维改善：G01错层暴露减少而共同支持RGB误差恶化，联合调整新增CAD穿插；G08优化后的原面投影覆盖略低于优化前。跨视频仅保留局部候选，三照片尚不能提供认证公制曲面。最后两次005推理因CUDA运行失败而停止，不能解释为几何无收益。

## 授权、输入与冻结边界

本轮任务及后续调整分别保存在[TASK.md](TASK.md)、[USER_STEERING.md](USER_STEERING.md)。后者优先于初版“旧主体不可调整”的条款。读取仓库AGENTS、COLLAB_STANDARD、README、baseline计划与历史FINAL_AUDIT后，在独立分支执行；未修改保护状态或创建baseline tag。分支为`exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001`，基础提交`4adfe3aac780bf319aebf9cdd137f42e1e0eb055`。

复用上一轮14份可读参考（9份历史P0、5份上一轮新增参考），本轮24次新HERO尝试中22次成功，最终36份可读参考。没有重新计算已有P0；新增推理使用同一冻结HERO权重与已有相机。原始XYZ/RGB/UV、开放Mesh、旧F1/F2、Type-2规则、Ring CAD、Ring-First及Dxy均未改动。历史值只作对照，不用于填补新路线失败。所有源索引和派生H保留。

相机条件分开：G01/G06为NORMAL_CONDITIONAL（2个独立物理组），G08为LIMITED（1组），G07为UNQUALIFIED_CAMERA_STRESS（1组）。G01两个视频只算一个物理病例。冻结相机关系也不是GT。

|审计项目|必须汇报|
|---|---|
|目标组数|4物理组、5视频；不把300轮或36参考当独立病例|
|本算法独立成功|4/4组、5/5视频产生本路线工程生长输出；物理正确性未认证|
|本算法失败|005新增参考2/7次推理失败；总计2/24。照片公制曲面3/3 NOT_EVALUABLE；跨视频统一融合未通过|
|历史测量值回退|0；无测量输出回退，失败无虚构XYZ/深度|
|失败组及具体原因|G01：共同支持误差恶化、CAD穿插、跨视频/照片候选、CUDA中断；G07：不合格相机；G08：有限相机和联合调整覆盖反例。证据见下表及Fig8/11/12|
|最终统计样本|4组全部保留；原生评价9帧（004为1帧，其余各2帧），63个方法×帧条件；不报告成功率或只选好帧|
|是否使用GT选择算法|否。预测/规则先冻结，GT文件访问被守卫拒绝；未读GT、未用Oracle|

## 主体选择与工程种子

冻结评分为相机质量系数×（0.55最大连续支持面积的同视频归一值＋0.20连续面积比例＋0.15非评价邻帧Mask支持＋0.10可靠法向比例）。仅比较同视频来源，不以GT或评价RGB选主体。逐项评分及原始分母见[main_surface_scores.csv](metrics/main_surface_scores.csv)。这是工程代理评分，不能认证稀疏/密集区域的真实性；005前两名接近，不宣称存在唯一正确主体。

'''
    sels=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'];text+=table(['视频','自动初始主体'],sels.items())
    seeds=load(R/'metrics/engineering_seeds.json');text+=table(['组','F1整来源点','F2接纳点','可恢复完整原面','面积mm²','原面分量'],[[s['group'],s['Cleaned_F1_source_points'],s['F2_accepted_points'],s['F2_complete_original_faces'],f'{s["F2_complete_original_face_area_mm2"]:.6f}',s['face_components']]for s in seeds])
    text+='''ENGINEERING_ACCEPTED_SEED是人工认可几何展示的工程起点，非GT。没有把F1全部蓝点认证为可信；缺乏完整原面的已接受点仍保存在种子缓存，不冒充连续面。初始主体所有Cleaned原面保留，最大主体分量和种子可提供外边界；主体其他小分量保留为辅助层，不自动作为外边界，但仍参与可见性，可能保守阻挡新曲面。Fig8中F3与旧F2的差异也包含初始主体组织方式的差异，不能把所有消失的F2区域说成本轮清理成功。

![工程种子与实际原面](figures/Fig1_engineering_seed_recovery.png)

![G01初始真实边界](figures/Fig2_G01_initial_frontiers.png)

![初始F1/F2及主体](figures/Fig3_F1_F2_selected_initial.png)

## 连续面生长和联合调整的实际实现

从仅被一个完整原三角面使用的边提取边界，区分观测终止、Ring遮挡、深度断裂、清理内孔、选面切口和未知。源XYZ/UV、边ID、法向、源相机单位方向、邻接面、非评价其他帧Mask支持及跨源原面投影支持均存档。清理内孔不作为生长前沿。Mask支持仅是二维支持，不等于独立深度认证。

复用历史反向投影分类，保留EXPLAINED、NOVEL、OCCLUDED、CONFLICT、UNKNOWN。候选必须从重叠连接带出发，沿原面共享边的邻接图扩展，单轮1.5mm，至少4个完整原面；不会生成新三角面或将整片重叠面重新叠加。连接带半径1.5mm、至少12点、法向夹角≤60°、接缝p95≤1.25mm、非评价邻帧Mask支持≥0.70。所有参数见[配置](config/growth_rules.json)，未按目标RGB误差调参。

成熟实现为Open3D GICP；近似平面带退化为稳健单法向point-to-plane偏移，避免虚构切向约束。旧主体/新面刚度3:1，已有补片/新面2:1，在新旧原始连通分量间分配SE(3)校正；两者均可移动。主体累计平移参数≤0.75mm、其他分量≤1.5mm、旋转≤5°，接缝拟合改善至少10%。这仍是局部双块联合调整，**没有实现全局多块联合束调整，也不是自由形变或焊接优化**；刚度和保留辅助层仍含工程保守偏置。

每接纳一块立即更新场景、可见性和实际前沿，再从尚未利用的≥3°方向选择新参考。没有每视频新增参考数量上限。HERO调用、反投影、原网格生成、旧清理与渲染均复用核验过的历史实现。原始native深度与既有显示网格分辨率转换分别保存，不把转换后缓存冒充native预测。

F3-A保留真实原三角面及来源/轮次；F3-B保留实际XYZ和各自源RGB。Raw、S0、每轮、PreJoint同面原坐标、Joint派生坐标均独立保存。所有模型都是开放可见曲面块，未声称闭合或焊接。

'''
    rows=[]
    for s in summary:
        rr=[x for x in new if x['group']+'_'+x['video']==s['scene']];rows.append([s['scene'],s['condition'],str(sum(x['success']for x in rr))+'/'+str(len(rr)),s['accepted_steps'],f'{s["new_complete_original_face_area_mm2"]:.4f}',f'{s["largest_new_complete_source_component_mm2"]:.4f}',f'{s["old_geometry_movement_mm"]["p95"]:.4f}',s['accepted_joint_steps'],s['stop_reason']])
    text+=table(['场景','相机条件','成功/新推理尝试','接纳轮数','新增完整源面mm²代理','最大新增源连通分量mm²','旧S0点位移p95 mm','联合调整轮','停止原因'],rows)
    text+='''面积是新增完整原始面暴露量，不是去重后的解剖面积或认证可信新增面积。300轮并非300个新视角，其中121轮新增面积<0.05mm²。每轮ΔA、接缝、来源和失败候选见growth_steps、patch_candidates、view_search；每轮ΔC见[per_round_crossframe_gain.csv](metrics/per_round_crossframe_gain.csv)，零增益与负增益均保留。

实际有21/300轮的主要重叠锚点来自先前生长块（005为15、G08为6）；其他多依赖主体，主要锚点没有来自旧工程种子的记录。新块确实更新了前沿，但不能据此证明旧种子是增长的因果来源，或每轮都是上一块向外的长链。每轮共享原边保证源内连通，不能保证跨源已形成单一连续拓扑。

边界长度是各源开放边之和，接缝可能重复计数。总边界增长和仍未覆盖的可扩展边增加，意味着补片切口/空隙仍存在，不能用边界变长声称完整性提高。详见[frontier_support_summary.csv](metrics/frontier_support_summary.csv)。

![G06逐轮生长](figures/Fig4_G06_004_incremental_growth.png)

![G07压力测试逐轮生长](figures/Fig5_G07_004_incremental_growth.png)

![G08有限相机逐轮生长](figures/Fig6_G08_005_incremental_growth.png)

![实际旧面和新面联合位移](figures/Fig7_local_joint_before_after.png)

## 冻结真实跨帧检验：覆盖、误差与损伤

9个真实目标帧在生长前冻结，依据相机方向而非最终图像误差选择，新增HERO的参考及源图均排除这些帧。004仅有1张满足排除条件，未伪造第二张。其余各2张。G06/G07/G08旧HERO源列表不完整，不能宣称全流程盲测；这是给定冻结相机的跨帧一致性检查，不是绝对深度精度。

7种方法包含选中主体、S0、历史Cleaned F1、历史F2、本轮全部可用Cleaned F1、PreJoint同面原坐标、Joint。同数据F1对照保留额外参考带来的数据收益，避免将其全部归因于聚合规则。PreJoint是最终选中面恢复原坐标的事后消融，不是独立无优化增长路线。原点中心投影协议未改，B Polyp Mask完整分母；原三角面射线覆盖另列，不能替换旧指标。

'''
    rows=[]
    for s in summary:
        sid=s['scene']
        for method in ['Initial_S0','Historical_F2','AllAvailable_Cleaned_F1','F3_PreJoint_SameFaces','F3_Joint']:
            e=[x for x in ev if x['scene']==sid and x['method']==method];t=[x for x in tri if x['scene']==sid and x['method']==method];rows.append([sid,method,len(e),f'{100*mean(e,"coverage"):.3f}',f'{100*mean(t,"coverage"):.3f}',f'{np.mean([x["RGB"]["MAE"]for x in e]):.3f}'])
    text+=table(['视频','方法','目标帧数','点中心覆盖%','原面射线覆盖%','自身有效支持RGB MAE/255'],rows)
    text+='''以上是逐帧等权平均，跨视频/组不合并成成功率。RGB误差分母随方法变化，必须结合下表**三个方法完全相同像素**的结果；完整63行及像素分母见[crossframe_comparison.csv](metrics/crossframe_comparison.csv)。

'''
    text+=table(['视频/目标','共同像素/完整目标','S0 MAE','PreJoint MAE','Joint MAE'],[[x['scene']+'/'+x['target'],str(x['same_support_N'])+'/'+str(x['target_Polyp_N']),*[f'{x["errors"][k]["MAE"]:.3f}'for k in ['Initial_S0','F3_PreJoint_SameFaces','F3_Joint']]]for x in common])
    text+='''G01的Joint覆盖较S0增加，但较历史F2的点覆盖降低；004原面覆盖85.308%也略低于历史F2的85.817%。005原面覆盖88.206%高于F2的87.656%，共同RGB仍恶化。G08 Joint原面覆盖86.014%低于PreJoint86.221%。没有“联合调整普遍改善真实跨视角解释”的结论。共同RGB也受反光、照明和相机误差影响，不能唯一归因于深度。

历史点中心支持会因小刚体位移发生像素采样更替。G06旧点支持损失11.779个百分点，而旧原面射线支持损失0.411个百分点，两项均公开；保留旧面ID不能叫几何无损。[sampling_vs_surface_change.csv](metrics/sampling_vs_surface_change.csv)保留各视频损失及完整分母。

标准五面板继续使用已认可渲染器：实际点云、源RGB、同相机、黑色实体CAD、真实背景XYZ。背景为冻结深度DISPLAY_ONLY，不混入Polyp指标。多参考F3图的颜色来自各自A来源，明确标注并非单一A；另为各视频保存严格单新参考A→B图。没有用B RGB上色/补几何。所有原主体/F2/F3及侧视图在本地图库可查。

![G06真实跨帧完整场景](figures/Fig10_standard_A_to_B_F3_G06.png)

## 接缝、重复层与原可信区域变化

'''
    rows=[]
    for s in summary:
        sid=s['scene'];steps=load(R/f'metrics/growth_steps_{sid}.json');ls=lambda ver:sum(x['inconsistent_layer_exposure_mm2']for x in layers if x['scene']==sid and x['version']==ver);nv=[x for x in novel if x['scene']==sid];rows.append([sid,f'{np.mean([x["seam_distance_mm"]["median"]for x in steps]):.4f}',f'{np.mean([x["seam_distance_mm"]["p95"]for x in steps]):.4f}',f'{ls("F3_PreJoint_SameFaces"):.4f} → {ls("F3_Joint"):.4f}',f'{sum(x["already_explained_before_joint_area_mm2"]for x in nv):.4f}',f'{sum(x["no_projected_novel_vertex_before_joint_area_mm2"]for x in nv):.4f}'])
    text+=table(['视频','逐轮接缝中位数的均值mm','逐轮接缝p95的均值mm','原面错层暴露Pre→Joint mm²','调整前已被解释的接纳面mm²','调整前无NOVEL顶点的接纳面mm²'],rows)
    text+='''错层统计为有另一来源原面射线命中的源面中心面积暴露，可双向重复计数；并非唯一重叠面积。G01错层暴露明显下降，但G06和G07略增。一部分新增接纳面在移动前已被解释，说明位置调整会制造投影空缺，“新面”不能全部归因于新观察信息。近层重复暴露亦在[overlap_layer_diagnostic.csv](metrics/overlap_layer_diagnostic.csv)保留，未声称全部去重。

原有S0全部源面ID保留、原始连通分量内部刚性不变；但跨块位置和连接发生变化。额外对固定封闭CAD实体作0.02mm容差穿插审计（非息肉GT），结果如下。

'''
    rows=[]
    for s in summary:
        sid=s['scene'];a=next(x for x in cad if x['scene']==sid and x['method']=='F3_Joint');b=next(x for x in cad if x['scene']==sid and x['method']=='F3_PreJoint_SameFaces');rows.append([sid,a['old_initial_inside_N'],a['old_initial_after_joint_inside_N'],a['new_old_point_penetrations_after_joint_N'],str(a['CAD_inside_point_N'])+'/'+str(a['point_exposure_denominator']),f'{a["maximum_inside_depth_mm"]:.4f}',b['CAD_inside_point_N']])
    text+=table(['视频','S0原点在CAD内','同批旧点Joint后在内','新增旧点穿插','全部Joint内点/分母','最大内深mm','PreJoint全部内点'],rows)
    text+='''G01新增19/21个旧点进入CAD实体，**不满足无新增不合理穿插的强验收**。这项检查在冻结输出后进行，未据此调参或重做预测；原坐标版本完整保留。G07原有287点穿插也保留为压力反例。联合配准未把CAD碰撞作为优化约束，因此局部接缝残差改善不能认证物理合理性。

G01头部/细柄/Ring近邻以源Mask连通块和像素邻近作代理，不是解剖GT。004可能细柄代理有0.1669mm²新完整面，005为0；Ring近邻代理分别9.3956/12.6956mm²。类别可重叠。可能真实短柄与异常延长线仍需人工区分，不能宣称柄部完全恢复或异常全部删除。所有原始结构保留，见[G01_region_support.csv](metrics/G01_region_support.csv)及原始/局部图。

![G01旧F1/F2和F3完整范围及同窗放大](figures/Fig8_G01_F1_F2_F3_full_and_zoom.png)

## 跨视频有限补片、照片和实际停止原因

实际执行两个方向的局部连续块试验，没有用整体冲突率直接否定全部局部区域。复用已有MASt3R/Ring H，未新做全局配准。005→004得到354个原面、251个源点、1.1331mm²连续候选，接缝中位0.1823mm/p95 0.2819mm；该次联合校正超出界限未采用，候选沿已有H保留。唯一004独立目标覆盖仍为10254/12966（79.084%），共同RGB MAE 23.9442→23.9461，**没有新增目标覆盖证据**。004→005的连接带试验失败，候选邻帧Mask支持仅0.1429，其余块无有效连接带。两方向及失败均归档，原生场景未被覆盖。

全部跨视频联合展示及GLB标为REGISTRATION_CANDIDATE_NOT_FUSED。六方向仍可见双层和背景错位，不能进入认证统一融合。

![G01候选配准六方向真实点云](figures/Fig11_G01_six_views_candidate_not_fused.png)

三张照片复用真实MASt3R图像对应与已有候选位姿，当前边界附近匹配数848/606/229，其中落在候选投影范围外155/253/59。这些是候选视野缺口线索，不是新表面面积。照片K490未认证、公制位姿仅CANDIDATE；均未生成照片HERO几何，三者新公制面积NOT_EVALUABLE，没有伪造三维相机或XYZ。

最后005的v005_00344、v005_00000在CUDA上传输入时失败；新进程torch CUDA检查也失败，nvidia-smi可见硬件不代表推理可用。22次成功缓存、2次失败日志、未生成几何的真实输入及原驱动停止元数据均保存。005停止原因已由驱动泛化的连续无收益修正为RECONSTRUCTION_FAILED_CUDA_RUNTIME_UNAVAILABLE；没有把运行故障计作几何拒绝，没有重置驱动或冒险覆盖环境。G08 DATA_EXHAUSTED仅指冻结可用相机集合，其余NO_VALID_NEW_VIEW是既定方向/边界门控下的有限结论。

![三照片真实对应和两次GPU失败输入](figures/Fig12_photo_boundary_candidates.png)

## 科研结论与Q1–Q7

1. **Q1，工程种子可否作稳定基础？** 来源和原完整面可精确恢复、被保留，三组均得到后续生长；但未有种子消融，主要锚点并非种子，不能证明其因果收益或物理稳定性。G07/G08质量限制继续保留。
2. **Q2，是否还有真实新方向？** 有，实际成功推理22份新增参考，非仅重复旧参考。它们是冻结相机条件下的观察方向；005最后两帧未完成，不能声称全数据已穷尽。
3. **Q3，是否增加连续原面？** 有，五视频新增源面代理分别17.8053、16.0070、8.8305、5.2470、15.7549mm²；每次为一个源内连通完整面块。跨源全局拓扑连续及唯一真实新增面积尚未认证。
4. **Q4，G01是否转为边界生长组织？** 工程上已实现主面选择、连接带、局部连续外延、旧新面联合调整及来源追踪，未锁死旧主体；仍有旧辅助层偏置、补片碎化、未连接柄部、CAD穿插与跨视频冲突。不能宣称完成完整可见解剖重建。
5. **Q5，改善是否仅视觉？** S0对比的实际原面目标覆盖增加，为真实另一帧提供有限几何解释证据；不等于三维真值精度。历史F2/同数据F1对照和共同RGB反例否定普遍优越性，不能只依靠更整齐的展示。
6. **Q6，照片能否补方向？** 真实对应提示可能互补，但标定/位姿不足，仅图像候选；公制增益NOT_EVALUABLE。
7. **Q7，主要限制？** G01有深度错层、局部配准/观测歧义及聚合约束不足的共同证据，缺少接缝碰撞/独立视角验收；G07首先是相机不合格；G08为有限相机和细小收益。005还受GPU故障截断。不能把所有失败统一归因缺视角或融合规则。

工程实现成功、有限跨帧覆盖支持、仅视觉整齐和失败分别记录。ACCEPTED仅表示算法工程接纳，**不是本轮人工验收**；CANDIDATE/CONFLICT/REJECTED不永久删除原始数据，逐项在[patch_review_ledger.csv](metrics/patch_review_ledger.csv)。本轮不产生正式物理指标，不报告虚构成功率/测量误差。

下一轮仅建议人工评审两项候选：①在既有局部联合配准中加入固定CAD非穿插及预冻结独立视角的接受/回退约束；②核验照片标定和跨视频剩余自由度的可观测性，再判断是否值得继续增长。**停止当前参数搜索、微小补片轮数堆积、未经认证跨视频融合及照片公制面积统计**。本轮到此结束，不自动执行以上建议。

## 复现、模型与交付

本地根目录：`'''+str(R)+'''`。

- [HTML图库](visualizations/index.html)：全部逐轮图、三方法及严格单源A→B、真实背景场景、RGB/深度六视角。
- [RESULT_INDEX.md](RESULT_INDEX.md)：全指标、模型及图片入口。
- [REPRODUCE.md](REPRODUCE.md)：只读缓存复现、版本及命令；默认不运行推理。
- [GLB_INDEX.csv](metrics/GLB_INDEX.csv)：30个本地模型（每视频S0/同面PreJoint/Joint×原面/点云），[跨视频候选索引](metrics/crossvideo_candidate_GLB_INDEX.csv)另含4个。几何原坐标mm，GLB标准单位m；Polyp/Ring/真实Background、source UV/ID/H均保留。PreJoint更适合作未校正基准，Joint仅作待审候选，两者均应检查。
- [OUTPUT_ASSET_INDEX.csv](metrics/OUTPUT_ASSET_INDEX.csv)、[FINAL_CODE_AND_SOURCE_MANIFEST.json](provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json)、[FINAL_VERIFICATION.json](provenance/FINAL_VERIFICATION.json)：本地缓存/源码哈希及保护状态检查。

独立分支增量已完成种子阶段`1f5852c`和三组生长阶段`67e7ac721c82f4153084507939651e255ee06417`；最终提交由Git记录及最终答复给出，避免报告自引用SHA。每阶段分别公开3、4、4张精选PNG。完整Raw/深度/权重/GLB/实验缓存均只留本地，公开源码仅限本轮受控封装及新增代码。原始帧仅作为已授权精选科研组合图的一部分，不另上传原帧资产。仓库未合并主线、未建立科学baseline tag。

本轮未读取GT或更改测量定义。验证覆盖原输入/权重哈希、12个受保护工作空间、源UV/RGB、完整原面连通、逐轮来源单调性、刚体界限、评价帧排除、预测不读取B RGB/Mask、GLB/PNG/HTML可访问性。完整测试见指标和最终核验记录。公开仓库不含原始缓存与权重，不能宣称仅clone即可完整推理复现。
'''
    (R/'TECHNICAL_REPORT.md').write_text(text)
    index()

if __name__=='__main__':main()
