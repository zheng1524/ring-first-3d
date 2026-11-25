"""Chinese presentation of every original mesh; rendering never changes admission."""
import math,html,csv,sys,importlib.util
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import trimesh,cv2
from .route import W,T,B,read,save,sha,environment

FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
plt.rcParams['font.family']=FontProperties(fname=FONT).get_name()
plt.rcParams['axes.unicode_minus']=False
plt.rcParams['font.size']=9
F=T/'figures';F.mkdir(exist_ok=True)
ANGLES=[('斜视一',20,-60),('斜视二',20,60),('斜视三',20,180),('沿X轴',0,0),('沿Y轴',0,90),('沿Z轴',89.9999,0)]
OLD=np.array([.12,.40,.85]);NEW=np.array([1.,.43,.05])
LABEL={'HIST':'历史锚帧候选','GRAPH':'连接图锚帧试点','BASELINE':'当前V6基线'}

def renderer():
 p=W/'src/ring_first_3d/mainline/native/_mesh_renderer.py'
 sp=importlib.util.spec_from_file_location('retained_actual_mesh_renderer',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m.actual_mesh_image

def short(case):return case.replace('GP_','').replace('_closed_',' / ').replace('_single_refY_',' / 视频')
def num(x):return '不可评价'if x is None else f'{x:.2f}'
def scale(ax,pxmm):
 wanted=60/max(pxmm,1e-12);power=10**math.floor(math.log10(wanted));mm=min([x*power for x in [1,2,5,10]],key=lambda x:abs(x-wanted))
 ax.plot([15,15+mm*pxmm],[375,375],color='black',lw=2);ax.text(15,360,f'中心深度约 {mm:g} 毫米',fontsize=7,backgroundcolor='white')
def finish(fig,path):
 fig.tight_layout(rect=(0,0,1,.93));fig.savefig(path,dpi=105,**({'pil_kwargs':{'quality':87}}if str(path).endswith('.jpg')else{}));plt.close(fig)
def geometry(rows):
 data={}
 for r in rows:
  if r['status']!='RENDERABLE':continue
  m=trimesh.load(r['mesh_path'],process=False);v=np.asarray(m.vertices);f=np.asarray(m.faces);c=np.asarray(m.visual.vertex_colors)[:,:3]/255.;data[r['tag']]=(v,f,c)
 return data
def draw(ax,v,f,c,cad,bounds,e=0,a=90):
 im,px=renderer()(v,f,cad['V'],cad['F'],bounds,e,a,'white',face_colors=c);ax.imshow(im);scale(ax,px);ax.axis('off')

def six(rows,data,cad,bounds,path,title,rule=False,summary=None):
 vv=[];ff=[];cc=[];n=0
 for r in rows:
  v,f,c=data[r['tag']];vv.append(v);ff.append(f+n);n+=len(v);cc.append(np.tile(OLD if r['old_rule_generated']else NEW,(len(f),1))if rule else c[f].mean(1))
 fig,axs=plt.subplots(2,3,figsize=(12,8.8))
 for ax,(name,e,a)in zip(axs.flat,ANGLES):
  if vv:draw(ax,np.concatenate(vv),np.concatenate(ff),np.concatenate(cc),cad,bounds,e,a)
  else:ax.text(.5,.5,('当前V6基线无正式面源\n未在基线输入上运行本轮Q1'if '当前V6基线'in title else'原规则无可渲染输出\n新规则仍无可渲染输出\n'+('无合法组合'if not summary.get('legal_combinations')else'存在合法组合，推理/建面/评价失败')),ha='center',va='center',fontsize=12);ax.axis('off')
  ax.set_title(name)
 old=sum(r['old_rule_generated']for r in rows);added=len(rows)-old
 fig.suptitle(title+f'\n全部可渲染 {len(rows)} 张；原规则 {old} 张'+('（原规则无可渲染输出）'if not old else'')+f'；放宽新增 {added} 张；失败/不可渲染 {summary.get("failed_or_nonrenderable",0)}\n'+('蓝色=原规则组合；橙色=放宽后新增；'if rule else'原始RGB面色；')+'黑色=真实Ring CAD；全范围毫米坐标；各运行yaw独立，不跨运行叠加',fontsize=10);finish(fig,path)

def per_source(r,rows,data,cad,bounds,path,R,pairs,render_ns):
 d=np.load(r['display']);v,f,c=data[r['tag']];L=read(R/'inputs/ledger005.json');p=r['plan'];fig,axs=plt.subplots(3,3,figsize=(14,10.5));axs=axs.ravel()
 axs[0].imshow(d['A_RGB']);axs[0].set_title(f"目标原始RGB：RAW {r['raw_target']}")
 axs[1].imshow(d['A_Mask'],vmin=0,vmax=2,cmap='viridis');axs[1].set_title('实际Mask：0背景 / 1息肉 / 2 Ring')
 ims=[cv2.cvtColor(cv2.resize(cv2.imread(L[i]['RGB_path']),(320,180)),cv2.COLOR_BGR2RGB)for i in p['sources']]
 axs[2].imshow(np.concatenate(ims,axis=0));axs[2].set_title('三个Support RAW帧（由上到下）\n'+str(r['raw_support']))
 im=axs[3].imshow(d['ring_heat'],vmin=0,vmax=5,cmap='magma');fig.colorbar(im,ax=axs[3],fraction=.035,extend='max')
 q=r['ring'];axs[3].set_title(f"Ring误差（毫米），上端三角表示>5\nMAE {num(q['MAE_mm'])} / P95 {num(q['p95_mm'])}\n>5: {q['over5_count']}像素；最大 {num(q['max_mm'])}")
 axs[4].imshow(d['B_RGB']);axs[4].set_title(f"非HERO输入B：RAW {r['noninput_B']['B_raw_frame']}\n其相机参与BA，非全链路独立")
 axs[5].imshow(d['A_to_B']);axs[5].set_title('本面原始三角形与RGB投影至B\n遮挡/纹理差异只作诊断')
 err=d['A_to_B_error'];good=np.isfinite(err)
 if good.any()and np.nanquantile(err,.95)>30:
  yy,xx=np.where(good&(err>=np.nanquantile(err,.95)));xy=(float(np.median(xx)),float(np.median(yy)))
  axs[5].annotate('疑似轮廓/纹理偏离\n待人工检查',xy=xy,xytext=(10,320),fontsize=8,color='darkred',bbox=dict(facecolor='white',alpha=.85),arrowprops=dict(arrowstyle='->',color='red'))
 draw(axs[6],v,f,c[f].mean(1),cad,bounds);axs[6].set_title('原始表面侧视；与总览相同比例')
 draw(axs[7],v,f,np.tile(OLD if r['old_rule_generated']else NEW,(len(f),1)),cad,bounds,20,-60);axs[7].set_title('原规则蓝色 / 新增橙色；未经融合')
 pp=[a for a in pairs if a['A']==r['tag']and a['P95_absolute_mm']is not None]
 if pp:
  worst=max(pp,key=lambda a:a['P95_absolute_mm']);other=next(a for a in rows if a['tag']==worst['B']);b=other['plan']['reference'];ver=read(R/'predictions/local005_primary.json')['primary_version'];C=np.load(R/f'predictions/local005_camera_{ver}.npz')['c2w'];z=np.load(other['native_path']);db=cv2.resize(z['depth_mm'],(640,360));bl=cv2.imread(L[b]['Mask_path'],0)
  pred=render_ns['render'](v,f,c,np.asarray(L[b]['K']),C[b],np.eye(4),'R5'if '_R5_'in r['case']else'R10');valid=pred['valid']&(bl==1)&np.isfinite(db)&(db>0);heat=np.where(valid,abs(pred['z_mm']-db),np.nan);im=axs[8].imshow(heat,vmin=0,vmax=5,cmap='magma');fig.colorbar(im,ax=axs[8],fraction=.035,extend='max')
  axs[8].set_title(f"重叠差异最大的一对：B RAW {other['raw_target']}\nP95 {num(worst['P95_absolute_mm'])}毫米；仅诊断")
  if valid.any()and worst['P95_absolute_mm']>2:
   yy,xx=np.where(valid&(heat>=np.nanquantile(heat,.95)));axs[8].annotate('疑似错层\n遮挡也可能造成差异',xy=(np.median(xx),np.median(yy)),xytext=(5,325),fontsize=8,color='darkred',bbox=dict(facecolor='white',alpha=.9),arrowprops=dict(arrowstyle='->',color='red'))
 else:axs[8].text(.5,.5,'无可评价的重叠面源',ha='center');axs[8].set_title('重叠一致性：不可评价')
 for ax in axs:ax.axis('off')
 reasons='；'.join(f"RAW {a['raw_frame']}："+'、'.join(a['reasons'])for a in p.get('addition_reasons',[]))
 rule='Q0 原规则组合已通过'if r['old_rule_generated']else'Q1 放宽新增：初始化中心分散≤2毫米硬门槛改为警告'
 fig.suptitle(short(r['case'])+' / '+LABEL[r['variant']]+f" / Target RAW {r['raw_target']} / Support {r['raw_support']}\n"+rule+'；通过上游门控不等于重建正确\n'+reasons,fontsize=10);finish(fig,path)

def render_run(out,bounds=None):
 out=Path(out);s=read(out/'SUMMARY.json');case=s['case'];variant=s['variant'];rows=[r for r in read(out/'RESULTS.json')if r['status']=='RENDERABLE'];data=geometry(rows);cad=dict(np.load(W/'runs/m2f5_unified/cad'/('R5.npz'if '_R5_'in case else'R10.npz')))
 assert (out/'COMPLETE.json').exists()and len(rows)==s['renderable'],'Evaluation is incomplete; do not render a partial result list'
 assert len(read(out/'RESULTS.json'))==s['legal_combinations'],'Every legal tuple must be represented'
 bounds=np.concatenate([cad['V']]+[a[0]for a in data.values()])if bounds is None else bounds
 prefix=variant+'__'+case;title=short(case)+' / '+LABEL[variant];images=[];details=[]
 for rule in [False,True]:
  name=prefix+('__规则.png'if rule else'__RGB.png');six(rows,data,cad,bounds,F/name,title,rule,s);images.append(name)
 R=Path(s.get('run_path',str(Path(rows[0]['mesh_path']).parent.parent if rows else B/variant/case)))
 if rows:
  fig,axs=plt.subplots(math.ceil(len(rows)/5),5,figsize=(15,3*math.ceil(len(rows)/5)),squeeze=False)
  for ax,r in zip(axs.flat,sorted(rows,key=lambda r:r['raw_target'])):
   v,f,c=data[r['tag']];draw(ax,v,f,c[f].mean(1),cad,bounds);ax.set_title(f"RAW {r['raw_target']} / "+('原规则'if r['old_rule_generated']else'放宽新增')+f"\nRing MAE/P95 {num(r['ring']['MAE_mm'])}/{num(r['ring']['p95_mm'])}毫米",fontsize=8)
  for ax in list(axs.flat)[len(rows):]:ax.axis('off')
  fig.suptitle(title+'：每一张原始面源，完整范围、统一侧视与比例；没有删除异常源');name=prefix+'__逐面图集.jpg';finish(fig,F/name);images.append(name)
  from .evaluate import scorer
  old,fn=scorer();r=rows[0];fs=old.frames(dict(route='V6',v6_root=str(R),plan=r['plan']));_,_,_,ns=fn(dict(ring_inner_mm=5 if '_R5_'in case else 10),fs,Path(r['display']).parent)
  pairs=read(out/'PAIR_DEPTH_CONSISTENCY.json')
  for r in rows:
   name=prefix+'__RAW'+str(r['raw_target'])+'.jpg';per_source(r,rows,data,cad,bounds,F/name,R,pairs,ns);details.append(dict(raw=r['raw_target'],support=r['raw_support'],old=r['old_rule_generated'],image=name,tag=r['tag']));print('SOURCE_FIGURE',variant,case,r['raw_target'],flush=True)
  L=read(R/'inputs/ledger005.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];C=np.load(R/f'predictions/local005_camera_{primary}.npz')['c2w'][:,:3,3]
  fig=plt.figure(figsize=(8,6));ax=fig.add_subplot(projection='3d');th=np.linspace(0,2*np.pi,120);rad=(3.1 if '_R5_'in case else 5.6);ax.plot(rad*np.cos(th),rad*np.sin(th),0*th,color='black');ax.plot(*C.T,'.-',lw=.7)
  for i,c in enumerate(C):ax.text(*c,str(L[i]['raw_frame']),fontsize=6)
  ax.set(xlabel='X（毫米）',ylabel='Y（毫米）',zlabel='Z（毫米）');fig.suptitle(title+'\n全部相机与真实RAW帧号；黑色Ring；各运行坐标独立');name=prefix+'__相机.png';finish(fig,F/name);images.append(name)
 result=dict(case=case,variant=variant,summary=s,images=images,details=details,gates=read(R/'metrics/GATES.json')if(R/'metrics/GATES.json').exists()else[],bounds_min_mm=bounds.min(0),bounds_max_mm=bounds.max(0),renderer=str(W/'src/ring_first_3d/mainline/native/_mesh_renderer.py'),renderer_sha256=sha(W/'src/ring_first_3d/mainline/native/_mesh_renderer.py'))
 save(out/'VISUALIZATION.json',result);return result

def index():
 records=[read(p)for p in sorted((B/'evaluation').glob('*/*/VISUALIZATION.json'))];parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>V6 RAW到HERO：中文完整图集</title><style>body{max-width:1450px;margin:2em auto;font-family:system-ui;background:#f5f6fa;color:#182336}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #bdc7da}img{max-width:100%}section{background:white;padding:1.3em;margin:1.5em 0}summary{cursor:pointer;padding:10px}a{color:#1458ac}.new{color:#a43e00}</style><h1>V6：从RAW重新运行的完整中文图集</h1><p>蓝色＝本轮同一相机下原规则已通过的组合；橙色＝放宽后新增。它们不等同于历史基线的成员。全部原始面源均保留；没有ICP、额外缩放、形变、融合或按深度误差删面。不同运行/视频的yaw未认证，不叠成一个世界。Ring指标以相机正确为条件；重叠差异及A→B投影均不是形状GT。</p><p><a href="TECHNICAL_REPORT.md">中文技术报告</a> · <a href="OBSERVATIONS_INDEX.html">RAW/Mask/Ring观测链</a> · <a href="SOURCE_MANIFEST.csv">逐源清单</a> · <a href="VIDEO_COMPARISON.csv">逐视频比较</a></p><table><tr><th>物理视频</th><th>运行</th><th>合法/启动/推理成功/可渲染/失败</th><th>原规则/新增</th><th>Ring MAE中位数（可评价源/可渲染源）</th><th>重叠P95中位数（可评价/有向配对）</th></tr>']
 for r in records:
  s=r['summary'];ident=r['variant']+'__'+r['case'];parts.append(f'<tr><td><a href="#{ident}">{short(r["case"])}</a></td><td>{LABEL[r["variant"]]}</td><td>{s.get("legal_combinations","待更新")} / {s.get("inference_started","待更新")} / {s.get("inference_success","待更新")} / {s["generated"]} / {s.get("failed_or_nonrenderable","待更新")}</td><td>{s["old_rule_generated"]} / {s["added"]}</td><td>{num(s["ring_MAE_median"])} ({s.get("ring_evaluable_sources","待更新")}/{s["generated"]})</td><td>{num(s["overlap_P95_pair_median"])} ({s["pair_evaluable"]}/{s["pair_count"]})</td></tr>')
 candidate=[r['summary']for r in records if r['variant']=='HIST'];parts[0]=parts[0].replace('<table><tr>',f'<p><b>固定5组10视频；统一HIST候选 {sum(x["generated"]for x in candidate)}张 / {sum(x["generated"]>0 for x in candidate)}/10视频。候选不升级，保留当前V6基线；没有共同RAW/Support的比较不记为通过。</b></p><table><tr>',1)
 parts.append('</table><p>表中毫米误差为不同目标集合的描述性统计；不能据此作同帧因果比较。下方可逐一展开每张面源。</p>')
 for r in records:
  ident=r['variant']+'__'+r['case'];parts.append(f'<section id="{ident}"><h2>{short(r["case"])} · {LABEL[r["variant"]]}</h2>')
  s=r['summary'];parts.append(f'<p>Ring共同像素/观测Ring像素：{s.get("ring_common_pixels","待更新")} / {s.get("ring_observed_pixels","待更新")}；重叠共同像素累计 {s.get("pair_common_pixels","待更新")}（各面重复计数，仅分母说明）。</p>')
  for failure in s.get('nonrenderable',[]):parts.append('<p class="new">未能渲染：Target RAW '+str(failure['raw_target'])+' / Support '+str(failure['raw_support'])+' / '+html.escape(failure.get('failure_reason',failure['status']))+'</p>')
  if s.get('not_admitted_targets'):parts.append('<details><summary>未获合法三Support组合的全部Target</summary><pre>'+html.escape(str([(x['raw_target'],'不足3个通过上游资格及共视条件的Support')for x in s['not_admitted_targets']]))+'</pre></details>')
  if r.get('gates'):
   parts.append('<details><summary>全部相机的旧/新门控与拒绝原因</summary><table><tr><th>RAW</th><th>旧/新通过</th><th>原因（像素或毫米）</th></tr>')
   for g in r['gates']:parts.append(f'<tr><td>{g["raw_frame"]}</td><td>{g["old_pass"]} / {g["new_pass"]}</td><td>'+html.escape('；'.join(g['reasons'])or'原规则通过')+'</td></tr>')
   parts.append('</table></details>')
  extra=[r['variant']+'__'+r['case']+'__'+x+'.png'for x in ['近景RGB','近景逐源']if(F/(r['variant']+'__'+r['case']+'__'+x+'.png')).exists()]
  for name in r['images']+extra:parts.append(f'<details open><summary>{html.escape(name.split("__")[-1])}</summary><a href="figures/{name}"><img loading="lazy" src="figures/{name}"></a></details>')
  for d in r['details']:parts.append(f'<details><summary class="{"new"if not d["old"]else""}">Target RAW {d["raw"]} / Support {d["support"]} / {"原规则"if d["old"]else"放宽新增：中心分散硬门槛改警告"}</summary><a href="figures/{d["image"]}"><img loading="lazy" src="figures/{d["image"]}"></a></details>')
  parts.append('</section>')
 parts.append('</html>');(T/'VISUALIZATION_INDEX.html').write_text('\n'.join(parts));save(T/'evidence/VISUALIZATION_INDEX.json',records)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--run');p.add_argument('--index',action='store_true');a=p.parse_args()
 if a.run:render_run(a.run)
 if a.index:index()
