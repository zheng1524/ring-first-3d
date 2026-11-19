"""Actual Mesh figures, native Mask explanations and full offline WebGL review."""
import json,csv,html,shutil
from pathlib import Path
import numpy as np
from ..policy.contracts import ROOT
from ..synthetic.io import fetch,save_json,outputs
from ..multisurface.visualize import viewer,plain_mesh
from ..multisurface.geometry import scene,cast,mesh_sections,plane_coordinates
from ..stress.real import load_view
from .train import sources

def run(task,attempt,smoke=False):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 from matplotlib.collections import LineCollection
 root=attempt.parents[1];ev='G3_smoke_evaluate'if smoke else'G3_all_evaluate';tr='G1_smoke_train'if smoke else'G1_all_train';hr='G2_smoke_hero'if smoke else'G2_all_hero';body=json.loads(fetch(root,ev,'BODY_SHAPE_METRICS.json').read_text());hero=json.loads(fetch(root,ev,'HERO_METRICS.json').read_text());pred=json.loads(fetch(root,tr,'BODY_PREDICTIONS_FROZEN.json').read_text())['records'];hpred=json.loads(fetch(root,hr,'ALL_HERO_PREDICTIONS_FROZEN.json').read_text())['groups'];rows={c['case']:c for c in sources(task)['cases']};real={c['group']:c for c in sources(task)['real_groups']};cases=list(dict.fromkeys(r['case']for r in pred));br={(r['case'],r['arm']):r for r in body['rows']};pr={(r['case'],r['arm']):r for r in pred};(attempt/'figures').mkdir();figures=[];world={};aligned={};GT={}
 for g in cases:
  GT[g]=dict(np.load(rows[g]['GT']['path']))
  for a in ['A0','A1','A2','A2S']:
   if br.get((g,a),{}).get('status')=='NUMERIC':aligned[g,a]=dict(np.load(fetch(root,ev,br[g,a]['aligned_mesh_relative'])));world[g,a]=dict(np.load(fetch(root,tr,pr[g,a]['world_mesh_relative'])))
 def box(meshes):
  V=np.concatenate([m['V']for m in meshes]);c=(V.min(0)+V.max(0))/2;r=max(.5,float(np.ptp(V,axis=0).max())*.55);return c,r
 def show(ax,mesh,center,r,gt=None,title=''):
  if gt is not None:ax.add_collection3d(Poly3DCollection(gt['V'][gt['F']],facecolors=(.55,.55,.55,.25),edgecolors='none'))
  if mesh is not None:ax.add_collection3d(Poly3DCollection(mesh['V'][mesh.get('F_solid',mesh['F'])],facecolors=(.48,.18,.68,.78),edgecolors='none'))
  else:ax.text(*center,'NOT_EVALUABLE',color='red')
  ax.set(xlim=(center[0]-r,center[0]+r),ylim=(center[1]-r,center[1]+r),zlim=(center[2]-r,center[2]+r),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.set_box_aspect((1,1,1));ax.view_init(15,-65);ax.tick_params(labelsize=5);ax.set_title(title,fontsize=8)
 def body_row(g,fig,row,nrows):
  c,r=box([GT[g]]+[m for (gg,a),m in aligned.items()if gg==g]);parts=[('A0',None),('A1',None),('A2',None),('A2',GT[g])]
  for col,(a,gt)in enumerate(parts):
   ax=fig.add_subplot(nrows,4,row*4+col+1,projection='3d');m=br.get((g,a),{});title=g+' / '+a+(' actual GT overlay'if col==3 else' aligned evaluation copy')
   if m.get('status')=='NUMERIC':title+='\nstrict IoU '+str(m['IoU_3D'])+' | conditional %.3f\nCD %.3f / p95 %.3f mm'%(m['conditional_occupancy_IoU'],m['Chamfer_MAE_mm'],m['Chamfer_P95_mm'])
   show(ax,aligned.get((g,a)),c,r,gt,title)
 fig=plt.figure(figsize=(18,4*len(cases)),layout='constrained')
 for i,g in enumerate(cases):body_row(g,fig,i,len(cases))
 fig.suptitle('Figure 1 | Actual Init-A shapes, each independently rigid-aligned to GT, scale1\nA0 immutable historical FINAL → A1 004-only → A2 joint 004+005 → GT gray / aligned A2 purple\nAll columns are evaluation copies in the same GT metric frame; original world predictions are untouched. Strict vs conditional IoU are separate.',fontsize=11);fig.savefig(attempt/'figures/Fig1_All_InitA_Bodies.png',dpi=100);plt.close(fig);figures.append('Fig1_All_InitA_Bodies.png')
 for g in cases:
  folder=attempt/g;folder.mkdir();fig=plt.figure(figsize=(18,5),layout='constrained');body_row(g,fig,0,1);fig.savefig(attempt/'figures'/(g+'_BODY_GT.png'),dpi=110);plt.close(fig)
  # Source images and actual Mesh masks, no idealized silhouette replacement.
  fig,axes=plt.subplots(2,5,figsize=(18,8),layout='constrained');ring=np.load(rows[g]['static']['RING.npz']['path']);rs=scene(ring['V'],ring['F'])
  for row,vv in enumerate(['004','005']):
   v=next((v for v in rows[g]['FIT']if v['meta']['video']==vv),None)
   if v is None:
    for ax in axes[row]:ax.text(.1,.5,'NO SOURCE '+vv);ax.axis('off')
    continue
   a=np.load(v['cache']['path']);H,W=a['labels'].shape;y,x=np.mgrid[:H,:W];uv=np.c_[x.ravel(),y.ravel()];rz,_,_=cast(rs,uv,a['K'],a['T']);axes[row,0].imshow(a['RGB']);axes[row,1].imshow(a['labels'],vmin=0,vmax=2);axes[row,0].set_title(v['meta']['id']);axes[row,1].set_title('Actual Polyp/Ring Mask')
   for col,arm in enumerate(['A0','A1','A2'],2):
    ax=axes[row,col];ax.imshow(a['RGB'])
    if(g,arm)in world:
     mm=world[g,arm];z,_,_=cast(scene(mm['V'],mm['F']),uv,a['K'],a['T']);pm=(np.isfinite(z)&(z>0)&(z<rz)).reshape(H,W);target=a['labels']==1;known=a['labels']!=2;overlay=np.zeros((H,W,4));overlay[target&pm]=[0.,.85,.1,.45];overlay[target&~pm]=[1.,.1,.8,.7];overlay[~target&pm&known]=[1.,.1,.1,.7];ax.imshow(overlay);tp=int((target&pm).sum());fp=int((~target&pm&known).sum());fn=int((target&~pm).sum());ax.set_title(arm+' native IoU %.4f'%(tp/max(1,tp+fp+fn)))
    else:ax.text(20,30,arm+' NOT_EVALUABLE',color='red')
   for ax in axes[row]:ax.axis('off')
  fig.suptitle(g+' / Figure 2: unchanged source cameras, world prediction masks; green TP, magenta missed, red extra; observed Ring negative evidence unknown',fontsize=10);fig.savefig(attempt/'figures'/(g+'_FIG2_MASKS.png'),dpi=105);plt.close(fig)
  # Full actual aligned Mesh viewer: no original-world fake GT overlay.
  arms=[a for a in ['A0','A1','A2','A2S']if(g,a)in aligned];shared=dict(frames=[],conditions=['SHAPE'],bodies={a:plain_mesh(aligned[g,a])for a in arms},GT=plain_mesh(GT[g]),ring=dict(V=[],F=[]),meshes={});packets={'SHAPE_'+a:dict(poses={},results={'M0|0.5':dict(corrections={},fused=None,summary=br[g,a])})for a in arms};viewer(folder,shared,packets);p=folder/'multisurface_3d.html';text=p.read_text();center,extent=box([GT[g]]+[aligned[g,a]for a in arms]);scale=1/(extent*1.1);text=text.replace('cases/C3_E1.js','cases/SHAPE_'+arms[0]+'.js').replace("cs.value='C3'","cs.value='SHAPE'").replace('<option>E1</option><option>E2</option>',''.join('<option>'+a+'</option>'for a in arms)).replace('<option>M0</option><option>ICP</option><option>BODY_VIDEO</option><option selected>BODY_HIER</option>','<option selected>M0</option>').replace('type="checkbox" checked>物理Ring','type="checkbox">Ring excluded in GT frame').replace('16独立深度栅格曲面 + 冻结Body + GT切面审阅',g+' actual scale1 GT-aligned shape copies').replace('G01_LIKE_SIMULATION / INDEPENDENT_DEPTH_GRID_SYNTHETIC_HERO_PROXY。','Real Init-A shape evaluation only; world models untouched. ')
  text=text.replace('[.55,.55,.55,.2]','[.48,.18,.68,.75]').replace("gl.disable(gl.DEPTH_TEST);mesh(S.GT,'GT',I,[.02,.02,.02,.65],true);gl.enable(gl.DEPTH_TEST)","gl.depthMask(false);mesh(S.GT,'GT',I,[.55,.55,.55,.28]);gl.depthMask(true)")
  text=text.replace('p.x*0.04','p.x*'+str(scale)).replace('p.y*0.0631579','p.y*'+str(scale*1200/760)).replace('x2="270"','x2="'+str(30+6000*scale)+'"').replace('vec4 p=view*model*vec4(position,1.0);','vec4 p=view*model*vec4(position,1.0);').replace('[[cy,sy,0,0],[-sy*sp,cy*sp,cp,4*cp],[sy*cp,-cy*cp,sp,4*sp],[0,0,0,1]]','[[cy,sy,0,-cy*'+str(center[0])+'-sy*'+str(center[1])+'],[-sy*sp,cy*sp,cp,sy*sp*'+str(center[0])+'-cy*sp*'+str(center[1])+'-cp*'+str(center[2])+'],[sy*cp,-cy*cp,sp,-sy*cp*'+str(center[0])+'-cy*cp*'+str(center[1])+'-sp*'+str(center[2])+'],[0,0,0,1]]').replace('href="MODEL_METRICS.json"','href="BODY_METRICS.json"').replace('href="REGISTRATION_METRICS.json"','href="BODY_METRICS.json"').replace('href="FAILURE_LEDGER.json"','href="BODY_METRICS.json"');p.write_text(text);save_json(folder/'BODY_METRICS.json',[br[g,a]for a in arms]);(folder/'index.html').write_text('<h1>'+g+' actual rigid-aligned shape copies</h1><a href="multisurface_3d.html">Interactive exact aligned Mesh + GT</a> · <a href="BODY_METRICS.json">IoU validity / metrics / SE3</a> · <a href="../index.html">Home</a>')
 # Explicit actual-world and actual aligned failure figures for both verified Ip diagnoses.
 ips=[g for g in ['G02','G03']if g in cases];
 if ips:
  fig=plt.figure(figsize=(22,5*len(ips)),layout='constrained')
  for i,g in enumerate(ips):
   initial=dict(np.load(rows[g]['initial']['path']));cc,rr=box([initial]+[world[g,a]for a in ['A1','A2']if(g,a)in world]);cg,rg=box([GT[g]]+[aligned[g,a]for a in ['A0','A1','A2']if(g,a)in aligned])
   for j,(a,m)in enumerate([('013 Initial',initial),('004-only',world.get((g,'A1'))),('004+005',world.get((g,'A2')))]):show(fig.add_subplot(len(ips),6,i*6+j+1,projection='3d'),m,cc,rr,None,g+' WORLD '+a)
   for j,a in enumerate(['A0','A1','A2']):show(fig.add_subplot(len(ips),6,i*6+j+4,projection='3d'),aligned.get((g,a)),cg,rg,GT[g],g+' '+a+' actual GT alignment')
  fig.suptitle('Figure 3 | Verified raw-source failures: G02 half-ellipsoid/cap-like start, G03 missing long stalk\nSame vertices/topology/update mechanism for every case. Actual SE3-evaluated head/stalk geometry, no morphology-specific patch.',fontsize=11);fig.savefig(attempt/'figures/Fig3_Verified_Ip_Failures.png',dpi=110);plt.close(fig);figures.append('Fig3_Verified_Ip_Failures.png')
 # Figure 4: complete actual HERO Mesh intersections. No fused skin can hide them.
 hero_rows={g['case']:g for g in hero['groups']}
 for group in hpred:
  g=group['case']
  if group['status']!='NUMERIC':continue
  folder=attempt/(g+'_HERO');folder.mkdir();src=real[g];data=[load_view(v,[.3,.1])for v in src['views']if v['role']=='FIT'];frames=[dict(id=d['id'],video=d['video'])for d in data];raw=[dict(V=d['V'],F=d['F'])for d in data];actual={r['method']:[dict(np.load(fetch(root,hr,g+'/'+r['method']+'/'+d['id']+'.npz')))for d in data]for r in group['records']if r['status']=='NUMERIC'};bod=world[g,'A2'];ring=dict(np.load(rows[g]['static']['RING.npz']['path']));V=np.concatenate([bod['V']]+[m['V']for mm in actual.values()for m in mm]);c,r=box([dict(V=V,F=np.empty((0,3),int))]);ranges=[[c[j]-r,c[j]+r]for j in range(3)];iv=np.load(rows[g]['initial']['path'])['V'];center=iv.mean(0);zlo,zhi=iv[:,2].min(),iv[:,2].max();planes=[(0,float(center[0])),(1,float(center[1])),(2,float(zlo+(zhi-zlo)/3)),(2,float(zlo+2*(zhi-zlo)/3))];fig,axs=plt.subplots(4,4,figsize=(18,18),layout='constrained')
  for row,(axis,off)in enumerate(planes):
   other=[j for j in range(3)if j!=axis];bseg=plane_coordinates(mesh_sections(bod['V'],bod['F'],axis,off),axis)
   for col,method in enumerate(['M0','BODY_A1','BODY_A2','ICP']):
    ax=axs[row,col]
    if len(bseg):ax.add_collection(LineCollection(bseg,colors='#999',linestyles='dashed',linewidths=1))
    for i,m in enumerate(actual.get(method,[])):
     seg=plane_coordinates(mesh_sections(m['V'],m['F'],axis,off),axis)
     if len(seg):ax.add_collection(LineCollection(seg,colors='#d3223c'if data[i]['video']=='004'else'#1f67d2',linewidths=.7,alpha=.65))
    ax.set(xlim=ranges[other[0]],ylim=ranges[other[1]],xlabel='XYZ'[other[0]]+' [mm]',ylabel='XYZ'[other[1]]+' [mm]');ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_title(method+'\n'+('XYZ'[axis])+f'={off:.4f} mm',fontsize=9)
  fig.suptitle(g+' Figure 4 | Full original HERO triangle-plane intersections; red004 blue005; A2 Body gray fixed across columns; no fused occlusion, no GT\nPlanes frozen from 013 initial center and Z thirds. Same per-case mm limits across all methods; every original local Mesh retained.',fontsize=10);filename=g+'_FIG4_HERO_CUTS.png';fig.savefig(attempt/'figures'/filename,dpi=105);plt.close(fig);figures.append(filename)
  bs={a:plain_mesh(world[g,a])for a in ['A0','A1','A2']if(g,a)in world};shared=dict(frames=frames,conditions=['WORLD'],bodies=bs,GT=dict(V=[],F=[]),ring=plain_mesh(ring),meshes={d['id']:plain_mesh(d)for d in data});results={r['method']+'|0.5':dict(corrections=r.get('corrections'),fused=None,summary=next(m for m in hero_rows[g]['methods']if m['method']==r['method']))for r in group['records']};packets={'WORLD_'+a:dict(poses={d['id']:np.eye(4).tolist()for d in data},results=results)for a in bs};viewer(folder,shared,packets);p=folder/'multisurface_3d.html';text=p.read_text().replace('cases/C3_E1.js','cases/WORLD_A2.js').replace("cs.value='C3'","cs.value='WORLD'").replace('<option>E1</option><option>E2</option>','<option>A2</option><option>A1</option><option>A0</option>').replace('<option>M0</option><option>ICP</option><option>BODY_VIDEO</option><option selected>BODY_HIER</option>','<option>M0</option><option>BODY_A0</option><option>BODY_A1</option><option selected>BODY_A2</option><option>ICP</option>').replace('type="checkbox" checked>GT黑色网格线','type="checkbox">No independent GT').replace('16独立深度栅格曲面 + 冻结Body + GT切面审阅',g+' actual complete HERO Mesh + frozen Init-A Body').replace('G01_LIKE_SIMULATION / INDEPENDENT_DEPTH_GRID_SYNTHETIC_HERO_PROXY。','REAL_HERO / exact source Meshes, no independent GT; no fused surface. ').replace('/16\\n','/'+str(len(data))+'\\n').replace('p.x*0.04','p.x*'+str(1/(r+np.linalg.norm(c)+2))).replace('p.y*0.0631579','p.y*'+str(1200/760/(r+np.linalg.norm(c)+2))).replace('x2="270"','x2="'+str(30+6000/(r+np.linalg.norm(c)+2))+'"').replace('p.z/100.0','p.z/1000.0').replace('href="MODEL_METRICS.json"','href="HERO_METRICS.json"').replace('href="REGISTRATION_METRICS.json"','href="HERO_METRICS.json"').replace('href="FAILURE_LEDGER.json"','href="HERO_METRICS.json"');p.write_text(text);save_json(folder/'HERO_METRICS.json',hero_rows[g]);(folder/'index.html').write_text('<h1>'+g+' full HERO Mesh, no independent GT</h1><a href="multisurface_3d.html">Full Mesh per-view toggles</a> · <a href="HERO_METRICS.json">Fixed target overlap / HOLDOUT / geometry</a> · <a href="../index.html">Home</a>')
 for name in ['BODY_SHAPE_METRICS.json','BODY_SHAPE_METRICS.csv','GT_RIGID_TRANSFORMS.json','HERO_METRICS.json','PAIRED_COMPARISONS.json','FAILURE_LEDGER.json']:shutil.copyfile(fetch(root,ev,name),attempt/name)
 paired=json.loads(fetch(root,ev,'PAIRED_COMPARISONS.json').read_text());summary=dict(target_cases=11,numeric_body_rows=sum(r['status']=='NUMERIC'for r in body['rows']),strict_IoU_rows=sum(r.get('IoU_3D')is not None for r in body['rows']),paired_body_cases=len(paired['body']),conditional_IoU_A2_better_cases=sum(r['conditional_IoU_delta_A2_minus_A1']>0 for r in paired['body']),Chamfer_A2_better_cases=sum(r['Chamfer_delta_A2_minus_A1_mm']<0 for r in paired['body']),HERO_numeric_groups=sum(g['status']=='NUMERIC'for g in hero['groups']),HERO_absolute_accuracy='NOT_EVALUABLE',GT_aligned_world_inputs=False);save_json(attempt/'SCIENTIFIC_SUMMARY.json',summary)
 report=f"# {task['task_id']}\n\n![Figure1: actual historical Init-A and multivideo predictions, true scale1 GT alignment copies](visualization/figures/Fig1_All_InitA_Bodies.png)\n\n"
 report+='## 版本来源与科学范围\n\n015正式来源`'+task['inita']['legacy_commit']+'`；A0为历史Init-A FINAL不可修改参考。A1与A2全部从真实FREE_VERTEX_013/inputs/.../INITIAL.npz开始，V/F/F_solid/基底标记与015 Init-A完全核验一致，没有E1/E2/Init-B/Init-C替代。训练调用原train_mesh.main、PyTorch3D Case/RingAware、FreeVertices、密集32/FCL/反向包含/自交保护、Adam/线搜索/顶点更新和80提案/40接受/30连续拒绝停止。只增加输入与多视频分母适配，原代码逐文件SHA锁定。所有预测取最后接受状态，不按GT或HOLDOUT挑checkpoint。\n\n'
 report+='004 FIT为015原8视角；005从014已有Ring-First/明确标记的派生相机中按方向最远点选8视角，GT不参与。每视频/每方向/每视角使用历史weights函数；弱深度项保留历史原始观测，仅将可用深度按视频/视角均衡，未生成新HERO。HOLDOUT不参与梯度、共享修正或模型选择。A2是一个共享Mesh，不是拼接两个Body。G08只有005，004-only和004+005均NOT_EVALUABLE，未冒充004。原014 G01跨视频共享位姿候选并无部署认证；直接版本如实使用既有相机来源，不能宣称绝对坐标正确。\n\n'
 report+='G02经实际初始Mesh和RGB/Mask核验为半椭球/扁帽状起点；G03原椭球未表达图像长柄。两者同算法，不使用形态补丁。A2若FIT005 IoU比004低>0.10或005<0.5，另行A2S：004固定、005一个共享SE3、FIT轮廓/Ring/先验求解后，从同一013起点重新跑原训练。A2/A2S独立报告，没有GT或逐帧相机优化，也未静默替换直接结果。\n\n'
 report+='## 真正的GT刚体评价与IoU有效性\n\n所有适用cohort预测先冻结，再逐模型复用best_rigid015.align：96固定旋转起点、top8双向真实最近曲面/刚性Kabsch与SE3回溯，尺度1；不认证数学全局最优。每组保存完整T、起点日志及实际对齐NPZ/PLY。GT变换只作用评价副本，训练Mesh、相机、Ring、HERO输入均逐SHA保护。Figure1所有预测使用各自真正对齐副本以便统一GT坐标比较，原公制结果另存Figure2/4和运行文件。\n\nIoU采用每例统一三维范围和相同2^17 Sobol三维点计算交并，不是原世界坐标假叠加。严格IoU要求双方闭合/一致朝向/无自交且无未认证推断基底；否则严格IoU为NaN。另报conditional_occupancy_IoU，实体无效时只是原F_solid射线奇偶诊断，不能称合法实体IoU。8192样本/方向查询实际三角面给Chamfer、P95、最大值、GT覆盖和0.5mm F-score。相对表面误差明确定义为绝对距离/GT包围盒对角线，不冒充DXY直径相对误差。\n\n'
 report+='## 全部主体结果\n\n| Case / arm | Strict IoU status | Conditional occupancy IoU | Chamfer MAE / P95 mm | F-score0.5 |\n| --- | --- | --- | --- | --- |\n'
 fmt=lambda x:'NaN'if x is None else f'{x:.6f}'
 for r in body['rows']:report+=f"| {r['case']} / {r['arm']} | {r.get('IoU_3D_status','NOT_EVALUABLE')} | {fmt(r.get('conditional_occupancy_IoU'))} | {fmt(r.get('Chamfer_MAE_mm'))} / {fmt(r.get('Chamfer_P95_mm'))} | {fmt(r.get('Fscore_0p5mm'))} |\n"
 report+='\n## 真实HERO定位与接口限制\n\n复用近期真实原生HERO适配器，严格验证深度/K/C/源像素/原Mask/DXY哈希/完整网格拓扑。对于无>=2个来源绑定完整Mesh的物理组逐组NOT_EVALUABLE，不把旧融合结果、采样点或新生成模型补齐。所有11组保留原HERO来源库存，缺接口并不删除目标分母。G01/G03/G05优先端到端Smoke后才扩展全组。\n\n使用实际Init-A Mesh的表观轮廓拟合二维投影椭圆作为中介，所有射线必须命中实际Init-A Face/重心；没有三维椭球替换。BODY_HIER的优化函数代码不变，只适配其投影数据提供器。M0、BODY_A0、BODY_A1、BODY_A2及原Robust ICP分开输出；每视频共享SE3和0.3°/0.10mm先验约束帧残余，Body容差0.5mm，所有Body固定，曲面保持整体刚性和完整原顶点/拓扑。GT对齐Body从不进入HERO。\n\n最近表面一致性使用配准前投影Mask冻结支持查询，不是独立材料真值。真实HERO无独立GT，绝对位置/误差NOT_EVALUABLE；保留跨视频原坐标不确定性、留出投影、对应拒绝、修正幅度和边长不变断言。Figure4没有最终融合层遮住局部曲面。\n\n'
 report+='## 配对回答\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n同组共同数值样本比较A2-A1，不按结果剔除失败。严格实体IoU不足时不把conditional值升级为严格主要指标。最终结论需同时核查对照表、图像、条件占据限制与HERO留出表现。\n\n'
 report+='## 固定审计表\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | 历史全部11个物理组，不将实验臂或视频当作独立病例 |\n| 本算法独立成功 | 数值输出、严格IoU可计算、形状正确、真实HERO多视频定位分别统计，见完整JSON/CSV |\n| 本算法失败 | G08缺004等逐组NOT_EVALUABLE/NaN；IoU实体无效、HERO接口缺失与科学负结果全部保留 |\n| 历史测量值回退 | 0；A0仅不可修改参考，授权013输入Mesh不作为最终结果回填 |\n| 失败组及具体原因 | FAILURE_LEDGER、主体GT有效性、真实HERO来源缺口和每病例图 |\n| 最终统计样本 | 所有目标11组保留；各项可计算N及共同样本配对独立报告 |\n| 是否使用GT选择算法 | 否；协议/源码/输入及最后接受checkpoint冻结，GT只在评价副本中作尺度固定SE3 |\n\n'
 for g in cases:
  report+=f'### {g}\n\n![{g} actual aligned Meshes](visualization/figures/{g}_BODY_GT.png)\n\n![{g} native Mask explanations](visualization/figures/{g}_FIG2_MASKS.png)\n\n[{g}实际GT对齐Mesh交互](visualization/{g}/index.html)\n\n'
  if any(p==g+'_FIG4_HERO_CUTS.png'for p in figures):report+=f'![{g} full HERO actual cuts](visualization/figures/{g}_FIG4_HERO_CUTS.png)\n\n[{g}完整HERO逐曲面交互](visualization/{g}_HERO/index.html)\n\n'
 if ips:report+='![G02/G03 failure details](visualization/figures/Fig3_Verified_Ip_Failures.png)\n'
 (attempt/'TECHNICAL_REPORT.md').write_text(report);(attempt/'RESULT_CARD.md').write_text('# '+task['task_id']+'\n\n执行完成，科学结论保留有效性与失败限制。\n\n[报告](TECHNICAL_REPORT.md) · [全组主体对照](visualization/BODY_SHAPE_METRICS.csv) · [HERO](visualization/HERO_METRICS.json) · [失败](visualization/FAILURE_LEDGER.json)\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Init-A multi-video research review</title><style>body{font:16px system-ui;max-width:1550px;margin:25px auto;background:#f5f7fa}img{max-width:100%}a{color:#235da8}</style><h1>历史Init-A：004-only、004+005与真实HERO定位</h1><p>首图使用真实尺度1刚体对齐后的Mesh副本；所有公制世界预测、相机和HERO保持冻结。</p><img src="figures/Fig1_All_InitA_Bodies.png" alt="Actual rigid-aligned Init-A Mesh comparison"><p><a href="../TECHNICAL_REPORT.md">技术报告</a> · <a href="../RESULT_CARD.md">结果卡</a> · <a href="BODY_SHAPE_METRICS.csv">全组形状对照</a> · <a href="HERO_METRICS.json">全组HERO</a> · <a href="GT_RIGID_TRANSFORMS.json">实际SE3矩阵</a> · <a href="FAILURE_LEDGER.json">失败台账</a> · <a href="../RUN_MANIFEST.json">运行清单</a></p><svg viewBox="0 0 1200 40"><text x="0" y="25">Exact 013 Mesh → inherited 015 trainer → prediction freeze → genuine scale1 GT evaluation copies / GT-free HERO localization</text></svg>'
 if ips:page+='<h2>已核验错误Ip专项</h2><img src="figures/Fig3_Verified_Ip_Failures.png">'
 for g in cases:
  page+='<h2>'+g+'</h2><a href="'+g+'/index.html">实际GT对齐完整Mesh</a><img loading="lazy" src="figures/'+g+'_FIG2_MASKS.png">'
  if g+'_FIG4_HERO_CUTS.png'in figures:page+='<a href="'+g+'_HERO/index.html">完整原始HERO曲面交互</a><img loading="lazy" src="figures/'+g+'_FIG4_HERO_CUTS.png">'
 page+='<details><summary>历史工程回归参考，非科学主图</summary><img src="../evidence.png" alt="Historical engineering regression reference"></details></html>';(attempt/'index.html').write_text(page)
 return outputs(attempt,dict(status='PASS',scientific_failures=json.loads(fetch(root,ev,'FAILURE_LEDGER.json').read_text())['failures'],summary=summary,actual_rigid_aligned_Mesh_figures=True,full_HERO_Mesh_cuts=True))
