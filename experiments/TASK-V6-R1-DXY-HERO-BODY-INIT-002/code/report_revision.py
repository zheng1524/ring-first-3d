"""Concise all-case accounting; no removal of refused relations or difficult inputs."""
from common import *
from collections import Counter
import csv,shutil

def csvout(name,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (T/'evidence'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows([{k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])

def main():
    verified=read(T/'evidence/FINAL_VERIFICATION.json');assert verified['scientific_key']==revision_key() and verified['config_sha256']==sha(T/'config.json')
    repair=read(T/'evidence/SELECTION_ID_REPAIR_FIT_COMPARISON.json')
    q=read(T/'evidence/REGISTRATION_QUALIFICATION.json');dx=read(T/'evidence/DXY_FRAME_INDEX.json');rows=[];groups=[];bias=[];index=[];fail=[]
    for g in q['groups']:
        folder=T/'runs/results'/g['group'];rec=read(folder/'GROUP_RESULT.json');fail+=rec['failures'];grows=[]
        for r in rec['results']:
            out=folder/r['configuration'];ev=read(out/'VISIBILITY.json');base=read(out/'BASE.json');body=np.load(out/'BODY.npz');oldfolder=OLD/'runs/results'/g['group']/r['configuration'];old=None;oldpenetration=None
            if (oldfolder/'VISIBILITY.json').exists():
                oe=read(oldfolder/'VISIBILITY.json');oldpenetration=oe['CAD_vertex_penetration_max_mm'];vals=[x['full_mesh_IoU'] for x in oe['frames'] if x['role']=='HOLDOUT'];old=float(np.mean(vals)) if vals else None
            held=[x['full_mesh_IoU'] for x in ev['frames'] if x['role']=='HOLDOUT'];fit=[x['full_mesh_IoU'] for x in ev['frames'] if x['role']=='FIT'];bs=[abs(x['b_mm']) for x in r['bias']]
            row=dict(group=g['group'],configuration=r['configuration'],videos=r['videos'],coordinate_frame=r['coordinate_frame'],status=r['status'],input_kind=r['input_kind'],source_N=r['source_N'],fit_full_mesh_IoU=np.mean(fit) if fit else None,held_full_mesh_IoU=np.mean(held) if held else None,old001_held_full_mesh_IoU=old,old001_CAD_penetration_max_mm=oldpenetration,base_status=r['base_status'],base_applied=r['base_applied'],base_before_conflict=base.get('original_001_status',base['status']),base_conflict_downgraded=base.get('downgraded_for_conflict',False),base_cut_side_N=base.get('original_trusted_removed_side_N'),base_cut_side_fraction=base.get('original_trusted_removed_side_fraction'),actual_cap_faces=int(body['inferred_base_faces'].sum()),bias_abs_median_mm=np.median(bs) if bs else None,bias_abs_max_mm=max(bs) if bs else None,bias_near_bound_N=sum(x>.39 for x in bs),fixed_depth_N=sum(x['fixed_N'] for x in ev['depth']),invalid_depth_N=sum(x['invalid_N'] for x in ev['depth']),CAD_inside_vertex_N=ev['CAD_inside_vertex_N'],CAD_beyond_tolerance_vertex_N=ev['CAD_beyond_tolerance_vertex_N'],CAD_penetration_max_mm=ev['CAD_penetration_max_mm'],seconds=r['seconds'],GT='NOT_EVALUABLE')
            rows.append(row);grows.append(row);bias.extend(dict(group=g['group'],configuration=r['configuration'],**x) for x in r['bias'])
            index.append(dict(group=g['group'],configuration=r['configuration'],videos=r['videos'],path=str(out/'RESULT.json'),sha256=sha(out/'RESULT.json'),coordinate_frame=r['coordinate_frame'],qualification=r['qualification']['status']))
        groups.append(dict(group=g['group'],videos=len(g['videos']),eligible_components=[c['videos'] for c in g['joint_components']],initializations=len(grows),not_run=rec['not_run'],failures=rec['failures']))
    singles=[r for r in rows if len(r['videos'])==1];joints=[r for r in rows if len(r['videos'])>1];babs=np.array([abs(x['b_mm']) for x in bias]);comparison=[]
    for r in joints:
        ss=[s for s in singles if s['group']==r['group'] and s['videos'][0] in r['videos']];delta=r['held_full_mesh_IoU']-np.mean([s['held_full_mesh_IoU'] for s in ss]);comparison.append(dict(group=r['group'],configuration=r['configuration'],videos=r['videos'],joint_full_mesh_IoU=r['held_full_mesh_IoU'],single_mean_full_mesh_IoU=np.mean([s['held_full_mesh_IoU'] for s in ss]),delta=delta))
    summary=dict(groups=len(groups),videos=sum(g['videos'] for g in groups),single=len(singles),joint=len(joints),configurations=len(rows),failures=len(fail),relation_states=Counter(e['status'] for g in q['groups'] for e in g['edges']),DXY_completed=dx['completed'],DXY_statuses=dx['statuses'],DXY_failures=len(dx['failures']),base_states=Counter(r['base_status'] for r in rows),actual_cuts=sum(r['actual_cap_faces']>0 for r in rows),base_conflict_downgrades=sum(r['base_conflict_downgraded'] for r in rows),base_hard_clip_prevented=sum(r['base_conflict_downgraded'] and r['base_before_conflict']=='RELIABLE' for r in rows),only_2D=sum(r['input_kind']=='DXY_MASK_2D_ONLY' for r in rows),bias_abs_median_mm=float(np.median(babs)),bias_abs_max_mm=float(babs.max()),bias_near_bound_N=int((babs>.39).sum()),fixed_depth_N=sum(r['fixed_depth_N'] for r in rows),invalid_depth_N=sum(r['invalid_depth_N'] for r in rows),CAD_penetration_configs=sum(r['CAD_beyond_tolerance_vertex_N']>0 for r in rows),joint_improves_single=sum(r['delta']>0 for r in comparison),joint_comparison_denominator=len(comparison))
    pairs=[r for r in rows if r['old001_CAD_penetration_max_mm'] is not None]
    summary.update(CAD_paired_configurations=len(pairs),old_CAD_above_tolerance=sum(r['old001_CAD_penetration_max_mm']>.05 for r in pairs),new_CAD_above_tolerance=sum(r['CAD_penetration_max_mm']>.05 for r in pairs),CAD_max_improved=sum(r['CAD_penetration_max_mm']<r['old001_CAD_penetration_max_mm']-1e-6 for r in pairs),CAD_max_worsened=sum(r['CAD_penetration_max_mm']>r['old001_CAD_penetration_max_mm']+1e-6 for r in pairs))
    save(T/'evidence/SUMMARY.json',summary);save(T/'evidence/FULL_STATUS.json',groups);save(T/'evidence/FAILURES.json',fail);csvout('CONFIGURATION_RESULTS.csv',rows);csvout('GROUP_COMPARISON.csv',comparison);csvout('SOURCE_BIASES.csv',bias)
    save(T/'INITIALIZATION_INDEX.json',dict(schema='R1_BODY_INIT_002_QUALIFIED',units='mm',consumer='code/consume_revision.py',qualification=asset(T/'evidence/REGISTRATION_QUALIFICATION.json'),configs=index,groups=groups,old_001_joint_is_not_accepted=True,evaluation_scope='2D omitted frames only; qualification uses prior HELD; not independent end-to-end test'))
    figures=T/'figures';figures.mkdir(exist_ok=True)
    examples=[('QUALIFIED','GP_IIa_14.0mm_closed_R5_single_refY','JOINT'),('REJECTED','GP_IIa_22.0mm_closed_R10_single_refY','005'),('BASE_CONFLICT','GP_IIa_5.2mm_closed_R10_single_refY','001')]
    for label,g,c in examples:
        for n in ['RGB_PROJECTIONS.png','GEOMETRY_SECTIONS.png']:
            src=T/'runs/results'/g/c/n
            if src.exists():shutil.copyfile(src,figures/(label+'_'+n))
    text=f'''# R1 初始化修正 002

本轮完成 {summary['groups']} 组、{summary['videos']} 视频的 **{summary['single']} 个本地单视频 + {summary['joint']} 个合格子集联合**，共 {summary['configurations']} 个新粗初体；执行失败 {summary['failures']}。全帧二维完成 {dx['completed']}/1700，状态 {dx['statuses']}。未启动高自由度更新。

## 先判断关系，再初始化

原 40 条关系统一按任务书尺度复核：{dict(summary['relation_states'])}。复用 27 条哈希核验的旧评价，对新增 13 条使用冻结 metrics2 同缓存补算；没有匹配、三角化或求新 T。62 个旧 T 与17个新增视频输入分别核验。CONNECTED 不改称历史 PASS。P95>30px仅尾部提示；缺值不按0处理。留出证据用于本轮使用判定，不再宣称端到端独立测试。

所有79个单视频在自身 VIDEO_LOCAL 坐标运行：相机、HERO采样与背景同时移回本地，不使用被拒共同 T。仅合格组件使用 inv(T_anchor)@T_video；14个联合中13个覆盖全组，Ip4/R5仅005+006，007单独，全组联合槽 NOT_RUN。IIa22/R10、Is7/R5、IIa9.5/R5、Is14/R5均未联合；前两组证据不足且残差很大，分类 INCONCLUSIVE，不表示接近通过。具体关系、失效分母和Ring结果见 [资格表](evidence/REGISTRATION_QUALIFICATION.csv) 与 JSON。

## 二维依据恢复到了什么程度

逐帧真实执行冻结 DXY@75d58ca 的 observe_files，保留原 P/Q/X 轮廓身份、Q法向区间、完整 ObservedMeasurement 候选池与实际选择 ID。no-Q 分支保留原 exact_V2 的真实求解候选，不以 variants 摘要代替完整池。完整可核验缓存才复用。官方无候选帧调用原 observable_P 与 exact_v2.geometry 的像素出口，真实拟合圆/椭圆，标 PIXEL_ONLY；不伪造 ring.valid，不输出毫米测量。

原32个缺曲线帧恢复29个PIXEL_ONLY，3个仍不可解。全1700帧中，1324个官方候选达到内部normal_Gate，303个属于Q冲突恢复；1289个strict_stable、135个P=0推断与这些类别有重叠，均不代表真实几何已验证。共1693帧生成曲线，7帧无曲线。

原790帧三维FIT/留出角色保持；新增910帧仅扩大二维计算覆盖，未自动加入三维拟合。二维主体用于形状起点与补全先验，P才作等式可见边界，Q沿原法向区间，X不作真实轮廓。profile及当前仍被拒绝的候选不作监督；官方恢复候选保留历史拒绝原因，恢复和像素出口统一降低软权重。OFFICIAL仅表示官方流程实际选出候选，不等于可靠几何或正式毫米测量通过；质量分级与measurement_eligible另行保留。全1700帧索引及逐帧过程入口位于 runs/review/index.html；不可解与不可靠状态按实记录。

完整性复核发现旧包装器用近似数值匹配候选 ID，1700帧中363帧指向邻近候选。已改为实际返回对象身份捕获，并将旧缓存与唯一精确参数记录核对；全部曲线、选中中心/basis/权重和官方导出字节不变。原数值执行源码与迁移回执分别保存，不把元数据迁移称为重新运行DXY。随后按新科学键真实复算全部93个初体：九参数最大差 {repair['max_parameter_abs_delta']:.3g}，来源偏置最大差 {repair['max_bias_abs_delta_mm']:.3g}mm。详见 [迁移证据](evidence/DXY_SELECTION_METADATA_MIGRATION.json) 和 [复算比较](evidence/SELECTION_ID_REPAIR_FIT_COMPARISON.json)。

## 拟合修正与受控证据

复用001九参数 Problem、历史A1几何、009平面和010精确三角裁切；新增代码在独立任务中适配。源偏置保持D-b沿原像素射线，不动相机、Ring、背景和Raw/Clean；sigma_b=.8mm、sigma_D=.25mm、加权共同偏移sigma=.15mm，上界仍±.4mm。b子问题与theta接受检查使用同一完整目标，含robust(q+h(b))和共同偏移代价。只依据既有虚拟G01控制统一选参，真实病例无单独参数。

实际虚拟theta/b优化：零注入平均|b|约0.0101mm；±.25mm注入得到[.2270,.2048,-.2328,-.2138]mm，平均绝对误差0.0304mm。固定真实几何仍调用同一带先验求解器，最大偏差0.0223mm；没有用median(D-GT)替代优化。非零注入条件中，错误高度214/512、翻侧509/512切侧观测及整主体裁除失败保留。控制结果见 [CONTROL_REVISION](evidence/CONTROL_REVISION.json) 和 [控制图](figures/CONTROL_BIAS.png)，不能外推为真实深度已校准。

CAD射线遮挡和容忍0.05mm后的穿入代价进入实际优化，交付Mesh另做同约定的可见性复核。背景稳定性还需与切侧距离、Target一致性合看；明显冲突降为候选，不再强推b迎合平面。{summary['base_conflict_downgrades']}个配置触发冲突诊断，其中{summary['base_hard_clip_prevented']}个从原可靠判据转为弱候选；{summary['actual_cuts']}个发生真实裁切；无平面仍初始化。背景未随b移动，但仍可能与前景共享HERO深度误差；RELIABLE只是内部证据标签，不是独立组织基底真值。底盖标为推断，不作HERO深度监督。合格联合比较粗起点与单视频解，固定同一p0正则参考和完整拟合目标，不按留出或GT选解。

## 结果与残留问题

{summary['only_2D']}个配置只有二维约束。实际|b|中位数 {summary['bias_abs_median_mm']:.4f}mm、最大 {summary['bias_abs_max_mm']:.4f}mm，{summary['bias_near_bound_N']}个来源配置接近上界（>0.39mm）；接近界限提示模型/观测冲突，不能解释为精确校准。唯一物理组分母39，源存在共享Target/Support相关性；单/联合重复来源不算独立样本。

固定源像素分母合计{summary['fixed_depth_N']}（配置间有重复），实际三角Mesh未解释{summary['invalid_depth_N']}，未删掉无交点、底盖或CAD遮挡样本。{summary['CAD_penetration_configs']}个配置仍有模型顶点超过CAD穿入容忍；这只是顶点采样检查，不是完整三角碰撞证明。在可对应的{summary['CAD_paired_configurations']}个配置中，超过0.05mm的配置由001的{summary['old_CAD_above_tolerance']}个变为{summary['new_CAD_above_tolerance']}个；最大穿入降低{summary['CAD_max_improved']}个、升高{summary['CAD_max_worsened']}个，负例不删除。早期一个二维缓存回执误收迁出的展示文件曾拦截Ip10.3/R5的004及联合；修复回执、保持科学字节不变后重跑，原失败与修复回执另存，不从运行历史抹掉。完整分母、前后偏置、基底、参数与不利案例在 [配置表](evidence/CONFIGURATION_RESULTS.csv)。

合格联合中，{summary['joint_improves_single']}/{summary['joint_comparison_denominator']}组全分辨率二维留出轮廓指标优于参与单视频平均。这些帧只从显式二维项留出，可能仍是HERO Target/Support、Clean或相机输入，不能称独立测试。001比较列保留原值，但本轮修正二维证据、坐标路由和目标，差异不是单因素因果结论。

## 审阅、接口及下一步

本地入口 runs/results/index.html，先各视频二维过程与单视频，再合格联合。全部HTML和PNG内部单列；RGB只有紫色算法二维主体和绿色交付三角Mesh可见投影。绿色内部遮挡边界来自主体可见区域，不是额外叠画CAD。几何图保留固定CAD、原始/校正HERO、完整母体、切侧、底盖及真实截面；不同本地视频不叠成已配准场景。

精选：[合格联合投影](figures/QUALIFIED_RGB_PROJECTIONS.png)、[合格联合截面](figures/QUALIFIED_GEOMETRY_SECTIONS.png)、[拒联合后的单视频](figures/REJECTED_RGB_PROJECTIONS.png)、[冲突基底](figures/BASE_CONFLICT_GEOMETRY_SECTIONS.png)、[真实像素恢复过程](figures/DXY_PIXEL_ONLY.png)、[实际无曲线失败](figures/DXY_NO_CURVE.png)。

INITIALIZATION_INDEX.json与code/consume_revision.py是本轮正式粗初始化入口，旧001失败联合不会被接受。消费者核验科学键、资格、配置、相机、原图/Mask、完整DXY过程、源OBS与Raw/Clean来源SHA。实际基础提交3b8610075a4959a32097cca83247faaddbf61aa1，科学执行提交见FULL_RUN_FREEZE.json。R1、M4、DXY与旧输出均只读，复用表/命令见EXECUTION_PLAN与README。

**已验证**：资格先行、LOCAL隔离、全帧真实二维流程、受控偏置修正、可逆精确裁切与两类线竖排展示。**初步有效**：部分合格组的共同轮廓拟合。**仍需研究**：接近偏置界限、CAD穿入、弱基底和椭球无法解释的蒂部。**当前不可评价**：真实部署形状/基底绝对精度。下一轮优先检查保守有界b的跨视角证据及剩余CAD/基底矛盾，再决定是否开展高自由度更新。
'''
    (T/'TECHNICAL_REPORT.md').write_text(text);print(json.dumps(clean(summary),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
