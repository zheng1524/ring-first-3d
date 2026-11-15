"""Report every group/arm, including rollback; never selects a prediction."""
from common import *
from collections import Counter
CFG=load(R/'config/PROTOCOL.json')
def f(x,n=4):return 'NOT_EVALUABLE'if x is None else str(round(float(x),n))
def main():
 m=load(R/'metrics/COMPARISON.json');by={(x['group'],x['arm']):x for x in m};pairs=load(R/'metrics/HERO_PAIR_AGGREGATES.json');grad=load(R/'metrics/REAL_NOHIT_GRADIENTS.json');rows=[];fail=[]
 for g in CFG['groups']:
  for arm in ['B1','B2','B3']:
   hh=load(R/'metrics'/(g+'_'+arm+'_ROUNDS.json'));bb=load(R/'metrics'/(g+'_'+arm+'_BIAS.json'));tr=load(R/'metrics'/(g+'_'+arm+'_TRIALS.json'));a=np.load(R/'runs'/g/arm/'FINAL.npz');r=dict(group=g,arm=arm,rounds=len(hh),accepted_rounds=sum(h['accepted']for h in hh),body_updates=hh[-1]['accepted_total'],corrected_sources=int((abs(a['theta']).max(1)>1e-8).sum()),bias_status=dict(Counter(x['status']for x in bb)),candidate_rejects=dict(Counter(y for x in tr for y in x['reasons'])),outer_rejects=dict(Counter(y for x in hh for y in x['reasons'])),seconds=load(R/'runs'/g/arm/'FINAL.json')['seconds']);rows.append(r)
   for h in hh:
    if not h['accepted']:fail.append(dict(group=g,arm=arm,round=h['round'],reasons=h['reasons'],hit_delta=h['candidate']['hit']-h['before']['hit'],matched_delta=h['candidate']['matched']-h['before']['matched'],evidence='metrics/'+g+'_'+arm+'_ROUNDS.json'))
 table('metrics/EXECUTION_SUMMARY.csv',rows);save('metrics/EXECUTION_SUMMARY.json',rows);table('metrics/OUTER_FAILURES.csv',fail);table('metrics/MODEL_MEASUREMENTS.csv',[{k:r[k]for k in ['group','arm','Dxy_model_mm','estimated_base_Hmax_mm','estimated_base_H95_mm','base_height_status','area_solid_mm2','volume_conditional_mm3','volume_status','watertight','winding_consistent','self_intersections']}for r in m])
 text='''# 共享Body锚定多HERO交替优化：正式R3技术摘要

四个独立物理组、75个原生FIT HERO来源、B0/B1/B2/B3共16个状态已实际运行。**闭环可运行，不等于多来源错层已经解决或测量精度得到证明。** 下面只报告契约修复后的正式R3，早期工程结果全部归档。未读GT、未做ICP、未改相机、未重新推理HERO。

|组|FIT来源|修正后首层MAE mm B0→B3|固定原生首层命中 N|FIT IoU|HOLDOUT IoU|Body最大位移mm|
|---|---:|---:|---:|---:|---:|---:|
'''
 for g in CFG['groups']:
  a,b=by[g,'B0'],by[g,'B3'];text+=f"|{g}|{a['source_N']}|{f(a['depth_corrected_MAE_mm'])} → {f(b['depth_corrected_MAE_mm'])}|{a['hit_N']} → {b['hit_N']} / {b['fixed_N']}|{f(a['FIT_IoU'])} → {f(b['FIT_IoU'])}|{f(a['HOLDOUT_IoU'])} → {f(b['HOLDOUT_IoU'])}|{f(b['max_displacement_mm'],6)}|\n"
 text+='\n修正后MAE在有效首层命中上计算，不是独立三维真值。校正HERO使其更接近Body，可能只改善自洽；因此另列不校正的原生深度、原生留出HERO和真实留出Mask。\n\n|组|未校正原生深度MAE mm：B0 / B2 / B3|B2 / B3 留出IoU|\n|---|---:|---:|\n'
 for g in CFG['groups']:
  a,c,b=by[g,'B0'],by[g,'B2'],by[g,'B3'];text+=f"|{g}|{f(a['depth_raw_MAE_mm'])} / {f(c['depth_raw_MAE_mm'])} / {f(b['depth_raw_MAE_mm'])}|{f(c['HOLDOUT_IoU'])} / {f(b['HOLDOUT_IoU'])}|\n"
 text+='\n## 来源间可见性一致性\n\n|组|同视频MAE mm B0→B3|跨视频MAE mm B0→B3|\n|---|---:|---:|\n'
 for g in CFG['groups']:
  vals=[]
  for typ in ['SAME_VIDEO','CROSS_VIDEO']:
   rr=[next((p for p in pairs if p['group']==g and p['arm']==a and p['pair_type']==typ),None)for a in ['B0','B3']];vals.append(' → '.join(f(r['MAE'])for r in rr)if all(rr)else'NOT_AVAILABLE：无该类来源对')
  text+='|'+g+'|'+'|'.join(vals)+'|\n'
 text+='''
这些查询处理了真实相机、原生深度网格与CAD遮挡。0.5mm带内支持、前方分歧、更深层观测、CAD遮挡和UNKNOWN独立列出；后层不自动记作错误。照片配对单列PHOTO_INVOLVED；G06没有跨视频分母。完整N、median、P95在HERO_PAIR_AGGREGATES.csv和逐对CSV。它们不是独立GT，源间相关性仍存在。

## 实际提交的更新

|组|方案|外轮|有效Body更新|最终非零校正来源|外层拒绝|
|---|---|---:|---:|---:|---|
'''
 for r in rows:text+='|'+ '|'.join([r['group'],r['arm'],str(r['rounds']),str(r['body_updates']),str(r['corrected_sources']),str(r['outer_rejects'])])+'|\n'
 text+='\n## 逐组判断\n\n'
 for g in CFG['groups']:
  a,b=by[g,'B0'],by[g,'B3'];rr=next(r for r in rows if r['group']==g and r['arm']=='B3');text+=f"- **{g}**：B3提交{rr['body_updates']}次Body更新、{rr['corrected_sources']}个来源保留非零修正；相对B0新增命中{b['new_hit_B0']}、丢失命中{b['lost_hit_B0']}、共同命中{b['common_hit_B0']}。修正后MAE变化{f(b['depth_corrected_MAE_mm']-a['depth_corrected_MAE_mm'])} mm，未修正原生MAE变化{f(b['depth_raw_MAE_mm']-a['depth_raw_MAE_mm'])} mm；拒绝原因{rr['outer_rejects']}。无更新/回退不称为形态改善。\n"
 text+='''
G03的巨大错层/花瓣不能因内部TRUSTED标签被认作全局准确。沿固定射线的三参数无法任意修复横向/旋转误差；大部分独特新表面缺少可靠同层重叠时必须保留UNEXPLAINED，而不是扩大边界强行拟合。各病例现状应结合相同尺度三视图和截面人工判断。固定Body条件下的Jacobian满秩也不能证明共享Body—偏差联合问题没有规范自由度。

所有原始TRUSTED面片保留，未按跨来源支持删除独特侧面，原生文件未改。累计来源面积不是解剖去重表面积。Body背面、底盖和基底高度仍含推断，完整Mesh能给模型Dxy/面积/条件体积，但不是实测真值。

## 算法实现与验证

- 复用018官方PyTorch3D渲染、Ring-Aware、首层插值、Edge/Laplacian/Normal、FreeVertices、GeometryGuard及016接触协同方向；017/MAX提供TRUSTED标签与新原生来源。
- 保留018原FIT全图轮廓；所有75来源共同提供原生射线/可信几何，**不是75个新全图轮廓项**。方向/上游RGB SHA相关性权重固定，未把所有来源当成独立证据。
- TRF soft-L1只估计b/a/c，固定对应，数据Jacobian秩/条件数门禁、累计与单轮轴向边界、正则和重新对应检查。无重叠来源保持原生。
- **只有MATCHED参与强深度/点到面梯度。** CONFLICT、UNEXPLAINED、UNKNOWN保留固定代价与分母，暂停强拟合。符合本相机前景、法向、可见性、CAD与局部距离的未命中点，才获得弱PyTorch3D点到三角面梯度，不能吸附全局最近面。
- 完整固定对应目标、固定原生覆盖/对应、独立重算几何代理和GeometryGuard共同决定接受；原有微小Ring穿透不得恶化，但不冒充初始零穿透。
- ARAP只作成熟参考，未声称已实现；未改变拓扑、未自动补洞、未进行正式融合或GT配准。

原定方法与实际代码逐项对照见[METHOD_AND_REUSE_AUDIT.md](METHOD_AND_REUSE_AUDIT.md)，实现位置：`native_multi.py`、`body_multi.py`、`run_multi.py`。模块关闭后018目标/完整参数梯度复核通过。强监督全部暂停时，真实Body参数深度梯度严格为零且分母不变。

'''
 text+=f"真实初始场景共有{len(grad)}个来源得到有限非零的受限未命中几何梯度；这是可微机制验证，不代表该方向必然安全或真实。逆序求和检验见REAL_SOURCE_ORDER_CHECK.json。\n"
 text+='''
合成同面错层从0.35mm降至约0.000794mm；两个独立几何分支通过生产对应函数保留合法后层UNEXPLAINED和独立可见MATCHED。零偏差、原像素射线、点–面有限差分、参数/Adam回退测试通过。预测冻结后额外验证一个闭合、单连通、具有两个分支的通用实体：两个可见分支保持MATCHED，遮挡后层保持UNEXPLAINED，弱约束三参数保持原生；见CONNECTED_BRANCH_CONTROL.json，未反馈真实优化。这是最小模块/几何控制，不证明复杂分支可被完整重建。

## 固定审计表

|审计项目|必须汇报|
|---|---|
|目标组数|4个独立物理组，16个对照状态|
|本算法独立成功|4/4闭环执行、16/16数值状态；实际有效更新数见上表，不等于测量正确|
|本算法失败|数值执行失败0/4；全部回退及未改善区域保留。G03大错层未解决、G06无Body形变；绝对GT精度4/4为NOT_EVALUABLE/NaN|
|历史测量值回退|0；授权018几何作初值，失败只恢复本路线的最后有效状态|
|失败组及具体原因|[FAILURE_LEDGER.md](FAILURE_LEDGER.md)，原始候选/外轮与Mesh证据|
|最终统计样本|全部4组及75个FIT来源，固定N和有效N并列；全部共同病例配对B0–B3，不含融合Mesh监督|
|是否使用GT选择算法|否；配置/源码与预测冻结、原始资产SHA在provenance；无GT读取|

GT中位绝对相对误差、MAE、P95、最大误差均NOT_EVALUABLE，不能用修正后自洽误差替代。HOLDOUT仅在预测冻结后评价；历史祖先可能使用相关视角，所以是本轮更新留出，不是严格端到端独立实验。契约修复前的HOLDOUT曾被评价，但修复来自代码违反任务指令，未按留出表现选参数或方案；全部旧版另行保留。

## 结论与停止

本轮只支持“受限三参数与共享Body闭环已经实现，某些条件下可以改善几何代理”的结论；不能概括为多来源错层已普遍消除，也不能宣称Body测量准确度得到验证。先人工检查G03花瓣、G05层差及各来源修正方向，再决定保留哪些模块。若需放宽覆盖门禁、改变参数边界或拓扑，属于下一轮，当前未执行。

核心图：[B0–B3](figures/Fig1_Four_Group_B0_B3.png)、[HERO校正](figures/Fig2_HERO_Ray_Correction.png)、[对应/位移/截面](figures/Fig3_Correspondences_Displacement_Sections.png)、[覆盖与体积](figures/Fig4_Round_Coverage_Displacement_Volume.png)。[RESULT_INDEX.md](RESULT_INDEX.md)提供本地GLB、Mesh和恢复路径。本轮完成后停止，等待人工审核。
'''
 (R/'TECHNICAL_REPORT_SUMMARY.md').write_text(text)
 report=text+'\n## 全部路线原始指标\n\n|组|方案|固定N|命中N|修正后MAE mm|原生MAE mm|FIT IoU|HOLDOUT IoU|Ring最小mm|自交对数|\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
 for r in m:report+='|'+ '|'.join([r['group'],r['arm'],str(r['fixed_N']),str(r['hit_N']),f(r['depth_corrected_MAE_mm']),f(r['depth_raw_MAE_mm']),f(r['FIT_IoU']),f(r['HOLDOUT_IoU']),f(r['Ring64_min_mm'],7),str(r['self_intersections'])])+'|\n'
 report+='''
## 计算口径与局限

原生固定分母是原OBS_TRUSTED的全部Pixel ID。偏差/近表面/弱锚点采用预固定最多1024点；首层深度保留全量分母，MATCHED资格决定强梯度，其他固定代价不反向传播。世界单位mm，相机深度为轴向Z，Mesh和native深度各保留原生/归档自己的网格及像素射线，无插值生成假深度。

条件误差仅在首层命中且CAD前方统计；未命中单独报告。固定-N代理为有效误差截至10mm、未命中罚10mm，另记录原018训练固定大代价；这两个量不混为一个loss。Body共同/新增/丢失命中以相同Pixel ID逐个比较。HERO–HERO统计为有序投影查询数，非独立物理点；median/P95在实际合并残差上重算，非平均分位数。0.5mm支持带、后层/前方/未知/CAD分开；后层不自动是错误。

来源面积为各来源真实三角面累计面积，不等于唯一解剖面积。0.25mm单元的固定采样占据数只是空间覆盖代理。未进行第二轮删除，原TRUSTED面片保留率100%。source方向/父RGB SHA仅为相关性代理，不完全解决同帧不同编码或裁剪，不能推导独立统计置信度。

Dxy是冻结背景基底法向下的投影凸包最大Feret。Hmax相对该估计平面，H95为顶点分位数、不是均匀表面分位数；弱基底标条件估计。体积仅在闭合、方向一致、无自交时给条件值，包含推断背面/底盖。真实GT准确度不可评价。模型尺寸不是DXY主线测量。

最终Ring采用64阶三角面内部采样独立审核；运行时保留32阶、双向实体/FCL/非邻接自交、翻面、基底和实际毫米位移保护。初始微小穿透保留，不能说几何完全无碰撞。每轮theta/q/Adam/guard状态整体回退，累计偏差和Body位移有界。固定Body下三参数满秩不等于共享Body—偏差系统绝对可辨识。

截面取预先规定的世界坐标切面，不伪称没有标注的精确头/柄/基底解剖。完整三视图与局部Body视图保留所有可见几何；未通过平滑/删面/相机改变美化。GLB仅移除没有任何面引用的顶点索引，原NPZ完整ID/坐标仍保留，推断底盖单独灰色图层。

## 工程偏差记录

保留初次偏差先验系数/鲁棒尺度修复、固定关联错误冻结XYZ修复、评价ID视频注释修复，以及最后的强监督门控修复。最终R3排除所有未遵守CONFLICT暂停强拟合的旧结果。权重/病例/几何阈值未按性能重新选择；旧版源码和预测在runtime归档。首次小工程pilot未事先完整快照源码，不伪称其哈希证据齐全；正式冻结有完整记录。可视化角色UPDATE_HOLDOUT选择异常单独修复，不影响优化。
'''
 (R/'TECHNICAL_REPORT.md').write_text(report)
 ledger='# Failure ledger — all groups retained\n\n'
 for x in fail:ledger+=f"- {x['group']} {x['arm']} round{x['round']}: {x['reasons']}; candidate hit delta {x['hit_delta']}, matched delta {x['matched_delta']}; full rollback. [{x['evidence']}]({x['evidence']}).\n"
 ledger+='\n## Per-case unsolved issues\n\n'
 for g in CFG['groups']:
  a,b=by[g,'B0'],by[g,'B3'];rr=next(r for r in rows if r['group']==g and r['arm']=='B3');ledger+=f"- {g}: committed Body updates {rr['body_updates']}; nonzero corrected sources {rr['corrected_sources']}; Ring64 minimum {b['Ring64_min_mm']:.7f} mm; raw native MAE delta {b['depth_raw_MAE_mm']-a['depth_raw_MAE_mm']:.6f} mm. Reason logs {rr['outer_rejects']}. See fixed three-direction atlas and all source states.\n"
 ledger+='''
G03 petals/unique branches remain ambiguous where no reliable same-layer overlap exists. Ray-only b/a/c cannot provide arbitrary 6DoF correction; no-overlap sources remain native. Weak anchors help only admitted same-camera foreground-connected geometry; other misses retain no strong gradient. No new topology was attempted.

Inherited Ring penetration, weak actual background bases, correlated sources and unknown backside/caps prevent unconditional physical/measurement claims. No GT accuracy metrics fabricated. A successful source correction can fit an incorrect Body; raw/HOLDOUT measures must remain separate.

Engineering archives: runtime/ENGINEERING_PILOT_BEFORE_UNIT_FIX, ANCHOR_SNAPSHOT_FIX_R1, STRONG_SUPERVISION_GATE_FIX_R2. These are excluded formal results; none deleted. Final R3 first-layer gradients obey MATCHED-only eligibility. Video-label parser correction did not alter a prediction. Initial detail-figure selector expected HOLDOUT instead of UPDATE_HOLDOUT; original plotting exception retained. No hyperparameter search or holdout-based winner selection.
'''
 (R/'FAILURE_LEDGER.md').write_text(ledger)
 index='# Result index\n\nSmall tracked results and large local-only artifacts are distinct. Native assets are SHA referenced, not copied to Git.\n\n'
 for g in CFG['groups']:
  index+=f"## {g}\n\n- Three viewpoints: `figures/{g}_FIXED_THREE_DIRECTIONS.png`; body-only: `{g}_BODY_ONLY_FIXED_VIEWS.png`; real RGB projection: `{g}_REAL_PROJECTIONS.png`; source legend: `{g}_SOURCE_LEGEND.png`.\n- Interactive: `figures/{g}_viewer.html` served over local HTTP.\n"
  for arm in CFG['arms']:index+=f"- {arm} actual final: `{R/'runs'/g/arm/'FINAL.npz'}` and `FINAL_mm.ply`; rounds and full latest optimizer/RNG state beside them.\n"
  p=R/'local_results'/(g+'_LAYERS.glb')
  if p.exists():index+=f"- Local GLB: `{p}`; {p.stat().st_size} bytes; SHA256 `{sha(p)}`. Independent source/Body/cap objects; mm→m root only.\n"
 index+='\nAll source theta and traceable IDs: config/SOURCES.json, metrics/BIAS_PARAMETERS.csv, DERIVED_HERO_INDEX.csv, local_results/derived_HERO/. Derived depths are sparse native Pixel-ID vectors, not a filled image; archive mesh UV and native observation UV are distinct keys. Zero corrections refer to original geometry, not another route. Per-pixel correspondence states and real no-hit gradients in local_results/.\n\nMetrics: COMPARISON, MODEL_MEASUREMENTS, SOURCE_GEOMETRY, PER_VIEW, HERO_PAIR_AGGREGATES, HERO_PAIR_CONSISTENCY, INDEPENDENT_HOLDOUT_HERO, EXECUTION_SUMMARY and OUTER_FAILURES CSVs. GT metrics NOT_EVALUABLE.\n'
 (R/'RESULT_INDEX.md').write_text(index);print('REPORTS',len(m),'states',len(fail),'outer rejections',flush=True)
if __name__=='__main__':main()
