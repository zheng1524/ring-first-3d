"""Assemble the report from actual fixed-denominator outputs; no model calls."""
from common import *
def percent(x):return f'{100*x:.2f}%'
def f(x,n=3):return 'NOT_EVALUABLE'if x is None else f'{x:.{n}f}'
def main():
    p=protocol();summary=load(R/'metrics/PREFIX_SUMMARY.json');runs=[load(x)for x in sorted((R/'metrics').glob('*_RUN.json'))];assert len(runs)==26
    gate=load(R/'config/CAMERA_GATE_RESULTS.json');by={x['source']:x for x in gate['sources']};cleanups={scene:load(R/f'metrics/{scene}_CLEANUP_SUMMARY.json')for scene in p['orders']};official=load(R/'metrics/FINAL_INVARIANTS.json');old=load(R/'metrics/HISTORICAL_OPEN3D_COMPARISON.json');orders=load(R/'metrics/ORDER_COMPARISON.json');layer=rows(R/'metrics/MULTILAYER_RAY_DIAGNOSTICS.csv');caps=rows(R/'metrics/FIRST_HIT_BOUNDARY_ATTRIBUTION.csv')
    get=lambda scene,order,j:load(R/f'metrics/{scene}_{order}_F{j}_METRICS.json')
    md='''# TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001 — TECHNICAL REPORT

2026-11-03，REPORTED，等待研究者审阅，非科学基线认证。

已根据G01_004实际脚本首次建立关键技术版本v1.0，统一核查27份现有来源的相机规则，冻结G01八源及G06五源，完整执行26个正序/逆序预训练前缀。每次均实际运行官方Extractor、FusionNet、Integrator、Translator和浮点Marching Cubes，权重未变，未训练。多视角提高总体覆盖，但没有稳定解决表面真实性：G01固定首次深度一致率15.13%→30.69%，首源ref08却73.52%→0.47%，四次以上交点显著增加；G06提高至61.39%，仍有台阶、封闭与弱参考退化。清理还新增局部孔洞，不能声称没有表面损失。第二组只有五份现存HERO，不冒称八视角。原始Mesh、状态、失败及四张真实证据图全部保留；20–30视角仅准备方案，当前不扩大运行。

## 1. 版本、来源和授权边界

首次总技术文档：[关键技术版本v1.0](../../docs/KEY_TECHNICAL_VERSION_v1.0.md)。研究者明确说明不存在旧总文档，并授权调研当前004脚本后建立。72份历史脚本完整路径及SHA见[脚本审计](provenance/SCRIPT_VERSION_AUDIT.json)，各E3-A/B/C/D、Camera Gate、A2/A3/V5/V6和上轮F0报告的阅读回执见[来源版本](provenance/READING_AND_VERSION_RECEIPTS.json)。相机/清理/裁剪/域规则全部在首次新推理前冻结，首个代码提交为`b9711c8`；后续只修改评价、可视化和可复现交付，见[变更记录](TECHNICAL_CHANGELOG.md)。

官方版本`4f0c14f67ad9d2368b68cbeb78c237a6328971e5`，ShapeNet noise005，checkpoint SHA256 `3ac6dc9f219449e8aa5a26dec0a77691714e55d4e29da688c79630bf46068bff`；严格加载1,403,920参数，eval/inference_mode，逐次参数bitwise未变。官方来源：[weders/NeuralFusion](https://github.com/weders/NeuralFusion)。本轮禁止/实际次数：训练=0、optimizer.step=0、HERO新推理=0、相机优化=0、GT/Oracle读取=0、新TSDF=0、Dxy修改=0、20–30视角推理=0。所有旧工作树、原生Mask/HERO/K/c2w/CAD未覆盖。

## 2. 当前Camera Gate及源选择

同一v0.1候选规范的真实CAD双向轮廓、RGB-only独立F、固定空间留出、Sampson、视差/正深度及无先验Jacobian用于全部27份现有来源。优先已有真实RGB匹配，缺少时仅CPU SIFT，无新神经匹配器。数值阈值继承，没有为了入组调整。完整原始结果见[当前Camera Gate](config/CAMERA_GATE_RESULTS.json)。未进行任何位姿修正。

严格资格与研究入组分开：INSUFFICIENT_EVIDENCE仍不合格认证；身份/公制变换可靠、Ring无明确矛盾且无充分RGB反证者按本轮允许制度条件性入组。G01 growth_r01的Ring p95=12.4px超过12px明确矛盾线，未入组。G01新r00的Ring p95=6.708px不满足6px通过线，但未达明确矛盾线；作为高风险条件输入保留，且不投负向清理票。没有把历史资格改成真实GT。

G01从全部11份原生来源按固定CORE种子及“未覆盖block优先、最远姿态”选8份；不是旧六源追加两个。覆盖B1–B5。G06–G08按输入资格比例、Ring通过比例/误差、分区及深度存在性预先确定评分；G06胜出，无网络结果参与选择。G06只有5份HERO，覆盖3分区，最多执行F0–F4；不存在八视角迁移成功的结论。

|场景/阶段|来源|分区|当前资格|Ring p95 px|
|---|---|---|---|---:|
'''
    for scene,ii in p['orders'].items():
        for j,cid in enumerate(ii):md+=f"|{scene} F{j}|{cid}|{block(cid)}|{by[cid]['qualification']}|{f(by[cid]['Ring_p95_px'])}|\n"
    md+='''
名单、顺序及理由：[VIEW_SELECTION_8.md](VIEW_SELECTION_8.md)、[输出前冻结](config/VIEW_SELECTION_FROZEN.json)。所有逆序均为空latent/count独立初始化，使用严格反转名单；无择优冒充主实验。

## 3. 原生输入、固定清理及表面损失

复用已认可六源V6的删除ID及原始HERO，另两G01来源与G06从真实原生深度开始；选定来源按相同A2候选/实际射线/Mask/CAD逻辑再执行一轮固定审查。每源最多512候选，未审查保留。支持/合法遮挡/未知保留，两个不同分区无支持或层竞争的轮廓反证屏蔽A；B竞争候选按最新已授权全B Mask语义派生屏蔽，Ring或映射身份不确定不删。原V6定向XYZ删除只保留其历史ID，不向新组外推，也没有在新源搜索类似空间阈值。A2 C/D的本轮判定保持保留，逐点证据全部保存。

|场景|原生合法Polyp|既有V6历史屏蔽|本轮A2/全B新增屏蔽|保留|新增闭合孔洞像素（净）|
|---|---:|---:|---:|---:|---:|
'''
    for scene,c in cleanups.items():
        ss=c['sources'];md+=f"|{scene}|{sum(r['raw_N']for r in ss)}|{sum(r['previous_removed_N']for r in ss)}|{sum(r['incremental_removed_N']for r in ss)}|{sum(r['cleaned_N']for r in ss)}|{sum(r['additional_closed_hole_pixels']for r in ss)}|\n"
    md+='\n|来源|新增屏蔽|新增闭合孔洞像素（净）|主体最大组件：前→后|\n|---|---:|---:|---:|\n'
    for c in cleanups.values():
        for s in c['sources']:md+=f"|{s['source']}|{s['incremental_removed_N']}|{s['additional_closed_hole_pixels']}|{s['before']['largest_component_N']}→{s['after']['largest_component_N']}|\n"
    md+='''
**清理存在真实覆盖风险，不能写为无损。** G01 r14新增436屏蔽，其中362位于最大原Mask组件，并形成362闭合孔洞像素；原V3/V6继承的r14头部507像素缺口也未修复。G01 r06/r10新增孔洞92/15像素，G06 r06新增4。这里“最大Mask组件”只是头部代理，其他组件只是侧面/细柄候选，不能自动认证解剖身份。全局展示未通过补洞隐藏损失；详见[头部/细柄/侧面代理](metrics/HEAD_STALK_SIDE_INPUT_PROXIES.csv)。旧3px薄结构硬门槛完全未执行。

所有屏蔽可逆：frozen_inputs/native含original_native_id、historical_excluded、incremental_excluded；原始XYZ由原生深度/原ID/冻结K/c2w精确恢复。决策CSV含来源、原ID、原XYZ、分类、原因及逐观察者证据。没有未知深度填充。

## 4. 裁剪、公制域及尺度核查

逐视角原生Polyp+可见Ring bbox，max(16px,20%最大跨度)余量，最小4:3虚拟矩形，等比例320×240，直接复用Gate A make_crop。A的半像素偏移为`a*(0.5-x0)-0.5`，`K_crop=A K_native`。nearest原生ID采样深度，invalid=0，RGB/Mask同步。相机旋转未改，c2w为相机到Ring世界坐标，深度为轴向Z毫米。

归一：`X_model=(X_mm-O)/L`、`Z_model=Z_mm/L`、`C_model=(C_mm-O)/L`，128³/17维latent。域使用本组全部保留原生XYZ+实际CAD顶点，加max(2mm,10%跨度)余量，边长上取0.001mm；不存在出域点剔除。两个组各自冻结，不要求同一边长；组内前缀/逆序保持完全相同域。

|场景|O mm|L mm|voxel mm|实际CAD外径逆映射 mm|外径/体素|
|---|---|---:|---:|---:|---:|
'''
    for scene,d in p['domains'].items():md+=f"|{scene}|{[round(x,6)for x in d['O_mm']]}|{d['L_mm']}|{d['voxel_mm']}|{f(d['ring_outer_diameter_inverse_mm'],6)}|{f(d['ring_outer_diameter_voxels'])}|\n"
    md+='''
R10文件名没有被解释为半径10mm；这两组实际外径均12.4mm。CPU代数逆映射<1e−5mm，实际GPU官方unproject误差<1e−4mm。nearest离散采样的原生像素中心与crop连续射线有有限量化位移，最大0.06378mm（不是相机校准残差），另列[采样误差](metrics/CROP_NEAREST_PIXEL_QUANTIZATION.csv)，没有用插值假深度消除它。

本轮G01域20.106mm不同于上轮F0的27.959mm，因此**不能把新旧F0差别单独归因于新增视角或清理收益**。本轮阶段间域/权重/采样保持固定，才能研究新增视角效应。

## 5. 官方完整链与Mesh真实性

26次实际链：输入深度/Mask/K/c2w → official unproject → FusionExtractor → FusionNet → FusionIntegrator更新共享latent → official get_translation调用Translator（每前缀全部known点同批）→真实SDF/occupancy → iso0浮点MC → `vertex_index/128*L+O`毫米Mesh。无占据体素立方体替代，无latent阈值伪Mesh，无直接点云充当预测。

128³官方路径只查询非零latent位置。未查询位置在原始field容器为0，不冒充网络预测或观测自由空间；供官方式MC的副本才使用+0.04哨兵。该处理可产生闭合壳/未知边界，面片全部保留并单列标记。SDF头参与官方训练损失；没有误把occupancy当SDF。Translator count归一保持官方完整批，未随意分块改变数学结果。

所有26个field已在CPU重放MC，浮点索引顶点和三角面与保存值完全一致。raw/flat/smooth-normal三份PLY的顶点/面逐项一致；GLB使用米，PLY使用毫米，回转误差<1e−5mm。法线插值只改变显示，没有平滑几何、缩面、补洞或删除网络推断区域。[完整审计](NEURALFUSION_OFFICIAL_PIPELINE_AUDIT.md)、[逐Mesh核查](metrics/MESH_EXTRACTION_AND_SHADING_AUDIT.csv)。

## 6. 固定分母的完整结果

分母为所有所选来源**清理前原生合法Polyp**：G01 136203，CAD遮挡4405，固定可见131798；G06 46856，CAD遮挡692，固定可见46164。所有阶段、顺序均一致。清理移除仍计入原分母，availability另列。hit不是正确，一致阈值0.25mm只是HERO/相机条件下代理；Raw面保留按原始全部面及原面积计，不删除困难面。该面积指标是逐来源加权，含共视重叠，不等于真实表面积或去重后的并集。八参考HERO共享部分上游RGB，E3-A来源DAG身份保留；八源和不同分区不等于八份独立统计证据，本轮未将共视留出称为盲测。

|场景|方向|阶段|视角数|命中率|首次深度一致≤0.25mm|Raw面积保留≤0.25mm|Mesh面积 mm²|连通组件|
|---|---|---|---:|---:|---:|---:|---:|---:|
'''
    for s in summary:md+=f"|{s['scene']}|{s['order']}|{s['stage']}|{s['view_N']}|{percent(s['hit_fraction'])}|{percent(s['agree_fraction'])}|{percent(s['Raw_area_retention'])}|{f(s['mesh_area_mm2'],2)}|{s['components_N']}|\n"
    md+='''
每源MAE/中位/p95/最大值在各*_RAYS.csv及*_METRICS.json中。hit-only误差与包含MISS的p95分开，MISS>5%时完整p95=∞（JSON值null加INFINITE_DUE_TO_MISSES状态，不当作0），不会只报命中均值。未做物理直径测量，物理GT的中位绝对相对误差/MAE/p95/max均NOT_EVALUABLE（NaN）。

|来源|F0首次一致率|正序最终一致率|最终hit-only MAE/p95/max mm|含MISS p95状态|
|---|---:|---:|---|---|
'''
    for scene,ii in p['orders'].items():
        a=get(scene,'forward',0);b=get(scene,'forward',len(ii)-1)
        for x,y in zip(a['rays'],b['rays']):
            st=y['hit_only_error_mm'];md+=f"|{x['source']}|{percent(x['agree_fraction'])}|{percent(y['agree_fraction'])}|{f(st['MAE'])}/{f(st['p95'])}/{f(st['maximum'])}|{y['p95_with_misses_status']}|\n"
    md+='''
总体覆盖增加有意义，但G01 ref08及r06的真实射线首层几乎全部偏移，不能被汇总改善掩盖。G01 F3、F5、F7的部分Raw保留/一致性也非单调；G06最后加入r00后总体一致率从F3 63.68%降至61.39%，仍完整执行，未用质量门槛停机。

### 光滑、完整、真实分开判断

光滑：G01邻接面法线角中位7.13°→11.80°，p95 72.11°→79.64°；近坐标轴法线比例14.92%→10.96%。指标方向不一致，真实图仍有块状/粗糙。G06法线角约1°而坐标轴法线比例约53%，浅表面仅跨少数Z体素，出现台阶环带；不能将平面/平滑显示当精度改善。

完整：两组固定射线命中和Raw面积保留均高于F0，但G01组件113→273、最大组件面积比例49.83%→48.20%，G06组件3→11、79.85%→74.49%。没有形成一个已验证的统一解剖表面，细柄/侧面连通仍未认证；清理孔洞没有因Mesh封闭而被解释为恢复真实组织。

真实：没有GT，首次表面与HERO是有条件几何解释。G01 ref08最终bad首交点13065中，12895落在MC单元8角均known区域，只有170为unknown边界代理；因此不能把全部深度退化归咎于unknown哨兵或渲染。G06对应1173个bad中1114也在all-known单元。都是代理归因，不是物理真值。

|场景/阶段|≥4次交点射线/固定可见分母|unknown边界面比例|可见但缺直接支持面比例|无观测/遮挡未知面|
|---|---:|---:|---:|---:|
'''
    for scene,ii in p['orders'].items():
        for j in [0,len(ii)-1]:
            tag=f'{scene}_forward_F{j}';a=[x for x in layer if x['tag']==tag];d=get(scene,'forward',j);N=d['topology']['faces_N'];md+=f"|{scene} F{j}|{percent(sum(int(x['rays_4plus_surfaces_N'])for x in a)/sum(int(x['fixed_visible_N'])for x in a))}|{percent(d['unknown_boundary_face_N']/N)}|{percent(d['surface_categories'].get('INFERRED_UNSUPPORTED_PROXY',{}).get('N',0)/N)}|{d['surface_categories'].get('UNKNOWN_OCCLUDED_OR_UNSEEN',{}).get('N',0)}|\n"
    md+='''
正常闭合壳本身有前后两次交点，所以“两次”不能自动视为重复层。G01四次以上交点6.44%→66.43%才是明显多壳/多层代理；G06约1.70%→1.73%，仍不能证明真实表面正确。

支持类别要求：面心距真实清理点<=0.25mm，且至少一真实相机投影有合法Polyp深度、轴向差<=0.25mm、CAD未遮挡。可见但无直接支持记INFERRED_UNSUPPORTED_PROXY，未见/遮挡/不足记UNKNOWN。所有标签未校准，不删面。任一来源的背景Mask反证/前方自由空间代理同时保留，跨来源可能冲突。邻近支持不等于该面是某视角的第一可见层，这正是ref08表面看似“被其他源支持”却首交点严重提前的原因。

新侧面不能只看面积：[新增观测代理](metrics/NEW_VIEW_GEOMETRY_PROXY.csv)中，G01 r06有6772个相对前源新颖且CAD可见点，当前Mesh近邻保留5975，却只有20个满足该源首次深度一致，说明邻近几何存在与真实可见首层解释是不同问题。G06后续点多为重复观测，新增侧面证据有限。

跨源输入本身也有差异：投影到ref08的r13/r03/r14/r00/r10/r04清理点轴向中位差约−0.544/−0.766/−1.573/−1.150/−1.119/−0.708mm；G06对应大多在0.03–0.29mm量级。这些受相机、HERO和离散化共同影响，不据此认证哪一源错误。官方局部±3体素更新、不显式施加本项目自由空间一致性，与远层残留机制相容；没有通过新增算法强迫它们成为单层。

### 严格逆序

'''
    for o in orders:md+=f"- {o['scene']}：正序→逆序全部面心距离MAE={f(o['forward_to_reverse_face_distance_mm']['MAE'],5)}mm，p95={f(o['forward_to_reverse_face_distance_mm']['p95'],5)}mm，max={f(o['forward_to_reverse_face_distance_mm']['maximum'],5)}mm；反向p95={f(o['reverse_to_forward_face_distance_mm']['p95'],5)}mm。\n"
    md+='''
最终总体一致率G01正序30.69%/逆序30.58%，G06 61.39%/61.24%；不是完全顺序不敏感，局部差异仍在。两条均原样保存，无择优输出。

### 历史Open3D对照

'''+f"G01历史D0 G1（旧六源、原生未清理、0.1mm）在本轮同一8源固定分母上命中率{percent(old['hit_fraction'])}、首次一致率{percent(old['agree_fraction'])}、Raw面积保留{percent(old['Raw_area_retention'])}。NeuralFusion最终首次一致率30.69%，未超过该历史数值。但两者输入/清理/分辨率不同，不能据此做纯融合算法因果排名。G06无已核验同组历史Open3D；返回NOT_AVAILABLE，没有补跑新TSDF或借其他组结果。历史融合只用于图与评价，未参与NeuralFusion预测。\n"
    md+='''
## 7. 四张核心证据图

![输入、分区、裁剪与相机](figures/Fig1_Inputs_Crops_Cameras.png)

![Raw、历史Open3D、全部正序和最终逆序](figures/Fig2_Raw_Open3D_All_Prefixes.png)

Figure 2各组所有列使用固定毫米观察坐标；原始Raw有域外长条，显示窗口按本轮清理域统一，原Raw文件并未裁剪/删除；它们全范围与原ID仍可读取。不要把图中窗口截取误认为清理算法输出。

![真实TSDF、Mesh浮点与局部显示](figures/Fig3_TSDF_Mesh_Shading_Details.png)

![真实RGB、首次交点与闭合/支持代理](figures/Fig4_RealRGB_FirstHits_Caps.png)

Figure 3局部放大中心来自冻结输入XYZ中位数；black CAD为真实几何。Figure 4所有RGB和射线均来自原相机，profile行由原Mask最宽行预定，未临时挑有利像素；蓝线最终首层与黑点原始HERO的偏离是实际几何，非光照变化。

## 8. 固定审计表

|审计项目|本轮必须汇报|
|---|---|
|目标组数|2，G01_004/G06_004；27来源仅做统一输入Gate，不作27个独立物理组|
|本算法独立成功|2/2产生独立非空预测；26/26前缀完成；不等于测量正确或科学验收|
|本算法失败|工程预测失败0/2；两组物理准确性均NOT_EVALUABLE/NaN，G01存在严重首层退化，G06迁移仅5视角|
|历史测量值回退|0；历史Open3D只读评价，没有参与预测|
|失败组及具体原因|两组均保留未认证风险，详见FAILURE_LEDGER.md及四图；未删除失败来源制造成功|
|最终统计样本|两组所有所选原始观测固定分母；总目标2；G06缺8视角单列，不隐瞒缺口|
|是否使用GT选择算法|否；b9711c8及provenance/BEFORE_GPU.json在输出前冻结，GT读取0；物理误差不计算|

独立数值覆盖2/2，已证实物理正确覆盖未知，不能写100%正确率。未来评价GT须独立授权并保持这次预测、参数及选择冻结。

## 9. 结论、交付与停止

**官方程序确实输出了Translator SDF驱动的真实三角Mesh，完整八视角实验已经执行，不能再把旧F0停机当作路线结论。** 新增视角改善固定总体覆盖和部分源解释，但没有稳定保持原可信主面，G01多层首交点冲突显著；G06更连贯但不足八源、存在台阶和弱参考。平滑法线不能解决这些真实几何问题。

本轮不宣布NeuralFusion全面失败，也不宣布已获得可靠测量模型；应由研究者结合全部结果决定是否投入增强输入。目前不能假设单纯增加重复视角就能纠正相互冲突的几何。24份现有RGB/相机候选资源和缺失计算见[增强方案](VIEW_EXPANSION_20_30_PLAN.md)：G01仅16缓存帧，G06仅8，两组不可合并，单组20–30仍需新增真实帧和身份/相机/HERO资格。

真实26组Mesh：meshes/*_raw_mm.ply（mm），对应flat、smooth_normals PLY和SI_m.glb；每阶段配置/调用/状态SHA在metrics/*_RUN.json。全部latent/count、原field/known/MC哨兵、浮点MC身份和逐观测数组保留local_results（LOCAL_ONLY，不复制原视频/大模型）；索引见LOCAL_RESULTS_INDEX.json。完整代码、配置、小表、Mesh和四图提交独立GitHub分支，复现见[REPRODUCE.md](REPRODUCE.md)。

完成本轮后停止，等待研究者/PM审阅。不自动运行20–30视角、新HERO、相机修正或训练。
'''
    (R/'TECHNICAL_REPORT.md').write_text(md)
    # Explicitly update execution status without changing any historical result.
    status=load(R/'TASK_STATUS.json');status.update(status='REPORTED_AWAITING_RESEARCHER_REVIEW',GPU_forward_N=26,optimizer_steps=0,new_HERO_N=0,enhanced_20_30_run=False,completed_forward_prefixes={'G01_004':8,'G06_004':5},completed_reverse_prefixes={'G01_004':8,'G06_004':5},scientific_accuracy='NOT_CERTIFIED');save('TASK_STATUS.json',status)
    files=[]
    for folder in ['local_results','frozen_inputs','meshes','figures']:
        for path in sorted((R/folder).rglob('*')):
            if path.is_file():files.append(dict(kind=folder,**asset(path)))
    save('LOCAL_RESULTS_INDEX.json',dict(files=files,large_states='LOCAL_ONLY; raw predicted meshes and selected evidence figures included in Git',copy_original_models_or_videos=False))
    (R/'NEURALFUSION_OFFICIAL_PIPELINE_AUDIT.md').write_text('''# Official NeuralFusion pipeline audit — actual 26-run evidence

官方仓库：https://github.com/weders/NeuralFusion ，commit `4f0c14f67ad9d2368b68cbeb78c237a6328971e5`，匹配ShapeNet noise005 config/checkpoint；24份历史核验文件中的实际使用模块再次逐SHA核对，见provenance/OFFICIAL_CHECKED_FILES.json。上轮F0也确实运行了Translator；历史未运行F1/F2是旧质量停机规则，不能解释为Translator缺失。

本轮G01正/逆8+8、G06正/逆5+5，共26次。每个metrics/*_RUN.json的actual_official_call_events均严格为`_extractor, _fusion, _integrator, _translator`。通过只读转调原bound forward方法记录真实输入/输出shape（不依赖会被直接.forward绕过的hook）。Translator点数等于对应非零latent known体素数，未替换为占据阈值或点云。全部1,403,920参数strict加载，逐前缀与checkpoint state_dict逐tensor bitwise相等，无optimizer、无梯度、无训练。

get_translation只提取官方training/utils.py中的该函数AST，不导入训练/dataset/GT数据库。128³使用全known同批Translator，未改变count归一范围；17维latent最后通道是官方use_count计数，外部count数组保持0属于官方配置行为，不是漏写状态。正/逆初始latent及count都为0，Integrator reset，序列前缀共享更新状态。

原始sdf_raw/occupancy_raw/known与MC正哨兵副本分别保存。unknown容器0是未查询，不是网络零SDF，也不是可靠自由空间；仅MC副本unknown=+0.04遵循官方mask导出意图。该处可制造封闭壳，保留原样并逐面all8-corners-known标记。全量Mesh没有因未观测/推断/unknown而删面。

Marching Cubes iso0，浮点插值顶点，毫米`vertex_index/128*L+O`；CPU逐一重放26个field，顶点/面与保存MC身份完全一致。raw/flat/smooth-normal PLY全部相同P/F，GLB单位米回转<1e−5mm。平滑仅插值法线，未几何平滑/补洞/缩面。详见metrics/MESH_EXTRACTION_AND_SHADING_AUDIT.csv及FINAL_INVARIANTS.json。

本轮所有网格有0开放边、0非流形边且watertight，不等于完整真实组织；局部窄带及unknown正哨兵倾向形成壳。G01最终约40.34%面邻接unknown，G06约57.02%。G01 ref08绝大多数bad首交点却来自all8-known单元，因此unknown封闭不是唯一机制。保留三类可见监督代理、跨来源冲突、实际多交点及原始Mesh供审阅，没有修改网络输出制造PASS。
''')
    lock=(R/'TECHNICAL_VERSION_LOCK.md').read_text().split('\n\n完成状态：')[0].rstrip();lock+='\n\n完成状态：26个前缀均完成；当前冻结输入/顺序/域见config/EXPERIMENT_FROZEN.json，首次GPU前SHA见provenance/BEFORE_GPU.json（首提交b9711c8）。后续仅评价/显示/复现适配记录在TECHNICAL_CHANGELOG.md，原推理Mesh和权重不变。所有当前代码SHA见provenance/DELIVERY_CODE.json。\n';(R/'TECHNICAL_VERSION_LOCK.md').write_text(lock)
    save('provenance/DELIVERY_CODE.json',dict(files=[asset(path)for path in sorted((R/'code').glob('*.py'))]))
    print('REPORT_ASSEMBLED',len(md),'chars',len(files),'local artifacts')
if __name__=='__main__':main()
