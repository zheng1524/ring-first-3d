"""Render reports from completed fixed-budget evidence; no optimization here."""
from common import *
def f(x,d=3):return 'NaN'if x is None else f'{x:.{d}f}'
def tab(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(str(x)for x in row)+' |\n'for row in rows)+'\n'
AUDIT='''
| 审计项目 | 本轮结果 |
| --- | --- |
| 目标组数 | E4-0资格覆盖6个物理组：G01/G04/G05/G06/G07/G08；A1实际拟合4组；G01_005是G01另一未统一视频空间，不另计物理组 |
| 本算法独立成功 | 独立产生数值主体4/6；仅指输出成功，严格独立资格及真实几何正确成功0/6 |
| 本算法失败 | 输入资格失败2/6：G04、G05，指标NaN；60次正式初值优化数值收敛60/60；另外保留G01_005不可评价记录 |
| 历史测量值回退 | 0；其他路线预测不参与本轮主体生成 |
| 失败组及具体原因 | [逐组失败](06_FAILURE_LEDGER.md)、[资格与路径](03_DATA_QUALIFICATION.csv)、[核心证据](figures/Fig4_Failure_Identifiability.png) |
| 最终统计样本 | 4个独立物理组的条件性/压力描述，完整资格分母6；不把帧、初值或模型当独立息肉；正式真值误差样本0 |
| 是否使用GT选择算法 | 否；真实GT/Oracle读取0；合成真值仅用于S1；[预注册](01_PM_PROTOCOL.md)和[冻结SHA](provenance/PREOPTIMIZATION_FREEZE.json)先于真实优化 |

真实测量 MARE、MAE、p95、最大GT误差均 NOT_EVALUABLE。本任务不输出独立真值直径。下文的D误差是相对HERO内部深度差的残差，不是独立三维精度。
'''
def write(name,s):(R/name).write_text(s)
def main():
    rr=load(R/'metrics/S2_PRIMARY.json');jj=load(R/'metrics/S4_JACOBIANS.json');pp=load(R/'metrics/S4_PERTURBATIONS.json');su=load(R/'metrics/EXPERIMENT_SUMMARY.json');ag=load(R/'metrics/AGGREGATE_FIXED_DENOMINATORS.json');ranges=load(R/'metrics/PARAMETER_EMPIRICAL_RANGES.json');fixed=load(R/'metrics/FIXED_OBSERVATION_B_METRICS.json');v=load(R/'metrics/VALIDATION.json')
    basic=[m for m in rr if m['arm']in ['A1-0','A1-1','A1-2','A1-3']]
    table_main=tab(['实例/身份','消融/参数','B IoU','固定D命中/32','相对D MAE / p95 / max mm','边界 median / p95 / max px','越界/固定头部分母'],[[m['scene']+' '+protocol()['scenes'][m['scene']]['tier'],m['arm']+'/'+str(m['parameter_N']),f(m['B_metrics'][0]['head_IoU']),str(m['B_metrics'][0]['depth_hit_ray_N'])+'/32',' / '.join(f(m['B_metrics'][0]['relative_depth_mm'][k])for k in ['MAE','p95','maximum']),' / '.join(f(m['B_metrics'][0]['boundary_px'][k],2)for k in ['median','p95','maximum']),f(next(x['outside_per_fixed_head']for x in fixed if(x['scene'],x['arm'])==(m['scene'],m['arm'])),4)]for m in basic])
    shape_table=tab(['实例/模型','中心 xyz mm','模型轴全范围 mm','模型峰高候选 mm','拓扑/限制'],[[m['scene']+' '+m['arm'],', '.join(f(x)for x in m['geometry']['center_mm']),', '.join(f(x)for x in m['geometry']['model_axis_full_extents_mm']),f(m['geometry']['peak_above_model_plane_mm']),'单连通；'+('闭合背面为先验推断'if m['family']in ['ellipsoid','star']else'开放上表面，无底面')]for m in rr if m['arm']in ['A1-2','A1-3']])
    jtable=tab(['实例/模型','观测秩@1e-3','条件数','两步长J相对差','判断'],[[x['scene']+' '+x['arm'],str(x['effective_ranks']['0.001'])+'/'+str(x['parameters']),f(x['condition_number'],1),f(x['relative_two_step_J_difference'],4),x['status']]for x in jj])
    text='''# Phase E4-0 / A1 技术报告

本轮实际完成资格审计、三类参数曲面、合成反例、真实四消融、真实B投影及可辨识性分析。**严格 G1 未通过**：当前全部B存在历史依赖，正式Is资格缺失；不能将条件性投影拟合升级为已恢复真实三维主体。A2只完成设计，未执行；B1/B2、GPU、神经训练/推理、新HERO、相机优化均为0。

路线正式调整为 E4-0→A1→人工审查→A2→B1→可选B2，详见[新版路线](PHASE_E4_RESEARCH_ROADMAP.md)。历史融合/MonoSDF结果全部保留；既有4000步MonoSDF不构成充分训练后的科学否定。本轮新主体只来自本轮参数模型，历史模型不参与生成。

## 版本、输入与资格

父提交 `6550275d518020f50ae7a02dd9b8c6907ca6189b`；预优化冻结提交 `7cd3c47`；分支 `exp/TASK-E4-A1-COARSE-BODY-001`。先冻结协议、代码、原生源ID及数据SHA，再运行60个初值；原始科学代码/输入校验全部保持一致。[审计清单](provenance/ASSET_AND_VERSION_AUDIT.json)、[输入SHA](provenance/INPUT_MANIFEST.json)、[完整性复核](provenance/FREEZE_INTEGRITY.json)。

复用最新E3-N0 Camera Gate与View Partition；G01/G06/G08复用既有冻结原生清理缓存，未重跑旧Type-2密度规则或实施额外清理。G07无合格新版清理链，保留Raw压力身份。未把任何旧融合面作为输入。原Mask和HERO、公制相机、CAD及DXY均未改动。

Ip：G01_004三CORE拟合，r14留出；头部使用固定形态学软线索，不把完整含柄Mask当头部真值。G01_005缺本轮最新Gate/清理链，保持独立空间、不可评价。IIa：G06两条件性相机A，r06留出；G08两条件性A、ref04压力留出。Is：主动查G04/G05及G07，未发现完整资格充分的实例；G07的ref04/r02当前单相机确实已条件性合格，但其历史HERO链仍未合格，故仅压力测试。

所有B不参与本轮拟合，但曾涉及上游/筛选/Gate，全部CONDITIONAL。G01 ref13与B光轴仅差1.62°；G07两个A同属B1分区，不能因为参考名不同声称独立基线。[实际分区和角度](metrics/FROZEN_VIEW_PARTITION_AND_ANGLES.csv)。输入矩阵见[03](03_DATA_QUALIFICATION.csv)，元数据列名修正及原冻结副本均保留，未更改任何入组或优化输入。
'''+AUDIT+'''
## 方法及执行

[预注册](01_PM_PROTOCOL.md)与[数学实现](02_MATH_IMPLEMENTATION.md)给出完整公式。9参数椭球、16参数Ip三阶有界星凸、10参数Is开放球冠、11参数IIa有限非负高度场。C为24方向可见投影凸支撑，不等同完整轮廓IoU；D为32条原生射线/16固定对的首次轴向Z差；H为96个原始顶点软支持/视角；R为弱固定先验。A1-3与A1-2输入预算一致。仅G06/G08额外启用+H对照；G01/G07的H-only只作条件性/压力诊断。

每模型3初值、TRF max_nfev60，seed20261104；20模型共60次，全部优化器数值收敛，实际残差调用'''+str(su['actual_residual_evaluations'])+'''次；求解累计'''+f(su['fit_seconds'],2)+'''秒，不含I/O、逐像素射线评价和制图。40个预注册敏感性求解累计'''+f(su['perturb_seconds'],2)+'''秒，全部数值收敛。没有因效果修改预算/权重/参考。完整参数、初值、active bounds与收敛原因见[所有初值](metrics/S2_ALL_STARTS.json)。数值收敛不证明物理正确。

S1四类首交点/坐标合同与3个反例均通过；规则没有据合成分数调整。单视角相对D的归一J秩8/9，三视角9/9；已知干净控制中可近零残差恢复，但单视角局部缺秩仍不能认证唯一真形状。改变隐藏下半面，真实透视相机首次深度完全不变；正交单轮廓对照中厚度不同但二维支撑相同。头柄控制保留99.85%头部、滤去绝大多数柄单独像素。所有合成示例明确标识，未作真实结果替身。[S1结果](metrics/S1_CONTROLS.json)。

## 固定B结果（全部主消融）

以下每个数都来自A目标最小的预定主解，不是B最优初值。每B固定32条D射线、16对；头部和全Polyp分母保存原像素数。D条件MAE必须与未命中同读。

'''+table_main+'''
A1-2相对纯二维：G06 IoU .789→.882，D-MAE 2.400→.277mm；G08 .890→.908，1.764→.413mm；G07压力 .811→.829，1.426→.465mm。G01 IoU .919→.895下降，而D-MAE 1.563→.398mm；固定射线命中31→30，也下降。不能称四组均改善。

A1-3相对A1-2：G06开放高度场IoU .882→.884（仅约0.2%，未达预注册5%IoU改善），D .277→.193mm且命中29→30，局部J更稳定，值得人工复核；G01星凸IoU .895→.880、命中30→29，D .398→.298mm，属于**降低覆盖伴随更低条件误差的潜在失败**；G08轮廓 .908→.912但D .413→.898mm恶化，不能以外观宣布收益；G07球冠 .829→.877，IoU相对改善5.7%，但Is压力身份及参考敏感性阻止正式成功判断。

H额外对照没有统一收益：G06椭球+H IoU .862/D .227，高度场+H .878/.182；G08椭球+H .900/.482，高度场+H .910/.629。G06高度场+H略减D但略损IoU；G08+H改善其高度场D仍显著弱于不加H椭球。单独H的G06模型IoU .494、越界过大，正式数值必要条件也不满足。[配对比较](metrics/PAIRED_COMPARISON.csv)。

四组条件/压力描述的跨组统计如下，分母保持6个资格候选物理组，其中4组有数值；不能当作正式总体准确率，也不能用16/60个模型取代4个息肉。

'''+tab(['消融','IoU median / p95 / max','每组D-MAE median / p95 / max mm'],[[x['arm'],' / '.join(f(x['IoU'][k])for k in ['median','p95','maximum']),' / '.join(f(x['relative_depth_MAE_across_groups_mm'][k])for k in ['median','p95','maximum'])]for x in ag])+'''
完整64+8行消融记录、NaN输入失败及所有初值见[04_ABLATION_METRICS.csv](04_ABLATION_METRICS.csv)。

## 形态与可辨识性

'''+shape_table+'''
表中“峰高”是相对模型自己的局部参考平面，不是实测Background高度。Ip只估计头部；未生成柄。G08高度场峰值约4.18mm、面积/尺度扩张不能解释为可信新增侧面。所有主模型单连通、无退化三角形；星凸/高度图结构排除任意自交，但这不是独立形状真值或外部穷举三角形相交检测。曲率/法向跳变和边界数是描述指标，未临时设门槛制造PASS。[几何诊断](metrics/GEOMETRY_DIAGNOSTICS.json)。

20个归一白化观测J中：14个局部满秩条件结果、5个差分不稳定、1个局部不可辨识（G08纯二维厚度）。**满秩不等于全局唯一、真实相机正确或信息独立。** 观测σ和相关性均是冻结工作代理，没有估计完整真实协方差；R先验不计入J。5个不稳定J均有切触附近射线命中切换，不能把数值尖峰当强约束。详细谱、弱方向、两步长和经验范围见[05](05_IDENTIFIABILITY_REPORT.md)。

相机小扰动只在副本上做敏感性：G06/G08高度场中心分别变化约.554/.530mm；删一个A后G07椭球/球冠约4.729/4.603mm，不能认证稳定主体。不同初值和扰动给的是经验范围，绝非校准置信区间。

## 评价合同与已发现限制

1. 原始报告字段outside_fraction=FP/predicted_N是精确率式动态分母；审计后**保留原字段和门槛，不回写结果**，另外提供FP/固定head_N与FP/230400，以及固定源轮廓点到预测的距离。所有新增固定分母都列入04和[固定B指标](metrics/FIXED_OBSERVATION_B_METRICS.csv)。这属于评价报告补齐，未影响拟合或选择，不能靠新分母制造PASS。
2. D无交点时删失仍有优化漏洞。C支撑域辅助并未完全消除：44个A源/模型记录中11个最终覆盖低于对应初值（见[覆盖账本](metrics/COVERAGE_DEGENERACY.csv)）；G01配对还出现降低B覆盖而条件D误差下降。0.25mm漏对诊断分数不是可靠几何惩罚，不能单独排名。
3. 四类S1内部射线误差≤.003mm只覆盖控制测试；真实主解共2048条源/模型射线，有1条星凸命中分歧。诊断证明这不只是网格粗糙：G01/ref08原生Pixel ID 85489，33点扫描漏掉同一小区间内两个根，4097点有限射线诊断与加密Mesh均确认有交点。因此 **G01 A1-3 的首次交点合同FAIL**，其命中和D指标保留失败身份，不能认证完整根计算。G07球冠另有最大连续/三角面差.215mm，单独将Mesh细分2×/4×后该误差降至.024/.008mm，属于离散化敏感。诊断未替换正式Mesh或重选模型。[逐源审计](metrics/REAL_ROOT_AND_CAD_AUDIT.csv)、[根漏检原因](metrics/ROOT_BRACKETING_FAILURE.json)、[离散化诊断](metrics/MESH_REFINEMENT_DIAGNOSTIC.json)。
4. D拟合前筛选原观测CAD资格，模型根CAD资格在独立评价检查；实际所有A的候选根均在CAD前。B有4条G01模型/射线根在CAD后，均正确计为遮挡/未命中。C可见顶点选择是低维近似，精确像素投影另评。
5. H采用面积CDF取样后再按原顶点面积归一，是确定性面积偏重软支持，**不是无偏连续面积积分**；方向对应距离也不是精确最近点SDF。此限制已披露，未据结果改权重。未来如改积分规则须独立预注册重跑，不能称本轮已解决。
6. 圆滑、闭合和良好B轮廓不能证明真实背面/接触部位；未知面均是低维先验推断，不属于新增观测。

## Gate及建议

G0：来源与版本核查完成，完整科学资格仍不充分；Ip/IIa只有条件性/压力验证，正式Is真实实证NOT_EVALUABLE。G1：NOT_PASSED，严格独立留出合格案例0。数值不退化的条件性候选存在，尤其G06高度场，但不能替代独立资格门槛。

建议先由人工复核G06高度场/真实轮廓与背景源的对应，并解决D漏射删失和真正留出资格；不建议立即作为“G1通过”启动正式A2。若另行授权探索性A2，必须保留条件身份、BASE_UNCERTAIN和独立对照，不能沿用本轮美观模型当真值。A2设计和现有Background清单见[A2预备](A2_PREPARATORY_DESIGN_ONLY.md)。本轮没有执行任何附着、B1或B2。

## 核心人工审阅图

- [Fig1：冻结真实B四消融](figures/Fig1_Frozen_B_Real_Projection.png)
- [Fig2：真实HERO与参数主体，统一mm](figures/Fig2_Metric_Body_HERO_Comparison.png)
- [Fig3：三类型模型，侧面/顶部](figures/Fig3_Class_Families_Side_Top.png)
- [Fig4：失败与可辨识性](figures/Fig4_Failure_Identifiability.png)

实际来源图像与Mask来自各B；B RGB从未给主体重新上色。3D原始XYZ使用自身来源颜色；粗主体固定橙/青色，Ring为黑色真实CAD，未平滑/补面。六视角、分离节点GLB和离线HTML在本地local_results/review，路径/SHA见[完整索引](metrics/VISUALIZATION_INDEX.json)。大输入和本地Mesh不复制上传；所有主体可以从已提交参数精确重建。

来源/冻结/参数导出等完整性核验'''+str(len(v['engineering_checks']))+'''/'''+str(len(v['engineering_checks']))+'''通过；这不包含全部根完备性，真实星凸首交点合同已有1例失败。不能把完整性检查PASS概括为整个数学实现PASS。科学Gate仍失败。[复现](REPRODUCE.md)、[失败记录](06_FAILURE_LEDGER.md)、[RA核对/Gate](07_RA_REVIEW_AND_GATE.md)。完成后停止，等待研究者/PM审核。
'''
    write('TECHNICAL_REPORT.md',text)
    write('05_IDENTIFIABILITY_REPORT.md','''# S4 可辨识性与稳定性

这里分析观测残差向量的J，不是标量总损失梯度；先用固定工作噪声σC=3px、σD/H=.25mm白化，再作来源/面积质量归一和物理参数尺度归一。相关性代理不是完整协方差白化，不把重复RGB来源当完全独立证据。全部R正则先验被剔除。

参数尺度：中心1mm、旋转.1rad、log轴.2、其他形状.1。中心差分h=.001和.0005，差异>.1不认证谱；CAD局部顶点可见集合冻结，但轮廓支撑点/首交点变化仍可非光滑。条件数为smax/smin；null代表无穷，不是0。多初值和五个固定扰动预算均在优化前登记，没有根据B重选。

'''+jtable+'''
14个局部满秩、1个LOCALLY_UNIDENTIFIABLE、5个NUMERICALLY_UNSTABLE_J。G08纯二维厚度列为0、秩8/9；仅投影轮廓不足以约束此厚度。5个不稳定J的归一差约.48–.63，并伴随首交点hit开关。故这些条件数和弱方向只是失败诊断，不作为正式信息强度数值。

完整参数弱方向和谱见[JSON](metrics/S4_JACOBIANS.json)。合成控制单视角相对D秩8/9，多视角9/9；隐藏背面反例说明相对D本身不能恢复任意不可见侧。椭球轴交换、旋转对称和硬界也会造成全局多解，局部满秩不排除这些情况。

'''+tab(['实例/模型','多解数','中心逐轴range mm','轴长逐轴range mm','最大两解中心距离 mm'],[[x['scene']+' '+x['arm'],x['empirical_solutions'],', '.join(f(y)for y in x['center_range_mm']),', '.join(f(y)for y in x['semiaxes_range_mm']),f(x['max_pairwise_center_mm'])]for x in ranges if x['arm']in ['A1-2','A1-3']])+'''
以上是三初值加五固定扰动的经验范围，不是置信区间。删最后一个A视角同时会减少信息并重建该A子集的初始化先验/R0；因此该项是整个拟合流程敏感性，不能解释为只删数据的严格Fisher信息实验。相机副本敏感性也包含同等有限再优化预算；科学相机原文件不变。

G07同一View Partition内两个A、历史HERO链不足，删参考后4.6–4.7mm变化严重；G06/G08高度场对.05mm/.1°相机副本扰动出现约.55/.53mm中心变化，需独立验证。D×.9/1.1经常返回几乎相同解，不能单独据此认证稳定。

固定32射线的丢失统计及两步长切换数见[根与CAD审计](metrics/REAL_ROOT_AND_CAD_AUDIT.json)、[参数范围](metrics/PARAMETER_EMPIRICAL_RANGES.json)；所有扰动解原样保存[JSON](metrics/S4_PERTURBATIONS.json)，不替换A-only主解。G1仍NOT_PASSED。
'''+AUDIT)
    write('06_FAILURE_LEDGER.md','''# E4 A1 失败与限制账本

没有删除失败初值或不利参考，没有改参数搜索范围。数值求解收敛与科学失败分开记录。

| ID | 范围/步骤 | 原因与证据 | 处理/状态 |
| --- | --- | --- | --- |
| F00 | prepare元数据尾部 | 首次13输入生成后PART常量缺失触发NameError | 优化前修正常量，--finalize完成；输入/规则未改变 |
| F01 | 汇总代码 | summarize.py初次解析缺少括号 | 仅汇总代码语法修复；不影响冻结拟合代码、配置或模型 |
| Q01 | 全部B/严格G1 | 上游HERO、Gate或选帧历史依赖；没有真正独立全流程留出 | G1 NOT_PASSED，0严格通过；[资格](03_DATA_QUALIFICATION.csv) |
| Q02 | G01_004 Ip | 当前CORE Gate证据不足；头部是未认证软线索，r14与ref13角度接近 | 条件验证；不称真实头部GT；[Fig1](figures/Fig1_Frozen_B_Real_Projection.png) |
| Q03 | G01_005 | 缺本轮当前Gate/清理链，004/005空间未统一 | 仅审计，四消融NaN，不混合 |
| Q04 | G04/G05 Is | 归档相机UNQUALIFIED_ARCHIVED_CAMERA | 输入资格失败，两组全部消融NaN；[主动搜索](provenance/IS_PATHS_AND_METADATA_CORRECTION.json) |
| Q05 | G07 Is | ref04/r02最新单相机条件通过，但历史HERO链未合格；两个A同分区 | 压力测试，正式Is NOT_EVALUABLE；不放宽门槛 |
| Q06 | G06 IIa | A条件资格有用；B、历史背景源ref04仍证据不足 | 不能认证完整G1或自动启动A2 |
| Q07 | G08 IIa | 历史/最新资格、背景与形态限制 | 压力测试；不得冒充另一合格重复样本 |
| M01 | G06 A1-1 | B IoU .494、投影越界明显 | 数值必要门槛失败；[Fig1](figures/Fig1_Frozen_B_Real_Projection.png) |
| M02 | G01 A1-3 | 相对A1-2，D误差下降但B固定命中30→29、IoU下降 | 潜在覆盖退化，不能宣布模型优势 |
| M03 | G08 A1-3 | 轮廓略好但相对D MAE .413→.898mm；模型峰高约4.18mm | 错误形态/过拟合风险，不能凭平滑获PASS；[Fig3/4](figures/Fig4_Failure_Identifiability.png) |
| M04 | G07 A1-2/3 | 删除一个A后中心变4.729/4.603mm | 实例信息/流程不稳定，压力数值不认证真实主体 |
| N01 | 5个J | G01 A1-3、G06 A1-2、G08 A1-2/+H、G07 A1-2两步长差>.1；伴随hit开关 | NUMERICALLY_UNSTABLE_J；不采用伪精确条件数；[S4](05_IDENTIFIABILITY_REPORT.md) |
| N02 | G08 A1-0 | 厚度观测列为0，局部秩8/9 | LOCALLY_UNIDENTIFIABLE，不用先验填满观测秩 |
| N03 | 全部D删失 | 11个A源/模型记录覆盖低于初值；漏射残差删失可能换取低误差 | 保留固定分母，记录潜在失败；本轮不反复改损失重跑 |
| N04 | 导出Mesh离散化 | 2048条真实模型/源射线：1个hit分歧，最大连续/三角面深度差.215mm | 保留原网格/指标，不能把控制实验.003mm上界推广到真实掠射 |
| N06 | G01 A1-3首交点合同 | ref08原生Pixel ID 85489的两个近根落在同一33点扫描格内，被错误判无交点；加密Mesh仍有hit | 正式根合同FAIL，保留原结果，不认证该模型；[诊断](metrics/ROOT_BRACKETING_FAILURE.json) |
| N05 | H软支持 | 面积CDF样本再按顶点面积归一，非无偏面积积分；方向对应不是真正最近点SDF | 明确近似，未来修改须重新冻结；未换权重制造好结果 |
| R01 | 越界报告 | 原FP/predicted_N不是固定观测分母 | 保留原字段与Gate，补FP/head_N及FP/画幅，不按新分母重判PASS |
| R02 | 资格CSV附加搜索行 | 历史相机状态列误列为current；旧字段别名导致两个路径null | 原CSV冻结副本保留；补最新状态/正确路径，主实验入组不变；[修正记录](provenance/IS_PATHS_AND_METADATA_CORRECTION.json) |
| V01 | XYZ图绘制 | 初稿CAD绘制层级会盖住已可见的前方点 | 审图后仅改显示层级与点大小，真实XYZ/CAD/相机不变；模型和评价不改 |
| G01 | A2/B1/B2 | G1无严格通过实例；本轮只有A2设计授权 | 实际执行0；完成A1后停止 |

负面的科学结果不等于参数化路线已被否定；本轮证明的是有条件收益与仍未解决的证据/数值限制。
'''+AUDIT)
    write('07_RA_REVIEW_AND_GATE.md','''# RA条目核对与 G0/G1

执行依据是人工TASK.md；RA参考任务更宽的A2范围没有自动授权。G0审计完成、完整资格不充分；G1 NOT_PASSED。

| 要求 | 实际完成 | 判断 |
| --- | --- | --- |
| 路线及历史保护 | 新增路线文档，旧实验/相机/HERO/CAD/DXY不写回 | 完成 |
| Ip/Is/IIa模型 | 椭球/星凸、开放球冠、有限非负高度场；合成合同7项 | 工程完成，非三类真实科学成功 |
| 主动寻找Is | E3完整来源表中的G07/G04/G05均核查 | 正式Is NOT_EVALUABLE |
| 公平四消融 | 4物理组×4基础臂，加G06/G08各两+H，共20模型/60初值 | 完成，资格分层 |
| A/B分离 | 只用A拟合/初始化/选择，B优化后评价 | 当前参数留出完成；全流程独立留出不足 |
| 相机Z/公制/CAD | 复用冻结原生映射及相机；控制合同通过，真实掠射复核 | G01星凸1条根漏检FAIL；球冠网格离散敏感单独记录 |
| 固定分母 | 完整原Mask及固定32D射线；补充FP/head_N | 完成报告补齐，原动态越界字段保留，不改Gate |
| 白化J/物理参数/SVD | 全20主模型，剔除先验，两差分步长 | 14条件局部满秩、5数值不稳、1不可辨识 |
| 有限稳定性 | 3初值＋A1-2/3各五扰动，40次；全解保存 | 完成，部分明显不稳定 |
| A2准备 | 未验证参数接口、9份真实背景资产索引、27旧ROI资格、三臂候选 | 只设计，执行0 |
| B1/B2 | 仅未来接口 | 执行0 |

Q1：A1-2是否优于仅二维或HERO？相对纯二维，D拟合普遍更好，IoU并非全部更好；相对H-only没有统一D优势。G01还降低覆盖，不可笼统PASS。

Q2：A1-3是否优于统一椭球？没有统一优势。G06有限高度图有较好D/覆盖且避免虚假下表面，但IoU收益仅.2%；G01星凸更多参数未改善留出，G08轮廓改善伴随深度恶化，G07球冠只有压力证据。

Q3：类别建议？Ip暂优先较简单椭球头，不生成柄；Is保留开放球冠研究接口但无正式实例；IIa有限高度图比闭合椭球更符合开放面表达，G06值得复核，不能推广到G08成功。

Q4/Q5：初始化/相机及可辨识性？均有敏感实例；G08二维厚度不可辨识，5个J因hit变化不稳，G07删参考后中心变约4.7mm。满秩仅局部代理，不能排除隐藏面和全局多解。

Q6：哪些真实案例已经证明方法不退化？部分G01/G06数值模型满足基本拓扑/投影必要条件；**没有一个同时具备充分资格和真正冻结独立留出的严格案例**，故正式证明数0。

Q7：是否进入A2？目前不建议以“G1已通过”启动正式A2。建议人工先看G06高度图及其轮廓/背景资格，并解决留出依赖、D删失。若要条件性探索A2需单独授权和清楚限定，不能自动进入。本轮停止。
'''+AUDIT)
    write('REPRODUCE.md','''# 复现与本地结果

独立分支 `exp/TASK-E4-A1-COARSE-BODY-001`。原始源资产不可公开复制，路径与SHA见provenance/INPUT_MANIFEST.json。只在本任务/新复现工作树写派生结果，不在原始科研资产或其他工作树运行清理命令。

本机环境：Python3虚拟环境 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`，具体版本见provenance/ENVIRONMENT.json；Open3D复用既有vendor，不下载模型。CPU-only，common.py禁止神经运行时、网络、GT/权重及任务外写操作。对另一台机器需显式映射common.py中的原始资产根，并核验相同SHA，不能悄悄替换输入。

```bash
cd /home/liu/ring_first_3d_e4_a1
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK_ROOT=experiments/TASK-E4-A1-COARSE-BODY-001
"$PY" -B "$TASK_ROOT/code/replay_inputs.py"
"$PY" -B "$TASK_ROOT/code/synthetic.py"
"$PY" -B "$TASK_ROOT/code/run.py" fit
"$PY" -B "$TASK_ROOT/code/run.py" jacobian
"$PY" -B "$TASK_ROOT/code/run.py" stability
"$PY" -B "$TASK_ROOT/code/audit.py"
"$PY" -B "$TASK_ROOT/code/visualize.py"
"$PY" -B "$TASK_ROOT/code/summarize.py"
"$PY" -B "$TASK_ROOT/code/validate.py"
"$PY" -B "$TASK_ROOT/code/refinement_diagnostic.py"
"$PY" -B "$TASK_ROOT/code/write_report.py"
"$PY" -B "$TASK_ROOT/code/finalize.py"
```

已有结果时run.py逐模型/初值恢复并跳过完成项。全新复现工作树缺少忽略的输入缓存时，先用 `replay_inputs.py --rebuild`；它只替换prepare.py的首次注册存在性断言，并将协议写入改成内容比较，科学数据准备语句不变、冻结代码SHA先核验，UTC外任何配置差异均拒绝。不要在已有人工结果目录删除模型来强制重跑；需要完全重跑时建独立复现工作树和目录，复制相同预注册与必要来源映射后执行。

本地目录：

- inputs/：13份固定原生射线、Mask、H点身份缓存；不上传。
- local_results/：20份实际参数三角Mesh、B像素首深度/Mask、S1控制几何。
- local_results/review/index.html：离线六视角审阅页，4份分离节点GLB和六视角PNG。
- metrics/S2_ALL_STARTS.json：60初值全部参数/优化状态/固定B指标；S2_PRIMARY为仅A目标选出的20主解。
- metrics/S4_PERTURBATIONS.json：40个原样扰动解；S4_JACOBIANS为白化观测谱。
- metrics/VISUALIZATION_INDEX.json、A2_BODY_INTERFACE_UNVALIDATED.json：本地Mesh/GLB/图路径和SHA。

PLY用导出float32保存，参数JSON为float64；validate.py比对实际参数Mesh与导出顶点/三角形，容差2e-6mm。无平滑、补面、额外删除或B RGB重上色。

失败NaN和原始元数据修正前副本均保留；来源完整性验证PASS不代表根完备性或G1通过。metrics/FINAL_ACCEPTANCE.json为最终门禁，保留S1通过与真实星凸根合同失败的区别。A2_PREPARATORY_DESIGN_ONLY.md只是下轮建议，不提供自动执行入口。
''')
    write('PHASE_E4_RESEARCH_ROADMAP.md',(REPO/'docs/PHASE_E4_RESEARCH_ROADMAP.md').read_text().replace('../experiments/TASK-E4-A1-COARSE-BODY-001/TASK.md','TASK.md'))
    print('REPORTS_WRITTEN',flush=True)
if __name__=='__main__':main()
