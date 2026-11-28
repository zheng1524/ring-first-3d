"""Vertical real-data review: RGB contains only native 2D body and visible 3D body curves."""
from common import *
from consume_revision import load_configuration,load_views as read_body_views
from observations import scene,cast,CFG
from geometry import rays,clipped_depth,corrected_points,basis
from visualize import show_mesh,section,hero_meshes,COL,plt,Poly3DCollection,LineCollection
import cv2,gzip,html,os,argparse
from urllib.parse import quote
PURPLE='#c65ce6';GREEN='#20be65'
STYLE='body{font-family:sans-serif;max-width:1040px;margin:24px auto;padding:12px;background:#fafafa;color:#222}section,figure{display:block;margin:22px 0}img,svg{display:block;max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse}td,th{padding:5px;border:1px solid #bbb}a{overflow-wrap:anywhere}'
def esc(x):return html.escape(str(x),quote=True)
def page(title,body):return '<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+STYLE+'</style><h1>'+esc(title)+'</h1>'+body+'</html>'
def relative(p,start):return quote(os.path.relpath(p,start),safe='/')
def curve(record):
    if not record or record.get('center_px') is None:return np.empty((0,2))
    t=np.linspace(0,2*np.pi,361);return np.array(record['center_px'])+np.c_[np.cos(t),np.sin(t)]@np.array(record['basis_px']).T

def selected_candidates(process,selected_id):
    pool=process.get('default_candidate_pool',[])
    # Actual IDs, deterministic order; a profile or rejected candidate never becomes an alternative prediction.
    eligible=[r for r in pool if r.get('supervision_eligible') and not r.get('diagnostic_profile') and not r.get('original_rejection_reasons') and not r.get('current_reasons') and r.get('record_id')!=selected_id]
    out=[]
    for body in sorted({r.get('body','') for r in eligible}):
        same=[r for r in eligible if r.get('body')==body]
        if same:out.append(min(same,key=lambda r:r.get('index',0)))
    return out[:2]

