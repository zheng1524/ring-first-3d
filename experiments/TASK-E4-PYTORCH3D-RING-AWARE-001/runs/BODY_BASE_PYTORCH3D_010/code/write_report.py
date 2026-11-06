from common import *
import csv

def main():
 cfg=load(R/'config/PROTOCOL.json');cases=load(R/'config/CASE_LOCK.json');metrics=load(R/'metrics/ALL_STAGE_WITH_BLENDER.json');serial=load(R/'runtime/SERIAL_STATUS.json');failed=load(R/'metrics/FAILURE_DIAGNOSIS.json');planes=load(R/'metrics/BASE_SIGN_REGRESSION.json');clips=load(R/'metrics/EXACT_CLIPPING_AUDIT.json');runs={(x['case'],x['route']):x['run']for x in serial};by={(x['case'],x['route'],x['label'],x['step']):x for x in metrics};fmt=lambda v:'NaN'if v is None else f'{v:.3f}'
 def final(n,a):return by.get((n,a,'FINAL',300))
 finalrows=[];initialrows=[];failrows=[]
 for c in cases:
  n=c['name'];p=final(n,'P');s=final(n,'S');pp=runs[n,'P'];ss=runs[n,'S'];p0=by[n,'P','CHECKPOINT',0];s0=by[n,'S','CHECKPOINT',0];b=by[n,'B','STATIC_B',0];bp=next(x for x in planes if x['case']==n)
  finalrows.append(f"| {n} {c['morphology']} | {pp['accepted_steps']} / {pp['optimizer_steps']} | {ss['accepted_steps']} / {ss['optimizer_steps']} | {fmt(None if p is None else p['HOLDOUT_IoU'])} / {fmt(None if s is None else s['HOLDOUT_IoU'])} | {fmt(None if p is None else p['FIT_raw_fixed_depth_cost'])} / {fmt(None if s is None else s['FIT_raw_fixed_depth_cost'])} |")
  initialrows.append(f"| {n} | {bp['new_status']} | {bp['contact']} | {bp['selected_ROI_upper_px']} | {'截断' if bp['clipped'] else '原B不变'} | {b['HOLDOUT_IoU']:.3f} / {p0['HOLDOUT_IoU']:.3f} / {s0['HOLDOUT_IoU']:.3f} |")
 for f in failed:
  failrows.append(f"| {f['case']} {f['route']} | {f['steps']} / {f['accepted']} | {f['max_candidate_step_mm']:.4f} | {f['candidate_volume_ratio']:.6f} | {', '.join(f['reasons'])} |")
 completed=[x for x in metrics if x['label']=='FINAL'];safe=[x for x in completed if not x['Ring_surface_collision']and not x['Ring_inside_body_sample_N']and x['Blender_nonadjacent_self_pair_N']==0 and x['watertight']and x['winding_consistent']and not x['nonmanifold_edge_N']];lossseconds=sum(x['run']['elapsed_seconds']for x in serial);wall=sum(x['seconds']for x in serial);maxmem=max(x['run']['peak_GPU_bytes']for x in serial)
 technical=f'''# TASK-E4-BODY-BASE-PYTORCH3D-010 技术报告

**基底法向修复和九例精确截断准备已完成；18 个正式条件全部执行，但只有 8/18 完成 300 步，10/18 按预登记紧急条件中断。固定方案未达到“18 次全部完整更新”的目标。** P/S 各完成 4/9；所有中断都发生在前100步全局阶段。中断组 FINAL300 为 NaN，不用最后安全状态替代最终结果，也没有调权重或追加重跑来补齐。

结论为 **MIXED / 全九例初始化优劣仍 INSUFFICIENT_EVIDENCE**：几何裁切成功保留了原 B 上部，但当前统一 SGD 渐进更新不够稳定。P 的四个300步输出都存在碰撞或自交；S 的四个输出中三个通过本轮 CAD/拓扑筛查，但仍保留基底下方的未观测球体结构，不能称真实形状更准确。两条路线共同完成的只有 G02/G04，不能从这两例或单张图推广到全部形态。

## 冻结与输入

- 分支 `exp/TASK-E4-BODY-BASE-PYTORCH3D-010`，预注册提交 `5aeec8b`。同一父实验体系的独立子目录，不覆盖009、修复版Ring-Aware、PROGRESSIVE_HERO或D2。[协议](01_PROTOCOL.md) / [配置](config/PROTOCOL.json) / [冻结SHA](assets_index/PREOPT_FREEZE.json)。
- Ip G01/G02/G03；Is G07/G04/G05；IIa G06/G08/G09，物理身份与 FIT/UPDATE_HOLDOUT 完全继承009。G08仅video005，G01不混video005；无跨视频坐标合并。旧Camera Gate标签不作拒绝条件。
- 无新HERO推理、相机恢复、Mask修改、DXY修改、网络训练或GT读取。冻结 B 是 P 的明确初值来源；S 从原始观测独立设置球体，没有读取 B 的三轴或参数。未截断 B 仅静态评价和图示，未运行第三条更新路线。
- 每例相同FIT/HOLDOUT、相同可靠原生深度ID、同一随机视角序列及同一公制数值归一。UPDATE_HOLDOUT 仅相对本轮Mesh优化留出，不冒称相机恢复过程完全独立。

## 1. 平面法向修复与统一基底策略

009 的 `fit_plane` 已把法向朝向内部点，但不同 ROI 若内部参考点接近平面，仍可能得到反号。旧比较直接 arccos(n·n0)，未处理几何等价。新实现对(n,d)整体归一化，先按参考法向对齐并同步翻转d，再在同一原生内部点中位位置比较偏移。夹角采用 atan2(||n×n0||,n·n0)，避免同向极限的arccos精度损失。保留半空间由可靠原生Polyp点的中位符号确定，不使用B/P0或类型。

G09：**176.042140° → 3.957860°**，共同参考位置偏移约0.058mm，由WEAK转RELIABLE。六例RELIABLE、三例WEAK；G05仍有约8.456°/0.876mm的ROI变化及内点比例不稳，不能通过反号修复把它伪装成可靠基底。G09内部点在保留侧约62%，中位高度仅0.026mm；G04约66%，故平面稳定性不等于半空间或真实接触已被解剖认证。

所有BROAD原始接触证据都生成候选，资格只记录不确定性。RELIABLE统一用45px ROI；WEAK优先满足>=100点/内点>=0.5的最近30/45/60px ROI，均不满足才取最近可用平面并标弱。实际 G05用30px；G09用45px。G01/G03小接触，不强制截断。接触来自009冻结原Mask/深度证据，未利用P0穿平面来反推。

| 病例 | 修复后基底 | 原始接触 | ROI上限px | P处理 | 留出IoU B静态 / P初值 / S初值 |
|---|---|---|---|---|---|
{chr(10).join(initialrows)}

[九例法向回归](metrics/BASE_SIGN_REGRESSION.csv)。118项预检查通过，包含平面正负/尺度等价、共同锚点偏移、旋转平面半立方体精确体积、封闭/法向、G09回归、18初值损失与梯度有限性、相对深度梯度和共同偏移不变性。[预检查](metrics/PREFLIGHT.json)

## 2. 精确几何裁切与球体初值

P读取冻结 B 的真实642顶点三角网格，用半空间线性裁切。完全在上方的原顶点逐位保持、原三角面保留；跨面三角形共享原边交点，裁切面做单独标记的平面耳切三角剖分。没有椭球重拟合、重新缩放、平滑或删除合理上部表面。九例初始实体均闭合、法向一致、无非邻接自交；七例有明确推断底盖。原顶点/边/面ID映射存入P_INITIAL.npz。[裁切审计](metrics/EXACT_CLIPPING_AUDIT.json)

G05保留255个原顶点、新增90个原边交点；G09保留197个原顶点、新增86个交点；所有保留原顶点坐标与冻结B逐位相同。裁切仍可保留旧B上部的CAD冲突；G03/G05/G06/G07的初始相交均如实保留并运行。

S调用官方 `pytorch3d.utils.ico_sphere(level=3)`，642顶点/1280面，**是几何网格函数，不是预训练重建网络**。同一主要FIT来源的完整Mask bbox与可靠HERO轴向深度中位数决定统一半径和中心，沿光轴后移0.5r；仅平移/等比缩放，无预优化和B参数读取。[两路线初始化参数](config/INITIALIZATIONS.json)

P裁切后上表面约478–1280面，S固定1280面；P部分具有开口可见面、推断底盖和切平面边界约束，而S是完整球面。两者的局部顶点数量/有效自由度不同，[DOF与尺度表](metrics/DOF_AND_SCALE_AUDIT.csv) 完整披露。因此本轮比较初始化策略整体，不宣称已完全隔离拓扑/边界差异。

## 3. 相同的PyTorch3D更新

官方PyTorch3D源码commit `e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31`，复用已安装框架。P/S共用每例由S观测得到的中心和半径作数值归一，避免学习率物理尺度因路线不同而变化。70组视角/初值的OpenCV→PyTorch3D→Open3D投影核验通过，Mask几何一致性IoU均1.0；不把实现一致性当真实相机认证。[投影记录](metrics/PROJECTION_GATE.json)

统一SGD lr1、momentum0.9，前100步平移+三轴缩放，后200步顶点局部位移，切换时形状连续并重置动量；边长、初始Laplacian、法向和无支持区域位移保护保持相同。Ring-Aware逻辑和修复的离散前后次序不变；没有新增Ring罚项。原生内部深度用D2边界降权和同视角相对项，权重绝对/相对各0.01，Huber σ0.5mm，上限/未命中均9.5，固定原始分母。不同来源只共享Mesh，不做深度配准/一致性损失。

推断底盖不参与轮廓、RGB、深度、可见支持判定或形状正则。边界顶点在两阶段均仅保留基底切平面内运动，以保持底盖平面身份；上部顶点未额外施加全局半空间不等式。**这条保护不足以防止上表面越过基底或与底盖自交**，是本轮明确暴露的限制，未事后补面或修理结果。

G02/G03/G04/G05/G09只有一个可靠原生深度参考，其余FIT有RGB/Mask；随机每步最多两个FIT，300步完整组有195步实际含HERO。它们与拥有多个深度源的病例有效监督频率不同，但每例P/S相同，不伪造缺失深度或私自改权重。[有效采样](metrics/EFFECTIVE_DEPTH_SAMPLING.csv)

## 4. 18组固定预算结果

“安全/实际步数”区分紧急候选已执行一次optimizer.step但未接受的情况。表中300步缺失保留NaN，任何最后安全状态都只进入单独诊断表/带STOP标记的图。

| 病例 | P安全 / 实际步数 | S安全 / 实际步数 | FINAL300留出IoU P / S | FINAL300固定分母深度代价 P / S |
|---|---|---|---|---|
{chr(10).join(finalrows)}

合计2729次实际SGD更新、2719次通过紧急检查的更新；预定5400步未全部达到。完成300步的P为G01/G02/G07/G04，S为G02/G04/G06/G09；3个物理组G03/G05/G08两路线均无FINAL300。总优化循环约{lossseconds:.1f}秒，含每进程启动的串行墙钟约{wall:.1f}秒，峰值Torch分配{maxmem/1024**2:.1f}MiB（非整个GPU占用）。不存在OOM、NaN/Inf或数据缺失导致的中断。

[全部18条件的固定分母最终表](metrics/FINAL_300_FIXED_DENOMINATOR.csv)、[所有阶段](metrics/ALL_STAGE_WITH_BLENDER.csv)、[逐参考轮廓/深度](metrics/PER_VIEW_METRICS.csv)、[共同完成配对](metrics/PAIRED_FINAL_COMPARISON.csv)。条件深度误差同时保留MAE/median/p95/max、命中/未命中及原始固定代价，不能只比较命中集平均值。

## 5. 失败及物理几何

| 条件 | 拒绝候选步 / 最后安全步 | 单步最大位移mm | 候选/初值体积比，仅诊断 | 原因 |
|---|---|---|---|---|
{chr(10).join(failrows)}

全部10次中断都在GLOBAL6阶段：8次超过固定2mm单步紧急线，2次体积跌出0.1–10紧急范围。该范围不是体积守恒目标，更不是真值；它阻止继续生成极端退化候选。不能把中断称为充分300步后的科学失败。没有改门槛重跑或把旧B/S替换失败路线。

冻结后零optimizer.step的只读回放用真实UNSAFE参数/动量重建失败前状态，位置最大差约几微米以下，逐项重算轮廓/形状/深度梯度。[失败提案回放](metrics/FAILED_PROPOSAL_GRADIENT_REPLAY.json)

- G03-S首步选中的两个FIT无HERO，轮廓梯度本身就产生2.235mm候选；不能把所有中断归咎HERO。
- G08-S首步约3.000mm，轮廓与深度全局参数梯度夹角余弦约0.59；G01-S、G07-S等失败提案中二者也大致同向。因此“梯度互相冲突”不是普遍必要原因，固定步长/动量和尺度响应更直接。
- G09-P拒绝时当前全局梯度范数约0.005，而实际动量缓冲约0.077；仍在推动已很薄的保留体收缩，候选体积比0.070。G06-P候选体积比约0.0017。仅靠轮廓与单面深度不足以阻止此类退化。

独立Blender/FCL/Open3D检查发现：8个完成输出中，P全部有几何失败：G01-P约0.0011mm CAD样本穿入；G02-P有5对非邻接自交；G07-P约0.444mm样本穿入且自交；G04-P有69对自交。S中G06有约0.0445mm CAD样本穿入，G02/G04/G09未检出CAD/自交/非流形问题。通过筛查的三个S仍不等于真实组织：大量球体顶点在估计基底下方，隐藏闭合没有真实观测认证。

G04-P第25步、G02-P第75步已检出自交，均早于释放顶点；G07-P第150步出现自交。G01-P中间有自交、最终消失但仍穿Ring，不能只看最终漂亮程度。基底边界投影与其余主体自由更新并不构成全网格非穿透/不自交保证，Ring遮挡损失也不是3D碰撞屏障。[首次保存自交阶段](metrics/FIRST_SAVED_SELF_INTERSECTION.json)

## 6. 初始化比较与形态判断

G02、G04是仅有的两组双路线共同300步结果：P相对S留出IoU分别高0.0334、0.0162；G02的固定深度代价P较低，G04则S较低。但P二者均发生自交，因此不能据IoU说P更正确。P/S各4/9完成率相同，不支持全九例某初始化已显著更稳定的结论。

Ip的G01-P保留了较好主面并出现柄部方向的形变，但边缘/局部粗糙及Ring接触仍失败；G03双路线早停。Is的G04/G07说明保留上部有利于轮廓起点，却不能靠切边平面约束保证基底连接拓扑；G05弱基底裁切只是探索候选。IIa的G06-S、G09-S从球体形成较低的可见前层，模型相对估计基底的最大高度分别约1.594/0.185mm；这些仅是模型估计，不是真实隆起测量，G06还穿Ring，G09的基底与前景高度相差很小尤其不确定。

本轮直接证明两点：**精确裁切可以保留已有合理上部，不必重拟合冠面；良好初值并不能替代有界、拓扑安全的更新机制。** S能学习观测前层，但没有自动得到真实基底或完整息肉。尚不能判断哪种路线整体三维更准确，尤其不能用有限成功组替代全体分母。修复统一更新步幅/动量及基底边界可行性应作为下一轮候选，未在本轮擅自执行，也不引入新框架。

## 固定审计表

| 审计项目 | 必须汇报 |
|---|---|
| 目标组数 | 9个独立物理组，Ip/Is/IIa各3；P/S共18条件，预定各300步 |
| 本算法独立成功 | FINAL300 P4/9、S4/9，共8/18；至少一条路线有FINAL的物理组6/9；共同完成2/9；数值完成不等于正确 |
| 本算法失败 | 最终缺失10/18（NaN）；G03/G05/G08两路线均缺失；另外5个300步模型有CAD或自交失败 |
| 历史测量值回退 | 0；B仅明确初始化/静态对照；不把B或另一条路线当失败路线最终预测 |
| 失败组及具体原因 | [失败台账](FAILURE_LEDGER.md)、全部STOP/UNSAFE/最后安全模型和逐病例图均保留 |
| 最终统计样本 | 数值指标仅8个实际FINAL，并始终给18分母；共同完成比较2/9；通过本轮CAD/拓扑筛查3/18。独立3D正确性仍NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；预注册源码/输入SHA及预测冻结证据齐全，无真实GT/Oracle读取 |

真实三维测量的中位绝对相对误差、MAE、p95、最大误差、高度/体积准确度均NaN / NOT_EVALUABLE；HERO残差是观测代理，未冒充真值误差。体积变化不以P0作为正确性标准。S没有复制P/B结果，P没有回退S。

## 图与恢复

[Fig1 九例总览](figures/Fig1_Nine_Case_Overview.png) · [Fig2 G05/G09精确裁切](figures/Fig2_G05_G09_Exact_Clipping.png) · [Fig3 三类型阶段演化](figures/Fig3_Representative_Progression.png) · [Fig4 真实观测与更新机制](figures/Fig4_Observation_Update_Mechanism.png)。九例各有近真实参考方向、侧视、斜视、Mask投影与不安全候选图，见[结果索引](RESULT_INDEX.md)。所有网格同病例共用观察/尺度和黑色实体CAD，失败状态不隐藏，底盖灰色且不当作观测。

[复现说明](REPRODUCE.md)与[方法审计](METHOD_AND_LOSS_AUDIT.md)。完整大输入/模型/状态保留本地，Git提交代码、小型审计表和四张核心图。技术版本只新增候选，不替换主线。**本轮固定方案执行结束，18/18完整更新目标未达到；停止并等待人工审查，不自动修调或扩大实验。**
'''
 technical+='\n说明：LAST_SAFE只表示上一次通过数值/单步紧急检查，仍可能穿环或自交。TRAINING/DEPTH_TRACE记录接受步骤，首步拒绝者为零行带表头，实际optimizer.step次数见RUN。零相交筛查不等于绝对解剖真值；微小CAD交线按固定准则保留，未事后放宽标准。\n'
 (R/'TECHNICAL_REPORT.md').write_text(technical)
 ledger='''# 失败台账

本轮所有18条件均入组，不因历史Gate拒绝。十个未完成条件的FINAL300为NaN，最后安全状态仅诊断；八个完成条件也按真实物理检查保留失败。

'''+technical[technical.index('| 条件 | 拒绝候选步'):technical.index('## 6. 初始化比较')]+'''
## 额外实施记录

- 平面单元测试第一版arccos对完全同向向量产生约1.2e-6°的数值伪角，未通过1e-6°测试。改用atan2叉积/点积稳定公式，未放宽阈值；旧源码/测试保留assets_index/PLANES_V1_ARCCOS.py.txt和PREFLIGHT_V1_ARCCOS_ZERO.json。发生在优化前。
- 初版阶段绘图的后缀匹配误把P50/P100/P200加载为P0，目视审阅发现后改为仅P0/S0精确匹配，重新从真实STEP文件画图。旧源码及坏图SHA见assets_index/VISUALIZATION_FAILURE.json；没有修改任何预测/指标或重跑优化。交付验证单独检查阶段路径与内容。
- G05基底仍WEAK；G09虽然数值稳定，但内部点相对平面高度低且只有约62%在正侧，不能称真实解剖基底已恢复。
- 所有原生球体都没有截断，因此估计基底以下闭合与P的推断底盖/边界条件不同。这是初始化策略比较的已知混杂，不隐藏为完全同拓扑实验。
- 未检出NaN/OOM/坏文件；十个中断不能称工具链无法运行，也不能称完成了全部预定步数。

逐例完整图：
'''+''.join(f"\n- [{c}](figures/full/{c}_Detailed.png)"for c in cfg['cases'])+'\n'
 (R/'FAILURE_LEDGER.md').write_text(ledger)
 save('metrics/RESULT.json',dict(task=cfg['task'],status='PARTIAL_BUDGET_COMPLETION_WITH_RECORDED_ALGORITHM_FAILURES',input_cases=9,formal_conditions=18,planned_steps_each=300,completed_300_N=8,completed_P=4,completed_S=4,missing_final_N=10,physical_groups_with_any_final_N=6,paired_final_group_N=2,geometry_screen_pass_final_N=len(safe),geometry_screen_pass_cases=[x['case']+'_'+x['route']for x in safe],actual_optimizer_steps=2729,accepted_steps=2719,GT_accuracy='NOT_EVALUABLE',historical_measurement_fallback_N=0,normal_bug_fixed=True,base_clip_candidates_N=7,strict_18_full_updates_goal_achieved=False,awaiting_human_review=True))
 print('REPORT_WRITTEN',len(safe))
if __name__=='__main__':main()
