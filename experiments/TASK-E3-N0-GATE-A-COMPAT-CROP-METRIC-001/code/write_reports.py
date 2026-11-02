"""Report actual evidence; never relax any geometry or crop threshold."""
from crop import *
V=R/'derived_projective_v1'
def md(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |'for r in rows)+'\n'
def pct(x):return f'{float(x)*100:.2f}%'
def put(path,text):(R/path).write_text(text.strip()+'\n')
def main():
    raw=list(csv.DictReader((R/'CROP_GEOMETRY_TESTS.csv').open()));cleaned=list(csv.DictReader((V/'CROP_GEOMETRY_TESTS.csv').open()));cross=list(csv.DictReader((R/'CROSS_VIEW_PROJECTION_VALIDATION.csv').open()));cross2=list(csv.DictReader((V/'CROSS_VIEW_PROJECTION_VALIDATION.csv').open()));metrics=load(R/'METRIC_TRANSFORM.json');full=metrics['domains']['ALL_INPUTS'];current=load(R/'config/POST_REVIEW_DOMAIN_SELECTION.json')['transform'];compat=load(R/'config/CHECKPOINT_COMPATIBILITY_DETAILS.json');tests=load(R/'config/CONTRACT_TEST_RESULTS.json');cleanup=load(R/'PROJECTIVE_CLEANUP_SUMMARY.json');candidates=list(csv.DictReader((R/'PROJECTIVE_CLEANUP_DECISIONS.csv').open()));human=load(R/'HUMAN_REVIEW_CONTEXT.json');baseline_N=sum(int(r['original_legal_N'])for r in raw);evidence_N=len(cross)
    crop_table=md(['来源','原生合法N','a','原ID采到比例（原始）','派生排除N','量化误差p95 / max mm（派生）','最窄输出代理px'],[[a['source'],a['original_legal_N'],f"{float(a['scale']):.6f}",pct(a['original_ID_retention']),46 if a['source'].endswith('r00')else 0,f"{float(b['nearest_XYZ_p95_mm']):.5f} / {float(b['nearest_XYZ_max_mm']):.5f}",f"{float(b['minimum_crop_ridge_width_px']):.4f}"]for a,b in zip(raw,cleaned)])
    cross_table=md(['有向关系','完整原点N','median px','p95 px','max px','裁后图外 / CAD遮挡 / 目标支持采样损失'],[[r['origin'].split('004_')[1]+'→'+r['target'].split('004_')[1],r['source_point_denominator'],f"{float(r['analytic_projection_median_px']):.3e}",f"{float(r['analytic_projection_p95_px']):.3e}",f"{float(r['analytic_projection_max_px']):.3e}",r['OUT_OF_CROP_FIELD_N']+' / '+r['CAD_OCCLUDED_N']+' / '+r['CROP_LOST_SUPPORT_N']]for r in cross[:6]])
    conditional_table=md(['条件性有向关系','全部原点N','max px','OUT_OF_CROP_FIELD / CAD'],[[r['origin'].split('004_')[1]+'→'+r['target'].split('004_')[1],r['source_point_denominator'],f"{float(r['analytic_projection_max_px']):.3e}",r['OUT_OF_CROP_FIELD_N']+' / '+r['CAD_OCCLUDED_N']]for r in cross[6:]])
    gate_rows=[dict(gate='A1',status='PASS',reason='fixed6 sources, original SHA/DAG/K/c2w/CAD unchanged'),dict(gate='A2',status='FAIL_THIN_PROXY_ANALYTIC_PASS',reason='all analytic XYZ<1e-5mm and no bbox loss; r14 output ridge proxy2px<3px, anatomy unresolved'),dict(gate='A3',status='PASS_TRANSFORM_ONLY',reason='6CORE+18conditional pairs, all original point IDs retained in validation before/after cleanup; not camera certification'),dict(gate='A4',status='PASS_INVERSE_CANDIDATE_PENDING_PM',reason='same29.641mm retained-input cube, reversible; all retained points enclosed; no formal domain freeze'),dict(gate='A5',status='PASS',reason='Ring/BG/Unknown/Pad depth0, NaN handled explicitly'),dict(gate='A6',status='PASS_CPU_STRICT_FORWARD_NOT_TESTED',reason='official ShapeNet30 state tensors/1,403,920 params exact strict load; backup only static'),dict(gate='A7',status='PASS',reason='historical source/unproject/K/project/CAD functions executed unchanged via AST/import'),dict(gate='A8',status='PASS_SUBJECT_TO_FINAL_HASH_CHECK',reason='no GT, neural forward, CUDA, newTSDF/HERO/camera fitting; only user-approved derived copies modified')]
    table('GATE_A_DECISION.csv',gate_rows);save('GATE_A_STATUS.json',dict(status='GATE_A_FAIL',subtype='GATE_A_FAIL_GEOMETRY',reason='r14 single2px mask-edge ridge proxy violates frozen3px threshold; formal crop/domain acceptance pending PM. No claim that true stalk disappeared.',gates=gate_rows,raw_contract_PASS=tests['PASS'],raw_contract_FAIL=tests['FAIL'],primary_official_model_strict_load=True,analytic_same_identity_world_max_mm=max(float(r['analytic_XYZ_max_mm'])for r in raw),analytic_target_projection_max_px=max(float(r['analytic_projection_max_px'])for r in cross),user_authorized_cleanup=dict(rounds=1,candidates=55,derived_excluded=46,retained_unresolved=9,original_data_mutation=0),proposed_metric_cube_L_mm=current['L_mm'],physical_voxel_mm=current['voxel_mm'],source_order=IDS,GT=False,GPU=0,NeuralFusion_forward=0,Translator_forward=0,new_TSDF=0,new_HERO=0,training=0,Gate_B_authorized=False,next_stage_started=False))
    gate_table=md(['Gate','状态','原因'],[[r['gate'],r['status'],r['reason']]for r in gate_rows])
    audit=md(['审计项目','必须汇报'],[['目标组数','1物理组，G01_004单视频；固定6来源，原始106,144合法原生像素'],['本算法独立成功','1/1组产生坐标/输入合同；整体GateA通过0/1。神经融合与测量NOT_RUN，不宣称重建成功'],['本算法失败','G01_004：r14裁后2px边缘代理触发3px门槛；初始物理域过粗；模型前向未评价。直径/形状GT误差NaN'],['历史测量值回退','0；未读取S0、历史融合测量或Dxy'],['失败组及具体原因','见FAILURE_LEDGER.md、Fig4及两张人工判读图；46派生排除、9未决点均逐原ID留存'],['最终统计样本','六源全部原像素分母106,144；派生保留106,098另列，投影校验仍保留全部原ID。独立物理GT/盲测样本=0'],['是否使用GT选择算法','否；先冻结FP64阈值和20%/16px统一裁剪，后计算；用户人工判读是记录的组织/可信性意见，不是物理GT']])
    put('TECHNICAL_REPORT.md',f'''# TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001

日期：2026-11-02（Asia/Shanghai）；父提交 `d69ade170352d1b5a1e46239f9516ab38c575648`；分支 `exp/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001`。

本轮仅执行Gate A。官方ShapeNet主模型在CPU构造并以strict=True加载，30个状态张量与1,403,920个神经参数逐项一致，未调用任何模型前向。六来源独立等比例裁剪的同原像素解析XYZ最大误差为1.59×10⁻¹⁴mm，三CORE六有向关系及18个条件性关系均保持，最大投影残差1.73×10⁻¹³px。原始全包域因边缘远端深度扩大至61.837mm；研究者现场判读后新增授权一轮投影清理，55候选中46点在派生副本排除、9点保留，候选全包域缩至29.641mm、体素0.23157mm。原始HERO/Mask/相机均未变。r14裁后出现2像素边缘宽度代理，低于冻结3像素门槛；尚不能认定为真实细柄损失，仍保留FAIL。整体结论为GATE_A_FAIL，未进入Gate B、GPU或任何融合实验。

## 授权、输入与复用

已读取AGENTS.md、COLLAB_STANDARD_v1.3.md及四份PM文件（docs/按原字节保留）。PM草案的DRAFT_NOT_APPROVED由用户本轮明确批准Gate A覆盖；B/C/D未获授权。首次缺文件时暂停正式验收，研究者下载补齐后才冻结并计算。附件和四文件SHA见 [AUTHORIZATION_AND_DOCUMENTS.json](config/AUTHORIZATION_AND_DOCUMENTS.json)。

顺序严格为ref08(B3)、ref13(B5)、ref03(B2)、growth_r04(B3)、new_r00(B1)、growth_r14(B4)。CORE是本轮角色，未提升历史相机资格：前五均保留Camera Gate的INSUFFICIENT_EVIDENCE，r14仍未单独完成Camera Gate。来源DAG、上游RGB相关性、原生352×640、归档360×640、原K/c2w和CAD沿用D0六源白名单。只验证必要六源文件及SHA，没有重做全资产审计。

实际复用 [CODE_REUSE_MATRIX.md](CODE_REUSE_MATRIX.md)：D0 source/native ancestry、HEROToTSDFAdapter、mesh_scene/cast/distance/ringmesh，旧unproject，冻结scaled_intrinsics/project_camera/camera_rays，SameCameraScene。采用精确AST抽取/直接导入，绑定本任务IO以避免D0模块main和旧输出写入。新增内容只是裁剪仿射、身份可追踪采样器与诊断组合；没有重写相机投影、反投影或射线算法。Raw Mesh仅作比较/诊断bbox，不生成伪深度。

## A6 官方模型、权重与环境

官方固定提交 [`4f0c14f`](https://github.com/weders/NeuralFusion/tree/4f0c14f67ad9d2368b68cbeb78c237a6328971e5)，24个代码/配置/权重文件逐Git blob及本地SHA256核对，清单 [OFFICIAL_ARTIFACTS.json](config/OFFICIAL_ARTIFACTS.json)。

| 权重 | SHA256 | 静态结构及结果 |
| --- | --- | --- |
| ShapeNet noise0.005 / best.ckpt | `3ac6dc9f219449e8aa5a26dec0a77691714e55d4e29da688c79630bf46068bff` | 16,882,708 bytes；128³、17特征（16 learned+count）、±3体素采样、SDF/occupancy heads、output_scale=0.04；strict=True PASS |
| Tanks&Temples / best.ckpt | `404867f7ab7e7cf978cd31bab3466334f50b4d12a3721e24e10e7d7d56ea570b` | 18,237,012 bytes；64³、9特征、外部count、±6采样、output_scale=0.06；仅静态反序列化/配置核验，无备用模型构造或前向 |

主模型保留官方FusionPipeline及全部层，仅以普通torch.nn.Module承载官方Lightning checkpoint的`_pipeline.`命名空间，避免import训练/GT数据库。未过滤任何state key；严格missing/unexpected/shape mismatch均为0。config.json、checkpoint hyper_parameters、hparams.yaml的网络配置一致，唯一运行设备放置为CPU。`weights_only=True`，只额外允许经审读的官方EasyDict1.9数据类；YAML用不构造Python对象的BaseLoader解析。备用状态与主结构的混载在真正载入前由键/形状合同拒绝，未用strict=False。

本机Python{compat['runtime']['python']}、Torch2.7.1+cu128（以 [实际runtime记录](config/CHECKPOINT_COMPATIBILITY_DETAILS.json) 为准），官方锁定Python3.7.6/Torch1.10.1/Lightning1.5.7/CUDA10.2/Open3D0.10。CPU严格加载进程峰值RSS约{compat['runtime']['max_RSS_MiB']:.1f}MiB；这不是融合峰值。未初始化CUDA，驱动仅只读/proc信息；GPU可用性/融合运行兼容NOT_TESTED。Open3D0.19复用历史vendor做CPU射线，无新TSDF。

主环境未修改。PyPI下载EasyDict因TLS EOF失败，改用其官方1.9标签对应提交`9d570ecc2799d8df16c640100c89a028dabc03a7`的原模块，独立置于任务runtime/python并核对blob/SHA；未升级全局包。官方training/database.py所需graphics沿RoutedFusion固定submodule追到[`weders/graphics@dfdd7d2`](https://github.com/weders/graphics/blob/dfdd7d21dcafe2542eb56f9c57f605117abbe4c5/src/graphics/voxelgrid.py)，还依赖tsdf/gridData等；没有安装或执行GT数据库。这个依赖问题不妨碍纯模块CPU构造，但完整官方test.py不在本轮可运行合同中。

[`pipeline.py`](https://github.com/weders/NeuralFusion/blob/4f0c14f67ad9d2368b68cbeb78c237a6328971e5/pipeline/pipeline.py)硬编码B1/H240/W320，FusionNet LayerNorm也固定空间尺寸。输入只消费深度/Mask/K/c2w、origin/resolution/latent/count，RGB仅供本轮判图。[`integrator.py`](https://github.com/weders/NeuralFusion/blob/4f0c14f67ad9d2368b68cbeb78c237a6328971e5/pipeline/integrator.py)在use_count=true时使用latent最后一维计数，外部count仍须初始化；reset不能替代重新置零体积/count。Translator可解码SDF/occupancy，但零count/Unknown的行为未前向验证，不得认证其零面。

## A2 独立裁剪与相同身份验证

[预登记协议](config/GATE_A_PREREGISTERED.json)在正式计算前冻结：FP64解析XYZ≤1e-5mm、连续目标投影≤1e-4px、薄结构输出宽度代理≥3px；所有原生合法点参与（每源12,163–23,771，均超过1000），不是只取有利像素。边界、近Ring、头部、深度跳变等都在完整点集中；原生未发现宽≤6px的medial ridge细柄代理，不能据此声称没有真实细柄。

每源bbox(Polyp∪visible Ring)两侧扩`max(ceil(0.2*max边),16px)`，扩为最小整数4k×3k虚拟矩形，再等比映到320×240。原图外是显式padding，不clip ROI。像素中心公式`u'=a(u-u0+0.5)-0.5`，`K'=AK`；nearest=floor(逆映射中心+0.5)。不同a完全允许，三维R/t与共同模型尺度不随之改变。深度只取对应原像素的合法Polyp值；不在无效0与前景间插值。

{crop_table}

六源ROI外丢失为0；ref03/r04/r00的原像素ID未直接采到是**离散重采样身份损失**，不能冒充连续几何错位，也不等于丢失同等百分比实体面积。逐原ID的represent/nearest-source-ID/actualXYZ误差均保存在local_results。解析最大原始1.5888e-14mm，派生1.2307e-14mm；实际nearest量化最大值仍达ref03 13.42mm、r04 11.64mm、派生r00 19.56mm，来自深度跳变处取到不同原像素，不能只报约0.03mm中位数遮蔽极值。原始r00最大49.77mm也保留。

Ring/BG/Unknown/Pad进入有效深度的数量全部0。r00 padding=960输出像素，其余0。解析CAD前后次序变化全部0；真实离散采样后的CAD次序变化依次64/45/86/47/107/51条（r00原始108），说明像素量化会影响遮挡资格，应供未来B阶段首层审计，不能混成解析变换失败或静默排除。

r14在crop(99,143)附近有一个宽度代理2px的局部距离变换极大值；原生没有对应<3px的medial ridge。现场图更接近Mask边缘凸起，**未认证为真实细柄，也未证明真实细柄已丢失**。冻结规则没有例外，本轮记THIN_STRUCTURE_UNRESOLVED_BY_CROP并保留FAIL，未手工改其ROI、删除像素或放宽阈值。

## A3 核心：跨视角关系不变性

直接使用原始世界点及冻结目标相机，比`π'_j(X)`与`A_jπ_j(X)`。没有最近邻点云替代身份闭环，没有剔除图外/遮挡点提高误差。以下是全部原点分母；CAD遮挡与目标支持采样变化是资格/采样记录，不能据此认证原位姿。

{cross_table}

全部24关系最大1.7288e-13px。条件性来源的完整表：

{conditional_table}

清理后再次执行相同24关系，仍使用全部**原始**世界点/ID（含46个派生排除点），数值门槛全部保持；其新目标输入有效域另列。未将排除点从坐标验证分母消失。原始及派生CSV均上传；完整逐点target UV/Mask/CAD/图外标志留本地索引。r00→ref08/13的28/72个图外投影如实保留。

## 人工判读后的单轮投影清理：新增授权

原本Gate A不做清理。发现55点使模型域膨胀后，先停域选择，提供两张真实RGB/Mask/深度/3D判读图。研究者明确判断这些边缘点的极远三维位置不可信，并新增授权一轮多角度投影清理后再选域。授权和方法边界见 [HUMAN_JUDGMENT_AND_SCOPE_UPDATE.json](config/HUMAN_JUDGMENT_AND_SCOPE_UPDATE.json)。它不授权任何神经前向或一般G2/G3。

本轮仅以已判读的55个new_r00原生像素为候选；其余106,089个原合法像素不在清理池。先冻结 [单轮规则](config/PROJECTIVE_CLEANUP_PREREGISTERED.json)：用ref08/ref13/ref03及r04作条件性观察者，至少两个不同View Partition区域出现图内BG投影、距Polyp外轮廓>8归档像素、无CAD遮挡，且没有≤0.25mm深度支持，才在派生副本无效化。8px来自历史CORE Ring p95最大值向上取整再加2px，并非看清理结果调阈。相同B3的ref08/r04不作为两个独立方向票；共享RGB仍不能当独立统计证据。

结果：**46/55派生排除，9/55保留未决**。9点P47–P55在其他视角落于Polyp Mask但存在前后层差异，其中还有CAD遮挡；不能把合法遮挡简单当错误面。全部220条观察证据、逐点动作与原坐标在 [PROJECTIVE_CLEANUP_EVIDENCE.csv](PROJECTIVE_CLEANUP_EVIDENCE.csv)、[DECISIONS](PROJECTIVE_CLEANUP_DECISIONS.csv)。原始文件/Mask/三角面均未删除；派生depth置0、valid=0，表现为Unknown，未补面。

这套轮廓反证仍受条件性相机与未知真实背景遮挡影响，**是经人工先验支持的工程代理，不是物理错误GT**。没有使用E3-C Free-space硬标签，没有新相机/匹配模型或参数搜索，只执行一轮。六源/源DAG/方向顺序/裁剪规则不变。

## A4 公制模型尺度与选择

原始全包候选L=61.837mm，128³体素0.483102mm，约12.4mm Ring只占25.67格；诊断小框L=25.735mm会有55原合法点出界。因此先保留停机记录并请求研究者判断，未偷删深度。

按新增授权清理后，选择**容纳全部保留输入（含9未决点）**的候选域：

- O_mm = `{[float(x)for x in current['O_mm']]}`；L_mm =29.641；同一世界/模型坐标适用于全部六源。
- `X_model=(X_mm-O_mm)/L_mm`，resolution_model=1/128；物理体素 **0.2315703125mm**，Ring外径约53.55格。
- 深度Z_model=Z_mm/L；c2w旋转不变，中心`(C_mm-O_mm)/L`；绝不是D0的w2c。所有源共用同一个3D尺度。
- Ring逆变换最大误差 `{current['ring_inverse_max_mm']:.3e}mm`，恢复外径约 `{current['ring_outer_diameter_inverse_mm']:.8f}mm`。公制代数可靠，没有通过GT或相机拟合确定尺度。
- 清理后原生输入106,098点全部在当前候选域；诊断小域仍有9点出界，故不用它强裁点。原始106,144分母另保留。

原始域、派生域、当前候选选择均在 [METRIC_TRANSFORM.json](METRIC_TRANSFORM.json)及 [POST_REVIEW_DOMAIN_SELECTION.json](config/POST_REVIEW_DOMAIN_SELECTION.json)。候选已选供PM审阅，**未正式冻结为可推理的合格模型域**。按原冻结门禁，薄结构代理尚未通过；原始停机测试不被改成PASS。主Translator标称±0.04模型单位若在未来运行，约对应±1.18564mm；本轮没有验证其实际输出或Unknown行为。

静态CPU空latent[128,128,128,17]与count[128,128,128]的全零/reset合同已实测，总存储144MiB，未调用任何写入融合。官方纯unproject函数在真实裁后输入上单独核对坐标；这不是FusionPipeline.forward。接口及各字段dtype/device/unit在 [INFERENCE_ONLY_SCHEMA.json](INFERENCE_ONLY_SCHEMA.json)，派生准备函数prepare_candidate也只返回数组。

## Gate结果、保护与复现

{gate_table}

原始专项合同42 PASS / 2 FAIL（r14薄结构代理、原始域未就绪），失败原样保留；一轮清理后的6源输入合同、24关系及原分母对照另列。错w2c、1000倍深度、native误用archived K、1px主点偏移、NaN/0/负深度、Ring/BG、padding、错误权重混载、GT/训练导入及历史写入均产生显式拒绝/状态。运行中u/v测试索引及AST缺helper的两处实现错误已修正并留记录，没有改阈。

[GT_ISOLATION_AUDIT.md](GT_ISOLATION_AUDIT.md)给出静态路径与守卫结果。没有读取GT/Oracle/Dxy、执行training/database、修改HERO/Ring-First/CAD/P0或创建任何新融合Mesh。只上传源码、表、四核心图与两张研究者要求的判图；权重/原深度/逐点大表LOCAL_ONLY。安全重放入口见 [REPRODUCE.md](REPRODUCE.md)，全部本地证据SHA见LOCAL_RESULTS_INDEX.json。

![输入与裁剪](figures/Fig1_RGB_Mask_Crop.png)
![同相机原始与裁后XYZ](figures/Fig2_Raw_vs_Cropped_CORE3_XYZ.png)
![跨视角变换](figures/Fig3_CrossView_Invariance.png)
![尺度与负案例](figures/Fig4_Metric_And_Failure.png)

## 五个最终回答

1. 官方模型：**主权重结构及CPU严格加载兼容**；完整融合前向/GPU/译码质量未测试，Tanks仅静态备用。
2. 六源裁剪：解析与ROI包围均有效；采样身份损失、深度跳变量化和r14的2px边缘代理使整体裁剪门槛尚未通过。
3. 三CORE关系：六个有向解析合同严格保持；其他18关系同样保持。它不认证原相机正确。
4. 公制尺度：共同可逆变换可靠；一轮清理后推荐29.641mm全包候选，容纳9个未决点，正式质量验收待PM。
5. Gate B：**暂不直接申请启动推理。** 先由PM审阅r14代理是否为需要保护的真实结构、统一门槛/候选域是否接受，以及46点派生处理的适用范围；没有自动清理第二轮或修改标准。后续推理仍须单独授权。

## 固定审计表

{audit}

结论：**GATE_A_FAIL（GATE_A_FAIL_GEOMETRY）**；停止等待PM/研究者验收。
''')
    put('FAILURE_LEDGER.md','''# 失败与未决记录

| ID | 状态/机制 | 证据与处置 |
| --- | --- | --- |
| ENV01 | RESOLVED：四PM文件起初缺失 | 研究者下载补齐后才正式预登记；没有编造规则；docs/保留原字节 |
| ENV02 | RESOLVED：EasyDict1.9 PyPI TLS失败 | pip/curl均未改主环境；取官方1.9标签精确模块置runtime/python，blob/SHA已记录 |
| IMPL01 | CORRECTED：阴性测试u/v赋值颠倒导致IndexError | config/VALIDATION_INITIAL_EXECUTION_ISSUE.json；修正测试索引，仅重跑中断验证，阈值不变 |
| IMPL02 | CORRECTED：派生重核AST namespace遗漏make_domain | config/DERIVED_RECHECK_EXECUTION_ISSUE.json；复用原helper，保留已完成crop，只续算metric |
| GEO01 | FAIL：r14裁后一个medial-ridge宽度代理2px<3px | Fig4、REVIEW02；原生无对应细柄代理。可能是Mask边缘锯齿，不认证细柄丢失；不改ROI/门槛 |
| GEO02 | OBSERVED：nearest重采样身份损失/极端量化 | ref03/r04/r00原ID保留69.48%/77.29%/70.94%；r00原始最大49.77mm，派生仍19.56mm；全部分母和失配身份留存 |
| VIS01 | OBSERVED：离散采样改变CAD前后次序 | 解析变化0，实际采样6源64/45/86/47/107/51（派生）；不把采样资格变化隐藏成解析PASS |
| ROI01 | ORIGINAL_STOP_RETAINED：全包域61.837mm过粗 | 128³voxel0.4831mm，诊断小域55点出界；按任务停域选择并给人工判图 |
| CLN01 | USER_AUTHORIZED：一轮派生清理46点 | 仅55已判读候选，固定跨视角规则/逐点依据；原数据不变，其他原点不清理。条件性相机、RGB相关和背景遮挡未独立标定 |
| CLN02 | UNRESOLVED：9点未获得大轮廓反证 | P47–P55落入其他Polyp Mask/存在深度层和CAD遮挡；保留，未扩大参数搜索或追加一轮 |
| ROI02 | CANDIDATE_PENDING_PM：清理后全包域29.641mm | 容纳全部保留点，0.23157mm/voxel；诊断小域仍9点出界，不使用小域硬裁；正式域未冻结 |
| MOD01 | NOT_TESTED：真正NeuralFusion前向/Unknown译码/GPU | strict CPU加载成功只证明结构/权重；没有F0–F5、Translator前向、任何Mesh、训练或新TSDF |

原始42PASS/2FAIL并未被覆盖。新增清理前后均保留106,144原始点分母；派生输入有效106,098另列，46点动作不冒充重建误差改善。

人工判读仅提供可信性意见，不构成物理GT或相机认证。当前整体GATE_A_FAIL_GEOMETRY；不建议绕过r14门槛直接开Gate B。
''')
    put('GT_ISOLATION_AUDIT.md','''# GT隔离与数据保护

执行入口只读D0六份原始HERO白名单、冻结RGB/Mask/K/c2w/Ring和源码/PM文档。以源码审计方式阅读官方training/database.py及training/pipeline.py，没有导入或调用其Database、setup、训练/评估逻辑；官方test.py未执行。没有GT/Oracle/Blender/Dxy/历史测量值访问。

原模块构造使用官方FusionPipeline置入普通torch.nn.Module的_pipeline命名空间，严格加载完整state_dict；避免Lightning与graphics的GT数据库初始化。checkpoint仅用weights_only=True及审读过的EasyDict1.9类。所有参数放CPU。profile守卫禁止官方/torch.nn forward入口；运行模型前向计数0，CUDA initialized=False，training/graphics/Lightning模块导入列表为空。见config/MODEL_LOAD_GUARD_RESULTS.json。

common.py运行审计hook拒绝：任务外写入、GT/Oracle/Dxy路径、非白名单几何/权重、training/graphics/Lightning导入、执行期网络。负测试的GT_READ、TRAINING_IMPORT、HISTORY_WRITE在文件访问/创建前触发PermissionError；并未创建假GT文件。无效0/NaN/Ring/BG进入有效深度数量0。外部文件读清单与预期拒绝见config/GEOMETRY_RUNTIME_ACCESS.json。

只有用户在看到两张真实判读图后明确新增授权的一轮派生清理写入了新的depth/valid副本；原始Mask、native深度、Raw三角面、相机、Ring CAD和DAG完全保留。清理范围固定55个原native像素，46排除、9保留，其他点逐位不变。没有将派生数组覆盖回源文件。

六来源及其必要资产SHA、所有历史工作树HEAD/已修改文件SHA在最终交付前复核；结果见config/FINAL_PROTECTION_CHECK.json。新实验只在独立分支和任务目录写入，没有git clean/reset/force push。主Python环境未pip升级；权重与隔离依赖仅在task runtime下，不上传。

所有图均为真实RGB/Mask、真实HERO坐标或候选体素边界；无神经输出、纹理平面、GT对齐或补面。结构精度/测量误差/真实相机位姿GT均NOT_EVALUABLE，直径NaN，历史回退0。
''')
    put('REPRODUCE.md','''# 安全复现（CPU，Gate A only）

父提交d69ade170352d1b5a1e46239f9516ab38c575648；全部源文件/原点身份、相机和SHA见SOURCE_AND_CROP_MANIFEST.json。数据路径沿用本机历史资产；另机需同身份/同SHA数据映射，不能用其他预测补齐。官方源码/两权重与EasyDict1.9仅在runtime本地，config/OFFICIAL_ARTIFACTS.json记录固定URL、Git blob和SHA256。

代码入口：preregister.py→checkpoint_compat.py→build_crops.py→cross_view.py→metric_domain.py→verify_contracts.py。人工查看human_review_figures.py的两张图后，用户新增授权projective_cleanup.py一次；随后recheck_cleaned_inputs.py、finish_scope_update.py保持相同裁剪/阈值重核并选全包候选。figures.py输出四核心图。禁止把未执行的F0–F5或matched Open3D加进复现链。

在已有交付目录**安全重放到全新目录**，不覆盖本轮数据：

```bash
cd /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/fetch_official.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/replay_geometry.py --output runtime/replay_review_01 --include-authorized-cleanup
```

fetch_official仅获取缺失的固定资产/核验已有SHA，不执行模型。replay_geometry在新的task/runtime子目录绑定同一源码函数与IO；重放原始crop、24关系、两个候选域、同一55点规则、派生crop和24关系，按原分母比较原CSV。它不是重新搜索/另做科学清理，也不触及原始资产。若runtime/replay_review_01已存在，换新目录名，脚本拒绝覆盖。模型静态严格加载结果可审阅CHECKPOINT_COMPATIBILITY_MATRIX.csv及config细节，不需要运行任何forward来复核状态键/形状。

需要独立重新strict CPU检查时，使用同固定官方源码、EasyDict1.9和TorchCPU加载路径；代码checkpoint_compat.py禁止training/GT/forward。该脚本默认写本任务结果，历史交付请在独立新工作树副本中检查，勿覆盖冻结统计。无需安装Lightning/graphics/官方旧完整环境，本轮只构造纯模块；兼容性不延伸至GPU或正式融合。

相同native像素的解析XYZ阈值1e-5mm；连续投影阈值1e-4px；r14宽度代理2<3保留FAIL。原始42PASS/2FAIL不是“全过”。完整本地逐点数组、depth/crop/身份、24关系和派生副本SHA见LOCAL_RESULTS_INDEX.json；权重/全深度和重放中间文件不进Git。docs中的两行Markdown双空格来自PM原文的换行，原字节保留，未篡改源规范。

主要依赖：Python3.12、Torch2.7.1、NumPy1.26.4、历史Open3D0.19 vendor、OpenCV、trimesh、Pillow、Matplotlib、PyYAML；无新模型推理、无GPU、无optimizer.step、无新TSDF。N0停止于Gate A，所有后续门禁仍需研究者单独授权。
''')
    # Explicit link of derived source bytes to original provenance, not pseudo-depth.
    lineage=[]
    for row in cleanup['sources']:
        cid=row['source'];original=next(r for r in MANIFEST['sources']if r['source_id']==cid);lineage.append(dict(source=cid,original_native=original['assets']['native_depth'],derived_depth_and_valid=row['derived_file'],original_legal_N=row['original_legal_N'],derived_legal_N=row['derived_legal_N'],excluded_original_native_ids=[int(r['native_pixel_id'])for r in candidates if r['source']==cid and r['derived_action']=='PROJECTIVE_EXCLUDE'],crop=asset(V/'local_results/crops'/(cid+'.npz')),original_Mask_unchanged=True,camera_unchanged=True))
    save('DERIVED_INPUT_LINEAGE.json',dict(sources=lineage,cleanup_rounds=1,protocol=asset(R/'config/PROJECTIVE_CLEANUP_PREREGISTERED.json'),all_original_SHA_retained=True))
    print('REPORTS_READY_GATE_A_FAIL_RETAINED',flush=True)
if __name__=='__main__':main()
