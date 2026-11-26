"""Summarize frozen predictions without selecting/refitting any method."""
from common2 import *
import csv,html
from visualize2 import plt

def csvwrite(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with open(path,'w',newline='')as f:
  keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,keys);w.writeheader();w.writerows(clean(rows))
def fmt(x):return '不可评价'if x is None else f'{x:.3f}'if isinstance(x,(float,np.floating))else str(x)
def mdtable(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(fmt(x)for x in row)+' |'for row in rows)+'\n'

def main():
 stage_freeze('DELIVER',T/'evidence');controls=read(T/'evidence/CONTROL_RESULTS.json');csvwrite(T/'evidence/CONTROL_RESULTS.csv',[{k:v for k,v in r.items()if not isinstance(v,dict)}for r in controls]);table=[];rr=[];sources=[];geos=[];bidirows=[];loos=[];groups=[];catrows=[];scope=[]
 for selected in read(T/'config/SELECTION.json')['groups']:
  group=selected['group'];groups.append(group);d=RUN/'real'/group;a=read(T/'config'/group/'ASSETS.json');e=read(d/'EVALUATION.json');st=e['stages'];pred=read(d/'PREDICTIONS.json');loo=read(d/'FIT_LOO.json');maxrot=max(r.get('delta_from_base',{}).get('rotation_deg',0)for r in loo);maxtrans=max(r.get('delta_from_base',{}).get('translation_mm',0)for r in loo);den=e['methods']['M4']['bidir']['denominators'];support=read(d/'SUPPORT_SELECTION.json')
  status='证据不足：双侧留出少于8'if not den['evidence_sufficient']else'支持有限投影改善；候选待研究，拒绝直接主体交接'
  table.append([group.replace('GP_','').replace('_closed_','/').replace('_single_refY',''),st['sources'],st['fit_valid'],st['fit_category']['1'],str(den['two_sided_DLT_tracks'])+'/'+str(st['held_total']),e['methods']['M1']['bidir']['A_to_B']['conditional_MAE'],e['methods']['M1']['bidir']['B_to_A']['conditional_MAE'],e['methods']['M4']['bidir']['A_to_B']['conditional_MAE'],e['methods']['M4']['bidir']['B_to_A']['conditional_MAE'],maxrot,100*st['trusted_area_mm2']/st['raw_area_mm2']])
  gates={v['side']:read(Path(v['run'])/'metrics/GATES.json')for v in a['videos']};save(d/'STAGE_SUMMARY.json',dict(stages=st,gates=gates,LOO_max_rotation_deg=maxrot,LOO_max_translation_mm=maxtrans,assessment=status,support_changed=False,clinical_or_GT_accuracy='NOT_ESTABLISHED'))
  for r in read(d/'CLEAN_INDEX.json'):
   s=r['source'];row=dict(group=group,side=s['side'],case=s['case'],tag=s['tag'],target=s['raw_target'],support=str(s['raw_support']),origin=r['origin'],status=r.get('status','COMPLETE'),raw_reference=str(Path(s['run'])/'meshes'/(s['tag']+'_Polyp.ply')),raw_sha=s['mesh_sha256'],native_reference=str(Path(s['run'])/'raw'/(s['tag']+'.npz')),native_sha=s['native_sha256'],selection=r.get('selection_path'),selection_sha=r.get('selection_sha256'),raw_area=r.get('raw_area_mm2'),clean_area=r.get('trusted_area_mm2'),excluded_area=r.get('excluded_area_mm2'),coordinate_change=0)
   for variant in ['raw','trusted']:
    for k in ['faces','face_edge_components','boundary_edges','boundary_components','referenced_vertices','unreferenced_vertices']:row[variant+'_'+k]=r.get(variant,{}).get(k)
   sources.append(row)
  for l in loo:loos.append(dict(group=group,drop_frame=l['drop_frame'],side=l['side'],raw_frame=l['raw_frame'],fit=l['fit_tracks'],surviving=l['surviving_base_tracks'],**l.get('delta_from_base',{}),quality=l['result']['quality']))
  for method,r in e['methods'].items():
   held=read(d/'evaluation'/(method+'_HELD.json'))
   for direction in ['A_to_B','B_to_A']:
    b=r['bidir'][direction];obs=[x for x in held if x['direction']==direction];row=dict(group=group,method=method,direction=direction,**{k:v for k,v in b.items()if k!='categories'},all_held_tracks=st['held_total'],two_sided_DLT_tracks=den['two_sided_DLT_tracks'],full_mean_status='NOT_EVALUABLE_NONFINITE'if b['invalid']else'FINITE',fraction_le3px=sum(x['error_px']is not None and x['error_px']<=3 for x in obs)/max(1,len(obs)),fraction_le6px=sum(x['error_px']is not None and x['error_px']<=6 for x in obs)/max(1,len(obs)),ring_B_MAE=r['ring']['by_side']['B']['MAE'],numerical=r['numerical'],quality=r['quality']);bidirows.append(row)
    for c,stat in b['categories'].items():catrows.append(dict(group=group,method=method,direction=direction,category={'0':'背景','1':'息肉','2':'Ring'}[c],**stat))
   for variant in ['raw','clean']:
    for direction,g in r.get(variant,{}).items():geos.append(dict(group=group,method=method,variant=variant,direction=direction,coverage=g['coverage_fraction'],N=g['full_raw_sample_domain']['N'],invalid=g['full_raw_sample_domain']['invalid'],full_mean=g['full_raw_sample_domain']['MAE'],conditional_common_original_face_MAE=g['conditional_retained_original_faces']['MAE'],conditional_common_original_face_P95=g['conditional_retained_original_faces']['P95'],missing=g['sample_missing_clean'],excluded_samples=g['source_sample_excluded'],interpretation='cross-video consistency; NOT GT'))
  # FIT spatial support: descriptive SVD only, after freeze; no rejection/retuning.
  lm=np.load(d/'LANDMARKS.npz');tr=np.load(d/'tracks/observations/tracks005.npz');X=lm['xyz'][lm['fit']]
  for i,side in enumerate(['A','B']):
   s=np.linalg.svd(X[:,i]-X[:,i].mean(0),compute_uv=False);scope.append(dict(group=group,side=side,fit=len(X),singular_mm=s.tolist(),extent_mm=np.ptp(X[:,i],axis=0).tolist(),polyp_fit=st['fit_category']['1'],warning='background-dominated; 3D SVD is descriptive, not independent ground truth'))
  fig,ax=plt.subplots(figsize=(13,7));ax.axis('off');text=[group,'真实 HIST；无独立三维 GT；'+status,'→ Mask/Ring/相机：沿用原门控，未重跑上游；详情 STAGE_SUMMARY.json',f'→ 匹配：{st["track_total"]}完整轨迹；FIT {st["fit_valid"]}（息肉{st["fit_category"]["1"]}）；全留出{st["held_total"]}，双侧DLT {den["two_sided_DLT_tracks"]}',f'→ FIT留一：最大Δ旋转 {maxrot:.3f}° / 平移 {maxtrans:.3f} mm；非GT误差',f'→ HERO：{st["sources"]}来源，Clean缺失{st["clean_missing"]}；原面{st["raw_faces"]} → TRUSTED {st["trusted_faces"]}',f'→ 面积（各源求和，非融合面积）：{st["raw_area_mm2"]:.1f} → {st["trusted_area_mm2"]:.1f} mm²；共同面坐标变化0 mm','→ base/raw_support/clean_support：FIT集合相同，T完全相同；未发现选点增益','', '方法      A→B条件MAE / B→A条件MAE (px)        固定CAD B侧 Ring held MAE (px)']
  for m in ['M0','M1','M2','M3','M4']:
   r=e['methods'][m];text.append(f'{m}           {r["bidir"]["A_to_B"]["conditional_MAE"]:.3f} / {r["bidir"]["B_to_A"]["conditional_MAE"]:.3f}                      {r["ring"]["by_side"]["B"]["MAE"]:.3f}')
  text+=['','完整留出存在失效观测，完整MAE不可评价；3/6px仅诊断，不据此改阈值。','曲面距离仅跨视频一致性；删面后较低条件均值不代表位姿精度提高。']
  ax.text(.01,.98,'\n'.join(text),va='top',fontsize=12);fig.tight_layout();vis=T/'visuals'/group;fig.savefig(vis/'stages.png',dpi=120);plt.close(fig);p=vis/'index.html';s=p.read_text().replace('<table border=', '<h2>逐阶段支持与残差</h2><img src="stages.png" style="width:100%"><table border=');p.write_text(s)
 csvwrite(T/'evidence/REAL_BIDIRECTIONAL.csv',bidirows);csvwrite(T/'evidence/REAL_CATEGORIES.csv',catrows);csvwrite(T/'evidence/RAW_CLEAN_SOURCES.csv',sources);csvwrite(T/'evidence/SURFACE_CONSISTENCY.csv',geos);csvwrite(T/'evidence/FIT_LOO.csv',loos);save(T/'evidence/FIT_SPATIAL_SUPPORT.json',scope)
 controltable=[]
 for phase in ['V0','V1','V2','V3']:
  for method in ['M2','M3','M4']:
   rows=[r for r in controls if r['condition'].split('_')[0]==phase and r['method']==method];controltable.append([phase,method,str(sum(r['pose_pass']for r in rows))+'/'+str(len(rows)),max(r['rotation_deg']for r in rows),max(r['translation_mm']for r in rows),max(r['observed_ring_center_drift_mm']for r in rows),max(r['observed_normal_drift_deg']for r in rows)])
 fig,axs=plt.subplots(1,2,figsize=(12,4));fig.suptitle('受控回归（非盲测）：M4精确Ring限制漂移，不消除逐帧误差；V3仅Ring参数误差')
 for m,color in [('M2','gray'),('M3','orange'),('M4','blue')]:
  rows=[r for r in controls if r['condition'].startswith(('V2','V3'))and r['method']==m];axs[0].plot(range(10),[r['rotation_deg']for r in rows],'o-',label=m,color=color);axs[1].plot(range(10),[r['translation_mm']for r in rows],'o-',label=m,color=color)
 for ax,threshold,unit in [(axs[0],.5,'旋转误差 (°)'),(axs[1],.2,'平移误差 (mm)')]:ax.axhline(threshold,c='red',ls='--',label='固定门槛');ax.set_ylabel(unit);ax.set_xticks(range(10),['V2-'+str(i)for i in range(1,6)]+['V3-'+str(i)for i in range(1,6)],rotation=45);ax.legend();ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(T/'visuals/control.png',dpi=130);plt.close(fig)
 report='''# TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002 技术报告

本轮同时完成受控回归与5个真实双视频组。M4修正了精确Ring条件下的漂移，但没有使所有有噪位姿通过。真实数据的多组有限留出投影改善，完整留出失效、背景主导的轨迹支持和曲面错层仍在；本轮没有任何组被批准直接接入主体拟合。Clean只删原面，未改变共同面的坐标；三个M4支持分支的FIT集合和T均完全相同，未观察到Clean选点增益。

## 身份、复用与范围

独立分支 `exp/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002`，基础提交 `2d34cc866cd175d4d770a3e09d07b31a5c3662d7`；批次 `R002_001`。用户附件原文见 [PM_TASK.txt](PM_TASK.txt)，运行前协议见 [EXECUTION_PLAN.md](EXECUTION_PLAN.md)。没有执行旧恢复任务，也没有使用H004。

|复用资产|本轮用途|薄适配|
|---|---|---|
|虚拟001，537c2070；原G01虚拟场景/纹理/独立网格/全部FIT-HOLDOUT|12条件回归、固定6655个GT可见点、4549个重叠点|V3仅扰005 Ring参数；不改原RGB/深度/网格|
|HIST实际全量执行快照da92d8dd，state.run_path及相机→计划→HERO收据|5组10视频、182个完整Raw来源|6帧/视频，原V6 SIFT/匹配/DLT；K与mm c2w保持原义|
|虚拟001原M2求解器|原方法对照|原函数AST载入，仅按R5/R10配置CAD中心线半径|
|Clean交付2d34cc86，分类执行e30ac479|017+gap分类、018 TRUSTED-only|复用2源、新分类180源；仅原F[state==0]，原V只读引用|
|原三角面光线求交、原mesh_sections、原Ring apparent contour|图示、截面和固定CAD留出评价|CPU单线程；真实三角面，不用顶点云充当Clean|

源清单及SHA见 `config/<group>/ASSETS.json`、[RAW_CLEAN_SOURCES.csv](evidence/RAW_CLEAN_SOURCES.csv)。完整来源依赖保留在原路径，本任务没有移动、删除共享资产。2个复用源是IIa22/A RAW640、Ip4/A RAW68，另2个历史Clean单来源不属于本轮选中组合。182源无缺失、无空Clean；复用输出及原V/F均逐项核验。审查后补验历史冻结camera/CAD/input/model/Target/Support与分类器/核/协议SHA，全匹配，见 `REUSED_IDENTITY_REVIEW.json`；这是补验，不冒称重新分类。

原全量39组中初查11组双视频合格，预先按新增形态/Ring规格、尺寸、已有Clean、ID规则选5组。Is无合格双视频组，未等待或干预队列。A/B按完整case排序固定，IIa22为005/006，其余为004/005。全部 source/tag 配对，不只展示历史4源。

坐标接口：毫米、c2w、尺度1；B侧相机/地标/全部网格同步左乘T，A固定，K和轴向Z不变。工作图640×360，K=(490,490,319.5,179.5)；HERO原生352格经原 `mapped_input_for_source` 的半像素/UV映射核验原V/F，未将原生网格尺寸误作K尺寸。Ring规格为内径，中心线半径R5=3.1、R10=5.6mm，管半径0.6mm。支持依赖继承Target+3 Support，HOLDOUT独立性只限新跨视频对应；不是上游BA/HERO的全链独立测试。

## 方法和真值隔离

M0恒等；M1名义Ring中心/法向对齐（本批两侧规范相同所以等于M0），yaw不可辨；M2保留原001；M3只估yaw；M4每坐标原3D RGB soft_l1、sigma=.2mm，1/N在损失外，另加lambda=1的5维Ring二次项。真实Sigma合并A/B FIT Ring候选重复性、固定留一稳定性与每侧.1mm/.3°底座；名义A原点不是零误差，不能排除系统偏差。保护界限同Sigma的Mahalanobis半径5。所有初始化、候选分支、FIT筛选、支持规则均不用HOLDOUT或GT。

受控预测用文件访问守卫阻止GT与实际注入参数；每个预测先冻结SHA再评价。V3仅独立Ring参数噪声（.1mm/轴、.3° rotvec/轴），不是分割噪声。正确D⁻¹只在评价器使用，V2/V3双向留出、留出视角与表面结果逐项完全一致；其仍有逐帧残差，不是可达误差下界。旧5种子明确为回归集，阈值保持0.5°/0.2mm。

## 受控结果

'''+mdtable(['条件','方法','位姿通过','最大旋转°','最大平移mm','最大观测Ring中心漂移mm','最大观测法向漂移°'],controltable)+'''
V0/V1均未被M3/M4破坏。精确Ring的M4与M3完全一致、漂移为数值零；V2只有1/5通过，说明限制Ring漂移并不等于恢复正确T。V3的M4通过2/5，原M2和M3均0/5；这一小回归集不能证明普遍改善。带噪Ring下“严格贴合观测Ring”不等于贴合真实物理CAD；报告区分 observed drift 与 physical error。全部72行含M0/M1及D⁻¹参考见 [CONTROL_RESULTS.csv](evidence/CONTROL_RESULTS.csv)，完整双向/GT表面指标见同名JSON。

## 真实五组

下表误差为**有限投影条件MAE**，不是完整留出均值。整轨迹20%留出，不按误差删轨迹；所有单侧/不可三角化/负深度/越界记录保留。完整MAE中有不可评价项，JSON以null并附invalid计数，CSV明确NOT_EVALUABLE_NONFINITE。方向反转时3D只由源视频独立DLT。3/6px只是诊断，各方法使用同一完整分母。

'''+mdtable(['组','源数','FIT','息肉FIT','双侧DLT/全held','M1 A→B px','M1 B→A px','M4 A→B px','M4 B→A px','LOO最大°','Clean面积保留%'],table)+'''
Ip8.8相对M1/M2两个方向均改善，固定CAD B侧Ring held约0.984px（M1 .752、M2 3.542），但条件重投影仍11.9/13.3px且LOO最大1.30°，只作后续候选。IIa14相对M1/M2改善，仍40.4/8.27px且LOO最大2.45°，不直接交接。Ip12相对M1改善、相对M2两个方向均退化，虽LOO更稳定（.194°），仍需研究。IIa22仅5条、Ip4仅3条双侧留出轨迹，均证据不足；Ip4 A→B条件残差还由663px增至1003px，失败保留。

所有M4数值求解收敛、未触发固定Ring冲突界限，这与科学验收分开。门控、逐阶段轨迹/视差/残差、6次FIT留一、空间SVD和类别分母分别在 `STAGE_SUMMARY.json`、`FIT_LOO.csv`、`FIT_SPATIAL_SUPPORT.json`、`REAL_CATEGORIES.csv`。SIFT按原方法排除Ring带，Ring类别轨迹为0，不伪造该类证据。每组FIT仅0–1条息肉点且全部支持分支原样保留；三个T完全一致是**无有效标签增量**，不是Clean提高了位姿。

## Raw/Clean的两种作用

182个Raw/Clean成对来源均使用同一T；共同原面坐标变化严格0mm。Raw面积、保留面积、排除面积、边界边数、边界分量、按面边连通的碎片数、原面ID及状态均保存。面积是各来源求和，重叠重复计入，不能当作融合面积。真实截面仍见错层/缺面；Clean删除外延碎片并可能退缩边界，未补孔、移动顶点或做主体形变。

每源预先固定96个原面面积采样（共17472样本），Raw/Clean用同一原面+bary分母；Clean排除样本保留为未覆盖。曲面评价是跨视频最近真实三角面的一致性诊断，阈值.2mm；**无真实GT，不能称表面精度/真实覆盖**。共同保留原面条件指标与全分母同时记录，见 [SURFACE_CONSISTENCY.csv](evidence/SURFACE_CONSISTENCY.csv)。只删面后的条件均值降低不解释为配准变好。

## 中文图集与可复核性

[中文HTML总索引](visuals/index.html)。每组7张PNG：六方向完整/固定近景、x=0/y=0真实三角面截面、真实RGB自动匹配/双向held、M4支持2×2、评价后单列最差实例、逐阶段支持/残差。所有同列对照用相同世界相机、共同Raw+CAD完整范围；近景仅显示固定盒内交点，框外相交原面数量明确标出。真实图无GT列，不把预测冒充GT。HTML需下载后浏览；GitHub可直接查看PNG。

代码执行前按阶段保存源码/外核SHA。运行时版本由回执为准；第一代码提交de7351cd、`EXECUTED_CODE_BEFORE_REVIEW.tar.gz`及最终源码保留阶段演化。审查修复的是缺Clean/空留出处理与历史身份断言，本批182源完整、未改既有科学预测或评价。7个契约测试通过；审查无剩余阻断项。工程失败（首次track参数重复、浮点断言容差）原日志保留，不冒充成功运行；科学失败和NOT_EVALUABLE不剔除。

资源：单科学进程、CPU affinity一核、数值/OpenCV/Open3D均1线程、nice19/ionice idle、GPU不可见。本任务检查预留3GiB、限256MiB；不调用全量调度/模型/缓存重跑，不操作上游锁/状态/日志。选中输入前后SHA一致。最终资源与只读进度收据见 `FINAL_VERIFICATION.json`。

## 下一步最小问题

优先以Ip8.8和Ip12作为候选诊断：在固定相机、固定全留出分母下，增加预先固定的跨视频帧覆盖是否能获得足够息肉轨迹，并区分错误对应/低视差/视频内相机误差。先解释背景主导及方向不对称残差，再决定能否交给共同主体拟合。当前已有T+原资产引用+面ID的接口，但5组均未获质量批准；不启动主体拟合、非刚性融合或全量Clean。
'''
 (T/'TECHNICAL_REPORT.md').write_text(report)
 index='<!doctype html><meta charset="utf-8"><title>002 中文图集</title><body style="font-family:sans-serif;max-width:1200px;margin:auto"><h1>配准噪声与 Raw/Clean：受控回归＋五组真实观测</h1><p>有改善，也有退化和证据不足；没有组获准直接主体交接。图像为真实网格/真实RGB，单位mm；真实组无三维GT。每组保留全部来源与完整留出分母。</p><img src="control.png" width="100%"><ul>'+''.join(f'<li><a href="{g}/index.html">{g}</a></li>'for g in groups)+'</ul><p><a href="../TECHNICAL_REPORT.md">技术报告</a>；各页条件MAE不可替代完整留出均值。</p></body>'
 (T/'visuals/index.html').write_text(index);print('DELIVERY SUMMARIES COMPLETE',flush=True)
if __name__=='__main__':main()
