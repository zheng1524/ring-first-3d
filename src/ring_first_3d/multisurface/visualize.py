"""Exact mesh-cut main figures and offline per-video/per-view full-mesh WebGL."""
import csv,html,json
import numpy as np
from pathlib import Path
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import require
from .geometry import mesh_sections,mesh_section_faces,plane_coordinates,point_segment_distance,transform


def plain_mesh(mesh):return dict(V=np.asarray(mesh['V']).round(5).tolist(),F=np.asarray(mesh['F']).tolist())


def viewer(attempt,shared,packets):
    save=(attempt/'data.js');save.write_text('window.MF_SHARED='+json.dumps(shared,separators=(',',':'))+';window.MF_CASES={};\n')
    (attempt/'cases').mkdir()
    for key,data in packets.items():(attempt/'cases'/(key+'.js')).write_text('window.MF_CASES['+json.dumps(key)+']='+json.dumps(data,separators=(',',':'))+';\n')
    page=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Independent multisurface + Body fusion</title><style>body{font:15px system-ui;margin:22px;background:#f5f7fa;color:#162334}canvas{max-width:1200px;width:100%;background:white;touch-action:none}select,button{padding:7px;margin:3px}#views{max-width:1200px;display:flex;flex-wrap:wrap;gap:7px;font-size:12px}pre{white-space:pre-wrap}a{color:#225db0}</style>
<h1>16独立深度栅格曲面 + 冻结Body + GT切面审阅</h1><p>G01_LIKE_SIMULATION / INDEPENDENT_DEPTH_GRID_SYNTHETIC_HERO_PROXY。红004、蓝005、紫融合、灰Body、黑GT。真实三角网格；不优化相机、不将观测点替换为椭球表面。5位小数仅为浏览器显示，评价使用完整精度。</p>
<label>条件<select id="condition"></select></label><label>Body<select id="arm"><option>E1</option><option>E2</option></select></label><label>方法<select id="method"><option>M0</option><option>ICP</option><option>BODY_VIDEO</option><option selected>BODY_HIER</option></select></label><label>容差mm<select id="tol"><option>0</option><option selected>0.5</option><option>1</option></select></label><label>阶段<select id="stage"><option value="before">配准前</option><option value="after" selected>配准后</option><option value="fusion">整体融合</option><option value="evaluation">GT评价</option></select></label>
<button id="front">正面</button><button id="side">侧面</button><button id="top">俯视</button><button id="oblique">斜视</button>
<p><label><input id="video004" type="checkbox" checked>004全部</label> <label><input id="video005" type="checkbox" checked>005全部</label> <label><input id="showbody" type="checkbox" checked>Body灰色</label> <label><input id="showgt" type="checkbox" checked>GT黑色网格线</label> <label><input id="showring" type="checkbox" checked>物理Ring</label> <label><input id="showfused" type="checkbox" checked>融合紫色</label></p><div id="views"></div>
<div style="position:relative;max-width:1200px"><canvas id="view" width="1200" height="760" style="display:block"></canvas><svg viewBox="0 0 1200 760" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none"><line x1="30" x2="270" y1="705" y2="705" stroke="black" stroke-width="2"/><text x="30" y="735">10 mm · fixed orthographic scale</text></svg></div><pre id="info"></pre><p>固定正交毫米尺度；拖动旋转。每视角开关只控制显示，不改变任何预测。</p><p><a href="index.html">主报告首页与真实切面</a> · <a href="MODEL_METRICS.json">整体指标</a> · <a href="REGISTRATION_METRICS.json">材料点及重叠指标</a> · <a href="FAILURE_LEDGER.json">失败台账</a></p>
<script src="data.js"></script><script src="cases/C3_E1.js"></script><script>
const S=window.MF_SHARED,cs=document.querySelector('#condition'),as=document.querySelector('#arm'),ms=document.querySelector('#method'),ts=document.querySelector('#tol'),ss=document.querySelector('#stage'),can=document.querySelector('#view'),gl=can.getContext('webgl',{preserveDrawingBuffer:true,alpha:false});let yaw=.6,pitch=.4;
S.conditions.forEach(k=>cs.add(new Option(k,k)));cs.value='C3';let checks={};S.frames.forEach((f,i)=>{let label=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.checked=true;box.onchange=draw;checks[f.id]=box;label.append(box,document.createTextNode(f.video+'/'+f.id));document.querySelector('#views').append(label)});
function shader(type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec3 position;uniform mat4 model;uniform mat4 view;varying float shade;void main(){vec4 p=view*model*vec4(position,1.0);shade=0.8+0.15*p.z/20.0;gl_Position=vec4(p.x*0.04,p.y*0.0631579,-p.z/100.0,1.0);}'));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,'precision mediump float;uniform vec4 color;varying float shade;void main(){gl_FragColor=vec4(color.rgb*shade,color.a);}'));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
const pos=gl.getAttribLocation(program,'position'),modelLoc=gl.getUniformLocation(program,'model'),viewLoc=gl.getUniformLocation(program,'view'),colorLoc=gl.getUniformLocation(program,'color');gl.enableVertexAttribArray(pos);gl.enable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);let buffers=new Map();
function matrix(a){return new Float32Array([a[0][0],a[1][0],a[2][0],a[3][0],a[0][1],a[1][1],a[2][1],a[3][1],a[0][2],a[1][2],a[2][2],a[3][2],a[0][3],a[1][3],a[2][3],a[3][3]])}
const I=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]];function mul(a,b){return a.map((r,i)=>r.map((_,j)=>r.reduce((z,v,k)=>z+v*b[k][j],0)))}
function mesh(data,key,T,color,wire=false){let B=buffers.get(key+(wire?'wire':''));if(!B){let indices=wire?data.F.flatMap(f=>[f[0],f[1],f[1],f[2],f[2],f[0]]):data.F.flat();if(data.V.length>65535)throw Error('Unexpected mesh index size');B={v:gl.createBuffer(),f:gl.createBuffer(),N:indices.length};gl.bindBuffer(gl.ARRAY_BUFFER,B.v);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data.V.flat()),gl.STATIC_DRAW);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,B.f);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(indices),gl.STATIC_DRAW);buffers.set(key+(wire?'wire':''),B)}gl.bindBuffer(gl.ARRAY_BUFFER,B.v);gl.vertexAttribPointer(pos,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,B.f);gl.uniformMatrix4fv(modelLoc,false,matrix(T));gl.uniform4fv(colorLoc,color);gl.drawElements(wire?gl.LINES:gl.TRIANGLES,B.N,gl.UNSIGNED_SHORT,0)}
function draw(){const key=cs.value+'_'+as.value,p=window.MF_CASES[key];if(!p){let script=document.createElement('script');script.src='cases/'+key+'.js';script.onload=draw;script.onerror=()=>document.querySelector('#info').textContent='Missing case data: '+key;document.head.append(script);return}const result=p.results[ms.value+'|'+Number(ts.value)];gl.viewport(0,0,1200,760);gl.clearColor(1,1,1,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);let cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);let V=[[cy,sy,0,0],[-sy*sp,cy*sp,cp,4*cp],[sy*cp,-cy*cp,sp,4*sp],[0,0,0,1]];gl.uniformMatrix4fv(viewLoc,false,matrix(V));
if(document.querySelector('#showbody').checked){gl.depthMask(false);mesh(S.bodies[as.value],'body'+as.value,I,[.55,.55,.55,.2]);gl.depthMask(true)}if(document.querySelector('#showring').checked)mesh(S.ring,'ring',I,[.08,.08,.08,1]);
let shown=0;S.frames.forEach((f,i)=>{if(!checks[f.id].checked||!document.querySelector('#video'+f.video).checked)return;let T=p.poses[f.id];if(ss.value!=='before'){if(!result||!result.corrections)return;T=mul(result.corrections[f.id],T)}const c=f.video==='004'?[.82,.10,.18,.44]:[.08,.33,.85,.44];gl.depthMask(false);mesh(S.meshes[f.id],f.id,T,c);gl.depthMask(true);shown++});
if(['fusion','evaluation'].includes(ss.value)&&document.querySelector('#showfused').checked&&result&&result.fused)mesh(result.fused,key+ms.value+ts.value+'fused',I,[.57,.15,.72,.8]);if(document.querySelector('#showgt').checked){gl.disable(gl.DEPTH_TEST);mesh(S.GT,'GT',I,[.02,.02,.02,.65],true);gl.enable(gl.DEPTH_TEST)}
document.querySelector('#info').textContent=key+' / '+ms.value+' / tolerance '+ts.value+'mm / '+ss.value+'\nComplete independent surfaces shown: '+shown+'/16\n'+(result?JSON.stringify(result.summary,null,2):'NOT_RUN: this ablation was not run; no fallback prediction')+'\nCamera files frozen; only surface rigid corrections applied. Mesh ownership conflicts and missing sections are retained.';}
[cs,as,ms,ts,ss,...document.querySelectorAll('p input')].forEach(c=>c.onchange=draw);document.querySelector('#front').onclick=()=>{yaw=0;pitch=0;draw()};document.querySelector('#side').onclick=()=>{yaw=Math.PI/2;pitch=0;draw()};document.querySelector('#top').onclick=()=>{yaw=0;pitch=Math.PI/2;draw()};document.querySelector('#oblique').onclick=()=>{yaw=.6;pitch=.4;draw()};let last=null;can.onpointerdown=e=>{last=[e.clientX,e.clientY];can.setPointerCapture(e.pointerId)};can.onpointerup=()=>last=null;can.onpointermove=e=>{if(last){yaw+=(e.clientX-last[0])*.008;pitch+=(e.clientY-last[1])*.008;last=[e.clientX,e.clientY];draw()}};draw();</script></html>'''
    (attempt/'multisurface_3d.html').write_text(page)


def run(task,attempt):
    root=attempt.parents[1];cfg=task['fusion'];frames=[r for r in json.loads(fetch(root,'G0_views_noise','public/FRAME_INDEX.json').read_text())if r['role']=='FIT']
    registrations=json.loads(fetch(root,'G4_evaluate','REGISTRATION_METRICS.json').read_text());models=json.loads(fetch(root,'G4_evaluate','MODEL_METRICS.json').read_text());failure=json.loads(fetch(root,'G4_evaluate','FAILURE_LEDGER.json').read_text());noise=json.loads(fetch(root,'G4_evaluate','NOISE_AUDIT.json').read_text());pred=json.loads(fetch(root,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text());fusion=json.loads(fetch(root,'G4_fusion_predict','FUSION_FROZEN.json').read_text())
    reg={r['key']:r for r in registrations['rows']};met={r['key']:r for r in models['models']};pb={r['key']:r for r in pred['rows']};fb={r['key']:r for r in fusion['rows']};body={a:dict(np.load(fetch(root,'G1_body',a+'_BODY.npz')))for a in cfg['body_arms']};GT=dict(np.load(fetch(root,'G0_views_noise','private/GT_SCENE.npz')));ring=dict(np.load(fetch(root,'G0_views_noise','public/FIXED_RING.npz')))
    shared=dict(frames=frames,conditions=cfg['condition_order'],bodies={a:plain_mesh(b)for a,b in body.items()},GT=plain_mesh(GT),ring=plain_mesh(ring),meshes={r['id']:plain_mesh(np.load(fetch(root,'G0_views_noise','public/camera_meshes/'+r['id']+'.npz')))for r in frames})
    packets={};all_models={};all_surfaces={};completion_masks={}
    for cond in cfg['condition_order']:
        poses={r['id']:r['estimated_C']for r in json.loads(fetch(root,'G0_views_noise','public/conditions/'+cond+'/ESTIMATED_POSES.json').read_text())}
        for arm in cfg['body_arms']:packets[cond+'_'+arm]=dict(poses=poses,results={})
    for r in pred['rows']:
        key=r['key'];model=None
        if fb[key]['status']=='NUMERIC':
            model=dict(np.load(fetch(root,'G4_fusion_predict',key+'/FUSED_MODEL.npz')));all_models[key]=model
            own=np.load(fetch(root,'G4_fusion_predict',key+'/SURFACE_OWNERSHIP.npz'));completion_masks[key]=own['face_completion']
        if r['status']=='NUMERIC':all_surfaces[key]=[dict(np.load(fetch(root,'G3_all_predict',key+'/'+f['id']+'.npz')))for f in frames]
        packets[r['condition']+'_'+r['arm']]['results'][r['method']+'|'+str(r['tolerance_mm']).rstrip('0').rstrip('.')]=dict(corrections=r.get('surface_corrections'),fused=plain_mesh(model)if model else None,
            summary=dict(status=r['status'],material_MAE_mm=reg[key]['mean_frame_material_MAE_mm'],model_bidirectional_mm=met[key].get('bidirectional_mm'),GT_unique_coverage=met[key].get('GT_unique_coverage'),ownership=fb[key],no_GT_alignment=True))
    # Numeric JS keys: Python 0.0 must become "0", while 0.5 stays "0.5".
    for p in packets.values():
        p['results']={k if not k.endswith('|')else k+'0':v for k,v in p['results'].items()}
    viewer(attempt,shared,packets)
    for name,data in [('REGISTRATION_METRICS.json',registrations),('MODEL_METRICS.json',models),('FAILURE_LEDGER.json',failure),('NOISE_AUDIT.json',noise),('GENERATION_AUDIT.json',json.loads(fetch(root,'G0_views_noise','GENERATION_AUDIT.json').read_text()))]:save_json(attempt/name,data)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.colors import Normalize
    (attempt/'figures').mkdir();figures={};cut_cache={}
    def segments(mesh,axis,off,cachekey):
        key=(cachekey,axis,off)
        if key not in cut_cache:cut_cache[key]=plane_coordinates(mesh_sections(mesh['V'],mesh['F'],axis,off),axis)
        return cut_cache[key]
    raw={c:[dict(np.load(fetch(root,'G0_views_noise','public/conditions/'+c+'/'+r['id']+'.npz')))for r in frames]for c in cfg['condition_order']}
    def add(ax,seg,color,lw=1.,alpha=1.,dashed=False):
        if len(seg):ax.add_collection(LineCollection(seg,colors=color,linewidths=lw,alpha=alpha,linestyles=(0,(2,2))if dashed else'solid'))
    def main_figure(cond,arm,method,filename):
        key=f'{cond}__{arm}__{method}__tol0.5';post=all_surfaces.get(key,[]);fused=all_models.get(key);fig,axes=plt.subplots(4,4,figsize=(18,19),layout='constrained')
        for row,spec in enumerate(cfg['sections']):
            axis,off=spec['axis'],spec['offset_mm'];gtseg=segments(GT,axis,off,'GT');bseg=segments(body[arm],axis,off,'body'+arm);fseg=segments(fused,axis,off,key+'fused')if fused is not None else np.empty((0,2,2))
            for col,stage in enumerate(['Before registration','After surface correction','Body + owned fusion','Independent GT evaluation']):
                ax=axes[row,col];add(ax,bseg,'#8b8b8b',1.1,.9,True)
                surfaces=raw[cond]if col==0 else post
                for i,m in enumerate(surfaces):add(ax,segments(m,axis,off,(cond,'raw',i)if col==0 else(key,'post',i)),'#d82439'if frames[i]['video']=='004'else'#1c66d4',.65,.48)
                if col>=2:
                    add(ax,fseg,'#9226b0',1.7,.96)
                    if fused is not None:
                        ss,faceids=mesh_section_faces(fused['V'],fused['F'],axis,off);ss=plane_coordinates(ss,axis);completion=completion_masks[key][faceids]
                        add(ax,ss[completion],'#df7eea',2.,.9,True)
                if col==3 and len(fseg)and len(gtseg):
                    mid=fseg.mean(1);err=point_segment_distance(mid,gtseg);ax.add_collection(LineCollection(fseg,colors=plt.get_cmap('magma')(Normalize(0,1)(err)),linewidths=5,alpha=.35,zorder=0));add(ax,fseg,'#9226b0',1.05)
                    missing=point_segment_distance(gtseg.mean(1),fseg)>cfg['coverage_threshold_mm'];add(ax,gtseg[missing],'#e7b72e',5.,.6)
                elif col==3 and len(gtseg):add(ax,gtseg,'#e7b72e',5.,.6)
                add(ax,gtseg,'black',1.5)
                axes_names=[j for j in range(3)if j!=axis];ax.set(xlim=(-12,12),ylim=(-18,8)if axis in [0,1]else(-12,12),xlabel='XYZ'[axes_names[0]]+' [mm]',ylabel='XYZ'[axes_names[1]]+' [mm]');ax.set_aspect('equal');ax.grid(alpha=.15)
                title=stage if row==0 else'';ax.set_title(title,fontsize=10);ax.text(.02,.98,f'{"XYZ"[axis]}={off:g} mm | actual triangles\nGT {len(gtseg)} / full local segments {sum(len(segments(m,axis,off,(cond,"raw",i)if col==0 else(key,"post",i)))for i,m in enumerate(surfaces))}',transform=ax.transAxes,ha='left',va='top',fontsize=7)
                if col==3:
                    sm=next((r for r in met[key].get('sections',[])if r['axis']==axis and r['offset_mm']==off),None)
                    if sm:ax.text(.02,.02,f'GT->fusion MAE={sm["GT_to_model_mm"]["MAE"] if sm["GT_to_model_mm"]["MAE"]is not None else "NaN"}\nP95={sm["GT_to_model_mm"]["p95"] if sm["GT_to_model_mm"]["p95"]is not None else "NaN"}',transform=ax.transAxes,fontsize=7)
            if not post:axes[row,1].text(0,-3,'FAILED / NO PREDICTION',color='red')
        sigma=cfg['conditions'][cond]['sigma'];bias=cfg['conditions'][cond]['bias'];fig.suptitle(f'{cond} / {arm} / {method} | black GT, dashed gray Body, all 004 red / 005 blue, purple fusion; pale purple dash=completion, yellow=unmatched GT >0.2mm\nBias {bias}; local zero-mean noise sigma R/t {sigma}; no GT rigid alignment | G01-like independent axial-depth-grid HERO Proxy\nEvery local Mesh is cut by actual triangle/plane intersections, never sampled/averaged contours; shaded errors fixed 0-1+mm',fontsize=10)
        fig.savefig(attempt/'figures'/filename,dpi=105);plt.close(fig);figures[filename]=f'{cond}/{arm}/{method}: four fixed actual Mesh sections, all independent local surfaces'
    main_figure('C3','E1','BODY_HIER','01_MAIN_MULTISURFACE_SECTIONS.png')
    for cond in ['C0','C1','C2','C4','C5']:main_figure(cond,'E1','BODY_HIER',cond+'_MULTISURFACE_SECTIONS.png')
    main_figure('C3','E2','BODY_HIER','C3_E2_MULTISURFACE_SECTIONS.png')
    # Quantitative all-method comparisons, not a post-GT chosen winner.
    fig,axes=plt.subplots(2,2,figsize=(14,9),layout='constrained')
    for arm,axs in zip(cfg['body_arms'],axes):
        for method in cfg['methods']:
            keys=[f'{c}__{arm}__{method}__tol0.5'for c in cfg['condition_order']]
            axs[0].plot(cfg['condition_order'],[reg[k]['mean_frame_material_MAE_mm']for k in keys],'o-',label=method)
            axs[1].plot(cfg['condition_order'],[(met[k].get('bidirectional_mm')or{}).get('MAE',np.nan)for k in keys],'o-',label=method)
        baseline=next(b for b in models['body_only']if b['arm']==arm and b['model']=='BODY_ONLY_MATCHED_CHART');axs[1].axhline(baseline['bidirectional_mm']['MAE'],ls='--',c='gray',label='Body-only matched chart')
        axs[0].set_title(arm+' all-material-point MAE [mm]');axs[1].set_title(arm+' whole-model bidirectional GT MAE [mm]')
        for ax in axs:ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('Fixed denominators; C0/low/no-noise/dual/high/pure-noise controls; all methods retained');fig.savefig(attempt/'figures/ALL_METHOD_METRICS.png',dpi=120);plt.close(fig);figures['ALL_METHOD_METRICS.png']='All main conditions, both Body initializers and four methods'
    # Surface Ownership Map audit for the preregistered first-figure result.
    mainkey='C3__E1__BODY_HIER__tol0.5'
    with(attempt/'SURFACE_OWNERSHIP_MAIN.csv').open('w',newline='')as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(['vertex','X_mm','Y_mm','Z_mm','owner_view','video','source_face','bary0','bary1','bary2','conflict','radial_spread_mm','reason'])
        if mainkey in all_models:
            own=np.load(fetch(root,'G4_fusion_predict',mainkey+'/SURFACE_OWNERSHIP.npz'));mesh=all_models[mainkey]
            for i,P in enumerate(mesh['V']):
                owner=int(own['owner'][i]);writer.writerow([i,*P,frames[owner]['id']if owner>=0 else'BODY',frames[owner]['video']if owner>=0 else'COMPLETION',int(own['selected_source_face'][i]),*own['selected_source_bary'][i],bool(own['conflict'][i]),float(own['spread_mm'][i]),str(own['reason'][i])])
    with(attempt/'ALL_CONDITION_METRICS.csv').open('w',newline='')as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(['key','condition','arm','method','kind','tol_mm','material_MAE_mm','GT_bidirectional_MAE_mm','GT_bidirectional_P95_mm','unique_GT_coverage','improves_Body','conflict_vertices','rejected_seam_faces'])
        for r in pred['rows']:
            key=r['key'];m=met[key];ss=m.get('bidirectional_mm')or{};owner=m.get('ownership_summary')or{}
            writer.writerow([key,r['condition'],r['arm'],r['method'],r['kind'],r['tolerance_mm'],reg[key]['mean_frame_material_MAE_mm'],ss.get('MAE'),ss.get('p95'),m.get('GT_unique_coverage'),m.get('improves_Body_bidirectional_MAE'),owner.get('overlap_conflict_vertices'),owner.get('seam_triangles_rejected')])
    scientific_summary={}
    for arm in cfg['body_arms']:
        for method in cfg['methods']:
            rr=[r for r in models['models']if r.get('arm')==arm and r.get('method')==method and r.get('kind')=='MAIN'];scientific_summary[arm+'/'+method]=dict(target_conditions=6,numeric=sum(r['status']=='NUMERIC'for r in rr),improved_body_MAE=sum(r.get('improves_Body_bidirectional_MAE',False)for r in rr))
    report=f"# {task['task_id']}\n\n![主图：多个局部曲面 + Body 与 GT 的真实三角面切面比较](visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png)\n\n"
    report+='主图为预先固定C3/E1/BODY_HIER：两张纵向(X=0、Y=0)、两张横向(Z=-2、Z=-6mm)；四列配准前→配准后→整体融合→GT评价。黑GT、灰虚线Body、全部004红/005蓝、紫融合。所有曲线来自实际三角面求交，未以采样点或平均轮廓替代。\n\n'
    report+='[离线逐视频/逐视角三维交互](visualization/multisurface_3d.html) · [全部条件指标](visualization/ALL_CONDITION_METRICS.csv) · [材料点/重叠](visualization/REGISTRATION_METRICS.json) · [整体/区域/截面](visualization/MODEL_METRICS.json) · [Surface Ownership Map](visualization/SURFACE_OWNERSHIP_MAIN.csv) · [失败台账](visualization/FAILURE_LEDGER.json)\n\n'
    report+='## 科学范围、来源与独立曲面\n\n复用已验收SIM_PROTOCOL_REV1的G01-like固定场景及GT-free正式E1/E2初始Body。004/005各选8个FIT视角：保留全部父Body拟合FIT引用，再按真实Camera-to-Ring方向最远点补齐；另保留8 HOLDOUT。真实机位定义本轮虚拟真值，不宣称真实部署认证。每视角重新生成RGB/Mask/轴向深度，并严格核对冻结DXY缓存的RGB/Mask内容SHA。没有新的DXY调用、P/Q或直径研究，没有HERO训练。\n\n'
    report+='每片局部Mesh独立由本帧Mask内原生2px深度栅格反投影并三角化；跨深度不连续大边显式拒绝，原始无效/缺失区域保留。禁止且未使用GT原始面按视频合并。GT像素/Face/重心身份只存在generator私有输出，评价器在预测冻结后才读取。所有未融合的16片独立曲面均保留。\n\n'
    report+='## 误差协议与曲面优化\n\nEstimatedPose=VideoBias×TruePose×FrameNoise。A=+Y2°/+X0.5mm，B=+Y3°/+X0.3mm；世界偏差左乘、零均值六维噪声右乘局部机位。种子20261117，按视频中心化，跨σ使用共同随机数；每轴分布σ为0、0.3°/0.10mm或0.7°/0.20mm。物理Ring和GT固定。每帧实际注入、经验均值/标准差/完整协方差见[NOISE_AUDIT](visualization/NOISE_AUDIT.json)。预测器未获得真实误差逆矩阵。\n\n'
    report+='C0全无误差；C1仅005=A+低方差；C2仅005=B、无随机噪声；C3两视频A/B+低方差；C4两视频A/B+高方差；C5两视频无系统偏差、仅低方差。\n\n'
    report+='比较M0、不含Body的多曲面Open3D Robust ICP、仅共享视频Body定位、视频共享+帧残余Body定位。ICP固定第一片004曲面作为其显式规范，评价不替其做GT对齐。Body两臂与所有相机文件始终冻结；只估计曲面刚体变换。中介在每次外层重新建立：将固定Body拉回不可变测量图表，计算椭圆规范坐标→Body候选区域，而非优化相机。错误/接触未知/低置信或超2.5mm对应可拒绝。Body允许0.5mm区域残差，并预先运行C3的0和1mm容差消融。\n\n'
    report+='帧残余为绕本帧固定估计机位图表的小曲面SE(3)，受σ归一化先验、3σ界及视频内均值先验约束；不输出新相机，不变更输入相机文件。完整源Mesh顶点统一刚体变换，Face拓扑及边长断言排除直接贴椭球/形态替换。\n\n'
    report+='## 有明确Ownership的整体几何\n\n这是明确标记的radial-chart融合基线：相同冻结椭球参数仅作96×96等极角图表重新细分，不优化Body；从Body中心射线查询每片实际测量三角面。共识支持≥2视角时只选择一个实际三角面交点，记录来源Face/重心和全部未采用候选，绝不输出平均坐标。其余位置由Body补全，观测但不可信与从未观测分开标记。冲突跨度>0.25mm逐点保留；跨owner接缝大边>0.8mm的三角形显式记为缺口，不静默删除。\n\n'
    report+='每图表单元最多一片最终三角形，GT覆盖只在固定独立GT样本上计一次，重复曲面不能提高分母或虚增覆盖。所有原片仍可独立开关。非星形、隐藏凹部和接缝仍是该基线的真实限制；有缺口、偏差或不改善均保留负结果。Body-only同时给原冻结网格和相同细分图表，主要改善比较使用相同图表，避免把细分误差归功于HERO。\n\n'
    report+='## 全部主条件和容差消融\n\n| Condition/arm/method/tol | Material MAE mm | Whole GT bidir MAE / P95 mm | Unique GT coverage | Improves Body |\n| --- | ---: | --- | ---: | --- |\n'
    fmt=lambda x:'NaN'if x is None else f'{x:.6f}'
    for r in pred['rows']:
        key=r['key'];m=met[key];s=m.get('bidirectional_mm')or{};report+=f"| {key} | {fmt(reg[key]['mean_frame_material_MAE_mm'])} | {fmt(s.get('MAE'))} / {fmt(s.get('p95'))} | {fmt(m.get('GT_unique_coverage'))} | {m.get('improves_Body_bidirectional_MAE',False)} |\n"
    report+='\n每片全部材料点误差、同视频及跨视频固定重叠材料目标、双向表面MAE/中位数/P95/最大值、真实观测/未观测区域覆盖、无向法向形态误差及真实Mesh截面误差均保留。材料点相对误差另给相对于真实轴向深度的定义；本任务不输出直径精度。GT目标12000和模型面积样本12000固定；局部截面使用固定400点弧长求积仅作指标，显示始终是全部真实线段。未命中和失败保留NaN/全分母，任何阶段未作GT最优刚体对齐。\n\n'
    report+='## 固定审计表\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | G01-like场景1；6主条件×2 Body×4方法；每条件16独立FIT片，另8 HOLDOUT源保留；4个C3容差消融 |\n| 本算法独立成功 | 数值生成与相对Body改善分开统计，见全条件表和RESULT_CARD |\n| 本算法失败 | 逐方法/条件负结果与NaN见FAILURE_LEDGER；全部实际切面保留 |\n| 历史测量值回退 | 0；用户明确授权复用GT-free二维Body/像素初始数据，不作为最终测量值回退 |\n| 失败组及具体原因 | 每条件/Body/方法关联材料点、重叠、Ownership冲突、接缝缺口和切面 |\n| 最终统计样本 | 固定每片全部材料顶点、固定重叠目标、固定GT样本；不只统计成功条件 |\n| 是否使用GT选择算法 | 否；TASK/源码/数据/先验及容差预先冻结，所有预测冻结后独立评价 |\n\n'
    report+='## 实际切面图\n\n'
    for name,caption in figures.items():report+=f'- [{caption}](visualization/figures/{name})\n'
    report+='\nSmoke先通过C0和单视频低方差实际Mesh错层/真实优化验证，随后才扩展矩阵和融合。执行/产物验收不代表科学准确性通过；不收敛、不改善和未匹配均为保留结果，不自动晋升永久规则。\n'
    (attempt/'TECHNICAL_REPORT.md').write_text(report);save_json(attempt/'SCIENTIFIC_SUMMARY.json',scientific_summary);save_json(attempt/'FIGURES.json',figures)
    card=f"# {task['task_id']}\n\nG0–G4执行完成，科学结论等待人工审阅；独立深度栅格曲面，非GT原面并集。\n\n[首张主图：真实切面四列比较](visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png) · [逐视角完整Mesh交互](visualization/multisurface_3d.html) · [报告](TECHNICAL_REPORT.md) · [Ownership](visualization/SURFACE_OWNERSHIP_MAIN.csv)\n\n"
    for key,v in scientific_summary.items():card+=f'- {key}: 数值{v["numeric"]}/6，整体双向MAE改善{v["improved_body_MAE"]}/6（非全部空间准确性认证）。\n'
    (attempt/'RESULT_CARD.md').write_text(card)
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>多独立曲面+Body融合审阅</title><style>body{font:16px system-ui;max-width:1450px;margin:26px auto;background:#f5f7fa;color:#172333}img{max-width:100%}a{color:#245cb0}</style><h1>多个局部曲面 + Body 与 GT：真实Mesh切面</h1><p>第一张主图：预注册C3/E1/BODY_HIER，两纵向、两横向；全部独立Mesh三角面求交，四列固定毫米范围。</p><img src="figures/01_MAIN_MULTISURFACE_SECTIONS.png" alt="Main scientific figure: all actual independent mesh intersections, GT, Body and owned fusion"><p><a href="multisurface_3d.html">逐视频、逐视角完整曲面交互</a> · <a href="../TECHNICAL_REPORT.md">技术报告</a> · <a href="../RESULT_CARD.md">结果卡</a> · <a href="../RUN_MANIFEST.json">运行清单</a> · <a href="ALL_CONDITION_METRICS.csv">全部指标CSV</a> · <a href="SURFACE_OWNERSHIP_MAIN.csv">Surface Ownership Map</a> · <a href="FAILURE_LEDGER.json">失败台账</a></p><svg viewBox="0 0 1100 35"><text x="0" y="23">G0 independent depth grid → G1 frozen E1/E2 → G2 candidates → C0/C1 Smoke → G3 hierarchical surfaces → G4 owned fusion + independent GT</text></svg>'
    for name,caption in figures.items():
        if name!='01_MAIN_MULTISURFACE_SECTIONS.png':page+=f'<h2>{html.escape(caption)}</h2><img loading="lazy" src="figures/{name}" alt="{html.escape(caption)}">'
    page+='<p><a href="NOISE_AUDIT.json">每帧真实注入/协方差</a> · <a href="MODEL_METRICS.json">整体/分区域/截面</a> · <a href="REGISTRATION_METRICS.json">全部材料点/固定重叠</a> · <a href="GENERATION_AUDIT.json">独立Mesh来源核验</a></p><details><summary>历史工程回归参考，非本轮科学结果</summary><img src="../evidence.png" alt="Historical engineering reference only"></details></html>'
    (attempt/'index.html').write_text(page)
    return outputs(attempt,dict(status='PASS',role='evaluator',figures=figures,scientific_summary=scientific_summary,scientific_failures=failure['failures'],exact_triangle_sections=True,first_main_figure='figures/01_MAIN_MULTISURFACE_SECTIONS.png',GT_read_by_visualizer=True))
