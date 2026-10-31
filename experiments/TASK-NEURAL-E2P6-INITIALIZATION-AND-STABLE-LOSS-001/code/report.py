"""Report the bounded experiment without converting finite gradients into readiness."""
from common import *
import platform,importlib.metadata

def rows(name):return list(csv.DictReader((R/name).open()))
def write(name,s):(R/name).write_text(s.strip()+'\n')
def md(headers,rr):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rr])
def val(x):return 'NaN' if x in ['',None] else f'{float(x):.6g}'

def main():
    init=rows('INITIALIZATION_VALIDATION.csv');stable=rows('STABLE_MASK_GRADIENT_TESTS.csv');neural=rows('metrics/PER_REFERENCE_NEURAL_SUPERVISION.csv');detail=rows('metrics/PER_REFERENCE_LOSSES_AND_GRADIENTS.csv')
    anchor=rows('metrics/WEAK_HERO_ANCHOR_GRADIENTS.csv');zero=rows('metrics/ZERO_LEVEL_VS_OPACITY.csv');cal=load(R/'config/SHELL_CALIBRATION_FROZEN.json')
    precision=rows('metrics/PROBE_GEOMETRY_PRECISION.csv');math=rows('metrics/MATH_TARGET_EQUIVALENCE.csv');coverage=load(R/'metrics/COVERAGE_GATE.json')
    integrity=load(R/'metrics/FINAL_INTEGRITY.json') if (R/'metrics/FINAL_INTEGRITY.json').exists() else None
    integrity_text=f"本次记录为{integrity['passed_N']}/{integrity['check_N']}项完整性检查通过，状态`{integrity['status']}`。" if integrity else '最终记录以`metrics/FINAL_INTEGRITY.json`为准。'
    summary='本轮仅执行一个预先冻结的几何壳校准规则，并在真实官方神经网络上验证稳定掩膜损失、弱表面锚点及固定分母覆盖门槛。校准后，005三个参考均有真实前表面命中及颜色、深度、掩膜参数梯度；004的ref13旧固定小批量仍仅命中2/6，未达到50%，尽管额外固定射线通过，也不改判。稳定损失的60项检查均有限，但全负场仍缺有效几何梯度；弱锚点仅证明一阶方向，未证明有效表面已恢复。三种损失均保留降低覆盖换取较低误差的风险，新增评价会拒绝这种退化。本轮未读取真值、未改上游、未更新学习参数或启动GPU；两视频联合验收失败，停止初始化搜索，尚不具备正式科学训练条件。'
    assert 200<=len(summary)<=350,len(summary)
    hittable=md(['源参考','旧固定16射线：hit/合格HERO','不相交额外64：hit/合格HERO','两批RGB/Mask/Depth几何梯度','门槛'],[
        [ref,*[f"{next(x for x in neural if x['source']==ref and x['split']==sp)['front_hit_N']}/{next(x for x in neural if x['source']==ref and x['split']==sp)['observed_HERO_N']}" for sp in ['small','extra']],
         '均有限且非零','FAIL' if any(x['hit_gate']=='False' for x in neural if x['source']==ref) else 'PASS'] for rr in selected().values() for ref in rr])
    lossgrad=md(['参考/批','合格/命中/未命中','Mask / Depth / RGB Loss','隐式参数梯度 Mask / Depth / RGB','Ring采样数'],[
        [r['source']+'/'+r['split'],r['observed_HERO_N']+'/'+r['front_hit_N']+'/'+r['miss_N'],
         ' / '.join(val(r[k]) for k in ['stable_Mask_loss','Depth_loss','RGB_loss']),
         ' / '.join(val(r[k]) for k in ['Mask_geometry_gradient','Depth_geometry_gradient','RGB_geometry_gradient']),r['Ring_ray_N']] for r in neural])
    signs=md(['视频','校准bias（网络单位）','目标壳半径mm','中心SDF mm','壳中位数mm / abs-p95 mm','beta mm'],[
        [sc,f"{x['bias_network']:.15g}",f"{x['radius_mm']:.9g}",f"{x['signs']['center_SDF_mm']:.9g}",
         f"{x['signs']['shell_median_mm']:.3g} / {x['signs']['shell_abs_p95_mm']:.6g}",f"{x['beta_mm']:.9g}"] for sc,x in cal.items()])
    controls=md(['控制','稳定Loss及全部参数梯度有限','有效隐式+trunk梯度','旧BCE非有限损失数'],[
        [case,f"{sum(x['stable_loss_finite']=='True' and x['all_parameter_gradients_finite']=='True' for x in stable if x['case']==case)}/12",
         f"{sum(x['useful_geometry_gradient']=='True' for x in stable if x['case']==case)}/12",sum(x['old_loss_finite']=='False' for x in stable if x['case']==case)]
         for case in cfg()['pathological_controls']])
    zeros=md(['同一神经控制场','固定合格HERO数','真实前交叉','高opacity>0.98','高opacity但无前交叉','前缀入口为负'],[
        [control,*[sum(int(x[k]) for x in zero if x['control']==control) for k in ['observed_N','front_cross_N','high_opacity_N','high_opacity_without_front_cross_N','observed_prefix_starts_inside_N']]] for control in ['NORMAL','POSITIVE','NEGATIVE']])
    report=f'''# TASK-NEURAL-E2P6-INITIALIZATION-AND-STABLE-LOSS-001 技术报告

{summary}

## 1. 验收结论

| 项目 | 结果 | 实际边界 |
| --- | --- | --- |
| P1 单一壳规则 | FAIL_STOP_INITIALIZATION_SEARCH | 两视频内外符号与物理beta检查通过；004/ref13 small=2/6失败，不再搜索 |
| P2 稳定Mask数值 | PASS_BOUNDED_NUMERICAL_TESTS | 60/60有限；48/48高精度目标对照；30/30 FP32/FP64损失及全参数梯度一致 |
| P3 无交点恢复 | PARTIAL / NOT_VALIDATED_AS_SURFACE_RECOVERY | 全正场有几何梯度；全负场稳定Mask无有效几何梯度；候选锚点96/96一阶方向，不是实际零交叉恢复 |
| P4 覆盖退化 | EVALUATION_REJECTS / OBJECTIVE_RISK_REMAINS | 三方案各7个低覆盖低损失反例；不能宣称损失已消除退化 |
| P5 三参考严格门槛 | FAIL_FIXED_SOURCE_GATE | 12个参考×批次均有三类真实梯度，004/ref13旧小批量未达50% |
| GPU MVP | NOT_READY / NOT_AUTHORIZED | 不冻结为已就绪方案，不启动GPU或训练 |

Q1：**严格意义未通过**。G01_005通过本轮两批三参考条件；G01_004虽六种参考/批次都有真实神经监督，ref13旧小批量仍失败。Q2：**尚不能证明可靠表面恢复**。稳定Mask修复正空场的数值梯度，不能修复所有负饱和场；弱HERO候选产生真实几何方向，但未发生参数更新或恢复后的前交点。Q3：**风险仍在，评价识别改善，目标免疫未证明**。[GPU门槛与三问](GPU_MVP_READINESS.md)、[失败记录](FAILURE_LEDGER.md)。

## 2. 授权、独立分支与固定审计表

本轮仅依据用户正式E2.6请求执行；旧文档是研究背景，未将其GPU建议或历史任务重新视为授权。独立分支`exp/{R.name}`，父提交`1eb9cc7fd49b70cf8370582dded7decb1d1cd4be`，工程/数值结果提交`261556d4c39923577d373197bccc2cdd952284ba`。最终报告版本由包含本文件的Git提交标识。继续同一研究上下文，未重新初始化项目、未重复E1/E2/E2.5审计。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 物理G01共1组；2独立视频、6源参考；不是6个独立息肉 |
| 本算法独立成功 | 新测量0/1（NOT_RUN）；CPU三参考严格门槛1/2视频，完整两视频任务失败；不是重建成功率 |
| 本算法失败 | 新测量NOT_RUN/NaN；G01_004/ref13 small 2/6失败；无前交点恢复与覆盖目标仍有门槛 |
| 历史测量值回退 | 0；不读取S0、历史V2、旧照片直径或其他路线预测补齐 |
| 失败组及具体原因 | G01：004/ref13固定批量覆盖不足；全负场无Mask几何恢复；详见[逐项失败与证据](FAILURE_LEDGER.md)、[图3](figures/Fig3_three_reference_neural_gate.png) |
| 最终统计样本 | 测量N=0/全分母1，独立测量覆盖率0/1；MedARE、MAE、p95、最大误差均NaN；共同成功配对N=0，无历史融合测量比较 |
| 是否使用GT选择算法 | 否；GT/Oracle、Dxy及目标评价帧未读；规则、来源像素和阈值均在新预测前冻结 |

GPU调用0、optimizer.step 0、学习参数更新0、MapAnything前向0、checkpoint IO 0。仅初始化构造器按预注册bias构造、相同初始化的控制场和精度副本；没有optimizer实例。模型SHA在各阶段结束后保持不变，详见`provenance/*MODEL_STATES.json`与`ZERO_LEVEL_CONTROL_STATES.json`。禁止将控制副本数称为初始化候选数：**规则始终只有1个**。

## 3. 最小复用与实际网络

官方`model.network.MonoSDFNetwork` revision `12513009cd20a08b35ddc2c55a7e42da2c7baf43`，不是解析球或自制网络。8×256隐式MLP、PE6、skip4、feature256；颜色2×256、方向PE4；共670,395个参数、37个参数张量，两个视频各用自己的共享神经场，未跨视频注册相机或混合监督。

E1的来源资格、E2的有限ROI/五类语义/固定CAD首交点/原生HERO/1或0.25冲突权重、E2.5的真实网络构造与神经梯度接线直接复用。E2有限renderer与有限单元权重以**原AST**执行；新薄适配仅将等价密度绑定改为稳定尾部计算。CPU构造器沿用E2.5对官方两处`.cuda()`常量分配的局部CPU转接（bg_color与beta_min），其余CUDA调用拒绝，本轮未写入官方源码。冻结本地官方副本包含早已审计的hashencoder惰性import改动：从模块顶层移至未使用的Grid构造器，避免plain MLP导入时编译CUDA；并非与upstream字节完全相同，MLP/密度逻辑不变，SHA与E2.5一致。官方adaptive sampler未验收；本轮仍为128个有限单元的CPU诊断器，不称正式GPU训练器。

`full_gradient`实际对所有37个可学习张量调用autograd，未使用项补零，形成670,395维梯度。分别记录implicit/trunk/head/radiance/beta，**非零beta不能冒充几何恢复**。一阶锚点方向还使用完整参数点Jacobian，不是对SDF输出附加标量偏移的证明。[复用函数和SHA](CODE_REUSE_E2P6.csv)、[环境](provenance/ENVIRONMENT.json)。

## 4. P1：唯一初始化规则、物理尺度与失败

规则在[预注册](config/PREREGISTERED.json)和[预测前冻结记录](provenance/BEFORE_CALIBRATION_AND_LOSS_TESTS.json)中先锁定：seed20261031，固定源ROI原点O、尺度s不变，目标壳半径0.5R；128个Fibonacci方向在壳上取点。先以bias0构造官方网络，求raw head壳输出中位数b，再以**相同种子**和bias=b重新构造；没有读取GT、评价目标、重建误差，也没有对不同视频分别搜索半径或参数。两视频b不同是同一规则与各自冻结源ROI的确定性结果。

坐标合同`x_net=(X_mm−O_mm)/s`、`f_mm=s*f_net`、`t_net=t_mm/s`、`beta_mm=s*beta_net`。004 s=34.02703180767122、R=22.466304910342206mm；005 s=28.3780268204276、R=10.27908157050465mm。两原点与E1 ROI中心相同，保持原Ring-First相机。beta初值0.08mm；官方beta_min=0.0001网络单位，对应0.003402703/0.002837803mm下限，不误当0.0001mm。

{signs}

中心为负；128个0.25R点负比例、R边界与1.25R点正比例均为1。壳中位数接近0，但abs-p95非零，**这不是完美球壳拟合**，也不是任意方向的全局符号证明。[完整校准与参数SHA](config/SHELL_CALIBRATION_FROZEN.json)。

![官方未训练raw SDF零水平集及前交点](figures/Fig1_initialization_zero_and_front.png)

图1为真实官方raw head的97×97 xz截面，不是合成球，不是三维重建。黑线为实际f=0，绿虚线为预先固定壳；右列每参考取既有small集合中首条合格HERO射线，实线校准后、虚线相同种子旧B，圆点为128单元采样检测的首次正→负交叉线性插值。射线选择未看预测，图中的未命中保留。

### 固定样本与每源50%门槛

small沿用E2.5每源16射线、五类配额6/3/3/3/1（每源6条合格HERO）。extra在预测前按源分区固定随机种子抽64条、配额32/12/10/6/4，**排除全部旧16像素**；004/ref03 extra只有31条合格HERO，其余每源32，未补抽不利像素。extra总384射线、191条合格HERO；small总96射线、36条合格HERO；两批合计480射线、227条合格观测。源/像素身份及packet SHA见[冻结来源](provenance/SOURCE_PROBES_FROZEN.json)。区域总体/采样数作重要性修正，未使用神经输出筛选。

{hittable}

预注册要求每源在**small和extra均≥50%**，不是合并分母后掩盖失败。004/ref13 small 2/6=33.3%，extra22/32=68.75%；只能说明小样本对空间分布敏感，不能据此放宽门槛、删参考或换像素。[初始化CSV](INITIALIZATION_VALIDATION.csv)、[停止搜索门槛](metrics/INITIALIZATION_GATE.json)。此后所有网络调用均为相同校准值/固定病理控制的损失诊断，没有第二条初始化规则。

同一old small与历史A、B都比较：[历史固定覆盖](metrics/HISTORICAL_FIXED_COVERAGE.csv)。相对A，004三个源从6/6降到5/6、4/6、2/6，记**3项潜在失败**；相对B无下降。新规则同时改变了相对A的物理beta等因素，不能声称单因子因果比较；不能选择“004用旧A、005用新规则”制造统一方案通过。

## 5. P2：稳定Mask与数学目标

有限、可见ROI段内`τ=Σ_j σ(f_j,β)Δt_j`、`p=1−exp(−τ)`；同一Mask BCE为

`ℓ(y,τ)=(1−y)τ−y log(1−exp(−τ))`。

稳定实现直接计算Laplace `logσ`和`logτ=logsumexp(logσ+logΔt)`。f≥0时`logσ=−log(2β)−f/β`；f<0时`logσ=−logβ+log(1−0.5 exp(f/β))`。正标签在`logτ<−20`时以`log p≈logτ`避免下溢，误差上界约1.04e−9；其余使用`log(−expm1(−τ))`。负标签损失是τ。有限段、Mask身份、权重、CAD截断均不变，未加入整射线吸收尾或让未知区参与监督。

代数目标与**未截断的有限opacity BCE相同**；它不会与旧代码的数值clamp在饱和区给出相同数值或梯度。旧实现把p截在[1e−8,1−1e−8]，FP32上上界可能舍入为1，造成0×log0/非有限值；FP64饱和区虽有限，也会掩盖损失、截断梯度。移除这种数值截断是恢复原BCE，不是换监督目标。原密度正尾`1+expm1`抵消也会造成假空场，新log密度保留该尾。

{controls}

正常/全正/空正/全负/Ring前缀均使用实际G01 small射线、真实官方参数；病理场仅按预注册±2ROI/s改变初始化SDF head bias，用来控制输出符号，**随后计算完整神经梯度**，不是初始化搜索或单标量导数演示。FP32与FP64从相同官方构造参数转换；未修改网络以绕过失败。

[60项梯度CSV](STABLE_MASK_GRADIENT_TESTS.csv)：稳定损失和全梯度均有限，但全负的12项不具有效implicit/trunk梯度。旧BCE的13项非有限损失全部发生FP32（正常6、全负6、Ring1），保留空值/false，未改写为0。非有限旧基线不算通过。

[80位目标对照](metrics/MATH_TARGET_EQUIVALENCE.csv)：48个FP64同样本代表射线（每可用标签首条），最大绝对差{max(float(x['abs_error']) for x in math):.12g}；不是另造的解析球。[30项精度表](metrics/FP32_FP64_CONSISTENCY.csv)损失及完整梯度余弦/范数均达预注册容差。另在两批全部12项中专门比较implicit向量，避免beta主导余弦：[几何精度表](metrics/PROBE_GEOMETRY_PRECISION.csv)，12/12通过。零几何梯度的FP32/64一致**不算恢复通过**。

![数值和真实神经梯度](figures/Fig2_stable_mask_and_gradients.png)

## 6. P3：opacity不是表面；弱HERO候选的证据上限

有效前面定义沿有序有限段存在raw SDF正→负交叉（含入口到首单元），且opacity质量≥1e−4。反向负→正是出表面，不能代替前面。高opacity不是交叉证明，也不把ROI入口自动当外部。

{zeros}

227为同一2批合格观测总数，每控制独立复核同样像素。[零面/opacity对照](metrics/ZERO_LEVEL_VS_OPACITY.csv)：正常控制有4条正密度尾形成高opacity但无零交叉；全负227条均高opacity、入口负、没有前交叉。全正227条没有前交叉与高opacity。全负时Laplace密度接近1/β、对f的导数趋零，稳定Mask也无法靠消除数值clamp获得有效几何恢复。更改beta不等于重新构成内外正确表面。

因此按原冻结条件触发**唯一最小候选**Reliable-HERO Weak Surface Anchor：每源在合格原生HERO点`X=o+d*(Z/cos)`上，对`f_mm(X)`使用Huber δ=0.5mm，联合权重0.01；同源相关分量1/3、已冻结像素冲突1或0.25、区域重要性修正照旧。HERO点必须处在已有可见ROI/CAD前缀内，**不依赖预测命中**，不使用Ring后错误深度，不把HERO当精确GT，不改原始HERO、不拟合偏移/逐像素校正。

24项（6源×2符号控制×2精度）均有有限真实几何/trunk梯度，最小implicit范数{min(float(x['geometry_gradient_norm']) for x in anchor):.9g}，beta梯度为0。将同视频3源的完整锚点梯度均值乘0.01；对每源前4个冻结合格点计算完整参数Jacobian与负联合梯度内积，96/96满足`f*df/dε<0`。[锚点梯度](metrics/WEAK_HERO_ANCHOR_GRADIENTS.csv)、[实际全参数方向](metrics/WEAK_HERO_POINT_DIRECTIONS.csv)。这说明原本没交点时可以向几何提供有效方向，**不证明有限参数更新后会出现正确前交点**，也不证明跨视角冲突消失。未施加任何学习参数更新；候选未加入正式主线。

没有加入自由空间约束：源资格可证明到HERO点/CAD之前的可见性，但没有额外证据保证每个ROI入口必在息肉外。只令HERO点接近0也不能确定内外方向或排除伪面，所以Q2仍为NOT_VALIDATED_AS_SURFACE_RECOVERY。

## 7. P4：固定观测分母与覆盖反例

{lossgrad}

逐源持续记录有效HERO总数、前交点/未命中、三项损失、真正隐式参数梯度与Ring射线数；未命中depth保留NaN。原Mask与稳定Mask、候选锚点的逐项参数梯度对照见[全损失梯度CSV](metrics/PER_REFERENCE_LOSSES_AND_GRADIENTS.csv)，共享梯度关系见[方向表](metrics/SHARED_GRADIENT_DIRECTIONS.csv)。每视频同一个参数对象跨3参考和两批使用；联合数据梯度为实际源autograd向量的精确线性和，加一份共享Eikonal，不冒称离散命中计数的可微梯度。

[覆盖退化CSV](COVERAGE_DEGENERACY_VALIDATION.csv)共48行：2视频×2批×保留100%/75%/25%/0命中的4种选择干预×3种目标。保持实际raw SDF、opacity、Mask项和锚点不变，按深度残差移除较难的已命中项，检验hit-gated RGB/Depth平均项的选择漏洞。这是**明确标注的损失选择敏感性控制**，不是一次连续网络运动、不是新模型预测、更不是训练结果。

CURRENT、STABLE_MASK、STABLE_MASK_PLUS_WEAK_ANCHOR各7个反例（共21）出现固定观测覆盖下降且总loss更低。锚点对未命中仍有监督，但在这个选择干预中不变，故没有数学免疫；不能通过将其权重加入后总loss改变宣称覆盖已改善。所有覆盖下降均被新验收标POTENTIAL_FAILURE_COVERAGE_LOWER；全未命中Depth/RGB/total保留空值=NaN/NOT_EVALUABLE，未以0代替。计数只作记录和门槛，没有作为梯度。

**已解决的是评价漏报，未解决的是优化目标风险**。本轮没有实际训练，不能报告覆盖恢复/下降的训练轨迹。下一阶段仍需在有授权的有限验证中证明机制改善覆盖，当前不能宣布Q3通过。[机器结论](metrics/COVERAGE_GATE.json)。

## 8. P5：真实三参考完整验收和遮挡

![六参考、两批真实命中与参数梯度](figures/Fig3_three_reference_neural_gate.png)

每参考每批都有非零有限RGB、稳定Mask、Depth隐式梯度（12/12）；同视频仅一个共享SDF、跨视频独立。每源≥50%的前交点率只有11/12通过，004/ref13 small失败使完整门槛失败。[最终三参考JSON](THREE_REFERENCE_NEURAL_GATE.json)。extra不是完全独立测试集：它来自同六个训练源，只用于规模适中的可重复性检查，不冒充独立临床样本或留出评价。

![真实Ring遮挡和最终可见监督资格](figures/Fig4_ring_visible_supervision.png)

图4使用004/ref13与005/raw00745固定源数据。Ring只画源Ring轮廓，不把黑色CAD覆盖到可见Polyp。五类为P_INTERIOR/P_BOUNDARY/KNOWN_NEGATIVE/RING_OCCLUDED/UNKNOWN；蓝/绿为有限Mask与合格HERO的**数据监督资格**，不代表模型已命中或已重建。右列为固定采样Ring射线，积分段终点≤首次CAD命中−0.05mm。全部12个批次段查询均在已有有限范围内、在首Ring之前；后方无监督。额外[遮挡数量表](metrics/RING_OCCLUSION_COUNTS.csv)区分采样Ring类、所有CAD交点、实际可见Ring前缀及正Mask原生HERO位于CAD之后的排除数，不把样本中排除数为0误称全图无冲突。真实背景代理和资格继续沿用E2，只读且条件启用，没有新建背景预测或改CAD。遮挡顺序通过只能证明自洽，不能消除HERO/相机物理不确定性。

## 9. 失败、来源保护与可复现性

[失败记录](FAILURE_LEDGER.md)包括科学失败和实现事故：P2首跑使用不存在的torch.flatnonzero导致API失败，改为torch.nonzero后按同规则重跑；启动新worktree时仅修复新管理目录；start_sdf返回trace占位NaN曾被发现，按同一网络重放修复trace并断言opacity/交叉/门槛完全不变。原失败日志保留在本地ignored runtime，SHA纳入交付清单，不能将其当成功运行。

保护检查只核对本轮实际复用的来源文件/函数SHA与原工作树状态，不是重做E1/E2/E2.5大审计。Ring-First相机、HERO、CAD、P0、Dxy、原用户脏修改和历史实验保持原样；未清理或删除旧产物。所有新文件限本任务目录。[来源复用](provenance/REUSED_INPUTS.json)、[终态保护](provenance/PROTECTED_END.json)、[交付清单](provenance/DELIVERY_MANIFEST.json)。NPZ射线/中间trace及运行依赖仅留本地，不上传全量源资产、视频或权重。

严格全流程留出仍为0；沿用E2已冻结身份但本轮未开目标帧、不扩大数据审计。既有HERO相关性/冲突不能当独立GT；不批准参考级深度校正。绝对测量误差与历史融合配对均NOT_EVALUABLE/NaN，未生成预测直径。

[复现说明](REPRODUCE.md)、[完整产物索引](RESULT_INDEX.md)、[四图浏览](visualizations/index.html)。最终完整性检查只验证数据/代码/报告一致性，不重新执行神经实验；完整性通过不得掩盖科学门槛失败。{integrity_text}

## 10. GPU后续门槛

本轮**NOT_READY / NOT_AUTHORIZED**。缺少：不改旧固定门槛的两视频统一初始化通过证据；全负场实际有意义前表面的恢复证据与内外方向依据；对hit-gated选择漏洞有实测改善的可微机制；后续另行授权的设备/有限采样CPU-GPU一致性检查；对HERO不确定性与严格留出0的PM处理；新的明确GPU授权。不得通过反复改壳、增参数、删ref13或读GT填平这些缺口。

由于三问未同时通过，不将旧E2.5建议配置改标为已冻结可启动GPU MVP；只冻结本轮失败状态、来源、数值实现与候选证据，等待PM依据具体机制决定下一项有限任务。
'''
    write('TECHNICAL_REPORT.md',report)
    failures=[
        ('F01','科学门槛失败','G01_004/ref13 small','2/6=33.3% < 预注册50%；extra22/32不替代small','INITIALIZATION_VALIDATION.csv / THREE_REFERENCE_NEURAL_GATE.json / 图3','保留FAIL；单一校准停止，不删参考或换像素'),
        ('F02','潜在覆盖失败','G01_004全部3源','相对历史A从6/6分别降为5/6、4/6、2/6；对B无下降','metrics/HISTORICAL_FIXED_COVERAGE.csv / 图3','两种历史对照均列出；不跨视频切换候选制造PASS'),
        ('F03','恢复机制失败','全负控制、两视频/6源/2精度','Mask几何与trunk梯度12/12未达有效阈值；227/227高opacity但0前交叉','STABLE_MASK_GRADIENT_TESTS.csv / metrics/ZERO_LEVEL_VS_OPACITY.csv / 图2','不以beta梯度或高opacity判恢复；仅检查预批准弱锚点'),
        ('F04','旧实现数值失败','FP32 old BCE','13项损失非有限：正常6、全负6、Ring1；全正尾梯度也被旧算法截断','STABLE_MASK_GRADIENT_TESTS.csv / 图2','旧失败保留；稳定新项60/60有限、目标48/48对照'),
        ('F05','候选证据不足','Reliable-HERO weak anchor','24项真实几何梯度、96/96点方向通过；没有更新后前交叉或内外正确表面证据','metrics/WEAK_ANCHOR_GATE.json / metrics/WEAK_HERO_POINT_DIRECTIONS.csv','candidate_only；不加入正式主线；不假设ROI入口在外'),
        ('F06','优化目标风险未消除','三种loss×固定small/extra','各7个低覆盖低总loss选择反例；共21','COVERAGE_DEGENERACY_VALIDATION.csv / metrics/COVERAGE_GATE.json','新评价全部拒绝；不称目标已免疫或覆盖已改善'),
        ('F07','科学边界未改变','G01两视频','严格全流程留出0；HERO来源相关/冲突仍在；无GT评价','GPU_MVP_READINESS.md / E2冻结评价身份','不做参考级校正，不称独立精度/临床验证'),
        ('I01','已修复执行事故','P2第一次运行','torch.flatnonzero不存在；首跑退出非零','本地 runtime/STABLE_ATTEMPT001.log；最终 runtime/STABLE_FINAL.log','改为torch.nonzero(as_tuple=True)，同规则/像素/阈值重跑；首日志不删除'),
        ('I02','已修复trace错误','P1 start_sdf返回字段','此前trace占位NaN；实际前交叉计算已使用真实入口SDF','provenance/START_SDF_TRACE_CORRECTION.json','同一SHA网络重放修复trace；assert opacity/交叉完全不变，门槛不变'),
        ('I03','已修复环境事故','新worktree稀疏检出','git add-worktree时新admin info缺失造成sparse锁路径错误','provenance/AUTHORIZATION.json','只创建新worktree info并稀疏检出；不reset/clean任何旧目录'),
        ('I04','已修复交付脚本事故','来源manifest生成','dict重复传入role关键字，报告脚本首跑退出','本地 runtime/REPORT_ATTEMPT001.log / runtime/REPORT.log','删除重复关键字后仅重生成文档与来源SHA；不重跑神经实验')]
    write('FAILURE_LEDGER.md','# E2.6 失败记录\n\nGPU NOT_AUTHORIZED；未训练、未更新参数。科学门槛失败保持原判。空值代表NaN/NOT_EVALUABLE，不能用0替换。\n\n'+md(['编号','类别','对象','失败机制/事实','证据','处置'],failures)+'''

图证：[初始化](figures/Fig1_initialization_zero_and_front.png)、[数值/梯度](figures/Fig2_stable_mask_and_gradients.png)、[逐参考](figures/Fig3_three_reference_neural_gate.png)、[可见区域](figures/Fig4_ring_visible_supervision.png)。实现事故的失败日志仅本地保留并在DELIVERY_MANIFEST中记录SHA。完整实验统计与固定审计表见[唯一技术报告](TECHNICAL_REPORT.md)。
''')
    write('GPU_MVP_READINESS.md','''# E2.6 GPU MVP readiness

**NOT_READY / GPU NOT_AUTHORIZED。正式GPU方案未冻结为可执行；GPU、训练、optimizer.step均未运行。**

| 问题 | 判定 | 依据 |
| --- | --- | --- |
| Q1 两视频能否都有有效三参考真实神经监督？ | PARTIAL，严格门槛FAIL | 12个参考×批次都有真实有限非零RGB/Mask/Depth几何梯度；005两批通过，004/ref13旧固定small仅2/6，低于50%。不以extra22/32抵消失败。 |
| Q2 空场/无前面有可靠可微恢复机制？ | PARTIAL，一阶梯度通过但表面恢复NOT_VALIDATED | 稳定Mask在全正/空正有梯度；全负饱和无有效几何梯度。弱HERO候选24项梯度、96/96点微分方向正确，但未证明更新后恢复前交叉和正确内外。不能将高opacity或beta梯度当表面。 |
| Q3 覆盖下降降低误差的风险是否消除？ | NO；仅评价识别改善 | 当前/稳定/加锚点各7个低覆盖低损失反例。固定分母和拒绝覆盖下降的门槛有效，目标结构性风险仍在，未训练所以没有覆盖改善轨迹。 |

后续缺口是具体科学/工程门槛，不再授权本轮搜索：

1. 两视频统一初始化在原固定small及不相交extra上逐源通过，不删困难参考、不换有利像素、不按视频挑旧/新算法。本轮唯一规则已停止搜索。
2. 对负饱和/无前面给出可靠恢复到真实前交叉的证据；若用弱HERO，应验证内外方向和多源冲突，不把HERO点锚定当精确GT。自由空间需要独立可见性依据。
3. 在固定观测分母下证明可微机制有助于保持/恢复覆盖，并继续将任何降低覆盖的低误差结果记为潜在失败；离散命中数不能当训练梯度。
4. 若PM批准下一阶段，再另行授权CPU/GPU设备移植及有限采样一致性检查；当前官方adaptive sampler未经验证，不可直接调用启动。
5. PM处理严格全流程留出0、HERO相关性/冲突及相机尺度边界；保持GT封存，不批准参考级深度校正。
6. 必须取得新的明确GPU授权。旧E2.5配置仍只是被阻断的建议，不借本轮稳定数值通过自动转为训练许可。

本轮可冻结供审阅的是：同一种子官方模型、同一壳规则失败结果、log-optical BCE数值实现、固定样本/门槛、弱锚点候选的一阶证据与失败记录；不是“已就绪GPU MVP”。

[技术报告](TECHNICAL_REPORT.md) · [三参考机器门槛](THREE_REFERENCE_NEURAL_GATE.json) · [失败记录](FAILURE_LEDGER.md) · [覆盖门槛](metrics/COVERAGE_GATE.json)
''')
    write('REPRODUCE.md',f'''# E2.6 CPU复现

原始E1/E2/E2.5不重跑，只读复用。任务目录`{R}`；Python `{sys.executable}`（Python {platform.python_version()}）。已有E0官方代码/缓存依赖、源参考与固定NPZ必须存在；不下载权重，不运行Map/GPU。

所有命令在任务目录下运行；已有冻结结果应先保留，逐阶段执行并保留失败日志。校准只有1条规则；如失败，**停止初始化搜索**，后续命令仅复核同一模型/病理控制的损失诊断，不改参重搜。

```bash
export PYTHONDONTWRITEBYTECODE=1
PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PYTHON" code/preregister.py
"$PYTHON" code/calibrate.py
"$PYTHON" code/stable_test.py
"$PYTHON" code/weak_anchor_test.py
"$PYTHON" code/neural_gate.py
"$PYTHON" code/coverage.py
"$PYTHON" code/zero_level_controls.py
"$PYTHON" code/figures.py
"$PYTHON" code/report.py
"$PYTHON" code/validate.py
```

`weak_anchor_test.py`以稳定Mask全负失败为条件；只是候选，不执行参数步。`zero_level_controls.py`不是新增校准，按同参数SHA核对opacity与真实前交叉。原E2.6结果发生一次start_sdf trace修正，不变的科学判定由独立assert记录。

仅最终完整性复核可单独运行`code/validate.py`；不会构造神经网络。它检查冻结SHA、固定像素、原工作树、真实CPU输出记录和报告链接。预期完整性PASS_WITH_RESEARCH_GATES_FAILED，**研究门槛预期FAIL**，不得为得到PASS改阈值。

本地`local_results/`和`runtime/`不入Git；输入来源/最终NPZ与日志SHA在交付manifest中。PNG是未训练官方raw SDF或明确标注控制实验，不是训练后三维重建。环境和旧代码依赖见`provenance/ENVIRONMENT.json`及`CODE_REUSE_E2P6.csv`。
''')
    write('RESULT_INDEX.md','''# E2.6 交付索引

- [完整技术报告](TECHNICAL_REPORT.md)
- [失败记录](FAILURE_LEDGER.md)
- [初始化验证](INITIALIZATION_VALIDATION.csv)
- [稳定Mask全参数梯度60项](STABLE_MASK_GRADIENT_TESTS.csv)
- [覆盖退化48项](COVERAGE_DEGENERACY_VALIDATION.csv)
- [三参考真实神经门槛](THREE_REFERENCE_NEURAL_GATE.json)
- [GPU就绪判定](GPU_MVP_READINESS.md)
- [复现](REPRODUCE.md)、[复用代码SHA](CODE_REUSE_E2P6.csv)
- [图1：零面与交点](figures/Fig1_initialization_zero_and_front.png)
- [图2：稳定损失与梯度](figures/Fig2_stable_mask_and_gradients.png)
- [图3：六参考完整分母](figures/Fig3_three_reference_neural_gate.png)
- [图4：Ring可见监督区域](figures/Fig4_ring_visible_supervision.png)
- [本地四图页](visualizations/index.html)
- [最终完整性结果](metrics/FINAL_INTEGRITY.json)、[检查项](metrics/FINAL_INTEGRITY_CHECKS.csv)
- [交付manifest](provenance/DELIVERY_MANIFEST.json)、[来源SHA](provenance/REUSED_INPUTS.json)

GPU NOT_AUTHORIZED，完整科学门槛FAIL。所有对照仅评价/诊断，未参与新路线预测补齐；本轮没有预测直径或正式重建。
''')
    env=dict(Python=sys.version,executable=sys.executable,platform=platform.platform(),torch=torch.__version__,numpy=np.__version__,
        CPU_threads=torch.get_num_threads(),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],GPU_call_N=0,optimizer_step_N=0,
        packages={p:importlib.metadata.version(p) for p in ['matplotlib','Pillow','trimesh']},official_revision=git(SDF,'rev-parse','HEAD'),
        E0_runtime=str(E0/'runtime/python'),official_model='model.network.MonoSDFNetwork',parameter_N=670395,parameter_tensor_N=37,
        forbidden_IO='GT/Dxy/checkpoints/network denied by scoped Python audit hook; no GPU execution')
    env['official_preexisting_port']='hashencoder import moved into unused Grid constructor; SHA matches E2.5; no E2.6 source modification'
    save('provenance/ENVIRONMENT.json',env)
    reused=[]
    for path,entries in [(E1/'code/common.py',['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring','cad_scene']),
                         (E25/'code/common.py',['registry','selected','e2_asset','source','grid','official_method','import_exact','freeze'])]:
        tree=ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node,ast.FunctionDef)and node.name in entries:
                reused.append(dict(path=str(path),name=node.name,line=node.lineno,file_SHA256=sha(path),AST_SHA256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),reuse='exact helper AST; new scoped globals'))
    for path,cls,name in [(E2C/'code/finite_joint_adapter.py','FiniteJointAdapter','render'),(SDF/'code/model/network.py','MonoSDFNetwork','__init__')]:
        _,info=official_method(path,cls,name);reused.append(dict(path=str(path),name=cls+'.'+name,line=info['line'],file_SHA256=info['file_SHA256'],AST_SHA256=info['AST_SHA256'],reuse='exact; CPU constructor ports inherited E2.5 / stable density binding scoped'))
    for path in [E25/'code/official_sdf_cpu_adapter.py',E2C/'code/opacity.py',SDF/'code/model/density.py',SDF/'code/model/network.py',REPO/'visualization/real_p0_renderer.py']:
        reused.append(dict(path=str(path),name='module read-only',line=1,file_SHA256=sha(path),AST_SHA256='',reuse='source unchanged, no historical audit main executed'))
    table('CODE_REUSE_E2P6.csv',reused)
    inputs=[];ringcounts=[]
    for scene,refs in selected().items():
        for ref in refs:
            c,p,r=source(ref)
            for key in ['RGB','Mask','pack','camera_file']:
                x=c['files'][key];inputs.append(dict(source=ref,**asset(x['path'],key,expected=x['sha256'])))
            for x,role in [(c['E1_actual_native'],'native_HERO_readonly'),(c['Ring_CAD'],'fixed_CAD_readonly')]:
                inputs.append(dict(source=ref,**asset(x['path'],role,expected=x['sha256'])))
            for rel in ['local_results/rays/'+ref+'.npz','local_results/'+ref+'_depth_reliability.npz']:
                inputs.append(dict(source=ref,**asset(e2_asset(rel),'E2 certified cache')))
            for split in ['small','extra']:
                from stable_losses import packet
                b=packet(ref,split);cad=np.isfinite(b['Ring_t_mm']);obs=b['depth_weight']>0
                rawt=b['target_Z']/b['cosine'];behind=(b['mask_target']==1)&np.isfinite(rawt)&(rawt>0)&cad&(rawt>=b['Ring_t_mm']-.05)
                ringcounts.append(dict(scene=scene,source=ref,split=split,sampled_Ring_class_N=int((b['sampling_class']==3).sum()),
                    sampled_any_CAD_hit_N=int(cad.sum()),sampled_visible_Ring_prefix_N=int(((b['sampling_class']==3)&b['valid']&cad).sum()),
                    positive_Mask_native_HERO_at_or_behind_CAD_margin_N=int(behind.sum()),qualified_HERO_behind_CAD_N=int((behind&obs).sum()),
                    qualified_HERO_N=int(obs.sum()),counts_are_fixed_sample_not_whole_source=True))
    for path in [E1/'provenance/INPUT_ELIGIBILITY.json',E1/'provenance/G01_PROPOSED_INPUTS.json',E2/'config/SDF_INITIALIZATION_CANDIDATE.json',E2/'provenance/EVALUATION_IDENTITIES_FROZEN.json']:
        inputs.append(asset(path,'frozen metadata only; target images not opened'))
    save('provenance/REUSED_INPUTS.json',dict(files=inputs,new_audit=False,scope='hash check only actually reused six-source assets; no large data audit',upstream_readonly=True))
    table('metrics/RING_OCCLUSION_COUNTS.csv',ringcounts)
    save('metrics/TASK_FINAL_STATUS.json',dict(status='COMPLETED_BOUNDED_CPU_TASK_WITH_FAILED_RESEARCH_GATES',
        initialization_rule_N=1,more_search=False,strict_three_reference_gate=False,Q1='PARTIAL_STRICT_FAIL',Q2='PARTIAL_NOT_VERIFIED_AS_SURFACE_RECOVERY',
        Q3='RISK_REMAINS_EVALUATION_REJECTION_ADDED',GPU_MVP='NOT_READY',GPU='NOT_AUTHORIZED',optimizer_step_N=0,GT_opened=False,
        measurement_independent_success_N=0,measurement_target_group_N=1,measurement_errors=None))
    print('REPORTS_COMPLETE',len(summary),'summary characters; no readiness claim')

if __name__=='__main__':main()
