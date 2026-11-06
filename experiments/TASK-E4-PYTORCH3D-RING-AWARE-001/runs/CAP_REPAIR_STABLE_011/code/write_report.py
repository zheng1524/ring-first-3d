from common import *
import collections

def main():
 runs=load(R/'metrics/NINE_CASE_RESULTS.json');stages=load(R/'metrics/ALL_STAGE_WITH_BLENDER.json');inherit=load(R/'metrics/C_INHERITANCE.json');case=load(R/'config/CASE_LOCK.json');cfg=load(R/'config/PROTOCOL.json');initial=load(R/'metrics/INITIAL_COMPARISON.json');meta={x['name']:x for x in case};by={(x['case'],x['label']):x for x in stages if x['label']in['INITIAL','FINAL']};lines=[];physics=[];details=[]
 for x in runs:
  n=x['case'];i=by[n,'INITIAL'];f=by[n,'FINAL'];st=x['stages_accepted'];lines.append(f"| {n} {meta[n]['morphology']} | {x['outer_iterations']} / {x['accepted_optimizer_steps']} | {st['GLOBAL']} / {st['LOW']} / {st['DETAIL']} | {x['final_active_modes']} | {i['FIT_IoU']:.3f} → {f['FIT_IoU']:.3f} | {i['HOLDOUT_IoU']:.3f} → {f['HOLDOUT_IoU']:.3f} | {i['FIT_raw_fixed_depth_cost']:.3f} → {f['FIT_raw_fixed_depth_cost']:.3f} | {i['FIT_depth_coverage']:.3f} → {f['FIT_depth_coverage']:.3f} |")
  physics.append(f"| {n} | {f['material_vertex_displacement_mm']['maximum']:.4f} | {i['Ring_signed_sample_penetration_mm']:.6f} → {f['Ring_signed_sample_penetration_mm']:.6f} | {i['Blender_Ring_pairs_N']} → {f['Blender_Ring_pairs_N']} | {f['Blender_self_N']} | {f['below_estimated_base_vertex_N']} | {f['connected_components']} / {f['nonmanifold_edge_N']} |")
  reasons=x['candidate_rejection_counts'];top=sorted(reasons.items(),key=lambda x:x[1],reverse=True)[:4];details.append(f"- **{n}**：{x['accepted_optimizer_steps']}/{x['outer_iterations']}接受，最终{6+x['final_active_modes']}个活动变量；候选拒绝主要为{top}。保留视角IoU变化{f['HOLDOUT_IoU']-i['HOLDOUT_IoU']:+.4f}，固定深度覆盖变化{f['FIT_depth_coverage']-i['FIT_depth_coverage']:+.4f}。原有/最终CAD抽样穿入{i['Ring_signed_sample_penetration_mm']:.6f}/{f['Ring_signed_sample_penetration_mm']:.6f}mm；[完整图](figures/full/{n}_Optimization_Detail.png)。")
 n=len(runs);fitup=sum(x['FIT_IoU_final']>x['FIT_IoU_initial']+1e-6 for x in runs);holdup=sum(x['HOLDOUT_IoU_final']>x['HOLDOUT_IoU_initial']+1e-6 for x in runs);depthup=sum(x['FIT_depth_cost_final']<x['FIT_depth_cost_initial']-1e-6 for x in runs);stalled=[x['case']for x in runs if x['more_than_half_outer_rejected']];selfbad=[x['case']for x in runs if x['final_self_N']>0];underground=[x['case']for x in runs if next(a for a in inherit if a['case']==x['case'])['needs_cap']and x['below_base_final']>0];depthdown=[x['case']for x in runs if x['FIT_depth_coverage_final']<x['FIT_depth_coverage_initial']-1e-6];strictRingfree=[x['case']for x in runs if not by[x['case'],'FINAL']['Ring_surface_collision']and not by[x['case'],'FINAL']['Ring_inside_body_sample_N']];seconds=sum(x['seconds']for x in runs);accepted=sum(x['accepted_optimizer_steps']for x in runs);restarts=sum(x['gradient_restart_updates']for x in runs);total=sum(x['outer_iterations']for x in runs)
 replay=load(R/'metrics/FULL_OBJECTIVE_COMPONENTS.json');replaybad=[dict(case=x['case'],difference=x['replay_difference'])for x in replay if x['label']=='FINAL'and not x['replay_within_training_tolerance']]
 title='''# TASK-E4-CAP-REPAIR-STABLE-PYTORCH3D-011 技术报告

本轮以009参数化C为基础，修正了B→C截断继承并完成九条统一受控PyTorch3D路线。不是010的B直接裁切，也没有重跑球体S。所有最终状态按固定预算保存，不从中间checkpoint挑最好结果；真实3D精度均NOT_EVALUABLE。
'''
 text=title+f'''
## 核心结果

- 初值：规则实际识别7例需截断，均为冠面且无地下顶点；另两例不强制截断。五个旧冠面和两个未截断C逐位复用，只拟合G05/G09缺失冠面的情况。G05仍为UNCERTAIN_BASE；G09保留009有向蓝侧，不用近零中位数定方向。
- 执行：{n}/9条路线输出固定预算末状态，合计{total}个外层提案、{accepted}次接受更新，其中{restarts}次为统一纯梯度重启备选。**提案数不等于有效更新数。** 超过一半外层被拒绝的病例为{stalled}；这些不能称持续有效优化。
- 观测：FIT IoU提高{fitup}/9、HOLDOUT IoU提高{holdup}/9、固定原始分母深度代价降低{depthup}/9。深度覆盖下降病例{depthdown}，必须与误差下降一起视为取舍/潜在失败。
- 独立几何：最终检出自交的病例{selfbad}，七个冠面中检出地下顶点的病例{underground}；零CAD表面/包含相交的终态{strictRingfree}。其他残余接触须与初值及抽样穿入比较，不能用守卫通过冒充完全无碰撞。
- 本轮定位为**基底继承与受控更新的工程验证**。是否改善完整真实三维形态仍不能由Mask/HERO代理单独确定，也不能把停滞、残留碰撞或覆盖损失隐藏为科学PASS。

关键反例：**G09的HOLDOUT IoU约0.929→0.837，G02原始固定深度代价约0.014→0.077，G01深度覆盖约0.945→0.915。** G04最大实际位移约0.000067mm，不能把其IoU微小数值上升计为实质几何改进。7/9仅表示数值方向，不是7例真实三维改善通过。所有这些末状态均原样保留，不用更好的中间轮次替代。

## 输入、版本与冻结

九例同009：Ip G01/G02/G03，Is G07/G04/G05，IIa G06/G08/G09。物理组彼此独立，G08仅video005，其他各守自身冻结坐标；无跨视频拼接。旧Camera Gate标签不拒绝病例。RGB/Mask、原生HERO、K/c2w、Type-2、Ring CAD和DXY保持不变，无新模型下载/推理或相机恢复。

初始化规则先在7ae5ab1冻结；第一循环52a014d的额外G01运行和中断G02现场完整留档。统一修复后的九例正式版本为8e7c043，[主冻结](assets_index/PREOPT_FREEZE.json)含九例C、固定谱基、输入、代码、配置与两张初始化图。全部最终预测冻结后才独立评价。初始投影和几何审查不使用HOLDOUT改初始化或选模型。

已有C的复用是用户批准的初始化，不是失败时回填其他路线预测。B仅用于明确的软初始化参考和静态对照；没有第三条B更新，没有球体S路线。各原始失败和历史报告未覆盖。

## B→C继承与G05/G09

读取009 `BASE.json`和原可视化的实际判别 `n·X+d<0` 为灰色，正侧为蓝色。平面系数归一；ROI比较采用010修复的同步反号(n,d)及共同世界参考点距离，但保留半空间的符号不变。G09历史176.042°主要是无向法向等价，修正约3.958°；这不能直接证明010归档主平面已经实际反向。011通过直接继承009蓝侧避免重新猜方向，内部可靠HERO上分位只提供诊断支持。

统一规则是原始接触BROAD、B在参考面两侧确有结构，才必须冠面；基底可靠性只标注不确定。不是看病例ID或类型决定。G01/G03弱接触不截断。新C仍是009足迹/轴长/高度/弧度模型，6→7→9，TRF每级30预算；只有FIT轮廓残差>3px才增参数。实际G05/G09均在6参数级结束。B蓝色上表面和截面原边交点只生成足迹/高度初值，软参考权重0.005，原Mask/内部HERO仍为主监督，不使用B直接裁切网格作为最终C。

G05保留009的45px背景面，不用010重新选的30px面；ROI变化约8.456°、共同位置偏移约0.876mm，UNCERTAIN_BASE始终保留。这里优化的是固定参考上的足迹与隆起关系，没有声称恢复精确组织平面。G09保留同一有向参考，HERO90分位为正但较低，不能从此推导解剖方向已绝对认证。

修复前后独立初始化评价：G05 HOLDOUT IoU约0.897→0.902，G09约0.770→0.929；G05仍有小幅可见覆盖损失需要记录，G09投影解释改善不等于真实高度精度。G09新C相对所选参考面的最大高度约0.309mm，旧C约1.032mm；这是模型变化，不是实际组织高度已认证。原HERO上表面证据很低，不能仅凭IoU排除过度截断或基底偏移的可能性，需结合严格同视角图人工审查。新初值均为单连通闭合记账实体，推断底盖单独标记，不参与Mask/RGB/深度观测。

[九例继承审计](metrics/C_INHERITANCE.csv)、[初始化对照](metrics/INITIAL_COMPARISON.csv)、[G05独立过程图](figures/full/G05_Cap_Repair.png)、[G09独立过程图](figures/full/G09_Cap_Repair.png)。

## 010机制复核与本轮工程修复

010的固定SGD lr1/momentum.9在GLOBAL6中出现实际2mm以上单步/异常塌缩；本轮未提高该紧急线，而以实际mm位移限幅、几何守卫和回缩替代直接接受。初期少量全局自由度，后续低频16、较高频48按接受稳定性门槛释放，所有病例同代码/规则。

本轮V1额外G01执行300提案/12接受，G02随后被中断。最初“动量方向上升”的猜测被只读复核纠正：Adam自动微分方向导数为负，但一个临界首层射线/四个点对的active-set跳变使真实全FIT目标出现离散缺失代价。纯梯度方向探针可下降，故加入统一STEEPEST_RESTART，不修改损失或挑有利像素。额外试跑、有限差分探针和原源码/模型均在[工程留档](assets_index/ENGINEERING_V1_ARCHIVE.json)及本地engineering_validation_v1，不计为额外科学实验臂，也不隐瞒计算开销。

九例均采用同一受控Adam0.02与8次0.5回缩。Ring阻塞可作一次SLSQP线性接触方向投影；若仍不能通过实际目标，可试同一最大lr的未预条件化负梯度，仍经过全部几何和目标检查。接受重启才清空旧矩，完全拒绝则参数/一二阶矩/step精确恢复。合成分段目标和真实状态回滚控制均通过。没有继续按最终输出改权重或扩大搜索。

## 逐例正式结果

冻结后只读分量回放显示：G02的轮廓项约0.016132→0.006643，主导总目标下降，尽管绝对深度和形状先验变差；G09轮廓代理项约0.001196→0.000485，但硬可见Mask IoU下降，说明软Ring-Aware训练目标下降不保证完整硬Mask评价改善。两者均不是所有观测同时改善的证据。[完整分量](metrics/FULL_OBJECTIVE_COMPONENTS.csv)为新进程只读重算，不包含任何反传、优化或选模。

**新增重放失败：** G02末状态跨进程重算总目标比训练日志相差约1.64844e-6，差异全部来自轮廓项，深度和正则逐项一致；其他八例重放一致。该差异超过原1e-7接受容差，严格重放检查记FAIL，未放宽阈值，也未改写日志或重跑预测。底层原因尚未完全定位，不能仅凭此断言CUDA非确定性。原先154项完整性/几何交付检查通过，新增这一项后为154/155通过；完整工程复现验收仍有此缺口，不能标成全PASS。所有预测SHA仍与冻结记录一致。

IoU为本例对应视角均值；深度代价按固定原生观测数汇总，为无量纲Huber代价，不是毫米误差。条件MAE/median/p95/max、原始N和命中/未命中另列，不只报告命中后的平均值。

| 病例 | 提案 / 接受 | 接受：整体 / 低频 / 细节 | 最终局部模式数 | FIT IoU | HOLDOUT IoU | 原始固定分母深度代价 | 固定深度覆盖 |
|---|---|---|---|---|---|---|---|
{chr(10).join(lines)}

[逐参考原始指标](metrics/PER_VIEW_METRICS.csv)、[逐例结果](metrics/NINE_CASE_RESULTS.csv)、[全部阶段](metrics/ALL_STAGE_WITH_BLENDER.csv)。本轮统一循环总用时约{seconds:.1f}秒，不含C准备/工程额外试跑/评价和画图；实际资源以各RUN记录为准。

## 物理几何和更新幅度

| 病例 | 最大初值位移mm | 抽样CAD穿入mm 初→末 | Blender CAD相交对 初→末 | 最终Blender自交对 | 基底下顶点 | 连通 / 非流形边 |
|---|---|---|---|---|---|---|
{chr(10).join(physics)}

守卫以实际毫米位移检查，单轮信赖域.0125D截在.075–.2mm，总位移限.25D。D是初值可见面的空间跨度，仅作数值尺度，不以P0体积衡量正确性。检查面积、原法向方向、正半空间/边界、非邻接自交和实际CAD；对既有碰撞，初值与上一接受状态双界阻止抽样穿入累积恶化，数值容差1e-5mm。初始无FCL相交者不允许新相交。抽样材料距离不是连续全表面的严格穿透上界，CAD对数也不直接等于穿透深度；独立Blender与原始CAD结果均保留。

全局微调没有自由改变基底法向；冠面正高度图和边界衰减保持交线一致。存在弱基底时，严格“高于所选参考面”只是几何契约，不等于参考面一定是真组织基底。灰色闭合面属于推断，闭合/平滑不是准确度证据。

## 逐组异常和限制

{chr(10).join(details)}

拒绝次数按候选统计，一个候选可以同时违反多条，因此各原因不是互斥百分比。多数被拒绝、未能释放更高自由度、很小实际位移或覆盖下降都列为限制；不能以有限局部空间/固定预算下未下降证明真实数据不可能或PyTorch3D路线失败。拒绝多也可能包含接近当前可行局部极小值的保守收敛，不单凭比例判定模型错误。真正的硬命中集合跳变仅在工程G01探针中有直接定位证据，不能把它当作所有病例已经证明的共同原因；各轮梯度与实际位移、观测变化仍需结合审查。初始和最终已有微碰撞仍需人工审阅，未根据图好看程度换角度或删除面片。

本轮C修复、正高度参数图、Adam方向/回缩与确定性全FIT求值同时变化，不是隔离因果的消融；和010只能作为历史对照，不把所有收益归因一个组件。48是相对16更高的有限谱细节，并非完全自由顶点高频能力。未释放的阶段不视为已验证。

## 固定审计表

| 审计项目 | 必须汇报 |
|---|---|
| 目标组数 | 9个独立真实物理组，Ip/Is/IIa各3 |
| 本算法独立成功 | 本轮末状态模型输出{n}/9；接受次数与是否真正改善逐例分列，不等同临床测量正确 |
| 本算法失败 | 停滞/几何/覆盖异常见本报告与FAILURE_LEDGER；真实完整3D准确度NaN / NOT_EVALUABLE |
| 历史测量值回退 | 0；冻结C是明确初值，不用其他路线替换本轮失败预测 |
| 失败组及具体原因 | [失败台账](FAILURE_LEDGER.md)，九例全图与所有候选均保留 |
| 最终统计样本 | 始终给9个物理组分母；共同初值/末状态配对，不筛掉难例或只报最好checkpoint |
| 是否使用GT选择算法 | 否；双阶段预注册、输入/预测SHA，真实GT/Oracle从未参与拟合、选择或调参 |

没有独立真实3D测量真值，故中位绝对相对误差、真实MAE/p95/最大误差以及高度/体积准确度均NOT_EVALUABLE。HERO误差只是观测代理。模型估计基底高度与面积/体积仅诊断，不当作真值。

## 图、复现与停止

五张核心图及九例详细图见[结果索引](RESULT_INDEX.md)，复现与状态恢复见[REPRODUCE](REPRODUCE.md)，实现差异/损失及配置遗留字段见[METHOD_AND_LOSS_AUDIT](METHOD_AND_LOSS_AUDIT.md)。原冻结Fig2混合了侧视/斜视，不适合跨列直接比较；原字节保留，新增Fig2b按同一行相同相机和毫米范围展示全部模型，不更改几何。大网格、checkpoint、所有提案参数保留本机并有绝对路径/SHA索引，Git仅代码、配置、小型结果表和核心图。

**停止于本轮九例C→PyTorch3D验证，等待人工审查；不替换正式主线，不运行新S对照、SDF、相机优化或跨视角HERO配准。**
'''
 (R/'TECHNICAL_REPORT.md').write_text(text)
 ledger='''# 失败台账与未解决问题

本轮保留全部九例、所有拒绝候选和额外工程试跑，不通过改权重/评价分母/挑checkpoint制造PASS。

'''+chr(10).join(details)+'''

## 工程记录

1. 初始化预检查首次缺少self_intersections导入，发生在任何正式更新前，补导入后所有检查通过；没有改变评价阈值。
2. 原始RelativePrior保留孤立底盖中心的弱顶点先验；底盖面从不参与真实观测。协议“底盖不进正则”的概述须按面/顶点区分，详细审计已说明，没有秘密改损失。
3. V1已知G01额外300提案/12接受，G02中断真实步数仅以已存checkpoint/log为下界，不捏造。源码、配置、模型和原路径映射完整保留。
4. 最初动量上升猜测不成立；ASCENT_DIRECTION_DIAGNOSIS和DIRECTION_FD_DIAGNOSIS保留了负方向导数及真实active-set损失跳变。统一纯梯度重启是一次工程修复，不是对某组单独调参或额外科学对照。
5. 继承JSON有未执行的旧mode/stop/reuse_B字段，实际以stages/trust/optimizer和冻结代码为准，原字节保留；CONFIG_IMPLEMENTATION_AUDIT独立说明，不用旧volume范围冒充本轮守卫。
6. 真实相机/原生深度和组织基底仍有不确定性，历史资格标签只记录，不阻塞。有限预算/局部约束下的停滞不是物理不可行的证明。
7. 冻结后分量回放首次在G02严格1e-7重放断言中止，原日志保留；后续只完成九例诊断并逐项保留FAIL，不改阈值。G02差异1.64844e-6全部在轮廓项，原因未完全定位。初次回放调用旧RelativePrior的同内容support缓存写入，所有冻结文件SHA核对完全一致；当前诊断入口只对照原缓存，不再写入。预测/输入/历史文件内容未改变。
8. G09硬Mask评价明显倒退，G02深度代价上升，G01深度覆盖下降，G04几乎无实质位移；这些结果不被总损失下降或全部模型有输出所抵消。

完整候选原因计数、覆盖变化和独立几何见FAILURES、NINE_CASE_RESULTS与逐参考表；每个病例的原图与模型证据均链接在上文。
'''
 (R/'FAILURE_LEDGER.md').write_text(ledger)
 save('metrics/RESULT.json',dict(task=cfg['task'],cases=9,final_model_N=n,outer_proposals=total,accepted_updates=accepted,gradient_restarts=restarts,fit_IoU_improved_N=fitup,holdout_IoU_improved_N=holdup,fixed_depth_cost_reduced_N=depthup,majority_rejected_cases=stalled,depth_coverage_drop_cases=depthdown,final_self_intersection_cases=selfbad,illegal_cap_underground_cases=underground,zero_CAD_intersection_cases=strictRingfree,GT_accuracy='NOT_EVALUABLE',historical_measurement_fallback_N=0,mainline_promoted=False,status='AWAITING_HUMAN_REVIEW'))
 result=load(R/'metrics/RESULT.json');result.update(strict_objective_replay_passed=not replaybad,objective_replay_failures=replaybad,full_engineering_acceptance_passed=not replaybad);save('metrics/RESULT.json',result)
 print('REPORT_WRITTEN')
if __name__=='__main__':main()
