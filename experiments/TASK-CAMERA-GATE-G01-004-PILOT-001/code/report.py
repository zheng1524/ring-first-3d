"""Camera-only report; all failure identities/denominators and no GT measurement."""
from common import *
def num(x,n=2):return 'NaN' if x is None else f'{x:.{n}f}'
def main():
    original=load(R/'config/ORIGINAL_TEST12.json');qual=load(R/'config/ORIGINAL_QUALIFICATION.json');aux=load(R/'config/HERO_AUXILIARY.json');obs=load(R/'config/ORIGINAL_OBSERVABILITY.json');corr=load(R/'config/BOUNDED_CORRECTION_RESULTS.json');plans=load(R/'config/RGB_ONLY_METHOD_SELECTION.json')
    old={r['source_id']:r['camera_status'] for r in csv.DictReader((A/'metrics/E3_CAMERA_QUALIFICATION.csv').open())};rows=[];summary=[]
    for cid in IDS:
        ringr=next(r for r in original['Ring'] if r['camera']==cid);relations=[r for r in original['pairs'] if r['selected_for_gate'] and cid in [r['A'],r['B']]]
        actual={r['B'] if r['A']==cid else r['A'] for r in relations};missing=sorted((set(BASE)-{cid})-actual)
        ca=next((r for r in corr if r['camera']==cid),None);a=IDS[0] if cid==IDS[1] else IDS[1];her=next(r for r in aux if r['source']==a and r['target']==cid and r['target_pose']=='ORIGINAL');st=ringr['visible_contour'];status='CORRECTION_CANDIDATE' if ca and ca['status']=='CORRECTION_CANDIDATE' else qual[cid]['original_status']
        rows.append(dict(camera=cid,original_qualification=old[cid],Ring_median_px=st['median'],Ring_MAE_px=st['MAE'],Ring_p95_px=st['p95'],Ring_pass=ringr['Ring_pass'],Ring_clear_contradiction=ringr['clear_contradiction'],Ring_center_mask_centroid_difference_px=ringr['centroid_difference_px'],Ring_observed_axis_ratio=ringr['observed_shape']['minor_major_ratio'],Ring_CAD_axis_ratio=ringr['CAD_shape']['minor_major_ratio'],image_geometry=[dict(other=r['B'] if r['A']==cid else r['A'],method=r['method'],extra_holdout=r['extra_holdout'],fit=r['groups']['fit'],held=r['groups']['held'],passed=r['pair_pass'],clear_contradiction=r['clear_contradiction'],near_planar_or_low_parallax=r['near_planar_or_low_parallax']) for r in relations],missing_sufficient_required_relations=missing,data_only_local_rank=obs[cid]['rank'],data_only_min_singular_ratio=obs[cid]['relative_min_singular_value'],HERO_aux_source=a,HERO_target_Polyp_denominator=her['target_Polyp_denominator'],HERO_target_coverage=her['target_Polyp_coverage'],HERO_projection_precision=her['projected_Polyp_precision'],HERO_CAD_hidden=her['CAD_hidden'],HERO_used_for_qualification=False,correction_status=ca['status'] if ca else 'NOT_ELIGIBLE_OLD_REFERENCE_DIAGNOSTIC_ONLY',optimizer_calls=ca['optimizer_calls'] if ca else 0,corrected_pose='NaN' if not ca or 'corrected_c2w' not in ca else ca['corrected_c2w'],new_status=status,reasons=qual[cid]['reasons'],original_camera_overwritten=False,absolute_pose_certified=False))
        summary.append(f"| {short(cid)} | {'历史条件性' if cid in BASE else '未经验证'} | {st['median']:.2f}/{st['p95']:.2f} px；{'通过' if ringr['Ring_pass'] else '未通过'} | {sum(r['pair_pass'] for r in relations)}/{len(BASE)-int(cid in BASE)} 必需关系通过 | {her['target_Polyp_coverage']:.1%}/{her['projected_Polyp_precision']:.1%} | 未修正 | `{status}` |")
    table('CAMERA_QUALIFICATION.csv',rows);save('config/FINAL_CAMERA_QUALIFICATION.json',rows)
    detailed=[]
    for r in original['pairs']:
        for split in ['all_usable','fit','held']:
            g=r['groups'][split];detailed.append(dict(A=r['A'],B=r['B'],method=r['method'],selected=r['selected_for_gate'],extra_holdout=r['extra_holdout'],split=split,N=g['N'],median_px=g['error_px']['median'],p95_px=g['error_px']['p95'],inlier_N=g['inlier_N'],inlier_fraction=g['inlier_fraction'],coverage_A=g['coverage_A'],coverage_B=g['coverage_B'],parallax=g['parallax_deg'],positive_fraction=g['positive_fraction'],pair_pass=r['pair_pass'],sufficient=r['sufficient'],homography_fraction=r['homography_F_consensus_fraction']))
    table('config/IMAGE_GEOMETRY_ALL_METHODS.csv',detailed)
    detail=[]
    for p in plans:
        method=p['selected_method'] or 'SIFT';r=next(r for r in original['pairs'] if r['A']==p['A'] and r['B']==p['B'] and r['method']==method);f,h=r['groups']['fit'],r['groups']['held']
        detail.append(f"| {short(p['A'])} ↔ {short(p['B'])} | {method}{'（数据不足，不作资格票）' if not p['selected_method'] else ''} | {f['N']}/{h['N']} | {num(f['inlier_fraction'],3)}/{num(h['inlier_fraction'],3)} | {num(h['error_px']['median'])}/{num(h['error_px']['p95'])} | {'通过' if r['pair_pass'] and p['selected_method'] else '不足/未通过'} |")
    hashes=sha(R/'config/protocol.json');measures='本轮不执行直径或形状测量；MedARE、MAE、p95、最大测量误差均NaN；共同测量成功组N=0。'
    text=f'''# G01_004 Camera Gate Pilot 技术报告

日期：2026-11-02（Asia/Shanghai）。任务 `TASK-CAMERA-GATE-G01-004-PILOT-001`，继承E3-C提交 `{cfg['parent_commit']}`，独立分支 `exp/TASK-CAMERA-GATE-G01-004-PILOT-001`。

**结论：本轮没有证明两个新增参考存在实际位姿错误。按冻结v0.1试行规则，五份相机均为INSUFFICIENT_EVIDENCE。** 三份旧参考与growth_r04通过Ring，但旧ref03相关图像关系对匹配器/2px内点门槛敏感；new_r00只有到ref03的充分对应，Ring略超容差；growth_r04在ref03/ref08关系良好，ref13额外留出对应不足。未满足明确错误触发条件，**优化器调用0次**，没有修正相机输出。数值检查通过与相机取得资格是两个独立结论。

本轮返回的是新试行规范下的资格，**不覆写或撤销历史资格，不把旧相机变成GT**。没有重估轨迹、BA/SLAM、新神经匹配/HERO推理、GPU、全局场、几何变形、GT/Oracle或Dxy操作。F1/F2/F3从未作为输入。完成后停止等待PM。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1物理组G01、1视频004、固定5相机（3旧+2新增），不含其他6候选 |
| 本算法独立成功 | 5/5完成相机证据计算；新资格通过0/5；不能将数值完成等同物理准确 |
| 本算法失败 | 5/5资格未获充分证明，全部INSUFFICIENT_EVIDENCE；认证/修正位姿NaN；原相机仅作冻结候选保留 |
| 历史测量值回退 | 0；无S0/V2/照片直径/融合预测补齐 |
| 失败组及具体原因 | G01_004逐相机见[失败记录](FAILURE_LEDGER.md)及[三图](#核心图) |
| 最终统计样本 | 全5相机、9图像对、20原HERO辅助有向投影；测量成功0/1；{measures} |
| 是否使用GT选择算法 | 否；正式计算前冻结协议/资产/匹配计划，参数SHA `{hashes}`；未依结果换匹配器或视角 |

## 五相机汇总

| 相机 | 原资格 | Ring 中位/p95 | 图像几何 | HERO覆盖/精确率（辅助） | 修正前后 | 新判断 |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(summary)}

HERO栏的“精确率”仅指原XYZ投影落入目标Polyp Mask的像素比例，不是三维正确率；全20投影在[辅助结果](config/HERO_AUXILIARY.csv)。汇总采用固定source ref08，目标ref08时用ref03，未按覆盖/误差选视角。没有HERO辅助指标进入相机资格判定。

## 输入与继承

直接复用E3-A身份/K/c2w/CAD与相机表、View Partition匹配器函数、V13原始匹配缓存、Phase D原色点投影raster和`real_p0_renderer`/`SameCameraScene`。只AST抽取必要函数，未执行历史main。[身份表](config/INPUT_IDENTITY.json)、[输入SHA](config/INPUT_HASHES_BEFORE.json)、[复用记录](config/CODE_REUSE.json)保留路径和SHA。

五份图像逐文件及解码尺寸绑定到同一冻结缓存身份，640×360；相机Xc=(Xw−C)R，c2w=(R,C)，轴向Z和XYZ单位mm，整数像素中心，K不加半像素偏移。相机包、HERO原始包的K/pose及元数据数值一致。历史 `G01_video004_LOCAL_RING_MM` 与 `G01_004_LOCAL_RING_MM` 视为已核验数值一致的同源别名，不进行坐标拟合。**缓存RGB身份充分，原视频逐帧号身份仍未独立认证**；没有为此重新解码或重新审计整段视频。固定K490及无新畸变校准仍是条件。

原3参考的相机上游均是冻结模型候选，历史筛查不是相机GT。Ring CAD是唯一固定公制参考，不以任何融合Mesh或HERO距离反向证明相机。

## Test 1：Ring

使用原始CAD全分辨率真实射线首次交点生成不透明投影；Ring Mask轮廓和CAD轮廓双向最近距离，报告中位、MAE、p95、原始未剔除统计。Polyp接触2px内及图像裁剪边界不作可观察Ring轮廓；没有把接触边缘当作真实环轮廓。可观察轮廓双向至少100点，MAE≤3px、p95≤6px；继承V13容差，明确矛盾阈值为MAE>6或p95>12px。Ring中心采用Mask/CAD像素质心差，形状采用二阶矩轴比与不含Polyp域IoU，**仅作描述**，部分遮挡会偏置质心。

new_r00的MAE=3.35px、p95=6.71px，属于容差未过而非本轮明确矛盾。其他四份通过。Ring旋转对称，不能据此认证完整六自由度或世界yaw。保留原CAD，未改Ring参数。

## Test 2：真实RGB几何

9个固定配对：原3两两3对，2新增分别对ref03/ref08/ref13共6对，不增加其他视角。复用4个SIFT缓存（含View Partition的new_r00↔ref03），补充5个CPU SIFT配对；只读复用原3的LightGlue/MASt3R/RoMa及new_r00↔ref03的MASt3R缓存，**没有运行任何神经匹配器**。缓存优先级固定SIFT→LightGlue→MASt3R→RoMa，仅按RGB-only F对应数量/覆盖充分性选择，不按候选位姿误差选获胜方法。全部匹配器输出保留在[完整结果](config/IMAGE_GEOMETRY_ALL_METHODS.csv)。历史SIFT缓存的检测Mask策略有差异，后处理语义规则统一，不能将匹配器差异解释成相机真值差异。

用同语义非Ring、非高光、图内点，按固定16px hash留出约20%；在非留出点拟合RGB-only Fundamental RANSAC（2px，seed0，2000次上限）。fit/held分别至少12/8个F相容点、各图≥4个32px格、凸包≥1%图像；pose判断使用这些**不由候选pose筛选**的对应及全部可用对应的原始统计。F筛查是真实RGB模型拟合，不是物理对应GT。ref13整对不进入本轮位姿拟合；对ref13自身做F诊断不等于调整它的位姿。它是本轮额外留出，**不是整个历史管线从未见过的盲测**。

| 图像关系 | 固定主方法 | F合格fit/held N | ≤2px内点比例fit/held | held中位/p95 px | 关系结论 |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(detail)}

相机预测F=Kb^(-T)[t]×Rrel Ka^(-1)，报告平方根Sampson像素误差，fit/held中位≤3px、p95≤6px、≤2px内点率≥70%；实际两相机射线视差中位≥0.5°，三角化正深度≥95%。同时报告RGB-only homography相容比例≥90%及低视差退化，匹配覆盖与数值秩均不替代物理对应身份。

ref03↔ref08主SIFT的fit/held内点率41.7%/40.0%；ref03↔ref13固定回退LightGlue为56.3%/72.2%，均未过完整关系门槛，**但没有达到明确矛盾阈值**。ref08↔ref13通过。历史MASt3R在ref03两对均可通过；RoMa结论亦有差异。此差异保留为不确定性，不能事后换主方法使旧参考通过，也不能据SIFT未过就断言ref03实际错误。

new_r00↔ref03通过；到ref08/ref13仅11/5个raw SIFT点，无法建立独立F验证。growth_r04↔ref03/ref08通过；到ref13有36个raw点，但F相容fit/held仅26/3，且留出覆盖不足，未达到冻结充分性规则。**ref13整对作为额外视角并不允许事后取消该对预注册的空间留出检查。**

## 可观测性与有界修正

采用已有解析torus轮廓函数，并检查其与原CAD表面方程一致；仅用于局部导数与可能修正，正式Ring评分始终用原Mesh raycast。Ring残差必须保留已知共同世界yaw零空间；消除有限曲线采样产生的伪导数后计算Ring+真实匹配**无先验**Jacobian SVD，旋转/平移列尺度5°/.5mm，相对奇异值门槛1e-3。五份局部分支秩均6；不意味着全局Ring对称性、共同参考系统偏差、匹配身份或K畸变已被证明。单独Ring至多秩5。HERO不参与此秩或修正。

两个候选均未满足“明确的FIT侧几何错误”触发条件。new_r00还缺两拟合参考约束，因此均NOT_ATTEMPTED。未进行SE(3)优化，修正前后数值不存在，不能拿原相机冒称修正成功。已实现的有界薄适配采用成熟SciPy soft_l1、冻结初值、最多60次评估、总旋转≤5°/平移≤.5mm、固定Ring与K；只拟合ref03/ref08非留出图像点，不以HERO距离优化。参数/边界不会因留出结果改变。本轮未触发的优化路径**未获得真实修复效能验收**。

## Test 3：HERO辅助

前两项原始结果冻结后才读取原始HERO XYZ；核验XYZ由已归档原深度直接反投影，无清理替代、融合、SE3形变或重新推理。五视角20个有向投影均完成，Phase D原色点raster保持原始点ID、真实目标K/c2w和CAD首次交点。固定目标Polyp像素分母，同时报告投影覆盖、落Mask比例、CAD挡住的点数和RGB误差。

辅助结果显示可见Polyp投影可以较好落Mask，但覆盖不等于几何正确或相机已认证。原点集仅Polyp：主SIFT对应很多在背景，XYZ匹配偏移可计算数很少或0，明确保留N=0/NaN，不能以此证明不存在系统偏移。Mask覆盖、RGB误差同时受HERO形状、可见性和真实对应影响，**不能单独归因位姿**，也没有反馈进前两项。

## 验证与复现

[工程验证](config/VALIDATION_RESULTS.json)共25项通过，包括像素/轴向深度/相机F方向控制、Ring连续yaw对称、缓存匹配坐标与输入SHA、ref13必需身份、无HERO资格反馈、原始固定分母和历史工作树保护。[隔离CPU复现](config/REPRODUCTION_VALIDATION.json)对六类完整数值/决策结果逐项精确一致。工程通过不是相机认证：新资格仍0/5，优化器0次。三图经过实际视觉核对，全部来自本轮真实RGB/原CAD/原XYZ。

## 必须回答的四个问题

1. **三个旧参考是否仍具条件性资格？** 历史状态保留；在本轮更完整且预先冻结的v0.1试行标准下，三者均未取得完整COND，主因ref03相关关系的主方法内点比例不足，非Ring失效、非已证明实际错误。ref08↔ref13本身通过。
2. **两个新增参考失败在哪里？** new_r00是Ring边界略超容差，加ref08/ref13对应不足；growth_r04的Ring和ref03/ref08真实图像关系通过，但ref13空间留出证据不足。两者均INSUFFICIENT_EVIDENCE，不硬判几何错误。
3. **是否有无需大改即可恢复资格的候选？** growth_r04是现有最接近者：无需发现新的几何修正就能解释两个拟合参考，但仍需ref13充分且独立的图像几何证据，不能现在恢复资格。没有实际得到或认证的修正候选。本轮不扩展匹配搜索。
4. **哪些可用于统一Gate？** SHA/坐标/图像身份、可见Ring边界、深度独立RGB几何、拟合/额外留出分离、覆盖/退化/无先验秩、受限修正与HERO仅辅助的接口和四状态语义可作为统一流程候选。具体阈值、matcher缺失策略与跨匹配器一致性尚需PM/研究者审核；**v0.1不自动成为所有组正式冻结标准**。

## 核心图

- [Figure 1：五相机Ring验证](figures/Figure1_Ring_validation.png)
- [Figure 2：全部九对真实匹配及额外留出](figures/Figure2_real_matching_geometry.png)
- [Figure 3：原始HERO三维投影](figures/Figure3_original_HERO_projection.png)

完整失败及工程修复记录见[FAILURE_LEDGER](FAILURE_LEDGER.md)；[统一流程候选](CAMERA_GATE_PROTOCOL_v0.1.md)；[复现说明](REPRODUCE.md)；[资格表](CAMERA_QUALIFICATION.csv)。未删除失败、未扩展来源、未调阈值或评价规则制造PASS。
'''
    (R/'TECHNICAL_REPORT.md').write_text(text)
    ledger='''# Failure ledger

资格不足是科学结果，不用工程PASS替代。没有认证的新位姿，正式修正输出NaN，所有原始输入保留。

| 相机 | 步骤与原因 | 解释限度 | 证据 |
| --- | --- | --- | --- |
| ref03 | Ring通过；与ref08主SIFT fit/held内点41.7%/40.0%，与ref13 LightGlue fit56.3%低于70% | 有中等残差且方法依赖；不足以归因实际pose错误 | [全部方法](config/IMAGE_GEOMETRY_ALL_METHODS.csv)、[Fig2](figures/Figure2_real_matching_geometry.png) |
| ref08 | Ring通过；与ref13通过，与ref03主方法未过 | 两视图关系不能唯一归因哪一相机错误 | [原始完整结果](config/ORIGINAL_TEST12.json)、[Fig2](figures/Figure2_real_matching_geometry.png) |
| ref13 | Ring通过；与ref08通过，与ref03主LightGlue未过 | 历史相机非GT，额外留出未用于本轮pose拟合 | [Fig1](figures/Figure1_Ring_validation.png)、[Fig2](figures/Figure2_real_matching_geometry.png) |
| new_r00 | Ring MAE3.35/p956.71px略超容差；到ref08/ref13仅11/5 raw SIFT点；无独立F与充分覆盖 | 到ref03通过；尚未达到明确矛盾，不能宣称实际位姿错 | [匹配充分性](config/RGB_ONLY_METHOD_SELECTION.json)、[Fig1](figures/Figure1_Ring_validation.png) |
| growth_r04 | Ring及ref03/ref08通过；ref13 raw36、F相容fit26/held3，held不足8及覆盖不足 | 无明确拟合侧误差，不为取得数值而修正；保留候选 | [Fig2](figures/Figure2_real_matching_geometry.png)、[Fig3](figures/Figure3_original_HERO_projection.png) |

## 工程事件与保留记录

- ENG01：新worktree初次sparse-checkout缺少其独立git管理目录info，命令失败，无历史文件改动。建立本worktree自身info后成功，未重置或清理其他工作树。
- ENG02：初版资格reducer只检查两条关系，遗漏新增相机必须有ref13的冻结身份条件，曾临时将growth_r04记为CONDITIONAL。交付前复核发现并修复；恢复所有必需身份检查，最终INSUFFICIENT。**不是修改阈值**。保留初版文件SHA及前后状态，[实现修复记录](config/ADJUDICATION_IMPLEMENTATION_FIX.json)。所有指标、配对和优化触发均未改变，优化器仍0次，未重新搜索。
- 原始Test12结果、原始无先验秩、两次NOT_ATTEMPTED原因和初版状态均保留；历史before-correction freeze中的初版状态不能当最终资格，最终以CAMERA_QUALIFICATION.csv为准。
- 辅助匹配偏移：原HERO点只有Polyp，部分主SIFT主要落背景，N=0明确保留，不补背景融合几何。稀疏投影孔洞不补面，不将高Mask精确率当物理准确。

没有训练/模型/网络推理错误，因为本轮未调用这些功能。没有为了提高通过率更换来源、追加匹配器推理、扩大边界或修改标准。
'''
    (R/'FAILURE_LEDGER.md').write_text(ledger)
    print('REPORT_AND_QUALIFICATION_COMPLETE',len(rows),'all fixed cameras',flush=True)
if __name__=='__main__':main()
