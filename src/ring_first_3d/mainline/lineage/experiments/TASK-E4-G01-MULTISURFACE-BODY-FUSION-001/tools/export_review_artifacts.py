from pathlib import Path
import json,shutil,hashlib,subprocess,csv
import numpy as np
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.synthetic.io import fetch
root=Path.cwd();td=root/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001';run=td/'runs/MULTISURFACE_001';task=load_task(td/'TASK.yaml');state=read_state(run)
assert state['accepted'];assert verify_task(task)['freeze_sha256']==state['freeze_sha256'];check_artifacts(run,state)
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates,mesh_section_faces,point_segment_distance,summary
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
for name in ['TECHNICAL_REPORT.md','RESULT_CARD.md','metrics.json','failures.json','evidence.png']:
 assert not(td/name).exists();shutil.copyfile(run/name,td/name)
shutil.copytree(run/'visualization',td/'visualization');(td/'evidence').mkdir()
for name in ['FREEZE.json','RUN_MANIFEST.json']:shutil.copyfile(run/name,td/'evidence'/('ORIGINAL_'+name))
for folder in sorted((run/'attempts').iterdir()):
 out=td/'evidence/attempts'/folder.name;out.mkdir(parents=True)
 for f in folder.iterdir():
  if f.is_file()and f.suffix in {'.json','.txt','.md','.csv'}:shutil.copyfile(f,out/f.name)
