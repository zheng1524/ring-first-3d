"""Compact full-inventory tables and report; no filtering of failed observations."""
from context import *
import csv,html,collections

def csvout(name,rows):
 p=T/'evidence'/name;p.parent.mkdir(exist_ok=True);keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='')as f:
  w=csv.DictWriter(f,keys);w.writeheader();w.writerows([{k:json.dumps(c.clean(v),ensure_ascii=False)if isinstance(v,(dict,list))else v for k,v in r.items()}for r in rows])

def main():
 inventory=read(T/'config/INVENTORY.json');groups=[];videos=[];sources=[];edges=[];regression=[];interfaces=[];missing=[]
 for row in inventory['groups']:
  g=row['group'];out=group_out(g);asset=read(out/'ASSETS.json');reg=read(out/'REGISTRATION.json');group=read(out/'GROUP.json')if(out/'GROUP.json').exists()else None;clean=read(out/'CLEAN_INDEX.json')if(out/'CLEAN_INDEX.json').exists()else[];complete=sum(r.get('status')=='COMPLETE'for r in clean);sur=read(out/'SURFACE_EVALUATION.json')if(out/'SURFACE_EVALUATION.json').exists()else{};ee=read(out/'EDGE_EVALUATION.json')
  note='可供下游试用；配准质量需结合投影和曲面复核'if reg['status']=='CONNECTED'else'单视频可读，未形成跨视频关系'if reg['status']=='SINGLE_VIDEO_ONLY'else'无合法HERO输出，未接入'
  cautions=[]
  for e in ee:
   b=e['methods']['M4']['bidir'];rb=e['methods']['M4']['ring']['by_side']['B'];r0=e['methods']['M0']['ring']['by_side']['B']
   if not b['denominators']['evidence_sufficient']:cautions.append('双侧留出支持量不足')
   if any((b[d]['conditional_median']or 0)>6 for d in ['A_to_B','B_to_A']):cautions.append('典型重投影残差仍偏大')
   if any((b[d]['conditional_P95']or 0)>30 for d in ['A_to_B','B_to_A']):cautions.append('保留明显尾部异常')
   if rb['conditional_MAE']is not None and r0['conditional_MAE']is not None and rb['conditional_MAE']>r0['conditional_MAE']+1:cautions.append('Ring吻合有明显代价')
   for method,m in e['methods'].items():
    for direction in ['A_to_B','B_to_A']:
     b0=m['bidir'][direction];edges.append(dict(group=g,parent=e['parent'],child=e['child'],method=method,direction=direction,FIT_tracks=e['FIT_tracks'],held_tracks=m['bidir']['denominators']['all_held_tracks'],two_sided_held=m['bidir']['denominators']['two_sided_DLT_tracks'],**{k:v for k,v in b0.items()if k!='categories'},Ring_B_conditional_MAE=m['ring']['by_side']['B']['conditional_MAE'],common_finite_N=e['common_finite'][direction]['methods'][method]['N'],common_finite_conditional_MAE=e['common_finite'][direction]['methods'][method]['conditional_MAE']))
  grow=dict(row,registration=reg['status'],clean_complete=complete,clean_missing=len(asset['sources'])-complete,review_ready=(out/'REVIEW_COMPLETE.json').exists(),downstream_note=note,cautions='；'.join(sorted(set(cautions))))
  if ee:
   b=ee[0]['methods']['M4']['bidir'];grow.update(A_to_B_mean=b['A_to_B']['conditional_MAE'],B_to_A_mean=b['B_to_A']['conditional_MAE'],A_to_B_median=b['A_to_B']['conditional_median'],B_to_A_median=b['B_to_A']['conditional_median'])
  groups.append(grow)
  for v in asset['all_video_states']:
   connection=reg['videos'].get(v['case'],{});videos.append(dict(group=g,case=v['case'],upstream_status=v['upstream']['status'],upstream_outcome=v['upstream'].get('outcome'),legal_sources=v['upstream'].get('legal_targets',0),asset_status=v['status'],registration=connection.get('status','NO_OUTPUT'),reference=reg['reference'],path=connection.get('path'),asset_error=v['error']))
  for r in clean:sources.append(dict(group=g,source_id=r['source']['source_id'],case=r['source']['case'],tag=r['source']['tag'],status=r['status'],origin=r['origin'],raw_faces=r.get('raw_faces'),trusted_faces=r.get('trusted_faces'),raw_area_mm2=r.get('raw_area_mm2'),trusted_area_mm2=r.get('trusted_area_mm2'),selection=r.get('selection_path'),error=r.get('error')))
  if group:interfaces.append(dict(group=g,path=str(out/'GROUP.json'),sha256=sha(out/'GROUP.json'),status=reg['status'],sources=len(group['sources'])))
  if complete!=len(asset['sources'])or not(out/'REVIEW_COMPLETE.json').exists():missing.append(g)
  if g in CFG['regression_groups']:
   old=read(prior_run()/g/'PREDICTIONS.json')['M4']['T'];new=reg['edges'][0]['results']['M4']['T'];delta=float(np.max(abs(np.array(old)-new)));assert delta<1e-12
   oldmetrics=read(prior_run()/g/'EVALUATION.json')['methods']['M4']['bidir'];newmetrics=ee[0]['methods']['M4']['bidir']
   regression.append(dict(group=g,T_max_abs_difference=delta,**{prefix+'_'+d:metrics[d]['conditional_MAE']for prefix,metrics in [('old',oldmetrics),('current',newmetrics)]for d in ['A_to_B','B_to_A']},domain='same reference, tracks, held identity, DLT, Ring prior; development regression, not blind'))
 csvout('GROUP_STATUS.csv',groups);csvout('VIDEO_STATUS.csv',videos);csvout('SOURCE_STATUS.csv',sources);csvout('EDGE_RESULTS.csv',edges);csvout('SIX_GROUP_REGRESSION.csv',regression)
 surface_rows=[]
 for row in inventory['groups']:
  p=group_out(row['group'])/'SURFACE_EVALUATION.json'
  if not p.exists():continue
  for pair in read(p)['pairs']:
   for method,metrics in pair['metrics'].items():
    for direction,r in metrics.items():
     if isinstance(r,dict):surface_rows.append(dict(group=row['group'],A=pair['A'],B=pair['B'],method=method,direction=direction,coverage_fraction=r.get('coverage_fraction'),**r.get('full_raw_sample_domain',{}),excluded_samples=r.get('source_sample_excluded')))
 csvout('SURFACE_RESULTS.csv',surface_rows)
 save(T/'GROUP_INDEX.json',dict(schema='R1_M4_GROUP_INDEX_1',method='M4',units='mm',groups=interfaces,all_manifest_groups=len(groups),all_manifest_videos=len(videos),source_total=sum(r['sources']for r in inventory['groups']),body_fitting_started=False))
 summary=dict(groups=len(groups),videos=len(videos),available_videos=sum(r['available_videos']for r in groups),HERO_sources=sum(r['sources']for r in groups),registered_multivideo_groups=sum(r['registration']=='CONNECTED'for r in groups),single_video_groups=sum(r['registration']=='SINGLE_VIDEO_ONLY'for r in groups),no_output_groups=sum(r['registration']=='NO_OUTPUT'for r in groups),clean_complete=sum(r['clean_complete']for r in groups),clean_origins=dict(collections.Counter(r['origin']for r in sources)),pending=missing)
 save(T/'evidence/SUMMARY.json',summary)
 def fmt(v):return '不可评价'if v is None else f'{v:.2f}'
 rows=[]
 for r in groups:
  rows.append('<tr><td><a href="'+r['group']+'/index.html">'+r['group']+'</a></td><td>'+r['registration']+'</td><td>'+str(r['available_videos'])+'/'+str(r['videos'])+'</td><td>'+str(r['clean_complete'])+'/'+str(r['sources'])+'</td><td>'+fmt(r.get('A_to_B_mean'))+' / '+fmt(r.get('B_to_A_mean'))+'</td><td>'+fmt(r.get('A_to_B_median'))+' / '+fmt(r.get('B_to_A_median'))+'</td><td>'+r['cautions']+'</td></tr>')
 (T/'visuals/index.html').write_text('<!doctype html><meta charset="utf-8"><title>R1 M4 全量配准</title><style>body{font-family:sans-serif;max-width:1800px;margin:auto}td,th{padding:7px;border:1px solid #ccc}table{border-collapse:collapse}</style><h1>R1 M4 全量配准与可信面</h1><p>'+html.escape(json.dumps(summary,ensure_ascii=False))+'</p><p>配准前 Raw／M4 配准后 Raw／M4 可信 Clean。单位mm，无三维GT。均值、中位数为有限投影条件统计；完整失效分母见 EDGE_RESULTS.csv。连接状态不等于科学配准验收；Clean不改变T。</p><table><tr><th>组（点击图集）</th><th>状态</th><th>有输出/全部视频</th><th>Clean/全部来源</th><th>A→B / B→A 均值px</th><th>中位数px</th><th>需留意</th></tr>'+''.join(rows)+'</table>')
 if missing:print('DELIVERY PENDING',missing);return
 text='''# TASK-V6-R1-M4-REGISTRATION-MAINLINE-002

本轮统一采用原 M4，已处理 R1 全量 39 组、79 个视频：27 个双视频组恢复视频级共同坐标（54 视频、989 个 HERO 来源）；8 组仅单视频有输出（164 源）；4 组无输出。全部 62 个有输出视频、1,153 个合法来源均有统一接口及对应可信面。连接成功表示流程完成，不表示所有组的配准精度均已通过。

## 异常是否真的拖动 T，为什么保留原 M4？

原六组是已看过的开发回归。对冻结 FIT 去除最高残差5%后，T变化约0.03–0.27°、0.002–0.043mm；移除距FIT点集中心最远的5%轨迹，T旋转变化约0.02–0.49°。双向held变化很小且方向不一致。IIa14/R10去除高FIT残差后均值约125.96/30.47px，原值126.00/30.45px，不能由held极端值断言FIT把T拖错。

因此没有硬加新算法，全量固定原`solver2.py@efa0adfb` M4：三维地标逐坐标soft_l1按1/N归一化，独立五维Ring二次先验保持原强度；每视频一个SE(3)，尺度1。诊断trim仅用于开发解释，未按组选择旧/新T。决策在新增组求解前冻结于[DECISION.json](config/DECISION.json)。完整诊断见[FIT_DIAGNOSIS.json](evidence/FIT_DIAGNOSIS.json)。

## 原来好的组、困难组与新增组

六组回归的T逐元素差为0，参考、自动轨迹、FIT/held、DLT与Ring先验相同：[回归表](evidence/SIX_GROUP_REGRESSION.csv)。IIa14/R5保持原表现，双向条件均值5.01/4.01px、中位数2.69/3.61px。

新增IIa9.5/R10双向条件均值4.53/6.98px、中位数2.39/2.95px，适合下游试用复核。IIa14/R10的均值126.00/30.45px、中位数4.38/3.90px；新增Is9.79/R10为8.34/327.71px、中位数4.19/3.69px，均说明尾部异常不能被隐藏，也不能单凭均值认定整个T失效。Ip4/R10、Ip8.8/R5仍有较大的典型投影残差；Ip8.8/R5的Ring代价也保留。Is18/R5、Ip7.1/R10、Is8.8/R5的双侧留出量偏少，使用时需留意证据不足。

27组中23组的双向有限投影条件均值均较M0下降；Ip6.2/R10、Is18/R10、Is9.79/R10、Is18/R5至少一个方向未改善。Is9.79/R10反向均值由103.57升至327.71px，Is18/R10由76.14升至96.16px，负结果不能被中位数较好掩盖。但Is9.79/R10的反向有限观测由40变41，其中一个原先负深度的观测变为有限极端投影；共同40个观测的均值实际由103.57降到4.19px。不能把有限集合变化误判为整个T变差，也不删除这个新极端值。共同有限观测域上的双向改善为24/27组，仍有Ip6.2/R10、Is18/R10、Is18/R5至少一向未改善。统计分母、失效数量和共同有限观测辅助均值均在结果表中。

这些说明是审阅提示，不是新自动拒绝门槛，也不按held改T。全量双向均值/中位数/P95、有效/失效/负深度/越界、Ring见[EDGE_RESULTS.csv](evidence/EDGE_RESULTS.csv)，全部39组状态与提示见[GROUP_STATUS.csv](evidence/GROUP_STATUS.csv)。同一方法完整held含缺DLT等失效，完整MAE不可评价时保留null；有限条件统计不冒充完整均值。每条边另保留共同有限观测ID比较。

## 全量范围与输入身份

实际终态读取`runs/v6_r1_full_b_001`；R1执行提交`29874fe61f59c429fb83d2377ab707c847992ef8`，manifest SHA `d414c797d66cdce88f5edf6793b10709cd74cfa0fe9e15a6dd2b977df2770515`。工作树基础`f7a3ff8581a80b44adc9eb8415d11748f086a6ee`。终态为39组79视频、62视频有输出、1,153合法HERO源，其余17视频为SCIENTIFIC_ZERO；不是HERO执行失败。终态摘要已在[UPSTREAM_TERMINAL.json](evidence/UPSTREAM_TERMINAL.json)补齐，不修改上游快照。

全部视频、无输出原因和资产状态保留于[VIDEO_STATUS.csv](evidence/VIDEO_STATUS.csv)。当前可用分布是27对＋8单视频；原manifest有三视频组，但本次没有三路同时有HERO的组。多视频共享轨迹与中转代码有契约测试，尚无本轮真实三路证据。

每组按可用case字典序选择参考，不看held或曲面效果。所有现有可用视频纳入，代表帧沿ledger等间隔至多8帧；新增组一次全视频匹配，原V6 SIFT6000/互向ratio .72及连通轨迹mod5划分，背景允许。各求解边共享原始轨迹/held身份，不把求解用过的特征当独立留出。优先直接参考，必要时用同一M4经已连接视频中转，不能连通者T为空。此次27对均得到T，未实际触发中转。上游BA已用观测标记仍保留，因此是新跨视频对应留出，不宣称相机训练独立。

## Clean、统一接口和曲面评价

统一入口为[GROUP_INDEX.json](GROUP_INDEX.json)，指向每组`GROUP.json`。每个来源以case+tag唯一登记，包含原Raw/native SHA、Target/Support、所属视频、T和可信原面索引；所有原始顶点引用只应用一次T，全视频相机和其内部地标已导出为COMMON坐标并显式标注，跨视频独立DLT地标单独保存。消费者无需判断M4/M5或candidate特例。

先冻结M4，再按017+gap、018原规则分类，只取原`F[state==0]`。实际703源核验同坐标复用，450源配准后新分类；1,153源后续复核复用了这批冻结分类，未重复计为新计算。参考侧仅在Raw、native、相机链、CAD和分类器SHA一致时复用R1原标签；非参考侧重新调用上一轮真实`clean_after.one`，没有使用M5标签。Clean只改保留面，没有额外顶点变化。旧六组221源的原面采样ID/重心坐标与历史完全一致；IIa14/R5的42源M4标签逐面复核改变数为0，原candidate补充已经成为统一常规路径。所有来源均由轻量读取器实际加载，核对相机坐标与轴向Z不变；本轮没有主体拟合。

曲面指标使用每源固定96个原面面积样点，Raw/Clean同域；删去的样点仍占完整分母并记未覆盖。最近真实三角面距离仅为跨视频一致性，0.2mm覆盖是固定样本距离阈值，不是GT表面完整率。[SURFACE_RESULTS.csv](evidence/SURFACE_RESULTS.csv)和[SOURCE_STATUS.csv](evidence/SOURCE_STATUS.csv)保留Raw/Clean及逐源面积变化。不能把清理整洁算作位姿提高。

代表性Raw跨视频最近三角面均距（A→B / B→A，mm，同一完整原样点域）：

|组|配准前|M4后|解释|
|---|---|---|---|
|IIa14/R5|0.0570 / 0.1287|0.0489 / 0.0595|改善|
|IIa9.5/R10|0.0159 / 0.0381|0.0162 / 0.0384|基本不变，不能把RGB改善扩大成曲面精度提升|
|Ip4/R10|0.1388 / 0.0583|0.1454 / 0.0616|略差，投影残差也仍偏大|


## 实现、验证与限制

已复用而未复制重写科学核：002的匹配/DLT/Ring/M4/评价、001的V6特征和几何核、R1的配准后Clean、017/018分类及原三角面渲染/截面。历史模块由Git提交解析到任务缓存，不要求保留旧临时工作树；原科学数据仍为可核验本地引用。配置、复用表和执行计划见[EXECUTION_PLAN.md](EXECUTION_PLAN.md)，单组/全量/续跑及消费者命令见[REPRODUCE.md](REPRODUCE.md)。

科学核保持原版。独立代码审查修复了中断目录无法续跑、单独输出/评价绕过输入与T冻结校验的问题，并补全多视频中转遍历；没有通过改变算法修复统计。初次全量计算使用9b00c9b32的编排，后续用修正入口核验冻结输入和全部缓存，结果T与科学核不变。源代码/运行回执和失败测试均保留。

中文[图集入口](visuals/index.html)覆盖所有组：配准前Raw／M4后Raw／M4可信Clean，同视角同尺度；完整范围、固定近景、真实三角截面、RGB/Ring及全相机布局。无输出组展示原因，不制造空的成功图。没有三维GT，绝对配准或重建精度仍无法证明。

下一阶段可直接从统一GROUP入口选择观测开展共同主体试用。建议先复核IIa14/R5和新增IIa9.5/R10，并对高尾部而中位数较好的组检查少量真实对应，区分误匹配、独立DLT和视频内部相机误差；不引入逐帧自由度或主体形变吸收残差。
'''
 (T/'TECHNICAL_REPORT.md').write_text(text);print('DELIVERED',summary,flush=True)
if __name__=='__main__':main()
