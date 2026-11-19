"""Exact original-triangle sections, inherited full Mesh viewer and honest reports."""
import csv,html,json,shutil
from pathlib import Path
import numpy as np
from ..synthetic.io import fetch,save_json,outputs
from ..multisurface.geometry import mesh_sections,mesh_section_faces,plane_coordinates,point_segment_distance
from ..multisurface.visualize import viewer,plain_mesh
from ..policy.contracts import ROOT

def cuts(mesh,sections):return [plane_coordinates(mesh_sections(mesh['V'],mesh['F'],s['axis'],s['offset_mm']),s['axis'])for s in sections]
def lists(a):return [x.round(6).tolist()for x in a]
def plot(attempt,name,sections,stages,body,GT,frames,fused,completion,ranges,title):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.collections import LineCollection
 fig,axes=plt.subplots(4,4,figsize=(18,18),layout='constrained');bc=cuts(body,sections);gc=cuts(GT,sections)if GT is not None else [np.empty((0,2,2))for _ in sections];fc=cuts(fused,sections)if fused else[np.empty((0,2,2))for _ in sections]
 cache=[[cuts(m,sections)for m in meshes]for meshes in stages]
 for r,s in enumerate(sections):
  axis=s['axis'];others=[i for i in range(3)if i!=axis]
  for col in range(4):
   ax=axes[r,col]
   def add(seg,color,width=1.,alpha=1.,dash=False):
    if len(seg):ax.add_collection(LineCollection(seg,colors=color,linewidths=width,alpha=alpha,linestyles='dashed'if dash else'solid'))
   add(bc[r],'#888',1.1,.9,True)
   for i,cc in enumerate(cache[col]):add(cc[r],'#d82439'if frames[i]['video']=='004'else'#2266ce',.65,.6)
   if col==3:
    add(fc[r],'#8f25ad',1.7)
    if fused and completion is not None:
     seg,ids=mesh_section_faces(fused['V'],fused['F'],axis,s['offset_mm']);add(plane_coordinates(seg[completion[ids]],axis),'#db81eb',2.,.9,True)
    if len(gc[r]):
     missing=point_segment_distance(gc[r].mean(1),fc[r])>.2 if len(fc[r])else np.ones(len(gc[r]),bool);add(gc[r][missing],'#e3b72b',5.,.6)
   add(gc[r],'black',1.4);ax.set(xlim=ranges[others[0]],ylim=ranges[others[1]],xlabel='XYZ'[others[0]]+' [mm]',ylabel='XYZ'[others[1]]+' [mm]');ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_title(['Original dispersion','Body video coarse location','Hierarchical / selected method','Owned unified surface'][col]if r==0 else'',fontsize=9);ax.text(.02,.98,f'{"XYZ"[axis]}={s["offset_mm"]:g} mm | all actual triangles\nlocal segments {sum(len(cc[r])for cc in cache[col])}',transform=ax.transAxes,va='top',fontsize=7)
 fig.suptitle(title+'\nBlack GT (simulation only), dashed gray Body, all 004 red / 005 blue, purple fused; pale dash Body completion; yellow unmatched GT >0.2mm. No sampled/mean contours.',fontsize=9);fig.savefig(attempt/'figures'/name,dpi=100);plt.close(fig)

