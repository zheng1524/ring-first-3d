"""Concise complete scientific report; results never feed fitting or replace021 outputs."""
from qcommon import *
from group_reports021 import md
import ast,platform

def write(p,text):(Q/p).write_text(text,encoding='utf8')
def main():
 while not(Q/'runtime/QUICK_FIGURES_COMPLETE.json').exists():time.sleep(5)
 reg={a['method']:a for a in load(Q/'metrics/REGISTRATION_COMPARISON.json')};her={a['method']:a for a in load(Q/'metrics/HERO_INDEPENDENT_AGGREGATE.json')};sift={(a['method'],a['role']):a for a in load(Q/'metrics/SYMMETRIC_SIFT_EVALUATION.json')};cm={a['method']:a for a in load(Q/'metrics/HERO_EXACT_COMMON_GAINED_LOST.json')};photo=load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json');assets=load(Q/'config/PHOTO_ASSETS.json');ready=load(Q/'config/ALL71_CAPTURE_IDENTITY_AND_READINESS.json');gr=load(Q/'metrics/GRADIENT_COMPONENT_ISOLATION.json');comparison=[]
 for i,arm in enumerate(['B1','B2','B3'],1):
  a=load(Q/'results'/arm/'FINAL.json');b='A0_'+arm;n='A'+str(i);g=load(Q/'metrics'/(arm+'_ORIGINAL_OBJECTIVE_GATE.json'));row=a.copy();row.update(endpoint_reproduction_max_abs=g['absolute_error'],endpoint_repeated_noise_range=g['repeat_range'],before_HOLDOUT_IoU=reg[b]['HOLDOUT_IoU'],after_HOLDOUT_IoU=reg[n]['HOLDOUT_IoU'],before_Ring_Inner_px=reg[b]['HOLDOUT_Inner_px_MAE'],after_Ring_Inner_px=reg[n]['HOLDOUT_Inner_px_MAE'],before_Ring_Outer_px=reg[b]['HOLDOUT_Outer_px_MAE'],after_Ring_Outer_px=reg[n]['HOLDOUT_Outer_px_MAE'],before_held_SIFT_F=sift[b,'HOLDOUT']['normalized_symmetric_F'],after_held_SIFT_F=sift[n,'HOLDOUT']['normalized_symmetric_F'],before_HERO_support=her[b]['support_fraction_fixed'],after_HERO_support=her[n]['support_fraction_fixed'],before_HERO_known_MAE_mm=her[b]['known_MAE_mm'],after_HERO_known_MAE_mm=her[n]['known_MAE_mm'],exact_common_N=cm[n]['common_N'],exact_common_before_MAE_mm=cm[n]['common_before_mm']['MAE'],exact_common_after_MAE_mm=cm[n]['common_after_mm']['MAE'],gained_N=cm[n]['gained_N'],lost_N=cm[n]['lost_N']);comparison.append(row)
 qsave('metrics/SOLVER_COMPARISON_FULL.json',comparison);qtable('SOLVER_COMPARISON.csv',comparison)
 audit='''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | BA为G01同一视频对的3条续优化；照片为4组×3=12个原始采集，G01三张做实际相机尝试 |
| 本算法独立成功 | 3/3实际成熟求解器输出，12/12同批RGB和Mask定位，G01 3/3独立数值相机候选；强照片监督资格0/3，不混为正确率 |
| 本算法失败 | 完整Ring梯度门禁失败；A1线搜索异常，A2/A3主要在数值波动附近终止；3照片新门禁均未过，照片HERO/可信新增面积NaN/NOT_EVALUABLE |
| 历史测量值回退 | 0；021终点是本轮明确授权的续优化初值/A0参考；没有旧Dxy或其他算法测量值补齐 |
| 失败组及具体原因 | G01三照片当前held误差门禁失败，photo003还存在Ring/尾部问题；错误采集批次已隔离。见失败台账及真实RGB/三维候选图 |
| 最终统计样本 | BA全部18轨迹/553FIT像素、全部52FIT+3HOLDOUT目标帧及固定21HERO来源；全部12照片保留，包括未运行HERO的三张 |
| 是否使用GT选择算法 | 否；原BA不含照片/body/HERO/HOLDOUT；候选先冻结再独立评价。照片只用PHOTO_FIT选初值与拟合，PHOTO_HELD/主体不参与 |
'''
 tests=[a for a in gr if a['parameter']=='pose'and a['h']==.01];maxsmooth=max(a['smooth_relative_error']for a in gr);posefd=md(tests,['arm','index','h','smooth_AD','smooth_FD','smooth_relative_error','Ring_curves_AD','Ring_curves_FD','Ring_relative_error'])
 small=md(comparison,['method','initial_loss','loss','initial_gradient_norm','final_gradient_norm','nit','nfev','solver_success','solver_message','translation_change_mm','rotation_change_deg','max_point_change_mm'])
 independent=md(comparison,['method','before_HOLDOUT_IoU','after_HOLDOUT_IoU','before_held_SIFT_F','after_held_SIFT_F','before_HERO_support','after_HERO_support','exact_common_N','exact_common_before_MAE_mm','exact_common_after_MAE_mm','gained_N','lost_N'])
 summary='''# QUICK-BA-SOLVER-REVIEW 结果摘要

**已完成三条成熟求解器实际续优化，以及同批12张独立照片恢复与G01三张实际配准。未开展主体训练或曲面融合。**

**主要结论：目前不能将021停滞归因“观测已经达到极限”。** 平滑SIFT/先验分支的AD–FD吻合，而Ring可微渲染分支在多方向出现大幅、甚至符号相反的AD–FD偏差。成熟L-BFGS-B没有使A2获得可信的联合几何改善；它仍使用这个未经验证的完整梯度，因此不能据其终止判定BA数据无解。

'''+small+'''
Loss无量纲、平移/点位移mm、旋转deg。A1部分下降但线搜索ABNORMAL；A2实际移动约3e−10mm，目标变化约1e−7，处于重复渲染波动量级。A3同样只发生微小变化。`solver_success=True`的相对函数变化终止，不等于低梯度或科学收敛。完整先验仍相对原始RoMa与联合三角化X0，没有在021终点重置正则中心。

## 独立几何结果

'''+independent+'''
全部候选冻结后统一评价。HERO分母固定2,893,126个重复原生源–目标观测，21来源/208有向跨视频配对；共同/新增/丢失严格依据同一原Pixel ID。共同误差仍含单列的后方/合法自遮挡代理，不是物理表面GT。A1只有微小代理变化；A2/A3没有实质独立收益。没有按这些HOLDOUT/HERO数值再调参，也未选择新终点。

## 独立照片与输入恢复

初次默认`rg --files`遵守Git忽略规则，遗漏raw20260805，曾误选旧picture/new picture目录中的同名照片。检查v4/v13原始来源SHA后发现不同采集批次；错误输出与源码完整保留在`provenance/WRONG_CAPTURE_COHORT_QUARANTINE/`，不计入正式结果、不回填。随后显式读取raw20260805：四组12/12原始JPG及对应原生分割缓存均找到，G01三张原SHA与同视频采集记录完全一致，640×360工作图也与历史原始输入逐像素一致。**同名不是同一采集身份。**

旧20260415 `missing_inner_ellipse`只是旧同名记录，不能当作本批照片缺失；当前本批三张都实际运行成熟DXY Ring流程。当前Mask是同批保留UNet3Plus多类缓存，非旧LabelMe，也不是本轮新分割推理。旧记录只取stem/status/reason，未使用旧测量值。不同采集批次旧失败与本批新拟合不构成严格同Mask算法对照。

'''+md(photo,['id','SIFT_FIT_PnP_inliers_N','PHOTO_HELD_error_px','Inner_MAE_px','Outer_MAE_px','minimum_direction_difference_deg','camera_status','current_gate_reasons'])+'''
三张均有独立Ring-First初始化、真实SIFT/PnP与Ring约束精修，未复制任何视频外参。photo001/002的004/005独立种子精修结果分别只相差约0.028/0.010mm、0.019/0.012°，但PHOTO_HELD MAE分别3.849/3.058px；photo003单侧种子、held MAE5.049px/p959.823px及Ring误差更大。它们均未通过事前固定3px MAE/6px P95门槛；该结论来自本轮新观测，非继承V13旧UNREGISTERED标签。photo002接近阈值，不等于物理无价值，更不能事后改阈值。

真实2D匹配另做固定16个视频FIT视角×3照片、复用缓存SIFT，Essential/Ring有限候选仅作显式2D-only补充；不虚构3D同名点，不称其为PnP，不根据留出或主体挑选。完整候选保留。独立照片不是短视频，彼此无已知相对轨迹。

## HERO与全视角适配

现有审计原生目标均是视频帧；V13照片历史记录亦为NOT_RUN。本轮核验了018官方HERO加载器和完整权重SHA、原017清理规则，准备了每张目标及三个同组FIT支持的RGB/K/统一世界相机清单。由于三张未通过新照片相机门禁，本轮实际新HERO推理0次，TRUSTED子集、面积、与已有曲面相容性、主体未覆盖和新增可信面积均为MISSING/NOT_EVALUABLE，不能用视频深度投影假装照片原生深度。

71是68视频+3独立照片的候选资产数，不是71份已合格三维监督。保留原8个HOLDOUT，现有60个FIT视角可提供条件性Mask观测，其中16个具有已登记原生TRUSTED HERO；三照片当前不进入强监督FIT。新增方向最小差约7.10°/1.53°/9.99°为数值候选条件估计，不等于新增可见表面积；photo002方向接近已有视角。

**下一轮坐标建议：暂时沿用事前固定的021 B3共同坐标基准，保留其已知局限；不自动将A1/A2/A3升级为新主线，也不按本轮HOLDOUT重新选择020候选。** 优先隔离修复Ring梯度一致性；对照片核对光学模式、误差来源及有限真实对应，001/002可优先进一步核验，003需更多Ring/位姿证据。真实独立照片的数值候选不是绝对位姿认证。

'''+audit+'''
[四张核心图与补充RGB证据](RESULT_INDEX.md) · [复现](REPRODUCE.md)。本轮结束，等待人工审核。
'''
 write('TECHNICAL_REPORT_SUMMARY.md',summary)
 method='''# 实际算法、目标和实现对照

| 原设计 | 实际实现 | 差异/限制 |
| --- | --- | --- |
| 原021共同BA目标 | `solver_review.one`直接调用原`BA.evaluate` | 数据18/553、全部52FIT、权重不变；q仍相对原RoMa、X prior仍相对原X0，不能在终点重置先验 |
| 成熟求解器 | SciPy `minimize(method=L-BFGS-B,jac=True)` | 25iteration/90evaluation软预算、12line-search；使用原完整AD。原耦合SE3/点范数/白化/正深度域以Infinity不可行域保持，非新增可行loss；外包盒覆盖原域 |
| 参数化 | 原6维q + (X−X0)/0.6mm | 只是变量尺度变化，梯度按链式乘0.6；不新增相机/尺度/观测 |
| 目标复现和梯度 | `solver_review`、`gradient_isolation` | 3次固定值重复；中心FD h=.01/.001；分离平滑SIFT/prior与Ring，未修复后冒称同一目标。完整Ring梯度未通过 |
| 独立评价 | `evaluate_review`调用原020/021评价组件 | 先冻结，统一52FIT+3HOLDOUT、全部固定21HERO源；共同比较同原生ID，不按条件均值选结果 |
| 照片身份 | `photo_assets` | 显式raw20260805路径/源SHA/原生Mask，拒绝旧同名采集；VIDEO_FRAME/INDEPENDENT_PHOTO分开 |
| Ring初始化 | `photo_registration.ring_initial` | 复用成熟Ring-First decode/image_seeds/solve，四个保留种子；解析实体圆环轮廓+材料/背景区域，保留绕轴/法向对称候选，不是完整pose认证 |
| 照片SIFT/位姿 | `source_banks`、`one` | 只提取三照片SIFT，复用153/980地标原RGB描述子；真实ID追溯，固定PHOTO_HELD，PnP不复制视频外参；005源只施加固定B3 |
| 照片精修目标 | `photo_registration.loss` | 成熟V5 Mask-region/轮廓 + 可见typedI/O .05 + SIFT .2 + posePrior .01；Huber3px、按源视频和观测数归一，least_squares线性外层；这与原BA的P3D软Mask不是同一个目标，明确分开 |
| 仅2D补充 | `photo_2d_geometry` | Sampson替代不可用2D3D时明确标注，OpenCV Essential+Ring距离生成候选、最多2个45nfev；不生成共同XYZ。原PnP FINAL不覆盖，不用held/body选择 |
| 相机评价 | `photo_audit` | 真实CAD三角面独立光栅、DXY原Mask支持点；PHOTO_HELD误差和种子差，原Gate标签不自动否决。K490是沿用同设备假设，非新标定 |
| HERO | `hero_prepare` | 官方权重SHA通过，仅准备；新相机门禁失败所以未推理，017 TRUSTED子集不伪造；无模型训练或权重更新 |

照片强监督门禁在正式照片拟合前以旧成熟3px/6px协议固定；源身份纠错不更改阈值。PHOTO_HELD=featureID%5==0，不是021历史8个整图HOLDOUT。解析圆环用于照片求解，最终用原完整三角面CAD独立评价；原BA的PyTorch3D目标完全保留。未知/Polyp遮挡区域不作为已知Ring不存在证据，Mid拟合曲线是诊断、不是完整可见物理边界。I/O采用原Mask≤2.5原生像素回溯，预处理外推点另存，不混作真实观察。

Ring纯绕轴本身不提供唯一yaw，新增真实图像特征对照片yaw给出数值约束，不认证绝对角度。照片没有HERO，因此当前没有可归因于照片的可信深度梯度；未做主体optimizer.step()。未来单主体适配应显式记录每来源Mask/HERO分量梯度和实际作用面，而不是将未观测深度填0。
'''
 method+='\n照片匹配独立性复核：各视频PnP内部的地标和照片feature ID均唯一；合并004/005后，001的50个FIT观测对应46个独立照片像素、002的44个对应42个、003的15个对应15个。同一照片像素在两套独立三角化地标中重复出现，并非完全独立证据；原视频归一化仍保留，未改变冻结优化。PHOTO_HELD对应数量同样是观测数而非独立物理点数。详见metrics/PHOTO_INLIER_IDENTITY_INDEPENDENCE.csv。多种子精修各自以PnP为先验中心，所以FIT目标排序包含种子先验差异，不能据此认证唯一最优姿态；最终均未获强监督资格。\n原生图1920×1080；照片Ring/SIFT重投影统计均为640×360工作像素，原生边界吸附阈值2.5px单独在原图定义。FD仅测试登记的位姿0/2/4轴和共同点X等方向，不冒称对全部60参数逐元素穷举。\n'
 write('METHOD_AND_LOSS_AUDIT.md',method)
 write('SOLVER_REVIEW_REPORT.md',summary+'\n## 原目标分量梯度隔离\n\n'+posefd+f'\n全部平滑分支方向的最大相对误差为{maxsmooth:.6g}；完整Ring分支显著不一致，不能将重复波动或光栅离散自动等同唯一根因。\n\n'+md(comparison,['method','endpoint_reproduction_max_abs','endpoint_repeated_noise_range','before_Ring_Inner_px','after_Ring_Inner_px','before_Ring_Outer_px','after_Ring_Outer_px','before_HERO_known_MAE_mm','after_HERO_known_MAE_mm'])+'\n'+method)
 pp=md(photo,['id','Ring_boundary_px','Ring_hard_balanced_MSE','Inner_MAE_px','Outer_MAE_px','SIFT_FIT_PnP_inliers_N','PHOTO_HELD_error_px','seed_pose_spread','minimum_direction_difference_deg','nearest_existing_video_view','frozen_independent_photo_pose_body_IoU','current_gate_reasons'])
 write('G01_PHOTO_POSE_AUDIT.md','# G01 独立照片数值位姿与资格\n\n'+pp+'\n原照片/同批Mask路径与SHA见INDEPENDENT_PHOTO_ASSET_MANIFEST.csv；每张Ring初值、两个PnP分支及精修、真实UV/描述子ID/原视频featureID均保留于results/photos和photo_features。原始PnP与2D-only Essential候选不混用；所有位姿在照片held/body评价前冻结。当前数值yaw由真实特征支持，但未满足强监督门禁；不能称Ring单独认证6DoF。内参K490沿用同设备工作图假设，不能称独立标定。照片对主体IoU仅为冻结后代理，不用于选姿态。\n\n'+audit)
 write('G01_PHOTO_HERO_AUDIT.md','''# G01 照片HERO准备与真实缺口

新照片原生HERO推理：**0次**。不是模型执行失败，也没有将视频HERO重投影伪装成照片原生几何。

三张已获得独立数值位姿，但新PHOTO_HELD门禁均失败，003还存在Ring残差与单侧几何支持问题。原生深度、原Mesh、TRUSTED面片子集、可靠面积、与已有源相容性及主体未覆盖比例均为MISSING/NOT_EVALUABLE；不得将缺失统计写成0mm误差或0新增表面积。当前强照片监督数量0/3，不能冒充3/3准备完毕。

已核验018所用官方完整HERO checkpoint实际SHA，保留原权重、官方load_official、原模型/分辨率适配及017固定保守清理规则索引。每张照片的候选三个FIT支持图像、K、统一世界相机和转换链已保存`inputs/G01_photo00*/HERO_PREPARATION.json`。005所有相机由固定B3统一到004，毫米→米只在官方调用时换一次；K index→edge +.5，目标352×640。

重新获得可用相机后，应依次运行官方前向→保存原生352×640轴向深度/Pixel ID→使用018原始mesher→执行017已冻结分类与gap规则→导出真正state==TRUSTED的原面子集。保留UNCERTAIN/UNKNOWN/REJECTED，不插值、不补洞、不改原点。上述步骤本轮只准备，未执行，不能把预备代码路径当成新几何产物。

是否有新增三维可见表面：**NOT_EVALUABLE**。当前7.10°/1.53°/9.99°只是数值候选相对既有方向的估计，不等同新增面积。图片显示不同表面潜力，不是几何证据认证。

'''+audit)
 write('ALL_VIEW_BODY_ADAPT_PLAN.md',f'''# 下一轮共享主体输入准备（本轮不执行）

71=68视频+3独立静态照片，仅候选资产计数。原视频保留60FIT+8HOLDOUT，{sum(a.get('can_provide_TRUSTED_HERO_FIT',False)for a in ready)}个FIT视角有已登记原生TRUSTED HERO。照片当前Mask强监督0、可信HERO0；单独列出数值候选和当前失败原因，不能将原照片变成视频关键帧或新增训练HOLDOUT后称协议相同。

暂沿用事前固定021 B3统一004世界坐标，保持三条新求解器候选只作复核，不根据本轮HOLDOUT替换基线。018冻结B2可作为下一轮单主体初始化，不建立三个照片主体再ICP拼接。

目标为 `sum_v w_v(lambda_H L_HERO^v + lambda_S L_Mask^v) + L_prior + L_Ring`。仅通过输入核验的FIT参与；相机、原生HERO、CAD冻结，只更新同一个Mesh。视频/方向/共享上游RGB相关性归一；可见性区分首层支持、前方分歧、后方/自遮挡和Unknown，不要求所有源互相重合。固定原始观测分母和miss代价，不按命中集合均值选择checkpoint。

每张照片将来需记录Mask/HERO独立梯度范数、非零顶点/原始面ID以及与其他视角的梯度夹角。本轮不训练主体、不计算假照片深度梯度；相机未验收和HERO缺失时记录NOT_EVALUABLE。需要人工审阅当前照片定位及Ring梯度复核，再单独授权下一轮。

当前最优先工程问题是Ring分支AD–FD不一致；在这个问题隔离前，不把更多相机自由度或照片数量当作自动修复。photo001/002可优先核对具体保留特征与光学模式；photo003需更充分的几何验证。G03/G05/G06已完成相同12张资产格式清单，本轮不自动恢复其照片相机或推理其HERO。
''')
 failure='''# 失败与不确定性台账

| 项目 | 真实处理 |
| --- | --- |
| 默认文件搜索忽略raw | `rg --files`默认遵守Git忽略导致初选同名旧照片；SHA与v4/v13同视频采集记录不符，全部旧照片输出/源码移入WRONG_CAPTURE_COHORT_QUARANTINE，正式记录仅raw20260805，未改变算法/阈值来制造成功 |
| 原完整Ring梯度门禁失败 | 原目标复现误差在1e−6内，但Ring方向AD–FD大幅/符号不一致；平滑分支通过。未静默修改损失，未称观察极限 |
| A1线搜索异常 | 保留真实部分改进与ABNORMAL，不称收敛 |
| A2/A3相对函数停止 | 梯度未小，主A2运动/误差变化在数值波动附近；原矩阵、点和约束保留，未扩大搜索 |
| 三照片强监督门禁失败 | photo001 MAE3.849px；002为3.058px接近阈值但不放宽；003 MAE5.049/P959.823px并有Ring尾部问题。数值位姿保留，不等于照片物理错误已证明 |
| 内参假设 | K490为同设备沿用值，EXIF/光学模式不提供独立标定，不搜索441/539或用GT定焦距 |
| 原生照片HERO缺失 | 模型/代码/支持输入核验完成，但门禁未过不新推理；TRUSTED面积/新增覆盖NaN，不提供伪深度 |
| 显示接口适配 | 初次FigB传入旧edge工具不支持的第四个参数，TypeError日志保留；只移除无效显示参数后重画，数据/位姿/指标不变 |
| 无绝对部署GT | 不能给绝对位姿/真实表面积/高度/直径误差，MedARE/MAE/P95/max均NOT_EVALUABLE；像素和HERO代理另列 |

'''+audit
 write('FAILURE_LEDGER.md',failure)
 write('REPRODUCE.md',f'''# 快速复核复现

工作目录 `{Q}`；沿用021当前分支，旧021冻结结果只读。Python为 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`，未安装新框架/下载模型。原始大型JPG/Mask/旧视频/权重保留本地并索引。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
Q21={Q}
# 已有FINAL时续优化和照片拟合跳过，不覆盖历史。全新回放先使用独立目录并配置qcommon.Q；先恢复同SHA原始资产。
$PY -B "$Q21/code/solver_review.py"
$PY -B "$Q21/code/evaluate_review.py"
$PY -B "$Q21/code/gradient_isolation.py"
# 照片资产必须显式raw20260805，禁止用同名旧照片。
$PY -B "$Q21/code/photo_assets.py"
$PY -B "$Q21/code/photo_registration.py"
$PY -B "$Q21/code/photo_2d_geometry.py"
$PY -B "$Q21/code/photo_audit.py"
$PY -B "$Q21/code/hero_prepare.py"
$PY -B "$Q21/code/figures_review.py"
$PY -B "$Q21/code/report_review.py"
$PY -B "$Q21/code/verify_review.py"
```

协议见config/SOLVER_PLAN、PHOTO_POSE_PROTOCOL、PHOTO_RGB2D_ADDENDUM；旧sourceSHA见021原始冻结清单及本目录provenance。当前photo_assets为正确批次源码，旧错误尝试全保留但不属于正式输入。正式同批源JPG的完整SHA/Mask与原图绑定见manifest和inputs/*/IDENTITY.json。准入由当前PHOTO_HELD与几何记录决定，不使用旧历史标签阻塞。

所有新文件限定本quick目录；不运行原021准备/优化脚本，不修改DXY/原相机/HERO。HERO清理/官方前向本轮没有执行；hero_prepare只核验和准备，绝不隐式启动推理。大数组/原件/隔离失败产物在本地SHA索引，不宣称全部上传。
''')
 index='# 快速复核结果索引\n\n[摘要](TECHNICAL_REPORT_SUMMARY.md) · [完整求解器报告](SOLVER_REVIEW_REPORT.md) · [方法审计](METHOD_AND_LOSS_AUDIT.md) · [失败台账](FAILURE_LEDGER.md)\n\n'
 for f in sorted((Q/'figures').glob('*.png')):index+=f'- [{f.stem}](figures/{f.name})\n'
 index+='\n[12张照片资产与SHA](INDEPENDENT_PHOTO_ASSET_MANIFEST.csv) · [G01相机审计](G01_PHOTO_POSE_AUDIT.md) · [HERO准备](G01_PHOTO_HERO_AUDIT.md) · [71候选视角表](ALL_VIEW_BODY_ADAPT_READINESS.csv) · [未来单主体方案](ALL_VIEW_BODY_ADAPT_PLAN.md)\n\n数值位姿与候选链：results/photos/G01_photo00*/，原RGB对应与特征ID：photo_features/、ALL_RGB_LANDMARK_MATCHES.json、RGB2D_PER_VIEW_AUDIT；BA目标调用与实际迭代：optimization/；独立原生共同集合：metrics/HERO_EXACT_COMMON_GAINED_LOST.csv。\n\n当前完整本地二进制/失败隔离索引见assets_index/LOCAL_ARTIFACTS.json；原始JPG/视频/权重未复制上传。照片HERO原生文件不存在，不列作成功产物。\n';write('RESULT_INDEX.md',index)
 # Exact local inventory, including explicitly excluded failure evidence.
 bins=[asset(p)|dict(excluded_from_formal_data='WRONG_CAPTURE_COHORT_QUARANTINE'in str(p))for p in Q.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix in ['.npz','.png']];qsave('assets_index/LOCAL_ARTIFACTS.json',bins)
 loc=[]
 for p in(Q/'code').glob('*.py'):
  for n in ast.parse(p.read_text()).body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):loc.append(dict(file=str(p),symbol=n.name,line=n.lineno,SHA=sha(p)))
 qtable('metrics/IMPLEMENTATION_CODE_LOCATIONS.csv',loc);qsave('provenance/DELIVERY_MANIFEST.json',dict(epoch=time.time(),code=[asset(p)for p in(Q/'code').glob('*.py')],reports=[asset(p)for p in Q.glob('*.md')],solver_poses=[asset(Q/'results'/a/'FINAL.json')for a in ['B1','B2','B3']],photo_poses=[asset(Q/'results/photos'/r['id']/'FINAL.json')for r in photo],new_inference_runs=0,source_root_unchanged=True));print('QUICK_REPORTS_COMPLETE',flush=True)
if __name__=='__main__':main()
