from common import *
def f(x,n=4):return 'NA'if x is None else f'{x:.{n}f}'
def main():
    ends=load(R/'metrics/ENDPOINTS.json');faults=load(R/'metrics/EXACT_GEOMETRY_DIAGNOSTICS.json');fair=load(R/'metrics/FAIRNESS.json');gate=load(R/'metrics/PREFLIGHT.json');diag=load(R/'metrics/POSTERIOR_CAUSE_DIAGNOSIS.json');rows=[]
    def row(name,arm):return next(r for r in ends if r['case']==name and r['arm']==arm)
    def fail(name,arm):return next(r for r in faults if r['case']==name and r['arm']==arm)
    lines=['# 渐进形变与HERO深度：一次固定预算最小验证', '',
    '**结论：形状保护有效缓解真实G01收缩；本轮渐进方案未稳定改善三维形状；HERO提供了有效深度梯度，但所有新增条件都未通过最终几何门禁。** A直接复用上轮数值修复版，未重复优化。B/C/D各病例各300次SGD更新，完整保留结果，没有后处理、选优中间轮或追加调参。', '',
    '## 五个问题', '',
    '1. **形状保护能否避免失真：部分有效。** 真实B体积/P0由A的60.1%改善至100.4%，留出IoU从0.8961升至0.9073，Ring隐藏P0顶点平均内缩由0.899mm减至0.006mm。但B仍有约0.0055mm穿环；虚拟B粗糙度及自交比A更差，不能称统一解决。',
    '2. **渐进释放是否更好：本配置没有证据支持。** 真实C的IoU和HERO残差均不优于B；虚拟C虽留出IoU高达0.9020，Chamfer及差异占据代理却更差、体积约为P0的2.10倍。仅六参数阶段100步时已膨胀2.12倍，问题并非都由后续自由顶点造成。全局参数采用相同SGD但聚合梯度/尺度与局部不同，其收敛动态也未隔离；真实D整体阶段出现明显振荡，不能声称六参数阶段已收敛。不能把失败唯一归因于表示。',
    '3. **HERO是否提供额外有效约束：是，但非完整验收。** 真实D相对C，拟合HERO条件MAE 0.777→0.335mm，留出0.950→0.627mm；固定分母深度损失也降低，深度命中率未降低。但Mask留出覆盖从91.569%降至91.477%，Ring穿透增大至约0.0533mm。虚拟D为理想GT深度上限；较C降低曲面误差，但体积仍约1.95倍，且Mask/深度覆盖下降，记录为潜在退化。',
    '4. **保留与停止：** A保留为冻结对照；B的相对形状保护和D的深度适配保留为模块候选；停止将当前C配置作为默认策略，不推广或继续本轮训练。B/C/D完整几何结果均不发布为合格重建，需先解决非穿透和局部自交。',
    '5. **下一步路线：优先保留PyTorch3D作有限几何约束验证，暂不转SDFStudio。** 目前证据指向目标、可见性不可辨识与几何可行性缺口；尚不足以据此否定渲染框架。SDFStudio是[神经隐式重建框架](https://github.com/autonomousvision/sdfstudio)，本轮没有同预算竞争实验，不能假定换框架会自动修复这些缺口。本轮未安装或实施SDFStudio/BundleSDF，下一步须另行授权。', '',
    '## 固定终点：虚拟IIa', '',
    '|条件|拟合/留出IoU|Chamfer MAE mm|差异占据代理 mm³*|体积/P0|法向角p95°|确认自交面对|','|---|---:|---:|---:|---:|---:|---:|']
    for arm in['P0','A','B','C','D']:
        r=row('virtual',arm);b=fail('virtual',arm);lines.append('|%s|%s / %s|%s|%s|%s|%s|%d|'%(arm,f(r['fit_IoU']),f(r['holdout_IoU']),f(r['Chamfer_MAE_mm']),f(r['symmetric_difference_mm3'],3),f(r['volume_ratio_P0'],3),f(r['roughness_p95_deg'],2),b['FCL_self_pairs_confirmed']))
    lines+=['', '*B/C/D存在自交，差异占据及净体积仅为原算子的诊断代理，严格实体Boolean差异体积NOT_EVALUABLE；不能据代理声称合格三维恢复。全部Chamfer MAE/中位/p95/最大及独立采样域见CSV。虚拟D只使用由已知GT独立渲染的理想深度，不是HERO，不与真实数据合并统计。', '',
    '后验位置诊断：虚拟C/D最低Z约−0.961/−1.011mm，原生GT最低Z=0；该GT平面只用于冻结后诊断，没有作为训练地板。六参数整体阶段已同时伸长并下移主体，局部更新未恢复隐藏底面。理想可见首层深度改善，也不等于未观测底部正确。', '',
    '## 固定终点：真实G01_004', '',
    '|条件|拟合/留出IoU|体积/P0|HERO MAE拟合/留出 mm*|Ring最大顶点穿透 mm|','|---|---:|---:|---:|---:|']
    for arm in['P0','A','B','C','D']:
        r=row('real',arm);b=fail('real',arm);lines.append('|%s|%s / %s|%s|%s / %s|%s|'%(arm,f(r['fit_IoU']),f(r['holdout_IoU']),f(r['volume_ratio_P0'],3),f(r['fit_depth_conditional_MAE_mm'],3),f(r['holdout_depth_conditional_MAE_mm'],3),f(b['max_vertex_penetration_into_Ring_mm'],6)))
    lines+=['', '*条件MAE只计算实际合格命中，不能单独使用。真实固定观测：拟合1536、留出1533；真实留出只针对本轮更新，P0已用过其他视角信息。所有相机仍INSUFFICIENT_EVIDENCE，仅条件研究入组。真实无完整GT，绝对三维精度、GT直径误差均NaN/NOT_EVALUABLE。', '',
    '|C→D比较|拟合|留出|','|---|---:|---:|']
    for title,key,scale in [('HERO命中率%','depth_hit_rate',100),('固定分母深度损失','depth_fixed_loss',1),('原始Mask覆盖率%','coverage',100)]:
        c=row('real','C');d=row('real','D');lines.append('|%s|%s→%s|%s→%s|'%(title,f(c['fit_'+key]*scale,3),f(d['fit_'+key]*scale,3),f(c['holdout_'+key]*scale,3),f(d['holdout_'+key]*scale,3)))
    lines+=['', 'D的深度改善没有通过丢失HERO命中实现，但并非每个参考都优于B，逐参考结果全保留。Mask覆盖的小幅下降及更严重穿环仍记为失败证据。B主要保留了原P0体量与下部形态，C/D对下部和侧面发生实际改变；没有完整真实GT，不能把看似柄部的形状直接认作真实柄。Ring遮挡保护仍进入原损失，但遮挡不是三维非穿透约束。', '',
    '## 工程与公平性', '',
    '原修复版p3d.py逐字节复用，P0/A0/B0/C0/D0在同一FP32渲染表示下完全相同。B替换向零边长及绝对Laplacian为相对P0的边长/局部坐标MSE，并加固定无观测顶点软位移先验；无硬体积守恒。C/D为100步六参数平移/尺度+200步顶点，旋转与全部相机固定；阶段起点严格继承，SGD因参数改变重建并清空动量，故此策略包含阶段切换效应。所有新增条件同一300步、种子及双视角序列。', '',
    '真实深度逐点认证原生Pixel ID、352×640深度K与360×640 RGB K映射、清理valid及HERO原值：均一致；仅留出r10有3点因Mask/CAD次序排除。训练只调用三FIT参考深度；缓存构造加载了留出文件，但未用于优化损失、选模或停止，调用记录单独核验。B/C禁止观测解码，完整性SHA读取不进入目标。HERO模型、源深度、Mask、相机、Ring与DXY未修改。', '',
    '新增深度用离散首次面ID+FP64解析射线交点对实际顶点反传，不调用zbuf反向。六参考深度最大误差<0.00004mm，最大分量及全顶点方向FD通过。FP32微小联合扰动的首轮检查失败已保留，改用FP64验证同一扰动/同一阈值；没有改损失制造PASS。零步完整性检查接线错误也保留，未产生优化更新。', '',
    '深度采用固定lambda=.01、sigma=.5mm、截断Huber；未命中/遮挡/病态射线计同一封顶惩罚9.5，分母固定，不能靠删除命中降低该观测代价。常数不提供几何恢复梯度；Mask仍负责覆盖。没有权重搜索、参考校正、回退预测或后处理。', '',
    '所有六个新增条件数值完成，粗工程停止阈值未触发；几何门禁均失败：虚拟自交21/5/7对由Blender与FCL独立确认，真实Ring相交28/134/212对，最深顶点穿透如表。连续、封闭、漂亮轮廓均不等于合格重建。完整原始面、checkpoint和失败位置保留。', '',
    '## 固定审计表', '', '|审计项目|汇报|','|---|---|',
    '|目标组数|2场景×3新增条件=6运行；另有A的2个冻结对照|',
    '|本算法独立成功|6/6独立完成300次更新；数值成功不等于几何正确|',
    '|本算法失败|最终几何门禁0/6通过；虚拟三条件自交、真实三条件穿环；真实GT指标NaN|',
    '|历史测量值回退|0；仅授权的P0初值和A冻结对照，不作失败填充|',
    '|失败组及具体原因|[FAILURE_LEDGER.md](FAILURE_LEDGER.md)，逐病例/条件有几何查询、原始Mesh及图1红色面证据|',
    '|最终统计样本|完整2/2场景配对，6/6数值输出；GT三维仅1/2虚拟场景，且自交占据体积仅诊断|',
    '|是否使用GT选择算法|否；正式配置/源码先冻结；虚拟D仅使用已授权理想深度，预测冻结后才计算三维GT误差；固定最终300步|', '',
    '四张图：[原始Mesh对照](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)、[留出投影](figures/Fig2_Fixed_Holdout_Projection.png)、[阶段指标](figures/Fig3_Stage_Geometry_And_Depth.png)、[固定射线深度](figures/Fig4_Fixed_Ray_Depth_Residuals.png)。完整表见[ENDPOINTS.csv](metrics/ENDPOINTS.csv)、[DEPTH_EVALUATION.csv](metrics/DEPTH_EVALUATION.csv)、[复现说明](REPRODUCE.md)。本轮完成后停止，等待人工审查。']
    (R/'TECHNICAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    report=(R/'TECHNICAL_REPORT.md').read_text().replace('原修复版p3d.py逐字节复用，','原P0拓扑不同：虚拟9044顶点的DMTet网格，真实642顶点的保守椭球；代码与参数统一，不把跨场景差异都归于形态或HERO质量。原修复版p3d.py逐字节复用，')
    (R/'TECHNICAL_REPORT.md').write_text(report)
    failures=[]
    for name in['virtual','real']:
        for arm in['B','C','D']:
            fault=fail(name,arm);r=row(name,arm);reason='CONFIRMED_SELF_INTERSECTION'if name=='virtual'else'RING_PENETRATION';failures.append(dict(case=name,arm=arm,numerical_status='COMPLETED_300',geometry_status='FAIL',reason=reason,fault=fault,three_dimensional_accuracy='NOT_ESTABLISHED',GT_solid_difference_volume='NOT_EVALUABLE_SELF_INTERSECTION'if name=='virtual'else'NOT_EVALUABLE_NO_GT',evidence='figures/Fig1_P0_A_B_C_D_Actual_Meshes.png'))
    save('metrics/FAILURES.json',failures)
    fl=['# 失败记录','','没有为了终点指标改变规则、删面、平滑、换参考或回退到较好中间轮。','', '|病例|条件|失败|证据|','|---|---|---|---|']
    for x in failures:
        b=x['fault'];fl.append('|%s|%s|%s；Ring面对%d / 自交面对%d，顶点最深穿环%.6fmm|[几何复核](metrics/EXACT_GEOMETRY_DIAGNOSTICS.json)、[图1](figures/Fig1_P0_A_B_C_D_Actual_Meshes.png)|'%(x['case'],x['arm'],x['reason'],b['Blender_Ring_pair_N'],b['FCL_self_pairs_confirmed'],b['max_vertex_penetration_into_Ring_mm']))
    fl+=['','补充限制：','', '- 虚拟B虽曲面距离比A低，p95法向粗糙度更高且有自交；C/D更圆滑也不能掩盖约2倍体量与GT误差。', '- D相对C的Mask覆盖下降：虚拟留出约1.98个百分点，真实约0.092个百分点，均保留为潜在覆盖退化；未以更低深度误差宣布整体成功。', '- 真实HERO为相关模型观测，不是精确GT；未校正参考尺度、相机或原生深度。真实六相机INSUFFICIENT_EVIDENCE，更新留出并非初始化独立。', '- 虚拟D理想GT深度上限不能冒充HERO迁移成功，也未解决隐藏底面。', '- FP32联合方向FD初检失败记录见PREFLIGHT_FP32_FD_FAILED.json；FP64同条件通过。', '- 第一次B在SHA检查中被观测隔离hook提前拦截，实际optimizer.step=0；源代码/旧freeze/stdout保留于assets_index/pre_run_guard_failure和PREOPT_FREEZE_V1_GUARD_REJECT。修正hook安装时机后重新冻结，没有改目标/参数。', '- 后验公平性首次错误地比较FP32世界坐标往返与原始FP64数据，原日志保留；改为与A0及同一渲染表示逐位比较，另报最大浮点往返差。没有修改任何Mesh。', '', '本轮数值停止阈值用于非有限/爆炸候选，未把Ring/自交纳入优化目标；离线几何失败如实报告，不追调为PASS。']
    (R/'FAILURE_LEDGER.md').write_text('\n'.join(fl)+'\n')
    runs=[load(R/'metrics'/(name+'_'+arm+'_RUN.json'))for name in['virtual','real']for arm in['B','C','D']]
    table('metrics/RUNS.csv',[dict(case=x['case'],arm=x['arm'],steps=x['optimizer_steps'],elapsed_seconds=x['elapsed_seconds'],peak_GPU_GiB=x['peak_GPU_bytes']/2**30,status=x['status'])for x in runs])
    save('metrics/RESULT.json',dict(status='COMPLETED_FIXED_PILOT_GEOMETRY_GATE_FAILED',target_cases=2,new_runs=6,completed_300_step_runs=6,geometry_passed_runs=0,A_rerun=False,shape_protection='helps real shrinkage, does not prevent all distortion',progressive='not superior in this fixed configuration',depth='valid additional supervision; not sufficient geometry qualification',recommendation='retain B prior and D depth modules as candidates, stop promoting current C/D configurations; no framework migration this round',SDFStudio_implemented=False,GT_tuning=False,stopped_for_human_review=True,failures=failures))
    print('Report and failure ledger written',flush=True)
if __name__=='__main__':main()