shutil.copyfile('/tmp/multisurface-browser.png',td/'evidence/INTERACTIVE_BROWSER.png');shutil.copyfile('/tmp/multisurface-browser.json',td/'evidence/BROWSER_VERIFICATION.json')
models=json.loads(fetch(run,'G4_evaluate','MODEL_METRICS.json').read_text());reg=json.loads(fetch(run,'G4_evaluate','REGISTRATION_METRICS.json').read_text());pred=json.loads(fetch(run,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text());index=[r for r in json.loads(fetch(run,'G0_views_noise','public/FRAME_INDEX.json').read_text())if r['role']=='FIT'];mb={r['key']:r for r in models['models']};rb={r['key']:r for r in reg['rows']}
GT=dict(np.load(fetch(run,'G0_views_noise','private/GT_SCENE.npz')));bodies={a:dict(np.load(fetch(run,'G1_body',a+'_BODY.npz')))for a in ['E1','E2']};truth={r['id']:np.load(fetch(run,'G0_views_noise','private/'+r['id']+'_truth.npz'))['Ptrue']for r in index};sections=task['fusion']['sections']
def cuts(mesh):return [plane_coordinates(mesh_sections(mesh['V'],mesh['F'],s['axis'],s['offset_mm']),s['axis'])for s in sections]
def lists(a):return [x.round(6).tolist()for x in a]
raw={cond:[dict(np.load(fetch(run,'G0_views_noise','public/conditions/'+cond+'/'+r['id']+'.npz')))for r in index]for cond in task['fusion']['condition_order']};before={c:[lists(cuts(mesh))for mesh in meshes]for c,meshes in raw.items()};gtcuts=cuts(GT)
shared=dict(frames=[dict(id=r['id'],video=r['video'])for r in index],planes=sections,GT=lists(gtcuts),Body={a:lists(cuts(b))for a,b in bodies.items()},before=before,keys=[r['key']for r in pred['rows']])
vis=td/'visualization';(vis/'sections').mkdir();(vis/'sections_shared.js').write_text('window.CUT_SHARED='+json.dumps(shared,separators=(',',':'))+';window.CUT_CASES={};\n')
aggregate=[];frame_fail=[];mainkey='C3__E1__BODY_HIER__tol0.5'
for r in pred['rows']:
 key=r['key'];per=[];after=[]
 for view in index:
  if r['status']=='NUMERIC':
   mesh=dict(np.load(fetch(run,'G3_all_predict',key+'/'+view['id']+'.npz')));per.append(np.linalg.norm(mesh['V']-truth[view['id']],axis=1));after.append(lists(cuts(mesh)))
  else:per.append(np.full(len(truth[view['id']]),np.nan));after.append([[]for _ in sections])
 error=np.concatenate(per);ok=np.isfinite(error);numeric=int(ok.sum());stats=summary(error);aggregate.append(dict(key=key,target_material_vertices=len(error),independent_numeric_vertices=numeric,failed_vertices=int((~ok).sum()),material_MAE_mm=stats['MAE'],material_median_mm=stats['median'],material_P95_mm=stats['p95'],material_max_mm=stats['maximum'],material_correct_within0p2mm=int((error<=.2).sum()),material_correct_fraction=float((error<=.2).mean()),GT_alignment=False))
 for f in rb[key]['frames']:
  if f['material_error_mm']['MAE']is None or f['material_error_mm']['MAE']>.2 or f['material_error_mm']['p95']>.2:frame_fail.append(dict(key=key,id=f['id'],video=f['video'],target_N=f['material_error_mm']['target_N'],MAE_mm=f['material_error_mm']['MAE'],P95_mm=f['material_error_mm']['p95'],coverage=f['material_coverage_within0p2mm'],section_plot='sections_all.html#'+key))
 m=mb[key];fusioncuts=[np.empty((0,2,2))for _ in sections];compcuts=[np.empty((0,2,2))for _ in sections]
 if m['status']=='NUMERIC':
  fm=dict(np.load(fetch(run,'G4_fusion_predict',key+'/FUSED_MODEL.npz')));own=np.load(fetch(run,'G4_fusion_predict',key+'/SURFACE_OWNERSHIP.npz'));fusioncuts=cuts(fm)
  for j,s in enumerate(sections):
   seg,ids=mesh_section_faces(fm['V'],fm['F'],s['axis'],s['offset_mm']);compcuts[j]=plane_coordinates(seg[own['face_completion'][ids]],s['axis'])
 missing=[]
 for g,f in zip(gtcuts,fusioncuts):
  flags=point_segment_distance(g.mean(1),f)>.2 if len(f)else np.ones(len(g),bool);missing.append(g[flags].round(6).tolist())
 payload=dict(key=key,arm=r['arm'],after=after,fused=lists(fusioncuts),completion=lists(compcuts),GT_unmatched=missing,metrics=dict(material=aggregate[-1],model=m),exact_triangle_intersection=True)
 (vis/'sections'/(key+'.js')).write_text('window.CUT_CASES['+json.dumps(key)+']='+json.dumps(payload,separators=(',',':'))+';\n')
(vis/'AGGREGATE_MATERIAL_METRICS.json').write_text(json.dumps(aggregate,indent=2)+'\n');(vis/'FRAME_FAILURE_LEDGER.json').write_text(json.dumps(frame_fail,indent=2)+'\n')
with(vis/'AGGREGATE_MATERIAL_METRICS.csv').open('w',newline='')as stream:
 writer=csv.DictWriter(stream,fieldnames=list(aggregate[0]),lineterminator='\n');writer.writeheader();writer.writerows(aggregate)
# All 52 experiments, including scientific failures, have an actual full-section plot.
page=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>全部实验真实Mesh切面</title><style>body{font:15px system-ui;margin:22px;background:#f5f7fa;color:#152238}canvas{width:100%;max-width:2000px;background:white}select{padding:8px;max-width:95%}pre{white-space:pre-wrap}a{color:#235bb0}</style><h1>全部52个条件/方法/容差：真实三角面切面</h1><p>全部16片源Mesh，黑GT、灰虚线Body、红004、蓝005、紫最终表面、浅紫虚线补全、黄底GT未匹配。四列：配准前→配准后→整体融合→GT评价；两纵向、两横向，固定毫米坐标。</p><select id="case"></select><label><input id="v004" type="checkbox" checked>004全部曲面</label><label><input id="v005" type="checkbox" checked>005全部曲面</label><canvas id="cuts" width="2000" height="2100"></canvas><pre id="details"></pre><p><a href="index.html">首页/第一张主图</a> · <a href="AGGREGATE_MATERIAL_METRICS.csv">全顶点材料误差</a> · <a href="FRAME_FAILURE_LEDGER.json">逐帧失败</a> · <a href="MODEL_METRICS.json">固定分母整体评价</a></p><script src="sections_shared.js"></script><script>const S=CUT_SHARED,sel=document.querySelector('#case'),can=document.querySelector('#cuts'),ctx=can.getContext('2d');S.keys.forEach(k=>sel.add(new Option(k,k)));const initial=decodeURIComponent(location.hash.slice(1));sel.value=S.keys.includes(initial)?initial:'C3__E1__BODY_HIER__tol0.5';
function draw(){const key=sel.value,p=CUT_CASES[key];if(!p){const s=document.createElement('script');s.src='sections/'+key+'.js';s.onload=draw;s.onerror=()=>document.querySelector('#details').textContent='MISSING '+key;document.head.append(s);return}location.hash=key;ctx.clearRect(0,0,2000,2100);const cond=key.split('__')[0],arm=p.arm,titles=['配准前','配准后','整体融合','独立GT评价'];
for(let row=0;row<4;row++)for(let col=0;col<4;col++){let x=col*500+48,y=row*510+58,w=430,h=430;const spec=S.planes[row],xmin=-12,xmax=12,ymin=spec.axis===2?-12:-18,ymax=spec.axis===2?12:8,scale=Math.min(w/(xmax-xmin),h/(ymax-ymin));const P=a=>[x+(a[0]-xmin)*scale,y+h-(a[1]-ymin)*scale];
ctx.fillStyle='#172334';ctx.font='16px system-ui';ctx.fillText(titles[col],x,y-30);ctx.font='13px system-ui';ctx.fillText('XYZ'[spec.axis]+'='+spec.offset_mm+' mm | actual triangle cuts',x,y-9);ctx.strokeStyle='#d8dce2';ctx.lineWidth=.5;ctx.setLineDash([]);for(let t=-15;t<=10;t+=5){if(t>=xmin&&t<=xmax){let a=P([t,ymin]),b=P([t,ymax]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.fillText(t,a[0]-7,a[1]+18)}if(t>=ymin&&t<=ymax){let a=P([xmin,t]),b=P([xmax,t]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.fillText(t,a[0]-28,a[1]+4)}}
function trace(segments,color,width=1,alpha=1,dash=[]){ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();ctx.strokeStyle=color;ctx.globalAlpha=alpha;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.beginPath();segments.forEach(s=>{let a=P(s[0]),b=P(s[1]);ctx.moveTo(...a);ctx.lineTo(...b)});ctx.stroke();ctx.restore()}
trace(S.Body[arm][row],'#888',1.4,1,[4,3]);S.frames.forEach((f,i)=>{if(!document.querySelector('#v'+f.video).checked)return;trace((col===0?S.before[cond]:p.after)[i][row],f.video==='004'?'#d22a3d':'#226cce',.9,.55)});if(col>=2){trace(p.fused[row],'#8d25ad',2);trace(p.completion[row],'#d881e8',2.5,.9,[4,3])}if(col===3)trace(p.GT_unmatched[row],'#e7ba31',6,.65);trace(S.GT[row],'black',1.7);ctx.fillStyle='#172334';let axes=[0,1,2].filter(v=>v!==spec.axis);ctx.fillText('XYZ'[axes[0]]+' [mm]',x+w/2,y+h+38);ctx.fillText('XYZ'[axes[1]]+' [mm]',x-40,y+15)}document.querySelector('#details').textContent=key+'\nExact original-triangle intersections; no point/mean-contour approximation. 16 complete independent surfaces retained.\n'+JSON.stringify(p.metrics,null,2);}
sel.onchange=draw;document.querySelector('#v004').onchange=draw;document.querySelector('#v005').onchange=draw;draw();</script></html>'''
(vis/'sections_all.html').write_text(page)
# Extend, do not replace or prettify, the already frozen negative-result ledger.
ledger=json.loads((vis/'FAILURE_LEDGER.json').read_text());ledger['per_frame_failures']=frame_fail;ledger['fixed_target_material_vertices_per_case']=sum(len(p)for p in truth.values());ledger['all_case_cut_plot']='sections_all.html#<record-key>';(vis/'FAILURE_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')
# Quantitative matched-numeric comparisons with fixed six-condition denominator.
pairs=[];ab={r['key']:r for r in aggregate}
for arm in ['E1','E2']:
 for first,second in [('M0','BODY_VIDEO'),('M0','BODY_HIER'),('ICP','BODY_HIER'),('BODY_VIDEO','BODY_HIER')]:
  keys=[(f'{c}__{arm}__{first}__tol0.5',f'{c}__{arm}__{second}__tol0.5')for c in task['fusion']['condition_order']];good=[(a,b)for a,b in keys if ab[a]['material_MAE_mm']is not None and ab[b]['material_MAE_mm']is not None]
  delta=np.array([ab[b]['material_MAE_mm']-ab[a]['material_MAE_mm']for a,b in good]);pairs.append(dict(arm=arm,first=first,second=second,target_conditions=6,common_numeric_conditions=len(good),mean_material_MAE_difference_second_minus_first_mm=float(delta.mean()),per_condition=[dict(first=a,second=b,delta_mm=ab[b]['material_MAE_mm']-ab[a]['material_MAE_mm'])for a,b in good],history_fusion=False))
(vis/'PAIRED_COMPARISONS.json').write_text(json.dumps(pairs,indent=2)+'\n')
# No GT-based retuning: the preregistered main remains C3/E1/HIER/0.5 despite negative material errors.
main=mb[mainkey];material=ab[mainkey];base=next(b for b in models['body_only']if b['arm']=='E1'and b['model']=='BODY_ONLY_MATCHED_CHART');raw_main=mb['C3__E1__M0__tol0.5'];generation=json.loads(fetch(run,'G0_views_noise','GENERATION_AUDIT.json').read_text());summary_result=dict(execution='ALL_G0_G4_COMPLETED',scientific_conclusion='Owned fusion improves Body-only average errors, but Body-mediated localization is not established: C0 bias and low-noise material degradation remain',main_key=mainkey,main_material=material,main_model=main,matched_Body_only=base,uncorrected_fusion=raw_main,tests=104,stages=13,independent_views=16,total_material_vertices=sum(len(p)for p in truth.values()),total_independent_triangles=sum(m['triangles']for m in generation['mesh_audit']),DXY_new_calls=0,GT_optimal_alignment=False,implementation_commit=commit)
(td/'SCIENTIFIC_RESULT.json').write_text(json.dumps(summary_result,indent=2)+'\n')
report=(td/'TECHNICAL_REPORT.md').read_text();anchor='主图为预先固定C3/E1/BODY_HIER';where=report.index(anchor)
intro=f'''**实测结论：执行完成，尚不能证明二维主体中介可靠恢复空间定位。**104项回归与13阶段执行/产物检查通过，48主组合+4容差消融全部产生真实模型。E1主组合融合6/6改善Body-only平均误差，但不修正也6/6改善，不能将这项改善全部归功于配准。

预注册C3/E1：匹配细分Body-only双向MAE {base['bidirectional_mm']['MAE']:.6f}mm →分层定位后融合{main['bidirectional_mm']['MAE']:.6f}mm；不修正直接融合更低，为{raw_main['bidirectional_mm']['MAE']:.6f}mm。完整材料顶点加权MAE为{material['material_MAE_mm']:.6f}mm；逐视角等权MAE由不修正0.460332升至分层0.514474mm。C0本来无误差，E1 Body方法却引入约0.376231mm逐视角MAE，提示模型/中介偏差，原因尚未隔离。

高方差C4/E1中，分层方法逐视角MAE约0.582827mm，低于仅视频级0.806058mm和不修正0.658540mm，说明小残余修正有部分作用，仍不等于正确定位。主纵向切面保留细柄缺失、黄色GT未匹配和Body补全区域；未用GT修补或改选容差。

实现提交：`{commit}`；Runner冻结指纹：`{state['freeze_sha256']}`。本轮运行耗时{state['spent_seconds']:.3f}s，未执行新DXY/HERO训练或相机优化。全部16视角具有不同RGB内容哈希，68,230材料顶点、127,691独立深度网格三角面；GT观察/未观察固定目标分别6132/5868，总分母12000。

[全部52组合真实切面（含失败与容差）](visualization/sections_all.html) · [全部材料顶点加权误差](visualization/AGGREGATE_MATERIAL_METRICS.csv) · [逐帧失败台账](visualization/FRAME_FAILURE_LEDGER.json) · [同数值条件配对](visualization/PAIRED_COMPARISONS.json)

以下补充只读导出已冻结几何与评价，不新增优化或修改原始Runner快照。所有材料目标保留；无GT最佳刚体对齐；Body-only匹配细分基线避免伪改进。单一固定种子、有限轨迹与radial-chart非星形限制意味着不能声称一般化成功。

'''
report=report[:where]+intro+report[where:];report+='\n## 全部结果的逐项真实切面\n\n每个条件/Body/方法/容差都有完整四列、四截面图，点击可检查全部原始线段，未用采样点/平均轮廓替代：\n\n'
for r in pred['rows']:report+=f"- [{r['key']}](visualization/sections_all.html#{r['key']})\n"
(td/'TECHNICAL_REPORT.md').write_text(report)
(td/'RESULT_CARD.md').write_text(f'''# TASK-E4-G01-MULTISURFACE-BODY-FUSION-001

104项测试、13阶段执行/产物门禁通过；科学结论未认定为可靠定位成功。

- 16独立深度栅格曲面，68,230材料顶点、127,691三角面；未使用GT面并集冒充观测。
- 6条件×2 Body×4方法+4消融，52模型；相机/Body冻结，DXY新调用0。
- C3/E1整体双向MAE：Body-only 0.323293→分层后融合0.303003mm；不修正融合0.201619mm更低。
- C3/E1逐视角材料MAE：不修正0.460332→分层0.514474mm；C0引入0.376231mm偏差。保留负结果。
- 高方差C4残余修正有部分改善，不能抵消低方差偏差或证明普遍恢复。

[第一张主图：真实切面](visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png) · [52组合真实切面](visualization/sections_all.html) · [完整逐视角3D](visualization/multisurface_3d.html) · [技术报告](TECHNICAL_REPORT.md) · [指标](visualization/ALL_CONDITION_METRICS.csv) · [失败台账](visualization/FAILURE_LEDGER.json) · [RUN_MANIFEST](RUN_MANIFEST.json)

实现提交：`{commit}`。GT只生成/独立后验评价，最终预测未做GT最佳刚体对齐。历史测量回退0。
''')
page=(vis/'index.html').read_text();note='<p style="padding:16px;background:#fff0d1"><b>科学结论仍有负结果：</b>融合改善Body-only平均误差并不证明定位正确；C0有Body偏差，C3分层材料误差未优于不修正。主图保留未匹配与细柄缺失。</p><p><a href="sections_all.html">全部52组合真实四列切面</a> · <a href="AGGREGATE_MATERIAL_METRICS.csv">全顶点加权指标</a> · <a href="FRAME_FAILURE_LEDGER.json">逐帧失败</a> · <a href="PAIRED_COMPARISONS.json">配对比较</a></p>'
page=page.replace('<p><a href="multisurface_3d.html">',note+'<p><a href="multisurface_3d.html">',1);(vis/'index.html').write_text(page)
# Existing Failure Registry schema: new scientific facts remain unreviewed candidates.
entries=[]
def entry(id,symptom,cause,paths):
 entries.append(dict(id=id,category='scientific_negative',modules=['MF02','MF03','MF04'],symptom=symptom,cause=cause,cause_status='observed_only',repair='Retain all fixed-denominator measurements and actual Mesh cuts for review. No GT-driven refit, method fallback or permanent rule promotion.',regression=['test_multisurface: tolerance, fixed denominators, ownership and exact triangle sections'],evidence=[dict(path=str((td/p).relative_to(root)),sha256=sha(td/p))for p in paths],rule_status='candidate',review=dict(status='unreviewed',reviewer=None,evidence=None)))
entry('FM-MULTISURFACE-C0-001','Body-mediated localization introduces nonzero material displacement on error-free C0','Coarse Body/mapping bias is observed; exact causal contribution is not isolated',['visualization/REGISTRATION_METRICS.json','visualization/AGGREGATE_MATERIAL_METRICS.json'])
entry('FM-MULTISURFACE-OWNERSHIP-001','Fusion reduces Body-only mean error yet leaves observed/unobserved stem and section gaps','Consensus rejection, visibility and star-chart restrictions may discard or fail to represent parts; no GT-based patching',['visualization/MODEL_METRICS.json','visualization/SURFACE_OWNERSHIP_MAIN.csv','visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png'])
entry('FM-MULTISURFACE-VARIANCE-001','Frame residual improves high-variance localization over video-only but not consistently over uncorrected low-noise input','Variance priors help some conditions while a biased Body correspondence remains; not a general accuracy certificate',['visualization/PAIRED_COMPARISONS.json','visualization/FRAME_FAILURE_LEDGER.json'])
(td/'FAILURE_REGISTRY.json').write_text(json.dumps(dict(schema=1,policy='Task-local candidate facts only, no automatic rule promotion',failures=entries),indent=2)+'\n')
(td/'README.md').write_text('''# 使用

先打开visualization/index.html，第一张主图为全部真实Mesh切面；sections_all.html含52组合及失败的四列切面；multisurface_3d.html可逐视频/逐视角显示完整三角面。SVG/Canvas线段来自实际三角面求交，没有平均轮廓。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/TASK.yaml --run-dir experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/runs/MULTISURFACE_001
```

check校验固定输入/源码；run --stage指定阶段，前置门禁不可跳过；accept只验收执行与产物，科学结论等待人工。Body初始几何为用户授权的已核验GT-free E1/E2复用，DXY未改也未重跑。原始每片RGB/Mask/轴向深度、独立Mesh、所有未融合Mesh、完整Ownership候选保留在本地runs；Git保存冻结配置、代码、小表、精选PNG和可离线查看全部完整曲面的JS/HTML。
''')
manifest=dict(schema='multisurface-delivery-1',task_id=task['task_id'],execution_status='ALL_G0_G4_COMPLETED',runner_accepted=True,scientific_acceptance='AWAITING_HUMAN_REVIEW',scientific_result=summary_result['scientific_conclusion'],implementation_commit=commit,task_sha256=sha(td/'TASK.yaml'),runner_freeze_sha256=state['freeze_sha256'],local_original_run=str(run),stages={s:'PASS'for s in task['authorization']['stages']},tests=dict(total=104,failures=0,errors=0),independent_views=16,independent_vertices=68230,independent_triangles=127691,main_figure='visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png',DXY_new_calls=0,GT_optimal_rigid_alignment=False,read_only_supplement='All-case exact sections and aggregate statistics exported from frozen Mesh predictions, no new fit or parameter selection',spent_seconds=state['spent_seconds'],budget=task['budget'])
files=[p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json'];manifest['artifacts']={str(p.relative_to(td)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(files)};(td/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PACKAGED',len(files),'files; all-case exact section plots',len(pred['rows']),'bytes',sum(x['bytes']for x in manifest['artifacts'].values()))
