from common import *

def main():
 runs=load(R/'metrics/NINE_CASE_RESULTS.json');metrics=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');by={(x['case'],x['label']):x for x in metrics};native=load(R/'metrics/NATIVE_WITH_GEOMETRY.json');nb={(x['case'],x['label']):x for x in native};sources=load(R/'evaluation_only/GT_SOURCE_LOCK.json');gtvalid=load(R/'metrics/GT_VALIDITY.json');sums=load(R/'metrics/MEASUREMENT_SUMMARY.json');finalsum=next(x for x in sums if x['label']=='FINAL012');oldsum=next(x for x in sums if x['label']=='FINAL011');diag={(x['case'],x['label']):x for x in load(R/'metrics/BASE_AND_SURFACE_DIAGNOSTICS.json')};names=load(R/'config/PROTOCOL.json')['cases'];accepted=sum(x.get('accepted',0)for x in runs);attempts=sum(x.get('attempts',0)for x in runs);stopped=[x['case']for x in runs if x['status']!='ACCEPTED_TARGET_REACHED'];seconds=sum(x.get('seconds',0)for x in runs);case={x['name']:x for x in load(R/'config/CASE_LOCK.json')};num=[];evalrows=[];failure=[]
 def fmt(v,places=3):return 'NOT_EVALUABLE'if v is None else f'{v:.{places}f}'
 for x in runs:
  n=x['case'];i=nb[n,'FINAL011'];f=nb[n,'FINAL012'];g=by[n,'FINAL012'];d=diag[n,'FINAL012'];num.append(f"|{n} {case[n]['morphology']}|{x['accepted']} / {x['attempts']}|{x['maximum_displacement_mm']:.6f}|{i['FIT_IoU']:.3f} → {f['FIT_IoU']:.3f}|{i['HOLDOUT_IoU']:.3f} → {f['HOLDOUT_IoU']:.3f}|{i['FIT_fixed_depth_cost']:.3f} → {f['FIT_fixed_depth_cost']:.3f}|{i['FIT_depth_coverage']:.3f} → {f['FIT_depth_coverage']:.3f}|{x['Ring_pairs_initial']} → {x['Ring_pairs_final']}|{x['seconds']:.1f}|")
  evalrows.append(f"|{n}|{g['Dxy_GT_mm']:.3f}|{g['Dxy_pred_mm']:.3f}|{100*g['Dxy_relative_error']:.2f}%|{g['height_max_GT_mm']:.3f} / {g['height_max_pred_mm']:.3f}|{g['H95_GT_mm']:.3f} / {d['area_uniform_whole_solid_H95_mm']:.3f}|{d['minimum_author_base_height_mm']:+.3f}|{fmt(g['IoU_3D'])}|{fmt(g['occupancy_IoU_proxy'])}|{g['Chamfer_MAE_mm']:.3f}|")
  causes=sorted(x['rejection_counts'].items(),key=lambda p:p[1],reverse=True)[:3];failure.append(f"- **{n}**：{x['status']}，接受{x['accepted']}/{x['attempts']}；最大实际位移{x['maximum_displacement_mm']:.6f}mm，主要候选拒绝{causes}。留出IoU变化{f['HOLDOUT_IoU']-i['HOLDOUT_IoU']:+.5f}，原始分母深度覆盖变化{f['FIT_depth_coverage']-i['FIT_depth_coverage']:+.5f}；CAD三角形相交对{x['Ring_pairs_initial']}→{x['Ring_pairs_final']}，自交检出{x['self_intersections_final']}。[原图/三阶段Mesh](figures/full/{n}_Three_Stage_Detail.png)。")
 gt_bad=[x['case']for x in gtvalid if not x.get('watertight',False)or x.get('GT_self_intersections_N')!=0];headline='''# TASK-E4-FREE-VERTEX-PYTORCH3D-012

本轮完成九例真实输入的统一自由顶点优化，结论为 **MIXED：自由表达与实际更新生效，但尚未证明三例Ip恢复了完整、方向可信的细柄，也未形成一致的三维改善。** 不替换正式主线，不追加轮廓权重、损失调参或其他路线。
'''
 report=headline+f'''
## 直接结果

- 九例均从逐位相同的011 FINAL独立开始，生成9/9末状态；合计{attempts}次提案、{accepted}次接受。只有G07/G05/G08达到300接受；其余{stopped}按预先冻结的连续80拒绝规则停止。数值接受不等于实质形态恢复。总优化循环{seconds:.1f}秒，含几何检查，不含GT配准与制图；逐例时间见下表。
- G01最大位移2.308mm，G02约0.656mm，局部表达明显比011受限模型更活跃；G03约0.000341mm基本未动。G07/G05虽各接受300次，最大位移只有约0.019/0.0047mm，不能称完整局部几何恢复。
- 九例均未检出自交，面数与拓扑不变，七个截断模型均满足原基底半空间。G03/G07仍有CAD残余相交，独立三角形相交对20→22及34→38；另G05/G06仍各34对。守卫约束的是离散采样穿入和是否出现新布尔相交，**不是连续最大穿透的严格证明**，不能标成全部无碰撞。
- G01出现局部凸起并覆盖一部分原缺失轮廓，但尚非清晰、完整细柄，头部粗糙度增加；G02有局部头部调整，但未见可验证的细柄增长；G03原Mask中可见的柄仍明显未恢复。没有进行头/柄硬分割，也没有借历史结果填补。

## 输入、方法与冻结

预注册提交`2e3ead1`，见[协议](01_PROTOCOL.md)和[输入回执](02_INPUT_RECEIPT.md)。唯一新表达是主体逐顶点XYZ毫米位移，约1683–1926独立坐标自由度；不是谱系数，也不是新神经网络。截断边界仅限制法向位移为零，推断底盖中心随边界移动，底盖面不参加Mask/深度。其余观测、三拟合/既有留出视角、Ring-Aware、HERO原生ID/边界权重/同视角点对均沿用011。类型只分组展示。

轮廓权重不变，绝对/相对深度各0.01；边长和初始Laplacian相对本轮011 FINAL，法向为既有相邻面一致性加初始方向守卫，未观测位移先验保持弱约束。无跨视角HERO一致性损失、相机优化、SDF或新模型。Adam0.02、8次回缩、精确状态恢复和统一纯梯度备选；旧低维接触QP不扩展到上千维。实际mm信赖域及0.25D总位移范围仍保留，因此这也不是无边界、无正则的任意形变能力上限测试。

011已知G02严格跨进程轮廓重放问题未在本轮宣称修复；本轮不开展额外优化器审计，不因结果差改容差。每例保存实际达到的接受里程碑及最后状态，不挑最好checkpoint；未达到200/300不生成伪造Mesh。GPU为原RTX3060 Laptop 6GiB，使用已有官方PyTorch3D源码，无大型依赖下载。

## 原始相机下的更新结果

|病例|接受 / 提案|最大初值位移mm|FIT IoU|HOLDOUT IoU|原始固定分母深度代价|深度覆盖|Blender CAD相交对 初→末|优化秒数|
|---|---|---|---|---|---|---|---|---|
{chr(10).join(num)}

深度为原始HERO观测代理而非GT；缺失保留9.5代价，报告原分母和命中。2D由原始冻结相机评价，刚性对齐不被单独应用于模型后投回旧相机；它在共同坐标变换下保持相同像素关系。

HOLDOUT沿用原有UPDATE_HOLDOUT身份，检验本轮更新；更早的P0/主体拟合可能已使用部分视角，不能宣称从未参与整个流程的严格独立验证。相机原有条件性资格仍保留，不因旧标签取消本轮病例。

## Ip柄部与局部形态

G01留出IoU约0.834→0.919，深度覆盖恢复到1.0，但原始模型存在的细柄未完整恢复。其相邻面角p95约6.10°→21.37°，新增一个>120°邻面角，说明局部折棱仍未避免；这不是检出自交或翻面，却不能称平滑真实改善。GT配准后Dxy误差0.444→0.205mm，而主表面Chamfer MAE反而0.350→0.362mm。

G02留出IoU约0.744→0.863，Dxy误差0.589→0.103mm、Chamfer约0.420→0.343mm，但Mesh仍呈薄冠和局部棱角；原基底约束与初始网格采样也限制向柄部的伸展。不能把这些改善直接认证为三维柄方向正确。G03几乎未更新，不能声称自由顶点已解决明显的缺柄。

[三例Ip专题](figures/Fig2_Three_Ip_Stalk_Review.png)提供完整Mask及固定旧残差区域放大；放大区域由011缺失轮廓确定，不是根据012好坏筛选。G01历史D仅作为[静态参考](figures/full/G01_Historical_Static_Reference.png)，在预测冻结后才读取；同Ring世界坐标核验一致，但历史初始化/监督协议不同，不作公平第三臂、不参与当前优化或定量排名。

## Ring尺度与原始Blender来源

九例输入本来就是毫米。R10从自身CAD几何测得约9.9999987mm，G07 R5约4.9999993mm，恢复比值接近1，实际应用系数全部为1，没有重复缩放。尺度在任何原始GT几何读取前锁定，见[RING尺度表](metrics/RING_SCALE_VALIDATION.csv)及SCALE_LOCK_BEFORE_GT。固定CAD尺度核验不是独立预测Ring尺寸。

九例均找到可追溯原始Blender来源，按物理组身份/目录或既有人工作证匹配，不按形状相似选模型。G04继续保留Is标签，但原始CAD为历史人工确认的IIa6.5命名别名；G07用同样有明确SHA绑定的Is14资产。原文件METRIC、scale_length=1.0，以米坐标乘1000转为GT毫米，不接触预测尺度。每例只有一个原始主体Mesh，未清理GT坏面，未按预测重建GT。

原始GT的自交/闭合检查中，{gt_bad}存在自交或非闭合限制。各例仍参与表面、Dxy与条件高度评价，严格实体IoU保留NaN。原始作者平面来自其世界XY方向及真实最低平面三角面，绝非Ring平面；它与真实部署组织基底的对应仍未被认证。

## After Ring-based Metric Recovery and 6-DoF Rigid Alignment

只在预测与尺度冻结后，对每个阶段独立采用24个固定正旋转初值的刚性ICP（with_scaling=False），固定多尺度阈值与预算。按对称配准残差选**评价变换**，不选择预测、不重训。所有R/t见[刚性参数](metrics/BLENDER_RIGID_ALIGNMENT.csv)及每个初值的残差表。det(R)=1、旋转正交，ICP尺度恒1。该评价允许消除未知部署姿态，不能冒称端到端相机或世界定位准确度。

主Dxy为同一作者基底方向上的投影最大Feret，不读取旧测量数，也不修改DXY。Hmax/H95为**条件作者基底高度**。下表H95对预测完整实体与GT完整实体采用同一个8192面积采样算子，灰色推断盖作为明确的模型假设计入，不混称真实可见组织准确度。另保留排除推断盖的主体H95、支持区/未知背面/底盖距离，避免不同表面定义混用；[统一高度表](metrics/REQUESTED_HEIGHT_METRICS.csv)列出完整实体H95、误差、相对误差和观测可参与面H95。GT自交/开口的病例这些量也只代表对原始CAD曲面的条件比较。

|病例|GT Dxy mm|012 Dxy mm|相对误差|GT / Pred Hmax mm（条件）|GT / Pred H95完整实体mm（条件）|预测最低点相对GT作者基底mm|严格3D IoU估计|占据估计/代理|主Chamfer MAE mm|
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(evalrows)}

**高度不能只看最高点。** G03虽然Hmax接近GT，但模型最低点仍高于作者基底约12.91mm，明显缺少下部；G01仍有约1.83mm基底间隙。G09条件Hmax仅约0.237mm、GT为1.0mm，且占据代理约0.117，不能被较小Dxy误差掩盖。原生基底合规不等于对齐后作者基底关系正确；负间隙也不等同违反原生冻结基底约束。详见[基底与完整表面诊断](metrics/BASE_AND_SURFACE_DIAGNOSTICS.csv)。

严格有效实体的体积IoU只能评价1/9（G01）；另4/9仅报告带推断底盖的占据代理，其余GT不满足实体条件。数字是131072个固定Sobol样本的占据估计，不是精确布尔体积，没有严谨置信区间；G01严格列与占据估计列是同一个估计，不是两个独立成功。高整体IoU可能由头部体积主导，不认证细柄恢复。

主Chamfer按双向面积采样的点到曲面距离，分别保留MAE/median/p95/max、预测→GT和GT→预测。预测面不包含推断底盖，但包含未观测背面，因此另列基于原相机证据的支持区、未知背面和盖距离。GT→预测覆盖完整原始GT，不只看已观察头部，不以模型外观判断真实新增面。

## 全体分母与配对统计

012的独立模型输出为9/9，CAD条件Dxy比较9/9：中位绝对相对误差 **{100*finalsum['Dxy_median_absolute_relative_error']:.2f}%**，MAE **{finalsum['Dxy_MAE_mm']:.3f}mm**，p95绝对误差 **{finalsum['Dxy_p95_absolute_error_mm']:.3f}mm**，最大误差 **{finalsum['Dxy_max_absolute_error_mm']:.3f}mm**。同九例011 FINAL对应中位相对误差{100*oldsum['Dxy_median_absolute_relative_error']:.2f}%、MAE{oldsum['Dxy_MAE_mm']:.3f}mm。完整逐组配对见[共同九例比较](metrics/PAIRED_011_012.csv)，对照为用户批准的011初始化，不包含历史融合结果或测量值回退。

这些是Ring尺度锁定、GT辅助刚性消姿后的CAD比较，不能直接写成临床Dxy/高度测量精度；真实部署基底和位姿误差没有被独立认证。数值输出覆盖率与测量正确率分开。模型局部表达能力、初值采样、形状保护、可见性分段和安全拒绝仍共同影响结果，本轮不足以归因单一因素或否定自由顶点路线。

## 固定审计表

|审计项目|必须汇报|
|---|---|
|目标组数|9个独立物理组，Ip/Is/IIa各3，始终给全体分母|
|本算法独立成功|9/9产生本轮末状态；条件CAD Dxy比较9/9，不等于9/9准确或细柄恢复|
|本算法失败|数值输出失败0/9，无预测回退；另有6例提前停滞，细柄未完整验证。严格IoU 8/9为NaN，真实部署高度精度NOT_EVALUABLE，条件高度另列；不把数值输出成功当作形态验收通过|
|历史测量值回退|0；没有读旧测量值补结果，011 FINAL只是明确批准的起点|
|失败组及具体原因|[逐例台账](FAILURE_LEDGER.md)，原始Mesh/拒绝示例/原图全保留|
|最终统计样本|Dxy条件比较9/9，共同配对9/9；严格IoU仅1/9、代理另4/9，不丢弃GT无效组|
|是否使用GT选择算法|否；PREOPT冻结先于训练，全部预测及Ring尺度冻结先于原始GT读取；ICP只作评价|

## 交付与停止

全部关键图、九例详细图、模型/checkpoint/对齐结果位置见[结果索引](RESULT_INDEX.md)，命令和恢复见[REPRODUCE](REPRODUCE.md)。[轻量模型包](review_models/README.md)同时提供三阶段PLY与012交互GLB供GitHub下载；PLY单位mm，GLB按格式标准仅转为m，精确NPZ/PT保持原毫米坐标。大文件保留本地并有SHA索引。原011、Ring-First、HERO、CAD、Mask和DXY未修改。

**本轮停止，等待人工审核；不自动追加新的轮廓距离/权重实验，不升级正式主线。**
'''
 (R/'TECHNICAL_REPORT.md').write_text(report)
 ledger='# 012失败与限制记录\n\n九例均有独立末状态；以下限制不通过删面、换病例、选最好checkpoint或修改评价标准隐藏。\n\n'+'\n'.join(failure)+f'''\n\nGT实体限制：{gt_bad}原始来源存在自交或非闭合，保留原始几何而非修复后制造IoU。严格IoU仅1/9，另外4例仅占据代理。\n\nG01头部粗糙度p95约6.10→21.37度，并有一个>120度邻面角；未检出自交不等于形态合理。G03几乎无更新且缺柄；G09条件高度和整体占据明显不足。G03/G07 CAD相交对数量小幅增加，不能把离散穿入代理受控称为严格连续非穿透证明。\n\n011已知严格轮廓重放问题继承为限制，没有改容差称PASS。Git早期HTTP2/分块推送失败后改用HTTP1.1与固定postBuffer传输，远端结果以最终ref实测核验；该问题没有改变任何科学输入或预测。\n\n所有接受里程碑与停止原因均原样保留；没有因达到300数值接受就声称形成有效细柄。\n'''
 (R/'FAILURE_LEDGER.md').write_text(ledger)
 index='''# 结果索引

核心图：

- [Figure1 九例三阶段](figures/Fig1_Nine_Free_Vertex_Overview.png)
- [Figure2 三例Ip柄部专题](figures/Fig2_Three_Ip_Stalk_Review.png)
- [Figure3 实际接受更新过程](figures/Fig3_Free_Vertex_Update_Process.png)
- [Figure4 Ring尺度与Blender刚性对齐](figures/Fig4_Ring_Scale_and_Blender_Alignment.png)
- [Figure5 定量结果](figures/Fig5_Quantitative_Results.png)

[输入回执](02_INPUT_RECEIPT.md) · [原始GT来源/单位/算子](03_GT_SOURCE_AND_METRICS.md) · [轻量模型下载](review_models/README.md)

[G01历史静态参考](figures/full/G01_Historical_Static_Reference.png)仅展示，没有参与优化或输出替换。

九例完整原图与三阶段Mesh：

'''+ '\n'.join('- ['+n+'](figures/full/'+n+'_Three_Stage_Detail.png)'for n in names)+f'''

本地绝对根目录：`{R}`。

每例起点`inputs/Gxx/INITIAL.npz`为011 FINAL；`C_011.npz`为011 C。新结果`local_results/Gxx/FINAL.npz/.pt/FINAL_mm.ply`，实际达到的ACCEPTED_N与提案检查点同目录。V均为原生世界毫米，F_solid中的inferred_base_faces为单独推断底盖，不能当真实可见面。

`local_results/metric/Gxx`为CAD尺度锁定后几何，`local_results/aligned/Gxx`为仅评价用6DoF派生几何；不覆盖原预测或相机。GT主体和原始来源/单位记录在evaluation_only，不上传大型原始场景。

原始相机指标`NATIVE_WITH_GEOMETRY`/`PER_VIEW_METRICS`，配准矩阵`BLENDER_RIGID_ALIGNMENT`，Dxy/高度/IoU/表面距离`BLENDER_GEOMETRIC_METRICS`，原始GT有效性`GT_VALIDITY`，分母/误差统计`MEASUREMENT_SUMMARY`，共同九例配对`PAIRED_011_012`，原生/作者基底差异与含盖诊断`BASE_AND_SURFACE_DIAGNOSTICS`。

可直接下载[轻量审阅模型](review_models/README.md)：九例各含C011、FINAL011、FINAL012毫米PLY、黑色Ring CAD及012带Ring的交互GLB（标准米单位）。MODEL_SEMANTICS记录底盖面ID与原始NPZ来源。精确模型/checkpoint和完整候选日志仍在本地，路径/大小/SHA见assets_index/LOCAL_RESULTS_INDEX.json；大型原始模型/视频/环境不上传，完整重跑需要按索引恢复本地数据。
'''
 (R/'RESULT_INDEX.md').write_text(index)
 save('metrics/RESULT.json',dict(task='TASK-E4-FREE-VERTEX-PYTORCH3D-012',status='AWAITING_HUMAN_REVIEW',conclusion='MIXED',target_N=9,independent_output_N=9,total_proposals=attempts,total_accepted=accepted,target300_reached_N=3,stagnation_cases=stopped,GT_matched_N=9,Dxy_summary=finalsum,strict_solid_IoU_N=1,occupancy_proxy_only_N=4,historical_measurement_fallback_N=0,GT_training_read=False,GT_used_for_rigid_evaluation=True,scale_changed_by_ICP=False,formal_mainline_replaced=False,stalk_complete_restoration='NOT_DEMONSTRATED',original011_untouched=True))
 print('REPORT_AND_INDEX_WRITTEN')

if __name__=='__main__':main()
