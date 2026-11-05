"""Reporting only. Preserve both frozen prediction attempts and select the declared numerical repair as current implementation."""
from common import *
import shutil
S=R/'runs/VISIBILITY_ORDER_REPAIR_001'
def ff(x):return 'NOT_EVALUABLE'if x is None else f'{x:.6f}'
def main():
    summary=load(S/'metrics/SUMMARY.json');gtgeom=load(S/'metrics/virtual_GEOMETRY.json');realgeom=load(S/'metrics/real_GEOMETRY.json');off=load(R/'metrics/OFFICIAL_REPRODUCTION.json');officialgate=load(R/'metrics/OFFICIAL_GATE.json');diag=load(R/'metrics/NUMERICAL_STABILITY_DIAGNOSIS.json');paired=load(R/'metrics/PAIRED_REPAIR_DIAGNOSTICS.json');env=load(R/'assets_index/ENVIRONMENT.json');bl=load(S/'metrics/BLENDER_GEOMETRY_CHECK.json')
    for name in['Fig1_Official_Reproduction.png','Fig2_Ring_Occlusion_Audit.png','Fig3_Actual_Mesh_Comparison.png','Fig4_Training_And_Independent_Evaluation.png']:
        old=R/'figures/failed_soft_zbuf_attempt'/name;old.parent.mkdir(exist_ok=True)
        if not old.exists():shutil.copyfile(R/'figures'/name,old)
        shutil.copyfile(S/'figures'/name,R/'figures'/name)
    shutil.copyfile(S/'metrics/SUMMARY.csv',R/'metrics/FINAL_PAIRED_METRICS.csv')
    tablelines=['|场景/条件|拟合IoU|留出IoU|Chamfer MAE / p95 mm|差异体积代理 mm³|Mesh体积 mm³|','|---|---:|---:|---:|---:|---:|']
    for r in summary:
        if r['step']in[0,300]:tablelines.append('|%s/%s|%s|%s|%s / %s|%s|%s|'%(r['case'],r['arm'],ff(r['fit_IoU']),ff(r['holdout_IoU']),ff(r['Chamfer_MAE_mm']),ff(r['Chamfer_p95_mm']),ff(r['symmetric_difference_mm3']),ff(r['volume_mm3'])))
    rr=[r for r in paired['hidden_proxy']if r['case']=='real'];base=next(r for r in rr if r['arm']=='Baseline');aware=next(r for r in rr if r['arm']=='RingAware');red=(abs(base['Ring_hidden_mean_signed_outward_mm'])-abs(aware['Ring_hidden_mean_signed_outward_mm']))/abs(base['Ring_hidden_mean_signed_outward_mm'])
    realb=next(r for r in summary if r['case']=='real'and r['arm']=='Baseline'and r['step']==300);reala=next(r for r in summary if r['case']=='real'and r['arm']=='RingAware'and r['step']==300)
    vgb=next(r for r in gtgeom if r['arm']=='Baseline'and r['step']==300);vga=next(r for r in gtgeom if r['arm']=='RingAware'and r['step']==300)
    runs=[load(S/'metrics'/(name+'_'+arm+'_RUN.json'))for name in['virtual','real']for arm in['Baseline','RingAware']]
    report=['# PyTorch3D 官方复现与 Ring-Aware 最小对照', '',
    '**结论：官方复现、相机接入和修复后的共享Mesh优化可运行；Ring-Aware在真实G01减少了部分Ring后方收缩代理，但仍明显收缩，尚未证明真实三维恢复更准确。虚拟场景没有有效Ring遮挡，不能用它宣布遮挡保护成功。**', '',
    '原软zbuf反传运行发生严重数值失稳，完整保留。仅做一次基于自动微分/有限差分矛盾的隔离修复，改为逐轮重算离散深度次序；未改相机、Mask、初值、SGD、正则化或300步预算。下表与四张核心图均为该预先登记修复的同条件配对结果，不是从中间轮筛选。原失败另列。', '',
    '\n'.join(tablelines), '',
    '完整0/100/200/300指标：[FINAL_PAIRED_METRICS.csv](metrics/FINAL_PAIRED_METRICS.csv)。真实三维GT误差均为NaN/NOT_EVALUABLE；表中Mesh体积不是GT准确度。', '',
    '## 七项问题的明确回答', '',
    '1. **官方复现：成功。** [官方教程](https://pytorch3d.org/tutorials/fit_textured_mesh)轮廓部分20视角、ico_sphere(4)、2000次SGD，完整20视角软轮廓MSE %.6f→%.6f。全顶点梯度非零，实际Mesh更新，OBJ导出/重载顶点和面位级一致，官方bin_size=0独立20视角重渲染差0。'%(off['initial_full_silhouette_L2'],off['final_full_silhouette_L2']),
    '2. **虚拟和G01相机接入：成功，但不提升相机资格。** 全11视角P0的PyTorch3D/Open3D硬轮廓IoU均1.0；点投影最大误差<0.000025px，深度中位差<0.000004mm；虚拟native GT→Blender Mask IoU 0.999288–1.0。真实六相机仍全部INSUFFICIENT_EVIDENCE，仅条件研究入组。',
    '3. **两侧分类：可见证据位置合理，待人工审阅。** 真实ref08截面A/B=58/119，ref13=59/113，ref03=78/148；蓝色PP主要在下弧，橙色PB在上/侧弧。实际取样位置绘于Fig2。虚拟全部C，没有PP/PB邻接；A/B不是真实隐藏面标签。',
    '4. **确实进入损失并影响梯度。** 修复版对CAD在前片元取消错误负监督；A/B/D局部未知带在缺CAD时仍保护，不要求2D与CAD同时成立。可见Polyp正证据、C背景、CAD前方错误Mesh仍有官方轮廓梯度。完整神经网络未参与：参数为官方Mesh顶点，所有视角共享一个网格。离散前后次序本身无深度梯度，不声称平滑地沿zbuf修复深度。',
    '5. **减少部分收缩，但未解决。** 真实P0中65个“首次主体面、被CAD及真实Ring Mask遮挡”的固定顶点，沿同一P0法向的平均内缩代理从%.6f降至%.6fmm，约减少%.1f%%；两条件65/65仍内缩。总Mesh体积从858.919降至Baseline %.3f、Ring-Aware %.3fmm³，后者仍损失约39.9%%初始体积。这个P0材料位移代理不是实际组织误删GT。'%(abs(base['Ring_hidden_mean_signed_outward_mm']),abs(aware['Ring_hidden_mean_signed_outward_mm']),100*red,realb['volume_mm3'],reala['volume_mm3']),
    '6. **虚拟GT没有显示Ring-Aware实质优势。** 两条件Mask改善、平均Chamfer较P0下降，但差异体积较P0上升，表面出现锯齿；Ring-Aware与Baseline差异很小。虚拟6000个固定GT样本的Ring遮挡分母=0，隐藏面保护NOT_EVALUABLE。双向面积采样Chamfer的小变化还受预测面积抽样变化影响；固定GT→预测方向MAE分别%.6f/%.6fmm，差约%.6fmm，不据此宣称方法优劣。'%(vgb['GT_to_prediction_mm']['MAE'],vga['GT_to_prediction_mm']['MAE'],vgb['GT_to_prediction_mm']['MAE']-vga['GT_to_prediction_mm']['MAE']),
    '7. **可作为增加HERO观测约束的候选基线，尚不能直接验收三维准确性。** 单独Mask与官方Mesh正则仍会牺牲未观测几何。下一阶段若人工授权，值得验证真实几何约束能否保护已知表面；本轮没有添加HERO深度或跨视角对应，也不证明它们必然有效。', '',
    '## 官方复用与唯一项目改动', '',
    '官方PyTorch3D提交`%s`，上游源码git status保持干净；许可证与教程副本在upstream/。复用Meshes、MeshRasterizer、SoftSilhouetteShader、MeshRenderer、SGD训练循环和mesh_edge_loss、mesh_normal_consistency、uniform mesh_laplacian_smoothing。没有新网络、优化器、HERO损失、后处理或顶点筛选。官方控制只不运行纹理/RGB阶段。'%load(R/'config/FROZEN.json')['official_commit'], '',
    '项目使用320×180、sigma=1e-4、faces_per_pixel=50，每步相同两个随机拟合视角、SGD(lr=1,momentum=.9)，silhouette=1、edge=1、normal=.01、Laplacian=1。每病例从同一P0归一化中心和等比例尺度得到网络坐标，相机和Ring同变换，输出恢复毫米。旋转/相机/实体CAD不学习。Mesh所有原始顶点可变，共享一个网格，不是每视角重建拼接。', '',
    '真实GP_Ip_12.0mm_closed_R10_single_refY/video004：FIT ref08/ref13/ref03，UPDATE_HOLDOUT growth_r04/r06/r10；原P0使用过其他视角，留出只针对本轮更新，不是初始化独立验证。虚拟IIa6.5：FIT obs01/03/05，HOLDOUT obs00/04，同一原生静止Blender目标、同一独立Gate A P0。没有重生成目标数据或混入video005。', '',
    '官方[cameras_from_opencv_projection](https://pytorch3d.readthedocs.io/en/latest/modules/utils.html)适配原OpenCV c2w。明确整数像素中心到半整数光栅中心的+.5主点转换，resize通过同一个中心仿射；不是改动冻结K。原生Mask用于正式统一评价，缩小标签的栅格边缘差异另记。', '',
    'Ring截面只只读提取DXY smooth_normal/beyond纯函数，宽度自适应出口、双侧邻接及邻截面池化；不运行P/Q，不迁移主体拟合。A强遮挡、B可能遮挡、C无直接延伸证据、D未知。仅局部Ring邻近带的未知负证据被放宽，所有可见Polyp正证据保留；不是排除全部Ring或背景。CAD前方冲突仍有损失和轮廓梯度，CAD/二维证据采用互补通道。', '',
    '## 初版失败与隔离修复', '',
    '初版协议使用连续sigmoid深度门控。真实ref13实际zbuf反传范数2.58×10¹³，最大顶点自动微分约−1.40×10¹³，而两档有限差分仅约−1.35×10⁻⁴/−1.63×10⁻⁴。原距离轮廓路径梯度约0.00887。首步最大位移约5.9×10¹³mm，最终几何无物理意义；有限但非零的梯度检查不足以证明正确。原GRADIENT_GATE的true保留，补充审计明确推翻其数值稳定性结论。见[NUMERICAL_STABILITY_DIAGNOSIS.json](metrics/NUMERICAL_STABILITY_DIAGNOSIS.json)。', '',
    '原local_results/{virtual,real}和metrics/SUMMARY属于失败初版，不覆盖、删除或改写。初版的真实Ring-Aware巨大体积、投影覆盖和碰撞阴性都不具有有效物理解释，不纳入最终有效几何成功率。原图另存figures/failed_soft_zbuf_attempt。', '',
    '一次修复只改变Ring组件：离散CAD/主体深度次序每轮重算，按前后片元组合官方软轮廓概率，不对zbuf次序反传。没有梯度裁剪、换学习率、换网络、增HERO或选GT更好轮次。正式修复配对两条件仍各300步，并从同一P0重新执行。真实三个参考全顶点Ring-Aware梯度范数0.01049/0.01023/0.02072，正常运行至终点。所有新预测先另行冻结，再做该次GT三维评价。旧失败的GT评价已存在，修复动因只来自数值Jacobian矛盾，不以GT调整规则。', '',
    '原版优化前遮挡图已生成并检查，复用其不变的分类、相机和CAD证据；修复版逐像素权重图因缺少只读截面元数据副本而在运行后补生成，未重跑优化或改变输入。该时序限制如实记录于[REPAIR_AUDIT_PROVENANCE.json](metrics/REPAIR_AUDIT_PROVENANCE.json)。它不是新的独立人工批准门禁。', '',
    '另两项工程问题：9位OBJ序列化/默认CUDA粗分箱重复渲染差异，以及密集P0分箱容量溢出。原失败保留；OBJ改为16位并与源float32逐位核对，导出审计使用官方bin_size=0，原最大像素阈值.001不变。项目分箱容量设为至少全部面数，原相机投影IoU门槛.98不变。没有调相机或用后处理让检查通过。', '',
    '## 几何性质、未观测区域与评价局限', '',
    '修复版P0/Baseline/Ring-Aware均封闭、同一连通分量；FCL未检出Ring碰撞，Blender独立未检出Ring三角面交集或非邻接自交。真实最终Ring最小距离Baseline %.6f、Ring-Aware %.6fmm。相邻退化面全形式自交证明不作声称。'%(next(r for r in realgeom if r['arm']=='Baseline'and r['step']==300)['Ring_min_distance_mm'],next(r for r in realgeom if r['arm']=='RingAware'and r['step']==300)['Ring_min_distance_mm']), '',
    '连续/闭合不等于真实：虚拟相邻法向角p95由8.39°升至15.75/15.84°，可见锯齿；真实由5.93°升至23.30/20.50°。没有额外平滑、补洞或删面。顶点沿P0法向位移与GT最近曲面Chamfer是不同诊断，表格明确标注，不混合为统一物理误差。', '',
    '“观测支持”按真实相机/Mask/首次主体命中/CAD深度对当前面分类；其余标为推断或未验证。颜色/面积不是三维GT。完整support数组保存在修复版local_results/eval。未知背面闭合来自共享封闭网格及正则先验，不是已观测真形状。', '',
    '覆盖率=预测首次可见主体命中原始Polyp像素/固定原始Polyp像素；未命中与FP同时报告。IoU分母是预测与原Mask并集，不能只凭覆盖高解释好。双向轮廓距离为像素空间最近边界距离。统一Open3D物理可见性对两条件评价，且保留原生全Mask分母，未知Ring不扩大Polyp分母。', '',
    'GT/预测各6000面积样本、固定种子，双向Chamfer报告MAE、中位、p95、最大；同一GT样本方向单列。独立2^18 Sobol域按P0固定extent padding，不根据GT或最终结果定域；差异、扩张、删除体积为代理积分，Mesh净体积另报。无GT测量直径，绝对相对直径误差NOT_EVALUABLE。', '',
    '## 环境、耗时与复现', '',
    '%s，%.2fGiB；torch%s、CUDA%s。PyTorch3D从源码独立编译约17分钟，未安装/下载无关模型或完整BundleSDF，GPU串行且没有终止其他任务。官方因序列化审计有两次同配置2000步控制，均保留；项目初版4×300步和一次修复4×300步也都保留，不隐去额外计算。'%(env['GPU'],env['GPU_total_bytes']/2**30,env['torch'],env['torch_cuda']), '',
    '|修复条件|更新数|实际秒|GPU峰值分配GiB|','|---|---:|---:|---:|']
    for r in runs:report.append('|%s/%s|%d|%.2f|%.3f|'%(r['case'],r['arm'],r['completed_steps'],r['elapsed_seconds'],r['peak_GPU_bytes']/2**30))
    report+=['', '复现和路径见[REPRODUCE.md](REPRODUCE.md)、[LOCAL_RESULTS.json](assets_index/LOCAL_RESULTS.json)。预注册d4686c8，首轮代码880cb68；最终代码/报告Git提交由交付信息列出。所有checkpoint和实际毫米Mesh保留本地，不上传大文件。', '',
    '## 固定审计表', '', '|审计项目|必须汇报|','|---|---|',
    '|目标组数|2场景：一个虚拟IIa、一个真实G01；官方cow为技术控制，不计物理病例数|',
    '|本算法独立成功|修复版2/2有独立数值输出，4/4条件各300步；不等于2/2几何正确|',
    '|本算法失败|初版真实G01 Ring-Aware数值失稳1/2场景；虚拟Ring遮挡有效分母0；真实GT=NaN/NOT_EVALUABLE，三维准确成功不宣称|',
    '|历史测量值回退|0；授权复用P0仅作初始Mesh，预测完全来自实际PyTorch3D更新|',
    '|失败组及具体原因|[FAILURE_LEDGER.md](FAILURE_LEDGER.md)，原始失败和修复均有图/日志/指标|',
    '|最终统计样本|2/2数值成功场景的配对；GT三维仅1/2，真实绝对精度NA；共同成功条件全列，未只挑好看结果|',
    '|是否使用GT选择算法|否；每次优化输出先冻结再评估；隔离数值修复由梯度矛盾触发，未用GT搜索位置、权重、阈值或checkpoint|', '',
    '四张核心图：[官方复现](figures/Fig1_Official_Reproduction.png)、[Ring证据](figures/Fig2_Ring_Occlusion_Audit.png)、[真实Mesh](figures/Fig3_Actual_Mesh_Comparison.png)、[阶段指标](figures/Fig4_Training_And_Independent_Evaluation.png)。完成后停止，等待人工审核，不自动加入HERO对应或升级正式主线。']
    (R/'TECHNICAL_REPORT.md').write_text('\n'.join(report)+'\n')
    ledger='''# 失败与限制记录

|编号|范围|原因与证据|处理|
|---|---|---|---|
|F01|官方首次导出|默认coarse-bin同Mesh重渲染也有像素波动；9位OBJ首检未通过，原2000步结果完整保留|16位OBJ和源float32逐位核对；官方bin_size=0独立重渲染差0，原.001阈值不变|
|F02|初次投影|密集P0分箱容量溢出，obs03 IoU .880，见PROJECTION_GATE_FAILED_BIN_CAPACITY|容量设至少全Mesh面数；原相机/Mask/几何和.98阈值不变，复核IoU均1|
|F03|真实G01初版Ring-Aware|zbuf反传1e8–1e13，与有限差分严重不符；首步非物理爆炸，原梯度门禁只有限/非零因此误判|全部原预测冻结，独立NUMERICAL_STABILITY_DIAGNOSIS推翻其稳定性结论；仅一次离散次序修复，保留两运行|
|F04|虚拟场景|所有Ring截面C，6000个GT样本中Ring遮挡分母0|隐藏面保护NOT_EVALUABLE；不移动Ring或制造成功|
|F05|真实相机|六相机仍INSUFFICIENT_EVIDENCE，P0用过其他视角|条件研究、仅更新阶段留出，不宣称真实绝对位姿认证|
|F06|真实GT|没有完整GT|三维准确度NaN/NOT_EVALUABLE，不用IoU宣称准确|
|F07|修复版几何|65个Ring隐藏P0材料点仍全部内缩；总量仍约损失40%，Mask正则并未充分保护主体|保留实际终点，不加新损失/调参/退回较好100步|
|F08|虚拟GT|IoU改善、平均Chamfer改善，但差异体积上升、Mesh出现锯齿|原始Mesh不平滑、不删面，不宣称真实三维成功|
|F09|修复权重审计时序|只读截面元数据副本缺失导致修复权重图首次生成失败|原始优化前分类/CAD图已检查；修复权重图运行后补生成，明确记录时序，不伪称再次人工批准|
|F10|数值复现|CUDA coarse-bin和其反向含局部重复差异，同种子两次Baseline并非位级一致|固定配置/状态/源哈希和完整日志；小差异不作统计显著性结论|

初版巨大体积不再具有物理体积意义，碰撞阴性也不能挽救失稳几何。初版GRADIENT_GATE.json保留原true，最终验收以新增数值稳定性审计及修复运行一起解释，不能只引用旧gate宣称通过。
'''
    (R/'FAILURE_LEDGER.md').write_text(ledger)
    result=dict(status='ENGINEERING_BASELINE_WORKS_AFTER_ONE_VISIBILITY_REPAIR_GEOMETRY_NOT_VALIDATED',official_reproduction=True,camera_projection=True,original_soft_depth_backward_failed=True,original_failure_retained=True,repaired_visibility='discrete forward ordering, no zbuf gradient; official silhouette vertex gradient retained',repaired_gradient_finite_and_stable=True,cases=2,steps_per_condition=300,real_holdout_IoU_baseline=realb['holdout_IoU'],real_holdout_IoU_aware=reala['holdout_IoU'],real_hidden_P0_material_mean_inward_baseline_mm=abs(base['Ring_hidden_mean_signed_outward_mm']),real_hidden_P0_material_mean_inward_aware_mm=abs(aware['Ring_hidden_mean_signed_outward_mm']),virtual_GT_Ring_occluded_N=0,three_dimensional_accuracy_claim=False,GT_HERO_or_measurement_fallback=0,new_HERO_loss=False,new_optimizer=False,stopped=True,mainline_promoted=False,current_result_root=str(S))
    save('metrics/FINAL_RESULT.json',result)
    save('assets_index/CURRENT_RESULT_INDEX.json',dict(current_root=str(S),original_failed_attempt_root=str(R/'local_results'),prediction_freeze_current=asset(S/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json'),prediction_freeze_original=asset(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json'),figures=[asset(R/'figures'/s)for s in['Fig1_Official_Reproduction.png','Fig2_Ring_Occlusion_Audit.png','Fig3_Actual_Mesh_Comparison.png','Fig4_Training_And_Independent_Evaluation.png']]))
    print(result,flush=True)
if __name__=='__main__':main()