def svg_rgb(rgb,shape,points,root):
    h,w=shape[:2];parts=[f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">',f'<image href="{relative(rgb,root)}" width="{w}" height="{h}"/>']
    if len(points):
        xy=' '.join(f'{x:.3f},{y:.3f}' for x,y in points if np.isfinite([x,y]).all());parts.append(f'<polyline points="{xy}" fill="none" stroke="{PURPLE}" stroke-width="1.4"/>')
    return ''.join(parts)+'</svg>'

def dxy_frame_page(path):
    r=read(path);folder=T/'runs/review/frames'/r['case']/r['frame_id'];folder.mkdir(parents=True,exist_ok=True);asset(r['RGB'],r['RGB_sha256']);asset(r['arrays']['path'],r['arrays']['sha256']);asset(r['process']['path'],r['process']['sha256'])
    curves=dict(np.load(r['arrays']['path']));process=read_gzip(r['process']['path']);selected=curves.get('selected_curve',np.empty((0,2)));alternatives=selected_candidates(process,r.get('selected_record_id'))
    state=f"{r['status']} / {r['quality']}；正式 Ring 测量 {'有效' if r['official_measurement_valid'] else '未通过'}；二维角色 {r['role']}"
    body=f'<p>{esc(state)}</p><p>紫色：本帧真实算法曲线。PIXEL_ONLY 不提供毫米量尺；有曲线不等于质量可靠。完整流程先于三维，未由三维反推。</p>'
    if len(selected):body+=f'<h2>算法选中主体：{esc(r.get("selected_record_id"))}</h2>'
    else:body+=f'<h2>无可用选中曲线</h2><p>{esc(r.get("official_reason"))} / {esc(process.get("pixel_branch",{}))}</p>'
    body+=svg_rgb(r['RGB'],r['native_shape'],selected,folder)
    body+='<h2>真实候选过程</h2><p>以下每幅只展示一个实际候选。它们是过程证据，不与选中预测同等使用；完整池中的拒绝项和 identifiability profile 仅供数据诊断。</p>'
    ids=[]
    for c in alternatives:
        ids.append(c['record_id']);body+=f'<h3>{esc(c["record_id"])}；{esc(c.get("body"))}/{esc(c.get("shape"))}</h3><p>来源 {esc(c.get("origin"))}；P loss {esc(c.get("P_loss"))}；Q loss {esc(c.get("Q_loss"))}</p>'+svg_rgb(r['RGB'],r['native_shape'],curve(c),folder)
    if not alternatives:body+='<p>没有额外满足展示条件的默认 A/B 候选；不构造演示曲线。像素出口的真实候选和拒绝原因仍见完整过程文件。</p>'
    body+=f'<p>P/Q/X 原轮廓点数：{r["P_count"]}/{r["Q_count"]}/{r["X_count"]}；完整候选 {r["candidate_count"]}，profile {r.get("profile_count",0)}。</p><p><a href="{relative(path,folder)}">身份、质量与选择</a> | <a href="{relative(Path(r["arrays"]["path"]),folder)}">原轮廓身份与 Q 法向区间</a> | <a href="{relative(Path(r["process"]["path"]),folder)}">完整候选池、选择及拒绝记录</a></p>'
    overlay=folder/'BODY_COMPARISON.png';comparison=folder/'BODY_COMPARISON.json';valid_comparison=False
    if overlay.exists() and comparison.exists():
        receipt=read(comparison);valid_comparison=all(Path(x['path']).exists() and sha(x['path'])==x['sha256'] for x in [receipt['result'],receipt['frame'],receipt['camera']])
    if valid_comparison:body+='<h2>本地单视频三维对照</h2><p>紫：二维主体；绿：当前交付三角主体的可见投影；固定 CAD 仅作遮挡计算。</p><img src="BODY_COMPARISON.png">'
    else:body+='<h2>三维对照状态</h2><p>此页只生成二维过程；未将未选帧加入三维拟合。若该视频单视频结果和真实相机已完成，可按需运行：</p><pre>bash run_python.sh code/visualize_revision.py --frame '+esc(r['case']+'/'+r['frame_id'])+'</pre>'
    (folder/'index.html').write_text(page(r['case']+' / '+r['frame_id'],body))
    save(folder/'DISPLAY.json',dict(selected_record_id=r.get('selected_record_id'),shown_alternative_record_ids=ids,rule='first eligible non-profile unrejected actual candidate per A/B; at most two; never invented',frame=asset(path),process=r['process'],curves=r['arrays'],layout='one_column',RGB_allowed_layers=['native_2D_body','delivered_3D_visible_body']))
    return r

def read_gzip(p):
    with gzip.open(p,'rt')as f:return json.load(f)

def dxy_index(cases=None):
    allcases=sorted(p for p in (T/'runs/dxy').iterdir() if p.is_dir());links=[];count=0
    for root in allcases:
        records=[]
        for p in sorted(root.glob('*/FRAME.json')):
            if cases is None or root.name in cases:r=dxy_frame_page(p)
            else:r=read(p)
            records.append(r)
        records.sort(key=lambda x:x['index']);count+=len(records)
        table='<table><tr><th>ledger序号</th><th>真实帧</th><th>状态/质量</th><th>三维角色</th><th>选中ID</th></tr>'
        table+=''.join(f'<tr><td>{r["index"]}</td><td><a href="{quote(r["frame_id"])}/index.html">{esc(r["frame_id"])}</a></td><td>{esc(r["status"])} / {esc(r["quality"])}</td><td>{esc(r["role"])}</td><td>{esc(r.get("selected_record_id"))}</td></tr>'for r in records)+'</table>'
        reviewroot=T/'runs/review/frames'/root.name;reviewroot.mkdir(parents=True,exist_ok=True)
        (reviewroot/'index.html').write_text(page(root.name+' 全帧二维过程',f'<p>已处理 {len(records)} 帧。二维覆盖与三维 FIT/HOLDOUT 角色分开；无曲线和弱证据保留。</p>'+table));links.append(f'<li><a href="frames/{quote(root.name)}/index.html">{esc(root.name)} — {len(records)} 帧</a></li>')
    (T/'runs/review/index.html').write_text(page('全 ledger 帧真实二维主体',f'<p>当前 {len(allcases)} 视频、{count} 帧。选中曲线、A/B候选、P/Q/X及失败原因均可追溯。</p><ul>'+''.join(links)+'</ul>'))
    return count

def load_views(g,r):
    frames,sources=read_body_views(r)
    for f in frames:f['DXY']=f['DXY_record']
    return frames,sources

def visible_projection(model_scene,cad_scene,frame,shape,step=2):
    h,w=shape[:2];y,x=np.mgrid[0:h:step,0:w:step];rr=rays(np.c_[x.ravel(),y.ravel()],frame['K'],frame['C']);z,_=cast(model_scene,rr);cz,_=cast(cad_scene,rr)
    pred=(np.isfinite(z)&(z>0)&(z<cz-CFG['cad_tolerance_mm'])).reshape(y.shape);return x,y,pred

def render_rgb_axis(ax,frame,model_scene,cad_scene):
    rgb=cv2.imread(frame['RGB'])[:,:,::-1];ax.imshow(rgb);x,y,pred=visible_projection(model_scene,cad_scene,frame,rgb.shape)
    if pred.any()and not pred.all():ax.contour(x,y,pred,levels=[.5],colors=[GREEN],linewidths=1.3)
    selected=np.asarray(frame.get('DXY_curve',curve(frame['DXY'].get('selected'))))
    if len(selected):ax.plot(selected[:,0],selected[:,1],color=PURPLE,lw=1.25)
    ax.set_xlim(0,rgb.shape[1]);ax.set_ylim(rgb.shape[0],0);ax.axis('off')
    status=frame['DXY']['status'];role={'FIT':'拟合','HOLDOUT':'仅二维目标留出'}.get(frame['role'],frame['role'])
    suffix='无选中二维曲线'if not len(selected)else frame['DXY'].get('selected_record_id')
    ax.set_title(f"{frame['case'].rsplit('_',1)[-1]} / {frame['id']} / {role}\n{status} / {suffix}",fontsize=10,pad=8)

def image_panels(g,r,folder):
    fs,ss=load_views(g,r);body=np.load(folder/'BODY.npz');model_scene=scene(body['V'],body['F_solid']);cad=np.load(r['cad']['path']);cad_scene=scene(cad['V'],cad['F']);selected=[]
    for case in r['videos']:
        ff=[f for f in fs if f['case']==case];fit=[f for f in ff if f['role']=='FIT'];held=[f for f in ff if f['role']=='HOLDOUT'];selected+=([fit[0],fit[len(fit)//2]]if fit else[])+held[:1]
    fig,axes=plt.subplots(len(selected),1,figsize=(9,5.8*len(selected)),squeeze=False)
    for ax,f in zip(axes[:,0],selected):render_rgb_axis(ax,f,model_scene,cad_scene)
    fig.suptitle(f"{g} / {r['configuration']}\n紫：本帧二维主体；绿：交付三角主体可见投影\n{r['coordinate_frame']}；{r['input_kind']}；基底 {r['base_status']}；GT 不可评价",fontsize=11,y=.995)
    fig.tight_layout(rect=(0,0,1,1-0.14/len(selected)));fig.savefig(folder/'RGB_PROJECTIONS.png',dpi=110);plt.close(fig)
    return [dict(case=f['case'],frame=f['id'],role=f['role'],DXY_selected_record_id=f['DXY'].get('selected_record_id'))for f in selected]

def geometry_panels(g,r,folder):
    fs,ss=load_views(g,r);raw=np.load(folder/'CORRECTED_OBSERVATIONS.npz');body=np.load(folder/'BODY.npz');mother=np.load(folder/'FINAL_UNCUT.npz');base=read(folder/'BASE.json');plane=np.array(base['plane'])if base.get('plane')is not None else None
    V,F=mother['V'],mother['F'];b=np.array([x['b_mm']for x in r['bias']]);meshes=hero_meshes(ss,b);cad=np.load(r['cad']['path']);n=plane[:3]if plane is not None else fs[0]['C'][:3,2];n=n/np.linalg.norm(n);u=basis(n)[:,0];v=np.cross(n,u);center=np.array(r['p'][:3]);origin=center
    missing=[]
    for i,s in enumerate(ss):
        z,hit,_=clipped_depth(np.array(r['p']),s['rays'],plane if r['base_applied']else None);cz=cast(scene(cad['V'],cad['F']),s['rays'])[0];hit &= z<cz-CFG['cad_tolerance_mm'];missing.extend(corrected_points(s['rays'],s['D'],b[i])[~hit])
    missing=np.array(missing).reshape(-1,3);cut=(V[F].mean(1)@plane[:3]+plane[3]<0)if plane is not None else np.zeros(len(F),bool)
    clouds=[V,cad['V'],raw['raw_X'],raw['corrected_X']];P=np.concatenate([p for p in clouds if len(p)]);mid=(P.min(0)+P.max(0))/2;rad=max(np.ptp(P,axis=0).max()/2,3)*1.08;limits=(mid-rad,mid+rad)
    fig=plt.figure(figsize=(10,25));ax1=fig.add_subplot(411,projection='3d');ax2=fig.add_subplot(412,projection='3d');ax3=fig.add_subplot(413);ax4=fig.add_subplot(414)
    for ax,near in [(ax1,False),(ax2,True)]:
        show_mesh(ax,V,F[~cut],COL['parent'],.08);show_mesh(ax,V,F[cut],COL['cut'],.2);show_mesh(ax,body['V'],body['F'],COL['body'],.25);show_mesh(ax,body['V'],body['F_solid'][body['inferred_base_faces']],COL['cap'],.7)
        for RV,RF,CV in meshes:show_mesh(ax,RV,RF,COL['raw'],.10,500);show_mesh(ax,CV,RF,COL['corrected'],.13,500)
        show_mesh(ax,cad['V'],cad['F'],'#303030',.5,1500)
        # Each video's unchanged local CAD follows the same qualified transform for diagnosis.
        for case in r['videos'][1:]:
            M=np.array(r['video_transforms'][case]);show_mesh(ax,cad['V']@M[:3,:3].T+M[:3,3],cad['F'],'#888888',.18,1000)
        if len(raw['raw_X']):
            ax.scatter(*raw['raw_X'][::6].T,s=1,c=COL['raw'],alpha=.35)
            if plane is not None:
                miss=raw['raw_X']@plane[:3]+plane[3]<0;ax.scatter(*raw['raw_X'][miss].T,s=4,c=COL['cut'])
        if len(missing):ax.scatter(*missing.T,s=8,c=COL['missing'],marker='x')
        if plane is not None:
            anchor=center-(center@n+plane[3])*n;radius=max(2,float(np.max(np.exp(np.array(r['p'])[6:]))));corners=anchor+np.array([[-1,-1],[1,-1],[1,1],[-1,1]])@np.c_[u,v].T*radius;ax.add_collection3d(Poly3DCollection([corners],facecolor='#aaaaaa',alpha=.16));ax.quiver(*anchor,*n,length=2,color='#222222')
        lo,hi=limits
        if near:
            rr=min(rad*.65,max(2,np.ptp(V,axis=0).max()*.35));focus=center if plane is None else center-(center@n+plane[3])*n;lo=focus-rr;hi=focus+rr
        ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect((1,1,1));ax.view_init(18,-65);ax.set(xlabel='X / mm',ylabel='Y / mm',zlabel='Z / mm');ax.set_title('全范围：同一坐标内固定毫米尺度'if not near else'基底邻域近景（上图保留全范围）',fontsize=11)
    for ax,normal,B,label in [(ax3,v,np.c_[u,n],'沿基底法向的真实三角面剖面'),(ax4,n,np.c_[u,v],'平行基底的真实三角面剖面')]:
        for VV,FF,col,lw in [(V,F,COL['parent'],1),(V,F[cut],COL['cut'],1.3),(body['V'],body['F'],COL['body'],1.5),(body['V'],body['F_solid'][body['inferred_base_faces']],COL['cap'],2),(cad['V'],cad['F'],'#303030',.7)]:
            seg=section(VV,FF,normal,origin);ax.add_collection(LineCollection((seg-origin)@B,colors=col,linewidths=lw))
        for RV,RF,CV in meshes:
            for VV,col in [(RV,COL['raw']),(CV,COL['corrected'])]:ax.add_collection(LineCollection((section(VV,RF,normal,origin)-origin)@B,colors=col,linewidths=.7,alpha=.65))
        if ax is ax3 and plane is not None:ax.axhline(-(origin@n+plane[3]),color='#333333',ls='--',lw=.8)
        if len(missing):
            close=missing[abs((missing-origin)@normal)<.3]
            if len(close):ax.scatter(*((close-origin)@B).T,s=8,c=COL['missing'],marker='x')
        ax.autoscale();ax.set_aspect('equal');ax.set(xlabel='截面水平 / mm',ylabel='截面垂直 / mm',title=label);ax.grid(alpha=.2)
    base_label='实际裁切'if r['base_applied']else'母体保留；基底仅可逆候选'if base.get('candidate')else'无受支持基底'
    fig.suptitle(f"{g} / {r['configuration']}\n{r['coordinate_frame']}；{r['base_status']}；{base_label}\n橙 原始 HERO / 青 校正 HERO / 蓝 未裁母体 / 绿 主体 / 红 切侧 / 紫 推断底盖\n深红× 未解释 {len(missing)}/{r['depth_fixed_N']}；黑 anchor CAD / 灰 其他视频 CAD\nHERO每视频均匀显示2来源；指标保留全部；单位 mm；真实 GT 不可评价",fontsize=11,y=.997)
    fig.tight_layout(rect=(0,0,1,.95));fig.savefig(folder/'GEOMETRY_SECTIONS.png',dpi=105);plt.close(fig)

def frame_comparison(case,frame_id):
    fp=T/'runs/dxy'/case/frame_id/'FRAME.json';d=read(fp);folder=T/'runs/results'/d['group']/case.rsplit('_',1)[-1]
    if not(folder/'RESULT.json').exists():raise ValueError('No completed single-video initialization for '+case)
    r=load_configuration(folder/'RESULT.json')['record'];assert r['coordinate_frame']=='VIDEO_LOCAL';asset(d['camera']['path'],d['camera']['sha256']);cam=np.load(d['camera']['path']);j=d['index']
    if j>=len(cam['c2w'])or not np.isfinite(cam['c2w'][j]).all():raise ValueError('No reliable finite camera for this ledger frame')
    f=dict(case=case,id=frame_id,role=d['role'],RGB=d['RGB'],K=cam['K'],C=cam['c2w'][j],DXY=d,DXY_curve=np.load(d['arrays']['path'])['selected_curve']);body=np.load(folder/'BODY.npz');cad=np.load(r['cad']['path']);fig,ax=plt.subplots(1,1,figsize=(9,6.5));render_rgb_axis(ax,f,scene(body['V'],body['F_solid']),scene(cad['V'],cad['F']));fig.suptitle('本地单视频：紫 二维算法主体 / 绿 交付三角主体可见投影\n真实相机与固定毫米尺度；GT不可评价',fontsize=11);fig.tight_layout(rect=(0,0,1,.9));review=T/'runs/review/frames'/case/frame_id;review.mkdir(parents=True,exist_ok=True);fig.savefig(review/'BODY_COMPARISON.png',dpi=110);plt.close(fig);save(review/'BODY_COMPARISON.json',dict(result=asset(folder/'RESULT.json'),frame=asset(fp),camera=d['camera'],projection='actual exported triangles; anchor CAD occlusion',layers=['2D_selected','3D_visible'],layout='one_column'));dxy_frame_page(fp)

def group_page(g):
    folder=T/'runs/results'/g;rec=read(folder/'GROUP_RESULT.json');parts=['<p>单视频均在自身 LOCAL 坐标，未把失败关系叠成同一场景；只有明确 PASS 的子集执行联合。GT不可评价。</p>'];shown=[]
    results=sorted(rec['results'],key=lambda r:(len(r['videos'])>1,r['configuration']))
    for r in results:
        name=r['configuration'];root=folder/name;load_configuration(root/'RESULT.json')
        if len(r['videos'])==1:
            case=r['videos'][0];parts.append(f'<h2>视频 {esc(name)}：独立二维过程</h2><p><a href="{relative(T/"runs/review/frames"/case/"index.html",folder)}">全部 ledger 帧、实际选中与候选过程</a></p>')
            paths=sorted((T/'runs/dxy'/case).glob('*/FRAME.json'))
            if paths:
                pick=next((p for p in paths if read(p)['status']=='PIXEL_ONLY'),paths[0]);parts.append(f'<p><a href="{relative(T/"runs/review/frames"/case/pick.parent.name/"index.html",folder)}">代表帧完整二维过程：{esc(pick.parent.name)}</a></p>')
        fk=digest([sha(root/'RESULT.json'),sha(root/'BASE.json'),sha(Path(__file__))]);receipt=root/'FIGURES.json'
        if not(receipt.exists()and read(receipt).get('key')==fk and all(Path(x['path']).exists()and sha(x['path'])==x['sha256']for x in read(receipt)['files'])):
            selected=image_panels(g,r,root);geometry_panels(g,r,root);save(receipt,dict(key=fk,layout='one_column_HTML_and_PNG',RGB_layers=['native_2D_body','delivered_3D_visible_body'],selected_frames=selected,files=[asset(root/n)for n in ['RGB_PROJECTIONS.png','GEOMETRY_SECTIONS.png']]))
        parts.append(f'<h2>{esc(name)}：{esc(r["coordinate_frame"])}</h2><p>{esc(r["input_kind"])}；基底 {esc(r["base_status"])}；显式二维留出 IoU {r["held_IoU_mean"]:.3f}（非独立端到端测试）。</p><p><a href="{name}/RESULT.json">参数与偏置</a> | <a href="{name}/BASE.json">基底证据</a> | <a href="{name}/EVALUATION.json">固定分母评价</a></p><img src="{name}/RGB_PROJECTIONS.png"><img src="{name}/GEOMETRY_SECTIONS.png">');shown.append(name)
    if rec.get('not_run'):parts.append('<h2>联合未运行</h2><p>既有关系未通过使用判据，不计算诊断联合。</p><pre>'+esc(json.dumps(rec['not_run'],ensure_ascii=False,indent=2)[:7000])+'</pre>')
    if rec.get('failures'):parts.append('<h2>执行失败（保留）</h2><pre>'+esc(json.dumps(rec['failures'],ensure_ascii=False,indent=2))+'</pre>')
    parts.append('<p><a href="GROUP_RESULT.json">全组结果与资格</a></p>');(folder/'index.html').write_text(page(g,''.join(parts)));print('VERTICAL_REVIEW',g,shown,flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--group');parser.add_argument('--frame');parser.add_argument('--dxy-only',action='store_true');args=parser.parse_args()
    if args.frame:
        case,f=args.frame.split('/');frame_comparison(case,f);return
    cases=None
    if args.group:
        q=next(g for g in read(T/'evidence/REGISTRATION_QUALIFICATION.json')['groups']if g['group']==args.group);cases=q['videos']
    count=dxy_index(cases)
    if args.dxy_only:return
    links=[]
    for root in sorted((T/'runs/results').glob('*')):
        if not root.is_dir()or not(root/'GROUP_RESULT.json').exists():continue
        if not args.group or root.name==args.group:group_page(root.name)
        links.append(f'<li><a href="{quote(root.name)}/index.html">{esc(root.name)}</a></li>')
    text=f'<p>全部图像与 PNG 内部均为单列。当前二维过程覆盖 {count} 帧；<a href="../review/index.html">全部帧二维索引</a>。</p><p>原图仅紫色二维主体和绿色当前三角主体投影。真实GT不可评价，数值完成不等于形状验证。</p><ul>'+''.join(links)+'</ul>'
    (T/'runs/results/index.html').write_text(page('R1 002：配准资格先行的粗主体审阅',text))
if __name__=='__main__':main()
