"""Visualize new CPU evidence and update the single E2 technical report."""
from continuation_context import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import html


def readrows(name):return list(csv.DictReader((CROOT/name).open()))
def md(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
        ['| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in rows])


def figures():
    losses=readrows('metrics/JOINT_LOSS_GRADIENTS.csv');gate=load(CROOT/'metrics/JOINT_WIRING_GATE.json')
    conflict=readrows('metrics/HERO_CONFLICT_CATEGORIES.csv');evidence=readrows('metrics/SOURCE_EVIDENCE_DENOMINATORS.csv')
    names=['rgb','mask','depth','eikonal'];fig,axs=plt.subplots(1,2,figsize=(14,6))
    for j,scene in enumerate(selected()):
        lookup={r['loss']:r for r in losses if r['scene']==scene}
        axs[0].bar(np.arange(4)+(j-.5)*.32,[float(lookup[k]['geometry_gradient_norm']) for k in names],.3,label=scene)
    axs[0].set(xticks=np.arange(4),xticklabels=names,yscale='log',ylabel='analytic geometry gradient norm',title='All four losses reach the same per-video geometry')
    axs[0].legend();axs[0].grid(axis='y',alpha=.2)
    labels=[];hits=[];misses=[]
    for scene in gate['scenes']:
        for ref,c in scene['counts'].items():
            labels.append(ref.replace('G01_',''));hits.append(c['valid_N']);misses.append(c['miss_N'])
    axs[1].bar(np.arange(6),hits,color='#2d8a5c',label='front-hit depth / RGB')
    axs[1].bar(np.arange(6),misses,bottom=hits,color='#d98d37',label='miss: NaN depth, positive Mask retained')
    axs[1].set(xticks=np.arange(6),xticklabels=labels,ylabel='qualified source depth samples',title='Observed572 = front hits408 + misses164')
    axs[1].tick_params(axis='x',rotation=35);axs[1].legend(fontsize=8)
    fig.suptitle('E2 continuation | raw-head + finite cells + RGB / Mask / HERO / Eikonal CPU graph',fontsize=13)
    fig.text(.04,.07,'Mask gradient: autograd3.6098133068 / finite difference3.6098132052\nRGB gradient: autograd-0.0335857256 / finite difference-0.0335857236',fontsize=9)
    fig.text(.54,.07,f"{gate['check_N']} new wiring checks | frozen actual cameras | analytic geometry/radiance only\nPhysical beta0.08mm is a control, not an official training configuration",fontsize=9)
    fig.text(.5,.015,'NO OFFICIAL NEURAL FORWARD / NO WEIGHT UPDATE / GPU NOT GRANTED / NOT MODEL ACCURACY',ha='center',color='firebrick',fontsize=10)
    fig.tight_layout(rect=(0,.17,1,.94));p=CROOT/'figures/Fig5_joint_loss_CPU.png';fig.savefig(p,dpi=145);plt.close(fig)
    fig,axs=plt.subplots(2,4,figsize=(17,8));C={x['id']:x for x in registry()['references']}
    for row,(scene,refs) in enumerate(selected().items()):
        for col,ref in enumerate(refs):
            z=np.load(BASE/f'local_results/rays/{ref}.npz');p=np.load(R/f'local_results/continuation_cpu/{ref}_COMMON_HERO.npz')
            rgb=np.asarray(Image.open(C[ref]['RGB']).convert('RGB')).copy();labels=z['labels'].reshape(360,640)
            # Show black fixed CAD only at observed Ring pixels, never paint over Polyp.
            ring_pixels=np.isfinite(z['ring_first_t_mm']).reshape(360,640)&(labels==2)
            rgb[ring_pixels]=[12,12,12]
            ax=axs[row,col];ax.imshow(rgb)
            cat=p['HERO_conflict_category'];bad=cat=='BEHIND_FIRST_RING_HIT';margin=cat=='RING_FRONT_MARGIN'
            if bad.any():ax.contour(bad.astype(float),levels=[.5],colors=['red'],linewidths=.6)
            if margin.any():
                y,x=np.where(margin);ax.scatter(x,y,s=10,marker='x',c='orange')
            rec=next(x for x in conflict if x['source']==ref)
            ax.set_title(ref+'\n'+rec['BEHIND_FIRST_RING_HIT']+' behind Ring + '+rec['RING_FRONT_MARGIN']+' margin',fontsize=9)
            ax.axis('off')
        records=[x for x in evidence if x['scene']==scene];keys=['single_view_no_comparison_N','co_visible_agree_all_N','co_visible_some_conflict_N','co_visible_all_compared_conflict_N']
        colors=['#477bba','#2d8a5c','#d8aa43','#bb534c'];bottom=np.zeros(3)
        for key,color in zip(keys,colors):
            vals=np.array([int(x[key]) for x in records]);axs[row,3].barh(np.arange(3),vals,left=bottom,color=color,label=key.replace('_N','').replace('co_visible_',''))
            bottom+=vals
        axs[row,3].set(yticks=np.arange(3),yticklabels=['refA','refB','refC'],xlabel='full qualified source observations',title=scene+' source evidence')
        axs[row,3].legend(fontsize=6,loc='best')
    fig.suptitle('Actual source RGB + fixed black CAD | red: HERO behind Ring; orange:0.05mm front margin\nEvery marked pixel keeps positive Mask; only contradictory HERO depth rejected',fontsize=12)
    fig.text(.03,.06,'2759 behind first Ring hit +4 front-margin conflicts =2763 | unresolved0\n5457 single-view-only depth observations retain weight1; per-video HERO component count1',fontsize=10)
    fig.text(.52,.06,'SDF / Map common geometry payload:86789 identical source-qualified HERO pixels\nRGB encoding/resolution and source-weight handling differ; full information equivalence is NOT claimed',fontsize=10)
    fig.text(.5,.015,'SOURCE OBSERVATIONS / CONDITIONAL DIAGNOSTICS — NO NEW RECONSTRUCTION — GPU NOT GRANTED',ha='center',color='firebrick',fontsize=10)
    fig.tight_layout(rect=(0,.15,1,.91));p=CROOT/'figures/Fig6_source_conflicts_common_HERO.png';fig.savefig(p,dpi=145);plt.close(fig)
    csave('provenance/FIGURES.json',dict(figures=[asset(p) for p in sorted((CROOT/'figures').glob('*.png'))],
        source_rendering='unchanged frozen camera/ray/CAD machinery; actual source RGB only; no target image access',GPU='NOT_GRANTED'))
    entries=[('../figures/'+p.name,p.name) for p in sorted((CROOT/'figures').glob('*.png'))]
    entries +=[('../../figures/'+p.name,'Previous E2: '+p.name) for p in sorted((R/'figures').glob('*.png'))]
    (CROOT/'visualizations/index.html').write_text('<!doctype html><meta charset="utf-8"><title>E2 CPU continuation</title><style>body{font:16px sans-serif;max-width:1400px;margin:2em auto}img{width:100%}h1{font-size:24px}</style><h1>E2 CPU continuation — GPU NOT GRANTED</h1><p>Analytic wiring and source input contracts; no new neural reconstruction.</p>'+''.join('<h2>'+html.escape(t)+'</h2><img src="'+html.escape(p)+'">' for p,t in entries))


def reports():
    gate=load(CROOT/'metrics/JOINT_WIRING_GATE.json');inp=load(CROOT/'metrics/CONTINUATION_INPUT_GATE.json')
    losses=readrows('metrics/JOINT_LOSS_GRADIENTS.csv');conf=readrows('metrics/HERO_CONFLICT_CATEGORIES.csv');ev=readrows('metrics/SOURCE_EVIDENCE_DENOMINATORS.csv')
    section=f'''## 9. 本轮继续执行：联合损失接线与共同几何输入（2026-10-31）

用户明确要求按同一RA指导继续上一轮；本轮只推进既有授权下可完成的CPU工程。基于上一轮最终提交`5d4bcbbee444d8db9a479ed256417fb7cfd9a83b`建立分支`exp/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001-cpu-continuation`，旧E2工作树和结果保持原样。前述第1–8节是第一轮已交付证据；本节补充当前实现状态，不重跑E1审计或上一轮275项阶段测试。

新增结果：联合损失/接口CPU检查 **{gate['check_N']}项通过**；冲突分类和共同几何输入 **{inp['check_N']}项通过**。这142项为本轮新增合同，不是新增科学样本。此前257项完整性核验属于上一轮记录。本轮独立保护/交付核验见[本轮完整性结果](continuation_cpu/metrics/FINAL_CONTINUATION_VALIDATION.json)。

### 9.1 已补齐的工程路径与验证边界

[薄adapter](code/finite_joint_adapter.py)实现了官方签名的raw implicit `forward(x_net)`、特征、raw SDF梯度、`RenderingNetwork.forward(points,normals,view_dirs,feature_vectors,indices)`调用协议，并将有限单元opacity、条件Polyp RGB、axial HERO深度和Eikonal接入同一损失图。所有积分重新求段内密度；不调用吸收球夹持的`get_outputs/get_sdf_vals`，不使用旧整射线权重或旧单目深度scale/shift拟合。Eikonal精确复用官方`MonoSDFLoss.get_eikonal_loss`函数AST。颜色只对P_INTERIOR且前表面命中的源像素监督，未知颜色/背景不交给Polyp外观场解释。

**真实官方网络和官方采样器均未构造或执行**；当前模块还显式拒绝来自`model`/`mapanything`的神经对象。测试替身是有明确解析公式的Sphere及颜色函数，非随机初始化神经网络。官方接口仅定向静态绑定，未重复E1来源审计。官方sampler含CUDA分配及夹持SDF访问，当前接口只接收已给定、单位明确的采样proposal并裁成有限单元；官方sampler运行与raw-SDF访问的真实改线仍需后续授权验证。

联合损失入口新增严格三参考门槛：任何源深度全部未命中会抛出带逐源观测/命中/缺失数的`IncompleteReferenceError`，不会将剩余两源均值冒充三源通过。逐射线未命中仍是NaN、不做零深度回归；正Mask保留。相机、视频身份及参考来源均检查，网络参数没有更新。

| 新增独立导数控制 | autograd | 有限差分 | 解释 |
| --- | --- | --- | --- |
| opacity对球半径 | 3.6098133068 | 3.6098132052 | 可见有限段，非吸收球终端 |
| RGB对球半径 | -0.0335857256 | -0.0335857236 | raw特征/法向/有限渲染的几何路径 |
| Eikonal | 0.0100000000 | 解析闭式(a−1)²，a=1.1 | 官方函数精确复用，几何振幅梯度0.2 |
| mm/network转换 | 差异2.22e−16 | 同一物理积分的两种单位 | beta和射线距离同时转换 |

几何梯度范数（参数块包含半径mm、Z偏移mm和无量纲场振幅；跨块数值不作为优化优劣比较）：

{md(['视频','损失','值（解析控制）','几何梯度范数','外观梯度范数'],[[r['scene'],r['loss'],f"{float(r['value']):.8g}",f"{float(r['geometry_gradient_norm']):.8g}",f"{float(r['radiance_gradient_norm']):.8g}"] for r in losses])}

![联合损失与解析命中分母](continuation_cpu/figures/Fig5_joint_loss_CPU.png)

合计572条合格深度观测、408条解析命中、164条未命中，沿用原冻结batch而非挑选有利像素。测试权重RGB=1、Mask=0.1、depth=0.1、Eikonal=0.1以及beta=0.08mm只为CPU图检查，**不是已批准的科学训练超参数**；官方物理beta、初始化、学习率/预算仍未冻结。没有损失下降曲线，因为没有优化步骤。

### 9.2 对2,763个HERO冲突的逐源归因

{md(['源','Ring后方','环前0.05mm裕量','ROI外/其他','保留正Mask/拒绝HERO'],[[r['source'],r['BEHIND_FIRST_RING_HIT'],r['RING_FRONT_MARGIN'],int(r['BEFORE_ROI_ENTRY'])+int(r['AFTER_ROI_EXIT'])+int(r['UNRESOLVED']),r['conflict_N']] for r in conf])}

总计 **2,759个在Ring首交点之后、4个在环前安全裕量内、0个未归因**。这是固定相机/CAD下的估计深度与可见性合同冲突，不能单凭这些数判断HERO、Mask或CAD谁是真实误差来源；未修改任何上游。所有冲突正Mask继续保留，原生深度未覆盖。[分类表](continuation_cpu/metrics/HERO_CONFLICT_CATEGORIES.csv)。

来源证据按有向共视比较进一步分为：无共视比较 **{sum(int(r['single_view_no_comparison_N']) for r in ev):,}**；所有已比较源一致 **{sum(int(r['co_visible_agree_all_N']) for r in ev):,}**；部分冲突 **{sum(int(r['co_visible_some_conflict_N']) for r in ev):,}**；所有已比较源均冲突 **{sum(int(r['co_visible_all_compared_conflict_N']) for r in ev):,}**。四类总和86,789，含单视角观测而不将其权重降为0。无比较仍为权重1；任一冲突固定0.25；每视频一个相关分量、每源1/3，政策未改变。[完整来源分母](continuation_cpu/metrics/SOURCE_EVIDENCE_DENOMINATORS.csv)。

![逐源可见性冲突和共同HERO输入资格](continuation_cpu/figures/Fig6_source_conflicts_common_HERO.png)

### 9.3 共同几何载荷补齐，但不夸大公平性

新增每视频一个`COMMON_QUALIFIED_HERO_GEOMETRY`配置：Map和SDF在源分辨率使用**完全相同的86,789个合格原生HERO像素**；Map之外的像素深度0，不增加CAD Ring深度条件，不混入派生F1/F2/F3。六源公制Z一致、K/pose不变、官方三视图预处理及未知0编码已检查。[数据Manifest](continuation_cpu/provenance/COMMON_HERO_GEOMETRY_MANIFEST.json)。

必须披露：①共同像素资格已利用Mask/ROI/Ring可见性，两路线都不是“从未使用分割或CAD”；②Map原生使用完整RGB并resize到280×154，SDF仅在源640×360的合格P_INTERIOR采样颜色；③SDF可对深度施加冻结冲突权重，Map白名单不接受任意confidence。故本轮只证明**源几何载荷匹配**，没有声称两种模型的编码、像素分辨率、置信权重或计算预算完全等价。

上一轮RA M0–M4的16个配置、30个派生深度和祖先身份保持冻结；这两个新配置是共同几何信息层的补充，不重新编号或替代M0–M4。S0/S1/S2/S3正式消融launcher尚未实现；当前联合损失为完整合同。未来比较S1−S0、S2−S1时须冻结相同资格和采样重要性；若公共资格本身已用CAD，S2边际只能解释为“增加显式积分截断”的作用，不能声称此前完全未用CAD。

### 9.4 当前门槛判断及固定审计表

| 审计项目 | 本轮继续执行后的状态 |
| --- | --- |
| 目标组数 | 仍为物理G01共1组，2视频、6参考；无扩组 |
| 本算法独立成功 | 0/1新测量；解析图和合法输入不计模型预测 |
| 本算法失败 | 1/1未产生测量，NOT_RUN，Dxy及精度NaN；两个视频的解析miss不冒充模型实测失败 |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | G01两视频官方神经执行/科学配置未运行；164个解析深度miss保留；冲突逐源证据见本节及[失败记录](FAILURE_LEDGER.md) |
| 最终统计样本 | 新测量N=0，总分母1；MedARE/MAE/p95/max均NaN，共同成功配对N=0 |
| 是否使用GT选择算法 | 否，未打开GT、Dxy或目标像素；未按组误差选择算法、参数或先验 |

**C2a/C2b新增CPU工程通过；正式GPU科学实验仍NOT_READY，GPU NOT_GRANTED。** 相比上一轮，已补齐raw/radiance/四损失的可执行解析计算图、严格缺源拒绝、逐源冲突归因和共同深度载荷。仍缺：官方真实网络及sampler的有界运行验证；物理beta/初始化及各消融配置冻结；真实不透明BG认证或明确不确定性政策；严格独立留出（当前0）与条件相机/HERO相关性边界的研究者接受；分辨率/颜色/置信使用差异下的评价设计和资源预算；新的明确GPU授权。本轮不据CPU梯度存在宣称重建正确或科学门槛已自动通过。
'''
    original=(BASE/'TECHNICAL_REPORT.md').read_text()
    old=original.split('\n\n')[1]
    summary='本轮在上一轮冻结交付上继续补齐工程，未重复旧审计。新增有限单元与原始几何输出、颜色及四项联合损失接口，使用解析替身验证共享几何梯度、有限差分和三参考缺源拒绝；完成72项接线检查及70项输入检查。对全部可见性冲突逐源归因：2,759个深度在固定环首交点后，4个在安全裕量内，正掩膜全部保留；5,457个缺少共视比较的观测保持原权重。新增两视频共同深度输入，与息肉场资格像素逐一一致，同时披露颜色编码和置信权重差异。官方神经网络及采样器未执行，测量输出仍为零，误差保持缺失。正式科学实验还需真实运行验证、物理参数和评价配置冻结及独立数据边界审阅；图形处理器授权仍未授予。'
    (R/'TECHNICAL_REPORT.md').write_text(original.replace(old,summary,1).rstrip()+'\n\n'+section)
    failure=(BASE/'FAILURE_LEDGER.md').read_text()
    failure+='''
## 本轮CPU继续执行补充

| ID | 状态 | 原因及处理 | 证据 |
| --- | --- | --- | --- |
| C01 | 工作树创建行政错误，已修复 | 新worktree已注册但Git继承稀疏检出缺少自身info目录；仅补建新worktree管理目录，未reset旧库。首次日志重定向前runtime目录未创建，补目录后执行；非数值PASS或科学失败 | [冻结事件](continuation_cpu/provenance/AUTHORIZATION_AND_FREEZE.json) |
| C02 | 官方神经/sampler NOT_RUN | raw/radiance调用协议和解析四损失图已实现；sampler含CUDA分配和夹持SDF访问，官方模块执行仍被拒绝，不用解析替身冒称官方网络已测 | [API绑定](continuation_cpu/provenance/OFFICIAL_API_BINDING.json)、[72项接线](continuation_cpu/metrics/JOINT_WIRING_GATE.json) |
| C03 | 三参考全miss的单源，EXPECTED_REJECT | 负控制明确移除一源全部命中，新联合入口抛出IncompleteReferenceError并保留逐源观测/缺失分母，不重归一其余两源来制造通过 | [测试表](continuation_cpu/metrics/JOINT_WIRING_TESTS.csv) |
| C04 | HERO可见性冲突未消除 | 2759在Ring后，4在0.05mm安全裕量，全部保留正Mask/拒绝深度；没有调整阈值、相机或CAD | [逐源分类](continuation_cpu/metrics/HERO_CONFLICT_CATEGORIES.csv)、[图6](continuation_cpu/figures/Fig6_source_conflicts_common_HERO.png) |
| C05 | 解析深度miss164，NaN | 572观测/408命中，未作优化；不代表正式MonoSDF结果 | [梯度和分母表](continuation_cpu/metrics/JOINT_LOSS_GRADIENTS.csv)、[图5](continuation_cpu/figures/Fig5_joint_loss_CPU.png) |
| C06 | 信息匹配只到几何载荷，OPEN | 两路线合格HERO像素相同，但RGB编码/分辨率/置信使用不同；公共资格本身已用Mask/CAD，不得称S0无任何CAD信息 | [共同数据Manifest](continuation_cpu/provenance/COMMON_HERO_GEOMETRY_MANIFEST.json) |
| C07 | G01新测量0/1，NOT_RUN | 正式网络/初始化/科学预算未执行；严格留出0和真实BG网格认证缺口仍在，GT与历史测量均未读取 | [最新报告第9节](TECHNICAL_REPORT.md#9-本轮继续执行联合损失接线与共同几何输入2026-10-31) |
| C08 | 本地日志清单回读失败，已修复 | 首次validator清单记录了自身仍在写入的日志，结束后该日志SHA变化；保留预期/实际SHA，改为排除活动日志、结束后由Git交付回执单独核验，不改科学阈值或输入 | [失败SHA回执](continuation_cpu/provenance/LOCAL_LOG_RECEIPT_FAILURE.json) |

新数值合同检查72+70项均通过；没有通过改容差或删源像素制造PASS。行政错误、预期拒绝、解析未命中、未执行的神经模型分别记录。
'''
    (R/'FAILURE_LEDGER.md').write_text(failure)
    (CROOT/'README.md').write_text('''# E2 CPU继续执行交付

唯一完整实验报告为[主技术报告第9节](../TECHNICAL_REPORT.md)。本目录保存本轮新增72项联合接线与70项输入合同、两张核心图、来源分类和Manifest；不替代上一轮冻结结果。

- [图浏览：新增2张+原4张](visualizations/index.html)
- [四项损失梯度](metrics/JOINT_LOSS_GRADIENTS.csv)、[接线门槛](metrics/JOINT_WIRING_GATE.json)
- [HERO冲突类别](metrics/HERO_CONFLICT_CATEGORIES.csv)、[完整源证据分母](metrics/SOURCE_EVIDENCE_DENOMINATORS.csv)
- [共同HERO几何Manifest](provenance/COMMON_HERO_GEOMETRY_MANIFEST.json)
- [新完整性核验](metrics/FINAL_CONTINUATION_VALIDATION.json)、[交付清单](provenance/CONTINUATION_MANIFEST.json)

GPU NOT_GRANTED；官方网络/采样器执行0；训练/更新0；新物理测量0/1，误差NaN。
''')
    (R/'REPRODUCE.md').write_text('''# 本轮E2继续执行：仅复现新增CPU工程

保留上一轮commit5d4bcbb；不重新初始化、重跑E1审计或重复上一轮275项阶段测试。上一轮完整复现说明仍在该提交。新工作树读取旧E2的冻结batch/射线/深度资格，只读SHA核验实际复用文件。

```bash
set -euo pipefail
cd /home/liu/ring_first_3d_neural_e2_cpu/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
e2_python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
mkdir -p runtime
"$e2_python" code/continuation_tests.py >runtime/CONTINUATION_WIRING_REPRODUCE.log 2>&1
"$e2_python" code/continuation_inputs.py >runtime/CONTINUATION_INPUT_REPRODUCE.log 2>&1
"$e2_python" code/continuation_deliver.py
"$e2_python" code/continuation_validate.py
```

仅解析Sphere/颜色函数与官方安全数学/输入工具执行。禁止调用官方神经网络、sampler或optimizer；官方模块注入会被拒绝。所有测试阈值和测试权重先冻结，无模型参数更新。实际GPU科学运行不在本复现命令中。

资产必须来自原E2工作树及已审计旧路径，缺文件或SHA变化会报错。local_results/continuation_cpu与runtime为本地持久数据，Git忽略。先保留当前提交，复现会更新本任务时间戳/报告/Manifest。
''')
    (R/'RESULT_INDEX.md').write_text('''# E2当前交付索引

- [单份完整技术报告](TECHNICAL_REPORT.md)：第1–8节为原冻结交付，第9节为本轮CPU继续执行。
- [新增证据索引](continuation_cpu/README.md)、[六张核心图浏览](continuation_cpu/visualizations/index.html)。
- [最新失败记录](FAILURE_LEDGER.md)、[仅新增CPU复现](REPRODUCE.md)。
- 本轮新增：联合接线72项、输入合同70项；[完整性核验](continuation_cpu/metrics/FINAL_CONTINUATION_VALIDATION.json)。原275项阶段检查和257项完整性记录保留，未重跑。
- [共同HERO几何Manifest](continuation_cpu/provenance/COMMON_HERO_GEOMETRY_MANIFEST.json)、[本轮交付Manifest](continuation_cpu/provenance/CONTINUATION_MANIFEST.json)。原Map M0–M4的16配置和30派生深度未改变。
- [GPU门槛](continuation_cpu/metrics/GPU_READINESS.json)：NOT_READY / NOT_GRANTED。官方神经模型/采样器执行0、更新0、新测量0/1、误差NaN。
- 原冻结分支exp/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001保持5d4bcbb；本轮独立续作分支exp/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001-cpu-continuation。远端回执在本地runtime/CONTINUATION_FINAL_GIT_SYNC.json。
''')
    csave('metrics/GPU_READINESS.json',dict(C2a='CPU_PASS_WITH_LIMITATIONS',C2b='CPU_PASS_WITH_LIMITATIONS',
        completed_now=['thin raw/radiance finite-cell bridge','joint RGB/Mask/HERO/Eikonal analytic gradients','strict all-reference loss gate','2763 visibility conflicts classified','2 equal-qualified-HERO geometry profiles'],
        official_neural_runtime_verified=False,official_sampler_execution_N=0,GPU='NOT_GRANTED',formal_GPU_ready=False,
        remaining=['official neural/sampler bounded runtime wiring validation','physical beta/initialization/ablation launcher scientific configuration freeze',
            'real opaque BG certification or accepted uncertainty policy','strict holdout0/conditional cameras/shared HERO dependence review',
            'RGB resolution/encoding/confidence differences and resource budgets preregistration','separate explicit GPU grant'],
        independent_measurement_success_N=0,target_group_N=1,error_metrics=None))
    print('CONTINUATION_REPORT_AND_FIGURES_COMPLETE')


if __name__=='__main__':figures();reports()
