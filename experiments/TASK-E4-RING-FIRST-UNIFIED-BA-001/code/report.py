"""Report actual runs and failures; never promote a numerical output to pose truth."""
from ucommon import *
import shutil,platform,importlib.metadata

def md(rows,keys):
 def val(x):
  if x is None:return 'NOT_EVALUABLE / N/A'
  return ('%.6g'%x)if isinstance(x,float)else str(x).replace('|','/')
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+''.join('| '+' | '.join(val(r.get(k))for k in keys)+' |\n'for r in rows)
def write(name,text): (N/name).write_text(text.rstrip()+'\n')
def main():
 checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');scores=load(N/'metrics/FOUR_GROUP_POSE_SCORECARD.json');hero=load(N/'metrics/HERO_SURFACE_ALIGNMENT_SCORECARD.json');stage=load(N/'STAGE_DECISION.json');inputs=load(N/'metrics/ALL_NATIVE_RGB_IDENTITIES_VERIFIED.json');sensitivity=load(N/'metrics/PREREGISTERED_MULTISTART_COMPARISON.json');arcs=load(N/'metrics/ACTUAL_VISIBLE_ARC_QUALIFICATION.json');info=[load(N/'metrics'/(g+'_JOINT_INFORMATION.json'))for g in GROUPS];ranks=[dict(group=i['group'],joint_variables=i['joint_parameter_dimension'],camera_chart_variables=i['active_camera_chart_dimension'],XYZ_variables=i['active_XYZ_dimension'],data_residuals=i['data_residual_dimension'],camera_marginal_rank=i['marginal_camera_information_rank'],camera_marginal_dimension=i['marginal_camera_information_dimension'],condition_J=i['condition_J_proxy'],graph_components=len(i['graph_components']))for i in info]
 fit=[r for r in scores if r['role']=='FIT'];ht=[r for r in hero if r.get('scope')==('CROSS_VIDEO'if r['group']=='G01'else'SAME_VIDEO')];hs=[dict(group=r['group'],method=r['method'],scope=r['scope'],known_N=r['known_N'],fixed_N=r['fixed_N'],MAE_mm=r['depth_mm']['MAE'],median_mm=r['depth_mm']['median'],P95_mm=r['depth_mm']['p95'],support_pm05=r['support_fraction_fixed'],front=r['front_fraction_fixed'],deeper_possible_occlusion=r['behind_possible_occlusion_fraction_fixed'],UNKNOWN=r['unknown_fraction_fixed'])for r in ht]
 runs=[]
 for g in GROUPS:
  r=load(N/'results'/g/'B3/FINAL.json');tr=load(N/'optimization'/g/'B3/TRACE.json');runs.append(dict(group=g,initial_full_cost=r['initial_loss'],final_full_cost=r['loss'],outer_accepted=r['accepted_outer'],outer_attempted=r['outer_iterations'],seconds=r['seconds'],Ceres_LM_iterations=sum(z['Ceres']['num_successful_steps']+z['Ceres']['num_unsuccessful_steps']for z in tr),Ceres_unsuccessful=sum(z['Ceres']['num_unsuccessful_steps']for z in tr),last_termination=tr[-1]['Ceres']['termination_type'],XYZ_N=len(r['X'])))
 table('metrics/ACTUAL_JOINT_SOLVER_COUNTS.csv',runs);save('metrics/ACTUAL_JOINT_SOLVER_COUNTS.json',runs);table('metrics/MARGINALIZED_CAMERA_INFORMATION_SUMMARY.csv',ranks)
 audit='''
| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；98 canonical视角=81FIT+17HOLDOUT。G01含004/005；其他三组只有004 |
| 本算法独立成功 | B1实际76个独立局部求解，另5个参考相机受保护；B2仅G01一个共享SE(3)求解；B3四个真实联合问题，76个五维局部相机块+一个六维H+1377个XYZ，数值输出不是绝对精度认证 |
| 本算法失败 | 无用旧位姿填充的失败预测；B4四组NOT_RUN，照片12/12 NOT_RUN；初次PyCeres冷调用崩溃保留，显式Jacobian预求值后实际组级运行完成；独立RGB科学可信性尚未建立（不是当前严重数值阈值FAIL） |
| 历史测量值回退 | 0；B0/参考相机/HOLDOUT是预登记对照或规范，不冒充新恢复结果。B2不适用的三组保持NaN/N/A，不复制B0 |
| 失败组及具体原因 | G01初版005地图评价坐标错误已纠正；当前未超过冻结严重退化阈值，但四组独立RGB仍有权衡；B3四组留出极线代理均增大；G01/G06旧深度相容性下降。见FAILURE_LEDGER、逐视角/逐来源CSV和Figure4–8 |
| 最终统计样本 | 全部4组完整保留；按每指标真实视角、轨迹或source-target像素分母统计；不把重复源观测当独立物理样本。真实GT测量MAE/MedARE/尺寸p95为NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；协议/输入/源码在运行前冻结，候选在HERO之前冻结；HOLDOUT不进目标，不按HERO选路线，保留预登记主初值而非较低损失的敏感性候选 |
'''
 keys=['group','method','target_N','numeric_N','Ring_IoU','descriptor_HELD_reprojection_px_MAE_macro','descriptor_HELD_epipolar_px_MAE_macro','center_change_mm'];core=md(fit,keys);htable=md(hs,['group','method','scope','known_N','fixed_N','MAE_mm','median_mm','P95_mm','support_pm05','UNKNOWN'])
 summary='''# Ring-First Unified BA — 四组真实结果（2026-11-15）

**已完成四组B0/B1/B2/B3实际运行、冻结后的RGB/HERO评价、8张核心图、4组六视角图集和独立来源GLB。数值统一实现成功，独立几何验收未通过；B4与12照片暂停，不升级相机主线。**

本轮使用原始解析厚Torus，不使用021有缺口的CAD边筛选。原方程前向、真轴对称yaw、72项分量Jacobian、四组完整联合方向导数和真实Ceres LM下降均通过。Ceres在同一个问题中优化多台相机与共同XYZ；G01原生地图中的18对真实RGB同名轨迹合并为18个共同点，未用3D最近邻制造身份。

## 实际范围与实现忠实性

- 4组、98视角；81FIT/17HOLDOUT。共1728真实RGB轨迹、11315原始特征像素观测；其中1377条FIT轨迹参与联合问题。
- B0保留原RF，G01的005使用**预登记完整RoMa**建立004共同坐标，未使用021精修位姿作新路线预测。因此G01基线不能直接与上轮“021 B3共同坐标”的均值混排。
- B1为独立相机+固定RGB地标的SIFT局部对照；B2只在G01优化共享H，固定视频内部轨迹与点；其他三组B2明确N/A。
- B3为真实Ceres LM+DENSE_SCHUR，76个局部相机块、H005与1377个XYZ共同进入目标。**本轮L2局部块为五维SE(3)图表（固定局部原生world-z twist），不是每帧完整6DoF；继承已有逐帧yaw，H005的yaw由RGB约束。** 不声称重新解决了全部逐帧yaw/法向分支，完整局部6DoF属于尚未获几何门禁放行的B4。
- 使用PyCeres自定义代价，Torch64自动微分；没有调用Ceres C++AutoDiffCostFunction，没有运行COLMAP标准BA，也未重写LM/Schur。
- 形状、HERO、相机原件、CAD、DXY全部只读。底层分割/匹配缓存可溯源复用，无GT、无新HERO/主体训练、无融合/ICP。

## 四组主对照

'''+core+'''
IoU无量纲；RGB为640×360工作像素；相机中心mm。`numeric_N`包含按规范保留的参考相机，并不全是独立新求解。完整逐视角I/O MAE、median、P95、真实IoU交并集、轨迹观测数和HOLDOUT见原始CSV；HOLDOUT未进行局部拟合。G01共享H可影响005留出相机，其他组留出相机直接Ring投影不变，但其与FIT相机的相对极线误差可以改变。

四组B3的Ring IoU均提高，**但未拟合的RGB地标残差均增大**；G01从1.39961到2.11717px，增量0.71756px，**未超过**预登记max(1px,25%)。初版2.63816px混入“005原生独立地图没有跟随候选H重表达”的评价坐标错误，旧表及源码已单独保留，不能继续作为严重退化证据。四组HOLDOUT相对极线代理均变差。不能因目标下降或局部信息满秩就宣布新相机更真实。

## 原生HERO独立诊断

'''+htable+'''
G01显示跨视频；G03/G05/G06显示同视频。全部固定分母、共同命中/新增/丢失、±0.2/0.5/1mm敏感性、前方分歧/深层可能遮挡/CAD/UNKNOWN在完整表中。±0.5mm“支持”是相容性代理，不是真实表面准确率；来源累计面积不是唯一解剖表面积。

- G01 B2的条件MAE仅小幅变化0.82598→0.82450mm，同时支持比例0.3450→0.3255，不能称配准明显改善。
- G01 B3跨视频MAE0.85550mm、支持0.3079，没有改善残余错层。
- G03、G05的B3旧深度相容性代理改善；G06下降。所有局部相机更改统一标记`POSE_CHANGED_DEPTH_NOT_REINFERRED`，不能称新HERO深度精度。
- B2是005整体刚体变换，其视频内部几何不可能因此改善；CAD可见性分类的变化也不等于内部曲面修复。

## 决策

**保留B0正式冻结输入；B1/B2/B3仅作为研究候选。** 共同BA已真实执行，但“原Torus物理模型＋真实RGB”尚未给出四组统一独立收益。暂停B4、12照片和主体训练。优先研究已量化的Ring/RGB残差竞争、005轨迹权重占比、未释放局部yaw和旧RGB地图/深度对原相机的依赖；本轮不根据这些评价反向修改权重重跑。

[完整报告](TECHNICAL_REPORT.md) · [图像和GLB索引](RESULT_INDEX.md) · [失败记录](FAILURE_LEDGER.md) · [复现](REPRODUCE.md)
'''+audit
 write('TECHNICAL_REPORT_SUMMARY.md',summary)
 line=[]
 for p in (N/'code').glob('*.py'):
  for a in ast.walk(ast.parse(p.read_text())):
   if isinstance(a,(ast.FunctionDef,ast.ClassDef)):line.append(dict(file=str(p),symbol=a.name,line=a.lineno,sha256=sha(p)))
 table('metrics/CODE_LOCATIONS.csv',line)
 full=summary+'\n## 真实求解和停止状态\n\n'+md(runs,list(runs[0]))+'\n'+md(ranks,list(ranks[0]))+'''
Ceres成功/失败步数保留其官方定义，含初始step0；不能全部当成新增相机更新。真正接受的外层对应更新为每组4次。G01达到预登记20次内层×4外层预算，最后一次Ceres报告NO_CONVERGENCE；这是有限预算内的可用数值候选，不声称全局或最终收敛。

## 科研问题Q1–Q10

1. **原RF五自由度能否无损统一？** 解析Torus前向与物理定义已逐视角一致，成熟联合BA可运行；但本轮没有重新枚举全部历史法向/yaw初值族，局部相机图表也不是原RF五参数的完全接口搬迁，因此不能称整个历史恢复流程已经无损替换。
2. **厚度、Inner/Outer与遮挡是否进入优化？** 是：R5.6/r0.6固定，I/O独立真实像素；5×5 Polyp邻接UNKNOWN沿用V5原策略。完整椭圆外推、Mid和Polyp接触边界不作第三份强真值。
3. **yaw零空间是否保留并由RGB约束？** 原Torus在真正轴对称作用下投影差近浮点精度；未制造Ring yaw信息。共享H yaw由RGB控制；L2逐帧yaw仍保留原规范，不应宣称全部逐帧yaw已新估计。
4. **解决旧梯度/逐帧假联合问题了吗？** 原理与数值上是：不再调用旧缺口CAD优化器，四组都是单个多相机多XYZ Ceres问题；分量和完整联合Jacobian通过。B1仍明确是独立局部对照，不冒充BA。
5. **四组独立Ring/RGB能同时改善吗？** 没有。Ring普遍改善，heldRGB及相对极线代理出现冲突。
6. **共享H与联合BA分别收益？** B2仅轻微改变G01条件深度MAE且固定支持下降；B3对G03/G05代理有改善，G01/G06无统一收益。单视频组B2不适用，不伪造跨视频结果。
7. **HERO错层减小了吗？** 非统一：G03/G05的反事实代理减小；G01跨视频与G06没有。不能从旧深度重表达推断重新预测精度。
8. **残余错层在哪里？** 逐对表含来源/像素分母；Figure4–6给出真实三角面叠加、固定物理平面交线和原始FaceID热图。前方proxy不等于物理错误，深层可能为合法自遮挡。
9. **哪些相机可冻结用于主体？** 本轮没有足够证据将任何新方案整体升级，继续用已冻结B0；新候选、差异和失败均保留，不自动替换输入。
10. **可引入12照片吗？** 当前不放行：四组Ring与未拟合RGB的权衡尚未解释，局部yaw也未充分验证，整体科学可信性尚未建立。修正005地图坐标评价后，预登记严重阈值没有触发；这不是把数字FAIL改标准做成PASS。12张正确raw20260805照片的SHA登记在NOT_RUN表，没有复制视频位姿补齐。

## 归因的证据与限度

真实共同地标不是GT；其初始化仍依赖旧相机，弱点先验不能解释为真实精度。消去XYZ后的相机信息在实际受限图表中数值满秩，只是局部、当前固定对应下的可辨识性，不证明静态假设、像素身份或相机模型完全正确。G01新旧位姿使背景/Polyp关系、Ring弧与RGB目标产生竞争；不能只凭某一指标区分相机偏差、分割误差或非刚性场景。

权重实现按轨迹、轨迹内video/direction归一，但**没有按全局视频轨迹数或材料类别再等权**。因此005具有更多独立背景轨迹，总RGB权重仍较高；ACTUAL_VIDEO_WEIGHT_SHARES给出实际比例。这是本轮实现限制，不能在看过HOLDOUT后悄悄修改。

B3五维局部图表排除了本视频原生world-z twist；它用于保守L2，不能代替“RGB重新估计每帧完整6DoF”。G01评价修正后未触发预登记严重阈值，但四组独立RGB均有负向权衡，整体几何可信性尚未建立，本轮不继续释放B4追求更好图像。

## 稳定性

'''+json.dumps(sensitivity,ensure_ascii=False,indent=2)+'''
两个预登记初值只检查局部敏感性，不保证全局最优；主结果没有替换成损失略低的敏感性候选。初值和主参数不依赖HOLDOUT/HERO。
'''
 cross=load(N/'metrics/INDEPENDENT_CROSS_VIDEO_HELD_RGB.json');full+='\n## 独立跨视频2D held轨迹\n\n'+md([dict(method=r['method'],unique_held_tracks=r['tracks_N'],raw_pair_N=r['raw_2D_pair_N'],MAE_px=r['epipolar_px']['MAE'],median_px=r['epipolar_px']['median'],P95_px=r['epipolar_px']['p95'])for r in cross],['method','unique_held_tracks','raw_pair_N','MAE_px','median_px','P95_px'])+'\n这347个source-target像素对仅来自4个held物理轨迹，不是347份独立地标；其对称归一极线残差不使用三维XYZ或HERO，单独检验共享H与相对相机关系。没有按该结果选路线或调权重。\n';write('TECHNICAL_REPORT.md',full)
 write('RING_FIRST_ORIGINAL_METHOD_AUDIT.md','''# 原始Ring-First复用审计

已读取并保存SHA快照：geometry.py::torus_contours、V5 g5_common/ring_observations、recover/torus_geometry、V6 local_ring_sfm、V8 registration、V9 local_pose_refinement、V13 rigid13及021。实际版本见ORIGINAL_SOURCE_READ_RECEIPT，不凭报告重写物理模型。

原方程 n(X)·(C−X)=0 给出厚Torus的两条透视表观轮廓，非共面圆。Torch仅将同方程改为64位可微接口，98视角与原函数逐点对照；不是021的网格候选边筛选。四组冻结CAD均核验为内径10mm的同一R10参数。

V5的Polyp邻接5×5 UNKNOWN规则用于实际I/O观测；既有DXY点需真实Mask支持，不使用完整椭圆/Mid补弧。保持原生像素中心坐标与K。原始源码存在+.5边界坐标的接口，当前继承021已核验的整数像素中心+K319.5/179.5，投影函数前向和独立CAD光栅逐项核对，未静默换K。

V8/V9的法向翻转、全局axial yaw分支逻辑已读；本轮从冻结RF分支出发，不重新进行72yaw全搜索，不声称所有分支已经被联合枚举。局部SE3修正和共享H保留SO(3)，Ring实体不变、尺度不开放。原资产全部只读。
'''+audit)
 write('CERES_COLMAP_REUSE_AUDIT.md','''# 成熟BA实际复用

实际环境：Python3.12.13、PyCeres2.6/Ceres2.2.0、PyCOLMAP4.2.1；PyCeres安装在本任务runtime/packages，未改共享旧环境。Ceres使用LM信赖域和DENSE_SCHUR；G01官方FullReport的自动消元顺序为888个点块、59个相机/共享块。不是普通PyCOLMAP BA自然支持Torus。

自定义Python代价包含解析Torus和真实SIFT，Torch64求导；Ceres负责原生求解。没有运行C++AutoDiffCostFunction或GradientChecker，采用外部独立FD检查同一残差。没有自编LM/Schur；joint_information的3×3点块消元只用于信息诊断，不参与更新。

实际参考：
- [Ceres官方BA教程](https://github.com/ceres-solver/ceres-solver/blob/2.2.0/examples/simple_bundle_adjuster.cc)
- [Ceres LM/Schur官方说明](https://ceres-solver.readthedocs.io/latest/nnls_solving.html)
- [PyCeres官方Python代价示例](https://github.com/cvg/pyceres/blob/v2.6/examples/test_python_cost.py)
- COLMAP官方bundle_adjustment源码已小量获取，准确commit和源码SHA见MATURE_SOURCE_READ_RECEIPT；仅参考数据结构/规范，不宣称调用了COLMAP默认BA。

**冷回调绑定故障**：PyCeres v2.6 cost_functions.h的cached_flag初始化分支，无条件读取jacobians[idx]，首次若只有残差求值则jacobians==nullptr，可原生崩溃。独立复现和gdb堆栈保留。先调用同一Problem.evaluate_jacobian建立非空缓存后，重复调用与四组全部实际运行完成。此接口处理不更改损失、变量、LM或Schur。原未修复backend快照和事故日志保留，不能把该崩溃归因于Torus数学。
'''+audit)
 write('UNIFIED_CAMERA_GEOMETRY.md','''# 统一相机约定

OpenCV c2w、mm、x向右/y图像向下/z向前。Xcam=(Xworld−C)R，uv=KXcam；K冻结640×360，f490、cx319.5、cy179.5。Native RF从原cache读取，G01 H0固定完整RoMa，004 H=I。

独立005 held地图先撤销历史H21，再用候选H映射到共同世界，避免将纯共享刚体重表达错算为内部RGB误差；真实004跨视频held身份则保持004参考，另给直接2D–2D极线评价。

实际 C=Exp(qH·S) H0 Exp(qlocal·S) RF，S=(0.6mm×3,5deg×3)。左乘在原生Ring坐标中，H把原生视频送到004共同世界；pose_t、SE3逆和原点/轴关系均验证。不是Sim(3)。

每视频首FIT局部块固定以识别共享H/局部轨迹分解；004首相机固定完整6DoF定义全局规范。B3其他相机仅在≥6个真实FIT观测时释放5D；局部world-z twist保持原规范，不能冒充完整6D yaw新恢复。005共有H是完整6D。对相机位移≤1.2mm、旋转≤10deg、地标漂移≤3mm及解析Torus可见域作真实外层回缩；不放宽已有几何约束。

GLB按格式规范将整个世界统一乘0.001输出米；metadata和layer_manifest记录恢复mm需×1000。这是显示单位转换，不是新拟合尺度，不按层独立中心化。
'''+audit)
 write('TORUS_RESIDUAL_AND_JACOBIAN_TEST.md','''# Torus残差与雅可比

原RF方程与Torch64在98视角前向、轴对称旋转和SE3层级测试均通过。72项分量测试覆盖Torus/RGB/先验与多种FD步长；四组完整联合Jacobian在实际活动相机图表和XYZ维度中另作随机方向FD，所有三个步长通过，原始误差不只给PASS。

Ring仅对真实可确认I/O弧建立最近解析曲线对应，固定theta/branch求局部导数；外层重建对应并计算真实完整目标后才接受。未用离散网格编号产生yaw信号，θ不是物理材料点身份。

初版用三角CAD向解析切线点投射射线，约70–79% MISS，并有少量提前命中，不能作为解析可见性真值。初版失败门禁已保留。随后对**同一原Torus隐式四次方程**，利用已知切根t=1的二重性除出(t−1)²，检查其余二次根：98视角没有更早正交点，余项约1e−15。没有把MISS自动置可见，也没有放宽网格深度阈值。

独立CAD硬渲染边界到解析曲线P95约0.89–0.91px；Mask IoU约0.91–0.94，反映像素/细线材光栅离散差异，未声称两种填充逐像素完全一致。实体CAD仅用于独立审计和可视化，没有替换原解析Torus目标。
'''+audit)
 write('JOINT_BA_IMPLEMENTATION_REPORT.md','''# 联合BA实现逐项对照

| 原定组件 | 实际实现 | 位置 |
| --- | --- | --- |
| 原始物理Torus | 原函数逐点复现的Torch64表观轮廓 | code/torus.py::torus_uv_t/curves |
| 可见实际I/O | V5 Polyp邻接UNKNOWN+已冻结真实Mask支持点 | code/visible_arcs.py::qualified |
| SE3公制更新 | H Exp(local) RF，SO3始终成立，无尺度 | code/torus.py::pose_t |
| 共同XYZ | 同一真实RGB身份一个3D变量，18跨视频link合并 | code/prepare.py；config/TRACKS.json |
| 鲁棒Ring/RGB | vectorHuber/3px，按曲线/视角或轨迹内video方向归一 | code/ceres_backend.py；code/joint_ba.py |
| 成熟LM/Schur | 实际pyceres.solve；每组一个多相机多点Problem | code/ceres_backend.py::solver；Joint.build |
| 先验/规范 | 固定004参考，首005局部固定；弱q、XYZ与相邻q差先验 | Joint.build |
| 逐帧完整6D | L2仅5D局部图表，B4完整释放被独立门禁暂停 | STAGE_DECISION.json |
| 条件可辨识性 | 数据J消去XYZ，排除所有先验；图连接与FD | code/joint_information.py |
| 外层可见性/接受 | 重算对应+真实全目标+物理域+回缩 | Joint.run/physical |

B3实际目标为Ring1、RGB0.2、pose0.01、XYZ0.001。Ring每曲线/每视频/方向归一；RGB每轨迹内video/方向归一，非全局等视频。相邻q差是固定Ring坐标中的一阶轨迹先验，不是精确相邻SE3测地距离；XYZ先验是1mm等方弱正则，不是GT协方差。没有重复加第二份RGB损失。

B2只用实际跨视频共同轨迹约束H，内部同视频轨迹保持固定；B3加入同视频轨迹、共同XYZ和局部5D。故B2/B3是预定层级比较，不能把全部差异仅归于“释放XYZ”单因素。B1是固定XYZ独立局部对照，所有路线的差异公开。

元数据命名纠正：通用serialize曾给B1_LOCAL/B2也写入FROZEN_NUMERIC_JOINT字符串，名称不准确；它只是通用数值状态，不能据此称联合BA。原始FINAL和SHA保持不变，NUMERIC_STATUS_SCOPE_CORRECTION及ACTUAL_PROBLEM_SCOPE_AUDIT按真实Ceres活动块明确纠正：B1单相机、B2共享H固定XYZ、只有B3为多相机和XYZ联合。顶层B1始终标INDEPENDENT_LOCAL_NOT_JOINT_BA。

完整函数行号及SHA见CODE_LOCATIONS.csv，避免只按方法名宣称实际忠实。
'''+audit)
 weights=load(N/'metrics/ACTUAL_VIDEO_WEIGHT_SHARES.json');write('MULTIVIEW_SIFT_AND_GAUGE_AUDIT.md','''# 真实RGB身份、规范与权重

1728轨迹/11315实际特征像素坐标逐个验证feature_id→缓存xy完全一致；未运行新SIFT、未用3D最近邻建身份。18共同link沿用021真实跨视频RGB证据。静态材料身份为RGB+RANSAC支持，不是绝对物理GT；高光/重复纹理和原相机误差仍不能完全排除。

'''+md(weights,['group','video','observations_N','RGB_weight_sum','RGB_weight_fraction','Ring_weight_sum'])+'\n'+md(ranks,list(ranks[0]))+'''
图表中的满秩仅指实际活动自由度、固定参考和当前局部对应，不能当作未释放yaw或全部场景真值可观测。固定的H004、参考相机和首005局部块明确消除规范；XYZ漂移有弱先验和独立3mm上限。原地图不是GT，held轨迹重投影也不是独立标定精度；HOLDOUT极线只依赖真实像素与相机，更适合检查相对关系，但仍受匹配身份影响。
'''+audit)
 write('HERO_LAYER_VISUALIZATION_REPORT.md','''# 原生HERO层、错层与单位

51份真实TRUSTED来源完整保留：G01 21、G03 9、G05 11、G06 10。每源原始Mesh、深度、Pixel/Face ID与SHA在HERO_NATIVE_IDENTITIES_AND_DERIVED_TRANSFORMS；无ICP、删面、补洞、平滑或重网格。保留原三角面集，只以新相机D=Cnew inv(Cnative)作诊断重表达。

Figure4按原视频颜色显示G01 B0/B2/B3；Figure5是同一世界Y平面与真实原三角面的交线，不把SDF代理或最近邻点云当原Mesh。Figure6根据原FaceID将可见性证据画回原面。灰色UNKNOWN不视作零误差，前方分歧是proxy，后层保留合法遮挡解释。局部图的同层可比性仍只是共视/近层证据，不是真实对应GT。

全部原生V仍保存，包括未被TRUSTED F引用的原顶点；可视范围按真正被面片引用的顶点计算，避免被未渲染原顶点拉到极远。没有删除任何实际TRUSTED三角面。同一病例B0/B1/B3共享观察方向和显示范围，Ring黑色；B0/B2主体为可选灰色静态层。

图2使用每组canonical顺序中首个非参考FIT，避免误将固定规范相机画成优化变化。初版误选受保护参考相机的图保留本地；修正选图按活动变量身份，不按IoU、GT或成功排名。

四GLB每源、每方法、相机视锥独立对象；HTML可切换B0/B1/B2/B3并逐层显示。GLB整个世界按标准从mm统一转换到m，不是独立ICP或拟合尺度；回读边界误差记录。大型GLB保留本地路径与SHA，不伪称上传仓库。

深度比较沿目标真实射线查原始TRUSTED第一层网格，排除CAD挡住和目标深度本已位于CAD后的不可靠顺序。支持±0.5mm、前方/更深层/Unknown分别计数，±0.2/1mm敏感性独立列。normal_angle为支持集合上方向无关的法向夹角，不作新的身份对应。累计来源面积不是去重解剖面积。

PER_NATIVE_SOURCE_UNIQUE_COVERAGE另给每个来源对其他所有来源的逻辑并集，避免把同一个原生PixelID被多个目标看见重复计数。覆盖和缺失是源内唯一像素口径，不是跨来源去重解剖面积；source_union NPZ保留原Pixel/FaceID和混合支持/冲突身份。采样面面积只是明确标注的代理，未采样面保留UNKNOWN。
'''+htable+audit)
 write('FAILURE_LEDGER.md','''# 失败和未解决问题

| 记录 | 原因和证据 | 处理 |
| --- | --- | --- |
| 初次PyCeres原生崩溃 | G05首冷调用及独立最小复现；v2.6 cached_flag分支解引用空jacobians；gdb/raw日志 | 原始代码快照、绑定源码及事故日志保留；显式预求Jacobian后全部真实运行完成 |
| 初版005 held地图评价坐标错误 | 把005独立地图固定于原H0却与更新H下相机比较，造成无意义刚体坐标残差 | 只修正评价，全部预测/XYZ及阈值不改；旧表、源码、门禁和报告保存在provenance/INITIAL_EVALUATION_FRAME_CONTRACT_ERROR |
| 早期三角CAD切线MISS门禁 | 三角近似的切线射线不命中，不能解释为原Torus自遮挡失败 | 原门禁保留；改用同一隐式方程严格根检查与独立硬渲染，无放宽遮挡阈值 |
| 独立RGB科学支持不足 | G01修正后1.39961→2.11717px，四组held残差均增加，但没有触发原严重阈值 | 不用错误初版数字停机；数值安全与科学可信性分开，当前不放行B4/照片 |
| 四组HOLDOUT相对极线变差 | 直接原始held相机保护不等于与更新FIT的相对关系不变 | 全部逐视角与N保留，不只展示RingIoU |
| G01/G06旧HERO相容性下降 | 深度差/支持率代理变差；旧HERO依赖旧相机，非绝对误差GT | 标POSE_CHANGED_DEPTH_NOT_REINFERRED，不用HERO选模 |
| B3局部yaw仍冻结 | L2为五维图表，未重新估计每帧完整6D | 明确方法差异，B4需几何门禁，不冒称完整yaw恢复 |
| RGB005轨迹权重占优 | 轨迹内video均衡不等于全局等视频；背景点较多 | 公开实际权重份额，未看过held后改权重重跑 |
| G01未最终收敛 | 预登记20内层×4外层，Ceres最后NO_CONVERGENCE但可用 | 不能称最终最优，也不借此放宽预算反复搜索 |
| 通用数值状态字符串过宽 | B1_LOCAL/B2的FROZEN_NUMERIC_JOINT不准确 | 附实际变量块作用域纠正表，原始结果不改，不称独立相机为联合BA |
| B2三组不适用 | G03/G05/G06无本轮验证的跨视频关系 | NaN/N/A，绝不使用旧或伪造跨视频位姿 |
| B4/照片未运行 | 独立门禁暂停；照片12张全部登记原raw20260805身份 | NOT_RUN，不复制历史/关键帧结果补齐 |
| 辅助验证脚本错误 | 对JSON list直接abs、误将StageA变量用于科学门禁字段 | 修正后重新验证；不改变相机、XYZ或任何科学指标 |
| 初版Ring对照图选中参考相机 | 四组首FIT恰为固定规范相机，无法展示实际更新 | 改为各组首个非参考FIT的统一次序规则；旧图保留，不按效果挑图 |
| 无真实位姿/三维GT | 原始作者模型不是已独立标定的当前世界GT | 绝对位姿/测量准确度NOT_EVALUABLE，不伪造GT误差 |

本轮没有主体训练、HERO重新推理、跨视频融合或DXY修改。失败不通过删掉困难视角、FaceID或调标准改成PASS。
'''+audit)
 write('REPRODUCE.md',f'''# 复现

本地目录 `{N}`。沿用Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；使用本目录runtime/packages的PyCeres2.6，Ceres2.2.0。系统python3.8不适用于本轮Python3.12语法。无GPU训练/推理。

既有原始数据、021特征地图和HERO必须位于索引登记路径；源文件SHA见INPUTS_FROZEN与资产索引，不把未上传本地缓存说成仓库内容。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
U={N}
# 已有FINAL时只验证，不重新优化或覆盖。
$PY -B "$U/code/replay.py"
# 只重建独立诊断/图像，候选保持冻结：
$PY -B "$U/code/joint_information.py" G01
$PY -B "$U/code/joint_information.py" G03
$PY -B "$U/code/joint_information.py" G05
$PY -B "$U/code/joint_information.py" G06
$PY -B "$U/code/evaluate.py"
$PY -B "$U/code/cross_held_audit.py"
$PY -B "$U/code/stage_decision.py"
$PY -B "$U/code/additional_audit.py"
$PY -B "$U/code/hero_evaluate.py"
$PY -B "$U/code/source_coverage.py"
$PY -B "$U/code/finalize_tables.py"
$PY -B "$U/code/scope_audit.py"
$PY -B "$U/code/export_layers.py"
$PY -B "$U/code/visualize.py"
$PY -B "$U/code/report.py"
$PY -B "$U/code/verify.py"
# 查看本地GLB/HTML（HTTP，首次需联网获取固定three0.169模块）：
$PY -m http.server 8765 --directory "$U/local_results/interactive"
# 浏览器 http://localhost:8765/G01_VIEWER.html，其余G03/G05/G06同名。
```

从干净的独立实验副本重跑：prepare → visible_arcs → stage_a → joint_ba(G01/G03/G05/G06) → sensitivity → information → evaluate → stage_decision → HERO/GLB/figures。使用同一protocol，不按HOLDOUT改参数。原生崩溃最小复现 binding_repro 的旧backend快照/日志保留；当前solver显式预求Jacobian，不能通过关闭自定义Torus残差“修复”。
'''+audit)
 index='''# 结果索引

[技术摘要](TECHNICAL_REPORT_SUMMARY.md) · [完整报告](TECHNICAL_REPORT.md) · [相机总表](FOUR_GROUP_POSE_SCORECARD.csv) · [HERO总表](HERO_SURFACE_ALIGNMENT_SCORECARD.csv)

'''
 for p in sorted((N/'figures').glob('*.png')):index+=f'- [{p.stem}](figures/{p.name})\n'
 index+='\n## 本地大型资产（未上传Git）\n\n'
 for a in load(N/'assets_index/INTERACTIVE_GLBS.json'):index+=f"- {a['group']}：`{a['GLB']['path']}`，{a['GLB']['bytes']} bytes，SHA256 `{a['GLB']['sha256']}`；同目录 `{a['group']}_VIEWER.html`。\n"
 index+='\n冻结相机：results/{group}/{B0,B1,B2,B3}/FINAL.json；B4原PENDING/初版NOT_RUN文件保留，当前结论读NOT_RUN_CORRECTED_EVALUATION_REASON和STAGE_DECISION。共同XYZ在B3 FINAL中；原始RGB轨迹及像素在config/TRACKS.json，描述子/图像原文件在输入SHA索引。外层拒绝原因、各次Ceres完整FullReport与真实日志在optimization。\n';write('RESULT_INDEX.md',index+audit)
 # Required original journals: exact raw logs copied as small text, not rewritten summaries.
 dst=N/'optimization/ACTUAL_PROCESS_LOGS';dst.mkdir(exist_ok=True)
 for p in (N/'runtime/logs').glob('*.log'):
  if p.name in ['G01_ba.log','G03_ba.log','G05_ba.log','G06_ba.log','stage_a.log','sensitivity.log','CERES_BINDING_MIN_REPRO.log','CERES_LIFETIME_ISOLATION.log','GDB_BINDING_FIRST_CALL.log','CERES_REPEATED_PROBLEM_REPRO.log','CERES_WARM_REPEATED_PROBLEMS.log']:shutil.copyfile(p,dst/(p.stem+'.txt'))
 save('assets_index/LOCAL_LARGE_FILES.json',[asset(p)for p in(N/'local_results').rglob('*')if p.is_file()]);save('provenance/DELIVERY_MANIFEST.json',dict(epoch=time.time(),code=[asset(p)for p in(N/'code').glob('*.py')],reports=[asset(p)for p in N.glob('*.md')],figures=[asset(p)for p in(N/'figures').glob('*.png')],all_final_pose_freeze=asset(N/'provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json'),stage=asset(N/'STAGE_DECISION.json'),local_large_index=asset(N/'assets_index/LOCAL_LARGE_FILES.json'),no_large_asset_upload_claim=True));print('REPORTS_AND_MANIFEST_COMPLETE',flush=True)
if __name__=='__main__':main()