def export_cuts(folder,sections,frames,body,GT,raw,records,coarse,models,completion,ranges,metrics,main):
 folder.mkdir(exist_ok=True);(folder/'sections').mkdir();gc=cuts(GT,sections)if GT is not None else[np.empty((0,2,2))for _ in sections]
 shared=dict(frames=frames,planes=sections,GT=lists(gc),Body={a:lists(cuts(b,sections))for a,b in body.items()},before={c:[lists(cuts(m,sections))for m in meshes]for c,meshes in raw.items()},keys=list(records),ranges=ranges)
 (folder/'sections_shared.js').write_text('window.CUT_SHARED='+json.dumps(shared,separators=(',',':'))+';window.CUT_CASES={};\n')
 for key,row in records.items():
  cc=coarse[row['condition'],row['arm']];m=models.get(key);fc=cuts(m,sections)if m is not None else[np.empty((0,2,2))for _ in sections];comp=[];missing=[]
  for i,s in enumerate(sections):
   if m is not None:
    seg,ids=mesh_section_faces(m['V'],m['F'],s['axis'],s['offset_mm']);comp.append(plane_coordinates(seg[completion[key][ids]],s['axis']))
   else:comp.append(np.empty((0,2,2)))
   flags=point_segment_distance(gc[i].mean(1),fc[i])>.2 if len(fc[i])and len(gc[i])else np.ones(len(gc[i]),bool);missing.append(gc[i][flags])
  payload=dict(key=key,arm=row['arm'],after=[lists(cuts(m,sections))for m in row['meshes']],coarse=[lists(cuts(m,sections))for m in cc],fused=lists(fc),completion=lists(comp),GT_unmatched=lists(missing),metrics=metrics[key],exact_triangle_intersection=True)
  (folder/'sections'/(key+'.js')).write_text('window.CUT_CASES['+json.dumps(key)+']='+json.dumps(payload,separators=(',',':'))+';\n')
 old=ROOT/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/visualization/sections_all.html';page=old.read_text();page=page.replace('全部52个条件/方法/容差','全部'+str(len(records))+'个冻结结果').replace('全部16片源Mesh','全部'+str(len(frames))+'片源Mesh').replace('16 complete independent surfaces',str(len(frames))+' complete independent surfaces').replace('C3__E1__BODY_HIER__tol0.5',main).replace("titles=['配准前','配准后','整体融合','独立GT评价']","titles=['原始分散','Body视频级粗定位','分层/所选方法','最终统一主面']").replace('(col===0?S.before[cond]:p.after)','(col===0?S.before[cond]:col===1?p.coarse:p.after)').replace('if(col>=2)','if(col===3)').replace("xmin=-12,xmax=12,ymin=spec.axis===2?-12:-18,ymax=spec.axis===2?12:8", "rangeAxes=S.ranges.filter((v,i)=>i!==spec.axis),xmin=rangeAxes[0][0],xmax=rangeAxes[0][1],ymin=rangeAxes[1][0],ymax=rangeAxes[1][1]")
 page=page.replace('四列：配准前→配准后→整体融合→GT评价','四列：原始分散→Body视频级粗定位→分层/所选方法→最终统一主面').replace('四列：','四列：').replace('<p><a href="index.html">首页/第一张主图</a>', '<p><a href="index.html">首页/第一张主图</a>')
 # These supplemental files have the same names in simulation and real subfolders.
 page=page.replace('AGGREGATE_MATERIAL_METRICS.csv','METRICS.json').replace('FRAME_FAILURE_LEDGER.json','FAILURE_LEDGER.json').replace('MODEL_METRICS.json','METRICS.json')
 (folder/'sections_all.html').write_text(page)

def adjusted_viewer(folder,shared,packets,initial,real=False,extent=25.):
 viewer(folder,shared,packets);p=folder/'multisurface_3d.html';s=p.read_text();s=s.replace('cases/C3_E1.js','cases/'+initial+'.js').replace("cs.value='C3'","cs.value="+json.dumps(initial.split('_')[0])).replace('/16\\n','/'+str(len(shared['frames']))+'\\n').replace('16独立深度栅格曲面',str(len(shared['frames']))+'独立完整曲面')
 s=s.replace('<option>0</option>','').replace('<option>1</option>','')
 if real:
  s=s.replace('<option>'+('E2'if initial.endswith('E1')else'E1')+'</option>','').replace('GT切面审阅','真实来源几何审阅').replace('G01_LIKE_SIMULATION / INDEPENDENT_DEPTH_GRID_SYNTHETIC_HERO_PROXY。','REAL_HERO_PILOT / 无独立GT，不能解释为绝对精度。').replace('type="checkbox" checked>GT黑色网格线','type="checkbox">GT不可获得').replace('黑GT','无GT').replace('GT评价','几何证据')
  scale=1/extent;s=s.replace('p.x*0.04','p.x*'+str(scale)).replace('p.y*0.0631579','p.y*'+str(scale*1200/760)).replace('x2="270"','x2="'+str(30+6000*scale)+'"')
 else:s=s.replace('<option selected>BODY_HIER</option>','<option selected>BODY_HIER</option><option>BODY_HIER_CTF</option>')
 (folder/'multisurface_3d.html').write_text(s)

