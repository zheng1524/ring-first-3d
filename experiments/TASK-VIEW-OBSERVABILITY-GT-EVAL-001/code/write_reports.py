"""Reports and actual HTML gallery from frozen tables; no scientific computation."""
from io_utils import *
import html
TASK='TASK-VIEW-OBSERVABILITY-GT-EVAL-001'
BRANCH='exp/'+TASK
URL='https://github.com/zheng1524/ring-first-3d/tree/'+BRANCH+'/experiments/'+TASK
def write(name,text):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n')
def table(headers,rows):
    def fmt(v):
        if v is None:return'NaN / NOT_EVALUABLE'
        if isinstance(v,float):return f'{v:.4f}'
        return str(v).replace('|','/').replace('\n',' ')
    return'\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(fmt(v)for v in r)+' |'for r in rows])
def main():
    s=load(R/'metrics/gt_summary.json');h=load(R/'metrics/gt_height_evaluation.json');d=load(R/'metrics/gt_dxy_evaluation.json');sources=load(R/'metrics/source_view_inventory.json');views=load(R/'metrics/view_coverage_summary.json');reproj=load(R/'metrics/a_to_b_results.json');plans=load(R/'metrics/a_to_b_pair_inventory.json');sc=load(R/'prediction_snapshot/B_scenes.json');gtbases=load(R/'metrics/gt_base_geometry.json');depths=load(R/'metrics/within_video_depth_conflicts.json');candidates=load(R/'metrics/photo_pose_candidates.json')
    gthead=table(['物理组','GT H95 mm','有效预测H95范围 mm','有效条件 / 全条件','相机条件'],[[x['group'],s['GT'][x['group']]['H_gt_mm'],x['height_pred_range'],str(x['height_numeric'])+'/'+str(x['height_conditions']),next(c['condition']for c in cases()if c['group']==x['group'])]for x in s['per_group']])
    drows=[]
    for g in ['G01','G06','G07','G08']:
        rr=[x for x in d if x['group_id']==g and x['Dxy_candidate_mm']is not None];drows.append([g,s['GT'][g]['Dxy_gt_mm'],[min(x['Dxy_candidate_mm']for x in rr),max(x['Dxy_candidate_mm']for x in rr)]if rr else None,len(rr),sum(x['group_id']==g for x in d),0,'基底/表面支持/端点条件失败'if g=='G01'else'两端点独立支持均失败'if g=='G06'else'相机不合格，候选也NaN'if g=='G07'else'一端点独立支持失败'])
    dtab=table(['组','GT Feret mm','全部数学候选范围 mm','数学候选数','全条件数','正式成功','主要限制'],drows)
    repotab=table(['配对','姿态状态','共同 / B目标像素','B目标覆盖','外逸 / 全预测像素','RGB MAE /255','角度°(条件)','基线mm(条件)'],[[r['pair_id'],r['status'],f"{r['common_pixels']}/{r['target_Polyp_pixels']}",f"{r['target_coverage']:.2%}",f"{r['predicted_outside_target_pixels']}/{r['prediction_valid_pixels']}",r['RGB_MAE_0_255'],r['conditional_optical_angle_deg'],r['conditional_baseline_mm']]for r in reproj])
    vtab=table(['来源','冻结帧/元数据合格','光轴对本地Ring法向倾角 min/median/max°','同视频最大光轴夹角°','同视频最大基线mm','条件'],[[v['source'],str(v['cached_frames'])+'/'+str(v['qualified_metadata']),v['tilt_to_local_negative_Ring_normal_deg'],v['within_source_max_optical_angle_deg'],v['within_source_max_baseline_mm'],v['quality']]for v in views])
    basetab=table(['组','原顶点','真实底盖原面','底盖面积mm²','连通盘/欧拉数','GT最大高度mm','GT H95mm'],[[r['group'],r['authoring_vertices'],r['cap_faces'],r['cap_area_mm2'],str(r['cap_components'])+'/'+str(r['cap_euler']),r['GT_height_max_mm'],r['H_gt_mm']]for r in gtbases])
    ht=table(['组/场景','源参考','ROI px','H_pred','H_GT','有符号差mm','原状态'],[[r['scene'],r['source_id'],r['roi_id'],r['H_pred_mm'],r['H_gt_mm'],r['error_mm'],r['original_status']]for r in h])
    stats=table(['预指定独立组统计','有效/目标组','MAE mm','中位绝对误差mm','中位绝对相对误差%','p95绝对误差mm','最大绝对误差mm','RMSE mm'],[[name,str(x['numeric'])+'/'+str(x['denominator']),x['MAE_mm'],x['median_abs_error_mm'],x['median_abs_relative_pct'],x['p95_abs_error_mm'],x['max_abs_error_mm'],x['RMSE_mm']]for name,x in [('H95',s['prespecified_group_height']),('3D Dxy数学候选',s['prespecified_group_Dxy_math']),('3D Dxy正式测量',s['prespecified_group_Dxy_formal'])]])
    write('reports/GT_HEIGHT_EVALUATION.md',f'''# 高度独立形状评价

预测值/失败完全来自上一轮冻结结果，无重新拟合。四组GT原文件均按旧用户认可映射+SHA验证；Blender5.0.1只读导出与旧缓存逐顶点/面完全一致。

实际作者底盖为单连通平面盘，不是Ring平面。容差0.0001mm；所有其他顶点在上侧；作者+Z确定方向。没有使用预测平面寻找GT基底。真实部署组织切面对应仍未知，因此模式为 **SHAPE_SCALAR_CONDITIONAL**。完整GT原网格顶点P95和可见P0点P95采样/覆盖不等价；不把下列差值宣称临床或完整自主精度。最大高度与H95分列。

{basetab}

{gthead}

10/27条件有数值，17/27保留不可评价；3/4组至少一条件有数值，但不能挑选最好ROI当病例结果。预指定 main+ROI5–30+core，G01固定004，只有G06/G08有效（2/4）；其完整独立组统计如下。G01_005不是用于替补失败004的病例结果。

{stats}

G01_005四个有效条件误差−3.4031至−3.2491mm；G06 −0.1214至−0.0116mm；G08 −0.3396至−0.1385mm。ROI变化只表示条件敏感性，不是测量重现精度。G01_004基底9/9失败，G07相机3/3失败。不能将这些失败条件的诊断候选计入高度成功。

全部27条件（不是27独立病例）：

{ht}

[CSV](../metrics/gt_height_evaluation.csv) · [基底几何](../metrics/gt_base_geometry.csv) · [GT配对](../metrics/gt_asset_manifest.csv)。实际底盖图LOCAL_ONLY：[查看]({R}/figures/groups/GT_actual_base_caps.png)。''')
    dt=table(['场景','基底参考/ROI','模型','数学候选mm','GTmm','有符号差mm','端点独立支持','正式状态'],[[r['scene'],r['source_id']+'/'+r['roi_id'],r['model'],r['Dxy_candidate_mm'],r['Dxy_gt_mm'],r['error_mm'],r['endpoint_observation_support'],r['original_formal_measurement_status']]for r in d])
    write('reports/GT_DXY_EVALUATION.md',f'''# 三维投影Feret原型：候选误差与正式有效性

正式Dxy主线没有导入、执行或修改。GT按实际作者底盖法向投影全部GT顶点，最大凸包点对给出Feret；与原型数学定义相同，但完整GT和可见/条件支持预测的覆盖不同，基底方向也分别独立估计。没有使用GT部署位姿或ICP。

{dtab}

72/81有数学候选可比较，9/81没有候选；**正式81/81仍NOT_EVALUABLE，0/4组成功**。3/4组有数学候选，不表示3/4正式测量成功。预指定组统计见[高度/配对统计](GT_HEIGHT_EVALUATION.md)，数学MAE1.1877mm来自3/4组，正式MAE为NaN。G06候选比GT小约1.376–1.377mm，G08约0.642–0.650mm。G08相对接近，但一端点缺独立观测支持，不能由GT接近升级成功。

端点支持失败不证明端点本身一定错误：可能因遮挡、Mask、相机、反光或模型本身。候选偏小也不能独断归因HERO；还包含可见边界缺失、基底方向和全形状定义差异。本轮不重选端点、改支持阈值、补面或读取历史直径回填。

全部81条件如下，primary/second/core可能是同一个单参考别名，不是独立样本。

{dt}

[CSV](../metrics/gt_dxy_evaluation.csv)保留原始严格状态、后验定义审计状态、表面比例、足迹比例及所有失败原因。''')
    write('reports/GT_EVALUATION_REPORT.md',f'''# GT身份与评价范围

4/4目标物理组有历史明确用户认可配对记录，原Blender哈希再次一致；无需替换组。仅3/4组有至少一个有效高度条件，固定ROI病例规则为2/4；正式3D Dxy0/4。GT表面误差4/4 NOT_EVALUABLE：没有独立预测—部署GT变换；未用旧Oracle H、未运行ICP。作者GT中无对应部署Ring几何。

GT只读取于本轮预测快照冻结后；历史项目曾暴露GT，不能称从未见GT的盲测。`provenance/PREDICTIONS_FROZEN.json`包含298文件哈希；评价脚本和协议在误差计算前记录哈希。首次评价保存全部表后仅控制台numpy布尔序列化报错，修复输出打印；没有重新计算或调整预测。详见[工程记录](../provenance/ENGINEERING_NOTES.json)。

{basetab}

{stats}

独立配对共同组是G06/G08；高度与Dxy有不同单位含义，不能将二者误差强行做算法配对优劣检验。历史融合对照身份：预测来自冻结主体优先core，primary/second也逐行保留；不是用旧算法预测补值。[全部高度](GT_HEIGHT_EVALUATION.md) / [全部Dxy](GT_DXY_EVALUATION.md)。''')
    failure_rows=[['OBSERVABILITY_LIMITED','部分支持，不能单独解释G01低增益','G06/G07/G08仅一份独立P0；G01未观测背面、照片未接入；无完整真实可见性GT','相机方向差异不直接等价新增面'],['REGISTRATION_FAILED','有数据支持','两视频只有候选H；三照片所有历史正式位姿为空，独立验证未通过','Ring轮廓不确定法向轴旋转，背景近似平面可退化'],['DEPTH_INCONSISTENT','同视频模型不一致得到支持','12个有向参考深度对；00403→08中位|Δz|0.7666mm、00557→459为0.8032mm','深度/相机误差、遮挡均可能，不独断归因HERO'],['FUSION_RULE_LIMITED','有限工程证据','上一轮混合原面一次细分直接恢复0.13938/0.00691mm²候选','新增不是独立认证组织面；不继续放宽阈值'],['SURFACE_SUPPORT_UNCERTAIN','强支持','004/005未知/冲突模型面积多；全GT无真实部署对应','不能认证真假或把条件补片叫真实新增'],['MESH_TOPOLOGY_ISSUE','支持','004主面8→core39分量；0053→9；非流形0不保证连续','来源独立碎片/T连接仍存在'],['PHYSICAL_METRIC_UNRELIABLE','支持','17/27高度条件失败；81/81正式Dxy失败；GT显示G01高度明显偏低','GT底盖与真实组织基底未认证，完整/可见定义差异']]
    write('reports/FUSION_ACCEPTANCE_DEFINITION.md','# 融合不合格的证据分类\n\n多标签可同时出现。依据已冻结表、真实XYZ和独立比较，不能只凭最终网格外观判因。\n\n'+table(['失败类型','本轮判断','主要证据','仍未知/限制'],failure_rows)+'''

本轮没有验收或修改融合器。研究意义上的通过需：可靠共同坐标/尺度、稳定非对称约束、同视频深度冲突被解释、保留原始覆盖、真正新视角支持、来源明确、留出视角无明显恶化、拓扑问题可审查；各证据须独立分母。没有真实部署GT时，不能把展示配准或低RGB误差等同高精度几何认证。

不设置事后新数值门槛来制造通过。G01跨视频与三照片仍NOT_FUSED/UNREGISTERED；单参考组不能计为跨视频融合成功。[深度冲突](../metrics/within_video_depth_conflicts.csv)、[来源支持](../metrics/source_surface_support.csv)、[A→B](../metrics/a_to_b_results.csv)。''')
    source_table=table(['来源','原始资产','现成P0数','相机/关联状态','限制'],[[x['source_id'],Path(x['file_path']).name,len(x['existing_pointcloud']),x['registration_status'],x['failure_reason']]for x in sources])
    write('research/TOP_LEVEL_RESEARCH_HANDOFF.md',f'''# 顶层研究设计者文献调研交接

本文件是实验事实与问题清单，不是文献综述，不替代RA独立审查，也不采用未经审查的新路线。Codex本轮未以关键词搜索决定重大科研路线。

实际主线：Ring-First冻结相机候选→HERO冻结轴向深度→有源像素XYZ/开放Mesh→既有Type-2候选（因结构损伤未采用，Applied仍Raw）→主面优先条件补片/证据分层→背景代理基底H95和独立3D Feret原型。正式Dxy独立冻结。旧源码与大资产只读、本地；无正式认证baseline。

上轮G01的004/005分别只有0.73701/0.83996mm²模型条件补片，冲突约207.5514/110.0452mm²、重复约46.1037/78.5382mm²（多参考面暴露，非解剖面积）。其余三组单参考，不能声称跨组融合通用性。

{gthead}

{dtab}

真实GT底盖可定义作者形状标量；真实部署姿态/组织切面未知，不能独立表面精度评价。27高度条件10有效，81正式Dxy全部失败。三照片有真实RGB/Mask与历史匹配，但光学模式K未知且正式位姿失败。五个G01来源必须分别看待，视频004/005共一物理组，不是两个病例。

{source_table}

{vtab}

请独立从原论文、arXiv、正式开放全文和官方代码核查下列问题。每项方法均填写：数据前提、相机/坐标假设、公制尺度来源、静态/刚体条件、遮挡和高光处理、成功/失败条件、真实内镜证据、GT身份、代码版本/许可证、与本冻结资产的最小兼容改动；不得仅列方法名或漂亮Demo。

1. 内镜多视图几何：在反光/弱纹理/部分遮挡、近似平面组织条件下，怎样独立诊断相机误差与深度错层？全局联合优化需要哪些真实约束？
2. 跨视频注册：圆环中心/法向/尺度之外，如何识别剩余旋转自由度？静态近端背景需要何种非对称/非共面结构，怎样判定退化而不是用ICP低残差宣布成功？
3. 已知标志物辅助位姿：环的对称性、双分支、内参不确定性和遮挡如何进入不确定性评价？独立物理校准的最小数据是什么？
4. 静态照片接入：手机/内镜光学模式及分辨率变化时，现有K490假设何时失效？哪些有界验证能够使用现存资产，不需要再跑完整HERO？
5. 多视角深度/可见表面融合：哪些成熟机制能保留主面、处理系统深度差、保留细蒂且不平均冲突层？何时需要修深度，何时只需改显式表面连接？
6. 遮挡/镜面高光/弱纹理：RGB残差有多大程度可解释为几何，哪些鲁棒或光照不变量有独立证据，而非事后挑选可见区域？
7. 新增表面评价：如何分离重叠点、条件重复面、真实新面、未注册冲突和未知区？需要何种可见GT、留出观测和面积分母？
8. 物理指标：可见点P95与完整GT顶点/面积P95如何匹配定义？作者底盖与真实组织切面需要什么独立证明？Feret极值端点支持应与数学直径、临床直径怎样分开？

待审候选仅两项：①已有相机/静态照片内参模式和跨源几何的独立认证；②在可信相机前提下，研究能解释参考间深度差的成熟多视图联合约束。均交PM/RA评审，不是本轮自动执行计划。停止无界清理阈值搜索、对称环+平面背景的盲目多初始化ICP、GT/Oracle修正正式预测、把点数/平滑/低同帧RGB误差当精度。''')
    # Actual local HTML links all complete artifacts, including every candidate/failure.
    gallery=R/'visualizations';gallery.mkdir(exist_ok=True)
    def href(p):return html.escape(os.path.relpath(p,gallery),quote=True)
    chunks=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>'+TASK+'</title><style>body{font:16px sans-serif;max-width:1600px;margin:auto;padding:24px}img{width:100%;height:auto}article{border-top:1px solid #aaa;margin:32px 0}code{overflow-wrap:anywhere}a{color:#1264a3}</style><h1>'+TASK+'</h1><p>REPORTED / DIAGNOSTIC ONLY；GT形状条件评价，未认证自主几何；22完整A→B，失败保留。</p>']
    for label,p in [('完整技术报告',R/'TECHNICAL_REPORT.md'),('结果索引',R/'RESULT_INDEX.md'),('GT高度',R/'reports/GT_HEIGHT_EVALUATION.md'),('GT Dxy',R/'reports/GT_DXY_EVALUATION.md'),('来源清单',R/'metrics/source_view_inventory.csv'),('顶层研究交接',R/'research/TOP_LEVEL_RESEARCH_HANDOFF.md'),('上轮完整分层/GLB索引',PREV/'visualizations/index.html')]:chunks.append(f'<p><a href="{href(p)}">{label}</a></p>')
    core=['G01_camera_view_coverage.png','G01_source_surface_support.png','A_to_B_core_review.png','GT_metric_summary.png']
    for n in core+['source_registration_graph.png','G01_view_direction_distribution.png','groups/all_photos_input_audit.png','groups/GT_actual_base_caps.png']:
        p=R/'figures'/n;chunks.append(f'<article><h2>{html.escape(n)}</h2><a href="{href(p)}"><img loading="lazy" src="{href(p)}"></a></article>')
    for r in reproj:
        p=R/r['figure'];chunks.append(f'<article><h2>{html.escape(r["pair_id"])}</h2><p>{html.escape(r["status"])}；共同支持 {r["common_pixels"]}/{r["target_Polyp_pixels"]}；MAE {r["RGB_MAE_0_255"]:.2f}/255。<a href="{href(R/r["prediction_file"])}">实际射线结果NPZ（LOCAL_ONLY）</a></p><a href="{href(p)}"><img loading="lazy" src="{href(p)}"></a></article>')
    chunks.append('</html>');write('visualizations/index.html','\n'.join(chunks))
    assetfiles=sorted(p for base in ['figures','local_results','evaluation_only','prediction_snapshot']for p in (R/base).rglob('*')if p.is_file());both('local_asset_index',[dict(path=str(p),relative_path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),status='PUBLIC_CORE'if p.parent==R/'figures'and p.name in core else'LOCAL_ONLY')for p in assetfiles])
    write('RESULT_INDEX.md',f'''# 结果入口

任务：{TASK}，四物理组、五已有局部场景；22完整重投影（14同视频、2跨视频候选、6照片目标候选），另88个来源方向因缺失/未注册不执行。没有新重建/融合/训练。

本地根目录：`{R}`  
[完整技术报告]({R}/TECHNICAL_REPORT.md) · [直接打开HTML图库]({gallery}/index.html) · [本地图像目录]({R}/figures/) · [本地所有A→B]({R}/figures/A_to_B/)

GitHub实验：[目录]({URL})。完整XYZ/GT/射线缓存及其余图像为LOCAL_ONLY，不能称已公开同步。

公开核心图：

1. [五来源相机/轨迹/方向/连接图](figures/G01_camera_view_coverage.png)
2. [四组来源支持与冲突](figures/G01_source_surface_support.png)
3. [标准五面板：好/有限/压力案例](figures/A_to_B_core_review.png)
4. [高度与Dxy形状GT条件评价](figures/GT_metric_summary.png)

[GT身份与配对](metrics/gt_asset_manifest.csv) · [高度27条件](metrics/gt_height_evaluation.csv) · [Dxy81条件](metrics/gt_dxy_evaluation.csv) · [独立组固定条件统计](metrics/gt_group_prespecified.csv) · [全部21来源](metrics/source_view_inventory.csv) · [62相机帧](metrics/camera_frame_inventory.csv) · [480对视角/来源](metrics/view_pairwise_metrics.csv) · [来源支持](metrics/source_surface_support.csv) · [110条A→B候选/缺失清单](metrics/a_to_b_pair_inventory.csv) · [22实测结果](metrics/a_to_b_results.csv) · [12同视频有向深度冲突](metrics/within_video_depth_conflicts.csv) · [本地资产SHA](metrics/local_asset_index.csv)。

[高度分报告](reports/GT_HEIGHT_EVALUATION.md) · [Dxy分报告](reports/GT_DXY_EVALUATION.md) · [GT审计](reports/GT_EVALUATION_REPORT.md) · [融合失败定义](reports/FUSION_ACCEPTANCE_DEFINITION.md) · [顶层设计者交接](research/TOP_LEVEL_RESEARCH_HANDOFF.md) · [复现](REPRODUCE.md)。

完整每张A→B图文件名、NPZ、输入SHA、数值均见`metrics/a_to_b_results.csv`；本地HTML直接展示全部22图。上轮10个GLB保持原路径不改：[上轮索引]({PREV}/RESULT_INDEX.md)。本轮不生成新的融合GLB。
''')
    absum='本轮冻结上一轮298项预测资产，仅对四个物理组开展GT与可观测性评价，不重跑重建或融合。四组Blender原文件、单位和实际平坦底盖均已核验，但真实部署坐标和组织切面对应仍未知。27个高度条件中10个有数值：G06/G08与形状GT较接近，G01_005明显偏低，004基底及G07相机条件失败。72个Dxy数学候选可比较，81个正式状态仍全为不可评价。审计21个原始来源和62个冻结相机帧，完成22张标准A→B图；照片及跨视频只保留历史候选。证据表明参考间深度不一致、注册未认证和观测支持不足共同限制融合，不能只归因于融合阈值。全部原始点、旧结果及正式Dxy未改。'
    main=f'''# {TASK}

状态：**REPORTED / EXPERIMENTAL — SHAPE-SCALAR GT CONDITIONAL; NO NEW FUSION**；等待PM与研究者验收。日期：2026-10-28（Asia/Shanghai）。

## 中文摘要

{absum}

## 快速查看与复现身份

真实仓库根：`{REPO}`；新分支`{BRANCH}`；任务从已实存、干净的上一轮`67ad7cc51a7f8e132d5e77e58deebf6d331efbba`创建独立worktree。正式baseline仍未认证，沿用用户明确科研授权；没有更改相机/HERO/P0/清理/正式Dxy。先读AGENTS、COLLAB标准、README、BASELINE清单和旧FINAL_AUDIT副本。

本地结果：[目录]({R}/) · [HTML图库]({gallery}/index.html) · [全部图]({R}/figures/) · [22张五面板]({R}/figures/A_to_B/)。GitHub：[实验目录]({URL})。指标与完整索引见[RESULT_INDEX](RESULT_INDEX.md)，复现见[REPRODUCE](REPRODUCE.md)。第一阶段真实提交`ef00b45`保存源码/协议/冻结配对；后续真实SHA由git日志给出，不在被其自身提交的报告中伪造自引用SHA。

预测快照在本轮首次打开GT前形成，298文件SHA+7份表快照；预测仍来自上一轮同一路线，历史值回退0。所有Raw/候选/主面core/证据层、来源索引、相机与高度方法原样保留。以前任务曾读取GT，本轮不是严格从未接触GT的盲测。

## A｜形状GT独立评价与边界

配对依据是历史明确用户认可的物理组映射和原文件SHA，**不是根据文件名、形状或误差猜配对**。实际Blender只读导出4/4，与历史顶点/面完全一致。四个底盖均为有正面积、单连通、欧拉数1的平面盘，其余顶点在上方；按冻结0.0001mm容差，以实际作者底盖和+Z法向定义基底。

{basetab}

GT模式为 **SHAPE_SCALAR_CONDITIONAL**：作者底盖不是预测平面或Ring平面；真实部署的组织切面是否严格等于该底盖仍无独立证明。GT全部原网格顶点与可见P0源点具有不同采样权重/覆盖。报告同数学定义的标量差，不称完整自主/临床精度。未计算或使用GT对齐；自主表面距离 **4/4 NOT_EVALUABLE**，作者文件均无对应部署Ring。无需以其他组替换这四个可靠形状配对。

{gthead}

G01_005仅4/9有效，高度偏低3.2491–3.4031mm（约20.5–21.4%）；G01_0049/9基底失败。G06误差−0.1214至−0.0116mm；G08 −0.3396至−0.1385mm。不能只展示后两组隐藏G01/G07。G07虽GT基底可定义，预测相机不合格仍NaN。

{dtab}

**Dxy数学比较72/81，正式成功0/81、0/4组。** G06候选约12.623mm而GT14.000mm（约−9.84%）；G08约21.35mm而GT22.000mm（约−2.95%）。G08接近不解除一端点无独立支持的失败；G06两端点均不通过。G01还受基底/面支持影响，G07无支持面候选。完整原始验收状态与后验定义审计状态均保留，未用GT修正端点。

独立组汇总事先固定：上一轮main、ROI5–30、core；G01固定场景序列首个004，**不因GT把005替补成病例成功**。

{stats}

这组摘要的有效高度只有2/4，不能外推四组可靠性。全部10/27有效条件和72/81候选的描述统计另列[gt_summary](metrics/gt_summary.json)，不能当作独立病例样本。共同有高度及候选的组为G06/G08；不对不同物理指标强行做算法优劣配对。[全部27高度条件](reports/GT_HEIGHT_EVALUATION.md)和[81 Dxy条件](reports/GT_DXY_EVALUATION.md)包含失败/NaN。

![GT评价与完整分母](figures/GT_metric_summary.png)

## B｜四组来源和五来源G01可观测性

共审计21个原始来源（8视频、13照片）、62个已有相机帧、9个冻结P0。只有G01有两视频各三独立参考面，其他三个任务场景各一份P0；额外原视频/照片缺现成可追溯相机/深度/P0，未重新推理。13张照片已实际读取并检查原图；Ring、息肉、背景可见不代表有三维位姿。G08还存在第四张静态jpg，已纳入清单，不冒充P0。

G01五来源：video004/video005各有独立Ring局部系；photo001/002/003有真实RGB、Mask和历史多算法匹配，但光学模式未知，K490只是候选；正式位姿均UNREGISTERED，无现成可靠照片深度/表面。旧V13三照片候选数10/8/10，验证通过均0；本轮没有重估相机。

{vtab}

004法向倾角44.0–48.3°、00524.2–28.2°，局部候选值明显不同，真实图亦有不同环/主体投影；这支持观察方向有差异。两段视频没有可靠统一yaw/平移；不报告可靠跨视频3D基线，不能将两条局部轨迹叠加为真实世界轨迹。480对表中条件内参考数值和未注册来源空值严格分开。跨视频候选条件数值单列candidate栏。

![五来源轨迹方向与关系图](figures/G01_camera_view_coverage.png)

图中相机位置/视锥只来自实际冻结矩阵；照片不画虚构相机。REGISTERED仅适用于同视频名义局部候选系，不代表独立相机GT；图中没有REGISTERED跨来源边。三张照片虽可用历史位姿作诊断投影，仍未进入正式共同坐标。

## 来源表面支持与融合受限原因

原始模型面积、条件重复面、冲突、未知、候选新增均复用上一轮来源索引，在同视频局部系统计；跨视频/照片不计算可靠重叠面积。004/005条件候选新增分别0.73701/0.83996mm²，独立认证真实新增均 **NOT_EVALUABLE**；G06/07/08只有单输入，无互补面可用于融合。面积是有来源的模型面暴露，不是新增解剖组织面积或点数。

004冲突207.5514、未知104.8827、重复46.1037mm²；005冲突110.0452、未知82.6861、重复78.5382mm²（原始多参考面暴露和，重复不是独立认证组织）。照片没有深度且未注册，所有photo-only三维面积为NaN，不是0。

![全部五局部场景支持与冲突](figures/G01_source_surface_support.png)

12个有向同视频深度比较揭示：00403→08中位|Δz|0.7666mm，共同目标深度21736源点中仅986在0.3mm内；反向08→03为0.8380mm、535/13277。00557→459为0.8032mm、4773/17558；459→745为0.2648mm、6459/12164。全部源点/目标有效深度分母见[冲突表](metrics/within_video_depth_conflicts.csv)。这是相机条件下的**模型深度不一致**，含可见性、HERO和相机误差，不能直接判定哪片是真或把全部残差归给HERO。

融合规则也有可量化限制：上轮仅混合父面细分直接回收0040.13938/0050.00691mm²候选，条件支持变更也影响其余增益。因此“融合规则完全没有影响”和“只要放宽融合阈值就能完整重建”均证据不足。当前主要瓶颈：**跨来源注册未认证 + 同视频深度不一致 + 真实支持未知**；观测不足在单参考组明确，但不能单独解释G01全部低增益。

## C｜标准A→B五面板

共110条配对/缺失记录：22个实际渲染（14同视频、2跨视频候选、6视频→照片候选），88条缺乏必要几何/姿态未执行。原16视频配对在本轮图像误差计算前冻结；照片补充在16视频结果之后、任何照片误差之前冻结全部6个既有LightGlue/f490候选，两个视频scope×三张照片全纳入，无误差择优。反向照片→视频因无照片P0不能执行，不用视频面冒充照片几何。

Panel1 A真实帧；Panel2同A相机的实际P0 XYZ与A源RGB/毫米比例；Panel3 B真实帧；Panel4原始A开放三角面射线投影、A顶点RGB重心插值，无纹理平面/新三角面；Panel5 50%叠加、共同/未覆盖/外逸支持、共同有效差异、实际XYZ毫米侧视。B RGB/Mask只在预测写盘后读取用于比较，预测接口无B图像/Mask/深度参数。原面z-buffer和黑色已知CAD深度处理遮挡，不知道的B组织遮挡不假称已解决。

灰区UNSUPPORTED_BY_A不计误差但单报目标覆盖；外逸预测不抹去，单报完整分母；颜色误差不直接等于深度误差。三角面投影与点标记覆盖不同，不拿其覆盖差当几何改善。同帧A→A只在小测试核验，绝不当独立精度证据。004 raw编号历史不一致/不能唯一绑定，所有图按固定缓存key+RGB SHA追溯，raw仅线索。

{repotab}

“较好/有限/困难”以预先已有的NORMAL G06、G01有角差P2配对、UNQUALIFIED G07条件选择代表，不是本轮误差最低的择优结果，更不是三维成功率。所有22图在[本地图库]({gallery}/index.html)。跨视频反向覆盖63.6%，照片候选覆盖54.6–89.8%；较好颜色对齐也不能认证未观测背面、轴向深度或部署相机。

![三种条件的标准五面板](figures/A_to_B_core_review.png)

## D｜失败分类、已知与假设

{table(['失败类型','判断','证据','限制'],failure_rows)}

详细验收定义：[FUSION_ACCEPTANCE_DEFINITION](reports/FUSION_ACCEPTANCE_DEFINITION.md)。工程执行成功包括资产冻结、独立GT导出、22真实重投影、来源/分母审计；科学支持的新事实是形状标量偏差、条件轨迹差异和参考间深度差。**没有宣称新的融合、清理或测量改善**；视觉接近仅一致性证据。真实组织基底/部署坐标/互补真实面积仍待认证。

## E｜顶层研究设计者交接与下一轮边界

[TOP_LEVEL_RESEARCH_HANDOFF](research/TOP_LEVEL_RESEARCH_HANDOFF.md)给出当前主线、真实结果、全部来源、GT身份和待解问题；要求RA独立查原论文/arXiv/开放全文/官方代码，逐方法核查数据、坐标、尺度、成功/失败前提。Codex没有以一次关键词搜索替代文献评审。

仅建议交PM/RA评审两项：①独立认证既有跨源相机及照片光学模式/内参，解决圆环旋转对称和背景退化的证据缺口；②以可靠相机为前提，评审成熟多视图深度一致性/联合约束，解释现有错层再讨论融合。均未自动执行，不预先采纳重大新路线。

应停止：C/M/A或绝对密度无界阈值搜索；靠Ring+近似平面背景反复ICP择优；GT/Oracle修正式预测；以平滑、点数或同帧重投影充当精度；为“成功”放松Feret端点/基底条件。没有证据表明仅改网格焊接就能解决当前错层。

## 固定科研审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；5已有局部场景；9P0，不把G01两视频当两病例 |
| 本算法独立成功 | 本轮不产新预测；旧H95数值10/27条件、3/4组至少一条件；固定病例条件2/4；正式3D Dxy0/81、0/4 |
| 本算法失败 | H95 17/27条件NaN；固定病例2/4 NaN；正式Dxy81/81 NaN；表面误差4/4不可评价 |
| 历史测量值回退 | 0；不读取S0/历史V2/旧照片直径补值 |
| 失败组及具体原因 | G01_004基底9/9；G01_0055/9基底，剩余高度低；G06端点支持；G07相机；G08端点且LIMITED。逐行CSV/本地图库保留 |
| 最终统计样本 | 固定病例高度G06/G08=2/4；数学Dxy G01/G06/G08=3/4；正式Dxy0/4。ROI不作独立病例 |
| 是否使用GT选择算法 | 否；298文件预测快照早于首次GT读取；原参数/正式状态不变；旧GT暴露已披露 |

## 最终十问

1. **H95差异？** G01有效005比形状GT低3.25–3.40mm；G06低0.012–0.121mm；G08低0.139–0.340mm。004基底和G07相机失败。10/27而非27/27可评价。
2. **Dxy差异与有效性？** 全数学候选G01比GT低0.430–1.789mm；G06低1.376–1.377mm；G08低0.642–0.650mm；G07无候选。正式81/81失败不因GT接近解除。
3. **两视频方向真不同？** 冻结局部倾角范围分离，图像投影也不同；准确跨视频相对旋转/基线仍未认证。
4. **照片能接入？** 当前不能正式接入；已有候选投影全部CANDIDATE，K模式/独立验证/深度缺失。
5. **五来源各支持什么？** 各视频内部三参考分别提供条件主面、重复、冲突和小量候选新增；照片仅图像对应，无可认证三维新增。分来源表不合并未知坐标。
6. **为何融合新增少？** 未认证注册、参考深度错层、重复/未知支持占比大与保守规则共同限制，不只是点少或焊接问题。
7. **主要瓶颈？** 当前注册与深度/相机联合几何优先，支持不确定；单参考组另有观测资产不足。
8. **事实和假设？** 文件/数值/渲染与失败分母为事实；真实新面、误差具体来源、真实组织基底和部署姿态仍假设/未认证。
9. **下一轮1–2方向？** 先相机/照片模式独立认证，再由RA审查多视图深度一致性成熟方案；不自动执行。
10. **停止什么？** 无界阈值/ICP、GT反调、漂亮网格与同帧误差充精度、失败样本回填。

验证和发布清单见`metrics/VALIDATION.json`及`provenance/FINAL_SOURCE_MANIFEST.json`。完整GT/视频/XYZ/缓存均LOCAL_ONLY，GitHub仅源码/表/协议/报告和四精选PNG。本轮结束后停止，等待人工验收。
'''
    main=main.replace('GT模式为 **SHAPE_SCALAR_CONDITIONAL**：','GT配对授权证据另保留旧人工任务原文的明确确认及SHA（见`provenance/GT_PAIRING_EVIDENCE.json`）；它是历史身份依据，不是本轮新算法指令，不能放宽当前GT隔离边界。\n\nGT模式为 **SHAPE_SCALAR_CONDITIONAL**：')
    main=main.replace('反向照片→视频因无照片P0不能执行，不用视频面冒充照片几何。','反向照片→视频因无照片P0不能执行，不用视频面冒充照片几何。照片目标曾参与旧候选位姿拟合，其本轮RGB图仅为fit-target诊断，绝非新的独立留出位姿认证；旧独立检查另列`metrics/photo_pose_candidates.csv`和`metrics/cached_correspondence_evidence.csv`，不能用当前图像接近推翻旧失败状态。')
    write('TECHNICAL_REPORT.md',main)
    write('REPRODUCE.md',f'''# 复现与只读核验

环境：既有 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（Python3.12），Open3D0.19从旧surface_fusion_v3/vendor只读导入；无安装/模型推理。项目固定renderer未改。源码/输入/冻结规则SHA见provenance。

验证已交付结果（不重跑预测）：

```bash
cd {REPO}
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/{TASK}/code/validate.py
```

本轮实际分步执行：freeze.py → 独立Blender export_gt.py → gt_evaluate.py（表已保存后控制台序列化异常，后修打印，无再次计算）→ inventory.py →7项小测试→首阶段commit/push→reprojection.py（16）→photo_candidates.py（在照片误差前冻结6继承候选）→reprojection.py --photo-supplement→visualize.py→supplemental_sources.py→finish_evidence.py→write_reports.py→validate.py。

需要重放时必须复制本任务源码到新空实验目录，再依此顺序运行；所有 `R` 从脚本位置派生，旧输入绝对路径只读。freeze.py和GT协议拒绝覆盖既有冻结清单。不要在本次已冻结目录直接重放，也不要运行旧完整重建入口。无需更改清理、上游或正式Dxy。全部22配对在各自误差前冻结，独立复现应保留原来的首次16/后续6两个计划。

GT独立导出命令（仅在新任务目录中运行）：

```bash
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --disable-autoexec -t 2 --python experiments/{TASK}/code/export_gt.py
```

本轮没有声称进行了第二次完整重放。完整HTML/NPZ/GT/原图路径依赖本机冻结资产；public仓库不含原始科研数据。
''')
    print('REPORTS_AND_GALLERY_COMPLETE',len(reproj),'plots,',len(h),'height',len(d),'Dxy')
if __name__=='__main__':main()
