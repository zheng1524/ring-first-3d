from model import *
import shutil
def main():
    post=load(R/'metrics/POSTERIOR.json');e=post['endpoints'];by={x['name']:x for x in e};p0=by['P0'];s1=by['S1/FINAL'];s2=by['S2/FINAL'];diag=load(R/'metrics/DIAGNOSIS.json');gate=load(R/'metrics/CENTER_RELEASE_GATE.json');cfg=protocol();comp=next(x for x in post['components']if x['name']=='COMPONENT_S2_GLOBAL_ONLY');loc=diag['local_components'][0]
    integrity=[]
    for label in ['PARENT_PROTECTION','PREOPT_FREEZE','S2_DYNAMIC_FREEZE']:
        files=load(R/'assets_index'/(label+'.json'))['files'];checks=[dict(path=x['path'],unchanged=sha(x['path'])==x['sha256'])for x in files];assert all(x['unchanged']for x in checks);integrity.append(dict(name=label,N=len(checks),checks=checks))
    original=REPO/'experiments/TASK-E4-2D3D-OBSERVABILITY-001';oldraw=load(original/'assets_index/LOCAL_RESULTS.json')['files'];rawchecks=[dict(path=x['path'],unchanged=sha(x['path'])==x['sha256'])for x in oldraw];assert all(x['unchanged']for x in rawchecks);integrity.append(dict(name='GATE_A_LOCAL_ASSETS_CHAIN',N=len(rawchecks),checks=rawchecks))
    frozen=load(R/'metrics/ALL_OPTIMIZED_PREDICTIONS_FREEZE.json');assert all(sha(x['path'])==x['sha256']for x in frozen['files']+frozen['configs'])
    save('assets_index/FINAL_INTEGRITY.json',dict(passed=True,groups=integrity,optimized_files_N=len(frozen['files']),optimized_predictions_unchanged=True))
    assets=[asset(p)for folder in ['inputs','local_results','audit_only']for p in sorted((R/folder).rglob('*'))if p.is_file()];save('assets_index/LOCAL_RESULTS.json',dict(files=assets,GT_reused_source=post['GT_source'],no_model_or_dataset_upload=True,units='mm'))
    rows=[]
    for x in e:
        v=x['volume'];rows.append(dict(stage=x['name'],fit_IoU=x['fit_IoU'],holdout_IoU=x['holdout_IoU'],Chamfer_MAE_mm=x['Chamfer_mm']['MAE'],Chamfer_p95_mm=x['Chamfer_mm']['p95'],symmetric_difference_mm3=v['symmetric_difference_mm3'],Mesh_volume_mm3=x['Mesh_dimensions']['volume_mm3'],added_vs_P0_mm3=v['added_from_P0_mm3'],removed_vs_P0_mm3=v['removed_from_P0_mm3'],wrong_added_vs_P0_mm3=v['added_from_P0_mm3']-v['GT_added_recovered_mm3'],wrong_removed_vs_P0_mm3=v['removed_from_P0_mm3']-v['GT_removed_recovered_mm3']))
    table('metrics/RESULT_SUMMARY.csv',rows)
    save('metrics/RESULT.json',dict(status='MIXED_GLOBAL_CORRECTION_LOCAL_NO_EFFECTIVE_SIGNAL',Q1='PARTIAL: Mask and average surface distance improve, volume disagreement and center error worsen',Q2='NO_SUBSTANTIAL_INDEPENDENT_LOCAL_BENEFIT_DEMONSTRATED; centers NOT_TRIGGERED',Q3='NOT_CONSISTENT_ACROSS_3D_METRICS',S3=load(R/'metrics/S3_STATUS.json'),Gate_B_C_D='NOT_RUN',stopped=True,mainline_promoted=False,one_case_one_progressive_run=True))
    lossmap={}
    for stage in post['stages']:
        for r in load(R/'metrics'/(stage+'_HISTORY.json')):lossmap[stage+'/'+r['checkpoint']]=r['loss']
    lossmap['P0']=lossmap['S1/START'];transitions=[]
    for before,after in zip(post['all_checkpoints'],post['all_checkpoints'][1:]):
        transitions.append(dict(before=before['name'],after=after['name'],before_loss=lossmap[before['name']],after_loss=lossmap[after['name']],before_fit_IoU=before['fit_IoU'],after_fit_IoU=after['fit_IoU'],before_Chamfer_MAE_mm=before['Chamfer_mm']['MAE'],after_Chamfer_MAE_mm=after['Chamfer_mm']['MAE'],before_Chamfer_p95_mm=before['Chamfer_mm']['p95'],after_Chamfer_p95_mm=after['Chamfer_mm']['p95'],before_difference_volume_mm3=before['volume']['symmetric_difference_mm3'],after_difference_volume_mm3=after['volume']['symmetric_difference_mm3'],loss_decreased=lossmap[after['name']]<lossmap[before['name']]-1e-8,difference_volume_worsened=after['volume']['symmetric_difference_mm3']>before['volume']['symmetric_difference_mm3']+post['fixed_space_weight_mm3']))
    table('metrics/CONSECUTIVE_TRANSITIONS.csv',transitions);save('metrics/CONSECUTIVE_TRANSITIONS.json',dict(rows=transitions,all_consecutive_saved_transitions=True,no_prediction_selection=True));transition=next(x for x in transitions if x['before']=='S1/ROUND_01'and x['after']=='S1/ROUND_02')
    tab='|指标|P0|S1：六参数|S2：六参数+双幅值|\n|---|---:|---:|---:|\n'
    specs=[('拟合Mask IoU',lambda x:x['fit_IoU']),('留出Mask IoU',lambda x:x['holdout_IoU']),('Chamfer MAE mm',lambda x:x['Chamfer_mm']['MAE']),('Chamfer中位 mm',lambda x:x['Chamfer_mm']['median_absolute']),('Chamfer p95 mm',lambda x:x['Chamfer_mm']['p95']),('Chamfer采样最大 mm',lambda x:x['Chamfer_mm']['maximum']),('差异体积代理 mm³',lambda x:x['volume']['symmetric_difference_mm3']),('实际封闭Mesh体积 mm³',lambda x:x['Mesh_dimensions']['volume_mm3']),('Mesh质心误差 mm',lambda x:x['center_of_mass_error_mm']),('可见区Chamfer MAE mm',lambda x:x['visible_Chamfer_mm']['MAE']),('未知区Chamfer MAE mm',lambda x:x['unknown_Chamfer_mm']['MAE']),('原始Mesh邻面角p95 度',lambda x:x['physical']['quality']['normal_angle_deg']['p95'])]
    for name,f in specs:tab+='|'+name+'|'+'|'.join(f'{f(x):.6f}'for x in e)+'|\n'
    vtab='|相对P0的占据变化代理 mm³|S1|S2|\n|---|---:|---:|\n'
    for name,f in [('实际新增',lambda x:x['volume']['added_from_P0_mm3']),('实际删除',lambda x:x['volume']['removed_from_P0_mm3']),('正确新增',lambda x:x['volume']['GT_added_recovered_mm3']),('错误新增',lambda x:x['volume']['added_from_P0_mm3']-x['volume']['GT_added_recovered_mm3']),('正确删除',lambda x:x['volume']['GT_removed_recovered_mm3']),('错误删除',lambda x:x['volume']['removed_from_P0_mm3']-x['volume']['GT_removed_recovered_mm3'])]:vtab+='|'+name+'|'+'|'.join(f'{f(x):.6f}'for x in [s1,s2])+'|\n'
    a=load(R/'metrics/S1_FINISHED.json');b=load(R/'metrics/S2_FINISHED.json');below=next(x for x in diag['regions']if x['stage']=='S2');initial=load(R/'metrics/P0_ZERO_AND_FIREWALL.json');fd0=load(R/'metrics/P0_GLOBAL6_SENSITIVITY.json');fd1=load(R/'metrics/S1_LOCAL8_SENSITIVITY.json');fd2=load(R/'metrics/S2_FINAL_SENSITIVITY.json')
    text=f'''# 渐进几何自由度验证：一次IIa运行

**结论：六参数显著改善轮廓和平均曲面距离，但体积/位置并未一致接近GT；双核未产生有效独立拟合信号，中心没有释放。** 本轮只完成P0→S1→S2，一场景一次渐进轨迹，不将三个检查点当三个病例，不自动运行Gate B/C/D。

## 三问回答

1. **六参数能否明显纠正P0？部分能。** 训练/留出IoU从{p0['fit_IoU']:.3f}/{p0['holdout_IoU']:.3f}提升至{s1['fit_IoU']:.3f}/{s1['holdout_IoU']:.3f}，Chamfer MAE下降{(p0['Chamfer_mm']['MAE']-s1['Chamfer_mm']['MAE'])/p0['Chamfer_mm']['MAE']:.1%}；但差异体积由{p0['volume']['symmetric_difference_mm3']:.3f}增至{s1['volume']['symmetric_difference_mm3']:.3f}mm³，质心误差亦增大，不能宣称整体三维稳定纠偏。
2. **两相反核能否进一步改善真实形状？本次未见实质独立收益。** 双核数学/数值方向合同通过，但优化后幅值只有{gate['amplitudes']}。S2仍开放六全局参数，故总阶段变化不能全归于局部；在同一最终全局参数处关掉两核，实际拟合loss反而略低。GT固定采样方向的局部净收益只有约{abs(loc['full_minus_global_only_FIXED_GT_to_prediction_MAE_mm']):.8f}mm，不能当有效恢复。S3按规则NOT_TRIGGERED。
3. **二维提升与三维误差下降是否一致？不完全一致。** Chamfer改善而差异体积、质心位置恶化。低轮廓loss、高IoU、闭合光滑都不足以证明真实三维正确。

## 数据/代码/GT隔离

独立目录与分支 `TASK-E4-PROGRESSIVE-DOF-001`，从Gate A c5fb079建立，原结果、代码和冻结证据不修改。P0、BASE_FIELD、Ring、K/c2w、五个原TARGET标签字节相同，没有重渲染Mask/RGB或重新导出GT。3拟合obs01/03/05、2留出obs00/04不变；模拟已知相机不冒称临床Camera Gate认证。GT直接复用原生CAD NPZ，全部优化文件先冻结后才打开，不用GT参数/深度选择初始化、核位置、停止或结果。

`renderer.py`和`continuous.py`与Gate A原字节一致。固定原版目标（corrected=False）：预测几何轮廓与前景像素中心轮廓的双向NN Huber/9 +0.2固定分母XOR。没有同时改用亚像素候选、固定残差平方loss、新优化器或几何先验。GT最低Z只作本报告后验审计，没有加入训练地板约束。

## 零面、尺度与灵敏度先行合同

中心ΔXYZ及半轴log倍率共六参数，零旋转。参考节点仿射变换，字段乘几何平均尺度，保证零局部幅值时零面为原P0的仿射变换。P0的V/F完全一致；各参数.02mm量级扰动与预期仿射顶点最大误差小于1e−6mm。只使用少量共享参数，不是自由顶点更新。

参考h=.15mm；世界网格间距随半轴倍率改变，非更换分辨率。各向异性字段**不是严格单位梯度距离场**，添加核后亦不保证Eikonal；near-zero梯度范数原值保留。物理评价从实际Mesh距离/占据取得，不能把SDF系数当真实表面位移。局部±.02系数测试确认节点占据和Mesh体积扩张/收缩方向正确，故没有“核接反/完全不响应”的实现失败。

固定索引残差J只作旁路诊断，Powell实际调用原标量loss，没有用Jᵀr驱动更新。初始六参的两种梯度方向余弦约{fd0['rows'][0]['gradient_cosine']:.3f}/{fd0['rows'][1]['gradient_cosine']:.3f}，S1后八参约{fd1['rows'][0]['gradient_cosine']:.3f}/{fd1['rows'][1]['gradient_cosine']:.3f}，S2最终约{fd2['rows'][0]['gradient_cosine']:.3f}/{fd2['rows'][1]['gradient_cosine']:.3f}；两套定义不等价，不能把诊断残差的满秩/下降方向当实际目标的证明。全部ε=.02/.01数据、分源loss和J在metrics及本地索引。

## 一次运行与阶段连续性

- S1：中心Δ各±.75mm，半轴倍率[.5,1.4]，初值0即原P0。{a['nfev']}次评价/{a['iterations']}轮/{a['seconds']:.1f}秒，达到500次预算，**未宣称充分收敛**。
- 核位置仅由S1三拟合视角可见轮廓残差确定；目标内欠覆盖提出扩张、目标外过覆盖提出收缩，Ring/UNKNOWN过滤保持。残差按源等权，取加权均值最近的实际表面候选。面ID属于预测S1零面，不是GT面身份。全部候选与两核选择CSV可追溯；半径固定1.8mm，无搜索。
- S2：保留六全局参数开放、增两幅值共8维，中心固定。{b['nfev']}次评价/{b['iterations']}轮/{b['seconds']:.1f}秒，正常数值退出；保存最后迭代，不挑更好中间轮。
- S3：逐核幅值/实际loss贡献门槛未通过，不释放中心。S1 loss={gate['S1_loss']:.9f}，S2={gate['S2_loss']:.9f}，S2停用两核={gate['S2_global_only_loss']:.9f}；局部净拟合收益{gate['local_component_loss_benefit']:+.9f}，不是有利贡献。结论并非只依赖.02幅值门槛，停用核的实际目标更低这一事实也否定了释放信号。

每阶段START继承上阶段FINAL，校验V/F完全相同，不重拟合P0。每阶段均12轮/500函数预算、同Powell及原xtol/ftol；direc按实际维度必要扩展，log半轴方向按.2/a0归一。Powell xtol=.01是相对数值容差，不能冒充统一毫米位移限制。未增加碰撞损失/正则化/搜索半径。

## 统一独立GT评价

{tab}
GT真实封闭Mesh体积为{post['GT_mesh_dimensions']['volume_mm3']:.6f}mm³。P0、S1、S2采用同一2^19 Sobol集合，固定域只由P0网格与最大仿射边界决定，GT域外顶点{post['GT_vertices_outside_fixed_metric_domain']}。单点体积权重{post['fixed_space_weight_mm3']:.9f}mm³；占据差异是积分代理，真实Mesh净体积另列。与Gate A的采样域不同，不将两个实验的微小体积读数直接比较。

三维距离每方向6000面积样本，GT点集固定，可见/未知按原相机Mask/CAD下GT首次表面后验分组；全部分母保留。预测面积采样点随三角化改变，局部微米级对称Chamfer差异可能有采样噪声，因此另报同一GT点集的配对方向。GT/预测Eulerian误差用同一固定P0参考点、同一有符号最近面距离变化，不与材料顶点位移混用。

{vtab}
“GT应删区域恢复率100%”不等于正确：S1/S2同时错误删除约8.54/8.55mm³，还错误新增约6.36/6.27mm³，不能用召回率或净体积抵消错误。S2相对S1新增{s2['volume']['added_from_previous_stage_mm3']:.6f}、删除{s2['volume']['removed_from_previous_stage_mm3']:.6f}mm³，阶段变化仍含全局继续拟合。

## 整体与局部分量

S1全局中心控制Z降到{s1['center_parameters_mm'][2]:.6f}mm，ΔZ={a['q'][2]:.6f}接近−.75下界；半轴={s1['semiaxes_mm']}mm。S2相近。这里不将椭球控制中心冒充GT的同名参数；真正比较的是两个Mesh质心，误差由0.3467变为0.4102/0.4056mm。

最终阶段在同一冻结全局参数下，关掉两核得到Chamfer {comp['Chamfer_mm']['MAE']:.6f}mm、差异体积{comp['volume']['symmetric_difference_mm3']:.6f}mm³；全模型分别{s2['Chamfer_mm']['MAE']:.6f}mm/{s2['volume']['symmetric_difference_mm3']:.6f}mm³。这些是固定参数分量诊断，不是重新优化/新实验臂，不用它们替代正式输出。

同一全局零面上，局部实际最大外扩{loc['largest_outward_mm']:.6f}mm、内缩{loc['largest_inward_mm']:.6f}mm。固定GT点方向平均误差仅改善约{abs(loc['full_minus_global_only_FIXED_GT_to_prediction_MAE_mm']):.8f}mm；差异体积改善约一个空间积分点权重。不能据此认定局部真实表面有实质改善，也没有重复实验为其建立统计置信度。S2相对S1的主要变化来自继续调整全局参数；此单轨迹没有额外预算匹配全局续训对照，不作过强因果外推。

## 不一致的原因及证据强度

**接口实现错误：不支持。** P0同一、仿射零面、符号/体积方向、相机/Mask/CAD字节合同均通过。字段非单位梯度已明示，评价没有混用系数/材料位移。

**轮廓目标不足以保证三维正确：直接支持。** 大幅提高IoU、降低实际loss时，差异体积和质心误差反而变大；最终约{below['prediction_volume_below_GT_min_z_mm3']:.6f}mm³预测占据低于GT的最低Z。三维体积错误并没有被二维轮廓充分惩罚。不能只凭此区分纯观测不充分与离散NN目标偏差的唯一份额；也不是误把FixedResidual接入了优化器。

**中间轨迹的同族反例。** S1第1→2轮，实际loss {transition['before_loss']:.6f}→{transition['after_loss']:.6f}，拟合IoU {transition['before_fit_IoU']:.6f}→{transition['after_fit_IoU']:.6f}；但Chamfer MAE {transition['before_Chamfer_MAE_mm']:.6f}→{transition['after_Chamfer_MAE_mm']:.6f}mm、p95 {transition['before_Chamfer_p95_mm']:.6f}→{transition['after_Chamfer_p95_mm']:.6f}mm、差异体积 {transition['before_difference_volume_mm3']:.6f}→{transition['after_difference_volume_mm3']:.6f}mm³均恶化。两者都在同一六参数可表达族内，后者确实更符合原训练目标；因此这次退化不能只解释为“表达不了更好的几何”或“尚未找到更低loss”。所有连续保存转移均见CONSECUTIVE_TRANSITIONS，不只挑这一行。该中间点只用于后验机制诊断，**未据GT回退/选作正式输出**。

**当前局部表达/定位受限：有局部证据。** 约{below['fraction_large_GT_errors_outside_local_support']:.1%}的大于.2mm GT误差样本位于两核支撑之外。固定中心幅值无法修改那些区域，边缘残差位置不等于应恢复内部形状的位置。双符号核已解除上轮单符号限制，不能继续套用“只能扩或只能缩”的旧结论；本轮未做GT最优拟合，不能证明所有可移动双核或所有SDF表示都不足。

**搜索未充分收敛：有证据但非唯一原因。** S1用满预算，已登记的Y正向.02/.01mm探针均进一步降低实际loss，没有选为新预测。S2有到Z下界的小步下降，部分ε探针被边界裁剪成同一实际位置，不能把它们当两个独立步长证据。正常退出不代表全局最优。保留全部有限差分和轨迹，不加预算、不改边界、不重启；当前证据不足以将GT体积恶化全归于搜索。

所有保存Mesh保持闭合、绕序一致、单连通，Ring候选碰撞记录为0；端点Blender EXACT Ring交集为0，非邻接三角面自交未检出。邻接/退化情形仍非完整形式认证，详见连续性表和Blender原值。光滑、连通并不认证真实几何。

剩余实际loss下降空间也不证明它就是GT改善方向；本轮没有把这些探针选为新输出或重新启动优化。

## 图与交付

![实际Mesh演化](figures/Fig1_Actual_Progressive_Meshes.png)

![五视角冻结轮廓](figures/Fig2_Five_View_Contours.png)

![真实训练与GT变化](figures/Fig3_Training_And_Independent_3D.png)

![整体局部分量位置](figures/Fig4_Global_Local_Contributions.png)

[结果汇总CSV](metrics/RESULT_SUMMARY.csv) · [逐轮GT表](metrics/ROUND_METRICS.csv) · [连续转移审计](metrics/CONSECUTIVE_TRANSITIONS.csv) · [逐源表](metrics/PER_VIEW_METRICS.csv) · [分量表](metrics/COMPONENT_METRICS.csv) · [归因审计](metrics/DIAGNOSIS.json) · [复现](REPRODUCE.md) · [失败记录](FAILURE_LEDGER.md) · [本地Mesh/SDF/采样索引](assets_index/LOCAL_RESULTS.json)。冻结代码668dbe1，全部优化文件SHA先于GT读取保留，未回写Gate A。

## 固定审计表

|审计项目|汇报|
|---|---|
|目标组数|1个IIa原生场景、1条渐进轨迹，非3病例或多方法搜索|
|本算法独立成功|1/1场景数值输出，P0/S1/S2保留；总体真实几何正确性未认证|
|本算法失败|S1预算终止未收敛；双核信号不足、S3未触发；几何多指标不一致保留|
|历史测量值回退|0；只复用获准P0和原始底层Mask/相机/Ring|
|失败及具体原因|见上节与FAILURE_LEDGER，Z下界/体积错误/局部覆盖/有限搜索均有证据|
|最终统计样本|完整1场景、3拟合2留出、每方向6000面积点、固定524288空间点，未删困难行|
|是否使用GT选算法|否；全部优化SHA冻结后才读原生GT，核位置与中心门槛仅用拟合观测|

本轮不是直径测量，ARE/直径MAE等NOT_EVALUABLE；曲面中位绝对/MAE/p95/最大完整提供。没有GPU、DXY修改、Gate B/C/D、其他息肉、超参搜索或更复杂模型。**完成后停止，等待人工审核。**
'''
    (R/'TECHNICAL_REPORT.md').write_text(text)
    (R/'FAILURE_LEDGER.md').write_text('''# 失败与限制记录

|ID|观察|处置|
|---|---|---|
|S1-BUDGET|六参500次用满，仍有既有有限探针下降|保留最后迭代与未收敛标记，不扩预算或挑更优中间轮|
|S2-NOSIGNAL|两核幅值小、关掉核实际loss反而更低|中心不释放，S3 NOT_TRIGGERED，非数值硬失败或漏跑|
|GEO-INCONSISTENT|Mask/Chamfer改善但差异体积和质心误差恶化|不宣称稳定三维恢复，不用单一漂亮指标制造PASS|
|Z-BOUND|全局ΔZ贴近预登记下界，预测有GT范围外体积|只作后验诊断，不根据GT抬高中心、改边界或加地板先验|
|SUPPORT|大部分较大GT误差在两核支撑外|记录残差定位的限制，不用GT重选核或加核|
|LOSS-DIAG|固定残差平方与实际Powell loss不同|梯度/有限差分分列，优化从未使用FixedResidual梯度|
|FIELD-SCALE|仿射字段非严格单位梯度SDF，系数不等于位移|零面/方向先核验，所有物理GT指标来自实际Mesh|
|SAMPLING|微小局部Chamfer变化含预测面积采样/三角化噪声|固定GT方向另列，不宣称微米级实质改善或统计显著|
|VOLUME|空间占据为固定Sobol积分代理，非精确布尔交集|同报封闭Mesh体积，差异体积不被Chamfer替代|
|CAUSALITY|S2全局仍开放，额外搜索预算与加核同时发生|固定最终参数分量只作诊断，不把总改善全归于核|
|SELF|非邻接BVH未检出不等于全部自交形式认证|邻接/退化情况限制保留，不改网格|
|SCOPE|只一个IIa、一条轨迹；未运行S3和Gate B/C/D|等待人工，不扩展模型或病例|
''')
    receipts=R/'run_receipts';receipts.mkdir(exist_ok=True)
    for name in ['S1_FIT','S2_FIT','KERNEL_SELECTION','P0_CHECKS','LOCAL_CHECKS','FINAL_PROBES','POSTERIOR']:
        path=R/'runtime'/(name+'.log')
        if path.exists():shutil.copyfile(path,receipts/(name+'.txt'))
    print('REPORT_COMPLETE',[(x['stage'],x['fit_IoU'],x['Chamfer_MAE_mm'],x['symmetric_difference_mm3'])for x in rows],flush=True)
if __name__=='__main__':main()
