"""Concise full-denominator report, comparisons, preservation list and portable small evidence."""
from core import *
from geometry import *
import csv,collections,shutil,tarfile
def table(path,rows):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if not rows:return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w')as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows([{k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(list,dict))else v for k,v in r.items()}for r in rows])
def avg(rows,key):
 v=[r[key]for r in rows if r.get(key)is not None];return float(np.mean(v))if v else None
def main():
 index=read(M4/'GROUP_INDEX.json')['groups'];rows=[];group_rows=[];failures=[];preserve={};objects=[];biasrows=[]
 for item in index:
  g=item['group'];auditpath=T/'runs/inputs'/g/'AUDIT.json';a=read(auditpath);root=T/'runs/results'/g;rec=read(root/'GROUP_RESULT.json');objects.append(rec)
  for x in a['files']:preserve[x['path']]=dict(x,reason='R1 frozen input')
  for x in [a['old_group'],asset(Path(item['path']).with_name('ASSETS.json')),asset(M4/'GROUP_INDEX.json')]:preserve[x['path']]=dict(x,reason='M4 source index and transform identity')
  for s in a['sources']:
   for p,h in [(s['raw_mesh'],s['raw_mesh_sha256']),(s['native_depth'],s['native_sha256']),(s['selection'],s['selection_sha256'])]:preserve[p]=dict(path=p,sha256=h,reason='M4 Raw/native/trusted face mapping')
  local=[]
  for r in rec['results']:
   folder=root/r['configuration'];base=read(folder/'BASE.json');ev=read(folder/'EVALUATION.json');body=np.load(folder/'BODY.npz');mother=np.load(folder/'FINAL_UNCUT.npz');bias=np.array([x['b_mm']for x in r['bias']]);removed=int(((mother['V'][mother['F']]@np.array(base['plane'][:3])+base['plane'][3]<0).all(1)).sum())if base.get('plane')is not None else 0
   row=dict(group=g,configuration=r['configuration'],status=r['status'],input_kind=r['input_kind'],videos=r['videos'],sources=r['source_N'],fit_IoU=r['fit_IoU_mean'],held_IoU=r['held_IoU_mean'],initial_held_IoU=avg([x for x in ev['initial']['projections']if x['role']=='HOLDOUT'],'IoU'),parent_held_IoU=avg([x for x in ev['parent']['projections']if x['role']=='HOLDOUT'],'IoU'),fixed_depth_N=r['depth_fixed_N'],valid_depth_N=r['depth_valid_N'],invalid_depth_N=r['depth_invalid_N'],bias_abs_median_mm=float(np.median(abs(bias)))if len(bias)else None,bias_abs_max_mm=float(max(abs(bias)))if len(bias)else None,base_status=r['base_status'],base_applied=r['base_applied'],base_unique_targets=base.get('unique_targets',0),base_cut_side_trusted_N=base.get('original_trusted_removed_side_N',0),base_cut_side_trusted_fraction=base.get('original_trusted_removed_side_fraction'),base_negative_p95_mm=base.get('negative_distance_p95_mm'),mother_faces=len(mother['F']),mother_fully_below_plane_faces=removed,inferred_cap_faces=int(body['inferred_base_faces'].sum()),corrected_CAD_conflict_N=sum(x['corrected_CAD_conflict_N']for x in ev['final']['depth']),original_CAD_conflict_N=sum(x['original_CAD_conflict_N']for x in ev['final']['depth']),corrected_negative_Z_N=sum(x['corrected_negative_Z_N']for x in ev['final']['depth']),shape_condition=r['initialization']['H_condition'],seconds=r['seconds'],GT='NOT_EVALUABLE')
   rows.append(row);local.append(row)
   for b in r['bias']:biasrows.append(dict(group=g,configuration=r['configuration'],**b))
  failures.extend([dict(group=g,**f)for f in rec['failures']]);single=[r for r in local if r['configuration']!='JOINT'];joint=next((r for r in local if r['configuration']=='JOINT'),None)
  group_rows.append(dict(group=g,registered_videos=len(rec['all_video_cases']),single_results=len(single),joint_result=joint is not None,joint_held_IoU=joint['held_IoU']if joint else None,mean_single_held_IoU=avg(single,'held_IoU'),joint_minus_single_held_IoU=(joint['held_IoU']-avg(single,'held_IoU'))if joint and joint['held_IoU']is not None else None,failed_slots=len(rec['failures']),excluded_from_joint=rec['joint_excluded_cases']))
 table(T/'evidence/CONFIGURATION_RESULTS.csv',rows);table(T/'evidence/GROUP_COMPARISON.csv',group_rows);table(T/'evidence/SOURCE_BIASES.csv',biasrows);save(T/'evidence/FAILURES.json',failures);table(T/'evidence/PRESERVE_DEPENDENCIES.csv',list(preserve.values()))
 save(T/'INITIALIZATION_INDEX.json',dict(schema='R1_COARSE_BODY_INIT_1',units='mm',upstream_commit=BASE,config_sha256=sha(T/'config.json'),groups=[dict(group=o['group'],path=str(T/'runs/results'/o['group']/'GROUP_RESULT.json'),sha256=sha(T/'runs/results'/o['group']/'GROUP_RESULT.json'),configurations=[dict(name=r['configuration'],path=str(T/'runs/results'/o['group']/r['configuration']/'RESULT.json'),sha256=sha(T/'runs/results'/o['group']/r['configuration']/'RESULT.json'),kind=r['input_kind'],base=r['base_status'])for r in o['results']],failures=o['failures'])for o in objects]))
 count=collections.Counter(r['input_kind']for r in rows);basecount=collections.Counter(r['base_status']for r in rows);applied=[r for r in rows if r['base_applied']];jointdiff=[r['joint_minus_single_held_IoU']for r in group_rows if r['joint_minus_single_held_IoU']is not None];control=read(T/'evidence/CONTROL_RESULT.json');verify=read(T/'evidence/FINAL_VERIFICATION.json')
 figures=T/'figures';figures.mkdir(exist_ok=True);chosen=[('BROAD','GP_IIa_14.0mm_closed_R5_single_refY','005'),('STALK','GP_Ip_12.0mm_closed_R10_single_refY','JOINT')]
 worst=min(rows,key=lambda r:r['held_IoU']if r['held_IoU']is not None else 1);chosen.append(('LOWEST_HELD',worst['group'],worst['configuration']))
 applied_rows=[r for r in rows if r['base_applied']];cutworst=max(applied_rows,key=lambda r:r['base_cut_side_trusted_fraction']or 0)if applied_rows else None
 if cutworst:chosen.append(('MAX_CUT_CONFLICT',cutworst['group'],cutworst['configuration']))
 for alias,g,c in chosen:
  for name in ['RGB_PROJECTIONS','GEOMETRY_SECTIONS']:
   src=T/'runs/results'/g/c/(name+'.png')
   if src.exists():shutil.copyfile(src,figures/(alias+'_'+name+'.png'))
 summary=dict(groups=39,videos=79,original_hero_videos=62,zero_hero_videos_audited=17,hero_sources=1153,configurations=len(rows),single=sum(r['configuration']!='JOINT'for r in rows),joint=sum(r['configuration']=='JOINT'for r in rows),kinds=dict(count),bases=dict(basecount),base_applied=len(applied),failed_slots=len(failures),joint_improves_mean_single_held=sum(v>0 for v in jointdiff),joint_comparison_N=len(jointdiff),joint_minus_single_median=float(np.median(jointdiff))if jointdiff else None,all_config_fixed_depth_samples=sum(r['fixed_depth_N']for r in rows),all_config_invalid_depth_samples=sum(r['invalid_depth_N']for r in rows),bias_abs_max_mm=max((r['bias_abs_max_mm']or 0)for r in rows),selected_figures=chosen,lowest_held=worst)
 save(T/'evidence/SUMMARY.json',summary)
 text=f'''# R1 全量粗主体初始化与基底截断

本轮完成 **{len(rows)} 个新初始化：{summary['single']} 单视频、{summary['joint']} 联合**，覆盖 39 组、79 视频；失败槽 {len(failures)}。其中 {count.get('DXY_MASK_2D_ONLY',0)} 个为明确标记的二维约束结果。它们是可审阅粗初体，不是已验证真实形状，也没有启动自由顶点更新。

## 结论与限制

- **已经验证**：R1 输入身份、79 视频审计、原 62 个 M4 变换逐值不变；新增 17 视频可读取相机/二维观测并获得冻结 M4 的数值变换。1153 HERO 来源从 state==0 的真实原面筛出原生像素，不将完整 V 当可信点云。新变换没有获得绝对配准精度认证。
- **已经执行**：同一个九参数椭球框架；单视频仅用自身观测，联合真实重算全部参与观测。配置 {dict(count)}；基底状态 {dict(basecount)}，实际应用并细化 {len(applied)} 个。弱基底候选与正式未裁母体分开，未借基底门控跳过二维初始化。
- **初步有效**：共同二维观测能给出多数可解释的低维轮廓；联合相对单视频平均留出 IoU 改善 {summary['joint_improves_mean_single_held']}/{len(jointdiff)} 组，差值中位数 {summary['joint_minus_single_median']:.4f}。这个共同样本比较保留全部组，并不说明联合总是更好。
- **仍需研究**：深度偏置可辨识性、局部背景是否真为附着面、头部与未解释蒂部的关系。不能把 RELIABLE 的内部一致性标签当独立基底真值。
- **当前无法评价**：真实部署形状精度、绝对基底位置、真实 HERO 偏差。没有为真实数据读取 GT 或按 GT 调参。

## 采用的方法与复用

实际基础提交 `80d00ad3530abfd782e27a2c1981a272bf9739e7`；R1 执行 `29874fe61f59c429fb83d2377ab707c847992ef8`。原始 R1/M4/Raw/Clean 已存在，本轮新算二维目标、固定可信深度样本、背景平面、粗体/偏置与裁切；没有重跑上游。

| 资产 | 实际入口与适配 |
|---|---|
| M4/Clean `80d00ad` | GROUP_INDEX/GROUP/ASSETS 与原始可信面；`observations.prepare_video` 按 consume 契约薄读，额外保存原面和原生像素 ID |
| 冻结 M4 | `supplement.py` 调用原 `video_asset / matches / solve_edge`；仅补新视频，旧 T 原值保留 |
| DXY `75d58ca5` | 原 `adapters/dxy.measure_pixels`；只使用像素中心、基底矩阵与质量回执，不输出其毫米读数。任务书 b1f8… 在本地不可解析；实际加载当前基线适配器并锁 SHA |
| A1 `4a09aed` | 原 `decode/ray_components/first_depth/ellipse_projection/signed_distance/robust`，AST 原样加载；旧配置和旧训练体不继承 |
| 009 `84a747a` | 原 RANSAC `fit_plane`；多来源邻近背景 ROI，ROI 不算独立视角，法向符号等价比较 |
| 010 `534b959` | 原 `clip/ear_clip` 精确半空间裁切、原边/面映射与推断底盖标记；未继承后续更新器 |
| 018 `62c286f` | 只采用轴向毫米、固定域、缺失罚项的契约；本轮解析低维射线前向，不启动其 PyTorch3D 更新器 |

每配置初值仅来自 DXY/Mask 像素中心射线和投影尺寸。弱视差时显式使用 Ring 邻域深度先验；不是三维实测。固定 8 个二维拟合视角、2 个主体二维留出视角/视频，每 HERO 最多 64 个可信原生像素。表中 IoU 在运行前固定的 16 px 网格计算，是采样轮廓指标；不是全分辨率像素 IoU。按视频、方向密度及 Target/Support 重叠分配固定来源质量，未按贴合程度调权。真实可见轮廓权重高于 DXY 补全先验；背景 RGB 地标未用作息肉深度真值。

theta 使用有界最小二乘，b 使用逐来源一维求解与完整目标接受检查。`|b|≤0.4 mm`，先验 sigma 0.15 mm，深度尺度 0.5 mm。先拟合母体，再固定可靠平面做短细化；目标只在同阶段比较。{verify['monotone_stage_steps']} 个阶段步骤通过非增检查。母体切换到裁切模型后目标可能上升，此跳变单独保存。DXY仍作为完整母体先验；真实可见边界与Mask项包含截断轮廓。

可靠平面方向依据观测相机位于局部背景的哪侧，并另检突出/接触证据；不按近零息肉高度中位数定向。背景/CAD不应用 b，平面不是世界高度减 b。保持平面固定；底盖只用于封口，cap-only 原生观测仍计未解释并受罚。固定深度分母在全部配置合计 {summary['all_config_fixed_depth_samples']}（同一来源在单/联合中分别计），失效 {summary['all_config_invalid_depth_samples']}；源级独立数仍为 1153。

## 受控检查、反例与实际观察

复用已有虚拟 G01 三角网格与渲染器，重新生成观测；本轮已知支撑平面放在该既有形状最低附着点，是声明的控制条件，不冒充历史实测背景。GT 和注入量只在生成/冻结后评价中使用。固定真实网格诊断的 b 恢复误差均小于 0.001 mm；正确 b 沿射线反投误差也小于 0.001 mm。

**粗椭球并未准确恢复注入 ±0.25 mm**：约校正 ±0.02 mm，保守先验与低维形状误差仍占主导。该失败保留，未据 GT 放宽偏置。完整母体对虚拟 GT 单向距离中位/P95 为 {control['parent_to_GT_mm']['median']:.3f}/{control['parent_to_GT_mm']['p95']:.3f} mm，仅为受控指标，不是全面覆盖精度。

错误基底高度切侧观测 214/512，翻侧 509/512；翻侧触发整主体裁除失败，没有用完整母体冒充裁切成功。真实宽接触示例中 005 产生实际截断；其 004 和联合平面不够稳定，保留候选。Ip12/R10 的 004 无 HERO，仍给出二维初体；蒂部不由椭球强拉成粗底座。

最低留出轮廓结果：`{worst['group']} / {worst['configuration']}`，IoU {worst['held_IoU']:.3f}。所有缺失、CAD 冲突、切侧原始可信点和失败槽均在 CSV/JSON 内保留。几何更一致或优化收敛均不等同于科学重建成功。主体二维留出可能参与过上游相机或 HERO Support，不能称端到端独立测试。

## 交付与下一步

本地全量入口：`runs/results/index.html`；每组并列单视频/联合，含实际 RGB 投影、固定尺度三维图、近景及真实三角面截面。图中 HERO 三角面均匀选每视频两个来源以保持可读，指标仍使用全部来源；不删评价分母。

关键图：[宽接触裁切](figures/BROAD_GEOMETRY_SECTIONS.png)、[宽接触 RGB](figures/BROAD_RGB_PROJECTIONS.png)、[有蒂联合](figures/STALK_GEOMETRY_SECTIONS.png)、[最低留出投影](figures/LOWEST_HELD_RGB_PROJECTIONS.png)、[最大切侧冲突](figures/MAX_CUT_CONFLICT_GEOMETRY_SECTIONS.png)、[错误基底](figures/CONTROL_BASE_FAILURE.png)。最大切侧冲突配置为 `{cutworst['group']if cutworst else '无'}/{cutworst['configuration']if cutworst else ''}`；它用于人工排查，不据此判定所有切侧点都是错误观测。

复现命令见 [README](README.md)。完整配置表、单/联合比较、偏置表和保留依赖分别在 `evidence/CONFIGURATION_RESULTS.csv`、`GROUP_COMPARISON.csv`、`SOURCE_BIASES.csv`、`PRESERVE_DEPENDENCIES.csv`。`INITIALIZATION_INDEX.json` 与 `consume_body.py` 提供参数、实际面、底盖、原始来源与 b 接口。校正后新增 CAD 矛盾在表中单独计数，原 TRUSTED 身份不为新位置背书。

下一轮最小问题：对少量多视角接触证据充分的配置，验证能否用独立的息肉跨视角证据约束来源偏置，并人工复核局部基底及未解释蒂部，再决定是否授权高自由度更新。本轮止于粗初始化。
'''
 (T/'TECHNICAL_REPORT.md').write_text(text)
 print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