def run(task,attempt):
 root=attempt.parents[1];cfg=task['fusion'];sections=cfg['sections'];frames=[f for f in json.loads(fetch(root,'G0_views_noise','public/FRAME_INDEX.json').read_text())if f['role']=='FIT'];pred=json.loads(fetch(root,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text())['rows'];stress=json.loads(fetch(root,'G4_evaluate','STRESS_METRICS.json').read_text());met={r['key']:r for r in stress['rows']};models_data=json.loads(fetch(root,'G4_evaluate','MODEL_METRICS.json').read_text());ledger=json.loads(fetch(root,'G4_evaluate','FAILURE_LEDGER.json').read_text());GT=dict(np.load(fetch(root,'G0_views_noise','private/GT_SCENE.npz')));ring=dict(np.load(fetch(root,'G0_views_noise','public/FIXED_RING.npz')));bodies={a:dict(np.load(fetch(root,'G1_body',a+'_BODY.npz')))for a in cfg['body_arms']};raw={c:[dict(np.load(fetch(root,'G0_views_noise','public/conditions/'+c+'/'+f['id']+'.npz')))for f in frames]for c in cfg['condition_order']};records={};models={};completion={};coarse={};packets={}
 (attempt/'figures').mkdir()
 for c in cfg['condition_order']:
  poses={f['id']:f['estimated_C']for f in json.loads(fetch(root,'G0_views_noise','public/conditions/'+c+'/ESTIMATED_POSES.json').read_text())}
  for arm in cfg['body_arms']:packets[c+'_'+arm]=dict(poses=poses,results={})
 for r in pred:
  key=r['key'];meshes=[dict(np.load(fetch(root,'G3_all_predict',key+'/'+f['id']+'.npz')))for f in frames]if r['status']=='NUMERIC'else[];records[key]=dict(condition=r['condition'],arm=r['arm'],meshes=meshes)
  if r['method']=='BODY_VIDEO':coarse[r['condition'],r['arm']]=meshes
  try:
   models[key]=dict(np.load(fetch(root,'G4_fusion_predict',key+'/FUSED_MODEL.npz')));completion[key]=np.load(fetch(root,'G4_fusion_predict',key+'/SURFACE_OWNERSHIP.npz'))['face_completion']
  except KeyError:pass
  packets[r['condition']+'_'+r['arm']]['results'][r['method']+'|0.5']=dict(corrections=r.get('surface_corrections'),fused=plain_mesh(models[key])if key in models else None,summary=met[key])
 shared=dict(frames=frames,conditions=cfg['condition_order'],bodies={a:plain_mesh(b)for a,b in bodies.items()},GT=plain_mesh(GT),ring=plain_mesh(ring),meshes={f['id']:plain_mesh(np.load(fetch(root,'G0_views_noise','public/camera_meshes/'+f['id']+'.npz')))for f in frames})
 adjusted_viewer(attempt,shared,packets,'C7_E1');ranges=[[-14,14],[-14,14],[-22,12]];main='C7__E1__BODY_HIER__tol0.5';export_cuts(attempt,sections,frames,bodies,GT,raw,records,coarse,models,completion,ranges,met,main)
 for c in cfg['condition_order']:
  key=c+'__E1__BODY_HIER__tol0.5';filename='01_MAIN_STRESS_SECTIONS.png'if c=='C7'else c+'_SECTIONS.png';plot(attempt,filename,sections,[raw[c],coarse[c,'E1'],records[key]['meshes'],records[key]['meshes']],bodies['E1'],GT,frames,models.get(key),completion.get(key),ranges,c+' / E1 / original thresholds | '+str(cfg['conditions'][c]))
 for name in ['STRESS_METRICS.json','STRESS_METRICS.csv','MODEL_METRICS.json','REGISTRATION_METRICS.json','NOISE_AUDIT.json','FAILURE_LEDGER.json']:shutil.copyfile(fetch(root,'G4_evaluate',name),attempt/name)
 save_json(attempt/'METRICS.json',stress);realmetrics=json.loads(fetch(root,'real_evaluate','REAL_METRICS.json').read_text());realpred=json.loads(fetch(root,'real_predict','REAL_PREDICTIONS_FROZEN.json').read_text());audit=json.loads(fetch(root,'G0_real_audit','REAL_AUDIT.json').read_text());save_json(attempt/'REAL_METRICS.json',realmetrics);save_json(attempt/'REAL_AUDIT.json',audit);save_json(attempt/'CTF_ELIGIBILITY.json',json.loads(fetch(root,'G3_all_predict','CTF_ELIGIBILITY.json').read_text()));figlinks=[]
 from .real import manifest,load_view
 sourceby={g['group']:g for g in manifest(task)['groups']}
 for group in realpred['groups']:
  g=group['group'];folder=attempt/g;folder.mkdir();save_json(folder/'METRICS.json',dict(rows=[r for r in realmetrics['rows']if r['group']==g]));save_json(folder/'FAILURE_LEDGER.json',dict(group=g,absolute_accuracy='NOT_EVALUABLE',scientific_negatives=[r for r in realmetrics['rows']if r['group']==g]));
  if group['status']!='NUMERIC':(folder/'index.html').write_text('<h1>'+g+' NOT_EVALUABLE</h1><pre>'+html.escape(json.dumps(group,indent=2))+'</pre>');continue
  source=sourceby[g];data=[load_view(r,[.3,.1])for r in source['views']if r['role']=='FIT'];fr=[dict(id=d['id'],video=d['video'])for d in data];body=dict(np.load(fetch(root,'real_predict',g+'/'+group['primary_body']+'_BODY.npz')));rg=dict(np.load(source['assets']['ring']['path']));records_real={};models_real={};completion_real={};realpacket={};rm={};coarse_real=[]
  for r in group['records']:
   key='REAL__'+group['primary_body']+'__'+r['method']+'__tol0.5';mm=[dict(np.load(fetch(root,'real_predict',g+'/'+r['method']+'/'+d['id']+'.npz')))for d in data]if r['status']=='NUMERIC'else[];records_real[key]=dict(condition='REAL',arm=group['primary_body'],meshes=mm);rm[key]=next(m for m in realmetrics['rows']if m['group']==g and m.get('method')==r['method'])
   if r['status']=='NUMERIC':models_real[key]=dict(np.load(fetch(root,'real_predict',g+'/'+r['method']+'/FUSED_MODEL.npz')));completion_real[key]=np.load(fetch(root,'real_predict',g+'/'+r['method']+'/SURFACE_OWNERSHIP.npz'))['face_completion']
   realpacket[r['method']+'|0.5']=dict(corrections=r.get('corrections'),fused=plain_mesh(models_real[key])if key in models_real else None,summary=rm[key])
   if r['method']=='BODY_VIDEO':coarse_real=mm
  allV=np.concatenate([d['V']for d in data]+[b['V']for r in records_real.values()for b in r['meshes']]+[b['V']for b in models_real.values()]+[body['V']]);extent=float(np.max(abs(allV)))+2;rr=[[-extent,extent]]*3;mainr='REAL__'+group['primary_body']+'__BODY_HIER__tol0.5';base=[dict(V=d['V'],F=d['F'])for d in data];export_cuts(folder,sections,fr,{group['primary_body']:body},None,{'REAL':base},records_real,{('REAL',group['primary_body']):coarse_real},models_real,completion_real,rr,rm,mainr)
  sharedreal=dict(frames=fr,conditions=['REAL'],bodies={group['primary_body']:plain_mesh(body)},GT=dict(V=[],F=[]),ring=plain_mesh(rg),meshes={d['id']:plain_mesh(d)for d in data});adjusted_viewer(folder,sharedreal,{'REAL_'+group['primary_body']:dict(poses={d['id']:np.eye(4).tolist()for d in data},results=realpacket)},'REAL_'+group['primary_body'],True,extent*1.1)
  filename=g+'_REAL_SECTIONS.png';plot(attempt,filename,sections,[base,coarse_real,records_real[mainr]['meshes'],records_real[mainr]['meshes']],body,None,fr,models_real.get(mainr),completion_real.get(mainr),rr,g+' REAL_HERO_PILOT | no independent GT | Body primary '+group['primary_body']);figlinks.append((filename,g));(folder/'index.html').write_text('<h1>'+g+' Real HERO: no independent GT</h1><p>Actual fresh FIT-only initializer '+group['primary_body']+'. Geometry is not replaced.</p><a href="sections_all.html">全部方法真实切面</a> · <a href="multisurface_3d.html">完整Mesh交互</a> · <a href="METRICS.json">留出视角/一致性/异常指标</a> · <a href="../index.html">首页</a>')
 report=f"# {task['task_id']}\n\n![主图：高方差独立多曲面与Body/GT真实切面](visualization/figures/01_MAIN_STRESS_SECTIONS.png)\n\n继承 `{task['stress']['baseline_commit']}` 的冻结科学模块，未修改配准器、融合器或既有独立GT评价器。主图预注册C7/E1/原阈值BODY_HIER：原始分散→Body视频级粗定位→分层配准→统一主面；两纵向两横向，全部实际三角面求交，固定毫米坐标。\n\n"
 report+='## 实测条件与结论\n\nC0无误差，C4原0.7°/0.20mm，C6为1.2°/0.35mm，C7为2°/0.60mm；后3者沿用004=A、005=B系统偏差、种子20261117和Bias@TruePose@FrameNoise。GT仅生成和预测冻结后独立评价，无GT最优对齐。E1/E2为原冻结初始化；所有局部曲面保留，Body容差仍0.5mm。\n\n| Condition / E1 method | Material MAE / P95 mm | Within / cross dispersion MAE mm | GT bidir MAE mm | Observed GT coverage |\n| --- | --- | --- | --- | --- |\n'
 fmt=lambda x:'NaN'if x is None else f'{x:.6f}'
 for r in stress['rows']:
  if r['arm']=='E1':report+=f"| {r['condition']} / {r['method']} | {fmt(r['material'].get('MAE'))} / {fmt(r['material'].get('p95'))} | {fmt((r['within_video']or{}).get('MAE'))} / {fmt((r['cross_video']or{}).get('MAE'))} | {fmt((r['GT_bidirectional_mm']or{}).get('MAE'))} | {fmt(r['observed_GT_coverage'])} |\n"
 report+='\n必须区分分散下降与位置正确。自动逐组合标记“固定重叠分散降低超过20%但GT材料误差上升”，包括未通过/非收敛模型；C0漂移是独立负证据，不因高方差改善而删除。全部E2、对应率、GT表面P95/最大值、观测/补全覆盖、同样本配对见[STRESS_METRICS](visualization/STRESS_METRICS.json)与[CSV](visualization/STRESS_METRICS.csv)。\n\n'
 report+='### 分散下降但GT误差恶化\n\n'+('```json\n'+json.dumps(stress['contradictions'],indent=2)+'\n```\n'if stress['contradictions']else'本轮冻结20%判据下未检测到该组合；完整连续指标仍保留。\n')
 report+='\n## 捕获范围与独立粗到细消融\n\n先执行原2.5mm候选/1.5mm重叠阈值；C6/C7只有当任一视角候选有效率<25%或总重叠有效率<50%时触发BODY_HIER_CTF。阈值按5/3→3.5/2→2.5/1.5mm，原优化API各执行一次外层，每级对累积后的曲面图表重新匹配；先验在每级重置，属于单独方法，不替换原结果。所有触发仅看预测输入，无GT。见[触发台账](visualization/CTF_ELIGIBILITY.json)。\n\n'
 report+='## 真实迁移实际完成情况与成本\n\n选择旧MAX推理记录每视频前2个原生HERO FIT、下1个HOLDOUT，不按误差挑选。直接读取完整RAW_NATIVE_MESH，核对原深度、原Mask精确原生采样、K/C、全部顶点/面、源像素反投影及正式DXY图像哈希。352px原生候选通过像素中心仿射从360px正式缓存转换；2D初始化仍调用原360px E1/E2 API，用本轮FIT从固定通用初值重拟合9参数；不读取历史3D结果或测量直径。每组E1正式可用则优先，否则显式E2，不按GT切换。\n\n所有真实相机不变；先验0.3°/0.10mm为未校准的明确启发式。原生网格不抽稀、吸附或更换拓扑。先使用同一原优化器、融合器和阈值，无真实CTF调参。真实Mask/Ring边界不认证为物理隐藏轮廓；环接触为unknown。留出Mask与独立HERO深度只提供可获得的证据，HERO深度不是GT；相机历史校准与视频共同坐标未经独立准确性认证。共同可见区域使用配准前投影Mask冻结查询材料顶点，最近表面一致性不是材料点真值。\n\n| Group | Input status | FIT/HOLDOUT | Actual prediction | Runtime seconds |\n| --- | --- | --- | --- | --- |\n'
 for g in realpred['groups']:
  a=next(a for a in audit['groups']if a['group']==g['group']);report+=f"| {g['group']}{' (difficult)'if a['difficult_group']else''} | {a['status']} | {a['FIT']} / {a['HOLDOUT']} | {g['status']} | {fmt(g.get('seconds'))} |\n"
 report+='\n迁移仅增加源身份/原生像素坐标适配和新任务FIT初始化；新DXY调用0，HERO推理/训练0，配准优化算法改动0。上表实际CPU耗时包含输入、初始化、四方法及融合；逐方法耗时和异常/留出指标见[真实指标](visualization/REAL_METRICS.json)，[逐视角输入审计](visualization/REAL_AUDIT.json)。留出目标若出现在FIT HERO支持图中会在审计单列，不宣称该视角严格独立。绝对三维精度对3/3真实组均为NOT_EVALUABLE。\n\n'
 report+='## 固定审计表\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | 仿真1场景×4条件×2 Body×4主方法=32主组合；CTF按冻结触发单列。真实目标G01/G03/G05共3组 |\n| 本算法独立成功 | 数值输出与准确性分开；各组合完整材料顶点、各组实际FIT视角及留出分母固定 |\n| 本算法失败 | 代码/输入失败保留NaN或NOT_EVALUABLE；科学负结果及C0漂移全部保留 |\n| 历史测量值回退 | 0；仅复用授权仿真初始Body、原HERO网络观测与已绑定二维候选缓存 |\n| 失败组及具体原因 | 每组合/组链接失败台账、材料点、固定重叠、对应率、留出覆盖、真实切面 |\n| 最终统计样本 | 固定68,230材料点/仿真组合；固定12,000 GT面积样本、12,000模型面积样本；真实全部选定视角，不剔除困难组 |\n| 是否使用GT选择算法 | 否；TASK、全部源/科学源码、阈值、随机种子与消融预冻结，GT只在独立评价阶段读取 |\n\n'
 report+='[全部条件实际切面](visualization/sections_all.html) · [完整曲面交互](visualization/multisurface_3d.html) · [失败台账](visualization/FAILURE_LEDGER.json) · [噪声协方差/注入](visualization/NOISE_AUDIT.json)\n\n'
 for filename,g in figlinks:report+=f'### {g}真实几何证据（无GT）\n\n![{g}全部真实Mesh切面](visualization/figures/{filename})\n\n[{g}完整Mesh与全部方法](visualization/{g}/index.html)\n\n'
 (attempt/'TECHNICAL_REPORT.md').write_text(report);card=f"# {task['task_id']}\n\n执行完成，科学结论等待人工审阅。仿真数值{sum(r['status']=='NUMERIC'for r in stress['rows'])}/{len(stress['rows'])}；真实数值组{sum(g['status']=='NUMERIC'for g in realpred['groups'])}/3，绝对精度NOT_EVALUABLE。\n\n[真实切面首图](visualization/figures/01_MAIN_STRESS_SECTIONS.png) · [报告](TECHNICAL_REPORT.md) · [指标](visualization/STRESS_METRICS.csv) · [真实迁移](visualization/REAL_METRICS.json) · [失败台账](visualization/FAILURE_LEDGER.json)\n\n分散下降不自动等于正确位置；C0及GT恶化证据全部保留。\n";(attempt/'RESULT_CARD.md').write_text(card)
 page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Multisurface stress + real pilot</title><style>body{font:16px system-ui;max-width:1500px;margin:25px auto;background:#f5f7fa}img{max-width:100%}a{color:#235aa5}</style><h1>高方差完整多曲面 + 真实HERO最小迁移</h1><p>原始分散→Body粗定位→分层配准→最终统一主面；全部真实三角面切面，非采样点/平均轮廓。GT仅仿真可得。</p><img src="figures/01_MAIN_STRESS_SECTIONS.png" alt="First main scientific figure: all independent local Mesh cuts"><p><a href="sections_all.html">全部组合真实切面</a> · <a href="multisurface_3d.html">仿真完整Mesh交互</a> · <a href="../TECHNICAL_REPORT.md">技术报告</a> · <a href="../RESULT_CARD.md">结果卡</a> · <a href="STRESS_METRICS.csv">仿真指标</a> · <a href="REAL_METRICS.json">真实指标</a> · <a href="FAILURE_LEDGER.json">失败台账</a> · <a href="../RUN_MANIFEST.json">运行清单</a></p><svg viewBox="0 0 1100 35"><text x="0" y="25">Frozen protocol → original thresholds → explicit CTF ablation → postfreeze independent evaluation</text></svg>'
 for c in ['C0','C4','C6']:page+=f'<h2>{c}实际切面</h2><img loading="lazy" src="figures/{c}_SECTIONS.png">'
 for g in task['stress']['real_groups']:
  page+=f'<h2>{g}真实HERO，无独立GT</h2><a href="{g}/index.html">{g}完整Mesh/切面/证据</a>'
  if any(x[1]==g for x in figlinks):page+=f'<img loading="lazy" src="figures/{g}_REAL_SECTIONS.png">'
 page+='<p><a href="REAL_AUDIT.json">真实源审计</a> · <a href="CTF_ELIGIBILITY.json">CTF触发</a> · <a href="NOISE_AUDIT.json">实际注入</a></p><details><summary>历史工程回归参考</summary><img src="../evidence.png" alt="Historical engineering evidence only"></details></html>';(attempt/'index.html').write_text(page)
 return outputs(attempt,dict(status='PASS',scientific_failures=ledger['failures'],simulation_models=len(stress['rows']),real_groups=3,exact_triangle_sections=True))
