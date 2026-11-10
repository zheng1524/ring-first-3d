from common017 import *
import gzip,shutil,subprocess
def mdtable(rows,keys):
    return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(str(r.get(k,''))for k in keys)+' |'for r in rows)+'\n'
def main():
    source=load(R/'config/SOURCE_LOCK.json');ss=load(R/'metrics/FINAL_SOURCE_SUMMARIES.json');groups=load(R/'metrics/GROUP_SUMMARY.json');arch=[x for x in groups if x['representation']=='ARCHIVE_RAW'];native=[x for x in groups if x['representation']=='NATIVE_GRID']
    codebook={0:'joint extreme perspective+tangent stretch (correlated geometric family)',1:'native depth range >0.5 mm',2:'needle or normal incoherence/kink (correlated shape family)',3:'source mapped-native Mask distance <=2 px',4:'at least2 CAD samples signed <-0.02 mm',5:'limited k32 nearest nonadjacent competition proxy',6:'original Mesh boundary vertex incident',7:'small original component area proxy, never deletion alone',8:'native depth/Mask binding not valid',9:'unknown due qualification/grazing/legitimate CAD occlusion',10:'initial rim conjunction rejected',11:'initial CAD conjunction rejected',12:'nonmanifold source vertex incident',13:'face spans independently source-patch-supported native discontinuity',14:'final two-sided gap face rejection'}
    save('REASON_CODEBOOK.json',dict(bits=codebook,state_map={0:'TRUSTED',1:'UNCERTAIN',2:'REJECTED',3:'UNKNOWN'},none='no warning under this finite internal diagnostic, not physical truth',dependencies='geometry indicators are correlated; no independent statistical votes or calibrated probability'))
    for p in sorted((R/'face_decisions').glob('*.csv')):
        with p.open()as f,gzip.open(str(p)+'.gz','wt',newline='')as out:
            rd=csv.DictReader(f);wr=csv.DictWriter(out,list(rd.fieldnames)+['reason_text'],lineterminator='\n');wr.writeheader()
            for row in rd:
                bits=int(row['reason_bits']);row['reason_text']='; '.join(text for bit,text in codebook.items()if bits&(1<<bit))or'NO_INTERNAL_WARNING_NOT_GT';wr.writerow(row)
    # Explicitly distinguish newly indexed native diagnostic triangles from original mesh outputs.
    note='NATIVE_GRID is a diagnostic discretization of unchanged original native depth. Its lattice triangles are newly indexed for source evidence, NOT original archive face IDs and NOT a reconstruction/adapter input. Use final_results/<source>/ARCHIVE_RAW/CLEANED_SUBSET.npz for the exact original-face subset. No filtered archive faces are restored or filled.\n'
    (R/'NATIVE_GRID_DIAGNOSTIC_ONLY.md').write_text(note)
    outindex=[]
    for row in ss:
        root=R/'final_results'/row['source']/row['representation'];a=np.load(root/'FACE_EVIDENCE.npz');outindex.append(dict(group=row['group'],source=row['source'],representation=row['representation'],role='ORIGINAL_MESH_SUBSET'if row['representation']=='ARCHIVE_RAW'else'DIAGNOSTIC_ONLY_NOT_ADAPTER_INPUT',evidence=asset(root/'FACE_EVIDENCE.npz'),subset=asset(root/'CLEANED_SUBSET.npz'),face_CSV=asset(R/'face_decisions'/(row['source']+'_'+row['representation']+'.csv.gz')),original_mesh=next(r['archive_mesh']for r in source if r['source_id']==row['source']),unreferenced_original_vertices=int(len(a['V'])-len(np.unique(a['F']))),raw_point_values_preserved=True))
    save('RESULT_INDEX.json',outindex)
    gtable=mdtable([dict(group=x['group'],sources=x['source_N'],raw_faces=x['original_faces'],trusted=x['TRUSTED_faces'],uncertain=x['UNCERTAIN_faces'],rejected=x['REJECTED_faces'],unknown=x['UNKNOWN_faces'],uncertain_unknown_area=f"{100*x['uncertain_unknown_area_fraction']:.2f}%")for x in arch],['group','sources','raw_faces','trusted','uncertain','rejected','unknown','uncertain_unknown_area'])
    stable='''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个独立物理组；18份video004原生HERO来源（G01=11、G03=1、G05=1、G06=5）；双表示不是36份独立观测 |
| 本算法独立成功 | 18/18来源完成原面标记、可追溯输出、原顶点/原面子集；仅数值/工程成功，不等于错误清理成功 |
| 本算法失败 | 自动清除伪影的科学目标未证明，4/4组均0删面；残余伪影、CAD冲突及无法判断区域全部保留。无来源读取失败；真误删率/召回率为NaN |
| 历史测量值回退 | 0。原始单参考Mesh是授权输入，不是历史融合或S0/V2预测回退；旧清理标签未参与本轮决定 |
| 失败组及具体原因 | G01/G03局部拉伸、PCA自解释及掠视/支持不足；G05/G06仍有边缘和CAD矛盾。逐源见FAILURE_LEDGER与metrics/RULE_BLOCKING_ATTRIBUTION.csv、figures/full |
| 最终统计样本 | 全4/4物理组、18/18来源；所有来源均保留。面积按来源观测求和，不是独立解剖面积；无GT测量，MedARE/MAE/p95/max真误差及共同测量配对N均NOT_EVALUABLE/0 |
| 是否使用GT选择算法 | 否。无GT/Oracle几何访问；初始协议、补充规则及各阶段源码/输出SHA独立冻结；控制实验是标注的解析几何，不是项目GT |
'''
    summary='''# TECHNICAL_REPORT_SUMMARY — 017

**结论：四组18来源的内部几何标记完成；保守清理没有产生有效删除，不通过“可靠自动清理输入已就绪”的验收。** 初始PCA规则和随后一次两侧源像素外推规则均为0删面。保留全部负结果，没有继续放宽阈值或凑删除比例。

## 目标、输入与完成范围

只研究G01/G03/G05/G06各自video004的原生HERO来源；G03和G05各只有一份深度，其他RGB视角不冒充HERO。18份原始深度、Mask、RGB、冻结K/c2w、CAD及单参考原Mesh均核对。无融合、无HERO重推、无优化配准、无主体/SDF训练、无DXY改动。

原始交付基准是已有单参考`ARCHIVE_RAW`的精确原面数组。历史Raw常先将352×640深度双线性升到360×640，并已在建面时作跳变过滤；不能冒充“完全未过滤的352网格”。为诊断该差异查询了原深度的未过滤原生像素格，但它的**新编号三角形仅作诊断，不作为新重建或适配输入**。主图与主表用原始归档面；原生格证据单独存档，绝不补回原Mesh缺面。

## 原定算法与实际代码

Phase-C原函数复用：`common017.py` AST提取`unproject`、`face_components`、`edge_counts`、`density.features`；没有运行旧清理入口。保留透视采样、PCA切平面预期边长、密度归一等机制。E3-B的面积加权相机朝向法向一致性、边界标记与k32最近面竞争被显式适配到逐面诊断。它们原来是局部场符号资格，**不能直接当错误标签**。

`analyze017.py:classify`：强透视和可靠切平面拉伸、原生深度跳变、针状/法向异常，再加源边界或CAD实体矛盾形成联合拒绝；单长边、单密度、单曲率、近Ring均不删除。Unknown保留。初始全36表示运行拒绝0。

诊断发现PCA会拟合到异常片层本身，造成自解释；坏三角面法向还会落入掠视Unknown。保留初始协议和结果后，登记一次`gap017.py`补充：两个不包含被测端点的源像素半侧邻域，拟合逆深度平面，检查两侧各自支持及跨边外推。未搜索阈值；8/4/0.5mm/0.2等沿用，局部拟合误差限固定为0.5/4mm。只拟删除跨层插值面，不删端点或两侧曲面。

最终两侧外推找到G01_growth_r10的4条断层边，关联8张原生格面；它们距Mask边界7–13原生px、也不在CAD材料内，未满足预先冻结的上下文条件，因此仍保留Unknown。这说明**额外上下文门控过保守**，不是“没有异常”。这些确认边没有映射到相应的Raw原面（历史建面/离散化已不同），不能声称Raw也检出了8面。没有为了这8面事后改规则。其他大部分边缺少足够侧向支持，或局部平面残差过大。完整损失/规则与代码对照见METHOD_AND_INPUT_AUDIT.md。

## 四组结果（原始归档面）

'''+gtable+'''
所有来源：删面面积0，原可见首层覆盖保留100%，最大连续片保留100%，新增边界/内删片0；这由没有删除直接决定，**不能作为异常已清除的证据**。各来源数量、面积、连通、拉伸、密度、Ring指标见`metrics/FINAL_SOURCE_SUMMARIES.csv`，不是只报汇总。

G05/G06未发生过度清理，但并非全部可信。原归档面有至少两处CAD内采样的面数：G01=2369、G03=0、G05=96、G06=15，全部保留且记录。它们是当前冻结位姿下的材料占据冲突代理，不能单凭近Ring或CAD冲突判定深度表面物理错误。

## 哪些证据有用，哪些容易误删

源像素边长+深度跳变能定位G01/G03的异常延伸；须考虑透视和斜视。80°连续平面透视拉伸可达34.61，正确切平面拉伸约1，控制未误删。局部密度、三角形长宽比、面积、法向和深度突变高度相关，不能当多份独立统计票。PCA可在持续错误片层上给出正常法向。最近面竞争可能只是密集采样，k32也会漏掉远重心大面。两侧平面能排除自解释的一部分，但原HERO噪声、窄结构和边界缺样使它覆盖不足；孤立尖刺被保留Unknown，不伪称已经检测清除。

## 可视化与GT

四张主图：原始几何、逐面指标、RGB/三维可信度、清理前后；18来源各有几何/标记/清理图和证据图，另有5份原面ID局部图。所有Ring为黑色CAD，毫米尺度，Raw与Clean共用Raw原面范围和相机；保留全部原面几何，不平滑显示来冒充几何变化。未引用的原顶点保留在数据中，不拿它们拉远Mesh显示相机；原生深度全范围诊断另行保留。

项目GT访问为0；本轮不做ICP、Dxy真误差或几何准确率评价。无面级真值，不能给出误删率/召回率。解析平面、已知深度台阶是明确标注的控制，非项目Oracle。

## 下一阶段判断

G05/G06的内部正常大连续片可作为**人工审核候选**；G01/G03的大残余异常与Unknown不能直接作为“清理完的可靠HERO”投入主体适配。完整HERO及标签一并交付，不能隐含删除Uncertain/Unknown。TRUSTED仅指原始观测支持且内部有限指标正常，不是物理正确概率。本轮不执行适配，不将0删面冒充清理成功。后续若修改边界上下文，需单独验证对真实薄结构的影响；本轮到此停止。

## 固定审计表

'''+stable+'''
复现：REPRODUCE.md；完整产物：RESULT_INDEX.md / RESULT_INDEX.json；冻结证据：provenance；异常：FAILURE_LEDGER.md。所有算法与指标定义及具体代码位置见METHOD_AND_INPUT_AUDIT.md和metrics/CODE_POSITIONS.csv。
'''
    (R/'TECHNICAL_REPORT_SUMMARY.md').write_text(summary)
    detail='''# TECHNICAL_REPORT — TASK-E4-HERO-GEOMETRY-CLEAN-017

状态：**LABELING_COMPLETE / CLEANING_INCONCLUSIVE / NO_FACE_REMOVAL / AWAITING_HUMAN_REVIEW**。本实验不宣布HERO路线科学失败，也不宣布自动清理通过。核心结果与固定审计表见[摘要](TECHNICAL_REPORT_SUMMARY.md)。

## 分母与原始输入

四物理组、18原生来源；每份来源独立处理，不合并曲面。G01/G06多来源共享RGB且可能同源相关。原Mask为1=Polyp、2=Ring、0=Background；原生网格用冻结K作半像素中心映射并最近邻读取原Mask，未改Mask。原深度单位是相机轴向Z毫米，`X_world=(K^-1[u,v,1] Z) R^T+t`。所有18来源native K、native pose、archive K/pose/labels及camera_metadata都相符，后者最大姿态差0。历史相机资格仍为条件诊断，不由本轮几何检测认证。

ARCHIVE_RAW的原Face ID就是原数组行号，原顶点值取原PLY序列化后精确值，原source points/pack反投影误差<1e-5mm。NATIVE_GRID仅用于查询原生深度像素证据，诊断Face ID为`2*(v*(W-1)+u)+side`，不是Raw Face ID，严禁混用。已有Raw建面过滤并非本轮清理收益；原深度格和Raw面积不能作同分母前后对比。

## 初始诊断、一次补充与最终冻结

1. `PREANALYSIS_FREEZE`在实际指标运行前冻结阈值、算法及输入；控制17项通过。输入适配缺少旧函数要求的距离字段已在真实运行前修复，初版快照保留。
2. 初始36表示分析全部完成、0删面；保留OUTPUT_FREEZE、local_results与全指标。
3. 发现PCA候选污染后，登记`FINAL_CLEANING_RULE`及`BEFORE_FINAL_CLEANING`，只加同一内部科学问题的两侧外推。5项额外控制通过：3个连续斜平面无假断层；两平层深度阶跃识别44条可支持断层边；单像素无支持尖刺不误称双面支持。不是优化器/阈值消融或删除率搜索。
4. 一次最终18来源×2表示规则运行，仍0删除；所有预测子集冻结，再作只读失败归因和图像展示。没有后续删面回合。

## 原始归档面数量与面积

'''+gtable+'''
逐来源完整计数：

'''+mdtable([dict(source=x['source'],faces=x['original_faces'],area_mm2=f"{x['original_area_mm2']:.4f}",trusted=x['TRUSTED_faces'],uncertain=x['UNCERTAIN_faces'],unknown=x['UNKNOWN_faces'],rejected=x['REJECTED_faces'],components=x['raw_components'])for x in ss if x['representation']=='ARCHIVE_RAW'],['source','faces','area_mm2','trusted','uncertain','unknown','rejected','components'])+'''
所有级别的逐源面积、删除面积比、最大分量面积与最大连续片、源边界新增情况、密度与拉伸的raw/clean统计，均在FINAL_SOURCE_SUMMARIES.csv。0删除使其配对差值全部为0。真解剖主面、柄部、表面误删真值没有人工标注，不用最大连通分量假冒其真值。

## 原生深度格诊断（不是本轮输出重建）

'''+mdtable([dict(group=x['group'],native_faces=x['original_faces'],native_area_mm2=f"{x['original_area_mm2']:.4f}",unknown_uncertain_area=f"{100*x['uncertain_unknown_area_fraction']:.2f}%")for x in native],['group','native_faces','native_area_mm2','unknown_uncertain_area'])+'''
原生未过滤格中的G01/G03存在远大于Raw面的异常面积。它说明历史Raw的升采样与建面预过滤已经改变可见几何分母，不能只看Raw就认证整幅原始深度。保留这些诊断，不把新索引的三角形送入主体适配。

## 阻塞与失败机制

12261条候选原生边进入双侧平面检查（同阈值）；24522个半侧补丁中：7972不足6个有效原Polyp样本，11352平面RMS>0.125mm，294被排除端点不获平面支持，4904半补丁支持。支持单侧不等于双侧断层。仅growth_r10的4条边通过双侧检验，8张原生格面仍被上下文条件阻塞；距Mask7–13px、无CAD材料采样，且现有PCA/面片法向将其判掠视。真实Raw并非有相同8个原生Face ID，映射需看RULE_BLOCKING_ATTRIBUTION，不得冒称删除了Raw8面。

“内部指标不足以认证删除”与“上下文门控过保守”两者都存在；不能把零删除全部归因于数据不足。没有移除这些条件来制造正结果。PCA的局部平面自解释还可能给连续错误片层TRUSTED，所以其标签也没有被物理准确率校准。

## Ring、折叠与连续性

CAD为冻结闭合一致绕序Ring，用Open3D三样本符号查询；对每面取3顶点、3中点、重心，至少2点<-0.02mm为材料矛盾代理。近Ring(<0.3mm)不独立触发删除；首次CAD遮挡保留Unknown，材料内样本与合法后方遮挡分开。有限采样没有证明所有面无相交，相机与HERO误差也没有被分离。

形状检查包括三角面积/针状程度、相机朝向邻面法向跳变、面积加权一致性、原边界、非流形与连通分量。原生正深度规则像素三角网的投影内部不交叠，几何上不能任意形成同像素多层自交；尖刺/折棱仍可能存在。PROJECTIVE_TOPOLOGY_AUDIT记录正深度、投影方向、重复/零面积面等，**没有冒充通用FCL逐三角形自交认证**。保留原面且零删除，因此不新增拓扑损伤，也不修复已有异常。

## 交付与边界

主图使用真正的既有Raw Mesh（所有原面），黑色CAD，无外观平滑。被删栏为空且明示0。Native诊断图在figures/diagnostic_native_grid；每个具体面和原图位置可通过face_decisions与local_archive面片ID图定位。完整最终几何在final_results/<source>/ARCHIVE_RAW，保留原始数组及所有未引用点，只有原面子集；本轮子集恰等于全原面。

适配前建议人工首先审查G01/G03 Unknown延伸和Ring占据冲突；G05/G06内部正常片可提交候选，但不自动宣布物理正确。没有把可信片提取伪装成保留全部Unknown的清理，也没有进行主体配准、融合、GT调参或新HERO。
'''
    (R/'TECHNICAL_REPORT.md').write_text(detail)
    (R/'FAILURE_LEDGER.md').write_text('''# FAILURE_LEDGER

| 项目/病例 | 实际问题与证据 | 本轮处理 |
|---|---|---|
| G01（全部11来源） | 边缘拉伸、Ring占据冲突及Unknown；原面不确定面积24.02%；逐源RULE_BLOCKING_ATTRIBUTION、figures/full | 0删除，全部保留，不称伪影消失 |
| G03（仅1原生来源） | 深度远延伸、局部PCA自解释/掠视；无第二份native补造支持 | 0删除；不以单来源身份自动拒绝或认证 |
| G05 | 不能把“预计可靠”当真值；原面96张多样本CAD材料矛盾、边界异常 | 0删除；无过清，但异常未修复 |
| G06（5来源） | 原面15张多样本CAD材料矛盾、局部边界/竞争代理 | 0删除；不可将低异常数量称严格可靠 |
| PCA归一自解释 | 极端异常可能塑造自己的切平面/法向；初始规则0删除 | 初版协议、指标和负结果保留；只增加一次源侧外推检验 |
| 两侧外推覆盖不足 | 24522半侧补丁中11352 RMS失败、7972样本不足、294端点失败；逐边逐侧PATCH_FAILURE_ATTRIBUTION | Uncertain/Unknown均保留；未获双侧证据不升成拒绝，单侧4904支持不作独立双票 |
| 上下文过严 | G01_growth_r10仅4条确认边；8个native诊断面距Mask7–13px，不符合边界/CAD上下文 | 不事后改阈值；8面保持Unknown。说明规则本身也有限制 |
| 原生/Raw离散差异 | Raw历史升采样和建面过滤；未过滤native格面不是原Raw Face ID | 双身份分开。仅ARCHIVE_RAW原面子集是清理输出；native诊断不得送入适配 |
| 真误删率/清除准确率 | 无独立人工面级真值和GT | NaN/NOT_EVALUABLE。0删不等于检测器准确 |
| 准备期接口错误 | E1元数据无顶层K；旧density函数需Mask距离字段 | 运行前从真实pack读取K并补入原Mask距离，未改冻结相机/规则 |
| 准备期GT防火墙 | 历史保护遍历碰到旧GT符号链接，open在读前被拒绝 | 保护清单排除GT资产；GT几何未读取。并非放行GT |

本轮最终状态不是PASS清理：检测/标记工程完成，充分证据删除0/18来源，残余异常完整保留。无后续阈值搜索、二次叠加删除或跨视角辅助删除。
''')
    (R/'METHOD_AND_INPUT_AUDIT.md').write_text('''# METHOD_AND_INPUT_AUDIT

## 实际复用与差异

| 历史实现 | 复用方式 | 不能继承的含义 |
|---|---|---|
| Phase-C density.py::features | AST逐字提取，原k12/normal16、r0.4mm、入射/非平面性定义；适配source pixel数据 | 未运行D0/D1旧删点；密度不是错误概率 |
| Phase-C sparse run.py::face_components/edge_counts | AST逐字提取原共享边连通定义 | 未继承3px薄结构硬门槛或旧清理标签 |
| ring_first_v1 common.py::unproject | AST逐字提取原公制反投影 | 未重新恢复相机，未更改K或尺度 |
| E3-B MeshLocalField | 复用相机定向、面积加权法向一致性、原边界、k32非共享顶点竞争机制 | 这些原来决定局部场符号，不是表面物理真假；竞争筛查有限 |
| E4原真实Mesh renderer | AST提取原O3D实体光线追踪函数，仅接逐面色；主图读取原Raw数组 | 不用点云/解析几何替代原面，不平滑，不通过模型变形改善图像 |

## 明确公式和变量

固定：所有原深度、RGB/Mask、K/c2w、CAD和原顶点/面。没有可学习参数、optimizer、GT、HERO推理。新变量仅为原面状态与保留布尔值。

透视采样尺度：邻接i,j的预期边长 `(Zi+Zj)/2 * ||K^-1 pi-K^-1 pj||`。切平面尺度用原PCA法向与同射线的平面交点外推，从两端预期距离取平均。面上记录相关顶点八邻接最大值，不把它伪称仅本三角形最长边比；另列三角形真实最长边和面积。针状品质 `4sqrt(3)*area/sum(edge_length^2)`，等边为1。

法向一致性沿用E3-B：各面先朝源相机，按两倍面积在顶点累加；合向量长度/权重和，面取三个顶点最小。邻面最大夹角是曲率/折棱代理，不是标定曲率或错误真值。密度按预期透视面积归一；PCA可能受异常自身污染。边界EDT是前景采样中心到背景采样中心的欧氏距离，最近原Mask映射到native后计算，不减半像素；不能冒称原360-Mask的直接EDT。

初始联合规则及数值在config/PROTOCOL.json。补充规则为`1/Z=alpha du+beta dv+gamma`；端点之外8个半侧样本至少6有效，逆深度线性拟合（不是三维SDF/表面重建），预测深度RMS及端点误差<=0.125mm；两侧各自支持且跨端点预测差>0.5mm、原边长相对两平面预期>4、入射>=0.2。只给跨边原面添加证据，最终仍需shape和2px边界或CAD上下文。不把SDF/GT引入判断。

原定最终规则与实际gap017.py逐项相符；但追加的上下文条件使内部已确认断层仍无法拒绝，是方法局限。没有为得到更好结果偷偷移除此项。两侧源像素可分离，但HERO预测共享上游，不声称统计独立。

## 数值控制

CONTROL_TESTS.json 17项，TWO_SIDED_CONTROL_TESTS.json 5项：连续前向/65°/80°平面无误删和假断层；台阶识别44条断层；单像素无支持尖刺保留；Ring近距本身不入删除规则。台阶是解析控制，不是项目GT；未用这些数值搜索项目阈值。

## 输入与图像身份

SOURCE_LOCK锁定18来源，SHA在PREANALYSIS_FREEZE。原native K、pose与pack一致，原Mask与pack labels逐像素一致；camera_metadata存储姿态匹配差0，逐源CAMERA_METADATA_BINDING_AUDIT。G01旧原始视频帧顺序身份仍继承档案的条件性，不把这些匹配冒充新的相机认证。各组不混用世界坐标；只用video004各自产物。

## 原生离散化的忠实性限制

ARCHIVE_RAW是输入真实单参考Mesh，其历史构建已处理过深度尺寸和跳变。没有把它当完全未处理的网络深度。NATIVE_GRID是同深度的源像素局部诊断载体，新增的lattice编号与Raw原面编号严格分开，不能把诊断格导出当成新增或补好的HERO预测。适配候选只指ARCHIVE_RAW原面子集，不新增任何面。保留全部原顶点，包括未被原面引用的点。

## 工具与来源

距离变换定义参照[SciPy官方distance_transform_edt](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.distance_transform_edt.html)。CAD符号距离使用现有Open3D CPU RaycastingScene，前提是闭合、一致绕序；有限样本仅作证据，不保证无碰撞。依赖沿用既有venv，无新增大型框架。
''')
    (R/'REPRODUCE.md').write_text('''# REPRODUCE

CPU only，使用现有环境 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`。不需要GPU、模型权重或GT。原始输入通过config/SOURCE_LOCK.json及SHA索引读取，不复制大型数据。

为保护现有结果，在同一仓库experiments下建立新的空复现副本；原009、015、016输入必须保留在本地原路径。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
SRC=experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017
DST=experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017-REPRO
test ! -e "$DST"
mkdir -p "$DST/code" "$DST/config"
cp "$SRC"/code/*.py "$DST/code/"
cp "$SRC/config/FINAL_CLEANING_RULE.json" "$DST/config/"
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PY" -B "$DST/code/prepare017.py"
"$PY" -B "$DST/code/test017.py"
"$PY" -B "$DST/code/test_gap017.py"
"$PY" -B "$DST/code/analyze017.py"
"$PY" -B "$DST/code/freeze_final017.py"
"$PY" -B "$DST/code/gap017.py"
"$PY" -B "$DST/code/diagnose017.py"
"$PY" -B "$DST/code/figures017.py"
"$PY" -B "$DST/code/local_figures017.py"
"$PY" -B "$DST/code/deliver017.py"
"$PY" -B "$DST/code/validate017.py"
```

主清理输入/输出只用ARCHIVE_RAW；NATIVE_GRID为诊断，不当作补面重建。repro的固定FINAL_CLEANING_RULE来自已提供配置，不重新搜索参数。各统计与npz数值应一致；gzip时间戳、日志、JSON冻结时间和PNG软件渲染元数据不要求字节一致。

原阶段文档和源码sha见provenance/PREANALYSIS_FREEZE_INITIAL.json、PREANALYSIS_FREEZE.json、BEFORE_FINAL_CLEANING.json。补充规则在初始负结果之后且最终处理之前冻结；不是声称从任务起只运行过一条规则。
''')
    (R/'RESULT_INDEX.md').write_text('''# RESULT_INDEX

- TECHNICAL_REPORT_SUMMARY.md：结论、审计表、局限和下一步资格。
- TECHNICAL_REPORT.md：全源分母和科学失败解释。
- METHOD_AND_INPUT_AUDIT.md：公式、历史复用及实际实现差异。
- metrics/FINAL_SOURCE_SUMMARIES.csv、GROUP_SUMMARY.csv：逐源/逐组原面数、面积、连通与覆盖。
- metrics/RULE_BLOCKING_ATTRIBUTION.csv、PATCH_FAILURE_ATTRIBUTION.csv：为何异常没有删除。
- metrics/TWO_SIDED_GAP/：每条测试边的来源、原生像素ID、端点、外推误差与原因。
- face_decisions/*.csv.gz：全部原面最终分类、理由文字、原点和native Pixel ID、邻面状态；REASON_CODEBOOK.json是位码合同。
- final_results/<source>/ARCHIVE_RAW/FACE_EVIDENCE.npz：原始V/F、所有逐面异常指标、状态、原Face/Pixel身份。
- final_results/<source>/ARCHIVE_RAW/CLEANED_SUBSET.npz / CLEANED.ply：真正清理输出，原面子集、坐标精确不变；本轮0删，故等于原面集合。
- final_results/*/NATIVE_GRID：仅原深度网格证据诊断，不作为主体适配输入或新的重建结果。
- local_results：初始PCA诊断负结果及其完整逐面指标/CSV，不覆盖。
- figures/Fig1–Fig4：四类原始Raw Mesh主图；figures/full：18来源各两图；figures/local_archive：原Raw Face ID局部证据。
- figures/diagnostic_native_grid：原深度格完整范围诊断图；编号和面积不能与Raw原面混淆。
- RESULT_INDEX.json：逐文件本地绝对路径、SHA与原source几何索引。

精确完整几何/证据NPZ保留本地；Git提交代码、配置、核心/逐源图、小表和完整压缩逐面决策。未上传大原始模型、视频或环境。未修改DXY/016/015及原始相机/HERO/Mask/CAD。
''')
    positions=[]
    for p in sorted((R/'code').glob('*.py')):
        for n in ast.parse(p.read_text()).body:
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)):positions.append(dict(file=str(p.relative_to(R)),name=n.name,line=n.lineno,sha256=sha(p)))
    table('metrics/CODE_POSITIONS.csv',positions)
    save('provenance/DELIVERY_FILES.json',dict(epoch=time.time(),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],documents=[asset(p)for p in sorted(R.glob('*.md'))],figures=[asset(p)for p in sorted((R/'figures').rglob('*.png'))],GT_used=False))
    print('REPORTS_INDEX_AND_FULL_FACE_CSV_GZ_COMPLETE',len(outindex),flush=True)
if __name__=='__main__':main()
