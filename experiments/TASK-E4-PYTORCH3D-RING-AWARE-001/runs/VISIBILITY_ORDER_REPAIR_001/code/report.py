from common import *
def f(x,n=6):return 'NOT_EVALUABLE'if x is None else f'{x:.{n}f}'
def main():
    off=load(R/'metrics/OFFICIAL_REPRODUCTION.json');export=load(R/'metrics/OFFICIAL_GATE.json');off['passed']=export['passed'];pro=load(R/'metrics/PROJECTION_GATE.json');grad=load(R/'metrics/GRADIENT_GATE.json');summary=load(R/'metrics/SUMMARY.json');blender=load(R/'metrics/BLENDER_GEOMETRY_CHECK.json');vg=load(R/'metrics/virtual_GEOMETRY.json');rg=load(R/'metrics/real_GEOMETRY.json');cfg=load(R/'config/FROZEN.json');env=load(R/'assets_index/ENVIRONMENT.json');audit=load(R/'metrics/OCCLUSION_AUDIT.json')
    tablelines=['|场景 / 最终阶段|FIT IoU|留出 IoU|Chamfer MAE / p95 mm|差异体积代理 mm³|Mesh体积 mm³|Ring穿透|','|---|---:|---:|---:|---:|---:|---|']
    for r in summary:
        if r['step']not in[0,300]:continue
        tablelines.append('|%s / %s|%s|%s|%s / %s|%s|%s|%s|'%(r['case'],r['arm'],f(r['fit_IoU']),f(r['holdout_IoU']),f(r['Chamfer_MAE_mm']),f(r['Chamfer_p95_mm']),f(r['symmetric_difference_mm3']),f(r['volume_mm3']),r['Ring_collision']))
    baseline=next(r for r in summary if r['case']=='virtual'and r['arm']=='Baseline'and r['step']==300);aware=next(r for r in summary if r['case']=='virtual'and r['arm']=='RingAware'and r['step']==300)
    gain=baseline['Chamfer_MAE_mm']-aware['Chamfer_MAE_mm'];diffvol=baseline['symmetric_difference_mm3']-aware['symmetric_difference_mm3']
    runs=[load(R/'metrics'/(name+'_'+arm+'_RUN.json'))for name in['virtual','real']for arm in['Baseline','RingAware']]
    lines=['# PyTorch3D 官方复现与 Ring-Aware 遮挡优化',
    '', '本轮只完成一个官方 cow 轮廓复现及两个固定病例的 Baseline/Ring-Aware 快速对照。最终预测来自各自实际更新后的同一共享 Mesh；没有 HERO 深度损失、跨视角几何对应、新优化器、重建结果回退或几何后处理。所有最终结果固定第300步；不按GT选择模型。',
    '', '## 直接结果', '', '\n'.join(tablelines), '',
    '虚拟GT为原生静止 Blender CAD；GT投影门禁独立运行，正式优化进程禁止读取GT。全部项目预测、配置、源码先冻结SHA，之后才读取GT作三维评价。相机投影门禁通过=%s；真实资格仍全部为 INSUFFICIENT_EVIDENCE，仅条件研究入组。真实无完整GT，上表三维准确度的缺失值是NOT_EVALUABLE。'%pro['passed'],
    '', '## 官方复现', '',
    '使用官方提交 `%s`，对应[fit_textured_mesh教程](https://pytorch3d.org/tutorials/fit_textured_mesh)。没有修改官方库源码。20个官方相机、128²、ico_sphere(4)、2000次SGD，lr=1、momentum=.9；轮廓L2、edge=1、normal=.01、uniform Laplacian=1。仅不执行未要求的纹理/RGB部分，目标软轮廓逐视角渲染、固定种子、OBJ精度16位用于复现审计。'%cfg['official_commit'],
    '', '20视角完整轮廓MSE %s → %s，首次全顶点梯度范数%s；默认CUDA分箱导出重载最大RGBA差%s；原失败保留。同Mesh重复渲染也有差异。顶点/面位级相同，官方bin_size=0独立审计二十视角差0，原.001阈值下通过，见OFFICIAL_GATE与EXACT_OBJ_RERENDER_AUDIT。最终复现门禁通过=%s，耗时%s秒。'%(f(off['initial_full_silhouette_L2']),f(off['final_full_silhouette_L2']),f(off['first_full_vertex_gradient']),f(off['OBJ_reload_max_rgba_error'],9),off['passed'],f(off['elapsed_seconds'],1)),
    '', '## 项目适配与相机', '',
    '复用官方 Meshes、MeshRasterizer、SoftSilhouetteShader、MeshRenderer、SGD及三项Mesh正则。项目唯一算法增量是Ring片元/像素损失；数据适配为固定毫米归一化、相机接口、已知像素resize和足够的coarse-bin容量。首次容量溢出失败保留；容量设为至少单Mesh全部面数，未改相机/Mask/几何或.98门槛，见ENGINEERING_REPAIRS.json。原生K/c2w不改写，使用官方[cameras_from_opencv_projection](https://pytorch3d.readthedocs.io/en/latest/modules/utils.html)，显式区分整数像素中心与PyTorch3D半整数像素中心。原生Blender标签单独验证，缩小标签的边缘离散差异不冒充相机错误。逐视角结果见[PROJECTION_GATE.csv](metrics/PROJECTION_GATE.csv)。',
    '', '虚拟 FIT=obs01/03/05、HOLDOUT=obs00/04；真实FIT=ref08/ref13/ref03、UPDATE_HOLDOUT=growth_r04/r06/r10。真实P0已经使用其他视角信息，留出仅指本轮Mesh更新阶段，不能宣称从初始化起独立验证。虚拟初值为Gate A独立Ring先验P0，非native GT字段或拟合结果。原P0/S1/S2全部保留。',
    '', '## Ring机制与梯度', '',
    '只从DXY只读提取smooth_normal和beyond两个纯截面函数；原文件SHA和commit见[DXY_READONLY_REFERENCE.json](assets_index/DXY_READONLY_REFERENCE.json)。不调用P/Q和主体拟合。原生Ring轮廓两侧最近非Ring出口、宽度自适应邻接取样、局部截面合并：PP=A、PB=B、BB=C、失败/混合=D。实际位置及取样点见Fig2与本地完整审计图。A/B/D只在局部Ring带放宽不确定负证据，Polyp正证据不屏蔽。C仍保留可见背景；不是全背景排除，也不对未知补假深度。',
    '', 'CAD硬深度固定，主体每个软片元按sigmoid((zCAD-zBody)/0.05mm)计算前后可见性，和官方sigmoid silhouette乘积结合。2D邻接及CAD单独都可提供保护，不采用双重AND门禁。CAD前方错误主体仍可得到损失/深度梯度；Ring不是永久loss空洞。控制实验与真实全顶点梯度见[GRADIENT_GATE.json](metrics/GRADIENT_GATE.json)，通过=%s。'%grad['passed'],
    '', '遮挡只消除错误负监督，不能消除原官方edge/Laplacian等正则对隐藏形状的作用；未观测几何仍可能收缩。预优化记录了轮廓项/正则项全参数梯度及一阶体积方向，实际非线性体积另测，不能将一阶诊断当优化轨迹。没有为了改善结果新增保护项。',
    '', '## 关键限制与结果解释', '',
    '固定IIa6.5场景Ring截面全部C类，缺乏真实PP/PB遮挡。该事实来自原目标Mask，不是为算法挑选的成功案例。虚拟GT被Ring遮挡的采样分母见[virtual_GEOMETRY.json](metrics/virtual_GEOMETRY.json)，若为0，则隐藏面保护=NOT_EVALUABLE，而不是零误删的成功。标量片元控制只证明损失机制，不能补足真实遮挡实验的统计证据。',
    '', '虚拟最终Ring-Aware相对Baseline：Chamfer MAE变化（基线减遮挡版）%s mm，差异体积代理变化%s mm³。正值表示该项改善，不保证所有指标同时改善，也不替代三维局部或碰撞检查。两者全部阶段原始指标保留，不依据输出增改预算。'%(f(gain,9),f(diffvol,9)),
    '', '真实G01没有完整GT。对Ring后方体积的保持、投影覆盖及轮廓位置可作现象观察，但无法认定真实隐藏组织恢复。真实连续、闭合、平滑只属几何性质；未知区域闭合属于网络外的网格先验推断，不是观测真值。',
    '', '## 独立几何审计与评价算子', '',
    '所有方法以相同原生640×360像素、相同固定全Polyp分母、相同Open3D首次可见表面/CAD次序评价；并记录命中、未命中、FP、轮廓双向距离及Ring前方冲突。覆盖率=预测可见主体命中Polyp像素数/原始Polyp像素数；IoU分母为预测和原Mask并集。轮廓MAE/p95是双向最近轮廓点的像素距离，不是毫米或GT几何误差。',
    '', 'GT/预测各6000个面积采样，固定种子，报告双向Chamfer MAE、中位、p95、最大；不是平方距离。2^18独立Sobol空间采样域由P0和固定extent padding定义，计算差异/扩张/删除体积代理；净Mesh体积另报。若出现自交，占据积分不再具有严格实体Boolean含义，必须结合自交失败记录解释。没有直径测量任务，绝对相对直径误差NOT_EVALUABLE，不套用其他路线直径。',
    '', 'FCL三维Ring碰撞、Open3D内部顶点和最小间隙独立检查，Blender BVH再核对Ring三角面交集和非邻接自交；相邻/退化面的全形式证明不作声称。[BLENDER_GEOMETRY_CHECK.json](metrics/BLENDER_GEOMETRY_CHECK.json)完整保留阴性与阳性结果。所有原始Mesh保留，没有删除碰撞面。',
    '', '## 七项验收回答', '',
    '1. 官方轮廓Mesh Fitting是否复现：%s；不是只导入网络或用其他渲染器代称。'%('是'if off['passed']else'未通过全部工程门槛'),
    '2. 虚拟/G01相机接入：逐视角投影与CAD门禁%s；保留真实条件资格。'%('通过'if pro['passed']else'有失败'),
    '3. 两侧分类：图中实际取样和邻接关系符合本轮可见Mask；仍需人工审阅，不能代替隐藏GT认证。',
    '4. 是否进入loss：是，实际全参数及前/后/未知/C背景梯度控制有记录；不是只生成分类图。',
    '5. 是否减少错误收缩：须看两病例体积、局部与Mask；本虚拟遮挡分母不足，真实无GT，不据可视化宣布普遍成功。',
    '6. 虚拟GT是否改善：上表逐指标给出，不以IoU替代；遮挡版相对基线Chamfer变化%s mm、差异体积变化%s mm³。'%(f(gain,9),f(diffvol,9)),
    '7. 是否值得加HERO对应：已有可运行官方基线及梯度通道可作为下一阶段候选；本轮没有验证HERO对应。应先人工验收本次几何/碰撞失败及遮挡证据限制，再另行授权，不自动增加新损失。',
    '', '## 固定审计表', '',
    '|审计项目|必须汇报|','|---|---|',
    '|目标组数|2场景：1虚拟IIa+1真实G01；另1官方cow技术控制，不计物理病例成功率|',
    '|本算法独立成功|2/2数值输出，每场景2条件、各300步；数值输出不等于三维正确|',
    '|本算法失败|三维证据不足或几何失败逐项见FAILURE_LEDGER；真实GT=NaN/NOT_EVALUABLE，不能算准确成功|',
    '|历史测量值回退|0；授权复用P0作初值，最终输出为实际PyTorch3D更新Mesh，不是历史测量补齐|',
    '|失败组及具体原因|见[FAILURE_LEDGER.md](FAILURE_LEDGER.md)、逐视角CSV和原始图片|',
    '|最终统计样本|同一2/2数值成功场景的配对比较；GT三维仅1/2虚拟场景，遮挡有效分母单列|',
    '|是否使用GT选择算法|否；GT投影门禁为独立进程，正式优化封禁GT读取；预测/源码SHA先冻结，再后验评估，不按GT挑中间轮|',
    '', '## 环境与交付', '',
    '本地 %s，显存%s GiB；torch%s / CUDA%s，官方扩展本地独立编译，无新模型或完整BundleSDF。环境、输入身份、官方源码、冻结证据和恢复索引分别位于assets_index/。'%(env['GPU'],f(env['GPU_total_bytes']/2**30,2),env['torch'],env['torch_cuda']),
    '', '|场景/条件|优化步|秒|峰值分配GiB|OBJ重载渲染差|','|---|---:|---:|---:|---:|']
    for rr in runs:lines.append('|%s/%s|%d|%s|%s|%s|'%(rr['case'],rr['arm'],rr['completed_steps'],f(rr['elapsed_seconds'],1),f(rr['peak_GPU_bytes']/2**30,3),f(rr['OBJ_reload_max_alpha_error'],9)))
    lines += ['', '四张核心图：[官方复现](figures/Fig1_Official_Reproduction.png)、[遮挡位置审计](figures/Fig2_Ring_Occlusion_Audit.png)、[实际Mesh](figures/Fig3_Actual_Mesh_Comparison.png)、[训练与独立评价](figures/Fig4_Training_And_Independent_Evaluation.png)。完整相机投影图、本地Mesh和checkpoint见[REPRODUCE.md](REPRODUCE.md)及[LOCAL_RESULTS.json](assets_index/LOCAL_RESULTS.json)。', '', '本轮完成后停止，等待人工确认；不升级正式主线、不增加HERO对应、不推进其他Gate。']
    (R/'TECHNICAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    failures=[dict(id='F01',case='real',cause='Six frozen cameras INSUFFICIENT_EVIDENCE; conditional research only',evidence='inputs/real/CASE.json'),dict(id='F02',case='virtual',cause='Fixed scene lacks Ring PP/PB contact; no meaningful hidden-surface protection inference if hidden GT denominator=0',evidence='metrics/RING_SIDES_COUNTS.csv'),dict(id='F03',case='real',cause='No complete GT; hidden-surface accuracy NOT_EVALUABLE',evidence='metrics/real_GEOMETRY.json'),dict(id='F04',case='both',cause='Original mesh priors remain active in hidden region; masking negative loss alone is no full geometry-preservation guarantee',evidence='metrics/FULL_VERTEX_GRADIENTS.csv')]
    for rr in blender:
        if rr['Ring_intersecting_triangle_pair_N']or rr['nonadjacent_self_intersection_pair_N']:failures.append(dict(id='GEOMETRY_'+rr['case']+'_'+rr['arm'],case=rr['case'],cause='Raw endpoint geometry intersections',details=rr,evidence='metrics/BLENDER_GEOMETRY_CHECK.json'))
    for g in vg+rg:
        if not g['watertight']or g['components']!=1 or g['Ring_collision']or g.get('outside_integration_domain_vertices',0)>0:failures.append(dict(id='STAGE_'+g['case']+'_'+g['arm']+'_'+str(g['step']),case=g['case'],cause='Raw stage geometry safety/integration-domain condition failed',details=g,evidence='metrics/'+g['case']+'_GEOMETRY.json'))
    save('metrics/FAILURES.json',failures)
    fl=['# 失败与限制记录','','所有原始结果保留；不修复后重评、不删掉困难条件。','', '|编号|范围|原因|证据|','|---|---|---|---|']
    for e in failures:fl.append('|%s|%s|%s|[%s](%s)|'%(e['id'],e['case'],e['cause'],e['evidence'],e['evidence']))
    fl+=['','PyTorch3D源码环境从零独立编译；编译警告保留本地日志，未修改官方源码消除警告。若有投影/依赖接线错误，修复记录另外附后，不通过更改验收阈值制造PASS。','', '实际几何变坏不触发重启、调权或选择其他中间结果。300步仅快速验证预算，非充分优化科学验收。']
    (R/'FAILURE_LEDGER.md').write_text('\n'.join(fl)+'\n')
    save('metrics/RESULT.json',dict(status='COMPLETED_CONTROLLED_PYTORCH3D_RING_AWARE_PILOT',official_reproduction_pass=off['passed'],projection_pass=pro['passed'],gradient_pass=grad['passed'],numeric_cases=2,target_cases=2,formal_camera_certification=False,virtual_Chamfer_improvement_vs_baseline_mm=gain,virtual_difference_volume_improvement_vs_baseline_mm3=diffvol,three_dimensional_scientific_success='NOT_ESTABLISHED_BY_THIS_PILOT',no_HERO_loss=True,no_new_optimizer=True,GT_model_selection=False,stopped_for_human_review=True))
    print('Report generated; review final figures and numerical outcomes before delivery',flush=True)
if __name__=='__main__':main()
