"""Mandatory experiment-driven full-mesh views, pixel evidence and offline UI."""
import csv,html,json
import numpy as np
from pathlib import Path
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import require
from ..contracts.identities import sha256
from .geometry import transform,scene,closest,contour,choose
from .legacy import namespace


def interactive(attempt,shared,cases):
    data=json.dumps(dict(shared=shared,cases=cases),separators=(',',':')).replace('</','<\\/')
    page=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>G01-like complete dual-video mesh registration</title>
<style>body{font:16px system-ui;margin:24px;background:#f1f4f8;color:#162033}canvas{width:100%;max-width:1200px;background:white;touch-action:none}select,button{padding:8px;margin:4px}pre{white-space:pre-wrap}a{color:#255bb0}.red{color:#cf2435}.blue{color:#2474d2}</style>
<h1>G01_LIKE_SIMULATION · SYNTHETIC_HERO_PROXY</h1><p>完整曲面：<b class="red">004红</b>、<b class="blue">005蓝</b>、冻结粗Body灰、R10黑。不是实际HERO推理，不认证真实G01部署。拖动旋转；所有条件使用同一毫米尺度。</p>
<label>Condition <select id="condition"></select></label><label>Method <select id="method"></select></label><label>Stage <select id="stage"><option value="original">1 原始状态</option><option value="perturbed">2 人工错层</option><option value="mediated">3 二维主体候选对应（非修正）</option><option value="registered">4 实际配准后</option><option value="gt">5 独立GT评价</option></select></label>
<button id="front">正面</button><button id="side">侧面</button><button id="top">俯视</button><button id="reset">固定斜视</button>
<p><label><input id="body" type="checkbox" checked>灰色Body</label> <label><input id="ring" type="checkbox" checked>黑色Ring</label> <label><input id="v4" type="checkbox" checked>004完整Mesh</label> <label><input id="v5" type="checkbox" checked>005完整Mesh</label> <label><input id="truth" type="checkbox">原始GT网格线（仅评价）</label></p>
<canvas id="view" width="1200" height="760"></canvas><pre id="info"></pre><p><a href="index.html">返回审阅首页</a> · <a href="REGISTRATION_METRICS.json">全部有效/无效指标</a> · <a href="FAILURE_LEDGER.json">失败台账</a></p>
<script>const DATA=__DATA__,S=DATA.shared;const cs=document.querySelector('#condition'),ms=document.querySelector('#method'),ss=document.querySelector('#stage'),can=document.querySelector('#view'),ctx=can.getContext('2d');let yaw=.6,pitch=.5;
Object.keys(DATA.cases).forEach(k=>cs.add(new Option(k,k)));Object.keys(DATA.cases[cs.value]).forEach(k=>ms.add(new Option(k,k)));ms.value='M2';cs.value='S1';
function project(p){const x=Math.cos(yaw)*p[0]+Math.sin(yaw)*p[2],z=-Math.sin(yaw)*p[0]+Math.cos(yaw)*p[2];return[600+24*x,300-24*(Math.cos(pitch)*p[1]-Math.sin(pitch)*z),Math.sin(pitch)*p[1]+Math.cos(pitch)*z]}
function line(a,b,color){a=project(a);b=project(b);ctx.strokeStyle=color;ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke()}
function heat(e){let t=Math.min(1,Math.max(0,e));return 'rgb('+Math.round(35+220*t)+','+Math.round(160*(1-t))+','+Math.round(240*(1-t))+')'}
function draw(){ctx.clearRect(0,0,1200,760);const c=DATA.cases[cs.value][ms.value],stage=ss.value;let triangles=[];
function mesh(V,F,color,alpha,errors){const P=V.map(project);F.forEach(f=>{if(!P[f[0]]||!P[f[1]]||!P[f[2]])return;triangles.push({p:f.map(i=>P[i]),z:(P[f[0]][2]+P[f[1]][2]+P[f[2]][2])/3,color:errors?heat((errors[f[0]]+errors[f[1]]+errors[f[2]])/3):color,alpha});});}
if(document.querySelector('#body').checked)mesh(S.body.V,S.body.F,'#999999',.14);
if(document.querySelector('#ring').checked)mesh(S.ring.V,S.ring.F,'#161616',1);
['004','005'].forEach((v,j)=>{if(!document.querySelector(j?'#v5':'#v4').checked)return;const V=stage==='original'?S.clean[v].V:stage==='perturbed'||stage==='mediated'?c.input[v]:c.registered[v];if(V)mesh(V,S.clean[v].F,j?'#2474d2':'#dc293b',.82,stage==='gt'?c.errors[v]:null);});
triangles.sort((a,b)=>a.z-b.z).forEach(t=>{ctx.globalAlpha=t.alpha;ctx.fillStyle=t.color;ctx.beginPath();ctx.moveTo(t.p[0][0],t.p[0][1]);ctx.lineTo(t.p[1][0],t.p[1][1]);ctx.lineTo(t.p[2][0],t.p[2][1]);ctx.closePath();ctx.fill();});ctx.globalAlpha=1;
if(stage==='mediated')(c.anchors||[]).forEach(a=>a.P.forEach((p,i)=>line(p,a.Q[i],a.video==='004'?'#dd7680':'#7dafe9')));
if(document.querySelector('#truth').checked){S.truth.F.forEach((f,i)=>{if(i%3===0){line(S.truth.V[f[0]],S.truth.V[f[1]],'#57645c')}})}
[[[5,0,0],'#b32930','X'],[[0,5,0],'#16855d','Y'],[[0,0,5],'#255fc4','Z']].forEach(([p,col,n])=>{line([0,0,0],p,col);let q=project(p);ctx.fillStyle=col;ctx.fillText(n+' 5 mm',q[0],q[1])});
ctx.strokeStyle='#111';ctx.beginPath();ctx.moveTo(30,700);ctx.lineTo(270,700);ctx.stroke();ctx.fillStyle='#111';ctx.fillText('10 mm · fixed 24 px/mm · orthographic',30,725);
if(stage==='gt'){for(let i=0;i<180;i++){ctx.fillStyle=heat(i/179);ctx.fillRect(950+i,680,1,14)}ctx.fillStyle='#111';ctx.fillText('0        GT surface mm        1+',950,715)}
document.querySelector('#info').textContent=cs.value+' / '+ms.value+' / '+stage+'\n'+c.description+'\n004 '+S.clean['004'].V.length+' vertices / '+S.clean['004'].F.length+' triangles; 005 '+S.clean['005'].V.length+' vertices / '+S.clean['005'].F.length+' triangles\n'+JSON.stringify(c.metrics,null,2)+'\nActual estimated corrections (one SE3/video): '+JSON.stringify(c.corrections);}
[cs,ms,ss,...document.querySelectorAll('input')].forEach(x=>x.onchange=draw);document.querySelector('#front').onclick=()=>{yaw=0;pitch=0;draw()};document.querySelector('#side').onclick=()=>{yaw=Math.PI/2;pitch=0;draw()};document.querySelector('#top').onclick=()=>{yaw=0;pitch=Math.PI/2;draw()};document.querySelector('#reset').onclick=()=>{yaw=.6;pitch=.5;draw()};let last=null;can.onpointerdown=e=>{last=[e.clientX,e.clientY];can.setPointerCapture(e.pointerId)};can.onpointerup=()=>last=null;can.onpointermove=e=>{if(last){yaw+=(e.clientX-last[0])*.008;pitch+=(e.clientY-last[1])*.008;last=[e.clientX,e.clientY];draw()}};draw();</script></html>'''
    (attempt/'mesh_registration.html').write_text(page.replace('__DATA__',data))


def run(task,attempt):
    root=attempt.parents[1];ns=namespace(task);sc=task['sim'];metrics=json.loads(fetch(root,'G4_evaluate','REGISTRATION_METRICS.json').read_text());g1=json.loads(fetch(root,'G1_evaluate','G1_METRICS.json').read_text());g2=json.loads(fetch(root,'G2_evaluate','G2_METRICS.json').read_text());pred=json.loads(fetch(root,'G3_matrix_predict','PREDICTIONS_FROZEN.json').read_text());g0=json.loads(fetch(root,'G0_simulate','G0_SCENE_AUDIT.json').read_text())
    body=dict(np.load(fetch(root,'G1_initialize','FROZEN_BODY.npz')));ring=dict(np.load(fetch(root,'G0_simulate','public/canonical_ring.npz')));truth=dict(np.load(fetch(root,'G0_simulate','private/virtual_GT.npz')));gs=scene(truth['V'],truth['F'])
    clean={v:dict(np.load(fetch(root,'G0_simulate','private/'+v+'_clean.npz')))for v in ['004','005']};inj=json.loads(fetch(root,'G0_simulate','private/INJECTIONS.json').read_text());frames=json.loads(fetch(root,'G0_simulate','public/frame_index.json').read_text());fits=json.loads(fetch(root,'G1_initialize','IMAGE_FITS.json').read_text())
    lookup={(r['condition'],r['method']):r for r in metrics['rows']};cases={};failures=[]
    for p in pred['rows']:
        c,m=p['condition'],p['method'];row=lookup[c,m];inputs={v:np.load(fetch(root,'G0_simulate','public/conditions/'+c+'/'+v+'_mesh.npz'))['V']for v in clean};registered={};errors={}
        for v in clean:
            if p['status']=='NUMERIC':
                V=np.load(fetch(root,'G3_matrix_predict',c+'/'+m+'/'+v+'_registered.npz'))['V'];E4=np.asarray(p['corrections']['004'])@np.asarray(inj[c]['004']);gauged=transform(V,np.linalg.inv(E4));Q,_,_=closest(gs,gauged);registered[v]=V.tolist();errors[v]=np.linalg.norm(gauged-Q,axis=1).tolist()
            else:registered[v]=None;errors[v]=None
        desc='G01_LIKE_SIMULATION / SYNTHETIC_HERO_PROXY; world-family Camera-to-Ring invariant; Body frozen; complete original mesh topology retained.'
        if c=='L1':desc+=' Separate camera-local ablation: CAD Ring is fixed; 3D Ring-only prior cannot observe this local camera error.'
        cases.setdefault(c,{})[m]=dict(input={v:inputs[v].tolist()for v in inputs},registered=registered,errors=errors,anchors=p.get('details',{}).get('anchor_preview',[]),metrics=row,corrections=p.get('corrections'),description=desc)
        if row['status']!='NUMERIC'or not row.get('relative_pose_pass',False)or not row.get('optimizer_success',True):
            failures.append(dict(condition=c,method=m,category='scientific_negative'if row['status']=='NUMERIC'else'code_or_method_failure',status=row['status'],cause_status='observed_only',reason='Relative pose criterion not met and/or optimizer not converged'if row['status']=='NUMERIC'else row.get('reason'),relative_after=row.get('relative_after'),evidence='REGISTRATION_METRICS.json',automatic_rule_promotion=False))
    shared=dict(body={k:body[k].tolist()for k in ['V','F']},ring={k:ring[k].tolist()for k in ['V','F']},truth={k:truth[k].tolist()for k in ['V','F']},clean={v:{k:clean[v][k].tolist()for k in ['V','F']}for v in clean})
    interactive(attempt,shared,cases)
    save_json(attempt/'REGISTRATION_METRICS.json',metrics);save_json(attempt/'G1_METRICS.json',g1);save_json(attempt/'G2_METRICS.json',g2);save_json(attempt/'G0_SCENE_AUDIT.json',g0);save_json(attempt/'FAILURE_LEDGER.json',dict(scientific_failures=failures,no_failure_hidden=True,scientific_negative_is_not_code_defect=True))
    with(attempt/'REGISTRATION_METRICS.csv').open('w',newline='')as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(['condition','family','method','status','relative_rotation_before_deg','relative_translation_before_mm','relative_rotation_after_deg','relative_translation_after_mm','GT_surface_MAE_mm','GT_surface_p95_mm','common_visible_MAE_mm','pose_pass'])
        for r in metrics['rows']:
            before=r['relative_before'];after=r.get('relative_after')or{};surface=r.get('GT_surface_mm')or{};common=r.get('common_visible_consistency_mm')or{}
            writer.writerow([r['condition'],r['family'],r['method'],r['status'],before['rotation_deg'],before['translation_mm'],after.get('rotation_deg'),after.get('translation_mm'),surface.get('MAE'),surface.get('p95'),common.get('MAE'),r.get('relative_pose_pass',False)])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import Normalize
    cm=plt.get_cmap('turbo');norm=Normalize(0,1)
    (attempt/'figures').mkdir();figures={}
    def draw(ax,c,m,stage,view,arrows=False):
        case=cases[c][m]
        for V,F,color,alpha in [(body['V'],body['F'],'#aaaaaa',.12),(ring['V'],ring['F'],'#111111',.9)]:ax.add_collection3d(Poly3DCollection(V[F],facecolors=color,alpha=alpha,linewidths=0))
        for v,color in [('004','#d72d3f'),('005','#2374cd')]:
            V=clean[v]['V']if stage=='original'else np.array(case['input'][v])if stage in {'perturbed','mediated'}else np.array(case['registered'][v])if case['registered'][v]is not None else None
            if V is None:continue
            colors=color if stage!='gt'else cm(norm(np.asarray(case['errors'][v])[clean[v]['F']].mean(1)))
            ax.add_collection3d(Poly3DCollection(V[clean[v]['F']],facecolors=colors,alpha=.78,linewidths=0))
        if stage=='mediated':
            for anchor in case['anchors']:
                for a,b in zip(np.array(anchor['P'])[::6],np.array(anchor['Q'])[::6]):ax.plot(*np.array([a,b]).T,c='#bf754d',lw=.5)
        elev,az=view;ax.view_init(elev,az);ax.set(xlim=(-10,10),ylim=(-10,10),zlim=(-16,9),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.set_box_aspect([20,20,25]);ax.tick_params(labelsize=6)
    for name,view in [('front',(0,-90)),('side',(0,0)),('top',(90,-90))]:
        fig=plt.figure(figsize=(19,4.8),layout='constrained')
        for j,stage in enumerate(['original','perturbed','mediated','registered','gt']):
            ax=fig.add_subplot(1,5,j+1,projection='3d');draw(ax,'S1','M2',stage,view);ax.set_title(stage,fontsize=10)
        r=lookup['S1','M2'];after=r.get('relative_after')or{}
        fig.suptitle(f'S1 / M2 / {name} | 004 red, 005 blue, frozen Body gray, R10 black | G01_LIKE_SIMULATION\n005 injected +Ry2deg / +X0.5mm; actual relative after: {after.get("rotation_deg",float("nan")):.5f}deg / {after.get("translation_mm",float("nan")):.5f}mm; GT surface colors 0-1+mm',fontsize=10)
        fname='S1_M2_PIPELINE_'+name+'.png';fig.savefig(attempt/'figures'/fname,dpi=110);plt.close(fig);figures[fname]='Actual complete meshes, fixed metric views; error colors 0-1+mm'
    fig=plt.figure(figsize=(15,20),layout='constrained')
    for i,c in enumerate(['S0','S1','S2','S3','S4']):
        for j,m in enumerate(['M0','M1','M2','RING_ONLY']):
            ax=fig.add_subplot(5,4,i*4+j+1,projection='3d');draw(ax,c,m,'registered',(20,-65));r=lookup[c,m];e=r.get('relative_after')or{}
            ax.set_title(f'{c} / {m}: {e.get("rotation_deg",float("nan")):.3f}deg / {e.get("translation_mm",float("nan")):.3f}mm',fontsize=9)
    fig.suptitle('Full original mesh outputs / identical mm limits / 004 red, 005 blue / G01-like simulation',fontsize=12);fig.savefig(attempt/'figures/MATRIX_COMPLETE_MESHES.png',dpi=100);plt.close(fig);figures['MATRIX_COMPLETE_MESHES.png']='All primary conditions, actual complete registered local meshes'
    # Each video: a FIT frame and a HOLDOUT frame, including original true G01
    # masks and the synthetic image actually consumed by the predictor.
    for video in ['004','005']:
        for role in ['FIT','HOLDOUT']:
            frame=next(f for f in frames if f['video']==video and f['role']==role);cid=frame['id'];obs=np.load(fetch(root,'G0_simulate','public/initialization/'+cid+'.npz'));fit=next(f for f in fits if f['id']==cid and f['domain']=='synthetic');realfit=next(f for f in fits if f['id']==cid and f['domain']=='real_source')
            maps=np.load(fetch(root,'G2_mapping','maps/synthetic__'+cid+'__MEDIATED.npz'));direct=np.load(fetch(root,'G2_mapping','maps/synthetic__'+cid+'__DIRECT_PIXEL.npz'))
            fig,ax=plt.subplots(1,4,figsize=(17,4.7),layout='constrained')
            ax[0].imshow(obs['real_RGB']);realuv=contour(obs['real_labels']==1);ax[0].plot(realuv[:,0],realuv[:,1],'.',color='lime',ms=.3);ax[0].set_title('Real G01 source contour (unaltered)')
            ax[1].imshow(obs['RGB']);uv=contour(obs['labels']==1);ax[1].plot(uv[:,0],uv[:,1],'.',color='lime',ms=.3)
            t=np.linspace(0,2*np.pi,256);e=np.c_[np.cos(t),np.sin(t)]@np.asarray(fit['basis_px']).T+fit['center_px'];ax[1].plot(e[:,0],e[:,1],c='magenta',lw=.8);ax[1].set_title('Synthetic observed contour + '+fit['mapping_fit'],fontsize=9)
            ax[2].imshow(obs['RGB']);curve=maps['body_curve'];ax[2].plot(curve[:,0],curve[:,1],c='gray',lw=1,label='Frozen Body projection')
            good=maps['valid'];u=maps['original_uv'];q=maps['mapped_uv'];ax[2].quiver(u[:,0],u[:,1],q[:,0]-u[:,0],q[:,1]-u[:,1],color='orange',angles='xy',scale_units='xy',scale=1,width=.002);ax[2].scatter(q[~good,0],q[~good,1],c='magenta',s=12,label='Unmatched');ax[2].legend(fontsize=6);ax[2].set_title(f'Mediated warp: {good.sum()}/{len(good)} candidates')
            ax[3].imshow(obs['RGB']);scatter=ax[3].scatter(q[good,0],q[good,1],c=maps['face'][good],s=12,cmap='tab20');ax[3].scatter(q[~good,0],q[~good,1],c='magenta',marker='x');ax[3].set_title(f'Actual Body Face IDs; direct hits {direct["valid"].sum()}/{len(good)}')
            for a in ax:a.set(xlim=(0,639),ylim=(359,0),xlabel='native x [px]',ylabel='native y [px]')
            fig.suptitle(f'{frame["source_id"]} | {role} | no injected error for mapping diagnostic | source pose {frame["pose_sha256"][:12]}\nCandidate XYZ / Face / barycentric / confidence / contact-unknown and failure arrays retained in G2 outputs. Neither plot is a physical correction.',fontsize=9)
            fname=video+'_'+role+'_PIXEL_BODY_CORRESPONDENCE.png';fig.savefig(attempt/'figures'/fname,dpi=100);plt.close(fig);figures[fname]='Original real contour, actual synthetic observations, fitted ellipse and nontrivial Body warp'
    # Actual metric curves preserve every method, including failure/negative arms.
    fig,axes=plt.subplots(1,3,figsize=(16,4.8),layout='constrained');conds=['S0','S1','S2','S3','S4']
    for m in sc['methods']:
        rr=[lookup[c,m]for c in conds]
        for ax,key in zip(axes,['rotation_deg','translation_mm','surface']):
            vals=[r.get('GT_surface_mm',{}).get('MAE',np.nan)if key=='surface'and r.get('GT_surface_mm')else(r.get('relative_after')or{}).get(key,np.nan)for r in rr]
            ax.plot(conds,vals,'o-',label=m,ms=3)
    for ax,title in zip(axes,['Relative rotation [deg]','Relative translation [mm]','004-gauge GT surface MAE [mm]']):ax.set_title(title);ax.grid(alpha=.2)
    axes[0].legend(fontsize=7);fig.suptitle('Actual frozen-method results; Ring-only is an independent explanatory control, no GT selection');fig.savefig(attempt/'figures/ACTUAL_METRICS.png',dpi=120);plt.close(fig);figures['ACTUAL_METRICS.png']='Actual all-method numerical results; S4 common gauge retained'
    save_json(attempt/'FIGURES.json',figures)
    summary_by_method={m:dict(primary_target_conditions=5,independent_numeric=sum(lookup[c,m]['status']=='NUMERIC'for c in conds),relative_pose_pass=sum(lookup[c,m].get('relative_pose_pass',False)for c in conds))for m in sc['methods']}
    report=f"# {task['task_id']}\n\nG01_LIKE_SIMULATION / SYNTHETIC_HERO_PROXY。G0–G4已实际执行；科学结果等待人工审阅。真实性为质量指标，内部几何/坐标/GT权限失败仍阻断。历史G0失败和冻结文件完整保留。\n\n"
    report+='[离线首页](visualization/index.html) · [完整曲面五阶段交互](visualization/mesh_registration.html) · [全部指标](visualization/REGISTRATION_METRICS.json) · [失败台账](visualization/FAILURE_LEDGER.json)\n\n'
    report+='## 来源、固定协议与角色隔离\n\n真实004/005各自原生Camera-to-Ring和33帧分区原样继承（25 FIT、8 HOLDOUT）；统一虚拟R10坐标系为明确的仿真假设，不宣称两真实视频已认证共同世界。原始G01 Blender形状不缩放；仅按冻结FIT轮廓规则选择一个共享静态平移。置放候选、分数、CAD尺度和逐帧射线/PyTorch3D独立检查见G0审计。\n\n'
    report+=f"静态摆放：{g0['placement'][g0['selected']]['translation_mm']}mm，旋转I，缩放1。原图Ring投影差异继续记录，不再阻断。所有受试网格为完整可见原始三角形并集，不是实际HERO输出；未平滑、未投到Body、未替换观测点。\n\n"
    report+='S0 I/I；S1 I/A；S2 I/B；S3 A/B；S4 A/A（004/005）。A=+Ry2°、+X0.5mm；B=+Ry3°、+X0.3mm；旋转中心Ring原点，世界左乘，种子20261116。相机/Ring/局部Mesh共同变换，段内相对相机及Camera-to-Ring不变；独立L1仅005相机局部A、CAD固定，不与主矩阵混合。\n\n'
    report+='G0 generator可读GT，G1/G2/G3 predictor拒绝GT和评价目录；G3额外拒绝干净相机目录及G2干净三维锚点，必须用实际受扰相机重算对应。Body与预测先SHA冻结，G1/G2/Smoke/G4独立evaluator才读GT。任何方法不收敛或误差大均保留，不使用其他方法补值。\n\n'
    report+='## 独立Body初始化\n\n复用T01/T03正式像素API、T04椭圆basis约定、T05九参数模型、T06/T07解析投影及完整Mask损失、T08原样三初值TRF、T09的2D-only策略。没有整体导入历史含HERO深度的Problem。二维参数只来自当前观测；固定FIT优先次序E1→E2→显式代理，不依据GT选择。\n\n'
    report+=f"选用Body臂：{g1['selected_arm']}。各臂多初值、数值/收敛状态、轮廓误差、Ring穿透代理及独立GT表面误差详见[G1指标](visualization/G1_METRICS.json)。隐藏表面是椭球先验推断，不冒充可观测轮廓。\n\n"
    report+='## 二维中介与真正曲面配准\n\n中介以观察椭圆的规范化坐标映射到Body投影椭圆，再求可见Face/重心和候选区域，径向收缩0.97用于切线邻域诊断；其查询像素一般不同于原像素。直接原像素Pixel-to-Face单独对照。Ring接触切边保留为物理轮廓未知、零置信度；未匹配点NaN且保留全分母。实际原始/映射像素、Face、重心、XYZ、basis和置信度在每帧G2冻结数组中。真实原图轮廓亦单独映射，但GT只是假定G01-like虚拟射线诊断，不是对真实物理对应的认证。\n\n'
    report+='M0不修正；M1 Open3D Tukey Robust ICP（固定004，估计005）；M2每视频共享6参数，联合二维中介三维锚点、Body轮廓和鲁棒局部曲面几何；M2_DIRECT改用直接像素；M2_RING加入Ring中心/法向约束。RING_ONLY只用未标记3D CAD的中心/法向，绕Ring法向的扭转不可观察，采用最小扭转规范。主扰动为Y倾斜，可由Ring直接解释；其恢复不能归功于二维Body。L1中3D CAD先验固定，因此此Ring-only对照本身不观察局部相机误差。\n\n'
    report+='所有实际修正作用于完整原网格全部顶点，Face拓扑与边长断言验证；优化可抽样约束点，输出和可视化始终是完整曲面。Body保持冻结。S4共有世界误差属于规范自由度，评价同时给绝对GT误差和004规范对齐后的误差，主要位姿指标为(E004)^-1 E005。不能仅由两曲面间距离判定成功。\n\n'
    report+='## 全部实测条件\n\n| Condition | Method | Numeric | Rel rot before→after deg | Rel trans before→after mm | GT surface MAE / p95 mm | Common-visible MAE mm | Pose criterion |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for r in metrics['rows']:
        a=r.get('relative_after')or{};b=r['relative_before'];s=r.get('GT_surface_mm')or{};q=r.get('common_visible_consistency_mm')or{}
        fmt=lambda x:'NaN'if x is None else f'{x:.6f}'
        report+=f"| {r['condition']} | {r['method']} | {r['status']} | {fmt(b['rotation_deg'])}→{fmt(a.get('rotation_deg'))} | {fmt(b['translation_mm'])}→{fmt(a.get('translation_mm'))} | {fmt(s.get('MAE'))} / {fmt(s.get('p95'))} | {fmt(q.get('MAE'))} | {r.get('relative_pose_pass',False)} |\n"
    report+='\n逐视频曲面MAE/中位数/p95/最大值、可见材料点一致性、0.1mm覆盖、完整目标顶点数及8帧HOLDOUT投影误差均在JSON内。直径MAE/相对直径误差N/A：本任务评价对应与配准，不产生直径测量。所有方法有共同分母，失败留NaN，不只统计成功条件。\n\n'
    report+='## 数值覆盖与科学通过的区别\n\n| Method | Primary targets | Independent numeric | Relative pose criterion pass |\n| --- | ---: | ---: | ---: |\n'
    for m,s in summary_by_method.items():report+=f"| {m} | 5 | {s['independent_numeric']} | {s['relative_pose_pass']} |\n"
    report+='\nL1单列不混入主条件分母。优化器未收敛、Body失配和对应偏差均为真实负结果，见失败台账；未自动晋升永久规则。Smoke先执行S0/S1并独立核验实际全Mesh扰动、相机相对不变和优化导致真实顶点位移，再扩展完整矩阵。\n\n'
    report+='## 固定审计表\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | G01-like静态场景1；5主条件、独立L1；每条件2视频；25 FIT / 8 HOLDOUT |\n| 本算法独立成功 | 每方法数值输出与位姿正确性分别见上表，不等同 |\n| 本算法失败 | 每方法/条件负结果及NaN保留；见FAILURE_LEDGER.json |\n| 历史测量值回退 | 0 |\n| 失败组及具体原因 | 每条件、方法、阶段和关联真实指标/图均保留 |\n| 最终统计样本 | 每方法全体5主条件分母，L1单列；共同成功条件可配对，无历史融合 |\n| 是否使用 GT 选择算法 | 否；参数/TASK/源码先冻结，Body先冻结，GT仅生成与独立后验评价 |\n\n'
    report+='## 可视化与实际修正\n\n'
    for name,caption in figures.items():report+=f'- [{name}](visualization/figures/{name})：{caption}\n'
    report+='\n完整估计变换、优化trace、每视频最大实际顶点位移和完整网格输出均在G3预测冻结产物中。交互HTML包含所有条件/方法的原始、错层、候选、实际配准、GT阶段，可直接离线打开。所有静态3D图使用相同毫米范围和0–1+mm色标，超过色标的实际误差未从数值表裁剪。\n'
    (attempt/'TECHNICAL_REPORT.md').write_text(report)
    (attempt/'RESULT_CARD.md').write_text(f"# SIM_PROTOCOL_REV1\n\nG0–G4实际执行；G01_LIKE_SIMULATION / SYNTHETIC_HERO_PROXY，等待人工科学审阅。\n\n独立Body={g1['selected_arm']}；历史回退0；Body冻结；完整Mesh共享刚体配准。\n\n"+'\n'.join(f"- {m}: 数值{s['independent_numeric']}/5，位姿门限{s['relative_pose_pass']}/5"for m,s in summary_by_method.items())+'\n\n[报告](TECHNICAL_REPORT.md) · [完整Mesh交互](visualization/mesh_registration.html) · [首页](visualization/index.html) · [失败台账](visualization/FAILURE_LEDGER.json)\n')
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>SIM_PROTOCOL_REV1 scientific review</title><style>body{font:16px system-ui;max-width:1450px;margin:30px auto;background:#f5f7fa;color:#172237}img{max-width:100%}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:6px}a{color:#205bb0}</style><h1>G01-like 双视频完整曲面配准</h1><p>G01_LIKE_SIMULATION · SYNTHETIC_HERO_PROXY；所有输出来自实际冻结运行，未认证真实部署。数值输出与科学正确性分开统计。</p><p><a href="mesh_registration.html">打开完整曲面五阶段交互</a> · <a href="../TECHNICAL_REPORT.md">技术报告</a> · <a href="../RESULT_CARD.md">结果卡</a> · <a href="../RUN_MANIFEST.json">运行清单</a> · <a href="REGISTRATION_METRICS.csv">完整数值CSV</a> · <a href="FAILURE_LEDGER.json">失败台账</a></p>'
    page+='<svg viewBox="0 0 900 35"><text x="0" y="23">G0 simulation → G1 independent Body → G2 mediated candidates → S0/S1 Smoke → G3 full Mesh → G4 evaluation</text></svg><p>Below historical engineering evidence is explicitly separate from current scientific figures.</p><details><summary>历史工程回归输入（非本轮结果）</summary><img src="../evidence.png" alt="Historical engineering reference only"></details>'
    page+='<p>实际局部Mesh：004 '+str(len(clean['004']['V']))+' 顶点/'+str(len(clean['004']['F']))+' 三角面；005 '+str(len(clean['005']['V']))+' 顶点/'+str(len(clean['005']['F']))+' 三角面。Body未更新。未匹配区域、GT不评价区域、局部相机消融及失败方法均保留。</p>'
    for name,caption in figures.items():page+=f'<h2>{html.escape(caption)}</h2><img loading="lazy" src="figures/{name}" alt="{html.escape(caption)}">'
    page+='<p><a href="G0_SCENE_AUDIT.json">场景真实性/内部核验</a> · <a href="G1_METRICS.json">初始化与HOLDOUT</a> · <a href="G2_METRICS.json">对应覆盖/错误/配对</a> · <a href="REGISTRATION_METRICS.json">独立GT评价全部指标</a></p></html>'
    (attempt/'index.html').write_text(page)
    return outputs(attempt,dict(status='PASS',role='evaluator',figures=figures,summary_by_method=summary_by_method,scientific_failures=failures,complete_mesh_interactive=True,GT_read_by_visualizer=True))
