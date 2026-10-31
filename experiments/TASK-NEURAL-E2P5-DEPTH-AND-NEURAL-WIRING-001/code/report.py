"""One E2.5 technical report, explicit failed gates and fully specified blocked MVP."""
from common import *
import platform,importlib.metadata

def rows(name):return list(csv.DictReader((R/'metrics'/name).open()))
def md(headers,rr):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
        ['| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in rr])
def write(name,s):(R/name).write_text(s.rstrip()+'\n')

def mvp():
    domains=load(E2/'config/SDF_INITIALIZATION_CANDIDATE.json')['scenes']
    cfg=dict(task=R.name,status='PROPOSED_NOT_RUN_BLOCKED_BY_CPU_GATES',GPU='NOT_AUTHORIZED',execute=False,
        scenes=selected(),domains=domains,model=dict(class_name='official MonoSDFNetwork plain MLP',official_revision='12513009cd20a08b35ddc2c55a7e42da2c7baf43',
            Grid_MLP=False,feature_vector_size=256,implicit_dims=[256]*8,multires=6,skip_in=[4],rendering_dims=[256,256],multires_view=4,per_image_code=False),
        initialization=dict(seed=20261031,rule='source ROI shell calibration proposed for NEXT bounded CPU gate; NOT RUN in this two-candidate task',
            radius_mm='0.5*frozen source ROI radius',shell_point_N=128,shell_points='deterministic Fibonacci sphere in network coordinates',
            bias_rule='create the same seeded raw-head network with bias0; b=median raw SDF on shell; reconstruct same seed with bias=b; no GT or per-group error selection',
            acceptance='all three fixed source probes must have >=50% observed front hits and finite nonzero RGB/Mask/depth shared-parameter gradients',
            current_task_new_candidate_executed=False),
        beta=dict(initial_mm=.08,official_beta_min_network=.0001,parameter_init='0.08/mm_per_unit - 0.0001',learned=True),
        optimizer=dict(type='Adam',implicit_and_radiance_lr=.0001,density_beta_lr=.00001,betas=[.9,.999],weight_decay=0),
        ray_sampler=dict(type='finite fixed cells, explicit raw SDF, no absorption tail',cells_per_ray=128,
            official_adaptive_sampler='NOT_VALIDATED_NOT_CLAIMED',GPU_device_port='NOT_VALIDATED; requires newly authorized five-batch parity gate before updates'),
        batch=dict(all_references_per_step=3,per_view_region_quota=[32,24,16,16,8],rays_per_view=96,
            importance='region population / sampled N',eikonal_points=256),
        losses=dict(RGB=dict(weight=1.,Huber_delta=.05,scope='P_INTERIOR front hit'),
            depth=dict(weight=.1,Huber_delta_mm=.5,no_scale_shift=True,missing_depth='NaN'),
            Mask=dict(weight=.1,type='log-optical BCE candidate; requires actual-parameter CPU gradient validation before adoption'),
            Eikonal=dict(weight=.1,type='official exact norm penalty')),
        arms=dict(E2P5_S0=dict(depth='native',Mask_weight=0,CAD_integral_cap=False,conflict_weight=.25),
            E2P5_S1=dict(depth='native',Mask_weight=.1,CAD_integral_cap=True,conflict_weight=.25),
            E2P5_S2='NOT_RUN_DUPLICATE_EXISTING_D0_D1_WEIGHT_POLICY; no distinct new reliability scheme certified',
            E2P5_S3='CANCELLED_D2_PHYSICAL_BIAS_NOT_IDENTIFIED'),
        common_policy='frozen source qualification already uses Mask/ROI/CAD; no arm claims segmentation-free or zero prior CAD knowledge; source correlation normalization common',
        budget=dict(max_steps_per_run=1000,max_minutes_per_run=30,max_GPU_allocated_GiB=5.,concurrent_runs=1,planned_runs=4,
            fixed_eval_step='final1000 only; failed runs keep NaN; no best-target checkpoint selection'),
        stop_rules=['any nonfinite loss/gradient','any source has no front hits','source hit coverage<50% or drops>10 percentage points for3 consecutive fixed probes',
            'camera/native data changes','VRAM>5GiB or time>30min','negative/unknown supervision enters loss','CAD penetration fraction>1% beyond0.1mm on supported surface'],
        evaluation=dict(target_identities=str(E2/'provenance/EVALUATION_IDENTITIES_FROZEN.json'),strict_holdout_N=0,
            source_probe_every_steps=25,metrics=['visible Mask IoU/boundary F1 + full denominators','A→B source-RGB error/coverage/spill',
            'supported visible surface fraction, CONFLICT/PRIOR_ONLY/UNKNOWN','fixed CAD consistency/penetration (not independent accuracy)',
            'physical-group independent coverage, MedARE/MAE/p95/max/paired common-success N'],
            GT='sealed; absolute error NaN until independent evaluation is valid',historical_baselines=['Raw','Cleaned','F1','F2','F3'],
            MapAnything='independent route, frozen E2 M0–M4; never SDF initializer'),
        launch_blockers=['two tested initializations fail005 three-reference depth/RGB','current clamp/density tail has zero recovery gradient',
            'partial-coverage objective loophole','new calibrated init and stable Mask must pass separately bounded CPU gate',
            'GPU adapter/sampler parity not validated','researcher acceptance of strict holdout0 and camera/HERO uncertainty','new explicit GPU grant'])
    save('config/GPU_MVP_PROPOSED.json',cfg)
    write('docs/GPU_MVP_PREREGISTRATION.md','''# GPU MVP完整配置建议（未运行，当前禁止启动）

机器可读配置：config/GPU_MVP_PROPOSED.json。不是已批准的训练任务，GPU NOT_AUTHORIZED。本轮真实三参考门槛在005失败，不能以“网络已能前反向”替代门槛。

## 范围与模型

004 ref03/ref08/ref13、005 raw00057/raw00459/raw00745；各自一个共享场、独立坐标系，不跨视频配准。官方plain MLP：8×256，feature256，位置编码6，skip4；颜色网络2×256，方向编码4，无per-image code。官方revision12513009。固定Ring、相机、原生HERO、来源DAG和资格。

## 可执行的初始化和beta定义，但尚须通过CPU门槛

当前A/B均不能让005三参考产生深度/RGB梯度，本任务已达到最多两候选上限，不新增第三候选。下一项有限CPU门槛可预注册**同一个几何壳校准规则**：源ROI中心/尺度不变，目标壳半径0.5×ROI半径；seed20261031；128个Fibonacci壳点。先用相同种子bias0的官方raw head求壳点输出中位数b，再以相同种子和bias=b构造初始化。只依赖预先固定源几何和网络初始化，不用GT、目标帧或源误差挑参数。此规则是未来提议，本轮未执行、未验证，不声称已得到可训练初始化。

beta初值0.08mm；官方beta_min=0.0001网络单位；参数初值=0.08/s−0.0001。004的s=34.02703180767122、005的s=28.3780268204276 mm/unit，对应物理beta_min约0.003403/0.002838mm。beta、SDF和射线距离必须同时转换。不得把旧0.1001网络单位当成0.1001mm。

校准后必须在相同三参考固定探针上满足每源观测前表面命中率≥50%、RGB/Mask/Depth对共享真实参数有有限非零梯度；门槛失败保留失败，不继续训练。稳定log-optical BCE只做候选数学评估，需真实参数梯度验证后才可采纳。GPU设备移植和有限128单元采样需新授权后先做5批无更新CPU/GPU一致性检查；官方自适应sampler未通过，不冒称已接入。当前代码是CPU诊断器，不能将其直接当已验证GPU训练器启动。

## 固定训练配置建议

- Adam；隐式场/颜色lr=1e−4，beta lr=1e−5；betas(0.9,0.999)，weight_decay0；单一种子20261031。
- 每步三个参考联合，分别96射线，五类配额32/24/16/16/8，按区域总体/采样数做重要性修正；每射线128有限单元，另256个共享Eikonal点。
- RGB权重1，Huber δ0.05，仅P_INTERIOR/front-hit；深度权重0.1、Huber δ0.5mm，不做scale/shift；Mask0.1、Eikonal0.1。所有未命中深度保留NaN，逐源完整观测分母和覆盖固定打印。
- 每视频/每arm最多1000步、30分钟、显存5GiB，单任务串行，首轮S0/S1共4个预注册run；只评价固定最终步，失败保留NaN，不挑最漂亮/目标误差最小的中间模型。

## Arm命名和因果边界

E2P5_S0：原生HERO+RGB+Eikonal，无显式Mask BCE，保留用户D0要求的现有冲突1/0.25、相关来源归一和稳健Huber；S1：S0增加有限Mask及Ring积分截断。S1一次加入Mask和Ring，不能分开归因二者贡献。公共数据资格已用Mask/ROI/CAD，S0不称完全无分割/无CAD信息。此命名仅属E2.5，保留原RA/E2 S0–S4历史命名，不覆盖。

用户D0已经要求现有稳健权重，D1初始版本也是1/0.25及相关分量归一，因此当前D0/D1在该政策上重合。不能再次将S2“新增相同不确定性权重”作为有效科学消融：S2标NOT_RUN_DUPLICATE_POLICY，等待有独立依据的新可靠性因素；本轮不虚构该因素。未来如需量化旧权重收益，可另立全1权重的负控制U0，但不得把它替换为用户指定的正式D0基线。

D0是深度身份不变，D1是监督权重政策，二者不是两套独立深度真值。D2物理偏移不可辨识，首轮S3取消。MapAnything继续独立M0–M4，不运行本轮推理、不用于SDF初始化；共同几何载荷与最佳合法输入对照分开报告，披露RGB/分辨率/置信差异。

## 停机和评价

任一NaN/Inf、任一参考零命中、固定探针命中率<50%或连续3次下降超过10个百分点即停；这些计数只作停机门槛，不是可微损失。相机/原生数据改变、显存/时间越界、未知区误监督也停。支持面上超过0.1mm的CAD穿插比例>1%停；CAD输入后的CAD误差只证明自洽。

每25步固定源探针，完整报告hit/observed、逐项梯度、区域分母。评价目标身份沿用E2：004诊断帧、005仅重建留出，严格全流程留出0，不用目标选步/选参。报告可见Mask/边界、真实A→B RGB误差与覆盖/溢出、支持面/冲突/未知比例、CAD关系；背面标PRIOR_ONLY/UNKNOWN。与Raw/Cleaned/F1/F2/F3在共同成功组配对，披露历史融合；物理独立分母G01=1，绝对MedARE/MAE/p95/max当前NaN，GT封存且部署位姿未认证。

启动仍需：新的初始化/稳定损失CPU门槛、GPU设备与采样一致性门槛、研究者接受非严格留出和来源相关性边界、明确GPU授权。本文件已给出具体模型、数值、预算和停止规则，但不掩盖当前方案尚未具备直接启动科学训练的条件。
''')

def main():
    mvp();pair=rows('HERO_PAIRWISE_DEPTH_CONFLICTS.csv');rr=rows('RING_DEPTH_RESIDUALS.csv');init=rows('NEURAL_INITIALIZATION_AND_HITS.csv');gg=rows('NEURAL_PER_REFERENCE_GRADIENTS.csv')
    bias=rows('DEPTH_BIAS_DIAGNOSTICS.csv');des=rows('BIAS_DESIGN_IDENTIFIABILITY.csv');runs=load(R/'metrics/OFFICIAL_SDF_CPU_RUNS.json');deg=load(R/'metrics/DEGENERACY_EXPLICIT_CONCLUSION.json')
    loose=[x for x in pair if x['region']=='ALL' and x['tier']=='LOOSE_PROJECTIVE_CANDIDATE'];conditional=[x for x in pair if x['region']=='ALL' and x['tier']=='CONDITIONAL_CYCLE_NORMAL']
    reliable=[x for x in rr if x['tier']=='RING_INTERIOR_INCIDENCE'];numerical=rows('STABLE_MASK_NUMERICAL_CHECKS.csv')
    summary='本轮先完成真实多参考深度与环诊断，再实例化冻结官方网络，未重跑旧审计或扩大解析球实验。六参考中四个呈方向稳定的偏移迹象，但相机、对应及材质误差仍不可分离，不建议直接校正原生深度。真实网络检查采用两项预注册初始化：004旧配置三参考均产生联合梯度，物理尺度候选缺一参考；005两配置均无合格前表面命中，三参考门槛失败。退化反例显示覆盖由全体降至三分之一时，深度和联合损失反而下降；空场中的密度尾部抵消及掩膜截断还会切断恢复梯度。已保留失败、给出稳定计算候选和四张证据图，但未更新任何参数、未训练、未运行图形处理器。下一阶段配置已具体化，仍因初始化、损失和设备接线门槛未齐而禁止启动。'
    gate_rows=[['DEPTH_CONSISTENCY','PASS_CONDITIONAL_DIAGNOSTICS','12方向、双资格层；不证明物理对应或真实深度精度'],
        ['RING_DEPTH_DIAGNOSTIC','EVALUABLE_ALL_6_SOURCES','原生Ring独立资格、无残差筛选'],
        ['BIAS_IDENTIFIABILITY','NOT_IDENTIFIED_PHYSICALLY','4个条件性稳定方向，设计秩3仍不能分离相机/材质/对应误差'],
        ['OFFICIAL_SDF_CPU','PASS_ACTUAL_CPU_FORWARD_BACKWARD','真实官方670395参数；固定有限采样，官方adaptive未通过'],
        ['THREE_REFERENCE_GRADIENT','PARTIAL / FAIL_FOR_TWO_VIDEO_SCOPE','004/A通过；004/B缺ref13；005/A、B均失败'],
        ['MISS_DEGENERACY','RISK_IDENTIFIED_NOT_ELIMINATED','partial命中仍可降低目标；all-miss gate不足以消除风险'],
        ['GPU_MVP_READINESS','NOT_READY / NOT_AUTHORIZED','新初始化/稳定loss真实参数/设备采样门槛及授权仍缺']]
    actual_p1=md(['A→B','源合格N','loose N','loose signed/abs median mm','MAD / p95abs mm','conditional N'],[
        [x['A']+'→'+x['B'],x['source_eligible_N'],x['N'],f"{float(x['median_signed']):.3f} / {float(x['median_abs']):.3f}",f"{float(x['MAD']):.3f} / {float(x['p95_abs']):.3f}",next(y['N'] for y in conditional if y['A']==x['A'] and y['B']==x['B'])] for x in loose])
    ring_table=md(['参考','可靠N/源Ring Mask','signed median mm','MAD mm','p95abs mm'],[[x['source'],x['N']+'/'+x['Ring_Mask_N'],f"{float(x['median_signed']):.4f}",f"{float(x['MAD']):.4f}",f"{float(x['p95_abs']):.4f}"] for x in reliable])
    hit_table=md(['视频/候选','参考','输入/正Mask/合格HERO','观测hit/miss','raw SDF范围mm','beta mm'],[[x['scene']+'/'+x['candidate'][0],x['source'],x['ray_N']+'/'+x['positive_Mask_N']+'/'+x['qualified_HERO_N'],x['observed_hit_N']+'/'+x['observed_miss_N'],f"{float(x['raw_SDF_min_mm']):.3f}..{float(x['raw_SDF_max_mm']):.3f}",f"{float(x['beta_mm']):.4f}"] for x in init])
    gradient_table=md(['004/A真实参数梯度','ref03','ref08','ref13'],[[term,*[next(x['gradient_norm'] for x in gg if x['scene']=='G01_004' and x['candidate']=='A_LEGACY_INIT_CONTROL' and x['source']==ref and x['loss']==term) for ref in selected()['G01_004']]] for term in ['rgb','mask','depth']])
    def fmt(x):return 'NaN' if not x else f"{float(x):.6g}"
    per_ref=[]
    for r in init:
        terms={x['loss']:x for x in gg if x['source']==r['source'] and x['candidate']==r['candidate']}
        per_ref.append([r['source']+'/'+r['candidate'][0],*[fmt(terms[k]['value']) for k in ['rgb','mask','depth']],
            ' / '.join(fmt(terms[k]['gradient_norm']) for k in ['rgb','mask','depth'])])
    per_ref_table=md(['参考/候选','RGB Loss','Mask Loss','Depth Loss','真实梯度范数 RGB/Mask/Depth'],per_ref)
    report=f'''# TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001 技术报告

{summary}

## 1. 当前结论与七项门槛

{md(['Gate','状态','解释'],gate_rows)}

本轮目标是诊断和真实CPU接线，不是恢复高精度模型。关键结论：HERO有系统性排序迹象，也有局部/对应/遮挡冲突，不能简单将其全归为可校正常数；真实MonoSDF已能接收共享多源梯度，但**尚未在两视频都达到完整三参考联合监督条件**。正式训练禁止启动。

## 2. 授权、版本与完整分母

用户请求逐字保存在[任务附件](inputs/USER_TASK.md)。新授权仅放宽真实官方网络的CPU构造、极小前向和autograd；GPU、优化器更新、正式训练、Map推理仍禁止。上一轮E2 continuation父提交`c530fcb375d3412d49a6f2ce0346af6aa4def74a`保持原样，本轮独立分支`exp/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001`。P1提交`42f99cd`；P2提交`0199bee`；报告提交由包含本文件的最终Git commit标识。

MonoSDF官方revision `12513009cd20a08b35ddc2c55a7e42da2c7baf43`，真实类`model.network.MonoSDFNetwork`。旧E1/E2代码、来源DAG、native HERO、Mask、K/c2w、ROI与CAD直接只读复用，不重跑其审计。004=`ref03/ref08/ref13`、005=`raw00057/raw00459/raw00745`，两个局部坐标系严格隔离。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 物理G01共1组；2视频、6输入参考；12有向比较不是12独立样本 |
| 本算法独立成功 | 新测量0/1；实际CPU神经诊断覆盖2/2视频、4个唯一场景×候选配置；非正式重建成功 |
| 本算法失败 | 新测量NOT_RUN/NaN；真实接线：004/B缺ref13深度命中、005/A与B全缺深度命中 |
| 历史测量值回退 | 0；不使用S0/V2旧测量、旧照片直径或其他路线补齐 |
| 失败组及具体原因 | G01两视频详细原因见[失败记录](FAILURE_LEDGER.md)、初始化命中表及图3/4；005为实测初始化失败，不删除或改采样 |
| 最终统计样本 | 测量N=0、总分母1；独立覆盖率0/1；MedARE/MAE/p95/max均NaN，共同成功配对N=0 |
| 是否使用GT选择算法 | 否；未读GT、Dxy或目标评价帧；阈值、像素和两个初始化候选先冻结，无第三候选搜索 |

原始4个网络各670,395参数；修复候选诊断数值bug时额外构造了2个**完全同种子、同参数SHA**的B复核实例：总实例6，唯一配置仍4、初始化候选仍2。模型所有学习参数前后SHA一致，OPTIMIZER_STEP0。没有保存或下载模型checkpoint，未复制视频/权重，未删除旧产物。[冻结配置](config/PREREGISTERED.json)、[实际网络配置](config/ACTUAL_OFFICIAL_NEURAL_CANDIDATES.json)、[复核SHA](provenance/IDENTICAL_NETWORK_DIAGNOSTIC_REPLAY.json)。

## 3. P1：正确的跨视角残差及未认证对应

将A原生axial Z反投影到固定世界坐标，再投影B，计算`e=Z_A→B−Z_B(round(u_B))`，从不减相同像素索引的两图Z。使用原生最近像素，不插值深度；原相机回投影闭环误差见[闭环表](metrics/DEPTH_PROJECTION_CLOSURE.csv)。

源资格为正Polyp Mask、有限正HERO、原有限ROI/CAD前缀，保留边界用于诊断；B需合法投影、同物体身份、有效原生深度及自身可见资格。排除已知CAD遮挡和投影A点自身Z-buffer后的明显后层。原生深度前后顺序冲突不按残差大小直接删除，而标记对应歧义。

保留两个层级：LOOSE_PROJECTIVE_CANDIDATE记录所有条件投影候选，不能称物理正确对应；CONDITIONAL_CYCLE_NORMAL另外要求回投影循环误差≤2px、两侧源法向有效且点积≥0.2。循环/法向也来自相同HERO，可能偏向一致像素，不是独立认证，**不以更小误差的子集宣称深度变好**。无法认证的候选保留，资格流与未认证数量逐方向公开。

{actual_p1}

有向反向结果单列，不当独立样本。完整[分区残差CSV](metrics/HERO_PAIRWISE_DEPTH_CONFLICTS.csv)共120行，包含ALL/主体代理/内边界2px/环邻近8px/掠视法向代理；优先级先冻结，不按误差重划区域。输出N、覆盖、signed median、MAD、median abs、p90/p95、正负比例及连续冲突区域数/最大像素面积。mm²为源HERO像素投影足印，**不是实际表面积**。[资格流分母](metrics/PAIRWISE_QUALIFICATION_FLOW.csv)。

![真实跨视角深度与未认证对应](figures/Fig1_depth_conflicts.png)

B是另一个输入参考而非目标评价帧。本轮没有打开任何已冻结评价目标像素。图的深度为mm，残差色标±2mm作显示截幅，统计保留全值。

## 4. P1-B/C：Ring证据和偏移可辨识性

Ring使用**独立原生Ring深度集合**。源Ring Mask内缩1px、CAD命中内缩1px、入射绝对余弦≥0.2；排除Polyp身份和无CAD对应。没有沿用E2 M3的“与CAD小残差才合格”过滤，避免循环筛选偏差；没有从Polyp或插值构造Ring观测。另公开未内缩的交集诊断层，避免边界尾部被隐藏。

{ring_table}

![Ring原始深度/固定CAD/残差](figures/Fig2_ring_depth_residuals.png)

四个参考对其他两参考有稳定残差方向，标为POSSIBLE_REFERENCE_BIAS；其余NO_STABLE_REFERENCE_BIAS只是该保守方向规则未满足，并非证明无系统误差。[逐源偏移诊断](metrics/DEPTH_BIAS_DIAGNOSTICS.csv)。Ring残差004约0.766/1.133/0.822mm、005约0.088/0.168/0.523mm，材料/反光/边界/相机仍可能贡献；其中004 ref08超出预注册±1mm偏移范围，**未clip成合法值**。

线性化模型`e_AB≈k_AB*b_A−b_B`的设计矩阵两视频数值秩均3，条件数约{float(des[0]['condition_number']):.2f}/{float(des[1]['condition_number']):.2f}；这仅在固定相机、固定像素对应下的代数可辨识性，不解决相机误差和深度偏移的物理混淆。未拟合深度校正参数。[可辨识性表](metrics/BIAS_DESIGN_IDENTIFIABILITY.csv)。

Ring棋盘半区的中位数仅用于固定对应的有界线性反事实检查，不实际修改或重投影校正深度。12方向中8个在±1mm范围内，其中5个中位绝对残差降低，其他并不统一；不能作为新精度。Ring到Polyp材料误差迁移未认证。[反事实表](metrics/RING_BIAS_EXPLANATION_COUNTERFACTUAL.csv)。

明确决定：首轮保持D0原生HERO和D1既有1/0.25冲突权重及相关分量归一。D2物理证据不足，不纳入首轮MVP；未来如有独立相机/材料证据，才考虑单独有界常数偏移，不拟合自由scale+shift、不逐像素修正。[五问完整决定](docs/DEPTH_CORRECTION_DECISION.md)。

## 5. P2：真实官方网络、有限采样和真实参数梯度

实际导入冻结`model.network`并构造完整`MonoSDFNetwork`，使用官方plain MLP分支（8×256、PE6、feature256、skip4；颜色2×256、方向PE4）。没有自造网络。CPU构造时只将官方bg_color和beta_min两处`.cuda()`张量分配局部转到CPU；其余CUDA调用会抛错，官方源码没有写入修改。实际子模块和参数数目在[运行记录](metrics/OFFICIAL_SDF_CPU_RUNS.json)。

直接复用E2 `finite_joint_adapter.py`的raw head、有限单元、颜色、深度、Eikonal及联合损失。新薄构造器仅承接本轮真实网络CPU授权，使用`implicit_network.forward`，不调用吸收球`get_outputs/get_sdf_vals`或旧full-ray renderer。官方自适应sampler含CUDA/夹持访问，因此采用用户允许的 **FIXED_SAMPLER_DIAGNOSTIC_ONLY**：128有限单元，段内重新求raw SDF，段外/终端不吸收。不能说官方sampler已通过。

每参考从E2冻结320条batch内按seed固定选16条（6/3/3/3/1配额），补乘原batch区域数/子采样数做重要性修正。每视频48条、每参考6条合格原生HERO；没有依命中结果换像素。[六份像素冻结文件](provenance/G01_004_ref03_CPU_PIXEL_SELECTION.json)。候选A：旧bias0.6、beta0.1001网络单位；候选B：bias=0.5×源ROI半径/s、beta0.08mm。两者是复合初始化控制，不冒充单因素科学消融。相同seed、两候选在预测前冻结，之后不增第三候选。

{hit_table}

004/A的三个参考RGB、Mask、Depth均对同一组真实参数有非零梯度，联合梯度范数约24.332；共享Eikonal梯度约10.259。Eikonal只作为一个场正则，不伪造三个来源。实际每源值及梯度全部见[逐源Loss和梯度](metrics/NEURAL_PER_REFERENCE_GRADIENTS.csv)。

{gradient_table}

每个参考、两个候选的实际损失及梯度如下；NaN表示该项没有合法前表面回归，0表示计算图实测零梯度：

{per_ref_table}

004/A三个参考隐式参数的RGB梯度两两余弦0.706–0.767，Mask0.862–0.918，Depth0.815–0.948，联合数据项0.887–0.959。这只是初始同向约束，不证明真实几何准确或HERO冲突已消失。[全部方向关系](metrics/NEURAL_GRADIENT_DIRECTIONS.csv)。

004/B的HERO命中分别2/6、1/6、0/6，ref13虽然其他类别有一个前交点，**不能冒充有效HERO命中**。005/A采样raw SDF全负，前表面位于所监督段之外或无该段前交点；005/B采样raw全正、opacity0，RGB/Depth无有效回归。不能把解析球初始化近似当实际神经几何，也不能根据004成功给005切换其他候选。

![真实官方网络有限射线/初始化/退化](figures/Fig3_official_sdf_cpu.png)

![三参考真实共享神经参数梯度](figures/Fig4_three_reference_gradients.png)

这四张图均未展示训练重建。P2原始四模型耗时约0.7–3.7秒/模型（不含所有后续诊断复核），阶段RSS约1.2–2.4GiB；环境未阻碍真实CPU执行，GPU未初始化。没有optimizer、学习率步骤、checkpoint读写或任何网络参数更新。

## 6. 漏命中退化：明确存在潜在风险

保持原18条真实HERO观测，004/A选择敏感性反例仅将高误差命中从回归选择里移除，不改变源观测和Mask opacity。它是**离散的loss选择反例，不是声称某个真实连续场已经产生了该轨迹**；离散计数没有伪造梯度。

| 条件 | 命中/固定观测 | Depth hit均值 | 联合目标 | 判读 |
| --- | --- | --- | --- | --- |
| 正常 | 18/18 | 2.087327 | 0.689999 | 三源均有效 |
| 部分缺失 | 15/18 | 1.480642 | 0.652145 | 现joint仍可接受部分覆盖 |
| 大量缺失 | 6/18 | 0.902485 | 0.595167 | 覆盖降至1/3，目标更小 |
| 全缺失 | 0/18 | NaN | NaN/REJECTED | 严格缺源门槛阻止通过 |

RGB也按保留命中子集重新算，未固定成有利值；完整[选择反例](metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv)。把已命中误差之和除以固定观测权重，同样会因为缺失项未贡献误差而降低，不能单独当解决方案；必须连同`C_hit=N_hit/N_observed`、各源miss及正可见性约束报告。

另在真实网络上对raw SDF施加预注册的连续输出偏移（0、0.15R、0.35R、1.2R、−1.2R），**不修改模型参数**，记录实际命中和dLoss/dOffset。005/B的0偏移本已0/18命中，当前Mask导数0；log-optical候选导数约3.55327，下降方向可降低正SDF偏移、扩张可见场。这是恢复梯度的诊断，不是已经训练恢复表面。[连续场诊断](metrics/DEGENERACY_TESTS.csv)。

还定位了两个数值原因：官方Laplace `0.5+0.5*expm1(−f/beta)`在正尾部抵消为0；005/B预选首射线的129个raw样本均出现“官方密度0但稳定表达式严格正”的情况。BCE再clamp到1e−8可继续截断梯度。[真实网络尾部检查](metrics/LAPLACE_TAIL_CANCELLATION.csv)。

稳定候选不添加命中计数loss，其数学仍为有限opacity BCE：`logτ=logsumexp(logσ+logΔ)`，正例`−log(1−exp(−τ))`，负例`τ`；正SDF的`logσ=−log(2β)−f/β`，负SDF为`−logβ+log(1−0.5exp(f/β))`。logτ<−20时log opacity近似logτ，误差界1.1e−9。真实未饱和射线上三次BCE等价检查最大误差{max(float(x['BCE_equivalence_abs_error']) for x in numerical):.3g}。仍需真实参数梯度、ROI起点已在内部时的反例及GPU数值一致性，**本轮未采纳为正式训练损失**。

该候选首版误用uint8 Mask取负，产生负BCE，已明确作废归档并改为浮点。仅重建两份同种子B网络复核，参数SHA与首次完全一致；旧网络Loss和初始化失败没有被替换成PASS。[失败原因](provenance/STABLE_MASK_ATTEMPT001_FAILURE.json)。

结论：**当前联合损失存在“降低覆盖换更低误差”的潜在退化，尚未排除。** all-miss门槛必要但不足；覆盖计数只作监控/停机，不能冒充可微训练约束。

## 7. 下一阶段配置与仍缺门槛

[完整GPU MVP预注册建议](docs/GPU_MVP_PREREGISTRATION.md)和[机器可读配置](config/GPU_MVP_PROPOSED.json)已经列明：官方结构、两个视频及三参考、固定源几何初始化壳校准规则、beta0.08mm、Adam1e−4/密度1e−5、RGB/Mask/Depth/Eikonal权重1/0.1/0.1/0.1、128单元、每源96射线、seed20261031、每run1000步/30分钟/5GiB、首轮四个预注册run及固定最终步评价。

E2.5_S0保留用户D0指定的原生HERO和当前1/0.25稳健权重；S1一起增加Mask+Ring（不能单独归因二者）。D0/D1当前定义已经共享相同不确定性政策，S2不能将相同权重重复包装成新消融，标NOT_RUN_DUPLICATE_POLICY；S3/D2取消。公共资格已使用Mask/ROI/CAD，S0不能称没有任何这类信息。此命名只属E2.5，不覆盖原E2/RA命名。MapAnything保持独立M0–M4，未推理、不用于初始化。

**配置是具体建议，但当前不能直接启动。** 005真实三参考门槛失败；已达本轮最多两个候选上限。下一项受控CPU门槛应在预测前冻结单一几何校准规则，验证每参考front-hit、Mask/RGB/Depth真实参数梯度，验证稳定loss的恢复方向。之后仍需新授权下无更新的GPU设备/采样一致性、研究者接受HERO相关性/相机/严格留出0的边界以及明确GPU训练授权。不能给失败初始化增加训练步数掩盖合同问题。

评价身份沿用E2，严格全流程holdout0。报告可见轮廓、源RGB真实A→B解释/覆盖/溢出、supported/conflict/prior/unknown面、CAD自洽/穿插；背面和体积不自动计真。历史Raw/Cleaned/F1/F2/F3只作明确对照，配对共同分母及历史融合标志必须公开。GT封存，部署位姿未认证，绝对3D精度当前NOT_EVALUABLE。

## 8. 交付、失败与复现

[完整失败记录](FAILURE_LEDGER.md)、[复现](REPRODUCE.md)、[复用来源](CODE_REUSE_E2P5.csv)、[环境](provenance/ENVIRONMENT.json)、[全部图浏览](visualizations/index.html)。大型原始资产仍在旧工作树；本任务只保存少量压缩二维诊断/射线trace，不生成大规模点云或模型权重。Git仅代码、指标、文档和四张精选PNG。

最终完整性核验见[DELIVERY_VALIDATION](metrics/DELIVERY_VALIDATION.json)，失败的研究门槛保持失败；完整性PASS不能转换为科学PASS。原生HERO、相机、CAD、P0、Dxy及所有旧工作树保护核对在交付清单中记录。

```text
MODEL_FORWARD: CPU_DIAGNOSTIC_ONLY
MODEL_TRAINING: NOT_RUN
OPTIMIZER_STEP: 0
GPU: NOT_AUTHORIZED
MAPANYTHING_FORWARD: NOT_RUN
NEW_RECONSTRUCTION_RESULT: NOT_CLAIMED
```
'''
    write('TECHNICAL_REPORT.md',report)
    write('FAILURE_LEDGER.md','''# E2.5失败、不可评价与协议修复

| ID | 对象/步骤 | 失败或限制 | 处理及证据 |
| --- | --- | --- | --- |
| F01 | 新工作树初始化 | Git继承稀疏检出却缺新info目录 | 仅修复新工作树管理目录，旧库未reset/清理；provenance/AUTHORIZATION.json |
| F02 | P1投影预览 | 同B像素多A点最后写入不是首交点显示 | 改为现成A投影Z-buffer，重算P1预览；统计资格/残差规则未变，runtime/P1_DEPTH.log及P1_DEPTH_FINAL.log |
| F03 | 真实对应/H1–H4 | 循环/法向来自HERO，无法认证同一物理点；严格子集可能偏向一致 | 同时公开loose与conditional全分母，未知保留；[图1](figures/Fig1_depth_conflicts.png)、[资格流](metrics/PAIRWISE_QUALIFICATION_FLOW.csv) |
| F04 | D2偏移识别 | 相机/对应/材质混杂；004ref08 Ring偏差超±1mm界，物理偏移不可辨识 | 不clip、不拟合校正、不写HERO；[偏移决定](docs/DEPTH_CORRECTION_DECISION.md)、[图2](figures/Fig2_ring_depth_residuals.png) |
| F05 | 004/B ref13 | 合格HERO0/6命中；其他类别1命中不能补齐 | joint保持FAIL，不更换像素/候选；[初始化表](metrics/NEURAL_INITIALIZATION_AND_HITS.csv)、[图4](figures/Fig4_three_reference_gradients.png) |
| F06 | 005/A三源 | 各0/6命中；采样raw全负，ROI可见段缺前交点 | RGB/Depth保留NaN，三源FAIL；[真实梯度表](metrics/NEURAL_PER_REFERENCE_GRADIENTS.csv)、[图3](figures/Fig3_official_sdf_cpu.png) |
| F07 | 005/B三源 | 各0/6；采样raw全正、opacity0、当前Mask梯度0 | 识别官方密度正尾抵消及BCE clamp；不增第三候选、不训练；[尾部审计](metrics/LAPLACE_TAIL_CANCELLATION.csv)、[图3](figures/Fig3_official_sdf_cpu.png) |
| F08 | 漏命中loss退化 | 固定18观测下覆盖1→1/3，Depth2.087→0.902，joint0.690→0.595 | 明确判有潜在风险；离散选择不是梯度/真实场轨迹；all-miss拒绝不消除partial风险；[反例](metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv) |
| F09 | 稳定BCE首版 | uint8目标取负wrap255，错误负BCE；候选诊断无效 | 原输出及源码归档ATTEMPT001；浮点修复后只精确同种子重建两个B实例，参数SHA一致；[原因](provenance/STABLE_MASK_ATTEMPT001_FAILURE.json)、[复核](provenance/IDENTICAL_NETWORK_DIAGNOSTIC_REPLAY.json) |
| F10 | 选择反例控制 | B没有完整三参考命中，无法充当正常覆盖正控制 | 使用同一个既定legacy A作两个视频的诊断控制，非挑最好模型；005仍全未命中，不制造正常覆盖；实际连续偏移另列 |
| F11 | 官方sampler | CUDA分配及吸收夹持访问，未合法运行 | 仅FIXED_SAMPLER_DIAGNOSTIC_ONLY；两处CPU构造分配显式端口，GPU从未初始化，真实源码不改 |
| F12 | 数值审计辅助脚本 | source重复关键字导致首次解析失败 | 修复字段名为evidence后运行；不影响任何原始数据、主网络结果或科学阈值 |
| F13 | 新物理测量 | G01新重建/测量0/1，未正式训练；严格holdout0、绝对GT位姿未认证 | 误差NaN、历史回退0；没有把CPU模型/图像当高精度重建 |

本轮预注册两候选均保留；未删困难像素、未改变资格或阈值来制造PASS；失败研究Gate不因交付完整性通过而改变。旧资产未删除，HERO/相机/CAD/P0/Dxy未改，GT及目标像素未访问。
''')
    write('REPRODUCE.md','''# E2.5仅复现本轮P1/P2（不重跑旧审计）

父提交c530fcb，官方MonoSDF12513009。Python3.12、torch2.7.1+cu128但实际CPU；pyhocon/skimage复用E0已存在runtime/python，不安装/下载权重。原始资产LOCAL_ONLY，缺文件或SHA不同应停止，不换图/补旧结果。

```bash
set -euo pipefail
cd /home/liu/ring_first_3d_neural_e2p5/experiments/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
e25_python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
mkdir -p runtime
"$e25_python" code/preregister.py
"$e25_python" code/depth_consistency.py >runtime/REPRO_P1_DEPTH.log 2>&1
"$e25_python" code/ring_depth_audit.py >runtime/REPRO_P1_RING.log 2>&1
"$e25_python" code/bias_diagnostics.py >runtime/REPRO_P1_BIAS.log 2>&1
"$e25_python" code/official_sdf_cpu_adapter.py >runtime/REPRO_P2.log 2>&1
"$e25_python" code/neural_numerics_audit.py
"$e25_python" code/figures.py
"$e25_python" code/report.py
"$e25_python" code/validate_delivery.py
```

正常干净复现只构造4个唯一场景/候选网络。原交付另有2个相同参数的诊断bug复核，历史记录保留，不必重复该失败。test_miss_degeneracy.py的单独main用于按原SHA复核B，不是正式训练。

P1先完成才允许P2。P2真实参数SHA前后相同，GPU调用被拒绝，官方构造两处CUDA张量仅局部转CPU。固定16源射线/128单元，不执行官方自适应sampler、Map推理、优化器、训练或参数更新。研究门槛失败是有效输出；脚本完成不能解释成三参考/重建PASS。

当前单次网络RSS约1.2–2.4GiB，只有二维诊断/少量射线trace；不复制原视频或大权重，不删除旧实验。local_results/runtime不进Git。报告/manifest时间戳会变化，复现前保留当前Git提交。
''')
    write('RESULT_INDEX.md','''# E2.5交付索引

- [唯一完整报告](TECHNICAL_REPORT.md)、[失败记录](FAILURE_LEDGER.md)、[复现](REPRODUCE.md)。
- [四张核心图浏览](visualizations/index.html)。
- [深度处理决定](docs/DEPTH_CORRECTION_DECISION.md)：首轮原生HERO+稳健权重，D2不建议。
- [具体GPU MVP建议](docs/GPU_MVP_PREREGISTRATION.md)、[机器可读配置](config/GPU_MVP_PROPOSED.json)：BLOCKED/NOT_AUTHORIZED。
- [跨视角残差](metrics/HERO_PAIRWISE_DEPTH_CONFLICTS.csv)、[Ring残差](metrics/RING_DEPTH_RESIDUALS.csv)、[偏移诊断](metrics/DEPTH_BIAS_DIAGNOSTICS.csv)。
- [真实官方CPU Gate](metrics/OFFICIAL_SDF_CPU_GATE.json)：CPU计算通过，三参考范围失败；[完整逐源梯度](metrics/NEURAL_PER_REFERENCE_GRADIENTS.csv)。
- [退化反例](metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv)、[明确结论](metrics/DEGENERACY_EXPLICIT_CONCLUSION.json)。
- [交付完整性](metrics/DELIVERY_VALIDATION.json)、[SHA清单](provenance/DELIVERY_MANIFEST.json)、[增量上传](provenance/GIT_SYNC_STAGE12.json)。最终HEAD远端回执在runtime/FINAL_GIT_SYNC.json，避免自引用。

MODEL_FORWARD CPU_DIAGNOSTIC_ONLY；TRAINING NOT_RUN；OPTIMIZER_STEP0；GPU NOT_AUTHORIZED；MAPANYTHING NOT_RUN；NEW_RECONSTRUCTION NOT_CLAIMED。
''')
    save('metrics/GATE_SUMMARY.json',dict(gates=[dict(Gate=x[0],status=x[1],reason=x[2]) for x in gate_rows],
        physical_group_N=1,video_N=2,reference_N=6,CPU_unique_scene_candidate_N=4,total_CPU_instantiations_including_exact_replay=6,
        new_measurement_success_N=0,measurement_error_metrics=None,paired_common_success_N=0,historical_measurement_fallback_N=0,
        official_model_training='NOT_RUN',optimizer_step_N=0,GPU='NOT_AUTHORIZED',MapAnything_forward_N=0,
        new_reconstruction_result='NOT_CLAIMED',formal_GPU_ready=False))
    reuse=[]
    for p,entry,mode in [(E1/'code/common.py','guard/protection/hash/io/ring','EXACT_AST_REUSE; only new-task neural-import grant changed'),
        (E2C/'code/opacity.py','finite density/Mask/depth loss','UNCHANGED_IMPORT'),
        (E2C/'code/finite_joint_adapter.py','FiniteJointAdapter raw/render/eikonal/joint_losses','UNCHANGED_INHERITED_METHODS; new authorized constructor'),
        (E2C/'code/continuation_context.py','source_packet','EXACT_AST_EXTRACTION'),
        (OLD/'ring_first_v1/scripts/common.py','unproject','EXACT_AST_REUSE'),
        (REPO/'visualization/real_p0_renderer.py','camera_rays/project_camera','UNCHANGED_IMPORT'),
        (REPO/'visualization/same_camera_scene.py','SameCameraScene','UNCHANGED_IMPORT'),
        (SDF/'code/model/network.py','MonoSDFNetwork/ImplicitNetwork/RenderingNetwork','REAL_OFFICIAL_IMPORT; CPU constructor tensor port only'),
        (SDF/'code/model/density.py','LaplaceDensity','REAL_OFFICIAL_PARAMETERS; beta_min CPU tensor port'),
        (SDF/'code/confs/dtu_mlp_3views.conf','model architecture','MLP_BRANCH; hash-grid-only kwargs removed')]:
        reuse.append(dict(path=str(p),entry=entry,mode=mode,SHA256=sha(p)))
    table('CODE_REUSE_E2P5.csv',reuse)
    save('provenance/ENVIRONMENT.json',dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
        numpy=np.__version__,official_source_revision=git(SDF,'rev-parse','HEAD'),runtime_python=str(E0/'runtime/python'),
        CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],CPU_threads=2,official_parameter_N=670395,optimizer_step_N=0,GPU='NOT_AUTHORIZED'))
    print('E2P5_REPORT_COMPLETE; failed scientific gates retained; MVP proposed but blocked')

if __name__=='__main__':main()
