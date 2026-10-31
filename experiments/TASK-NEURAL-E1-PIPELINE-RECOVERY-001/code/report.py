"""Build the one Chinese technical report from actual CPU result artifacts."""
from common import *
import re

def main():
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');c0=load(R/'metrics/C0_SUMMARY.json');sf=load(R/'metrics/SDF_GATE_STATUS.json');mf=load(R/'metrics/MAP_GATE_STATUS.json');validation=load(R/'metrics/FINAL_VALIDATION.json')
    refs=D['references'];prop=load(R/'provenance/G01_PROPOSED_INPUTS.json')['proposals'];pairs=list(csv.DictReader((R/'metrics/REFERENCE_COVISIBILITY.csv').open()));mr=list(csv.DictReader((R/'metrics/MAP_GEOMETRY_ADAPTER_CONTRACT.csv').open()))
    stage=load(R/'provenance/SOURCE_COMMITS.json');old=list(csv.DictReader((R/'metrics/E0_M3_FAILURE_RECHECK.csv').open()))
    group=[]
    for g in ['G01','G06','G08','G07']:
        rr=[c for c in refs if c['group']==g];eligible=0 if g=='G07' else len(rr)
        group.append(dict(group=g,physical_group_N=1,video_scene_N=len({c['scene_id']for c in rr}),AUDITED_N=len(rr),
            ELIGIBLE_N=eligible,eligibility='UNQUALIFIED_STRESS_ONLY' if g=='G07' else 'LIMITED_CONDITIONAL' if g=='G08' else 'NORMAL_CONDITIONAL',
            ADAPTER_TESTED_N=sum(r['scene'].startswith(g)for r in mr),MODEL_RUN_N=0,SCIENTIFIC_SUCCESS_N='NOT_EVALUATED',
            numeric_raster_success_N=sum(r['scene'].startswith(g) and r['status']=='LEGAL_DERIVED_DEPTH'for r in mr),
            independent_measurement_success_N=0,diameter_mm=np.nan,absolute_relative_error=np.nan,
            strict_holdout_N=0,historical_measurement_fallback_N=0))
    table('metrics/FOUR_GROUP_STATUS.csv',group)
    table('metrics/PHYSICAL_MEASUREMENT_STATISTICS.csv',[dict(target_physical_groups=4,independent_measurement_N=0,independent_coverage=0.,
        median_absolute_relative_error=np.nan,MAE_mm=np.nan,p95_mm=np.nan,maximum_mm=np.nan,paired_common_success_N=0,
        paired_comparison='NOT_EVALUABLE_NO_NEW_MODEL_OR_MEASUREMENT',historical_fusion_in_baseline='E0 only; F3_Joint includes historical fusion',
        current_predictions='NONE; no measurement or GT accessed')])
    gates=[
      ('C0-01','GATE_PASS','独立分支、基点/来源SHA、旧工作树状态及哈希','provenance/SOURCE_COMMITS.json'),
      ('C0-02','GATE_PASS','36/36真实来源与native链；display别名另纠正','metrics/NATIVE_DEPTH_AUDIT.csv'),
      ('C0-03','GATE_PASS','Raw/Cleaned/F1/F2/F3父系，不增加独立观察数','provenance/E1_SOURCE_DAG.json'),
      ('C0-04','PASS_WITH_LIMITATIONS','两视频各3真实候选，有角度/共视；深度冲突显著','metrics/REFERENCE_COVISIBILITY.csv'),
      ('C0-05','PASS_WITH_LIMITATIONS','G06/G08/G07分层；三照片未认证；两视频未融合','provenance/PHOTO_QUALIFICATION.json'),
      ('C0-06','HOLDOUT_STRICT_UNAVAILABLE','strict holdout=0；raw00351/raw00293污染确认','provenance/SOURCE_LEAKAGE_LEDGER.csv'),
      ('C0-07','GATE_PASS','精确源码SHA、签名、可执行范围及最小桥接','CODE_REUSE_E1.csv'),
      ('C1-01','GATE_PASS','36真实几何、合成Ray/Z负例、相机逐值相同','metrics/OPENCV_METRIC_TESTS.csv'),
      ('C1-02','GATE_PASS','R10/R5真实CAD；5场景前后遮挡及最近层合成控制','metrics/SYNTHETIC_CAD_ZBUFFER_TESTS.csv'),
      ('C1-03','EXPECTED_FAIL_E0','官方真实规则静态拦截，BCE定量匹配旧400步','metrics/SDF_GATE_STATUS.json'),
      ('C1-04','ADAPTER_INVALID / STOP_SDF_BRANCH','两种物理域射线几何可行，但旧全射线轮廓合同仍无效','metrics/SDF_RAY_DOMAIN_SUMMARY.csv'),
      ('C1-05','FUTURE_REQUIRED / NOT_WIRED','本轮不装配可微loss，ROI轮廓/多源loss未入图','metrics/SDF_FUTURE_LOSS_CONTRACT.csv'),
      ('C1-06','GATE_PASS_CPU_ONLY','官方固定rev原生M0–M3：两视频各3源，8组合CPU预处理','metrics/MAP_NATIVE_CPU_CONTRACT.csv'),
      ('C1-07','GATE_PASS_CPU_ONLY','32/32源几何光栅化/来源索引/单位/无效值合同','metrics/MAP_GEOMETRY_ADAPTER_CONTRACT.csv'),
      ('C1-08','GATE_PASS_CPU_ONLY','互斥先验、层冲突、原生/派生/不支持矩阵','metrics/MAP_LEGAL_INPUT_MATRIX.csv'),
      ('C1-09','E0_FAILURE_REPRODUCED_CPU','旧M3约22mm CAD偏差与输入/输出pose残差','metrics/E0_M3_FAILURE_RECHECK.csv'),
      ('C1-10','GATE_PASS_SCHEMA_ONLY','支持域6标签冻结，F3/三角面插值不冒充新观察','config/CPU_CONTRACT.json'),
      ('C1-11','DELIVERED','4核心PNG、5逐场景证据、本地HTML、单份中文报告','visualizations/index.html'),
      ('C1-12','GATE_PASS','0 GPU/模型forward/训练/下载/GT；412旧文件SHA不变','metrics/FINAL_VALIDATION.json')]
    table('metrics/ACCEPTANCE_MATRIX.csv',[dict(gate=i,status=s,evidence=d,path=p)for i,s,d,p in gates])
    failures=[
      dict(id='E1-SDF-01',group='G01',video='004/005',step='C1.2 official sampler / mask',type='ADAPTER_INVALID',
        reason='旧近端sphere clamp可在表面前吸收；全射线weights.sum又被终端吸收强制饱和，不能当Polyp轮廓',evidence='metrics/SDF_GATE_STATUS.json',figure='figures/Fig2_SDF_domain_gate.png',next='STOP_SDF_BRANCH',measurement_mm=np.nan),
      dict(id='E1-SDF-02',group='G01',video='004/005',step='C1.2 official components',type='BLOCKED_STATIC_ANALYSIS_ONLY',
        reason='ErrorBoundSampler/LaplaceDensity/MonoSDFNetwork真实组件含CUDA/网络调用；仅执行NumPy等价几何，未伪造官方运行',evidence='provenance/SDF_OFFICIAL_SOURCE_BEHAVIOR.json',figure='figures/Fig2_SDF_domain_gate.png',next='separate review required',measurement_mm=np.nan),
      dict(id='E1-SDF-03',group='G01',video='004/005',step='C1.2 candidate uniform fraction',type='LIMITATION_NOT_RELAXED',
        reason='48个候选×源×类别行中44行未达预冻0.95均匀样本球内比例；末端吸收样本仍计入分母，未改阈值换PASS',evidence='metrics/SDF_RAY_DOMAIN_SUMMARY.csv',figure='figures/Fig2_SDF_domain_gate.png',next='retain raw denominator; do not train',measurement_mm=np.nan),
      dict(id='E1-M3-OLD',group='G01',video='005',step='C1.3 old M3 recheck',type='OLD_METRIC_FAILURE_NOT_NEW_RUN',
        reason='固定CAD中位偏差22.35/21.94mm；第二视角pose平移残差9.94mm',evidence='metrics/E0_M3_FAILURE_RECHECK.csv',figure='figures/Fig4_Map_legal_geometry_adapter.png',next='do not adopt output pose',measurement_mm=np.nan),
      dict(id='E1-004',group='G01',video='004',step='C0 source identity',type='C0_LIMITED',reason='参考身份以归档图SHA成立；raw顺序编号未认证，004/005跨视频变换未认证',evidence='metrics/E1_SOURCE_MANIFEST.csv',figure='figures/local/G01_004_failure_evidence.png',next='same-video only',measurement_mm=np.nan),
      dict(id='E1-G06',group='G06',video='004',step='C0.2 holdout',type='KNOWN_HERO_INPUT_LEAKAGE',reason='raw00351曾输入G06_004_ref04 HERO',evidence='provenance/SOURCE_LEAKAGE_LEDGER.csv',figure='figures/local/G06_004_failure_evidence.png',next='DIAGNOSTIC_ONLY',measurement_mm=np.nan),
      dict(id='E1-G07',group='G07',video='004',step='C0.2 camera and holdout',type='UNQUALIFIED_STRESS',reason='相机不合格；raw00293曾输入G07_004_ref04 HERO',evidence='provenance/SOURCE_LEAKAGE_LEDGER.csv',figure='figures/local/G07_004_failure_evidence.png',next='stress only; exclude normal success',measurement_mm=np.nan),
      dict(id='E1-G08',group='G08',video='005',step='C0.2 holdout',type='LIMITED_STRESS',reason='raw00943/raw01080无预冻结严格独立留出证据',evidence='provenance/SOURCE_LEAKAGE_LEDGER.csv',figure='figures/local/G08_005_failure_evidence.png',next='diagnostic only',measurement_mm=np.nan),
      dict(id='E1-PHOTO',group='G01',video='photo001/002/003',step='C0.2 photo',type='DATA_INELIGIBLE_FOR_METRIC_RECON',reason='真实图像/匹配存在但K/pose未认证',evidence='provenance/PHOTO_QUALIFICATION.json',figure='figures/Fig1_scene_source_DAG.png',next='no metric camera fabricated',measurement_mm=np.nan),
      dict(id='E1-STRICT',group='ALL4',video='ALL5',step='C0.2 leakage',type='HOLDOUT_STRICT_UNAVAILABLE',reason='0严格全流程留出；历史曝光不能事后重新分组消除',evidence='provenance/SOURCE_LEAKAGE_LEDGER.csv',figure='figures/Fig1_scene_source_DAG.png',next='no blind-test claim',measurement_mm=np.nan),
      dict(id='E1-ENGINEERING-01',group='N/A',video='N/A',step='SDF CPU integration',type='RUNTIME_API_COMPATIBILITY_FIXED',reason='NumPy1.x没有trapezoid；改用同义trapz，原日志与原源码冻结SHA保留，未更改科学容差',evidence='runtime/SDF_attempt001.log',figure='figures/Fig2_SDF_domain_gate.png',next='resolved CPU-only',measurement_mm=np.nan)]
    table('metrics/E1_FAILURE_LEDGER.csv',failures)
    ft=['# E1 失败与限制台账','', '本表区分新合同失败、旧失败复核、输入不合格、未执行及工程兼容错误。全部模型运行数为0；测量结果均为NaN。','', '| ID | 组/视频/步骤 | 类型与具体原因 | 证据与图 | 处置 |','| --- | --- | --- | --- | --- |']
    for f in failures:
        ft.append(f"| {f['id']} | {f['group']} {f['video']} / {f['step']} | `{f['type']}`：{f['reason']} | [数值/原始证据]({f['evidence']})；[可视化]({f['figure']}) | {f['next']}；NaN |")
    ft+=['','所有复放命令见 [REPRODUCE.md](REPRODUCE.md)。`figures/local/`、`runtime/` 为本地证据，不进入Git；远端四幅核心图包含对应组的分层、来源和旧故障概览。']
    (R/'FAILURE_LEDGER.md').write_text('\n'.join(ft)+'\n')
    maxuv=max(float(x['source_UV_reprojection_max_px'])for x in csv.DictReader((R/'metrics/OPENCV_METRIC_TESTS.csv').open()))
    maxmap=max(json.loads(x['axial_Z_error_mm'])['maximum']or 0 for x in mr)
    lines=['# TASK-NEURAL-E1-PIPELINE-RECOVERY-001 技术报告','',
    '**2026-10-31，Asia/Shanghai。状态：C0_LIMITED；OpenCV/CAD合同通过；SDF ADAPTER_INVALID / STOP_SDF_BRANCH；Map CPU输入合同通过。C2–C4未执行。**','',
    '本轮在独立E1工作树完成用户授权的C0+C1 CPU审计。真实复核36份参考、47个HERO输入RGB身份和154条依赖边，并检查252个同视频有向参考对。两段G01各保留三份不同参考，但共享HERO父系且深度冲突显著，严格全流程留出仍为0。零训练射线检查不仅复现旧SDF近端吸收，还发现整射线权重和会被官方终端吸收强制饱和，精确解释旧恒定轮廓损失，故停止该分支。Map完成32项真实几何转换及8项三视图原生配置CPU合同；旧M3约22mm公制偏差原样保留。全部冻结相机及旧资产未变；无GPU、模型前向、训练、下载、GT或历史测量回退。本轮没有新重建模型、测量精度或科学赢家。','',
    '## 固定科研审计表','', '| 审计项目 | 必须汇报 |','| --- | --- |',
    '| 目标组数 | 4个物理组：G01/G06/G08/G07，5段视频。G01两视频只算1个病例；36参考不是36病例。 |',
    '| 本算法独立成功 | **新测量0/4、模型运行0/4**。CPU数值光栅化32/32及原生接口8/8通过，只表示合同成立，不表示测量正确。 |',
    '| 本算法失败 | G01 SDF适配合同失败1物理组/两视频；新模型均NOT_RUN。其余输入资格限制逐组列示，四组测量全部NaN。 |',
    '| 历史测量值回退 | **0**。历史XYZ/F1/F2/F3是本任务明确允许的被审计先验；旧M3只作失败对照，没有回填新预测。 |',
    '| 失败组及具体原因 | G01：吸收/轮廓合同、深度冲突与坐标限制；G06：raw00351泄漏；G08：有限留出；G07：相机不合格及raw00293泄漏。逐组链接见[失败台账](FAILURE_LEDGER.md)。 |',
    '| 最终统计样本 | 真实独立新测量0/4，配对共同成功组0。CPU转换按32任务分别计数，禁止代作病例成功率。 |',
    '| 是否使用 GT 选择算法 | **否**，未打开GT/Blender、未拟合尺度或pose；[容差](config/CPU_CONTRACT.json)、逐阶段BEFORE_TEST冻结及源码SHA均先于对应测试。历史报告已有曝光，因此不声称历史信息盲测。 |','',
    '独立覆盖率为**0/4新测量**；中位绝对相对误差、MAE、p95、最大误差均为**NaN/NOT_EVALUABLE**；共同成功组配对比较N=0。参见[物理统计表](metrics/PHYSICAL_MEASUREMENT_STATISTICS.csv)。CAD距离及HERO一致性误差不是息肉真值误差。','',
    '## 实际版本、复用与边界','',f'工作树 `{REPO}`；分支 `exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001`。本地HTML：`{R}/visualizations/index.html`。用户原有脏main未提交或清理。','',
    '| 来源 | 精确 SHA |','| --- | --- |']
    for k,v in stage.items(): lines.append(f"| {k} | `{v['SHA']}` |")
    lines+=['', '附件五正文SHA全部匹配，原任务未改写。授权证据见[AUTHORIZATION](provenance/AUTHORIZATION.json)，任务依赖与入口见[执行计划](TASK_EXECUTION_PLAN.md)。[复用表](CODE_REUSE_E1.csv)记录真实路径、SHA、函数签名与最小适配。E0来源函数、原`unproject`、原点/三角面Z-buffer、SameCameraScene及renderer均复用；旧`audit.py` main会探测CUDA，故没有执行，只精确提取CPU函数。MonoSDF官方含GPU组件未实例化；Map只导入官方数据utils，未导入模型或加载权重。','',
    '## C0：来源、独立性与分母','', '| 组 | AUDITED_N参考 | ELIGIBLE_N参考 | ADAPTER_TESTED_N转换 | MODEL_RUN_N | SCIENTIFIC_SUCCESS_N |','| --- | --- | --- | --- | --- | --- |']
    for g in group:lines.append(f"| {g['group']} / {g['eligibility']} | {g['AUDITED_N']} | {g['ELIGIBLE_N']} | {g['ADAPTER_TESTED_N']} | 0 | NOT_EVALUATED |")
    lines+=['','ELIGIBLE_N仅表示相机/来源条件下可提出后续候选：G01/G06为正常条件25参考，G08另列有限6参考，G07的5参考仅压力。它不构成训练授权或全独立HERO监督。36/36 native逐文件可读；三个004 display别名已沿真实infer/package链更正，未将display当native。详见[来源清单](metrics/E1_SOURCE_MANIFEST.csv)、[native核验](metrics/NATIVE_DEPTH_AUDIT.csv)、[父系DAG](provenance/E1_SOURCE_DAG.json)。','',
    '![场景与来源DAG](figures/Fig1_scene_source_DAG.png)','',
    '| G01视频 | 固定提出的三参考 | 光轴夹角范围 | 有向对共视深度点数范围 | 深度冲突比例范围 |','| --- | --- | --- | --- | --- |']
    for sid,ids in prop.items():
        ps=[p for p in pairs if p['source']in ids and p['target']in ids];angles=[float(p['optical_axis_angle_deg'])for p in ps];N=[int(p['common_visible_depth_N'])for p in ps];cf=[float(p['depth_conflict_fraction'])for p in ps]
        lines.append(f"| {sid} | {' / '.join(x.replace(sid+'_','')for x in ids)} | {min(angles):.2f}–{max(angles):.2f}° | {min(N)}–{max(N)} | {min(cf):.1%}–{max(cf):.1%} |")
    lines+=['','采用预注册最初三参考，不按目标误差换源。共视分母是源点投影到另一个来源Mask且通过CAD遮挡/有效深度后的点数，含投影到同像素的多点；不是独立像素/病例。阈值固定`max(0.5mm,3像素足迹)`。三参考的身份、冻结相机和射线链成立；**可信多深度一致性闭环尚未成立**。HERO输入父系共享数逐对保留；同一RGB上的F1/F2/F3只能作互斥先验，不增加相机观察数。','',
    'G06 raw00351及G07 raw00293分别确认为旧ref04的HERO输入；G08 raw00943/raw01080没有预冻严格独立留出。三照片各有真实RGB/Mask和3条缓存匹配比较，但pose未注册、K仅候选，不制造公制相机。004/005保持两个局部系，没有跨视频融合。严格全流程holdout仍为0，见[逐帧泄漏表](provenance/SOURCE_LEAKAGE_LEDGER.csv)。','',
    '## C1.1：相机、单位与CAD','',
    f'36/36真实基础几何合同通过；XYZ→UV最大残差`{maxuv:.3g}px`，原unproject回算误差0。36/36 pack的K/pose与归档相机按来源reference_index逐值相同，差值0；32个Map条件产物另逐文件比对源K/c2w。mm→m只改变接口表达并闭环回mm；resize/crop的K是官方图像坐标变换，不是重拟合物理相机。所有源文件哈希不变。','',
    '合成负例证实轴向Z不能直接当单位射线长度，漏掉半像素主点项也会被捕获。R10 CAD中心线半径5.6mm/截面0.6mm、R5为3.1/0.6mm，真实网格均闭合。5个场景各64条射线在真实CAD前/后各1mm构造控制例：前方64/64可见，后方0/64可见，重叠时64/64选择近层。CAD始终单独作刚体遮挡，未与息肉标签合并；Ring接触边界不当真实息肉轮廓。见[相机不变量](metrics/FROZEN_CAMERA_INVARIANTS.csv)、[CAD测试](metrics/SYNTHETIC_CAD_ZBUFFER_TESTS.csv)。','',
    '## C1.2：SDF负例、两方案及停止结论','',
    f'两视频各3来源，每源按前景64、邻近背景64、Ring64、角落4采样，共1176条真实像素射线；旧域+两候选形成3528条域测试记录。Ray/Z点相交最大误差`{sf["ray_Z_max_error_mm"]:.3g}mm`。官方固定revision的ErrorBoundSampler实际先取cube far，再补全局`far=3.5R`；ImplicitNetwork用`min(sdf, R−||x||)`吸收；LaplaceDensity按CDF转密度。源码/行号及完整类见[官方行为证据](provenance/SDF_OFFICIAL_SOURCE_BEHAVIOR.json)。','',
    '旧10mm/unit、R=2.5域中，真实射线可穿入表面支持区间——因此“目标在域内”的子检查确实能通过，未为得到FAIL更改断言。但ray近端在吸收球外时，负sphere SDF会在表面之前产生高密度，24个源×类别汇总被正确拦截。旧两输入camera norm 3.2714/3.8705只作背景事实，判据使用具体entry/exit、target t、采样比例和透过率，而非仅看camera norm。','',
    f'更直接的包装错误是`acc=weights.sum(-1)`：官方有限边界外的吸收与远端终止会让每条射线最终不透明。128前景/64背景、float32 clamp(1e−5,1−1e−5)数学计算得到BCE **{sf["saturated_mask_BCE_expected"]:.9f}**，旧400步全程实测 **{sf["E0_recorded_silhouette_min"]:.9f}**，差小于1e−6。该数值无需网络/训练即能重现。','',
    '仅静态设计两种具有物理理由的规范域：以固定Ring原点或真实可见ROI中心为原点，根据冻结相机+实际来源点包络及10β边界余量确定统一规范尺度。源公制K/c2w不变，仅ray的表达规范变化且回算闭环；不是重估pose或按误差搜索半径。两候选均让目标t进入有效区间并避免近端处在吸收球外，但**不能修复旧全射线轮廓损失**。预冻0.95球内均匀样本比例在48汇总行中44行未达标；球外终端/角落样本仍计分母，未放宽阈值。这不是方法普适失败的证明。','',
    '解析球/平面控制验证正负号、零交叉、有限段吸收/透明变化；另对真实射线给出empty-space有限段与终端opacity对照。官方GPU/网络组件均标`BLOCKED_STATIC_ANALYSIS_ONLY`；没有伪造官方Sampler运行或神经梯度。有限可信ROI内的轮廓累积仅是后续设计，未接入计算图。**最终SDF门禁为ADAPTER_INVALID / STOP_SDF_BRANCH**；没有可认证当前包装进入训练的方案。RGB/多HERO/权重/Eikonal/anchor/CAD损失的状态逐项写为FUTURE_REQUIRED或NOT_WIRED，见[loss合同](metrics/SDF_FUTURE_LOSS_CONTRACT.csv)。','',
    '![SDF真实射线与旧失败](figures/Fig2_SDF_domain_gate.png)','',
    '## C1.3：Map原生与局部几何合法条件','',
    '锁定官方revision`3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9`。对两个G01视频各3个真实参考执行M0–M3共8个CPU预处理/校验组合；没有调用infer或网络。官方真实白名单支持img、intrinsics或ray_directions、depth_z、camera_poses、is_metric_scale；拒绝额外valid/PLY/GLB/任意confidence/多层depth字段。depth要求校准，K与ray_directions互斥，带pose时第一view必须带pose。API文档写B×H×W×1，但实际image预处理产物为B×H×W，inference再加末维；本轮按真实代码而非仅按docstring测试。','',
    f'两个G01视频各5几何族×点/原三角面两种光栅化=20合同；G06/G08/G07各Raw/Cleaned×两种=12压力合同；合计**32/32合法转换**。最大轴向Z回算残差`{maxmap:.6g}mm`，预冻容差0.002mm；resize后的逐深度值与官方最近邻来源像素索引重放误差0。Raw为本来源；Cleaned使用原删除索引；F1为历史来源Cleaned并集；F2为原accepted索引并集；F3为真实Joint来源索引及原face_ids，保留其历史变换身份。','',
    '稀疏点仅落到其实际投影像素，未按邻近填洞；只有原有三角面才光栅化。每个本地产物包含axial_Z_mm、depth_z_m、validity、来源点/三角面ID、来源参考与UV/重心、surface_origin、Ring_occluded、UNKNOWN、冻结相机及预处理来源索引。官方validity不是原生字段，作为审计元数据保留，绝不塞入infer。','',
    '无效深度在适配器中严格写0，正深度用m。官方`normalize_depth_using_non_zero_pixels`以`depth>0`计数，0归一化/编码后仍为0，证明它表示缺失条件；NaN乘mask仍会传播，CPU负例确认污染，故拒绝NaN进入官方utils。不能据此声称模型对稀疏输入科学有效。保存全部F1/F2/F3互斥层及20对同RGB先验冲突表，不融合为一个“更好”结果。M4/M5正式名称未启用。','',
    '![多参考HERO冲突](figures/Fig3_HERO_geometry_conflicts.png)','',
    '| 旧M3来源 | Ring有效/预处理Mask像素（280×154） | CAD距离 median / MAE / p95 / max（mm） | 冻结条件pose相对输出pose的平移 / 转角 |','| --- | --- | --- | --- |']
    for r in old:
        st=json.loads(r['CAD_distance_mm']);lines.append(f"| {r['source']} | {r['Ring_output_valid_N']}/{r['Ring_input_pixel_N']} | {st['median']:.3f} / {st['MAE']:.3f} / {st['p95']:.3f} / {st['maximum']:.3f} | {float(r['pose_translation_residual_mm']):.6g}mm / {float(r['pose_rotation_residual_deg']):.6g}° |")
    lines+=['','这是旧E0 M3缓存，表达转换仅复用其原先保存的首相机刚体gauge，没有新ICP/尺度拟合/pose优化。首相机本来就是该gauge锚点，约0.012° trace残差主要是旧float32矩阵数值精度，不代表独立定位精度。第二视角约9.94mm残差及约22mm的CAD偏差均保留，输出pose从未成为本轮输入。','',
    '![Map合法转换和旧M3故障](figures/Fig4_Map_legal_geometry_adapter.png)','',
    '## 支持域、不能进入后续的输入与验收','',
    '冻结标签：MULTI_VIEW_OBSERVED_SUPPORTED、SINGLE_VIEW_OBSERVED_SUPPORTED、CONFLICT、RING_OCCLUDED、PRIOR_ONLY、UNKNOWN。原始可追溯来源点只获条件性的单来源证据；F3 Joint变化点和三角面内部插值保守标先验；冲突层独立保存。没有生成新的supported mesh，未知背面、Ring后遮挡及先验补全不计观测面积。概览正交图中CAD填色仅是既有面片布局；物理遮挡结论以source-view CPU Z-buffer为准。','',
    '确定不能直接进入下一轮的输入/包装包括：当前SDF全射线轮廓损失；未认证照片公制相机；G07作为正常成功组；G06 raw00351/G07 raw00293作为独立留出；任何未认证004/005融合；任意PLY/GLB/confidence/valid原生字段；同RGB多先验伪装多相机；NaN/负深度未经清洗的条件。','',
    '| 门禁 | 最终状态 | 真实证据 |','| --- | --- | --- |']
    for i,s,d,p in gates:lines.append(f'| {i} | `{s}` | [{d}]({p}) |')
    lines+=['',f'独立验证实际通过 **{validation["check_N"]}项断言**，旧输入/源码 **{validation["old_input_hash_N"]}项SHA不变**。失败及工程错误未删除：一次NumPy1.x无trapezoid的兼容错误已改同义trapz，原日志、原冻结SHA留本地；这是CPU工程修复，没有训练重试或容差调整。详见[验证](metrics/FINAL_VALIDATION.json)、[失败台账](FAILURE_LEDGER.md)、[复现](REPRODUCE.md)。','',
    '本轮在C1结束。Map合同通过不自动授权新Map前向；SDF当前包装必须保持停止。后续只提交研究者/RA审阅，C2数据/loss冻案需另立任务；不自动进入C2/C3/C4。Git同步的实际commit与远端结果以[同步记录](provenance/GIT_SYNC_STATUS.json)为准。']
    (R/'TECHNICAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    repro=f'''# CPU复现

本地完整目录：`{R}`。HTML绝对路径：`{R}/visualizations/index.html`。

只有本机仍有旧数据与原环境时可完整重放；GitHub不含原视频/权重/全量NPZ/GLB和隔离依赖。缺失资产按MISSING/BLOCKED记录，不能从报告造数据。下面只运行本任务CPU脚本，不运行E0模型、CUDA探针或清理入口。

```bash
cd {REPO}
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1
TASK_E1_PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK_E1_DIR=experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001
"$TASK_E1_PY" "$TASK_E1_DIR/code/source_audit.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/sdf_contract.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/map_contract.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/figures.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/failure_evidence.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/validate.py"
"$TASK_E1_PY" "$TASK_E1_DIR/code/report.py"
```

重放会更新本E1派生指标、图和时间戳；如需保留本次完整原件，先复制新任务目录并重新建立新分支，保持旧工作树只读。原有源码/物理相机、数据和E0结果由保护哈希验证。

只读核验可仅运行`validate.py`；它读取既有产物，重做小型CPU断言并写本任务验证文件。每次源码变化后重建对应BEFORE_TEST冻结；不得改变CPU_CONTRACT容差去换PASS。SDF组件状态是BLOCKED_STATIC_ANALYSIS_ONLY，数学等价几何不能当官方神经执行。

数据转换：原始几何mm，官方条件m；原源相机保持相同。source-index与原UV、三角面ID、重心、未知/遮挡标签保存在`local_results/depth_conditions/*.npz`，仅本地。首次SDF CPU兼容错误见`runtime/SDF_attempt001.log`和`provenance/SDF_ATTEMPT001_FREEZE.json`。
'''
    (R/'REPRODUCE.md').write_text(repro)
    idx=['# E1结果索引','',f'完整目录：`{R}`。','', '| 产物 | 位置与含义 |','| --- | --- |',
         '| 单份完整技术报告 | [TECHNICAL_REPORT](TECHNICAL_REPORT.md) |',
         '| CPU复现 | [REPRODUCE](REPRODUCE.md) |',
         '| 本地HTML | [visualizations/index.html](visualizations/index.html) |',
         '| 原任务与构建拆解 | [TASK](TASK.md)、[执行计划](TASK_EXECUTION_PLAN.md) |',
         '| 来源清单 / DAG | [manifest](metrics/E1_SOURCE_MANIFEST.csv)、[DAG](provenance/E1_SOURCE_DAG.json) |',
         '| 既有代码复用 | [CODE_REUSE_E1.csv](CODE_REUSE_E1.csv) |',
         '| 逐组及全体分母 | [四组](metrics/FOUR_GROUP_STATUS.csv)、[物理统计](metrics/PHYSICAL_MEASUREMENT_STATISTICS.csv) |',
         '| 独立验证 / 验收矩阵 | [验证](metrics/FINAL_VALIDATION.json)、[矩阵](metrics/ACCEPTANCE_MATRIX.csv) |',
         '| 失败与逐组本地证据 | [FAILURE_LEDGER](FAILURE_LEDGER.md)、[证据索引](provenance/PER_SCENE_FAILURE_EVIDENCE.json) |',
         '| 相机与源保护 | [相机不变量](metrics/FROZEN_CAMERA_INVARIANTS.csv)、[412项源哈希](provenance/INPUTS_AND_SHAS.json) |',
         '| Map合法矩阵 / 来源先验 | [矩阵](metrics/MAP_LEGAL_INPUT_MATRIX.csv)、[父系](metrics/MAP_PRIOR_DEPENDENCY.csv) |',
         '| Map实际深度条件文件 | [含路径与SHA的示例索引](provenance/MAP_SOURCE_VIEW_DEPTH_EXAMPLES.json)，原NPZ为LOCAL_ONLY |',
         '| Git同步 | [GIT_SYNC_STATUS](provenance/GIT_SYNC_STATUS.json) |']
    for p in sorted((R/'figures').glob('Fig*.png')):idx.append(f'| 核心图 {p.name} | [{p.name}](figures/{p.name}) |')
    (R/'RESULT_INDEX.md').write_text('\n'.join(idx)+'\n')
    html=R/'visualizations/index.html';text=html.read_text()
    if '逐场景失败证据' not in text:
        text+='<article><h2>逐场景失败证据（本地）</h2>'
        for p in sorted((R/'figures/local').glob('*_failure_evidence.png')):text+=f'<p><a href="../figures/local/{p.name}">{p.name}</a></p>'
        text+='</article>';html.write_text(text)
    # Publication ledger is updated with actual push results outside this guard.
    if not (R/'provenance/GIT_SYNC_STATUS.json').exists():
        save('provenance/GIT_SYNC_STATUS.json',dict(status='NOT_PUSHED_YET',branch=git(REPO,'branch','--show-current'),base_SHA=stage['base_E0']['SHA']))
    # Final deliverable links and artifact inventory, no self-referential hashes.
    broken=[]
    for name in ['TECHNICAL_REPORT.md','REPRODUCE.md','RESULT_INDEX.md','FAILURE_LEDGER.md','TASK_EXECUTION_PLAN.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(R/name).read_text()):
            if '://' not in link and not link.startswith('#') and not (R/link.split('#')[0]).exists():broken.append(link)
    if broken:raise AssertionError(('broken local links',broken))
    files=[]
    for p in sorted(R.rglob('*')):
        if p.is_file() and not p.is_relative_to(R/'runtime') and p.name not in ['DELIVERY_MANIFEST.json','GIT_SYNC_STATUS.json']:
            files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),
                delivery='LOCAL_ONLY' if p.is_relative_to(R/'local_results') or p.is_relative_to(R/'figures/local') else 'GIT_INCREMENT'))
    save('provenance/DELIVERY_MANIFEST.json',dict(files=files,GT_used=False,model_run_N=0,source_inputs_hash_N=412,
        scope='C0+C1 only',link_check='PASS',report='one TECHNICAL_REPORT.md',new_models=False))
    print('REPORT_COMPLETE',len(files),'artifacts; all handoff links exist',flush=True)

if __name__=='__main__':main()
